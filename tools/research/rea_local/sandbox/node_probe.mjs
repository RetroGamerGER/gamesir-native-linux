// SPDX-License-Identifier: GPL-2.0-only
// Own synthetic probe only: no REA/firmware import, DNS or host-network route.
import fs from 'node:fs';
import crypto from 'node:crypto';
import os from 'node:os';
import net from 'node:net';

const baseline = JSON.parse(fs.readFileSync('/opt/rea-check/baseline.json', 'utf8'));
const fail = (message) => { throw new Error(message); };
if (process.getuid() !== baseline.uid || process.getuid() === 0) fail('Unexpected Node UID');
if (process.getgid() !== baseline.gid) fail('Unexpected Node GID');
if (process.execPath !== baseline.node_inside) fail('Wrong Node executable');
if (crypto.createHash('sha256').update(fs.readFileSync(process.execPath)).digest('hex') !== baseline.node_sha256) fail('Node digest mismatch');
for (const [name, entries] of Object.entries(os.networkInterfaces())) {
  if (name !== 'lo' || entries.some((entry) => !entry.internal)) fail('Unexpected Node network interface');
}
const newNet = fs.readlinkSync('/proc/self/ns/net');
if (newNet === baseline.namespaces.net) fail('Node reused the host network namespace');
// Literal TEST-NET address: no DNS lookup. Namespace admission above is mandatory.
const blockedConnect = () => new Promise((resolve, reject) => {
  const socket = net.createConnection({host: '203.0.113.1', port: 9});
  const timer = setTimeout(() => {
    socket.destroy(); reject(new Error('Network refusal was not immediate'));
  }, 1500);
  socket.once('connect', () => {
    clearTimeout(timer); socket.destroy(); reject(new Error('Unexpected network connection'));
  });
  socket.once('error', (error) => {
    clearTimeout(timer); socket.destroy();
    if (!['ENETUNREACH', 'EHOSTUNREACH', 'EAFNOSUPPORT'].includes(error.code)) {
      reject(new Error(`Unexpected network refusal: ${error.code}`)); return;
    }
    resolve(error.code);
  });
});
const refused = await blockedConnect();
const result = {synthetic_only: true, passed: true, node_version: process.version,
                external_literal_connect_refused: refused, host_namespace_reused: false};
fs.writeFileSync('/out/node-write-probe.json', `${JSON.stringify(result)}\n`, {flag: 'wx', mode: 0o600});
process.stdout.write(`${JSON.stringify(result)}\n`);
