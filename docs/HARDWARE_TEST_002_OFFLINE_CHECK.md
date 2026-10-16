> Public export: personal tester, host and path references were anonymized. Historical evidence hashes refer to the private originals.

# Hardwaretest 002 — Offline-Prüfung und lesender Vorabcheck

Stand: 12. Oktober 2026. **Offline-Prüfung bestanden; kein Hardwaretest ausgeführt.**
Freigegeben waren Prüfung/Absicherung des Ablaufhelfers und ein frischer lesender
Vorabcheck. Keine erhöhten Rechte, Geräteöffnungen, Module, Bindungsänderungen,
Deadband-Sitzungen oder Motorbefehle wurden ausgeführt.

## Geprüfter Ablaufhelfer

`tools/native/hardware_test_002.py` erweitert den vorhandenen Client und den
lesenden Vorabcheck. Der evdev-Lesepfad folgt dem bewährten Test-001-Leser;
die historische Datei und ihre Originaldaten bleiben unverändert.

- Offline-Modus `show-plan`: nur Dateizeitplan, keine Geräte-/Systemabfragen.
- Live-Modus `execute-authorized`: gesondert freizugebende Operation in einem
  sichtbaren Terminal mit lokalem `BEREIT` und 15 s Countdown. Kein Live-Modus
  wurde zur Prüfung gestartet, auch nicht als vermeintlicher Trockenlauf.
- Exaktes Ziel und Hashes, geladene Modulparameter, Besitzer/Endpunkte, Ende von
  Deadband und vollständig sichtbare Gerätehandles als Voraussetzungen.
- Einmalige begrenzte Folge xpad-Abbindung → native Bindung → START. Kein Laden,
  Identitätswechsel, neuer Versuch, Rückbinden oder Entladen durch den Helfer.
- 120 s mit den unveränderten Ruhe-/Pufferzeiten aus dem
  [Ablaufplan](HARDWARE_TEST_002.md). Genau vier Einzelimpulse bei
  +91/+96/+101/+106 s, je 100 % und 400 ms; zusätzlicher bestätigter Stopp.
- START-Zeitmarke aus dem tatsächlichen C-Client, monotone Zeit und UTC in den
  Logs. Zeitstempel werden gegen die Empfangszeit geprüft; Entstehung während
  einer Abfrage wird nicht fälschlich als Zukunft gewertet.
- evdev-Zuordnung über das USB-Elterninterface, keine fest übernommene Eventnummer.
  Ein einziger Client für Status, IMU-Snapshots und Motoren. Gyro bleibt roh.
- Geräte-/Prozessprüfungen, Clientfehler, veraltete Sensordaten, Datenstillstand
  während der Motorphase, fehlende Bestätigungen, SYN_DROPPED und verspätete
  Phasen brechen ab. Keine nachgeholten Impulse.
- Laufendes Kerneljournal ab frischem Cursor. Neue Priorität 0–4 führt zum Halt;
  auch der bekannte xpad-ENOENT-Hinweis besitzt keine pauschale Ausnahme.
- END und Abschlussprotokoll auch im Fehlerpfad; keine automatische Rückbindung.
  Ein fehlender Abschlusssnapshot wird dokumentiert. Zusammenfassungsfehler
  verhindern nicht den Versuch, vorhandene Logs zu schließen und zu sichern.

Der C-Client erhielt nur die START-Zeitmarke, eine dazu passende präzise
Sitzungsfrist und die ausdrücklich ausgegebene erfolgreiche STOP-Bestätigung.
Der Kernelcode und der bereits vorbereitete Test-002-Modulbuild blieben in
dieser Prüfung unverändert. Kein Neuentwurf des Treiberkerns.

## Offline-Nachweise

`make test` besteht: 44 bestehende Parserprüfungen, C-Kern/Runtime/Sensoren und
Mapping/Fixtures, Client-Selbsttest, **17 Helferprüfungen** sowie **drei Fälle des
echten C-Clients mit künstlichen Systemaufrufen unter ASan/UBSan**.

Die virtuelle Uhr durchläuft die vollen 120 s ohne Wartezeit und ohne Hardware.
Getestet sind außerdem unter anderem falsche PID/Adresse/Bindung, offene Handles,
zu langsame Übergabe, veraltete oder zukünftige IMU-Samples, eingefrorener
Gamepadzähler, fehlendes START/PULSE/STOP, verlorenes Gerät, Ctrl-C, Kernelwarnung,
fehlgeschlagenes END und Fehler beim Schreiben des Abschlussberichts.
Ein Test blockiert echte Geräteöffnungen, Subprozesse und Schlafaufrufe während
des künstlichen Ablaufs. Weitere Tests speisen gespeicherte künstliche Zeilen
in den echten Kerneljournal- und Clientparser.

Maschinenlesbarer Nachweis: [HARDWARE_TEST_002_OFFLINE_CHECK.json](HARDWARE_TEST_002_OFFLINE_CHECK.json).
Private vollständige Prüflogs einschließlich Hashkontrolle:
`build/results/hardware-test002-offline-20261012T151820746633Z/`.

## Frischer lesender Systembefund

Zeitpunkt **12. Oktober, 15:14:25 UTC / 17:14:25 MESZ**. Vorher/Nachher innerhalb
dieses Checks identisch; Funkcontroller laut Nutzer eingeschaltet und verbunden.
Die Beobachtung ist zeitgebunden und keine Zusage für einen späteren Lauf.

| Merkmal | Befund |
|---|---|
| Kernel und vorhandene Header | `7.2.9-2-garuda` |
| Ziel | `3537:100a`, Bus 8, Adresse **14**, physischer Port `8-6` |
| Interface 0 | `xpad`, ff/5d/01, Interrupt 02/82 mit 32 Byte |
| Interface 1 | `usbhid`, 03/00/00, Interrupt 04/84 mit 64 Byte |
| Module | `industrialio` bereits geladen; `gs_native` nicht geladen |
| Test-002-Build | passendes vermagic, Abhängigkeit industrialio, keine Autoload-Aliase |
| Speicher | rund 388 GiB frei; private Ergebnisdateien erfolgreich geschrieben |
| Programme | Python, clang, sudo, ksshaskpass, journalctl und Python-evdev vorhanden |
| Kerneljournal | ohne erhöhte Rechte lesbar; Cursor gesichert |

Modul-SHA256:
`10bf827f05cdbff4a5389b47e2fb514a69cdbf604010d5d6439f0cf55eddf0ca`.
Der ursprüngliche Test-001-Build mit SHA256
`6cf68587aa951d95c84ec8bd30f14dd0a751e034ed10c2865eba208c4cd397d8`
liegt weiterhin unter `build/module-history/4e76ff7/`.
Client und Helfer sind im JSON-Nachweis mit ihren aktuellen Hashes erfasst.

Keine sichtbare Deadband-Instanz und keine sichtbaren Handles auf das Zielgerät.
**497 Prozesse waren unprivilegiert nicht vollständig einsehbar.** Das ist kein
Nachweis, dass dort keine offenen Gerätehandles existieren. Vor der später
freigegebenen Übergabe muss diese Prüfung vollständig sein; der Helfer bricht
bei unvollständiger Sicht ab. Heute wurde dafür kein sudo verwendet.

Das gespeicherte Journal enthält bei der 100a-Neuanmeldung um 15:12:25 UTC die
Meldung `hid-generic: ignoring exceeding usage max`. Sie ist auch bei früheren
100a-Neuanmeldungen vorhanden und liegt vor diesem Vorabcheck. Daher wird der
Ausgangszustand ausdrücklich nicht als völlig warnungsfrei bezeichnet. Es wurde
kein nativer Test ausgeführt, dem diese Meldung zugerechnet werden könnte.

Ein früherer Check um 14:51 UTC sah `109c`, Adresse 11, IF0 xpad und IF1 frei.
[tester] bestätigte danach, dass der Funkcontroller durch Inaktivität ausgegangen
war. Nach seiner Bestätigung der erneuten Verbindung wurde obenstehender
100a-Zustand erfasst. Daraus folgt keine allgemeine PID-/Funkzustandsregel.
Die früheren Dateien wurden nicht überschrieben.

Private Originaldaten samt geprüften SHA256:
`build/hardware-tests/002-precheck-20261012T151425513553Z/`.
Sie enthalten auch fremde Kernel-/Prozessinformationen und gehören nicht in Git.

## Grenzen und nächste Freigaben

Die Offline-Prüfung belegt Ablauf- und Fehlerlogik. USB-Timing, blockierende
Kernelaufrufe, tatsächliche evdev-/IMU-Ausgabe, mechanischer Motorstopp und die
Rückkehr aus nativem 109c sind noch nicht hardwarevalidiert. Latest-Sample-
Snapshots sind kein vollständiger IMU-Paketstrom. Die endgültige Auswertung
muss gleichzeitige Eingaben in den Motorfenstern und die Nutzerwahrnehmung aller
vier Motoren separat nachweisen. Gyro-SI-Skalierung und SDL-Freigabe bleiben offen.

Vor einer Ausführung: Ausgangszustand frisch bestätigen; explizite Freigaben
für den manuellen Deadband-Übergang, die native Modulregistrierung, die genau
benannte Übergabe/Sitzung und die jeweiligen Rückwegaktionen einholen. Die
vollständigen Befehlsvorlagen und Abbruchgrenzen stehen im
[Hardwaretest-002-Plan](HARDWARE_TEST_002.md). Es wurde kein Ausführungsmanifest
erstellt und keine dieser Hardwareaktionen begonnen.
