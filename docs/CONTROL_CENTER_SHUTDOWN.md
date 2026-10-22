# Control Center shutdown lifetime correction — 21 October 2026

The maintainer reported QML `Cannot read property ... of null` messages from
the alpha1 AppImage, while the window remained usable and was closed normally.
The local `publish-candidate` image has SHA256
`2fab3e69a6702b2fb7589f950ab2bcd7596f2bb7edb1d850f236b53a23fddbbc`:
it matches the [recorded GitHub publication](evidence/CONTROL_CENTER_PUBLICATION_20261021.json),
despite its local directory name. It is not a separate preview-only binary.

## Confirmed defect and correction

Fresh-process tests of the actual `main()` entry point reproduce this original
destruction order: **model → QML window → engine**. Python can clear the engine
wrapper's `center_model` attribute before C++ destroys the window. QML bindings
can therefore outlive the object exposed as `appModel`. Holding a model only
as an engine-wrapper attribute does not guarantee the required teardown order.

After the event loop returns, the corrected entry point finishes existing
workers, explicitly schedules engine deletion and processes that deferred
deletion while the wrapper still holds the model and settings. The observed
order is now **QML window → engine → model**. The existing restriction on
cancellation is retained: only pre-authentication checking/download work may
be cancelled; helper/package transactions and their hooks are not interrupted.
No QML warning suppression, null-value placeholders or helper changes are used.

The exact reported warning flood was **not** reproduced in the headless runs.
The lifetime violation is directly demonstrated and fits the report; a new
interactive desktop close remains a separate confirmation of the symptom.

## Offline verification and artifact boundary

- 419 Control Center tests in 26 groups pass, including seven new fresh-process
  lifecycle tests. They cover demo, read-only status, rehearsal, existing/missing
  helper and closing during status/inspection work. Worker completion precedes
  QML destruction; no system command or package/setup submission is permitted.
- Running the new lifecycle probe against the old entry point violates the
  model/window-order assertion, providing a negative control.
- All seven lifecycle scenarios also pass with the rebuilt image's extracted
  Python/Qt runtime and entry source. Four existing synthetic AppImage lanes
  pass through its actual launcher, with no host-data or privileged operations.
- The rebuilt payload changes only `app/main.py` plus its build metadata;
  the other 1,858 regular payload files are byte-identical, including libraries,
  notices, helpers, package trust and reviewed packages. Extraction verifies all
  1,859 recorded file hashes.

The new image is a **local, unpublished correction candidate**, retained
separately. Its SHA256 is
`b942b7df4de27728edc40c9441add51d8fdccd0b5bd208beea94b5e26c330b3c`.
The original image and public release remain unchanged. The published source
lock describes the original binary; any future upload of the corrected image
requires matching updated project sources, lock, manifest and checksums as well
as publication approval. The existing third-party source kit remains retained.
No signing key, installed helper, driver, service, Steam setting or hardware
was accessed or changed. Precise gyro calibration remains paused.

[Machine-readable evidence](evidence/CONTROL_CENTER_SHUTDOWN_20261021.json).
