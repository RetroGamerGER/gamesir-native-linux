> Public export: personal tester, host and path references were anonymized. Historical evidence hashes refer to the private originals.

# Experimentelle LSM6DS3TR-C-Gyrodiagnose

Stand: 16. Oktober 2026. Zunächst offline implementiert und geprüft. Ein
anschließend separat freigegebener IIO-Anzeigelauf wurde wegen verspäteter
Chatansagen abgebrochen. Der danach erneut freigegebene, lokal getaktete
KDE-/IIO-Anzeigelauf ist inzwischen bestanden. Das bestätigt den Diagnose-
und Ansagepfad, keine physikalische Gyrokalibrierung oder weitere Testfreigabe.

[tester] gibt LSM6DS3TR-C für diesen Versuch als Arbeitshypothese vor. Der
tatsächliche Sensor, der aktive Messbereich und die unveränderte Übernahme
von Sensorzählwerten in USB-Pakete bleiben unbewiesen. Kein Profil wird
automatisch ausgewählt oder als bestätigte Kalibrierung installiert.

Für die anschließende bekannte Winkelreferenz wurde inzwischen ein
[kohärenter IIO-Pufferpfad mit eigenem Leser und Winkelanalyse](COHERENT_IMU_CALIBRATION.md)
offline ergänzt. Die nachstehende Einzelattributdiagnose bleibt eine
separate Anzeige; ihre historischen Daten werden dadurch nicht nachträglich
kohärent. Noch kein neuer Sensorlauf oder installiertes Modul.

## Werkzeug und Quellenstatus

`tools/imu/gamesir_imu_diagnostic.py` ist ein eigenständiges Diagnoseprogramm.
Es erweitert die Offline-Auswertung des vorhandenen IMU-Rohdatenpfads und
bereitet eine ausdrücklich freizugebende IIO-Beobachtung vor. Der produktive
Kernel-Treiber, Bootstrap, Paddles, Force Feedback und die SDL-Laufzeitfreigabe
bleiben unverändert. Das Programm sendet keine USB- oder Sensorbefehle.

| Experimentelles Profil ±Grad/s | Grad/s je Rohwert | Exakter Faktor |
| --- | --- | --- |
| 125 | 0,004375 | 7/1600 |
| 250 | 0,00875 | 7/800 |
| 500 | 0,0175 | 7/400 |
| 1000 | 0,035 | 7/200 |
| 2000 | 0,07 | 7/100 |

Die fünf Werte stammen aus der vom Nutzer vorgelegten ST-Datenblatttabelle.
Die gespeicherte Linux-In-Tree-ST-Referenz bestätigt die vier Gewinne von
8,75 bis 70 mdps/LSB auch für LSM6DS3TR-C. **125 Grad/s beziehungsweise
4,375 mdps/LSB ist hier noch nicht durch ein lokales ST-Original belegt.**
Keine Netzwerkprüfung wird daraus abgeleitet. Quellenstand und ursprüngliche
Fotoauskunft bleiben in `imu-sensor-identification.json` erhalten.

Berechnet werden `(gyro_raw - bias_raw) × Profilfaktor` in Grad/s und daraus
durch Multiplikation mit π/180 in rad/s. Der Gyrofaktor wird nicht aus dem
Beschleunigungsfaktor abgeleitet. Beschleunigung bleibt separat experimentell
mit 8192 LSB/g und 9,80665 m/s² je g. Die Rohwerte werden stets mitgespeichert;
Testwerte sind als experimentell markiert. Standardmäßig wird kein Bias
abgezogen. `--bias-raw G0,G1,G2` bezeichnet eine ausdrücklich vorgegebene
Hypothese, keine automatisch bestätigte Nullpunktkorrektur.

## Gerätefreie Verwendung

Die folgenden Befehle werden aus dem Projektwurzelordner ausgeführt.
`profiles` und `plan` geben nur Informationen aus:

```sh
python3 -B tools/imu/gamesir_imu_diagnostic.py profiles
python3 -B tools/imu/gamesir_imu_diagnostic.py plan
```

Replay nimmt vorhandene Parserdatensätze im JSONL-Format an, nicht das
abgeleitete `telemetry-raw.json`-Array. Der bestehende Offline-Parser filtert
vollständige erfolgreiche IMU-Telemetrie auf Interface 0, Endpunkt 0x82.
Verschiedene Geräte-, Sitzungs- oder Zeitbasisströme werden nicht vermischt.
Im Beispiel sind der Eingabepfad und der neue Laufname zu ersetzen; das
übergeordnete Ausgabeverzeichnis muss bereits bestehen:

```sh
python3 -B tools/imu/gamesir_imu_diagnostic.py replay \
  --experimental --profile all \
  --records "/PFAD/ZUM/GESPEICHERTEN/LAUF/derived/parser-records.jsonl" \
  --output ".local/gyro-replay-NEUER-LAUF"
```

Einzelprofile werden mit `--profile 125`, `250`, `500`, `1000` oder `2000`
explizit gewählt. Es gibt keinen Standardmessbereich; `all` ist ausschließlich
für Replay zulässig. Kein Vergleich erklärt ein Profil zum tatsächlichen
Hardwareprofil. Ausgabe: `observations.jsonl`, `report.json`, `SHA256SUMS` in
einem neuen privaten Verzeichnis. Vorhandene Ausgaben werden nicht ersetzt.
Auch eine unterbrochene Beobachtung erhält Fehlerstatus und Teilergebnisse.

## Was die vorhandenen 12.204 Pakete belegen

Referenz ist Sprint 002, Lauf
`20261011T141131938846Z-measurement-B-deadband`, dessen privater Speicherort
in `.local/project-paths.json` unter `capture_dir` steht. Original-PCAPNG:
SHA256 `4045577a7a9e7a1a0f84307a45e96fd524cd7dea1d4af276ebd7db20a0994a89`.
Alle 12.204 erfolgreichen IMU-Pakete wurden unabhängig mit sechs signed
LE16-Werten ab Offset 17 gegen `derived/telemetry-raw.json` geprüft.

* Beobachtete Hostrate rund 62,527 Hz; Medianabstand 16 ms, maximal 200,007 ms.
  Das ist keine nachgewiesene interne Sensorabtastrate.
* Kein signed16-Endpunkt in den sechs Rohkanälen und keine identischen
  aufeinanderfolgenden Sechsachsensätze. Das beweist keine Verlustfreiheit.
* In der damaligen ausgewählten Ruhephase: Gyromittel roh ungefähr
  `[-0,122667; 0,485333; 0,304]`; kein allgemein gültiger Gerätebias.
* Beschleunigungsnormmedian dort rund 8215,84 roh, etwa +0,291 Prozent
  gegenüber 8192. 29 heuristisch ruhige Fenster decken nur rund 2 Grad
  unterschiedliche Schwerkraftrichtungen ab, keine sechs Referenzlagen.
* Die tatsächliche Bewegung setzte nach der Yaw-Ansage verzögert ein.
  Ansage, Phasenname und manuelle Rückmeldung ersetzen keine zeitlich
  verifizierte Drehung um einen bekannten Winkel.

Alle fünf Profile lassen sich auf dieselben Rohdaten anwenden. Es fehlen
jedoch unabhängige Winkelreferenzen, um einen der Faktoren auszuwählen.
Achsendominanz allein beweist weder die Gehäuseachse noch deren Vorzeichen.
Der bestehende ausführliche Statistikbericht bleibt maßgeblich:
`IMU-STATISTIK-UND-SENSORIDENTIFIKATION.rst` und
`imu-calibration-analysis.json`. Der neue Replay-Vergleich enthält unter
allen fünf Profilen dieselben 12.204 Rohdatensätze und Zeitstempel, ohne
Abweichung von der vorhandenen Ableitung. Maximaler absoluter Gyrokanal:

| Profil | Größter umgerechneter Betrag im gespeicherten Lauf, Grad/s |
| --- | --- |
| 125 | 22,9775 |
| 250 | 45,955 |
| 500 | 91,91 |
| 1000 | 183,82 |
| 2000 | 367,64 |

Diese Werte sind fünf Interpretationen, keine fünf unabhängigen Messungen.
44 neue synthetische Diagnosetests, die vollständige Suite `make test` und
18 Paddle-/12 Sensor-Sandboxfälle aus `make test-sdl` bestehen. Die neuen
Fälle umfassen auch bekannte synthetische ±90-/±180-Grad-Drehungen jeder
Achse und sechs künstliche Schwerkraftlagen; das ist kein Hardwarebeleg.
[Eigene Prüfmetadaten und Quellenprüfsummen](experimental-gyro-validation.json).

## Grenzen der vorbereiteten IIO-Anzeige

Der vorhandene IIO-Pfad bietet sechs separate Attribute:
`in_anglvel_x_raw` bis `in_anglvel_z_raw` und `in_accel_x_raw` bis
`in_accel_z_raw`. Jeder Zugriff holt einen aktuellen Snapshot; sechs
nacheinander gelesene Dateien müssen nicht dasselbe USB-Paket repräsentieren.
Es fehlen ein gemeinsamer Samplezeitstempel und eine gemeinsame Nummer.

`observe-iio` prüft Gerätenamen und Instanz, klammert jeden Leseumlauf mit
Host-Monotonzeit ein und markiert ihn als **nicht kohärent**. Die Mitte dieses
Fensters ist eine Beobachtungszeit, keine Sensorzeit. Deshalb ist dieser
Modus nur eine Anzeige der sechs Rohkanäle und experimentellen Umrechnungen;
**keine belastbare Winkelkalibrierung oder Winkelintegration**. Unveränderte
Werte beweisen weder ein erneut gelesenes Paket noch einen Sensorstillstand.

**Nur nach gesonderter Hardwarefreigabe; derzeit nicht ausführen.** Das
folgende Beispiel enthält absichtlich keine aktuelle Gerätenummer:

```sh
python3 -B tools/imu/gamesir_imu_diagnostic.py observe-iio \
  --experimental --profile 500 \
  --iio-dir "/sys/bus/iio/devices/iio:devicePLATZHALTER" \
  --duration 30 --period-ms 20 \
  --output ".local/gyro-iio-NEUER-FREIGEGEBENER-LAUF"
```

Das ist keine Auswahl von 500 als wahrscheinlichem Bereich. Für einen
anderen ausdrücklich gewählten Vergleich ist das Profil zu ersetzen.
Auf Gerätenameabweichung, Instanzwechsel, Lesefehler, veralteten Werten als
Treiberfehler, nicht monotoner Zeit oder einem Leseumlauf über 100 ms wird
angehalten; es gibt keine automatische Wiederverbindung oder Reparatur.
Die 100-ms-Grenze ist eine nachträgliche Qualitätsprüfung, kein harter
I/O-Timeout. Auch die angeforderte Dauer ist keine Echtzeitgarantie.

### Lokale Ansagen statt zeitkritischer Chatsteuerung

Für einen neuen freizugebenden Lauf kann derselbe Beobachter zusätzlich
`--guided-kde --duration 90` verwenden. Er nutzt das bereits vorhandene
`/usr/bin/kdialog` mit festen Argumenten und ohne Shell. Keine Installation
oder Konfigurationsänderung. Die passiven KDE-Fenster werden lokal anhand
absoluter Monotonzeit ausgelöst; Chat-/Modellwartezeit steuert keine Phase.

| Zeit | Lokaler Hinweis | Sensorreads |
| --- | --- | --- |
| Vorbereitung, 30 s | Controller ruhig ablegen, Bewegungsansage abwarten | keine |
| Aufzeichnung 0–15 s | Ruhe | ja |
| 15–30 s | Vorsichtig aufnehmen; noch nicht drehen | ja |
| 30–60 s | Langsam um alle drei Achsen und in beide Richtungen bewegen | ja |
| 60–75 s | Ablegen, 15 s Reaktionspuffer | ja |
| 75–90 s | Schlussruhe | ja |
| danach, 3 s | Test beendet | keine |

Dieser kurze Anzeigetest ist keine Referenzdrehung und ersetzt den
Kalibrierungsplan unten nicht. Vorbereitungs- und Abschlusszeit gehören
nicht zu den 90 s Beobachtung. `cues.jsonl` dokumentiert geplante und
tatsächliche Ansagezeit mit der ausdrücklich offenen Frage, ob der Nutzer
das Fenster gesehen hat. Datei und Teildaten erhalten SHA256-Prüfsummen.

Bei einer übersprungenen oder über zwei Sekunden verspäteten Phase, GUI-
Start-/Prozessfehlern oder Geräteinstanzwechsel abbrechen, statt Meldungen
nachzuholen. Den ursprünglichen Fehler auch bei Problemen des GUI-Aufräumens
erhalten. Nur eigene Popup-Prozesse werden beendet; keine Dienst-, Treiber-,
Motor- oder Wiederherstellungsaktion. Das sind Qualitätswächter, keine harte
Echtzeitgarantie bei blockierenden Kernel-/Dateisystemzugriffen.

### Erster freigegebener Anzeigelauf

Der erste Lauf nutzte Commit `b2b9515`, Profil 500 ausschließlich als
Umrechnungshypothese und sechs IIO-Rohattribute. Codex brach ihn nach
74,763645717 s beobachteter Spanne/3.600 Sätzen per SIGINT ab: die Chatansagen
waren zu spät, eine Bewegungsansage wurde nicht mehr erteilt. Der Lauf gilt
als **abgebrochen**, nicht als erfolgreicher 90-s-Test. Recorderstatus
`user_interrupted` bedeutet hier das Signal von Codex, keinen Nutzerabbruch.

Alle Rohdaten, ursprünglichen Logs und Prüfsummen bleiben privat erhalten.
Die Nachprüfung las nur Metadaten: Dienst active/running, PID1060,
NRestarts0, 109c/gs_native und IIO unverändert. Kein neuer Kernellogabruf,
keine behauptete allgemeine Fehlerfreiheit und keine Treiberänderung.
[Eigene Ergebnis-/Zeitmarkenmetadaten](experimental-gyro-live-001.json).
Die einmalige Freigabe ist verbraucht; kein automatischer neuer Lauf.
Der nachfolgende lokale Ansagenfix besteht 65 synthetische Diagnosefälle
und die vollständige Suite `make test`. Ein Fake-Uhr-/GUI-Lauf prüft 30 s
ohne Rohdatenlesung, 90 s Beobachtung und 3 s Endhinweis ohne neue Reads.
Weder echte KDE-Fenster noch weitere Sensorwerte wurden dazu geöffnet.

### Zweiter freigegebener Anzeigelauf bestanden

[tester] gab die Wiederholung einschließlich lokaler KDE-Hinweise separat
frei. Mit Commit `b0fc0a1` wurden nach 30 s Vorbereitung 90 s lang sechs
IIO-Einzelattribute gelesen: 4.305 Sätze, 89,987772072 s zwischen erstem
und letztem Lesezeitmittelpunkt. Die rund 47,83 Leser-Snapshots/s sind keine
USB-Pollingrate oder interne IMU-Abtastrate. Die sieben lokalen Ansagen kamen
in richtiger Reihenfolge, maximal 20,365 ms nach ihrem Solltermin. Keine
Sensorreads während Vorbereitung oder nach Endansage. [tester] bestätigt:
„Ja, Hinweise sichtbar und Ablauf durchgeführt“.

In den jeweils um zwei Sekunden beschnittenen Ruhe-/Bewegungsfenstern
beträgt die Standardabweichung der drei Gyro-Rohkanäle:

| Fenster | G0 | G1 | G2 |
| --- | --- | --- | --- |
| Anfangsruhe | 1,786 | 0,670 | 1,953 |
| Bewegung | 1206,972 | 338,860 | 1612,411 |
| Schlussruhe | 1,062 | 0,661 | 1,624 |

Alle drei Rohkanäle ändern sich im Bewegungsfenster und beruhigen sich
danach. Das belegt weder die Zuordnung zu Gehäuseachsen noch Vorzeichen,
Bias oder Gyrofaktor. Die sechs Attribute sind weiterhin nicht atomar;
Winkelintegration bleibt null. Profil 500 war ausschließlich eine
Umrechnungshypothese; alle fünf Faktoren wurden danach aus denselben
gespeicherten Rohwerten offline verglichen. Kein Bereich ausgewählt.

Originale, Ansagezeiten, Logs und SHA256 bleiben im privaten Laufverzeichnis
erhalten. Die Abschlusskontrolle bestätigte anhand gecachter Metadaten
dieselbe 109c/Adresse7/gs_native-/IIO-Instanz sowie Dienst PID1060,
NRestarts0, active/running. Kein neuer Kernellogabruf, keine Treiber-/
Systemänderung und keine behauptete allgemeine Warnungsfreiheit. Keine
zusätzliche Sensoraufnahme oder produktive SDL-Freigabe daraus ableiten.
[Ergebnis, Nutzerbestätigung und Prüfsummen](experimental-gyro-live-002.json).

Der vorhandene `GSN_GET_SAMPLE`-Aufruf wird **nicht** als Abkürzung benutzt:
Sein Kontroll-Geräteknoten ist mit exklusiver Control-Ownership und dem
STOP-Verhalten beim Schließen verbunden. Ein Diagnoseprogramm darf dadurch
die laufende Verwaltung nicht übernehmen oder beenden.

Für eine qualifizierte neue Winkelmessung fehlt somit noch ein kohärenter,
rein lesender Sensorstrom mit Samplekennung und Zeitstempel. Eine passende
Erweiterung wäre ein eigener, zunächst offline zu prüfender Folgeschritt;
sie ist aktuell nicht installiert oder aktiviert. Alternativ kann später
ein separat freigegebener passiver USB-Mitschnitt mit dem vorhandenen
isolierten Recorder kohärente Paketwerte samt Hostzeit liefern. Hier wird
keine neue Aufnahmeinfrastruktur entwickelt oder gestartet.

## Geführter zukünftiger Messablauf

`plan` ist ein ausdruckbarer Ablauf, kein Messstart. Er beginnt mit
30 Sekunden Vorbereitung und 30 Sekunden Ruhe. Vor jedem Dreh- und
Lagefenster liegen 15 Sekunden Reaktions- und Vorbereitungspuffer; am Ende
folgen erneut Puffer und Schlussruhe. Der Nutzer darf einen Schritt in Ruhe
vorbereiten. Der tatsächliche Beginn und das Ende einer Bewegung müssen
zusätzlich markiert werden; keine Annahme, dass die Bewegung exakt mit der
Ansage beginnt.

Vor der Freigabe Gehäuseachsen in einer Skizze eindeutig definieren:
Yaw, Pitch und Roll, zugehörige positive Drehrichtung und gemeinsame
Ausgangslage. Die Drahtachsen G0/G1/G2 beziehungsweise A0/A1/A2 bleiben bis
zur Auswertung davon getrennt. Eine Bildschirmrichtung ist keine automatische
SDL-Achsenkonvention.

Der ausgegebene Basisplan enthält je Gehäuseachse eine langsame, markierte
90-Grad-Drehung in beide Richtungen. Für die eigentliche Faktorbestimmung
sind mehrere kontrollierte Wiederholungen mit ±90 und ±180 Grad vorzusehen;
die zusätzlichen Wiederholungen und 180-Grad-Fenster gehören ausdrücklich
in den vor der Hardwarefreigabe konkretisierten Messplan. Nicht im selben
Messfenster unmarkiert zurückdrehen. Anfangs- und Endruhe dienen der
Biasprüfung. Der bekannte Winkel muss aus einer unabhängigen Markierung
oder mechanischen Referenz stammen, nicht aus dem angezeigten Gyrowert.

Anschließend sechs dokumentierte waagerechte Ruhelagen auf Ober-/Unterseite,
links/rechts sowie vorne/hinten: jeweils 15 Sekunden zum Umlegen und
20 Sekunden Ruhe im Basisplan. Aus entgegengesetzten Lagen lassen sich
Achsen, Vorzeichen, Bias und effektive Beschleunigungsskalen prüfen.
Temperatur, Auflage, Gehäuseseite, Nutzerreaktionen und mögliche Bewegung
notieren. Nur nachgewiesen ruhige Teilfenster als Nullpunktskandidaten nutzen;
keine automatische Übernahme als dauerhafte Kalibrierung.

Der Replay-Bericht kennzeichnet Lücken über dem Doppelten des
Medianabstands heuristisch und schließt diese Intervalle aus seinem rein
illustrativen Hostzeitintegral aus. Dieses Integral ist keine bestätigte
Drehung. Doppelte oder rückläufige Zeitstempel werden abgelehnt. Capture-Drops,
USB-Fehler, Hostlieferlücken und unbekannte interne Paketverluste sind
getrennte Größen. Aus dem bislang nicht als IMU-exklusiv nachgewiesenen
Headerzähler oder aus unveränderten Messwerten keine Funkverluste berechnen.

Abbruch bei Nutzer-STOP, Disconnect, falschem Gerät, veralteten/fehlenden
Messwerten als Lesefehler, Instanzwechsel, Zeitbasisfehler oder unerwarteter
Controller-/Systemänderung. Originale und Teildaten erhalten; keine aktive
Reparatur, kein Neustart des Bootstraps und keine Profil-/Firmwareänderung.

## SDL-3-Abnahme bleibt ein eigener Schritt

Der vorhandene gerätefreie Sandbox-Test `make test-sdl` prüft die technische
Zuordnung synthetischer evdev-Sensoren zu einem Gamepad. Er ist eine
Abnahmevorbereitung und kein GameSir-Gyrokalibrierungsnachweis. Seine
synthetischen Werte 16 beziehungsweise 16,4 LSB/(Grad/s) sind keine Profile
für diesen Controller.

Eine spätere zusätzliche evdev-Sensorschnittstelle benötigt denselben
eindeutigen, nicht leeren `uniq` wie das Gamepad, `INPUT_PROP_ACCELEROMETER`,
korrekte positive Auflösungen, verifizierte Achsenzuordnung und Vorzeichen,
Biasbehandlung sowie physikalisch korrekte Werte. SDL erwartet Beschleunigung
in m/s² und Winkelgeschwindigkeit in rad/s. IIO-Rohdaten bleiben erhalten.
Die physikalische Kalibrierung und eine echte SDL-Geräteprüfung müssen
gesondert bestanden werden. Ein Browser-Gamepadtester beweist diesen Pfad
nicht. Es gibt derzeit keine produktive SDL-Sensor- oder Eden-Freigabe.
