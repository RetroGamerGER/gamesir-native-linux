> Public export: personal tester, host and path references were anonymized. Historical evidence hashes refer to the private originals.

# Hardwaretest 002: Deadband-Motorvergleich zur Freigabe

12. Oktober 2026. **Der erneut freigegebene Lauf aus `3c64312` ist abgeschlossen:**
zwölf erfolgreiche Start-/Stopp-Paare, alle laut [tester] spürbar und beendet,
anschließend normale KDE-Eingaben. [Ergebnisbericht](MOTOR_COMPARISON_RESULTS.md).
Dieser Plan und `MOTOR_COMPARISON_PREPARATION.json` dokumentieren den damaligen
Vorbereitungsstand; erneute Ausführung ist damit nicht freigegeben.
Grund: Im nativen 120-s-Lauf `743407f` war laut [tester] am linken Griff keine
Vibration spürbar. Gamepad/IMU liefen während aller vier nativen Motorbefehle
weiter; END/Rückkehr zu xpad und anschließendes Entladen sind geprüft.
Details: [Hardwareverlauf](HARDWARE_TEST_002_PROGRESS.md).

## Einmaliger Ablauf

Bestehender isolierter dumpcap-Recorder, unveränderte 270 s Gesamtdauer.
Manuell genau drei Einzeltests pro Motor, zwölf insgesamt. Keine automatischen
Motoraufrufe; lokale Desktop-/Terminalansagen nennen Motor und Wiederholung.
Zehn Sekunden zwischen Klickansagen, jeweils nominell 400 ms bei 100 %.
Mindestens fünf Sekunden Pause nach einem tatsächlichen Klick einhalten.
Verpasste/zu spät bemerkte Ansagen auslassen; nichts nachholen oder doppelt klicken.
Bei einer um mindestens zwei Sekunden verspäteten Helferansage wird abgebrochen,
anstatt mehrere Ansagen auf einmal auszugeben. Reaktionszeit wird im Mitschnitt
über tatsächliche Paketzeiten sichtbar; die Ansagezeit gilt nicht als Klickzeit.

| Zeit ab bestätigtem Recorderstart | Handlung |
|---|---|
| 0–35 s | Ausgangslage 100a/xpad; Controller verbunden, Deadband geschlossen |
| 35–65 s | Ansage: Deadband einmal manuell starten; bekannter Übergang nach 109c |
| 65–75 s | Verbindung und gespeicherte IMU-Telemetrie geprüft; kurze Ruhe |
| 75–95 s | Vibration öffnen, viermal 100 % und 1000 Hz nur ablesen; nichts ändern/speichern |
| 95–125 s | Linker Griff; fünf Sekunden Vorbereitung, Klickansagen bei 100/110/120 s |
| 125–155 s | Rechter Griff; Klickansagen bei 130/140/150 s |
| 155–185 s | Linker Trigger; Klickansagen bei 160/170/180 s |
| 185–215 s | Rechter Trigger; Klickansagen bei 190/200/210 s |
| 215–233 s | Keine weiteren Tests, Pause |
| 233–253 s | Deadband-Fenster regulär direkt schließen; Rückkehr nach 100a/xpad prüfen |
| 253–263 s | Kurze normale Eingaben zur Rückkehr; kein Neustart/Reset |
| 263–270 s | Schlussruhe, automatisches Aufnahmeende und Sicherung |

Nur die Schaltflächen „Test left grip (heavy motor)“, „Test right grip (light
motor)“, „Test left trigger“, „Test right trigger“. **Kein „Test both grip
motors“**: Das wäre laut Quellcode ein anderer Befehl mit Standardamplitude 75 %.
Force/Sync unverändert lassen. Kein Speichern, keine Profile-/Pollingänderung,
kein Funk-Neustart; Dongle bleibt am Port. Keine zusätzlichen IMU-Bewegungs- oder
Tasten-Zuordnungstests in diesem Lauf. IMU/Gamepad-Verkehr wird passiv mitgespeichert.
Keine fortlaufende Stickbewegung nötig: Der native Laufzeitwächter läuft hier nicht.

## Exakter Einstieg nach separater Freigabe

Arbeitsbereich lokal:
`/path/to/workspace`.
Der vorhandene Hosthelfer wurde für diese Ansagen kopiert; Recorderengine und
Sandbox bleiben unverändert. Ein sichtbares Terminal startet ausschließlich:

```sh
/usr/bin/python -B /path/to/workspace/work/run-motor-comparison.py
```

Versionierter Nachweis: [Quellhashes und Offline-Prüfung](MOTOR_COMPARISON_PREPARATION.json),
[vollständiger Unterschied zum bisherigen Hosthelfer](MOTOR_COMPARISON_RECORDER.patch).
Die angepasste Metadatenprüfung ist als
[separater Unterschied](MOTOR_COMPARISON_STATE_CHECK.patch) erhalten.
Vor Ausführung den SHA256 des Helfers erneut gegen diesen Nachweis prüfen.
Zum ursprünglichen Vorbereitungsstand war der Helfer weder importiert noch
ausgeführt; AST/Compile und Shellsyntax wurden gerätefrei geprüft,
einschließlich der zwölf Zeiten und Latenzgrenze.
Die vorhandenen Projekt-Grundtests (`make test`) bestehen ebenfalls.

Nach lesenden Prüfungen führt er die ausdrücklich mitfreizugebende Anmeldung aus:

```sh
SUDO_ASKPASS=/usr/bin/ksshaskpass /usr/bin/sudo -A -p 'Password: ' -v
```

Anschließend wartet er auf `START` (Groß-/Kleinschreibung egal). Erst danach
startet die bereits geprüfte privilegierte Kette, deren vollständiges argv
im neuen Datenordner als `command-argv.json` erhalten bleibt:

```sh
sudo -n /usr/bin/timeout --signal=TERM --kill-after=2s 300s \
  /usr/bin/env -i PATH=/usr/bin LANG=C TZ=UTC HOME=/ \
  /usr/bin/unshare --mount --propagation private \
  /usr/bin/bash -euc "$setup" measurement-B "$baseline" "$guest" "$identity"
```

Die vier Argumente sind gelesene Inhalte der vorhandenen Dateien
`work/motor-comparison-code/setup.sh`, `guest-check.py`, `identity-check.py` und
der unmittelbar zuvor lesend erhobene JSON-Ausgangszustand. Diese Darstellung
ist die Expansion des geprüften Python-argv, kein separat auszuführender Shellblock.
Innerhalb der Sandbox lautet der eigentliche Recorderbefehl unverändert:

```sh
/usr/bin/dumpcap -i usbmon8 -y USB_LINUX_MMAPPED -s 0 -F pcapng \
  -a duration:270 -a filesize:2000000 -q -w -
```

Er darf **nicht außerhalb der Sandbox** aufgerufen werden. Nur `/dev/usbmon8`
wird eingebunden; `/dev/bus/usb` ist nicht sichtbar. Sechs Namespaces, private
Mounts, alle fünf Capability-Sätze null, NoNewPrivs=1 sowie FD-/Rechte-/Mapping-
Prüfungen vor und nach dumpcap bleiben unverändert. So kann libpcap keine
zusätzlichen USB-Deskriptorabfragen über usbfs senden. Passive udev-Beobachtung
dokumentiert die Neuanmeldungen. Deadband selbst sendet bei Start, Tests und
Schließen USB-Befehle und kann xpad ablösen; genau das ist Teil der Freigabe.

## Voraussetzungen, Abbruch und Rückweg

Vorbereitung lesend bestätigt: Paketstände unverändert (bubblewrap 0.13.0-1,
util-linux 2.42.4-1, wireshark-cli 4.7.4-1, libpcap 1.11.0-1,
deadband-git r152.771b28a-1); nach [tester]' manuellem Deadband-Gegencheck
3537:100a, Bus 8, Adresse 27, Port 8-6,
IF0 xpad/IF1 usbhid, gs_native entladen. **Zeitgebundene Beobachtung**;
der Helfer prüft Zustand, Hashes und mindestens 5 GiB freien Speicher erneut.
Er übernimmt die dann aktuelle Adresse aus der Geräteidentität, nicht pauschal 27.
Deadband, Spiele und Eingabetester vor Start schließen. installierte App bleibt
unverändert; keine Module, Bindungsdateien oder Systemrechte werden geändert.

Am 12. Oktober fehlte zunächst `/dev/usbmon8`: `usbmon` war nicht geladen.
Nach zusätzlicher ausdrücklicher Freigabe wurde das vorhandene Modul einmal
geladen; Controllerzustand blieb unverändert. Der nächste Anlauf stoppte vor
Aufnahme an der alten festen Major 235. Aktuell registriert der Kernel usbmon
als Major 234 und IIO als 235. USBmon vergibt die Major dynamisch und verwendet
die USB-Busnummer als Minor; [Kernelquelle](https://github.com/gregkh/linux/blob/v7.2.9/drivers/usb/mon/mon_bin.c#L1281).

Die neue Kopie `work/motor-comparison-code/state-check.py` verlangt daher:
Char-Knoten root:root/0600, Minor 8, genau eine passende usbmon-Registrierung
im Character-Abschnitt von `/proc/devices`, identische Sysfs-Klassen-/Charpfade,
passendes Subsystem, beide `dev`-Dateien und übereinstimmendes `uevent`.
Alle frischen Inode-/rdev-/Rechte-/Namespace-Vergleiche bleiben erhalten.
Alte Quelldateien und Abbruchordner bleiben unverändert; Setup, Gastprüfung und
Controller-Identitätsprüfung sind byteidentisch. 13 künstliche Prüffälle bestehen:

```sh
python -B tests/check_usbmon_metadata.py --source /pfad/zum/arbeitsbereich/work/motor-comparison-code/state-check.py
```

Dieser Test verwendet nur künstliche Metadaten. Die anschließende echte
Host-/Controllerprüfung las ausschließlich Metadaten, ohne Geräteknoten zu öffnen.
`usbmon` ist seit dem freigegebenen Laden vorhanden und wird nicht automatisch
erneut geladen oder entladen. Jeder weitere Aufnahmeanlauf bleibt gesperrt bis
zur neuen Freigabe. Es gibt keine automatische Wiederholung.

Abbruch bei anderem Port/VID/PID (hier nur 100a/109c), Neuanmeldung außerhalb
35–65/233–253 s, fehlender Deadband-Sitzung/IMU-Aktivität, verlorenem Claim,
Recorder-/Isolationsfehler, Speicher unter 1 GiB, verspäteten Ansagen oder STOPP.
Bei abweichenden sichtbaren Einstellungen, falschem Motor, ausbleibendem Stopp
oder Deadband-Fehlermeldung keine weiteren Klicks und sofort STOPP melden.
Fehlende Vibration wird als Messbefund erfasst; bei dreimal stillem Motor keine
zusätzlichen Versuche außerhalb seines Fensters. Ein verlorener Gerätezustand
oder Übertragungsfehler führt unabhängig davon zum Abbruch.

`STOP`, `STOPP` oder `ABORT` im lokalen Terminal beendet den Recorder gezielt.
Der bereits vorhandene Abbruchpfad darf erforderlichenfalls ausschließlich dem
an PID, Startzeit und Programm geprüften eigenen Recorder-Supervisor SIGINT
senden. Keine USB-Reparatur. Deadband regulär schließen; dessen eigener Release
und die beobachtete Rückkehr sind vorgesehen. Falls 100a/xpad/usbhid nicht
zurückkehrt: anhalten, Zustand sichern, nächste konkrete Freigabe anfordern.
Keine automatische Treiberbindung, kein globales xpad-Entladen oder Modulstart.
Anschließend normale Funktion im KDE Center durch [tester] bestätigen lassen.

## Dauerhafte Daten und Auswertung

Neuer privater Ordner (0700) außerhalb temporärer Verzeichnisse:
`outputs/sprint-002/captures/<UTC>-motor-comparison-deadband/` im Arbeitsbereich.
Original `original-usbmon8.pcapng`, Recorder-/udev-Logs, UTC- und monotone
Ansagezeiten, Geräteepochen, ausgeführte Quellen, Rechte-/Rückkehrprüfungen und
SHA256 bleiben dauerhaft erhalten. Kein Überschreiben/Löschen früherer Daten.
`-s 0` fordert vollständige Nutzdaten; abgeschnittene Pakete, Dropzähler und
URB-Ergebnisse werden anschließend ausdrücklich geprüft, nicht vorausgesetzt.
Das Original kann Verkehr anderer Geräte auf Bus 8 enthalten und bleibt privat.
Zielauszüge anhand Bus, Zeitfenster und zugehöriger Geräteadresse jeder Epoche
erzeugen; nicht allein nach der anfänglichen Adresse filtern. Ein- UND ausgehende
Übertragungen samt Submit/Complete/Fehler behalten; Header-/Enumerationsepoche
gesondert auswerten. Filter und Hashes der Auszüge dokumentieren.

Pro Motor und Wiederholung: tatsächlicher Start-/Stoppzeitpunkt, 13-Byte-
Nutzdaten, Sequenz, Stärke, Dauer, Kanalwahl, vollständige erfolgreiche
Übertragung und Nutzerwahrnehmung. Erwartet zwölf aktive Einzelmotorbefehle
mit je einem folgenden Nullbefehl; weitere Nullpakete zur Initialisierung/
Freigabe getrennt zählen. Ausgelassene/mehrfache Klicks transparent benennen.
Keine mechanische Wirkung aus einem USB-Erfolg ableiten.

Statischer Quellennachweis (installierter Deadband-Stand 771b28a):
`bridge.py:2708` wandelt 100 % in 255; `vendors/gamesir/models/g7pro/protocol.py:435`
wandelt dies in den Protokollwert 100. `vendors/gamesir/control.py:133` sendet
den Einzelmotorbefehl, wartet nach dem Schreibaufruf 400 ms und sendet null.
Motorpaket `09 00 SS 09 00 0f LT RT LG RG 28 00 00`; genau ein Motorwert `64`.
Unser `src/gs_protocol.c` erzeugt dieselben Nutzdaten (Sequenz variabel).
Nativer Ablauf: Frist beginnt vor USB-Transfer, Ablaufprüfung etwa alle 10 ms,
zusätzlicher expliziter STOP nach 600 ms. Diese Zeitpunkte sind keine Garantie
für exakt 400 ms mechanische Bewegung.

Der native Lauf besitzt **keinen USB-Rohmitschnitt**. Seine erwarteten Encoderbytes
und bestätigten Clientaufrufe mit tatsächlich aufgezeichneten Deadband-Paketen
vergleichen; nicht behaupten, native USB-Bytes seien damit aufgezeichnet.
Bei Bedarf daraus einen gezielten späteren nativen Vergleich ableiten, separat
freigeben. Gyro-Skalierung und finale SDL-Freigabe bleiben unabhängig offen.
