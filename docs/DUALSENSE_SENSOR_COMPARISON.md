# DualSense-Sensorausgabe als Referenz für GameSir

Stand: 15. Oktober 2026. Ausschließlich lokale Offline-Quellcodeprüfung;
keine Geräteöffnung, Messung, Ausführung fremden Quellcodes oder Änderung der
installierten Alpha. Dieser Bericht ergänzt die vorhandenen
[SDL-Ergebnisse](SDL-SENSOR-ERGEBNIS.rst) und
[GameSir-Kalibriergrenzen](SDL-SKALIERUNG-UND-ACHSEN.rst).

**Empfehlung:** IIO für unveränderte GameSir-Rohdaten behalten. Für SDL später
ein zusätzliches, getrenntes evdev-Sensorgerät aus demselben empfangenen
IMU-Paket versorgen. Dessen Freigabe benötigt eine eigenständige belegte
Gyroskop-Skalierung sowie bestätigte Achsen, Vorzeichen und Offsets. Die
experimentellen 8192 LSB/g bleiben austauschbar; sie bestimmen weder den
Gyrofaktor noch den verwendeten Sensorchip. Hier wird kein Sensorinterface
implementiert oder aktiviert.

## Quellenstand und Beweisgrenzen

- Offizieller Linux-Treiber `drivers/hid/hid-playstation.c`: gespeicherter
  Snapshot von `torvalds/linux`, Commit
  `a5ebb76233b79db01e82e061173cb73c6d2b5c6b`, laut lokalem `snapshot.json`
  vom 10. Oktober 2026. Das ist die geprüfte Referenz, kein Nachweis des
  heutigen Upstream-HEAD oder des genauen Garuda-Quellstands.
- SDL3-Release `3.4.18`, Commit
  `829a65d769d935c4852f8159e964312c0957260a`, mit vorhandenem
  [portablen Quellmanifest](sdl-source-manifest.json). Das ursprüngliche lokale
  Prüfmanifest mit Maschinenpfaden bleibt unverändert außerhalb von Git und Paket.
  Die lokalen installierten
  Header nennen weiterhin diese Revision. Die drei unten genannten
  Release-Quelldateien stimmen mit ihren gespeicherten SHA256-Werten überein.
- Zusätzlich gelesene lokale Datei `research/sdl3/src/joystick/linux/SDL_sysjoystick.c`:
  `IsSensor`, `ConfigJoystick`, `GetSensor`, `LINUX_JoystickSetSensorsEnabled`,
  `CorrectSensorData`, `PollAllSensors` und `HandleInputEvents` sind gegenüber
  dem Release in den geprüften Funktionsabschnitten bytegleich. Der gesamte
  Backend-Code ist nicht bytegleich. Das Verzeichnis besitzt ältere
  Snapshot-Metadaten, enthält aber auch später ergänzte Quellen; deshalb wird
  diese Datei ausschließlich durch den unten angegebenen SHA256 identifiziert
  und keinem ungeprüften Upstream-Commit zugeordnet. Die externen SDL-Links
  beziehen sich auf die per Dateimanifest bestätigte Release-Quelle.
- GameSir-Codebasis des Vergleichs: Commit
  `9e8e531be09f5703cbba3460cabe2197dfea6a4b`, insbesondere
  `kernel/gs_native_usb.c`, `src/gs_sensor.c` und `src/gs_sensor.h`.
  Laufende unabhängige Bootstrap-Diagnosen werden hierdurch nicht verändert.

Alle externen Links unten sind versionsgebundene Fundstellen. In diesem
Arbeitsgang wurde kein Netzwerkzugriff durchgeführt; Repository/Commit-Zuordnung
stammt aus den vorhandenen lokalen Metadaten. Die Hashes am Ende identifizieren
die tatsächlich gelesenen Dateien.

## 1. Wie hid-playstation Gyro und Beschleunigung liest und kalibriert

`dualsense_parse_report()` akzeptiert den vollständigen USB-Report mit ID
`0x01` und 64 Byte beziehungsweise den Bluetooth-Report mit ID `0x31` und
78 Byte; Bluetooth wird zusätzlich auf CRC geprüft. Beide Sensortypen
kommen zusammen mit normalen Eingaben im selben HID-Bericht an. Je drei
Little-Endian-Werte werden als vorzeichenbehaftete 16-Bit-Zahlen interpretiert.
Dies ist ein Sony-HID-Pfad, kein GameSir-GIP-Decoder. [PS-Eingang]

Vor der Sensorregistrierung fordert `dualsense_get_calibration_data()` den
Sony-Feature-Report `0x05` mit 41 Byte an. Darin stehen pro Gyroachse Bias
und positive/negative Referenzwerte, zwei Drehgeschwindigkeitsreferenzen
sowie die positiven/negativen Beschleunigungsreferenzen. Der Treiber berechnet
aus diesen Daten achsenspezifische rationale Verstärkungen. Ein fehlgeschlagener
Reportabruf bricht die DualSense-Erzeugung ab. Ein Nullnenner einzelner Achsen
führt dagegen zu einer Warnung und einer Sony-spezifischen Ersatznormalisierung;
das beweist keine allgemeine Kalibrierung beliebiger IMUs. [PS-Kalibrierung],
[PS-Erzeugung]

Für Gyro gilt im geprüften Code, mit `p/m` als Referenzmessungen und `b` als
ausgelesenem Referenzbias:

```text
gain_i = (speed_plus + speed_minus) * 1024
         / (abs(p_i - b_i) + abs(m_i - b_i))
evdev_gyro_i = mult_frac(gain_numerator_i, raw_gyro_i, gain_denominator_i)
```

**Wichtige Präzisierung:** Der ausgelesene Gyrobias geht hier in den Nenner
ein. Der Treiber setzt den gespeicherten Gyrobias auf null und zieht im
DualSense-Laufzeitloop keinen Gyrobias vom Rohwert ab. Daraus folgt weder,
dass GameSir keinen Bias benötigt, noch ein Nachweis einer Bias-Korrektur in
GameSirs Firmware. Für Beschleunigung wird der Bias dagegen ausdrücklich
abgezogen: `range_i = plus_i - minus_i`,
`bias_i = plus_i - range_i/2`, Verstärkung `2*8192/range_i`.
Die Laufzeit benutzt `mult_frac` und die kalibrierten Achsencodes. [PS-Kalibrierung],
[PS-Sensorausgabe]

**GameSir-Vergleich:** `gsn_imu()` erhält bereits sechs dekodierte Rohkanäle,
bewahrt Gyro und Accel unverändert und erstellt nur zusätzlich eine ausdrücklich
experimentelle Accel-Umrechnung. Der vorbereitete gemeinsame C-Kern kann Bias,
Vorzeichen, Permutation und rationale Verstärkung anwenden, verlangt für den
strengen Pfad aber bestätigte Metadaten. Ein verifiziertes GameSir-Profil ist
nicht vorhanden. [GameSir-Kalibrierprofil](sdl-sensor-calibration.json),
`src/gs_sensor.c:41–97`, `kernel/gs_native_usb.c:389–413` im genannten Commit.

## 2. Achsen, Vorzeichen, Skalierung, Auflösung und Zeitstempel

| Aspekt | Geprüfter DualSense-Treiber | Konsequenz für GameSir |
| --- | --- | --- |
| Beschleunigungsachsen | Reportelemente 0/1/2 → `ABS_X/Y/Z` | GameSir A0/A1/A2 noch nicht ohne Messbeleg zu SDL-X/Y/Z erklären. |
| Gyroachsen | Pitch/Yaw/Roll → `ABS_RX/RY/RZ` | G0/G1/G2 separat vorzeichenrichtig zuordnen. |
| Vorzeichen | Kein zusätzlicher Vorzeichenwechsel im DualSense-Sensorloop; Reportkonvention und Kalibrierung bestimmen die Ausgabe. | Sony-Vorzeichen nicht übernehmen; Gamepad-Stick-Y-Inversion ist keine IMU-Achsenregel. |
| Accel-Auflösung | Normalisierte Ausgabe `8192` Einheiten/g, deklarierter Bereich ±4 g | Die gleiche Zahl wie unser experimenteller Wert ist kein GameSir-Skalierungs- oder Chipnachweis. |
| Gyro-Auflösung | Normalisierte Ausgabe `1024` Einheiten/(°/s), deklarierter Bereich ±2048 °/s | `1024` ist keine aus diesem Code ableitbare pauschale Rohsensitivität des Chips. Nicht auf GameSir übertragen. |
| Rauschfilter | Sensorachsen `fuzz=16`, `flat=0` | Filter und Quantisierung für GameSir anhand eigener Daten bestimmen. |
| Gerätezeit | 32-Bit-Geräteticks in nominell 1/3 µs, zu µs akkumuliert und als `MSC_TIMESTAMP` gemeldet | Für GameSir ist kein solcher Takt belegt; Hostzeit ausdrücklich Hostzeit nennen. |

Fundstellen: [PS-Grenzen], [PS-Kalibrierung], [PS-Input-Sensor], [PS-Sensorausgabe].
`input_absinfo.resolution` beschreibt bei `INPUT_PROP_ACCELEROMETER` Einheiten/g
beziehungsweise Einheiten/(°/s), nicht die Zahl der ADC-Bits und nicht die
Abtastrate. Das ist auch im lokal gelesenen Linux-UAPI-Header vor
`struct input_absinfo` dokumentiert. Die Sony-Gyroausgabe kann durch die
Normalisierung deutlich größere Zahlen als der ursprüngliche 16-Bit-Rohwert
haben; Linux-Input transportiert dafür Integerwerte.

SDL rechnet die evdev-Ausgabe anschließend um:

```text
accel_m_s2[i] = evdev_accel[i] * 9.80665 / accel_resolution[i]
gyro_rad_s[i] = evdev_gyro[i] * (pi / 180) / gyro_resolution[i]
```

Im allgemeinen Linux-evdev-Pfad bleibt die Achsenfolge erhalten.
`CorrectSensorData()` besitzt eine spezielle Nintendo-Umordnung; GameSir
wird dort nicht automatisch passend gedreht. SDL definiert für einen vor
dem Nutzer gehaltenen Controller +X nach rechts, +Y nach oben und +Z zum
Nutzer. Positive Rotation erscheint für einen Beobachter auf der positiven
Achse gegen den Uhrzeigersinn; Gyro-X/Y/Z entsprechen Pitch/Yaw/Roll.
Beschleunigung enthält die Schwerkraft; sie wird für SDL nicht entfernt.
[SDL-Umrechnung], [SDL-Koordinaten]

DualSense erkennt einen Überlauf der 32-Bit-Rohgerätezeit, bildet ein Delta
und akkumuliert gerundete Mikrosekunden. Danach folgen `MSC_TIMESTAMP` und
genau ein `input_sync()` für den Sensorrahmen. SDL unterscheidet den
Host-Ereigniszeitstempel und den aus `MSC_TIMESTAMP` aufgebauten Sensorzeitwert
in Nanosekunden. Ohne MSC-Ereignisse bleibt der separate Sensorzeitwert in
diesem Backend zunächst null; das verhindert nicht die Ausgabe von Werten
mit Host-Ereigniszeit. Für GameSir müssen Reset, Überlauf, Funkunterbrechung
und verlorene Frames ausdrücklich geprüft werden, bevor eine Geräteuhr
oder Integrationsgenauigkeit behauptet wird. [PS-Sensorausgabe], [SDL-Ereignisse]

## 3. Separates input_dev gegenüber der bisherigen IIO-Ausgabe

`hid-playstation` erstellt für DualSense ein normales Gamepad und zusätzlich
ein `input_dev` mit dem Namenszusatz `Motion Sensors`. Das Sensorgerät besitzt
`INPUT_PROP_ACCELEROMETER`, sechs Sensor-ABS-Achsen und `MSC_TIMESTAMP`.
Gamepad-Sticks und Sensorachsen können dadurch dieselben ABS-Codes benutzen,
ohne am selben evdev-Knoten miteinander zu kollidieren. Dieser konkrete
DualSense-Pfad veröffentlicht die Bewegungssensoren über das Input-Subsystem,
nicht über IIO. [PS-Input-Sensor], [PS-Erzeugung]

Die GameSir-Alpha hat dagegen ein Gamepad-`input_dev` und für native PIDs ein
IIO-Gerät mit sechs signierten Rohkanälen. `gsn_iio_raw()` akzeptiert nur
`IIO_CHAN_INFO_RAW`; die Kanäle verwenden Direktmodus ohne Scanpuffer und
ohne standardisierten SCALE-Eintrag. Zusätzlich gibt es das explizit
experimentelle `accel_experimental_um_s2` und den Status
`gyro_raw axes_unverified`. IIO-X/Y/Z bezeichnen hier die Drahtkanalfolge,
keine verifizierte Gehäuseorientierung. Der private Sample-Snapshot enthält
zusammengehörige sechs Rohwerte plus Host-Monotonzeit und Samplezähler;
separate IIO-Attributlesevorgänge können verschiedene neu eingetroffene
Samples treffen. `kernel/gs_native_usb.c:389–404,500–560,1753–1772`.

IIO ist für Rohdaten, Debugging und spätere Sensorwerkzeuge sinnvoll, stellt
aber für den geprüften SDL3-Linux-Gamepadpfad keinen Ersatz für den Input-Knoten
dar. Die allgemeine SDL-Sensor-Treiberliste enthält in diesem Stand ebenfalls
kein Linux-IIO-Backend. Der vorhandene isolierte Test bestätigte bereits
**IIO allein → kein Gamepad-Sensor**; das war ein Bibliothekstest mit künstlichen
Geräteschnittstellen, kein GameSir-Sensor-Hardwaretest. [SDL-Sensorbackends],
[vorhandener Testbericht](SDL-SENSOR-ERGEBNIS.rst)

## 4. Wie SDL3 die Sensoren dem eigentlichen Gamepad zuordnet

Der geprüfte Pfad arbeitet in vier Schritten:

1. `IsSensor()` beziehungsweise die Linux-Geräteklassifizierung erkennt den
   separaten Sensor-evdev-Knoten. `INPUT_PROP_ACCELEROMETER` klassifiziert ihn
   ausdrücklich als Sensor statt als zweites Gamepad. [SDL-Klassifizierung]
2. `GetSensor()` liest `EVIOCGUNIQ` am Gamepad und an noch nicht zugeordneten
   Sensorgeräten und vergleicht die Zeichenketten. **Weder gleicher Name noch
   VID/PID oder gemeinsamer Sysfs-Parent ersetzen diese Prüfung.** Der Code
   verlangt nicht ausdrücklich eine nichtleere Kennung; sogar zwei leere
   Zeichenketten können gleich sein. Unsere sichere Ausgabe muss deshalb
   dieselbe eindeutige, nichtleere Instanzkennung für beide Geräte bereitstellen,
   damit zwei angeschlossene GameSir-Dongles nicht falsch gruppiert werden.
   DualSense setzt hierfür seine ermittelte MAC in `hdev->uniq` und übernimmt
   dieselbe `uniq` in die Input-Geräte. [SDL-Zuordnung], [PS-MAC], [PS-Identität]
3. `ConfigJoystick()` verlangt jeweils drei vollständige Achsen, liest ihre
   `EVIOCGABS`-Auflösungen und registriert Gyro/Accel am bereits vorhandenen
   Joystick. Der geprüfte Code prüft dabei nicht auf eine positive Auflösung;
   die bisherige Nullauflösungs-Fixture erzeugte unendliche Werte. Eine positive
   verifizierte Auflösung ist somit eine Pflicht unseres Treibers, keine
   verlässliche Schutzprüfung von SDL. Der Backend-Aufruf nennt die Datenrate
   `0.0f`, also unbekannt; daraus keine 1000-Hz-IMU ableiten. [SDL-Auflösung]
4. Ein Spiel öffnet das Gamepad, prüft `SDL_GamepadHasSensor()`, aktiviert
   `SDL_SENSOR_GYRO` und/oder `SDL_SENSOR_ACCEL` mit
   `SDL_SetGamepadSensorEnabled()` und liest über `SDL_GetGamepadSensorData()`
   oder `SDL_EVENT_GAMEPAD_SENSOR_UPDATE`. Das Ereignis enthält die
   Joystick-Instanz-ID, Sensortyp und drei Werte; sie gehören damit zum
   eigentlichen Gamepad. Erkennung allein aktiviert noch keinen Sensorstrom.
   `SDL_GetGamepadSensorDataRate()` darf bei unbekannter Rate null melden.
   [SDL-Spiele-API], [SDL-Ereignis-API], [SDL-Aktivierung]

Dies beschreibt den Linux-evdev-Backendpfad. Die bisherigen zwölf gerätefreien
SDL3-/SDL2-Compat-Fälle deaktivierten HIDAPI und verwendeten eine explizite
Gamepad-Zuordnung. Sie belegen weder automatische Backendauswahl noch Sensoren
in Steam Input, Proton oder einem Spiel mit eigener SDL-Version. Für eine
fertige Integration sind Berechtigungen, Mehrgerätezuordnung, Hotplug und die
konkrete Anwendung weiterhin getrennt nachzuweisen. Hier wurden diese Tests
nicht erneut ausgeführt.

## 5. Konkrete Empfehlung für gs_native

IIO unverändert als Rohdaten-/Diagnoseausgabe erhalten und später **ein weiteres
Input-Sensorgerät im vorhandenen Kerneladapter** hinzufügen. Ein gemeinsamer
USB-Besitzer und derselbe Decoder genügen; kein zweiter USB-Leser, virtueller
Controller, DualSense-ID oder Deadband-Prozess ist dafür notwendig.

Der vorbereitete Vertrag aus [sdl-sensor-calibration.json](sdl-sensor-calibration.json)
passt zum offiziellen Referenzmuster:

- Normales Gamepad ohne `INPUT_PROP_ACCELEROMETER`; daneben ein Sensorgerät
  ohne Gamepad-Tasten mit `ABS_X/Y/Z` und `ABS_RX/RY/RZ` und derselben
  eindeutigen nichtleeren `uniq`. Die bisherige Gamepad-Registrierung setzt
  noch keine `uniq`; die künftige gemeinsame Kennung muss auch den Lebenszyklus
  von Dongle-/Controllerinstanzen und mehrere gleichzeitig angeschlossene
  Geräte abdecken. Keine ungeprüfte modusübergreifende Seriennummer behaupten.
- Rohdaten aus genau einem dekodierten Paket beibehalten; separat die
  kalibrierte Achsenpermutation, Vorzeichen und Bias anwenden. Nach Ausgabe
  aller Sensorachsen genau einen Sensorrahmen synchronisieren. Gleichzeitige
  normale Eingaben und Viermotorbetrieb bleiben im bestehenden Transport.
- `gs_sensor_convert()` wiederverwenden. Für gewählte positive ganzzahlige
  Ausgabeauflösungen `R_a/R_g` wird je Achse mit `R/S_i` normalisiert, wobei
  `S_i` die belegte Rohsensitivität ist. Fractionale Sensitivitäten bleiben
  über Zähler/Nenner darstellbar. Ausgabeauflösung, physikalische Sensitivität,
  Rauschfilter und Abtastrate getrennt dokumentieren; Überlauf und Messbereich
  testen. Mikro-m/s² aus dem experimentellen Helfer nicht irrtümlich als
  evdev-Einheiten/g veröffentlichen.
- Freigabe durch den vorhandenen strengen Skalierungs-/Achsen-/Bias-Vertrag;
  keine `resolution=0`, kein künstlicher Gyrofaktor und keine automatischen
  Sony-Fallbackwerte. Bis zur Belegung bleibt `runtime_enable=false` für diese
  kalibrierte SDL-Ausgabe; normale Alpha-Eingaben/Motoren und IIO bleiben davon
  unabhängig. Einzelne Verifikationsbits ersetzen keine Messbelege.
- Hostzeit weiter explizit nutzen. `MSC_TIMESTAMP` nur mit belegter Zeitbasis
  und getestetem Reset-/Überlaufverhalten ergänzen; fehlende Gerätezeit darf
  die erste korrekt skalierte SDL-Ausgabe nicht unnötig verhindern.

Das ist eine Architekturentscheidung und Umsetzungsempfehlung. Es wurde keine
zusätzliche Geräteschnittstelle registriert und keine Hardwarefreigabe erteilt.

## 6. Welche GameSir-Messungen noch fehlen

Die bestehenden **12.204** IMU-Pakete sichern Format, Kanalfolge und Rohwerte.
Der Ruhemedian des Accel-Betrags von `8215.838` Zählern liegt ungefähr
`0.291 %` über 8192; das unterstützt den experimentellen Kandidaten. Freie
Handbewegungen ohne belegte Winkel, Richtungen und Zeitfenster bestimmen aber
keine Gyroskop-Empfindlichkeit. [bestehende Statistik](imu-calibration-analysis.json)

Für eine pragmatische Kalibrierung ohne weitere Chip-Suche fehlen gezielte,
später separat freizugebende Referenzen:

1. **Ruhender Gyro:** mehrere dokumentierte Ruhefenster vor/nach Bewegung,
   möglichst nach Aufwärmen. Je Kanal Bias, Rauschen und Wiederholbarkeit
   prüfen; keine gravitationsabhängige Accel-Nullung als Gyrokalibrierung nutzen.
2. **Bekannte Winkel in beiden Richtungen:** um jede physische Controllerachse
   beispielsweise +180/−180 oder +360/−360 Grad, mit eindeutigem Anfang/Ende
   und mehreren Wiederholungen/Geschwindigkeiten. Das liefert Kanal, Vorzeichen
   und einen unabhängigen Faktor. Mit überprüften Sekundenintervallen gilt
   `S_i ≈ Integral(raw_i - bias_i, dt) / Winkel_in_Grad`; die negative Richtung
   dient zusätzlich der Vorzeichen-/Symmetrieprüfung. Ein Drehtisch mit bekannter
   Rate wäre eine Alternative, kein zwingender Einstieg.
3. **Zeit-/Datenvollständigkeit:** verfügbare Hostzeit auf Lücken, Reihenfolge,
   Latenz und Start-/Endzuordnung prüfen; Geräteuhr nur bei Beleg auswerten.
   Nicht die USB-Pollingrate als IMU-Abtastrate einsetzen. Die alten freien
   Bewegungsphasen und Bedienansagen allein reichen für die Winkelintegration
   nicht aus.
4. **Sechs ruhige Accel-Lagen:** jede Achse einmal positiv/negativ zur bekannten
   Schwerkraftrichtung. Damit lassen sich Vorzeichen, Bias und Gain trennen:
   nominell `bias=(a_plus+a_minus)/2`, `S=(a_plus-a_minus)/2` in Zählern/g.
   Die SDL-Beschleunigung behält g. Eine einzelne vorherrschende Rohachse
   beweist keine vollständige Gehäuseorientierung.
5. **Unabhängige Abnahme:** Kalibrierung aus einem Teil der Messungen bestimmen,
   auf zurückgehaltenen Winkel-/Ruheläufen prüfen; Fehlergrenzen und
   Restdrift angeben. Erst danach physikalische SDL-Referenzfälle, reale
   Gruppierung zweier Geräte, Host-/Sensorzeit und gleichzeitige Eingaben/
   Haptik prüfen. Pro Variante und verwendeter Einstellung kennzeichnen,
   welche Kalibrierung tatsächlich belegt ist.

Ein identifizierter Chip kann ergänzend helfen, ist aber keine Voraussetzung
für diese Referenzmethode. Weder Sony-Feature-Report `0x05`, Sony-Bias noch
die DualSense-Ausgabeauflösung `1024` liefern GameSir-Kalibrierwerte. Gezielte
Kalibrierungsmessungen sind vom offenen Bootstrap-Problem und vom bereits
belegten normalen Eingabe-/Viermotorpfad getrennte Aufgaben.

## Fundstellen und lokale SHA256-Pins

Die ersten fünf Dateien liegen in den vorhandenen lokalen Research-Verzeichnissen;
die letzten vier sind installierte Header mit lokal bestätigter SDL-Revision.
Es wurden keine Fremdquellen in das Projekt kopiert.

| Geprüfte Datei | SHA256 |
| --- | --- |
| Linux `hid-playstation.c` | `48a08dddf8d276a611195311a29cd4f113a949a1f5431ecc84b0396b106ec896` |
| SDL Release `SDL_sysjoystick.c` | `4c787e35305b959a680c19aedc661e90000259d0f6d2a520a169dc6821067178` |
| SDL Release `SDL_evdev_capabilities.c` | `dc3e9c9c1f672b70ea671bdf75f0eb88b4ae399655bb35a87dfe2e029dae5106` |
| SDL Release `SDL_sensor.c` | `a3919d4bf150cf1c049af7acd78a91eb580790f08658c0222a86e255546006fb` |
| zusätzliche SDL-Datei, Commit nicht neu belegt | `b7d34469509a19b16d4bce197baa0418bebef6822439a4290e0c92878e151680` |
| `/usr/include/SDL3/SDL_sensor.h` | `8c91002fc95799b820d07671541c97c012f77bcf8eb16f624e717142fa051c72` |
| `/usr/include/SDL3/SDL_gamepad.h` | `93beab034992a9ff3392dfbfb461862fca22301ea5eb9f7d96c2dc37457fb487` |
| `/usr/include/SDL3/SDL_events.h` | `df509bcdb9fb84ad82ebfbd3d77eb8176e0c34ed5dc54044f8e20e97e72214f7` |
| `/usr/include/SDL3/SDL_revision.h` | `22729d37b87545769c9677a955b9f69c2c5dae7bc0d04650d979f478382586fa` |

GameSir-Referenzdateien im genannten Commit:
`kernel/gs_native_usb.c` SHA256
`746bc2a8e31c01f9fc1f960cf0e3352d79f71fc7bfe751699e35398efd504cfd`,
`src/gs_sensor.c`
`7da367e58d3b15ac154659e78fe354e21973acc6a032534afbdc94186761c1ea`,
`src/gs_sensor.h`
`5a7cd469283b6878f387a60cb9fa3224ae5b48e457028380290957505bc13616`.

[PS-Grenzen]: https://github.com/torvalds/linux/blob/a5ebb76233b79db01e82e061173cb73c6d2b5c6b/drivers/hid/hid-playstation.c#L172-L176
[PS-Eingang]: https://github.com/torvalds/linux/blob/a5ebb76233b79db01e82e061173cb73c6d2b5c6b/drivers/hid/hid-playstation.c#L1436-L1469
[PS-Kalibrierung]: https://github.com/torvalds/linux/blob/a5ebb76233b79db01e82e061173cb73c6d2b5c6b/drivers/hid/hid-playstation.c#L1023-L1147
[PS-Sensorausgabe]: https://github.com/torvalds/linux/blob/a5ebb76233b79db01e82e061173cb73c6d2b5c6b/drivers/hid/hid-playstation.c#L1555-L1590
[PS-Input-Sensor]: https://github.com/torvalds/linux/blob/a5ebb76233b79db01e82e061173cb73c6d2b5c6b/drivers/hid/hid-playstation.c#L910-L944
[PS-Erzeugung]: https://github.com/torvalds/linux/blob/a5ebb76233b79db01e82e061173cb73c6d2b5c6b/drivers/hid/hid-playstation.c#L1816-L1844
[PS-Identität]: https://github.com/torvalds/linux/blob/a5ebb76233b79db01e82e061173cb73c6d2b5c6b/drivers/hid/hid-playstation.c#L639-L665
[PS-MAC]: https://github.com/torvalds/linux/blob/a5ebb76233b79db01e82e061173cb73c6d2b5c6b/drivers/hid/hid-playstation.c#L1783-L1788
[SDL-Klassifizierung]: https://github.com/libsdl-org/SDL/blob/829a65d769d935c4852f8159e964312c0957260a/src/core/linux/SDL_evdev_capabilities.c#L61-L95
[SDL-Zuordnung]: https://github.com/libsdl-org/SDL/blob/829a65d769d935c4852f8159e964312c0957260a/src/joystick/linux/SDL_sysjoystick.c#L1530-L1582
[SDL-Auflösung]: https://github.com/libsdl-org/SDL/blob/829a65d769d935c4852f8159e964312c0957260a/src/joystick/linux/SDL_sysjoystick.c#L1416-L1451
[SDL-Umrechnung]: https://github.com/libsdl-org/SDL/blob/829a65d769d935c4852f8159e964312c0957260a/src/joystick/linux/SDL_sysjoystick.c#L1880-L1929
[SDL-Ereignisse]: https://github.com/libsdl-org/SDL/blob/829a65d769d935c4852f8159e964312c0957260a/src/joystick/linux/SDL_sysjoystick.c#L2063-L2120
[SDL-Aktivierung]: https://github.com/libsdl-org/SDL/blob/829a65d769d935c4852f8159e964312c0957260a/src/joystick/linux/SDL_sysjoystick.c#L1700-L1727
[SDL-Sensorbackends]: https://github.com/libsdl-org/SDL/blob/829a65d769d935c4852f8159e964312c0957260a/src/sensor/SDL_sensor.c#L30-L52
[SDL-Koordinaten]: https://github.com/libsdl-org/SDL/blob/829a65d769d935c4852f8159e964312c0957260a/include/SDL3/SDL_sensor.h#L83-L126
[SDL-Spiele-API]: https://github.com/libsdl-org/SDL/blob/829a65d769d935c4852f8159e964312c0957260a/include/SDL3/SDL_gamepad.h#L1435-L1512
[SDL-Ereignis-API]: https://github.com/libsdl-org/SDL/blob/829a65d769d935c4852f8159e964312c0957260a/include/SDL3/SDL_events.h#L702-L711
