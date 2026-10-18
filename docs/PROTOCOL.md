> Public export: personal tester, host and path references were anonymized. Historical evidence hashes refer to the private originals.

# Protokoll, Beleglage und Quellen

Bytepositionen sind nullbasiert. Die Offline-Tests verarbeiten gespeicherte Dateien;
spätere Hardwarebelege sind ausdrücklich bezeichnet.
Capture-SHA256:
`4045577a7a9e7a1a0f84307a45e96fd524cd7dea1d4af276ebd7db20a0994a89`.
Das vollständige Original bleibt privat außerhalb des Repositorys.

**Experimenteller 105e-Pfad ab Alpha3:** Der ZZZ-Dongle verwendet im Quellcode
dieselben GIP-/IMU-/Viermotorformate, mit direkter Initialisierung statt des
100a→109c-Übergangs. Seine Interface-/Endpunktmerkmale sind lesend bestätigt;
die Paketgleichheit und native Funktion noch nicht. Die folgenden Captures
bleiben Belege des ersten Exemplars und werden nicht als 105e-Messdaten
umetikettiert. [Details](G7_PRO_VARIANTS.md).

## Im Sprint-002-Mitschnitt belegt

VID `3537`, PIDs `100a`/`109c`; Aufnahme enthält `100a → 109c → 100a`.
Die Identitäten allein beweisen weder Funkverbindung noch Treiberbindung.
Der normale Rückkehrzustand wurde separat mit Interface 0 `xpad` und
Interface 1 `usbhid` geprüft.

| Typ | Richtung/Länge | Struktur |
|---|---|---|
| XInput | IN 0x82, 20 Byte | `00 14`; Tasten 2/3; 8-Bit-Trigger 4/5; vier signed-LE16-Sticks ab 6 |
| GIP | IN 0x82, 36 Byte | `20 00 seq 20`; Tasten LE16 ab 4; Trigger LE16 ab 6/8 (0..1023); Sticks signed-LE16 ab 10 |
| IMU | IN 0x82, 64 Byte | Typ `10`, Byte 3 `3c`, Byte 4 `e0`; Gyro signed-LE16 ab 17/19/21; Accel ab 23/25/27; Zusatztasten 57/58 |
| vier Motoren | OUT 0x02, 13 Byte | `09 00 seq 09 00 0f LT RT LG RG duration pause repeat` |
| Wartung | OUT 0x02, 64 Byte | `0f 00 seq 02 f2...` Heartbeat oder `0f 00 seq 01 selector...` Abfrage |
| Identitätsübergang | OUT, neun 8-Byte-Pakete | fünf `00 08 00 <Wort> 00 00 00`, dazwischen vier leere Flush-Pakete; Wörter `ga`, `me`, `si`, `ra`, `pp` |

Motorwerte liegen in 0..100. Der geprüfte Builder verwendet bei aktiven
Motoren Dauer `0x28`, sonst null; Pause/Wiederholung sind null. Die Deutung
40 × 10 ms ist quellengestützt; Paketbytes sind capturebestätigt, exakte
mechanische Laufzeit wurde nicht vermessen. Der C-Kern erstellt nur Bytes.

Der [native Motorvergleich](NATIVE_MOTOR_COMPARISON_RESULTS.md) belegt inzwischen
zwölf vollständige erfolgreiche Ein-Sekunden-Startpakete: `duration=0x64`, Pause
und Wiederholung null. Alle zwölf Impulse waren laut Nutzer spürbar und endeten.
Die 10-ms-Einheit ist quellengestützt; eine exakte mechanische Zeitmessung fehlt.
Der zeitbehaftete Encoder verwendet die verbleibende Frist (auf zehn ms
aufgerundet). Die ursprüngliche 400-ms-Funktion bleibt für Referenzaufnahmen
erhalten. Im nativen Lauf sind 697 OUT-Pakete mit gemeinsamem Sequenzzähler
lückenlos einschließlich zweier Überläufe erfolgreich; darunter 36 bytegenau
geprüfte Motorpakete (zwölf Starts, 24 Nulltransfers). Dies beweist keine
allgemeine Firmwarevorgabe für die Sequenzzähler anderer Implementierungen.

Der gleiche Lauf enthält 15 vollständige erfolgreiche Acht-Byte-Eingaben
`03 20 SS 04 87 00 00 00`, ungefähr alle 20 s. C- und Python-Decoder behandeln
sie als unbekannt. Sie erklären dort den Zähler `rejected=15`; ihre Bedeutung
ist weiterhin unbestimmt, kein Nachweis eines Transportfehlers.

XInput-Trigger werden mit `(v*1023+127)/255` normalisiert; Stick-Rohwerte
bleiben erhalten. Spätere Input-Ausgabe muss übliche Y-Achsen-Semantiken
bewusst umsetzen. IMU-Rohachsen sind keine kalibrierten SDL-Achsen.

Vollvergleich: 1.458 XInput, 3.786 GIP, 12.204 IMU, zehn Motorpakete,
neun Übergangspakete und 521 Wartungspakete. 14 fehlerhafte/abgeschnittene
Datensätze werden übersprungen; elf unbekannte Eingaben bleiben unbekannt.
Andere Herstellerantworten werden nicht als IMU umgedeutet.

`fixtures/sprint002-target.json` enthält sieben erfolgreiche Zielgerätepakete,
drei GIP-Initialisierungen
und neun Übergangspakete, mit Quellzeilen/Prüfsummen. Seriennummern,
Busadressen, absolute Zeiten und fremder Verkehr sind nicht enthalten.
Künstliche Parser-Fixtures in `tools/offline/fixtures` bleiben getrennt.

## Physische Zusatztasten

Die Alpha-Aktivierung am 13. Oktober 2026 erfasste isolierte evdev-Ereignisse
für alle vier Zusatztasten. [tester] korrigierte anschließend seine zunächst
bestätigte Bedienung: Bei den Ansagen hatte er L4/L5 und R4/R5 vertauscht
gedrückt. Die physische Spalte beruht auf dieser ausdrücklichen Korrektur;
Byte-/Bitpositionen stammen aus dem unveränderten Decoder und Kerneladapter,
nicht aus einem neuen USB-Mitschnitt.

| Physische Taste | Linux-Code | Telemetriebyte / Bit |
|---|---|---|
| L4 | 704 / BTN_TRIGGER_HAPPY1 | 57 / 3 |
| R4 | 705 / BTN_TRIGGER_HAPPY2 | 57 / 4 |
| L5 | 706 / BTN_TRIGGER_HAPPY3 | 58 / 0 |
| R5 | 707 / BTN_TRIGGER_HAPPY4 | 58 / 1 |

Alle vier Codes sind unabhängig von normalen Xbox-Tasten. Rohfenster,
Nutzerkorrektur und Grenzen: [Aktivierungsbericht](ALPHA_INSTALLATION.md#eingaben-und-korrigierte-physische-tastenbeschriftung).
Die konkrete Anwendung muss sie weiterhin selbst erkennen und frei belegen
können; die Codezuordnung beweist keine Embercade-/Steam-Integration.

## Initialisierung und weiterhin nur quellengestützter Guide-Pfad

GIP-Guide/Acknowledge ist im C-Kern vorbereitet, im aktuellen Capture nicht
beobachtet. Die drei GIP-Initialisierungstypen sind dagegen inzwischen gegen
alle 21 Vorkommen im vorhandenen Capture bytegenau geprüft. Ihr Ablauf
verwendet Längen 5/7/6 und sequenzierte Header 05/0a/06 mit Option 20.
Allgemeine GIP-Varianten werden dadurch nicht freigegeben: aktuell ist nur
das beobachtete 36-Byte-Eingabelayout aktiviert.

Fixierte Quellen, Hashes und Fundstellen: `tools/offline/docs/source-map.json`
und `imu-calibration-analysis.json`:

- [Deadband G7-Pro-Protokoll, Commit 771b28a](https://github.com/broroeror/gamesir-linux-tools/blob/771b28ae75b0a614a6a7fec9aa606606a27b3b8d/vendors/gamesir/models/g7pro/protocol.py)
- [Linux xpad, fixierter Commit](https://github.com/gregkh/linux/blob/5fce161649b4d779d1b76d9fcd52dc77779774b8/drivers/input/joystick/xpad.c)
- [g7ctl-Sitzungslogik, Commit 0ea4b52](https://github.com/questionablesyntax/g7ctl/blob/0ea4b5223ba2191c88a3c4d1ff8d34f594bfeb1b/pyg7/session.py)

Verweise stammen aus der vorhandenen lokalen Recherche. Drittcode wird
bei Tests nicht importiert oder ausgeführt.

## Skalierung und offene Fragen

**Experimentell:** Beschleunigung 8192 LSB/g; Standardgravitation 9,80665 m/s²,
Ausgabe µm/s² in Rohachsenfolge. Austausch über `sdl-sensor-calibration.json`.

**Externer Sensorhinweis:** [tester] bestätigt am 16. Oktober die DigiKey-
Fotoauskunft LSM6DSO/LSM6DSOTR, stellt die exakte Variante danach aber
infrage. Als Auskunft erhalten, Modell wieder offen; Herkunft und Grenzen in
[imu-sensor-identification.json](imu-sensor-identification.json). Originalfoto
und Vendorantwort wurden hier nicht unabhängig geprüft; weitere PCB-Revisionen
oder Varianten sind dadurch nicht identifiziert.

**Offline-Registerreferenz:** Das gespeicherte Linux-ST-Modul belegt für
LSM6DSO WHO_AM_I `0x0f`/`0x6c`, Gyroregister `0x11` mit Maske `0x0c` und
vier Gewinne passend zu 8,75/17,5/35/70 mdps/LSB. Das sind Linux-Referenzwerte,
keine GameSir-Registermessung oder USB-Befehle. Zum damaligen Suchstand war
kein Initialisierungspfad/aktiver Wert belegt; der gesonderte ±125-Modus
ist in dieser Vierertabelle nicht abgedeckt. [Fundstellen und Grenzen](IMU-STATISTIK-UND-SENSORIDENTIFIKATION.rst).

**Vorheriger Strukturpass:** Positionsabhängige Dateidekodierung und
288 Header-/48 Bereichs-/96 Datei-CRC bestätigen `app.bin`/`cfg_tool.bin`.
Lesbare Sensorwahl-/Kalibriermeldungen sind neue statische Anker. Weder
LSM6DS3TR-/QMI8658-Namen noch `gyro factory` belegen den real ausgewählten
Sensor, einen aktiven CTRL2_G-Wert oder eine USB-Skalierung. Damals blieben
MCU-Befehle und Datenfluss offen. [Format- und CRC-Nachweise](GAMESIR_NEXUS_RESEARCH.md).

Der damalige MCU-Pass erhärtete nur drei Teilformen und einen gemeinsamen
Textausgabe-Zielkandidaten; keine vollständige ISA oder Sensor-Schreibroutine.
Die lokale Linux-Referenz bestätigt WHO_AM_I `0x0f`→`0x6a` für TR-C und
`0x6c` für DSO, bei gleichen Referenzgewinnen. Dabei wurde noch kein
GameSir-ID-Lese-/Vergleichspfad oder aktiver CTRL2_G-Wert gewonnen.
Byte-/Namenstreffer sind keine Chipidentifikation.

**Aktueller statischer Firmwarebefund:** Die spätere
[Initialisierungsanalyse](JIELI_SENSOR_INITIALIZATION.md) identifiziert in
drei Apps einen ST-Kandidaten mit Vergleich `0x6a` und Schreibvorbereitung
`0x11 ← 0x6c`, `0x10 ← 0x68`. Der
[Datenflusspass](JIELI_SENSOR_REPORT_DATAFLOW.md) stützt Achsenumordnung,
bedingten Offset-Abzug und die Zuordnung zu den Positionen 17–27 eines
`10/3c/e0`-Berichtskonstruktors. Im untersuchten ST-Ausgabeabschnitt keine
zusätzliche Gyro-Verstärkung. Der [Transportfolgepass](JIELI_USB_TRANSPORT.md)
ordnet den Kopieraufruf dem SDK-ROM-Stub `memcpy`/`memmove` zu. Die
Controller-Queue hat mehrere Verbraucher. Der neue
[Funkrahmen-Folgepass](JIELI_WIRELESS_DATAFLOW.md) verbindet einen beidseitig
passenden `A2`-/Queue-Pfad mit dem Dongle-Sendepuffer für IN `0x82`; in den
geprüften Transportkopien keine weitere Sensorrechnung. Aktive Callback-
Anbindung/untere Funkstrecke, Halfword-/Vorzeichenformen und tatsächlich
aktive Konfiguration bleiben offen. Unter der ST-Annahme ist
`0,07 Grad/s je Sensorzählwert` weiterhin ein Kandidat, kein bestätigter
USB-Faktor. Die unten genannten Unbekannten
beziehen sich auf den realen Controller; der Parser und seine Rohachsen
werden durch diese statischen Erkenntnisse nicht umgestellt.

**Unbekannt:** aktiver Gyro-Messbereich und Gyro-LSB/(°/s) am USB-Report,
vollständige Achsen-/Vorzeichenabbildung, bestätigte Offsets, Geräteuhr und
interne Abtastrate. Ein Foto-Typnachweis bestimmt keine Firmware-Skalierung.
16 oder 16,4 LSB/(°/s) in Tests sind ausschließlich künstliche Referenzen.
8192 wird niemals als Gyrofaktor verwendet.

Median der IMU-Host-Abschlussintervalle: 16 ms; beobachtet etwa 62,53 Hz.
Pollingrate 1000 Hz belegt keine IMU-Ausgabe mit 1000 Hz. Bewegungsaufforderungen
beweisen keine tatsächlich ausgeführte Richtung. Statistik und Einschränkungen:
`IMU-STATISTIK-UND-SENSORIDENTIFIKATION.rst`.

## Nexus: getrennte statische Forschungsreferenz

Der [Nexus-Bericht](GAMESIR_NEXUS_RESEARCH.md) mit
[Quellhashes und Fundstellen](nexus-source-manifest.json) belegt einen
zusätzlichen SDK-Updatepfad, Geräteversions-API und Motion-/Kalibrierungs-UI.
Diese statischen Befunde erweitern nicht die oben capturebestätigten
Laufzeitformate. Keine Updatefragmente oder WebView-Kalibrierparameter als
freigegebene USB-Abfragen übernehmen. Kein neuer Gyrofaktor, IMU-Chip oder
Bootloader-/Firmware-Rückweg bestätigt. Herstellerfirmware bleibt privat;
gemeinsamer Variantenkern, experimentelle 8192 LSB/g und SDL-Grenzen bleiben.

Die [native Sensor-Fortsetzung](NEXUS_SENSOR_DATAFLOW.md) belegt sechs
aufgelöste Int32-Feldzugriffe ohne Skalierung. In sieben geprüften Eingabe-
Zustandspfaden bleiben diese Felder null; C2-Profilbytes und /255-Kurvenwerte
sind Konfiguration. Die namentliche Zuordnung zu `D4X.SendMessage` macht
die Kalibrierungsnutzbytes noch nicht zu validierten USB-Kommandos. F1 ist
eine JL-Firmwarebridge; MessageC und weitere indirekte Provider bleiben als
mögliche Sensorpfade offen. Weder vollständige Header-/Modellzuordnung noch Gyrofaktor
oder globale Abwesenheit einer Umrechnung sind bewiesen. Keine neue
Laufzeitfunktion oder SDL-Sensorausgabe daraus aktiviert.
