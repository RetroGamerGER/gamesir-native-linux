> Public export: personal tester, host and path references were anonymized. Historical evidence hashes refer to the private originals.

# Kohärenter IMU-Strom und geführte Winkelreferenzen

Stand: 16. Oktober 2026. **Die Gyrokalibrierung ist auf [tester]' Wunsch auf Eis.**
Eine geeignete externe 90°-Referenz fehlt. Der vorbereitete Winkelassistent
wird als offline geprüfter Zwischenstand lokal gesichert; weiterarbeiten erst
nach neuem Auftrag. Dieses Dokument erteilt keine Freigabe für Fenster,
Passwortabfrage, Geräteöffnung, Pufferkonfiguration oder Messung.

Ergänzung vom 18. Oktober: Ein getrennter [qualitativer Achsentest](GYRO_AXIS_TEST.md)
ist ohne bekannten Winkel offline vorbereitet. Er verwendet denselben begrenzten
Puffer-Worker, aber eigene Ansagen und eine reine Rohkanalauswertung. Die unten
beschriebene 90°-Kalibrierung bleibt davon unberührt und weiterhin pausiert.

Revision `0.1.0.alpha3-5` mit kohärentem Kernelpuffer ist inzwischen separat
installiert und der native Betrieb lesend bestätigt. Der letzte dokumentierte
Pufferzustand ist deaktiviert. Noch kein kohärenter Live-Pufferlauf und keine
bekannte Winkelreferenz wurden gemessen. Diese Abschlussarbeit öffnet keine
Geräte und verändert den laufenden Controllerbetrieb nicht. Installation und
historische Lesebestätigung: [Sensorupdate](COHERENT_IMU_UPDATE.md).

Ziel ist zunächst ein einzeln begleiteter Test: **dreimal 90° nach links**.
Erst nach Abschluss und neuer Bereitschaft folgen getrennt rechts, nach vorne
und nach hinten. Es gibt keinen automatisch durchlaufenden Gesamttest.

Bei einer später ausdrücklich neu beauftragten Fortsetzung ist zunächst nur
`yaw90left` mit drei einzeln bestätigten Wiederholungen vorgesehen; andere
Richtungen bleiben aus. Zuerst Zustand und konkrete Befehle frisch vorlegen,
keine alte USB-/IIO-Instanz oder frühere Freigabe ungeprüft wiederverwenden.

## Gesicherter Offline-Zwischenstand des Winkelassistenten

`tools/imu/gamesir_gyro_guided.py` trennt das unprivilegierte KDE-Frontend
vom begrenzten Worker `gamesir_gyro_worker.py`. Ein Aufruf führt höchstens
eine Wiederholung 1, 2 oder 3 aus. Vor jeder Wiederholung steht ein eigenes
lokales Go mit Abbrechen als Vorgabe. Es folgen 30 s Vorbereitung ohne
Geräteöffnung, dann die unten beschriebenen 105 s Messphasen und 3 s passive
Nachzeit. Erst nach bestätigter Rückstellung darf zurückgedreht werden;
mindestens 15 s Rücksetzpause, kein automatischer Folgelauf.

`gamesir_iio_buffer.py` prüft Metadaten/Build/USB- und IIO-Instanz und hält
das genaue Read-only-IIO-FD vor dem ersten Write bis nach der Rückstellung.
Scanmaske, Host-Uhr, Länge 512 und Watermark 1 werden bei deaktiviertem
Puffer eingestellt; passende Werte werden nicht erneut geschrieben. Danach
einmal aktivieren, begrenzt lesen, deaktivieren und die ursprünglichen Werte
wiederherstellen. Jeder Write prüft die ursprüngliche Instanz. Keine Änderung
von Geräteberechtigungen, Treibern, Diensten oder USB-Konfiguration.

Ein frischer Prozess-FD-Metadatencheck erkennt sichtbare konkurrierende Leser.
Ein simuliertes EBUSY beweist keine Kernel-Exklusivität; ein fremder Client
kann später starten. Deshalb keine weiteren IIO-Leser parallel und bei
Zählerlücken stoppen. Der Leser verwendet dasselbe FD, keine zweite Öffnung.
EOF/STOP/fehlender Frontend-Heartbeat, Sensor-/Zeitfehler und Signale führen
zur Rückstellung, nicht zu Reconnect oder Wiederholung. Bei Geräteersatz
keine Writes an die neue Instanz; ein nicht bestätigter Rückweg bleibt Fehler.

Originalbytes, kohärente JSONL-Samples, Layout, Puffertransaktion und Bericht
werden unter `capture/` privat mit SHA256 gespeichert. Das Frontend prüft
diese Dateien unabhängig, protokolliert UTC/Monotonzeit der Ansagen und
erzeugt erst nach ausdrücklicher Bestätigung der externen Winkelreferenz
`reference.json`/`analysis.json`. Grenzen werden auf vorhandene Samplezeiten
innerhalb der tatsächlich angeforderten Ansagen gelegt. Kein erfundener
Zeitstempel, automatischer Faktor oder produktives SDL-Profil.

Die vorbereitete Lückengrenze beträgt 250 ms, fehlende frische Daten führen
nach 2 s zum Abbruch. Das sind dokumentierte Qualitäts-/Abbruchgrenzen,
keine nachgewiesene Sensor-ODR oder Funkverlustrate. Die echte Puffer-,
Passwortfenster-, Ansagen- und Rückstellungsabnahme steht vollständig aus.
Es wurde für diesen Zwischenstand kein ausführbares Geräte-Manifest erstellt
und kein `run` ausgeführt. Konkrete Live-Befehle erst nach Wiederaufnahme
und frischer Zustandsprüfung zeigen; diesen Commit nicht als Freigabe nutzen.

## Warum ein neuer Datenpfad erforderlich ist

Der abgeschlossene 90-Sekunden-Anzeigetest mit 4.305 Beobachtungen las sechs
separate IIO-Rohwertdateien. Er belegt eine Reaktion der Gyrokanäle auf
Bewegung. Die sechs Werte einer Beobachtung stammen jedoch nicht garantiert
aus demselben USB-Bericht. Daraus folgt keine kohärente Winkelintegration,
bestätigte Achsenzuordnung oder Kalibrierung. Die Originale dieses historischen
Tests und ihre Kennzeichnung bleiben erhalten.

Der neue Standard-IIO-Puffer übernimmt dagegen alle sechs Rohwerte aus
demselben bereits akzeptierten IMU-Bericht. Er ergänzt einen Host-Zähler und
einen Host-Zeitstempel. Rohwerte werden dabei weder skaliert noch umgeordnet.
Bootstrap, normale Eingaben, Paddles und Motorbefehle erhalten keinen neuen
Aktivierungsauftrag. Der Puffer ist standardmäßig aus.

## Format und Aussagegrenzen

Der vollständige, vom Leser verlangte Scan ist 32 Byte groß:

| Byteoffset | Feld | Kodierung |
| --- | --- | --- |
| 0, 2, 4 | Beschleunigung A0, A1, A2 | Je signed 16 Bit, Little Endian |
| 6, 8, 10 | Gyro G0, G1, G2 | Je signed 16 Bit, Little Endian |
| 12–15 | Ausrichtungspadding | Vier Nullbytes |
| 16 | Anzahl akzeptierter IMU-Berichte dieser Geräteinstanz | Unsigned 64 Bit, Little Endian |
| 24 | Zeit der Host-Verarbeitung des Berichts | Signed 64 Bit, native CPU-Byteordnung, Nanosekunden |

Die Scanreihenfolge ist Beschleunigung vor Gyro. Das JSONL-Format benennt
beide Vektoren ausdrücklich als `accel_raw` und `gyro_raw`; die bisherige
Rohkanalreihenfolge bleibt erhalten. Aktiv sein müssen alle acht
`scan_elements`: sechs Rohkanäle, `in_count0` und `in_timestamp`. Der Leser
prüft Index, Datentyp, aktivierte Kanäle, IIO-Gerätenamen, Instanz,
Gerätenummer und `current_timestamp_clock = monotonic`.

Der Zeitpunkt stammt aus `ktime_get_ns()` / `CLOCK_MONOTONIC` bei der
Verarbeitung des IMU-Berichts. Er ist **keine Sensorabtastzeit**. USB-Jitter,
eine mögliche interne Mittelung und die interne Sensorrate bleiben offen.
Der Zähler zählt akzeptierte Host-Berichte; er ist weder ein Sensorzähler
noch ein Nachweis über Funkverluste. Ein Sprung kann fehlende Beobachtungen
zwischen Treiber und Leser anzeigen, erklärt aber nicht selbst deren Ursache.
Die zusätzliche IIO-Eigenschaft `buffer_push_errors` macht fehlgeschlagene
Pufferübergaben sichtbar. Ein voller Diagnosepuffer soll normale
Gamepad-Eingaben nicht zum Fehlerfall machen.

Die nur lesbare Eigenschaft `buffer_stream_active` zeigt, ob der native
Treiber tatsächlich neue Scans in den Puffer übernehmen darf. Nach Suspend
oder Quiesce kann dieser Wert 0 sein, obwohl das IIO-Attribut `buffer/enable`
noch 1 enthält. Der Leser verlangt beide Werte auf 1 und stoppt bei einem
geschlossenen Stream-Gate. Zusätzlich kontrolliert er die Differenz von
BOOTTIME und MONOTONIC, um eine Suspend-/Uhrdiskontinuität zu erkennen.

Der Kernelzusatz verwendet einen Software-KFIFO und benötigt zusätzlich
`kfifo_buf`. Die Abhängigkeit ist in der separat freigegebenen Revision5-
Installation bestätigt. Die Messhelfer laden oder installieren keine Module.

## Pufferkonfiguration bleibt ein gesonderter Schritt

`gamesir_imu_stream.py` schreibt keine IIO-Eigenschaften. Der später separat
freizugebende Aufbau muss vorher die einzige beabsichtigte Geräteinstanz und
das Fehlen eines konkurrierenden Pufferlesers prüfen. Erst bei deaktiviertem
Puffer dürfen Host-Uhr, Scanmaske, Länge und gegebenenfalls Watermark passend
gesetzt werden. Die vorbereitete Empfehlung ist Länge 512 und Watermark 1,
sofern diese Eigenschaft vorhanden ist.

**Puffer aktivieren ist eine Host-Zustandsänderung.** Der Leser verlangt
einen bereits freigegeben und korrekt aktivierten Puffer. Er öffnet nur das
zu genau dieser Instanz passende IIO-Zeichengerät lesend und nichtblockierend.
Er öffnet keinen exklusiven `gsnative`-Kontrollkanal und sendet keine USB- oder
Sensorkonfigurationsbefehle.

**Schließen des Lesers deaktiviert den Puffer nicht.** Deshalb müssen für
einen echten Lauf vorher auch das anschließende Deaktivieren und die
Wiederherstellung der ursprünglichen Host-Einstellungen konkret freigegeben
und vorbereitet sein. Bei einem Fehler gibt es kein automatisches Resume,
Reconnect, Treiberwechsel oder blindes Nachkonfigurieren.

Den vollständigen deklarativen Ablauf nur ausgeben, ohne ihn auszuführen:

```sh
python3 -B tools/imu/gamesir_imu_stream.py configuration-plan
```

## Ein menschlich durchführbarer Test nach dem anderen

Die Gehäusekonvention ist unabhängig von den unbekannten Rohkanälen:
X zeigt beim normalen Halten nach rechts, Y zur USB-/Vorderkante und Z aus
der Tastenfläche. Das ist eine vereinbarte rechtshändige Beschreibung der
Bewegungen, kein bereits bestätigtes G0/G1/G2-Mapping.

„90° nach links“ meint eine horizontale Drehung mit der Tastenfläche nach
oben, wie auf einer Tischplatte: Die zuvor vom Spieler weg zeigende
USB-Kante zeigt am Ende nach links. Den Controller dabei nicht senkrecht
aufrichten. Eine senkrechte Endlage gehört zum gesonderten Vorwärts-/
Rückwärtsneigen, das nicht Teil der nächsten drei Linksdrehungen ist.

Die ersten vier **getrennten** Sitzungen sind:

| Sitzung | Jeweils drei Wiederholungen | Winkel nach Gehäusekonvention |
| --- | --- | --- |
| `yaw90left` | 90° nach links drehen | +90° um Z |
| `yaw90right` | 90° nach rechts drehen | −90° um Z |
| `pitch90forward` | 90° nach vorne neigen, USB-Kante nach unten | −90° um X |
| `pitch90back` | 90° nach hinten neigen, USB-Kante nach oben | +90° um X |

**Vor jeder einzelnen Wiederholung ist eine neue Bereitbestätigung
vorgesehen.** Eine schwierige oder verspätete Bewegung wird verworfen und
nicht automatisch wiederholt. Vor der ersten Wiederholung gibt es
30 Sekunden Vorbereitung. Danach gilt pro Wiederholung:

1. 20 Sekunden ruhige Vorphase für einen experimentellen Bias.
2. 15 Sekunden Aufnehmen und Ausrichten an der externen Startmarkierung.
3. 5 Sekunden an der Startmarke stillhalten.
4. Innerhalb von höchstens 15 Sekunden genau die angesagte Drehung zur
   Endmarkierung ausführen und dort bleiben. Nicht zurückdrehen.
5. 5 Sekunden an der Endmarke stillhalten.
6. 15 Sekunden zum vorsichtigen Ablegen; dieses Umlegen gehört nicht zum
   ausgewerteten Drehfenster.
7. 30 Sekunden ruhige Nachphase, um Biasänderung und Streuung zu prüfen.
8. Erst außerhalb des abgeschlossenen Integrationsfensters in mindestens
   15 Sekunden zur Ausgangsposition zurücksetzen. Danach auf die nächste
   Bereitbestätigung warten.

Das Referenzmaß muss unabhängig vom Gyro sein: etwa sichtbare 0°-/90°-/
180°-Markierungen mit fester Zeigerkante oder eine geeignete Winkelvorrichtung.
Die Bezeichnung „90°“ im Plan beweist nicht, dass diese Drehung tatsächlich
ausgeführt wurde. Anfang, Ende, Richtung, Wiederholung und verwendete
Winkelreferenz werden deshalb separat notiert. Aufnehmen, Ablegen und
Rücksetzen dürfen keine unmarkierte Gegenrotation im Integrationsfenster
erzeugen. Die ausgewertete Bewegung schließt die ruhigen Ränder an Start
und Ende ein, jedoch keine Umpositionierung.

Die Planbefehle geben nur JSON aus. Sie starten weder Timer noch KDE-Hinweise
oder Gerätezugriffe:

```sh
python3 -B tools/imu/gyro_reference.py plan --session yaw90left
python3 -B tools/imu/gyro_reference.py plan --session yaw90right
python3 -B tools/imu/gyro_reference.py plan --session pitch90forward
python3 -B tools/imu/gyro_reference.py plan --session pitch90back
python3 -B tools/imu/gyro_reference.py metadata-schema
```

Rollbewegungen und ±180°-Drehungen sind spätere, erneut getrennte Sitzungen.
Auch die sechs Beschleunigungsruhelagen ±X, ±Y und ±Z sind ein optionaler
eigener Ablauf: je Lage neue Bereitschaft, mindestens 15 Sekunden
Umlegepuffer und 30 Sekunden Ruhe. Experimentell 8192 LSB/g ist hierbei eine
zu überprüfende Annahme, keine Grundlage für den unabhängigen Gyrofaktor.
Der neue Winkelanalysator führt noch keine automatische Sechslagenanpassung
oder Kalibrierungsinstallation durch.

## Gespeicherte Daten und Offline-Auswertung

Der Streamleser legt immer ein neues privates Ergebnisverzeichnis an, statt
vorhandene Läufe zu überschreiben. Das Bundle enthält:

- `scans.bin`: empfangene rohe Scanbytes, auch bis zum Abbruch erhalten.
- `observations.jsonl`: vollständig dekodierte kohärente Scans.
- `layout.json`: Scanformat, Instanz, Quelle und ausgewählte Zeitgrenze.
- `report.json`: Abschluss- oder Fehlerstatus und Anzahl ausgegebener Scans.
- `SHA256SUMS`: Prüfsummen der vier Dateien.

Vor einer Auswertung muss `report.json` erfolgreich abgeschlossen sein und
die Prüfsummen müssen stimmen. Eine vorhandene Teilaufzeichnung wird
aufbewahrt, beweist aber keine bestandene Kalibrierung. Bei `decode-file`
bleibt außerdem die bereits gespeicherte Quelldatei unverändert erhalten.

Die folgenden Beispiele setzen bewusst **bereits vorhandene gespeicherte
Dateien** unter `.local/gyro-reference/` voraus. Sie öffnen kein Gerät. Der
Zielordner `yaw90left-001-decoded` darf noch nicht existieren:

```sh
python3 -B tools/imu/gamesir_imu_stream.py decode-file \
  --scans .local/gyro-reference/yaw90left-001/scans.bin \
  --instance-id saved-yaw90left-001 \
  --source-kind iio_buffer \
  --max-gap-ms 50 \
  --output .local/gyro-reference/yaw90left-001-decoded

python3 -B tools/imu/gyro_reference.py analyze \
  .local/gyro-reference/yaw90left-001-decoded/observations.jsonl \
  .local/gyro-reference/yaw90left-001/markers.json \
  --max-gap-ns 50000000
```

Die hier beispielhaft gewählten 50 ms sind eine explizite Qualitätsgrenze
für die Auswertung, keine nachgewiesene Sensorrate und kein tolerierter
Funkverlust. Vor einer echten Messung wird die geeignete Grenze anhand der
bekannten Host-Berichtsintervalle festgelegt und dokumentiert. Eine lockere
Grenze darf keine beobachteten Lücken verschwinden lassen.

`markers.json` folgt dem ausgegebenen Metadatenschema. Jedes Referenzfenster
benötigt eine eindeutige Bezeichnung, Gehäuseachse, vorzeichenbehaftete
90°-/180°-Referenz, Beschreibung der externen Referenz sowie getrennte
Vorruhe-, Bewegungs- und Nachruheintervalle. Die Intervallgrenzen müssen
tatsächlich gespeicherte Sample-Zeitstempel sein. Es werden keine neuen
Zeitpunkte interpoliert oder aus dem gewünschten Winkel erzeugt. Die
Bestätigungen `reference_completed` und
`motion_bounds_include_stationary_margins` sind bewusste Angaben zum
tatsächlich ausgeführten Ablauf, keine automatisch angenommenen Fakten.

Ein optionales `axis_mapping` muss alle X/Y/Z-Achsen ausdrücklich als
Permutation der Rohkanäle 0/1/2 mit Vorzeichen ±1 angeben. Auch dieses Mapping
bleibt eine Hypothese. Ohne Mapping zeigt die Auswertung die Integrale aller
drei Rohkanäle, ohne einen davon zur angeblich richtigen Gehäuseachse zu
erklären.

## Bias, Integration und fünf getrennte Hypothesen

Die Auswertung bestimmt einen ausdrücklich experimentellen Bias aus den
ausgewählten Vor- und Nachruhe-Samples. Sie berichtet beide Ruheverteilungen
und ihre Mittelwertdifferenz separat. Damit bleibt eine Änderung während des
Tests sichtbar. Unruhige Ruhephasen werden bei der fachlichen Auswertung
verworfen; ein berechneter Mittelwert allein bestätigt keinen stabilen Bias.

Für jeden Rohkanal gilt mit aufgezeichneten Host-Zeitstempeln:

```text
Rohintegral = Σ ((raw[i] − Bias) + (raw[i+1] − Bias)) / 2 × Δt_in_Sekunden
Winkel_in_Grad = Rohintegral × hypothetischer_Faktor_in_Grad_pro_Sekunde_pro_Count
Winkel_in_Radiant = Winkel_in_Grad × π / 180
```

Verglichen werden unverändert alle fünf LSM6DS3TR-C-Arbeitshypothesen:

| Angenommener Messbereich | Hypothetische °/s je Rohwert |
| --- | --- |
| ±125 °/s | 0,004375 |
| ±250 °/s | 0,00875 |
| ±500 °/s | 0,0175 |
| ±1000 °/s | 0,035 |
| ±2000 °/s | 0,07 |

Der 125-dps-Wert stammt aus der vom Nutzer berichteten Datenblatttabelle;
ein lokales Originaldatenblatt wurde dafür nicht geprüft. Die vier anderen
Gewinne sind zusätzlich durch die gespeicherte Linux-Referenz gestützt.
Weder die tatsächliche Chipvariante noch der aktive Messbereich oder eine
unveränderte Sensorregister→USB-Skalierung sind damit bestätigt.

Nur mit einem ausdrücklichen Achsenmapping werden Winkelabweichung,
empirischer Faktorkandidat und Querachsenanteil unter dieser Mappingannahme
berechnet. Kein Ergebnis wählt automatisch ein Produktivprofil. Wiederholte
Drehungen in beiden Richtungen, verschiedene Winkel und die protokollierten
Referenzunsicherheiten müssen gemeinsam beurteilt werden.

## Abbruch und Abnahmekriterien

Ein Zählerfehler, doppelter oder rückwärts laufender Zeitstempel, Überschreiten
der expliziten Zeitgrenze, Instanzwechsel oder inkohärenter Satz verwirft die
gesamte Referenzanalyse. Auch Fehler außerhalb des Drehfensters werden nicht
herausgeschnitten. Es gibt keine nachgefüllten Samples und kein Teilintegral
als Kalibrierungsbeleg. Mögliche Gyro-Sättigung an einem int16-Endpunkt
verhindert ebenfalls die Referenzintegration.

Der für einen späteren echten Lauf vorbereitete Leser stoppt außerdem bei
Geräteende, veraltetem oder zukünftigem Host-Zeitstempel, ausbleibenden Daten,
neuen Pufferübergabefehlern sowie erkannter Suspend-/Uhrdiskontinuität. Eine
deaktivierte Stream-Freigabe `buffer_stream_active` oder eine unvollständige
abschließende Scanstruktur gilt ebenfalls als Fehler. Empfangene Bytes
und der Fehlerstatus bleiben gespeichert; der Leser versucht keine Reparatur.

Offline-Prüfungen verwenden konstruierte Bytefolgen, temporäre Fake-IIO-Bäume
und gemockte Gerätezugriffe. Sie belegen Decoder, Fehlerbehandlung und
Rechenweg, jedoch keine echte IIO-Pufferaufnahme oder physikalische
Kalibrierung:

```sh
python3 -B tests/test_imu_stream.py
python3 -B tests/test_gyro_reference.py
python3 -B tests/test_iio_buffer_setup.py
python3 -B tests/test_gyro_worker.py
python3 -B tests/test_gyro_guided.py
python3 -B tests/test_imu_diagnostic.py
python3 -B tests/check_kernel_iio_buffer.py
```

Vor dem ersten Referenzlauf fehlen externe Winkelreferenz, frischer Geräte-/
Abhängigkeitencheck, konkret freigegebene Host-Pufferkonfiguration samt Rückbau
und explizite Messfreigabe. Der ausführende KDE-Winkelassistent ist getrennt
von den reinen JSON-Planbefehlen und wurde noch nicht live gestartet. Die
bisherigen Hinweise aus dem Anzeigetest sind keine fertige Winkelmessung.

Eine zusätzliche evdev-Sensorschnittstelle und die SDL-3-/Eden-Abnahme bleiben
der spätere Schritt gemäß dem vorhandenen
[DualSense-Vergleich](DUALSENSE_SENSOR_COMPARISON.md). Die historischen
Anzeigeläufe und Profilannahmen stehen in
[EXPERIMENTAL_GYRO_TEST.md](EXPERIMENTAL_GYRO_TEST.md). IIO bleibt erhalten;
Produktivkalibrierung und SDL-Sensorausgabe werden durch diese
Offline-Vorbereitung nicht aktiviert.

## Ergebnis der Offline-Prüfung des pausierten Zwischenstands

`make test` ist vollständig bestanden. Die neuen Helfer bestehen 32 Puffer-
Transaktions-, 41 Worker- und 36 Frontendtests; der Leser besteht jetzt
58 Streamtests. Weiterhin bestanden: 43 Referenz- und 65 Diagnosetests.
Die zusätzlichen Tests prüfen geliehene FDs, Ein-Go-Ablauf, PING-Rückstau,
Abbruch während Aufbau, jeden Setup-Writefehler, Instanzersatz, fehlende
Rückstellung, ursprünglichen Fehler trotz Folgefehlern und unabhängige
Prüfsummen vor jeder Winkelanalyse. Keine echten Geräte oder Fenster.
Das Testprotokoll liegt lokal unter `build/gyro-checkpoint-tests.log` und
ist als Buildausgabe nicht für Git vorgesehen.

Der unveränderte tatsächliche Kernel-C-Pufferpfad
besteht 47 Testgruppen und drei absichtlich defekte Negativkontrollen.
Zwölf C→Python→Winkelanalyse-Fälle verwenden synthetische ±90°/±180°-Signale
auf allen drei Rohachsen; sie bestätigen den Rechenweg, keinen realen Faktor.
Lesen, Unterbrechung, Gate und Fehlererhalt werden dabei ohne Gerät geprüft.

Beim vorangegangenen Pufferbau wurde das Modul über `scripts/kernel_toolchain.py` separat nach
`build/kernel-coherent-iio/gs_native.ko` für die vorbereiteten Header
`7.2.11-1-garuda` gebaut: Kbuild Exit 0, passende Vermagic, keine Autoload-
Aliase, Abhängigkeiten `ff-memless,industrialio,kfifo_buf`. Ein Kbuild-Hinweis
bleibt ausdrücklich erhalten: der Kernel wurde mit Clang 23.1.1 gebaut,
lokal ist Clang 23.1.3 vorhanden. Keine weitere Compilerdiagnose im Log;
daher kein uneingeschränkt „warnungsfreier“ Bau. Der strengere bisherige
Wrapper `scripts/build_kernel.py` verwirft auch diesen Versionshinweis und
wurde dafür nicht abgeschwächt. Das ist kein Installationstest.

Eigene [Prüfmetadaten und Quellhashes](coherent-imu-validation.json) sind
versioniert; vollständige lokale Logs liegen unter `build/results/`.
Installierte Pakete und produktive SDL-Kalibrierung wurden nicht verändert.
