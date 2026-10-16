> Public export: personal tester, host and path references were anonymized. Historical evidence hashes refer to the private originals.

# Hardwaretest 002 — laufende Durchführung

12. Oktober 2026. **Zwischenstand, kein E2E-Abschluss.**
Alle nachstehenden Hardware-/Rechteschritte wurden jeweils konkret freigegeben.
Private Originaldaten bleiben erhalten; keine erneute Hardwareaktion ohne Freigabe.

- 15:31:11 UTC: Vollständiger lesender Prozesscheck unter sudo bestanden.
  100a/Adresse 14, xpad/usbhid; keine Deadband-Prozesse, offenen Ziel-USB-Handles
  oder unlesbaren Prozesse. Beleg: `build/hardware-tests/002-access-check-20261012T153108045307Z/`.
- Manueller Deadband-Start durch [tester]: Übergang zu 109c/Adresse 15, IF0 usbfs,
  IF1 frei. Genau Deadband-PID 53346 hält ein USB-Handle; vollständige Sicht.
  Beleg: `build/hardware-tests/002-deadband-check-20261012T153436792547Z/`.
- Die bekannte einmalige xpad-Submit-Meldung -ENOENT bei 15:34:15.610503 UTC
  liegt vor dem Verschwinden von 100a/14 und vor der 109c-Neuanmeldung.
  Sie wird nicht als pauschale Ausnahme für den späteren nativen Handover verwendet.
- 15:37:30 UTC: gs_native einmal registriert, ohne Geräteübernahme. Deadband
  hält usbfs weiter, kein nativer Knoten. Parameter anschließend lesend bestätigt:
  Port 8-6:1.0, PID 0x109c, Output-Gate an, 135000 ms, 8192/1 LSB/g;
  srcversion 871C78F248057A94E1D682A. Kein START. Beleg:
  `build/hardware-tests/002-module-step-20261012T153513429703Z/`.
- Erster sichtbarer Helferaufruf: sudo authentifiziert, anschließend Eingabe
  `bereit`. Der Helfer in Commit 2805340 akzeptierte ausschließlich `BEREIT`.
  Abbruch um 15:41:04 UTC **vor** Abbindung/Bindung/START und vor Motorbefehlen.
  Beleg: `build/hardware-tests/002-native-20261012T153854695436Z/`.
- Korrektur: Bereitschaft ignoriert Groß-/Kleinschreibung und umgebende Leerzeichen;
  fünf Minuten lokale Bereitschaftsfrist. Leere/verneinende Eingaben bleiben
  abgelehnt. Abbruch wird ohne Python-Traceback ausgegeben. 19 Helferprüfungen
  und drei tatsächliche C-Client-Fälle mit künstlichen Systemaufrufen bestehen.
  Keine Änderung an Kernel, 120-s-Ablauf, Puffern, Impulsen oder Sicherheitsprüfungen.
- Nebenmeldung ksshaskpass: Der sudo-Standardprompt wurde nicht erkannt;
  Anmeldung trotzdem erfolgreich. Das installierte Programm enthält statisch
  das Muster `^Password: $`; ein künftiger freigegebener Aufruf erhält daher
  `sudo -A -p 'Password: '`. Keine Systemkonfiguration geändert.
- [tester] bestätigte eine erneute Funkverbindung. Gespeichertes Journal zeigt
  109c/15 → 109c/16 → 100a/17 → 109c/18. Lesend zuletzt IF0 usbfs, IF1 frei,
  gs_native geladen, keine nativen Knoten und keine protokollierte native Bindung.
  Beleg: `build/hardware-tests/002-reconnect-check-20261012T154545077694Z/`.
  Eine neue Freigabe/Zuordnung muss Adresse 18 verwenden und frische Prüfungen
  einschließen; die alte Adresse 15 darf nicht erneut eingesetzt werden.

## Zweiter freigegebener Versuch und gesicherter Rückweg

- Bereitschaftskorrektur in Commit `e46567e`, neues Manifest für 109c/Adresse 18,
  unverändertes Modul und Client. Der neue Lauf wurde separat freigegeben.
- 15:51:35 UTC: `bereit` erfolgreich akzeptiert. Die anschließende Anweisung
  lautete noch „Release to games und Deadband regulär schließen“.
- 15:51:56,208506 UTC: xpad registriert unter 109c einen Input-Knoten.
  15:51:57,514511 UTC: Disconnect von Adresse 18, Abstand **1,306005 s**.
  Der Helfer wartete noch auf Prozessende/USB-Handle-Freigabe und stoppte
  um 15:51:57,576970 UTC bei fehlendem Port. Keine `binding_action`, kein START,
  keine native Eingabe-/IMU-Erfassung und keine Motorbefehle.
  Beleg: `build/hardware-tests/002-native-20261012T155049076072Z/`;
  vollständige Originaldateien und SHA256-Prüfung erhalten.
- 15:51:59 UTC: automatische Neuanmeldung als 100a/Adresse 19, IF0 xpad,
  IF1 usbhid. Ein `hid-generic: ignoring exceeding usage max` erschien bei der
  HID-Neuanmeldung; keine native Bindung oder native Warnung. Der Helfer änderte
  weder Identität noch Bindung und führte keine automatische Wiederholung aus.
- Separat freigegebenes einmaliges `rmmod gs_native`: erfolgreich um
  15:53:49 UTC. Danach 100a/19 mit xpad/usbhid, gs_native nicht geladen,
  industrialio weiterhin geladen. Nur Deregistrierung im Kerneljournal, keine
  neue Warnung beim Entladen. [tester] bestätigte normale Eingaben im KDE Center.
  Beleg: `build/hardware-tests/002-unload-20261012T155346563451Z/`;
  Journalfortsetzung, Vor-/Nachzustand, Exitcode und SHA256 geprüft.

## Gezielte Korrektur der Übergabeanweisung

Statische Prüfung der installierten Deadband-Dateien; keine Änderung der App:

- `deadband.py:78`: `aboutToQuit` ruft `release_controller()` auf.
- `reader.py:45–55`: `config_wanted=False`, aktives USB-Handle synchron schließen.
- `vendors/gamesir/usb_transport.py:332–352`: Interface freigeben, bisherigen
  Kerneltreiber anhängen, libusb-Handle/Kontext schließen.
- `bridge.py:2693–2701`: „Release to games“ allein setzt das Flag;
  der Prozess bleibt bestehen und liest danach evdev (`reader.py:308–320`).
- Reader/Press-Select sind Daemonthreads (`deadband.py:71–73`), kein Shutdown-Join.
  Die vier genannten installierten Dateien stimmen bytegenau mit dem bekannten
  Forschungsstand `771b28a` überein.

Die neue Ansage verlangt **nur reguläres Schließen des Fensters**, ohne vorherige
Schaltfläche. So entfällt die zusätzliche menschliche Aktion nach Ende der
Heartbeats. Alle Prozess-, Handle-, Identitäts- und Fristprüfungen bleiben bestehen.
Keine Zeitgarantie: `close()` wartet auf den I/O-Lock; laufende Übertragungen und
Prozessende können verzögern. Das gemessene Intervall ist keine Firmware-Zusage.
Ein neuer Start/Modulladevorgang/Testlauf braucht jeweils eine neue konkrete Freigabe.
Die erneute Offline-Prüfung besteht: 19 Helferprüfungen und drei C-Client-Fälle
mit künstlichen Systemaufrufen unter ASan/UBSan, ohne Hardwarezugriffe.

## Dritter freigegebener Versuch: native Bindung und START, Workqueue-Abbruch

- Erneuter Deadband-Start und vollständiger lesender Prozesscheck separat
  freigegeben: 109c/Adresse 20, IF0 usbfs, nur Deadband-PID 57053 mit USB-Handle.
  Beleg: `build/hardware-tests/002-deadband-check-20261012T155718416282Z/`.
- Einmaliges Modulladen separat freigegeben. Eine zunächst falsch gewählte lokale
  Vorprüfung erwartete bereits das geladene Modul und stoppte vor jedem sudo-Aufruf;
  korrigiert auf den dokumentierten Zustand vor dem Laden. Der einzige anschließende
  insmod-Aufruf war erfolgreich. Parameter und Belegung geprüft, keine neue Warnung.
  Beleg: `build/hardware-tests/002-module-step-20261012T155903462232Z/`.
- Neuer Testlauf separat freigegeben, Code `e2776ca`, alter unveränderter Kernelbuild.
  Diesmal Deadband direkt regulär geschlossen. Vor Übergabe Prozess-/Handle-Check
  bestanden; 109c/20 unverändert. xpad-Abbindung um 16:00:39,551533 UTC,
  native Bindung um 16:00:39,566264 UTC, START bestätigt um 16:00:39,881152 UTC.
- 16:00:39,892503 UTC: Kernelwarnung Priorität 4:
  `workqueue: work func gsn_service [gs_native] enqueued on deprecated workqueue. Use system_{percpu|dfl}_wq instead.`
  Helfer stoppt sofort nach Empfang der Warnung, sendet quit/END; Null-Motortransfer
  bestätigt um 16:00:40,237528 UTC. Keine Warnungsausnahme oder Wiederholung.
- Die letzten Statusantworten zählen 25 bzw. 41 IMU-Pakete, `pad=0`, `error=0`,
  `rejected=0`. Keine Samples angefordert (erst ab Sekunde 5 vorgesehen), nur zwei
  Input-Zustandssnapshots, keine echten Input-Ereignisse, keine Motorimpulse.
  **41 erkannte IMU-Berichte belegen Empfang, keinen Sechsachsen-Bewegungstest.**
  Beleg: `build/hardware-tests/002-native-20261012T155928920622Z/`;
  Originale und SHA256 geprüft, vollständiger 120-s-Lauf nicht erreicht.
- Nach END: Disconnect 109c/20 um 16:00:41,340493 UTC; 100a/21 erkannt um
  16:00:42,942557 UTC; xpad/usbhid automatisch wieder gebunden. Eine HID-Parserwarnung
  wie beim vorigen Rückweg, keine weitere native Warnung. Keine Bindungsschreibvorgänge
  durch den Helfer beim Rückweg. [tester] bestätigt normale Funktion im KDE Center.
- Separat freigegebenes rmmod erfolgreich um 16:02:18 UTC; keine neue Warnung beim
  Entladen, gs_native danach nicht geladen. Beleg einschließlich Journalfortsetzung:
  `build/hardware-tests/002-unload-20261012T160215250257Z/`; SHA256 geprüft.

## Offline-Korrektur des belegten Kernelblockers

Vier `mod_delayed_work`-Stellen verwenden jetzt `system_percpu_wq` statt
`system_wq`: Fehlerpfad, Service-Neuplanung, Guide-Ack und START. Der installierte
Zielheader `include/linux/workqueue.h:465` nennt dies ausdrücklich als Ersatz;
`Module.symvers` exportiert das Symbol. Per-CPU-Scheduling, Locks, Fristen,
`cancel_delayed_work_sync`, Bindung und USB-Pakete bleiben unverändert.
Keine neue Warteschlange, Warnungsunterdrückung oder Kompatibilitätsannahme für
andere Kernel. Getestetes Buildziel bleibt ausschließlich 7.2.9-2-garuda.

Der vorherige Build und seine Quellen/Buildberichte bleiben unter
`build/module-history/e2776ca/` mit SHA256 erhalten. Neuer Build:

- Modul-SHA256 `ae7b6947b391fb11fa82d4d5c0c446bb548687b1f7b2f62ef1d522d374792188`
- srcversion `B550E7E3C66CD0ED6C39053`
- `make kernel-analyze`: Build ohne Warnungen, keine Autoload-Aliase,
  checkpatch und vier Clang-Analysen bestanden.
- `make test`: vollständige Grundtests einschließlich 44 Parser- und 19 Helferfälle
  sowie drei C-Client-Fälle bestanden. Keine Hardware bei diesen Prüfungen geöffnet.
- Symbolprüfung des neuen Moduls: `system_percpu_wq`, keine Referenz auf `system_wq`.

Die Korrektur ist bisher nur offline geprüft und braucht einen neuen ausdrücklich
freigegebenen Hardwarelauf. Offen bleiben echte 109c-Gamepad-Ereignisse, alle sechs
bewegten IMU-Kanäle, vier Motorwirkungen und deren gemeinsamer Dauerbetrieb.
Bindung/START, kurzer IMU-Empfang, END/Nulltransfer und die anschließende Rückkehr
zu xpad sind für diesen kurzen Lauf belegt. **Hardwaretest 002 bleibt unvollständig.**

## Vierter freigegebener Versuch: echte Gamepad- und Sechsachsen-Daten

Neuer Deadband-Übergang, lesender Prozesscheck, korrigierter Build aus `14579a4`
und genau ein weiterer Testlauf jeweils separat freigegeben. 109c/Adresse 22,
Port 8-6, IF0 exklusiv nativ nach direktem Schließen von Deadband.
Vorprüfungen: `build/hardware-tests/002-deadband-check-20261012T160640845137Z/`,
Modulladen: `build/hardware-tests/002-module-step-20261012T160743172613Z/`.
Messdaten: `build/hardware-tests/002-native-20261012T160815304829Z/` (SHA256 geprüft).

- Bindung und START erfolgreich. Keine neue Kernelwarnung während der nativen Sitzung;
  die korrigierte Workqueue wird nun auf echter Hardware verwendet.
- 17.146 tatsächliche evdev-Ereignisse: 13.172 ABS, 98 KEY, 3.876 SYN.
  Alle vier Stickachsen −32768…32767, beide Trigger 0…1023, beide D-Padachsen −1…1.
  15 Tastencodes mit Betätigung und Loslassen: 304, 305, 307, 308, 310, 311,
  314, 315, 316, 317, 318 und 704…707. Physische Beschriftung damit nicht vollständig geprüft.
- 4.029 gespeicherte, eindeutig nummerierte IMU-Snapshots (Nummern 319…5630).
  Min/max Gyro G0/G1/G2: −2982…3961 / −1233…2096 / −4233…3518.
  Min/max Accel A0/A1/A2: −7320…8820 / 821…15721 / −9059…6992.
  Alle sechs Rohkanäle ändern sich. Keine Gyro-Skalierung/Achsenzuordnung behauptet.
- Ende bei T+90,015606 s vor jedem Motorimpuls: letzte beobachtete Gamepadänderung
  T+87,083506 s, Zähler 3864. IMU läuft weiter; letzte gespeicherte Sensorzeit
  beim Abbruch 32,2 ms alt. Die Anfangsruhe zeigt bereits pad=0 bei wachsender IMU.
  Das ist mit ereignisabhängigen Gamepadberichten vereinbar; kein belegter Transportstillstand.
- Vier verworfene Pakete gezählt, Ursache/Inhalte aus diesem Statusprotokoll unbekannt.
  Keine Pulse, leere Motoraufzeichnung. END/Null-Motortransfer bestätigt.
- Danach automatische Rückkehr zu 100a/Adresse 23, xpad/usbhid. Bekannte HID-Parserwarnung
  erst bei der Neuanmeldung. gs_native auf neue Einzelfreigabe erfolgreich entladen,
  keine neue Warnung beim Entladen. [tester] bestätigt normale Eingaben im KDE Center.
  Rückweg/Journal: `build/hardware-tests/002-unload-20261012T161328526167Z/`, SHA256 geprüft.

Die bisherige Anleitung nannte Eingaben während der Motorphase nur optional,
während der Helfer jede Sekunde Fortschritt verlangte. Die Chatansage kam zu spät.
Korrektur: schon vor `bereit` die nötige fortlaufende Stickbewegung erklären;
ab IMU-Phase T+70 s anfordern und in Puffer/Motorfenstern wiederholen, bis Schlussruhe.
Das gibt 20 s Vorbereitung vor der Voraussetzung ab T+90 s. Zeitplan, vier
400-ms-Impulse und alle Prüfschwellen bleiben unverändert. Der Abbruch benennt
nun eine fehlende Eingabevoraussetzung und protokolliert Alter/Zähler statt einen
unbewiesenen Transportfehler zu behaupten. 19 Helfer- und drei C-Client-Prüfungen
bestehen erneut. Nutzer wünscht neuen Lauf; jede Hardwareaktion weiter separat.

Offen bleiben alle vier Motorwirkungen und ihr gleichzeitiger Betrieb mit
Gamepad/IMU im vollständigen 120-s-Lauf. Bisherige Originale bleiben erhalten.

## Fünfter freigegebener Versuch: 120 s Transport bestanden, Motorvergleich offen

Lauf aus `743407f` mit dem korrigierten Kernelbuild (SHA256 `ae7b6947…92188`),
109c/Adresse 24, Port 8-6, IF0 nach geprüfter Übergabe exklusiv an gs_native.
Originaldaten: `build/hardware-tests/002-native-20261012T161847612148Z/`;
alle elf Dateien gegen die vorhandenen SHA256-Prüfsummen geprüft.
START bestätigt um 16:20:11,460634 UTC, bei T+0,315143 s.
END/Null-Motortransfer bestätigt um 16:22:11,172533 UTC, bei T+120,027044 s.

- 73.023 tatsächliche evdev-Ereignisse: 50.682 ABS, 140 KEY, 22.201 SYN.
  Alle vier Stickachsen −32768…32767, beide Trigger 0…1023, D-Padachsen −1…1.
  16 Tastencodes mit Betätigung und Loslassen: 167, 304, 305, 307, 308, 310,
  311, 314, 315, 316, 317, 318 sowie 704…707. Die physische Zuordnung der
  zusätzlichen Codes ist damit noch nicht unabhängig bestätigt.
- 5.318 eindeutig nummerierte IMU-Snapshots, Nummern 318…7504; alle sechs
  Rohkanäle variabel. Min/max Gyro G0/G1/G2: −2283…1848 / −1020…2017 /
  −2680…3009. Min/max Accel A0/A1/A2: −4181…8100 / 2026…12348 / −7017…2907.
  Sample-Alter bei Abruf: Median 13,38 ms, maximal 38,67 ms.
  1.869 zwischenliegende Nummern wurden im Latest-Sample-Pfad nicht gespeichert;
  das ist kein Nachweis von USB-Paketverlust. Gyrofaktor/Achsenzuordnung bleiben offen.
- Letzter Status: 22.163 Gamepad-, 7.503 IMU- und fünf verworfene Pakete;
  `error=0`, Sitzung aktiv bis END. Die letzte gespeicherte IMU-Nummer ist 7504.
  Keine neuen Kernelwarnungen oder Fehlerereignisse während der nativen Sitzung.
  Inhalte und Ursache der fünf verworfenen Pakete sind nicht aufgezeichnet.

Genau vier Einzelimpulse zu 100 % und angeforderten 400 ms sowie vier zusätzliche
Stopps wurden akzeptiert. Die protokollierten Clientanforderungen lagen bei T+91,001946 /
96,004422 / 101,002200 / 106,002689 s; Stopps jeweils etwa 0,6 s später.
In den jeweils angeforderten 400-ms-Fenstern ab Clientanforderung liefen Eingabe- und
IMU-Erfassung gleichzeitig weiter:

| Motorbefehl | Input-Ereignisse | IMU-Snapshots |
|---|---:|---:|
| Linker Griff | 558 | 19 |
| Rechter Griff | 522 | 17 |
| Linker Trigger | 525 | 19 |
| Rechter Trigger | 525 | 19 |

Dies belegt gleichzeitigen Datentransport während der angenommenen Motorbefehle,
keine mechanische Wirkung allein durch USB-Erfolg. **[tester] präzisiert: Am linken
Griffmotor war keine Vibration spürbar.** Die übrigen drei
Motorwirkungen wurden für diesen nativen Lauf noch nicht einzeln bestätigt.
`passed_transport_run=true` bedeutet deshalb weiterhin keinen vollständigen
mechanischen E2E-Erfolg. Nächster gezielter Schritt ist ein freizugebender
Vergleich mit Deadbands bestehenden Einzelmotorbefehlen; keine Änderung der
Motorzuordnung oder Firmware auf Verdacht.
Dieser native Lauf enthält Client-/Treiberstatus und keine USB-Rohaufnahme;
ein Vergleich mit neuer Deadband-Aufnahme muss erwartete native Encoderbytes
von tatsächlich aufgezeichneten USB-Paketen unterscheiden.

Ruhegrenzen: T+5–15 s zeigt ruhige IMU-Werte; ab T+15 s deutliche Bewegung,
weshalb die gesamten vorgesehenen 15 s nicht als Ruhekalibrierung gelten.
Der Snapshot zu T+110 s zeigt Sticks `0, −1, 0, −1` und beide Trigger null.
Danach folgen 46 Triggeränderungen bis T+119,471 s; die Schlussphase ist keine
vollständig unberührte Ruheprüfung. Die anfänglichen Input-Nullwerte vor dem
ersten Gamepadbericht sind kein eigenständiger Zentrierungsnachweis.

Nach END automatische Neuanmeldung: Disconnect von 109c/24 um 16:22:12,471513 UTC,
100a/25 erkannt um 16:22:14,073514 UTC, IF0 xpad und IF1 usbhid. Die bekannte
HID-Parserwarnung erschien bei dieser Neuanmeldung nach dem nativen Lauf.
Separat freigegebenes einmaliges Entladen erfolgreich um 16:25:55,476491 UTC;
keine neue Warnung beim Entladen. gs_native danach nicht geladen, industrialio
weiter vorhanden. Rückweg: `build/hardware-tests/002-unload-20261012T162520351695Z/`,
alle sieben Dateien SHA256-geprüft. [tester] bestätigt normale Funktion im KDE Center.
**Hardwaretest 002 bleibt wegen des offenen mechanischen Motorvergleichs unvollständig.**

## Zusätzliche Tastencodes: belegte Softwarezuordnung, physischer Test offen

| Linux-Code | Rohbyte/Maskenbit (0-basiert) | Deadband-Label | Physische Bezeichnung laut Deadband |
|---|---|---|---|
| 704 / BTN_TRIGGER_HAPPY1 | Byte 57, 0x08 | L4 | linke Rücktaste |
| 705 / BTN_TRIGGER_HAPPY2 | Byte 57, 0x10 | R4 | rechte Rücktaste |
| 706 / BTN_TRIGGER_HAPPY3 | Byte 58, 0x01 | L5 | zusätzliche linke Schultertaste |
| 707 / BTN_TRIGGER_HAPPY4 | Byte 58, 0x02 | R5 | zusätzliche rechte Schultertaste |

Nachweis: `src/gs_protocol.c` dekodiert die vier Zusatzbits, `kernel/gs_native_usb.c`
ordnet sie den Linux-Codes zu. Installiertes Deadband `771b28a`:
`vendors/gamesir/models/g7pro/protocol.py:371–396` und
`qml/App/ControllerView.qml:43,392` benennen Bits und Positionen.
Der bisherige native Mitschnitt belegt Press/Release dieser Codes, aber keine
zeitlich einzeln angesagte physische Taste. Daher **noch keine praktische
Zuordnungsbestätigung für [tester]' Controller**. Ein solcher Einzeltest bleibt
ausstehend; der nächste Motorvergleich erhält keine zusätzlichen Tastenphasen.

## Manueller Deadband-Gegencheck nach dem nativen Lauf

[tester] testete anschließend selbst alle vier Motoren in Deadband und bestätigte:
„Alle getestet und alle haben vibriert“. Auch der linke Griff war somit dort
spürbar. Diese Nutzerrückmeldung wurde ohne neue USB-Aufnahme erhoben; Zahl,
Nutzdaten und Stoppzeiten der manuellen Tests sind damit nicht aufgezeichnet.
Sie spricht gegen einen dauerhaft ausgefallenen Motor, erklärt aber die fehlende
Wirkung im nativen Lauf noch nicht.

Anschließend nur lesend aus zwischengespeichertem sysfs geprüft: 3537:100a,
Bus 8, Adresse 27, Port 8-6, IF0 xpad/IF1 usbhid, gs_native entladen.
In der unprivilegierten Prozesssicht kein Deadband-Prozess. Keine neue Aufnahme,
kein Modul- oder Bindungsbefehl. Der wiederholte USB-Motorvergleich bleibt bis
zur konkreten Freigabe vorbereitet.

## Wiederholter Motorvergleich: Vorprüfungen, noch keine Aufnahme

[tester] gab den einmaligen 270-s-Vergleich mit zwölf manuellen Einzeltests und
Passwortabfrage frei. Der Helfer stoppte am 12. Oktober um 16:40:59 UTC bereits
im lesenden `host-before`: `/dev/usbmon8` fehlte, usbmon war nicht geladen.
Beleg außerhalb dieses Repositorys:
`outputs/sprint-002/captures/20261012T164059851184Z-motor-comparison-deadband/`
(relativ zum Arbeitsbereich). 22 Dateien SHA256-geprüft; keine Authentifizierung,
kein Recorderstart, keine PCAPNG-Datei, keine Motorbefehle.

Auf zusätzliche Freigabe „Ja, usbmon laden und einen neuen Anlauf freigeben“
einmal `sudo -A -p 'Password: ' -- /usr/bin/modprobe --first-time usbmon`:
erfolgreich um 16:43:48 UTC. Vorher/nachher identische Controller-Metadaten:
100a/27, Port 8-6, xpad/usbhid, gs_native entladen. Monitorknoten root:root/0600,
Major 234, Minor 8. Beleg: `build/hardware-tests/002-usbmon-load-20261012T164339986720Z/`.

Der ausdrücklich freigegebene zweite Anlauf stoppte um 16:44:09 UTC erneut vor
Authentifizierung und Aufnahme. Der übernommene alte Hosthelfer erwartete fest
235:8 aus Sprint-002-Stufe-2. Kernelregistrierung aktuell: 234 usbmon, 235 iio.
Beleg: `outputs/sprint-002/captures/20261012T164409079141Z-motor-comparison-deadband/`
im Arbeitsbereich. Kein Recorder geöffnet, keine Motorbefehle oder USB-Umschaltung.

Offline korrigiert: neue Kopie der vorhandenen Helfer, nur Host-Metadatenprüfung
an die dynamische Majorregistrierung gebunden; alte Dateien unverändert.
Minor 8, Eigentümer/Rechte, Sysfs-Klasse, Char-Knoten, Subsystem und `uevent`
müssen widerspruchsfrei sein. Alle Sandboxprüfungen und frischen Knotenvergleiche
bleiben erhalten. 13 künstliche Prüffälle bestanden; echte Host-, Identitäts-
und Prozessvorprüfungen danach rein lesend erfolgreich. Keine weiteren
flüchtigen historischen Gerätenummern im Recorder gefunden.
Details und aktuelle Quellhashes: [Vergleichsplan](MOTOR_COMPARISON_PLAN.md).
usbmon bleibt geladen; kein weiterer Modulbefehl, keine automatische Wiederholung.

## Aufgezeichneter Deadband-Vergleich: zwölf erfolgreiche Einzelimpulse

Der nachfolgend ausdrücklich freigegebene Anlauf aus `3c64312` lief am
12. Oktober von 16:52:18 bis 16:56:48 UTC erfolgreich. 57 ursprüngliche
Belegdateien einschließlich 1.067.005.244-Byte-PCAPNG SHA256-geprüft und erhalten.
Zwölf Starts und zwölf eindeutig zugeordnete Nullstopps, jeweils drei pro Motor;
alle 24 Transfers vollständig und erfolgreich, bytegenau passend zum nativen
C-Encoder. [tester] bestätigt: **Alle zwölf waren spürbar und endeten wieder.**

Nach regulärem Deadband-Schließen: 100a/29, Port 8-6, xpad/usbhid, keine
verbliebenen Deadband-/Recorderprozesse; gs_native nicht geladen. [tester]
bestätigt normale Eingaben im KDE Center. Kein automatisches Entladen von
usbmon/industrialio oder neuer Hardwarelauf. Originaldaten bleiben privat.
[Ergebnisse, Quellen, Übergangsfehler und Grenzen](MOTOR_COMPARISON_RESULTS.md).

Die fehlende native linke Griffvibration ist damit nicht erklärt. Kein nativer
USB-Rohmitschnitt vorhanden; gemeinsamer nativer Sequenzzähler gegenüber
getrennten Deadband-Zählern ist eine Vergleichsvariable, keine belegte Ursache.
Auf [tester]' Wunsch ist ein nativer Vergleich mit 60 s pro Motor, drei Impulsen
im 15-s-Abstand und USB-Aufnahme vorgeschlagen. Bestehende 400-ms-Impulsgrenze
bleibt zunächst erhalten. 300-s-Ablaufvariante braucht noch Offline-Anpassung,
Tests und eigene konkrete Hardwarefreigaben. Hardwaretest 002 bleibt offen.

## Offline-Vorbereitung des fünfminütigen nativen Vergleichs

[tester] änderte anschließend die Vorgabe auf **eine Sekunde pro Impuls und
mindestens fünf Sekunden Pause**. Der vorhandene Helfer hat dafür eine eigene
300-s-Variante: 30 s Vorbereitung, vier 60-s-Motorblöcke mit je drei Einzelimpulsen
bei 100 %, 30 s Schlussruhe. Startabstände nominal sechs Sekunden; die reale
Pause beginnt erst nach bestätigtem STOP. Ansagen und Reaktionspuffer bleiben.

Client und Kernel erlauben nun begrenzt 300 s beziehungsweise 315 s sowie
1.000-ms-Impulse; bisherige Standardzeiten bleiben erhalten. Der Encoder bildet
die verbleibende Motorfrist in 10-ms-Einheiten ab. Eine beim endgültigen
Sendeschritt bereits abgelaufene Frist darf keinen neuen Impuls auslösen.
Die frühere 400-ms-Paketfolge bleibt reproduzierbar. Gemeinsamer nativer
Sequenzzähler unverändert; keine unbelegte Ursachenbehauptung.

Die bisher validierte isolierte dumpcap-Kette ist kontrolliert in das Projekt
übernommen: Start vor Übergabe, laufende Recorderkontrolle, höchstens 450 s
Aufnahme und nach END 30 s passiver Nachlauf. Kein usbfs in der Sandbox,
kein automatisches Modul-Laden, kein Moduswechsel- oder Rückbindungsbefehl.

Alle Offline-Prüfungen erfolgreich: 29 Ablaufhelfer-, 31 Recorderadaptertests,
elf Clientfälle, 15 Tests tatsächlicher Kernel-Sendefunktionen mit künstlichem
USB, Bestandsprüfungen und gespeicherte Capture-Regression. Neuer Modulbuild
und statische Analyse ohne Befund. Alter Build und Originalaufnahmen erhalten.
Keine Hardwarezugriffe, aktuellen Geräteprüfungen, privilegierten Schritte
oder neuen Aufnahmen in dieser Vorbereitung. Hardwaretest 002 bleibt offen.

[Ablauf und Freigabeschritte](NATIVE_MOTOR_COMPARISON.md),
[Prüfergebnisse und Artefakthashes](NATIVE_MOTOR_COMPARISON_OFFLINE.json).

## Nativer Fünfminutenvergleich: kontrollierter E2E-Lauf abgeschlossen

Am 12. Oktober wurde nach erneuten Einzelfreigaben der vorbereitete Lauf aus
`4a415cf` tatsächlich ausgeführt. Der vorher rein lesend aufgefallene
dumpcap-Paketgruppencheck war eng begrenzt offline korrigiert worden;
34 Adaptertests bestanden, keine Systemrechte verändert.

Ausgangszustand 100a/31, Port 8-6, xpad/usbhid. Manueller freigegebener
Deadband-Übergang zu 109c/32, exklusive usbfs-Bindung und anschließend separat
freigegebenes Modulladen. Vor dem Übergang erschien auf der alten 100a-Identität
die neue xpad-Meldung `unable to receive magic message: -32`; der gespeicherte
Quellcode ordnet sie einer nicht fatal behandelten Zusatzabfrage zu. Die neue
109c-Konfiguration wurde anschließend erfolgreich geprüft. Ursache des Stalls
nicht bewiesen; keine allgemeine Warnungsausnahme im Helfer eingeführt.

Nach weiterer Freigabe: isolierte USB-Aufnahme, lokale Bereitschaft/Countdown,
reguläres Deadband-Schließen und kontrollierte Übergabe ausschließlich IF0 an
gs_native. START bis END-Bestätigung **300,013 s**, etwa 17:53:12–17:58:12 UTC.
Zwölf einzelne 100-%-/1000-ms-Impulse, je drei pro Motor; mindestens fünf
Sekunden Pause nach bestätigtem STOP. Alle zwölf Impuls- und STOP-Bestätigungen
vorhanden. [tester] bestätigt ausdrücklich: **alle zwölf spürbar und jeweils beendet**.

USB-Nachweis: zwölf erfolgreiche Starts, 24 erfolgreiche Nullpakete, alle
36 Motorpakete vollständig und bytegenau zum C-Encoder. 697 erfolgreiche
native OUT-Transfers mit lückenloser gemeinsamer Sequenz. Während jedes
Impulses liefen GIP und IMU weiter. Insgesamt 34.125 native GIP- und 18.744
IMU-Pakete; 101.995 Linux-Input-Ereignisse, kein SYN_DROPPED, sechs veränderliche
IMU-Rohkanäle. `rejected=15` ist durch vollständige erfolgreiche, bislang
unbekannte Acht-Byte-Reports des Typs 03 erklärt. Keine USB-Fehler oder
gespeicherten Kernelwarnungen im nativen START–END-Fenster.

Nach END Neuanmeldung als 100a/33, IF0 xpad, IF1 usbhid; im Nachlauf bekannte
HID-Warnung. Keine manuelle Rückbindung erforderlich. Separat freigegebenes
einmaliges Entladen des ungebundenen gs_native um 18:01:05 UTC erfolgreich.
[tester] bestätigt normale Funktion im KDE Center. usbmon/industrialio bleiben
geladen. Keine weitere Hardwareänderung, keine Dauerinstallation.

Original-PCAPNG und native Logs unverändert privat gespeichert, SHA256 geprüft.
314.799 Busereignisse, 109.687 Zielereignisse, keine Kürzungen, `ifdrop=0`;
fehlender Betriebssystem-Dropzähler bleibt unbekannt. Vier fehlgeschlagene
URB-Abschlüsse ausschließlich vor START/nach END separat dokumentiert.
Offline-Grundtests nach dem Lauf erneut erfolgreich.

Der kontrollierte E2E-Test ist damit abgeschlossen. Der autonome Start ohne
Deadband bleibt ausdrücklich offen: Deadband lieferte noch den anfänglichen
Identitätsübergang, war während des nativen Betriebs aber geschlossen.
Die Ursache der früher fehlenden 400-ms-Linksmotorwirkung ist nicht geklärt;
die neue 1000-ms-Variante ist erfolgreich, ohne spekulative Sequenzänderung.
Gyrofaktor/Achsenkalibrierung und finale SDL-Sensorfreigabe bleiben offen.

[Vollständiger Ergebnisbericht](NATIVE_MOTOR_COMPARISON_RESULTS.md),
[geprüfte Zielgerätedaten](NATIVE_MOTOR_COMPARISON_RESULTS.json),
[nächster Schritt vor einer Installation](NATIVE_INSTALLATION_READINESS.md).
