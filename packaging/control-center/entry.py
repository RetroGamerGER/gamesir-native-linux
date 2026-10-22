# SPDX-License-Identifier: GPL-2.0-only
"""Isolated bundled entry. Self-test never creates a real metadata collector."""
import json
import os
from pathlib import Path
import sys
import tempfile

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE / 'app'))


def loaded_runtime_paths(maps):
    """Keep spaces in proc-maps pathnames; only the first five fields are metadata."""
    paths = set()
    for line in maps.splitlines():
        fields = line.split(None, 5)
        if len(fields) == 6 and fields[5].startswith('/') and any(
                name in fields[5] for name in ('libQt6', 'libpyside6', 'libshiboken6', 'libpython3')):
            paths.add(fields[5])
    return paths


def self_test(*, package_flow=False, first_run=False, release_flow=False):
    from PySide6.QtCore import QCoreApplication, QEventLoop, QTimer, QEvent, QMetaObject
    from PySide6.QtGui import QGuiApplication
    from main import create_engine
    from status import Snapshot, Fact
    import PySide6
    import shiboken6
    root = BASE.parents[2]
    class SyntheticCollector:
        def collect(self):
            return Snapshot('synthetic', 'synthetic', {
                'os': Fact('ok', 'Offline fixture'), 'kernel': Fact('ok', 'test-kernel'),
                'architecture': Fact('ok', 'x86_64'), 'headers': Fact('match', 'test-kernel'),
                'connection': Fact('unobserved'), 'receiver': Fact('absent')})
    # The smoke test intentionally uses no real display, input or user config.
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    app = QGuiApplication([])
    app.setQuitOnLastWindowClosed(False)
    with tempfile.TemporaryDirectory(prefix='gamesir-ui-qa-') as temporary:
        engine = create_engine(Path(temporary) / 'preferences.ini', demo=False,
                               collector=SyntheticCollector())
        loop = QEventLoop()
        model = engine.center_model
        def received():
            if model.snapshot is not None or model.failed:
                loop.quit()
        model.changed.connect(received)
        QTimer.singleShot(10000, loop.quit)
        loop.exec()
        model.changed.disconnect(received)
        if not engine.rootObjects() or model.snapshot is None or model.failed:
            raise RuntimeError('Bundled synthetic QML test failed')
        window = engine.rootObjects()[0]
        for language in ('de', 'en'):
            model.setLanguage(language)
            app.processEvents()
            if model.language != language:
                raise RuntimeError('Language switch failed')
        from PySide6.QtCore import QObject
        dialog = window.findChild(QObject, 'detailsDialog')
        QMetaObject.invokeMethod(dialog, 'open')
        app.processEvents()
        if not dialog.property('visible') or model.view['canInstall'] or model.view['canRemove']:
            raise RuntimeError('Read-only dialog guard failed')
        QMetaObject.invokeMethod(dialog, 'close')
        if window.grabWindow().isNull():
            raise RuntimeError('Software render failed')
        maps = Path('/proc/self/maps').read_text()
        libraries = loaded_runtime_paths(maps)
        isolated = (Path(sys.base_prefix).is_relative_to(root) and
                    Path(PySide6.__file__).is_relative_to(root) and
                    Path(shiboken6.__file__).is_relative_to(root) and libraries and
                    all(Path(name).is_relative_to(root) for name in libraries))
        if not isolated:
            raise RuntimeError('Host Python/Qt fallback detected')
        window.close()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        if package_flow or release_flow:
            package_flow_test(app, Path(temporary), release_flow=release_flow)
        if first_run:
            first_run_flow_test(app, Path(temporary))
        print(json.dumps({'synthetic_release_download': release_flow, 'synthetic_first_run': first_run, 'synthetic_package_flow': package_flow, 'privileged_calls': 0, 'ok': True, 'python': sys.version.split()[0], 'pyside': PySide6.__version__,
                          'bundled_runtime_only': True, 'read_only': True,
                          'synthetic_status': True, 'languages': ['de', 'en'],
                          'system_details': True, 'software_render': True}))
    return 0



def package_flow_test(app, temporary, *, release_flow=False):
    """Explicit offline smoke lane. Never load the embedded real review bundle."""
    from dataclasses import replace
    import hashlib
    import io
    import time
    from PySide6.QtCore import QCoreApplication, QEvent, QThreadPool
    from main import create_engine
    from app_packages import AppImageTransactions
    from backend import Outcome
    from package_catalog import CATALOG, serialize_catalog
    from package_client import FILES
    from package_execution import ExecutionTrust, InstalledReview
    from package_wire import parse_message, receipt
    from rehearsal import fixture_catalog, OfflinePort, KERNEL
    catalog, blobs = fixture_catalog()
    trust = ExecutionTrust(catalog, tuple(InstalledReview(r.component, r.version, r.guards)
                                         for r in catalog.records))
    data = serialize_catalog(trust)
    directory = temporary / 'synthetic-packages'; directory.mkdir()
    pins = [[p, hashlib.sha256(data).hexdigest() if p == CATALOG else 'a'*64] for p in FILES]
    (directory / 'profile.json').write_text(json.dumps({'schema': 1, 'scope': 'local_review',
        'pins': pins, 'distribution': 'cachyos', 'kernel': KERNEL}))
    (directory / 'REVIEWED_PACKAGES.json').write_bytes(data)
    for c, value in blobs.items(): (directory / (c + '.pkg.tar.zst')).write_bytes(value)
    downloader, downloads = None, []
    if release_flow:
        from release_download import ReleaseAsset, ReleaseDownloader, serialize_assets
        assets = tuple(ReleaseAsset(r.component, 'offline-' + r.component + '.pkg.tar.zst', r)
                       for r in catalog.records)
        (directory / 'release-assets.json').write_bytes(serialize_assets(assets))
        for p in directory.glob('*.pkg.tar.zst'): p.unlink()
        class Reply:
            status = 200
            def __init__(self, data):
                self.stream = io.BytesIO(data)
                self.headers = [('Content-Length', str(len(data)))]
            def read(self, size, timeout): return self.stream.read(size)
            def close(self): self.stream.close()
        class Client:
            def open(self, url, timeout):
                downloads.append(url)
                asset = next(a for a in assets if a.url == url)
                return Reply(blobs[asset.component])
        downloader = ReleaseDownloader(Client(), clock=lambda: 100)
    state = OfflinePort('success', lambda: 100)
    counts = []
    class Auditor:
        def inspect(self, *args, **kwargs): pass  # Deliberately synthetic; no root reads.
    class Reader:
        def collect(self): return state.observe()
    class Transport:
        auditor = Auditor()
        def __init__(self, pins): pass
        def invoke(self, message):
            source = io.BytesIO(b''.join(message.chunks()))
            parsed = parse_message(source.read, trust)
            counts.append(parsed.plan.request.operation)
            state.commit(parsed.plan); state.verify(parsed.plan)
            return 0, receipt(parsed, Outcome('verified_success', 'privileged_postcheck', changes_possible=True))
    class Collector:
        def collect(self): return None  # No real status collector.
    def wait_for(predicate):
        end = time.monotonic() + 5
        while not predicate() and time.monotonic() < end:
            app.processEvents(); time.sleep(0.005)
        if not predicate(): raise RuntimeError('Packaged synthetic flow timed out')
    for operation in ('install', 'remove'):
        tx = AppImageTransactions(directory, reader=lambda r: Reader(),
                                   transport_factory=Transport, clock=lambda: 100, downloader=downloader)
        engine = create_engine(temporary / (operation + '.ini'), demo=False,
                               collector=Collector(), execution=tx)
        model = engine.center_model
        wait_for(lambda: tx.state == 'idle')
        model.request(operation); model.prepareBackend()
        wait_for(lambda: tx.state == 'review')
        if len(counts) != (0 if operation == 'install' else 1):
            raise RuntimeError('Submission occurred before confirmation')
        model.confirmBackend(); wait_for(lambda: tx.state == 'done')
        if tx.outcome.state != 'verified_success' or model.view['canInstall'] or model.view['canRemove']:
            raise RuntimeError('Packaged synthetic result/one-shot guard failed')
        QThreadPool.globalInstance().waitForDone(5000)
        engine.rootObjects()[0].close(); engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    if counts != ['install', 'remove'] or state.host.installed != (('unrelated-controller', '1.0-1'),):
        raise RuntimeError('Packaged synthetic round trip failed')
    if release_flow and len(downloads) != 1:
        raise RuntimeError('Unexpected synthetic release download count')


def first_run_flow_test(app, temporary):
    """Synthetic first run only: never reads the real helper or asks for root."""
    import hashlib
    import time
    from PySide6.QtCore import QCoreApplication, QEvent, QMetaObject, QThreadPool, QObject
    from main import create_engine
    from first_run import FirstRunTransactions
    from helper_setup import TARGETS, COPYING, PARENT, DIRS, SUDO, POLICY, SetupInspector, mode
    from package_catalog import CATALOG, serialize_catalog
    from package_client import FILES
    from package_execution import ExecutionTrust, InstalledReview
    from rehearsal import fixture_catalog, OfflinePort, KERNEL
    catalog, blobs = fixture_catalog()
    trust = ExecutionTrust(catalog, tuple(InstalledReview(r.component, r.version, r.guards)
                                         for r in catalog.records))
    root = temporary / 'synthetic-first-run'; root.mkdir()
    packages = root / 'reviewed-packages'; packages.mkdir()
    sources = root / 'helper-payload'
    data = {p: b'OFFLINE FIXTURE ONLY, NOT EXECUTABLE\n' for p in TARGETS}
    data[COPYING] = (BASE.parent / 'licenses/gamesir-control-center/COPYING').read_bytes()
    data[CATALOG] = serialize_catalog(trust)
    pins = [[p, hashlib.sha256(data[p]).hexdigest()] for p in FILES]
    (packages / 'profile.json').write_text(json.dumps({'schema': 1, 'scope': 'local_review',
        'distribution': 'cachyos', 'kernel': KERNEL, 'pins': pins}))
    (packages / 'REVIEWED_PACKAGES.json').write_bytes(data[CATALOG])
    for c, value in blobs.items(): (packages / (c + '.pkg.tar.zst')).write_bytes(value)
    for p, value in data.items():
        path = sources / p.lstrip('/'); path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(value)
    class Target:
        def __init__(self):
            self.dirs = {p: 0o755 for p in ('/usr/lib', '/usr/share/licenses',
                '/usr/share/polkit-1/actions', '/var/cache', PARENT)}
            self.files = {}; self.calls = 0
        def exists(self, p): return p in self.files or p in self.dirs
        def directory(self, p, expected=None):
            assert p in self.dirs and (expected is None or self.dirs[p] == expected)
        def file(self, p, digest, bits): assert self.files[p] == (digest, bits)
        def policy(self, installed): assert (POLICY in self.files) == installed
        def prerequisites(self): pass
        def runner(self, argv, source=None):
            assert argv[:len(SUDO)] == SUDO
            tail = argv[len(SUDO):]; self.calls += 1
            if source is None:
                assert tail[0] == '/usr/bin/mkdir' and not self.exists(tail[-1])
                self.dirs[tail[-1]] = int(tail[2], 8)
            else:
                assert tail[0] == '/usr/bin/install' and not self.exists(tail[-1])
                self.files[tail[-1]] = (hashlib.sha256(source.read()).hexdigest(), mode(tail[-1]))
    class Auditor:
        def inspect(self, *args, **kwargs): pass
    class Transport:
        auditor = Auditor()
        def __init__(self, pins): pass
        def invoke(self, message): raise AssertionError('No package action during first-run test')
    host = OfflinePort('success', lambda: 100)
    class Reader:
        def collect(self): return host.observe()
    class Collector:
        def collect(self): return None
    def wait_for(predicate):
        end = time.monotonic() + 5
        while not predicate() and time.monotonic() < end:
            app.processEvents(); time.sleep(0.005)
        if not predicate(): raise RuntimeError('Packaged first-run fixture timed out')
    target = Target()
    tx = FirstRunTransactions(packages, inspector=SetupInspector(target), setup_runner=target.runner,
        reader=lambda r: Reader(), transport_factory=Transport, clock=lambda: 100)
    engine = create_engine(root / 'prefs.ini', demo=False, collector=Collector(), execution=tx)
    model = engine.center_model
    window = engine.rootObjects()[0]
    wait_for(lambda: tx.state == 'setup_required')
    assert target.calls == 0 and not model.view['canInstall']
    model.requestSetup(); assert target.calls == 0
    model.confirmSetup(); wait_for(lambda: tx.state == 'setup_done')
    assert target.calls == 16 and model.setup['success']
    button = window.findChild(QObject, 'setupCancel')
    assert QMetaObject.invokeMethod(button, 'clicked')
    wait_for(lambda: tx.state == 'idle')
    dialog = window.findChild(QObject, 'setupDialog')
    assert not dialog.property('visible') and window.isVisible()
    assert target.calls == 16 and model.view['canInstall']
    QThreadPool.globalInstance().waitForDone(5000)
    window.close(); engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

def calibration_flow_test():
    """Bundled Qt/worker/normal window, with only in-memory controller replies."""
    from PySide6.QtCore import QCoreApplication, QEvent
    from PySide6.QtGui import QGuiApplication
    import time
    from main import create_engine, calibration_factory
    from stick_calibration import Calibration
    if calibration_factory(BASE) is None:
        raise RuntimeError('Reviewed calibration pins are not bundled')
    app = QGuiApplication.instance() or QGuiApplication([])
    app.setQuitOnLastWindowClosed(False)
    calls = []
    view = Calibration().snapshot()
    class Client:
        def call(self, action, **fields):
            calls.append(action)
            if action == 'list':
                return {'targets': [{'pid': 0x105e, 'port': '1-2'}]}
            if action == 'select':
                view.update(phase='ready', running=True, canStart=True)
            elif action == 'prepare':
                view.update(phase='measuring', canStart=False)
            elif action == 'poll' and view['phase'] == 'measuring':
                view.update(phase='ready_to_finish', canFinish=True)
            elif action == 'finish':
                view.update(phase='completed', canFinish=False, running=False)
            else:
                raise RuntimeError('Unexpected synthetic calibration action')
            return {'view': dict(view)}
        def close(self): pass
    class Collector:
        def collect(self): return None
    def wait_for(predicate):
        end = time.monotonic() + 5
        while not predicate() and time.monotonic() < end:
            app.processEvents(); time.sleep(.005)
        if not predicate(): raise RuntimeError('Bundled calibration fixture timed out')
    with tempfile.TemporaryDirectory() as temporary:
        engine = create_engine(Path(temporary) / 'prefs.ini', demo=False, collector=Collector(),
                               calibration_factory=lambda cancelled: Client())
        model = engine.center_model; bridge = model.stickCalibration
        try:
            if calls or not model.canCalibrate:
                raise RuntimeError('Calibration started without a click or is unavailable')
            if not bridge.open(): raise RuntimeError('Cannot open synthetic calibration')
            wait_for(lambda: bridge.view['phase'] == 'selecting')
            bridge.select(0); wait_for(lambda: bridge.view['canStart'])
            bridge.start(); wait_for(lambda: bridge.view['canFinish'])
            bridge.finish(); wait_for(lambda: bridge.view['phase'] == 'completed' and not bridge.inUse)
            for language in ('de', 'en'):
                model.setLanguage(language); app.processEvents()
                if engine.rootObjects()[0].grabWindow().isNull():
                    raise RuntimeError('Bundled calibration render failed')
            if calls.count('prepare') != 1 or calls.count('finish') != 1:
                raise RuntimeError('Synthetic calibration action repeated')
        finally:
            bridge.shutdown(); engine.rootObjects()[0].close(); engine.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    print(json.dumps({'ok': True, 'synthetic_calibration': True, 'privileged_calls': 0,
                      'controller_access': False, 'normal_window': True}))
    return 0


if __name__ == '__main__':
    if os.geteuid() == 0:
        raise SystemExit('Run Control Center as the desktop user, never as root.')
    if sys.argv[1:] == ['--bundle-calibration-self-test']:
        raise SystemExit(calibration_flow_test())
    if sys.argv[1:] in (['--bundle-self-test'], ['--bundle-package-self-test'], ['--bundle-first-run-self-test'], ['--bundle-release-self-test']):
        raise SystemExit(self_test(package_flow=sys.argv[1:] == ['--bundle-package-self-test'],
                                  first_run=sys.argv[1:] == ['--bundle-first-run-self-test'],
                                  release_flow=sys.argv[1:] == ['--bundle-release-self-test']))
    from main import main
    packages = BASE / 'reviewed-packages'
    raise SystemExit(main(sys.argv[1:], packages_directory=packages if packages.exists() else None))
