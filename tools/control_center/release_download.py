# SPDX-License-Identifier: GPL-2.0-only
"""Explicit user-side release fetch. Imports/construction never access network.

The independently reviewed catalog supplies versions, tags, sizes and hashes.
Release metadata, redirects and downloaded bytes never create trust or update
the root catalog. No latest/API lookup, extraction, cache, auth or execution.
"""
from dataclasses import dataclass
import http.client
import re
import ssl
import time
from urllib.parse import urlsplit

from artifacts import BackendError, Catalog
from package_wire import decode, encode

REPOSITORY = 'RetroGamerGER/gamesir-native-linux'
PREFIX = 'https://github.com/' + REPOSITORY + '/releases/download/'
# Reserved fixed metadata channel; not published/enabled by this offline work.
CATALOG_URL = 'https://raw.githubusercontent.com/' + REPOSITORY + '/main/updates/pre-alpha.json'
CDN_HOSTS = ('release-assets.githubusercontent.com', 'objects.githubusercontent.com')
CHUNK = 64 * 1024
DEADLINE = 90
IO_TIMEOUT = 10


@dataclass(frozen=True)
class ReleaseAsset:
    component: str
    filename: str
    review: object

    def validate(self):
        self.review.validate()
        if (self.component != self.review.component or type(self.filename) is not str
                or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.+\-]{0,180}\.pkg\.tar\.zst', self.filename)
                or '..' in self.filename):
            raise BackendError('invalid_release_asset')

    @property
    def url(self):
        self.validate()
        return PREFIX + self.review.tag + '/' + self.filename


def parse_assets(data, catalog):
    value = decode(data)
    if (type(value) is not dict or set(value) != {'schema', 'repository', 'assets'}
            or type(value['schema']) is not int or value['schema'] != 1
            or value['repository'] != REPOSITORY or type(value['assets']) is not list
            or not 0 < len(value['assets']) <= 4):
        raise BackendError('invalid_release_index')
    records = {r.component: r for r in catalog.records}
    if len(records) != len(catalog.records):
        raise BackendError('ambiguous_release_catalog')
    found = []
    for raw in value['assets']:
        if (type(raw) is not dict or set(raw) != {'component', 'filename'}
                or type(raw['component']) is not str or raw['component'] not in records):
            raise BackendError('invalid_release_index')
        asset = ReleaseAsset(raw['component'], raw['filename'], records[raw['component']])
        asset.validate(); found.append(asset)
    if (len({a.component for a in found}) != len(found) or {a.component for a in found} != set(records)
            or len({a.url for a in found}) != len(found)):
        raise BackendError('incomplete_release_index')
    return tuple(found)


def serialize_assets(assets):
    return encode({'schema': 1, 'repository': REPOSITORY,
                   'assets': [{'component': a.component, 'filename': a.filename} for a in assets]}) + b'\n'


def allowed_url(url, initial):
    if (type(url) is not str or len(url) > 8192 or not url.isascii()
            or any(ord(c) <= 32 or ord(c) == 127 for c in url) or '\\' in url):
        raise BackendError('release_redirect_refused')
    try:
        p = urlsplit(url)
        if p.scheme != 'https' or p.username is not None or p.password is not None or p.fragment:
            raise ValueError
        if url == initial and (p.netloc == 'github.com' or url == CATALOG_URL):
            return p
        if (p.netloc not in CDN_HOSTS or not p.path.startswith('/github-production-release-asset/')
                or '/..' in p.path or '%' in p.path):
            raise ValueError
        return p
    except ValueError:
        raise BackendError('release_redirect_refused') from None


class HTTPSReply:
    def __init__(self, connection, response, sock):
        self.connection, self.response, self.sock = connection, response, sock
        self.status, self.headers = response.status, tuple(response.getheaders())

    def read(self, size, timeout):
        if self.response.isclosed():
            return b''
        self.sock.settimeout(timeout)
        return self.response.read(size)

    def close(self):
        self.response.close(); self.connection.close()


class HTTPSClient:
    """No proxy environment, cookies, credentials, automatic redirects or retry."""
    def open(self, url, timeout):
        p = urlsplit(url)
        connection = http.client.HTTPSConnection(p.hostname, timeout=timeout,
                                                context=ssl.create_default_context())
        try:
            connection.request('GET', p.path + ('?' + p.query if p.query else ''), headers={
                'User-Agent': 'GameSir-Control-Center/PRE-ALPHA',
                'Accept': 'application/octet-stream', 'Accept-Encoding': 'identity',
                'Connection': 'close'})
            sock = connection.sock
            return HTTPSReply(connection, connection.getresponse(), sock)
        except Exception:
            connection.close()
            raise


def headers(reply):
    if len(reply.headers) > 64:
        raise BackendError('invalid_release_response')
    result = {}
    size = 0
    for name, value in reply.headers:
        if type(name) is not str or type(value) is not str:
            raise BackendError('invalid_release_response')
        size += len(name) + len(value)
        if size > 16384:
            raise BackendError('invalid_release_response')
        key = name.lower()
        if key in result and key in ('content-length', 'location', 'content-encoding', 'transfer-encoding'):
            raise BackendError('invalid_release_response')
        result[key] = value
    return result


class ReleaseDownloader:
    def __init__(self, client=None, *, clock=time.monotonic):
        self.client = HTTPSClient() if client is None else client
        self.clock = clock

    def fetch(self, asset, *, cancelled=lambda: False):
        asset.validate()
        data, budget = self._fetch(asset.url, asset.review.size, asset.review.size, cancelled)
        Catalog((asset.review,)).verify(asset.component, data)
        budget()
        return data

    def fetch_catalog(self, *, cancelled=lambda: False):
        from package_catalog import CATALOG_LIMIT
        data, budget = self._fetch(CATALOG_URL, None, CATALOG_LIMIT, cancelled)
        budget()
        return data

    def _fetch(self, initial, expected_size, limit, cancelled):
        url = initial
        deadline, visited = self.clock() + DEADLINE, set()

        def budget():
            if cancelled():
                raise BackendError('release_download_cancelled')
            left = deadline - self.clock()
            if left <= 0:
                raise BackendError('release_download_timeout')
            return min(IO_TIMEOUT, left)

        try:
            for _ in range(4):
                allowed_url(url, initial)
                if url in visited:
                    raise BackendError('release_redirect_refused')
                visited.add(url)
                reply = self.client.open(url, budget())
                try:
                    budget()
                    h = headers(reply)
                    if reply.status in (301, 302, 303, 307, 308):
                        url = h.get('location', '')
                        continue
                    if reply.status != 200:
                        raise BackendError('release_download_unavailable')
                    length = h.get('content-length', '')
                    if (not re.fullmatch(r'[0-9]{1,10}', length)
                            or not 0 < int(length) <= limit
                            or expected_size is not None and int(length) != expected_size
                            or h.get('content-encoding', 'identity') != 'identity'
                            or 'transfer-encoding' in h):
                        raise BackendError('release_download_size_mismatch')
                    wanted_size = int(length)
                    chunks, total = [], 0
                    while total < wanted_size:
                        wanted = min(CHUNK, wanted_size - total)
                        chunk = reply.read(wanted, budget())
                        if type(chunk) is not bytes or len(chunk) > wanted:
                            raise BackendError('invalid_release_response')
                        if not chunk:
                            raise BackendError('release_download_incomplete')
                        chunks.append(chunk); total += len(chunk)
                    if reply.read(1, budget()):
                        raise BackendError('release_download_size_mismatch')
                    budget()
                    data = b''.join(chunks)
                    return data, budget
                finally:
                    reply.close()
            raise BackendError('release_redirect_limit')
        except BackendError:
            raise
        except (OSError, http.client.HTTPException):
            # Never leak signed CDN query strings, TLS errors or private paths.
            raise BackendError('release_download_unavailable') from None
