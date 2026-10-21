# Control Center — permission boundary and scoped local test

21 October 2026: the [separate package executor](CONTROL_CENTER_PACKAGES.md)
is now prepared offline. It has a different action, entry and schema; none of
that new payload is installed here. The accepted installed permission-only
helper below is unchanged and cannot execute a package transaction.

20 October 2026. PRE-ALPHA. After the offline preparation below, the maintainer
separately approved installing the exact reviewed helper/policy and running
one permission-only check. That check passed on local KDE Wayland with
`authorized_only` and `executed: false`. No package transaction or driver
action ran. See the final section for the limited live evidence.

Original offline checkpoint: the maintainer accepted the GUI rehearsal and
authorized preparing the genuine graphical authorization path **offline**.
No installed helper, policy, password prompt, root execution, package action,
driver change, hardware access or push occurs in this checkpoint.

## What is prepared

The ordinary GUI/AppImage stays unprivileged and its real installation controls
remain disabled. A separate fixed helper and Polkit policy are staged as
source. `privilege.client.AuthorizationAttempt` is one-shot and has **no
default transport**. The prepared `PkexecTransport` must be explicitly supplied
with independently reviewed helper/policy hashes. It is not constructed by
normal status mode, the existing demo or the normal offline-rehearsal CLI.

The initial helper implements **authorization-only**, not a package executor.
Its acknowledgement means only that the permission probe completed. It is
neither installation success nor a credential or authorization for a later
transaction. No package-manager, service, module, USB, manager or filesystem
mutation operation exists in the helper. Future package execution still needs
its own reviewed privileged implementation and fresh authorization.

### Future process boundary

The fixed internal argv, once separately approved and installed, is:

```text
/usr/bin/pkexec --disable-internal-agent /usr/lib/gamesir-control-center/authorize
```

This is an internal boundary, not a general installation command. The client
supplies a small closed stdin JSON request; no package path, command, shell fragment or password is
passed as an argument. Polkit uses the authentication agent registered for the
calling desktop session. Its own graphical window handles the password; the
Qt application never creates a password field or receives/stores credentials.
Internal terminal-agent fallback is disabled so it cannot consume the JSON
input as a password. No elevated Qt application or GUI-environment forwarding.

Action: `io.github.RetroGamerGER.gamesir_native.control_center.authorize`.
Its policy binds the exact helper path, denies other/inactive sessions, and
requires `auth_admin` for an active local session. There is no
`auth_admin_keep`, sudoers modification, passwordless rule, wildcard command
or persistent credential. Existing system policy and agent availability still
govern actual authentication. The later local KDE permission-only check does
not establish Gamescope authentication or package-installation acceptance.
An absent agent, denied authorization or a missing reviewed installation stops;
the client never falls back to sudo, a terminal prompt or another executable.

The client's installed-file checks attest pkexec ownership plus the exact
root-owned, non-writable, hash-pinned helper, shared modules and policy. Parent
directories must be real root-owned non-writable directories; final file opens
use `O_NOFOLLOW` and `fstat`. The installed helper entry independently checks its
fixed location, isolated system Python (`-IBS`: no site hooks or bytecode
writes), effective root UID and protected code
before importing from its fixed root-owned directory. It refuses extra argv,
disables bytecode writes and never loads modules from the AppImage/user tree.
`PKEXEC_UID` is checked for correlation with a non-root caller; that environment
variable alone is not proof of authentication. Root/Polkit/code ownership form
the actual privilege boundary.

### Bounded protocol and failure behavior

Schema 1 requests have exactly mode `authorize_only`, operation `install|remove`,
one to four explicit project component names, a plan digest and a fresh random
request ID. IDs correlate a response, **not permission tokens**. Request and
response are at most 2,048 bytes. Duplicate/unknown fields, extra JSON, wrong
types, activation/paths/commands/password fields and mismatched replies stop.
Even a zero process exit is insufficient: the response must match the exact
request/plan and explicitly contain `executed: false` and `authorized_only`.

The helper waits at most five seconds for request EOF. The client uses a
bounded 120-second authorization window, capped stdout/stderr and a clean
process environment. It sends no Python/loader injection or display variables
to the elevated helper. Agent cancellation (pkexec 126), denial/error (127),
invalid reply, timeout and output-limit failure remain distinct stable states;
raw stderr/private paths are not returned to the GUI. Each attempt is consumed
once, including failure and cancellation; no automatic retry.

Cancellation/timeout attempts to terminate only the spawned process. After
elevation a same-user client may lack permission to signal a root process.
Failure to confirm termination is therefore **completion unknown**, not a
claim that cancellation succeeded. The current fixed helper cannot change
packages even if it finishes later. A future package executor must separately
handle uncertain transactions and cannot inherit a false no-change guarantee.

## Offline staging and review

As the ordinary build user:

```sh
python -B scripts/package_control_center_auth.py --dest build/control-center-auth
```

This only creates a fresh staging tree, never a live `/usr`/policy/profile
entry. Existing/nonempty/system/user-profile destinations and real root builds
are refused. No post-install hook or service activation is supplied.

The optional payload comprises the fixed `authorize` entry, only three small
root-side Python files, the single Polkit policy and GPL-v2 `COPYING`.
`AUTHORIZATION_REVIEW.json` records exact system destinations and source hashes
with `installed: false`, `reviewed: false`, `release_ready: false`. The staging
manifest's self-computed hashes are not automatically trusted: a maintainer
must independently review the source/payload and supply the trusted pins.
The driver/DKMS recipes do not install this optional payload.

Before any real permission probe, review the staged sources/hashes and target
Python/Polkit/session-agent prerequisites, then separately approve installation
of exactly that optional root-owned helper/policy. Confirm action registration,
policy loading and trusted installation on the target; a file hash alone does
not prove the authority loaded an action. Then approve one GUI/client
authorization-only test. It should display the explicit no-package-changes
message, return a correlated acknowledgement and leave packages/runtime intact.
Cancellation, missing-agent behavior and removal of owned helper/policy files
also require separate target acceptance. None of these live steps ran here.

The future real installer additionally needs authenticated binary review,
protected-byte handoff, fresh independent privileged host/guard evidence,
ALPM locking/target comparison/commit and trustworthy postchecks. It must reuse
existing cleanup hooks and keep activation separate. A successful probe must
not be cached or reused as permission for those operations.

## Offline evidence

`test_control_center_authorization.py` covers the strict protocol, fake root
identity, cancellation/denial, reply correlation, fixed invocation/environment,
timeouts/pipe limits, failed termination, root code/path/hash checks, policy
shape and noninstalled staging. Process tests replace pkexec with explicitly
harmless same-user Python fixtures; **no real pkexec or root execution**.
The existing GUI worker can inject this client into `OfflinePort` for tests;
an additional real QML test proves agent cancellation stops before even the
synthetic commit. Normal GUI defaults cannot open a permission dialog.

Final checkpoint: 27 authorization cases pass; full `make test` passes 1,492
Python cases in 52 groups plus the existing C/actual-kernel-adapter/sanitizer
checks. Optional GUI tests pass 35 cases. The separate staged payload rehashes
correctly; source diff, privacy, licensing/readme and repository manifest
checks pass. Build/test/staging outputs remain private ignored artifacts.

Local API references were read without execution/network: the installed
`pkexec(1)` manual and core Polkit policy. They document registered-session
agents, safe environment/`PKEXEC_UID`, exit codes 126/127 and policy defaults.
No manufacturer code, firmware or third-party implementation was copied.

## Read-only prerequisite check and proposed local test

20 October 2026, after the separate preparation request: the maintainer's
local KDE Wayland session is active/nonremote; Polkit and the KDE agent service
are active, and the agent belongs to the desktop user. Installed prerequisites:
Polkit 128-1, KDE agent and ksshaskpass 6.8.0-1, Python 3.14.8-1 and systemd
262.1-1. System Python accepts isolated/no-site/no-bytecode startup; pkexec and
the system destination parents are root-owned and not user-writable.
The proposed helper/module/policy/license files and new directories are absent;
the custom action is not registered. This is expected before installation.
Running agent/session metadata is not proof of a live authentication exchange.

Staged bytes and frontend source were independently compared with committed
source `580124c`, including the full GPL text. A private reviewed setup/probe/
rollback proposal is prepared under ignored build output. No public reusable
installer, trusted binary catalog or automatic GUI enablement is added here.
The proposal covers exactly six files (helper, three Python modules, one
policy, one license) and three new directories, with no existing-file overwrite.

The proposed setup runs as the desktop user. It verifies and seals all six
payloads in memory before any administrator request. Only fixed system
`install` commands run elevated; they consume sealed stdin instead of opening
mutable user source paths. The policy is copied last. Root never executes the
user-owned preparation script. This avoids privileged source-symlink reads and
input changes while the password window is open. An ordinary-user fake-root
test proved six sealed payloads and seven fixed install calls; actual sudo
calls/installations remain zero. Shell syntax and the read-only preflight pass.

After separately approved setup, installed hashes/ownership/modes and loaded
policy must match before the single authorization-only probe. No automatic
policy-service restart, source retry, package/driver action or probe follows a
failure. The separate proposed rollback checks the exact unchanged manually
installed files, preserves package-managed/unrelated content, removes no files
recursively and only removes empty owned directories. At that preparation
checkpoint, none of the setup, authentication or rollback commands had run.
Driver alpha3-16 stayed untouched.

## Approved local permission-only result

20 October 2026, after explicit approval of the reviewed setup and single
probe: fresh source/payload pins, absent destinations, active local session,
Polkit and KDE agent checks passed. The ordinary-user setup sealed all six
inputs before its fixed administrative install calls. Six exact root-owned
files and three protected directories were installed; the policy was copied
last. The source baseline remains `580124c`. No existing file was overwritten.

Installed hashes, ownership, modes and the loaded custom Polkit action matched
before the probe. Exactly one real `PkexecTransport` attempt then returned:

```json
{"state": "authorized_only", "error": "", "executed": false}
```

The final read-only installed-file/action check passed again. This proves the
fixed helper, registered desktop authorization route and correlated reply on
this KDE session. It does not prove that a password was freshly typed rather
than accepted under existing system authorization policy. No credentials were
read or stored by the client. No package manager, device, manager, service,
module, Steam or driver action was invoked by the probe or setup. Installed
alpha3-16 remains unchanged.

The optional helper/policy remains installed for this scoped acceptance;
ordinary GUI actions are still locked and no AppImage was replaced. There was
no retry, service restart or rollback. Real cancellation, missing-agent and
removal acceptance, Gamescope authorization and a real package executor remain
separate work. A successful acknowledgement grants no future transaction
permission. Documentation is committed locally only; no push or release.
