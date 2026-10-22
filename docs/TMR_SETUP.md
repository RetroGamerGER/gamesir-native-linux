# Optional stick calibration in Control Center alpha2

This PRE-ALPHA function is optional. Normal gamepad input, paddles and motion
do not require it. First read the project warning and complete the normal
[driver installation and activation](INSTALLATION.md).

The tested combination is core/manager **0.1.0.alpha3-20**, calibration helper
**0.1.0.alpha1-2** and Control Center **0.1.0.alpha2**. Tests cover the normal
G7 Pro and ZZZ on the Garuda desktop. Other firmware/platforms need acceptance.

## One-time setup

1. Close games, Eden, Deadband and other controller tools.
2. Use the Control Center's **Check driver updates**, then review/install the
   current driver. Follow its separate activation/recovery instructions.
3. Download `gamesir-native-tmr-helper-0.1.0.alpha1-2-any.pkg.tar.zst` from the
   same PRE-ALPHA.4 release and verify it against the release checksums. Install
   this optional package using the normal package manager:

   ```sh
   sudo pacman -U -- gamesir-native-tmr-helper-0.1.0.alpha1-2-any.pkg.tar.zst
   ```

4. If not already explicitly enabled, create `/etc/modprobe.d/92-gamesir-native-tmr.conf`
   containing this line, without changing existing gyro/receiver settings:

   ```text
   options gs_native experimental_tmr=1
   ```

   If the file already exists, inspect and preserve its settings before editing.
   This read-only module option takes effect on the next normal boot. Do not
   reload the module while applications are using the controller.
5. After your next normal reboot and native controller connection, open the
   Control Center and choose **Open stick calibration**. The system permission
   window authorizes that session; the app itself stays unprivileged.

The AppImage does not install this helper automatically or activate the TMR
option. A missing helper, disabled API or unready controller stops the flow;
there is no raw USB fallback or automatic driver switching.

## Calibrate

Choose the intended controller, including its USB port when several receivers
are present. Release both sticks before Start. After the three-second pause,
slowly circle each stick along the outer edge three times. When both report
ready, release them and finish once. The controller owns calculation/storage.
Then check center and full travel in the ordinary controller tester.

The ring shows visited areas, not calibration accuracy. A detected connection
loss stops the session; a short invisible radio interruption cannot always be
detected. There is no automatic Finish, replay or resumed calibration. Check
the state before deliberately beginning another run after a failure.

## Remove the optional feature

Close the calibration dialog and application first. Remove the optional helper:

```sh
sudo pacman -R -- gamesir-native-tmr-helper
```

If you created the TMR-only configuration file above, remove only that file
after checking its contents, then use your next normal reboot. Preserve all
other GameSir, gyro and receiver settings. Removing the helper does not undo
the controller's stored calibration. Remove it before a complete core-driver
removal; the GUI does not yet include this fifth optional package in its list.
