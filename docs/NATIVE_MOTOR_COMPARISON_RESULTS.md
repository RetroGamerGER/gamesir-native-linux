> Public export: personal tester, host and path references were anonymized. Historical evidence hashes refer to the private originals.

# Hardwaretest 002: nativer Fünfminutenvergleich abgeschlossen

12. Oktober 2026. Der separat freigegebene Lauf hat **alle vier Motoren mit
je drei Einzelimpulsen erfolgreich geprüft**. [tester] bestätigte alle zwölf
Impulse als spürbar und jeweils beendet. Während jedes Impulses wurden echte
Gamepad-Eingaben und sechs IMU-Rohkanäle verarbeitet. Nach END kehrte das Gerät
zu `3537:100a` und xpad/usbhid zurück; [tester] bestätigte normale Funktion im
KDE Center. Das ungebundene `gs_native` wurde danach separat freigegeben entladen.

Damit ist der kontrollierte E2E-Test einschließlich manueller Deadband-Starthilfe
abgeschlossen. **Ein selbstständiger Start ohne Deadband ist noch nicht
implementiert.** Ebenso wenig folgt daraus eine Freigabe für dauerhafte
Installation, Autoload, weitere Hardwareläufe oder kalibrierte SDL-Sensoren.
[Nächster Entwicklungsschritt](NATIVE_INSTALLATION_READINESS.md).

## Durchführung und unabhängige Nachweise

Quellstand `4a415cf`, Kernel `7.2.9-2-garuda`; Modul und Client unverändert aus
der geprüften Vorbereitung. Modul-SHA256:
`b54a2a76a50b997e90f82cb1003a27f1c4f564a90876a03505562df6c4964127`.
Der unveränderte physische Port war `8-6`, Bus 8, ausschließlich Interface 0.
Der Ablauf folgte dem [freigegebenen Plan](NATIVE_MOTOR_COMPARISON.md):

1. Frische lesende Kontrollen: `100a`, Adresse 31, xpad/usbhid, keine fremden
   Gerätezugriffe. Privilegierte Leseschritte jeweils gesondert freigegeben.
2. Manueller Deadband-Start nach Freigabe: `109c`, Adresse 32, IF0 exklusiv
   usbfs/Deadband, IF1 ungebunden. Keine Einstellungs- oder Motorentests in Deadband.
3. Separat freigegebenes Modulladen mit Ziel IF0/109c, `enable_output=1`,
   `session_ms=315000`; anschließend noch keine native Bindung.
4. Ein genehmigter kombinierter Lauf: isolierter Recorder, lokale Bereitschaft
   und Countdown, Deadband regulär schließen, gezielte xpad-Abbindung und
   native Bindung, START, 300 s mit Puffern, zwölf Impulse, STOP/END, 30 s Nachlauf.
5. Normale Neuanmeldung nach END: `100a`, Adresse 33, xpad/usbhid. Keine manuelle
   Rückbindung nötig. Ungebundenes Modul nach eigener Freigabe einmal entladen;
   Nachkontrolle am 12. Oktober um 18:01:05 UTC erfolgreich. usbmon und
   industrialio blieben geladen. Keine dauerhafte Installation.

START_CALL bis Empfang der END-Bestätigung: **300,013066814 s**. UTC näherungsweise
17:53:12,571–17:58:12,584 (19:53–19:58 Uhr Berlin). Maßgeblich für Ablaufabstände
ist die monotone Hostzeit. PCAPNG enthält Host-USB-Zeitstempel in Mikrosekunden;
die UTC-Zuordnung der Clientzeiten ist eine Übersetzung, keine Geräteuhr.

USB-Capture, native Input-/IMU-Protokolle und Nutzerwahrnehmung sind getrennte
Belege. Zwei Kopien derselben Clientmeldung zählen nicht als unabhängige Messung.
Originale `result.json` bleiben unverändert: ihre damaligen Felder
`motor_perception_confirmed=false` und `xpad_restored=false` wurden erst durch
spätere Nutzerbestätigung und Rückkehrkontrolle ergänzt, nicht rückwirkend geändert.

## Motoren, Stopps und parallele Eingaben

| Physischer Motor | Impulse | Angefordert | USB-Startpakete | Nutzer bestätigt |
|---|---:|---|---:|---|
| Linker Griff | 3 | 100 %, 1.000 ms | 3 erfolgreich | alle spürbar und beendet |
| Rechter Griff | 3 | 100 %, 1.000 ms | 3 erfolgreich | alle spürbar und beendet |
| Linker Trigger | 3 | 100 %, 1.000 ms | 3 erfolgreich | alle spürbar und beendet |
| Rechter Trigger | 3 | 100 %, 1.000 ms | 3 erfolgreich | alle spürbar und beendet |

Alle zwölf Starts und **24 Nullpakete** sind vollständige erfolgreiche
13-Byte-Transfers und stimmen bytegenau mit dem C-Encoder überein. Je Impuls
gab es einen Nulltransfer beim Fristablauf und einen weiteren für den expliziten
STOP. Zwölf Impuls-ACKs, zwölf STOP-ACKs und eine END-Bestätigung sind dokumentiert.
END bestätigt den erreichten Nullzustand; ein zusätzliches Paket war nicht nötig.
Alle zwölf Startpakete enthalten `duration=0x64`, Pause/Wiederholung null.

USB-Submit des Starts bis zum ersten Nullpaket: **999,116–1.007,376 ms**.
Kürzeste bestätigte STOP-Pause bis zum nächsten Client-Impulsbefehl:
**5,000154597 s**; bis zum nächsten USB-Submit **5,000194 s**. Beide Prüfungen
erfüllen die fünf Sekunden. USB-/Hostzeiten messen keine exakte mechanische
Laufzeit. Ein STOP-ACK benötigte 26,350 ms, die übrigen etwa 5,1–5,3 ms;
das ist kein Nachweis entsprechend verlängerter Vibration.

Zwischen Start und erstem USB-Nullpaket liefen je Impuls **396–440 GIP-Berichte
und 61–63 IMU-Berichte** weiter. Die engeren Clientfenster zwischen Impuls-ACK
und STOP-Aufruf enthalten je 1.177–1.323 Input-Ereignisse und 44–47 IMU-Snapshots;
alle sechs Rohkanäle waren jeweils vorhanden und veränderlich.

Gesamte native Sitzung:

- **34.125 GIP-Berichte**, **18.744 IMU-Berichte** im Rohmitschnitt, mit
  erfolgreichem Vergleich der Feldwerte zwischen C-Kern und Python-Parser.
- **101.995 Linux-Input-Ereignisse**, kein `SYN_DROPPED`.
- **13.634 IMU-Snapshotzeilen**, 13.633 unterschiedliche Samplezähler;
  keine rückläufigen Zähler/Zeitstempel. Die Abfrage liefert Momentaufnahmen,
  nicht jedes USB-Paket. Der Rohmitschnitt erhält den vollständigen Stream.
- 1.118 Statuszeilen mit `state=1`, `error=0`, `output=1`. Letzte Zähler vor
  END: Pad 34.125, IMU 18.731, rejected 15. Genau diese Zahlen sind auch im
  Capture bis zu diesem früheren Statuszeitpunkt vorhanden.
- Alle **697 nativen OUT-Transfers** erfolgreich und vollständig: drei
  Initialisierungen, 658 Heartbeats, 36 Motorpakete. Gemeinsame Sequenz lückenlos
  einschließlich zweier Überläufe; kein separater Motorzähler erforderlich,
  um diesen erfolgreichen Lauf zu erklären.

IMU-Abschlussintervalle: Median 16 ms, etwa 62,476 Hz über die beobachtete
Reportspanne. GIP-Median 2 ms, mit langen eingabefreien Pausen. Daraus folgt
weder eine konstante Gamepad-Pollingrate noch die interne Sensor-Abtastrate.
Dieser Motorvergleich ersetzt keine erneute vollständige Tasten-/Triggerprüfung
oder Stick-Ruhekalibrierung; entsprechende frühere Eingabetests bleiben separat.

## Fehler und Grenzen

Die 15 vom Treiber als `rejected` gezählten Eingaben sind **vollständige,
USB-erfolgreiche Acht-Byte-Berichte** `03 20 SS 04 87 00 00 00`, Sequenzen
`1d` bis `2b`, ungefähr alle 20 s. Beide Decoder erkennen Typ `03` noch nicht.
Keine fehlerhaften Nutzdaten oder Übertragungsfehler daraus ableiten;
eine mögliche Statusbedeutung bleibt unbewiesen.

Im nativen START–END-Fenster: **keine fehlgeschlagenen Zielgerät-URBs und keine
gespeicherten Kernelwarnungen**. Vier fehlgeschlagene Zielgerät-Abschlüsse im
gesamten Capture liegen außerhalb dieses Fensters: `-ENOENT` bei −0,150 s,
`-ESHUTDOWN` bei −0,038 s und +301,482 s sowie `-ENOENT` bei +303,242 s.
Sie bleiben als Übergangs-/Abbauereignisse erhalten und werden nicht als
erfolgreiche Datenübertragungen gezählt.

Vor der Aufnahme, beim manuell freigegebenen Deadband-Übergang, erschien an der
alten 100a-Identität zusätzlich `unable to receive magic message: -32`.
Die gespeicherte xpad-Quelle ordnet dies der optionalen Vendor-IN-Abfrage in
`xpad_start_input` zu; der Abfragefehler beendet diese Initialisierung nicht
mit einem Fehlercode. Die Trennung des alten Geräts folgte rund 0,36 ms später.
Das erklärt die Fundstelle, beweist aber keine Ursache des Stalls. Der neue
109c-Zustand wurde anschließend erfolgreich geprüft. Keine allgemeine Ausnahme
für solche Warnungen im nativen Testhelfer eingeführt. Nach END trat beim
100a-HID-Interface die bereits bekannte Warnung `ignoring exceeding usage max`
auf; xpad und KDE-Eingaben waren anschließend funktionsfähig.

Der frühere native 400-ms-Lauf hatte keine spürbare linke Griffvibration.
Der neue Lauf verwendet 1.000 ms; der gemeinsame Sequenzzähler blieb erhalten.
**Die damalige Ursache ist damit nicht kausal geklärt.** Der gespeicherte
Deadband-Vergleich hatte 400 ms und einen Nulltransfer pro Impuls, der neue
native Lauf 1.000 ms und zwei. Erfolg des neuen Ablaufs ist belegt,
eine bestimmte Fehlerursache oder Reparatur daraus nicht.

Gyrofaktor, physikalische Achsenorientierung/Bias und finale SDL-Ausgabe bleiben
offen. 8192 LSB/g bleibt ausdrücklich experimentell. Zusatztastencodes werden
durch diesen Motorvergleich nicht neu physischen Tasten zugeordnet. Dauerbetrieb,
Suspend, Hotplug, unerwarteter Funkverlust und ein autonomer Start brauchen
weitere Implementierung beziehungsweise eigene freigegebene Tests.

## Speicherung, Integrität und Offline-Regression

Projektrelative private Belegpfade:

- `build/hardware-tests/002-native-motor-comparison-20261012T175050895176Z-run/`:
  unveränderte native Logs, `result.json`, `SHA256SUMS` und `usb-capture/`.
- Darin `usb-capture/original-usbmon8.pcapng`: **1.375.197.976 Byte**,
  347,341978 s vom ersten bis zum letzten Paket, 314.799 Busereignisse,
  davon 109.687 dem Zielgerät zugeordnet. Epochen `109c/32 → 100a/33`;
  der vorherige Übergang `100a/31 → 109c/32` liegt vor der Aufnahme.
- Gleichnamiger `-control/`-Ordner: Freigabe, Terminalprotokoll und
  spätere Nutzerbestätigung; `-run-analysis/`: separate Offline-Ableitungen.
- `build/results/native-motor-client-analysis-20261012.json`: Clientauswertung.
- `build/hardware-tests/002-native-motor-module-unload-20261012T180059111239Z/`:
  autorisiertes Entladen, Vor-/Nachprüfung und KDE-Bestätigung.

Original-PCAPNG-SHA256:
`ec53d79ba5ee46ccefb4df2cc1b6c67c0d083eafdf6e1d3a52258e80a338d998`.
Alle geprüften Original-Prüfsummen stimmen. Keine gekürzten Frames;
Recorderzähler `ifdrop=0`, `osdrop` nicht enthalten und daher unbekannt.
Sandboxprüfungen vor/nach Aufnahme erfolgreich, ausschließlich usbmon8 ohne
usbfs, keine Änderung der Host-Mounts, Namespaces oder Geräteknotenrechte.
Der gemeinsame Busmitschnitt bleibt privat und wird weder committet noch hochgeladen.

Die erste separate Offline-Auswertung hatte im GIP-C-Vergleich eine falsche
Enumzahl verwendet; die Ableitung wurde anhand des vorhandenen Headers
korrigiert und vollständig nachgeprüft. Original und erste Ableitung blieben
erhalten. Maßgeblich ist `compact-target-results-reviewed.json`, ergänzt um
`supplementary-out-audit.json`, jeweils mit eigener Prüfsummenkette. Kein
Treiber- oder Protokollfehler war dafür verantwortlich.

Nach dem Hardwarelauf erneut **`make test` erfolgreich**: 44 Parsertests,
Sensor-/Protokoll-/Runtime- und Fixture-Prüfungen, Kernelmapping, 15 synthetische
Motor-Sendefälle, Client-Selbsttest, 29 Ablaufhelfertests, elf synthetische
Clientfälle und 34 Recorderadaptertests. Kein erneuter Hardwarezugriff.
Früherer Modulbau und statische Analyse: [Offline-Nachweis](NATIVE_MOTOR_COMPARISON_OFFLINE.json).
Kompakte geprüfte Zielgerätedaten: [Ergebnis-JSON](NATIVE_MOTOR_COMPARISON_RESULTS.json).
