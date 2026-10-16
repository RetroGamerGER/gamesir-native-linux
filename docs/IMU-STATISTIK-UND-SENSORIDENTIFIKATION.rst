.. note:: Public export: private tester, host and path references anonymized; historical hashes refer to private originals.

G7 Pro: IMU-Statistik und Sensoridentifikation
============================================

Stand: 11. Oktober 2026, ausschließlich gespeicherte Dateien und öffentliche Quellen
---------------------------------------------------------------------------------

Alle 12.204 erfolgreichen IMU-Pakete sind statistisch ausgewertet und aus
den gespeicherten Paketbytes unabhängig decodiert worden. Das Ergebnis
stützt ungefähr 8192 Zähler/g als Beschleunigungsmaßstab. Es belegt weder
exakt diesen Gewinn noch einen bestimmten Sensorchip oder Gyrofaktor.
Nach dem damaligen Quellenstand vom 11. Oktober blieb die Chipidentifikation
offen; [tester] wollte den Chipaufdruck selbst prüfen. Die neue externe
Fotoidentifikation vom 16. Oktober steht in der Ergänzung direkt darunter.
Diese statistische Auswertung führte keine Hardwarezugriffe aus.

Aktualisierung nach MCU- und Variantendiskussion, 16. Oktober
-----------------------------------------------------------

[tester] hält eine Verwechslung der exakten Sensorvariante bei DigiKey für
möglich und berichtet, dass die beiden Gehäuse gleich aussehen. Die frühere
Fotoauskunft bleibt als Quelle erhalten; das tatsächliche Modell wird wieder
offen geführt. Weder ein DigiKey-Fehler noch ein eingebauter TR-C ist bewiesen.
Firmwarestrings sind weiterhin keine Chipidentifikation.

Die vorhandene lokale Linux-ST-Referenz bestätigt WHO_AM_I bei 0x0f mit
erwartet 0x6a für LSM6DS3TR-C und 0x6c für LSM6DSO. Der ursprüngliche
LSM6DS3 verwendet 0x69; auch DSOX hat 0x6c. Die Referenz-Gewinntabellen
von TR-C und DSO sind identisch, daher trennt ungefähr 8192 Zähler/g diese
Kandidaten nicht. Kein ID-Wert wurde vom GameSir gelesen. Ein generischer
ST-Pfad für mehrere Varianten ist möglich, aber nicht nachgewiesen.

Der neue MCU-Pass erhärtet drei begrenzte Muster für Adressliterale,
relative 22-Verweise und vorzeichenbehaftete 16-Konstanten. Ein versionsübergreifend
gleicher Textausgabe-Zielkandidat zur Kalibriermeldung ist identifiziert;
ein vollständiger ISA-/ABI-/Kompakt-/Speicherdecoder fehlt. 175 Kontrollen
und acht Ablehnungstests bestehen. WHO-Lesen → ID-Vergleich → Sensorwahl/
Initialisierung → letzter wirksamer CTRL2_G-Wert → USB-Skalierung bleibt
unbelegt. Keine Schlussfolgerung aus unzugeordneten Bytefolgen oder aus
dem Fehlen einer ID in den bisher bekannten langen Literalformen.

Ein bereits dokumentierter Diagnoseweg wäre später gesondert zu prüfen;
keine unbekannten Befehle oder experimentellen I2C-Schreibzugriffe daraus
ableiten. Aktuell ausschließlich statisch/offline, keine neue Hardwarefreigabe.
Details und Hashes: GAMESIR_NEXUS_RESEARCH.md, nexus-source-manifest.json
unter mcu_sensor_followup_20261016. Aktuelle Modellunsicherheit und historische
Fotoauskunft: imu-sensor-identification.json. Alle folgenden älteren
Ergänzungen behalten ihren damaligen Erkenntnisstand; kein Gyrofaktor gewählt.

Ergänzung: DigiKey-Fotoidentifikation vom 16. Oktober 2026
--------------------------------------------------------

[tester] bestätigt ausdrücklich, dass DigiKey den Typ LSM6DSO/LSM6DSOTR
anhand eines Fotos aus seinem G7 Pro identifiziert hat. Dieser Nutzerbeleg
wird als bestätigte externe Fotozuordnung geführt. Das Originalfoto,
der ausgelesene 2D-Code und die Originalantwort sind in diesem Arbeitsgang
nicht vorhanden; eine eigene Sichtprüfung oder Herstellerbestätigung
wird nicht behauptet. Die konkrete PCB-Revision und weitere Exemplare/
Editionen sind daraus nicht identifiziert. Die Samsung-Querverweisung
1209-002578 stammt aus dem eingefügten Bericht und ist separat ungeprüft.

Der neue Befund ergänzt den damaligen offenen Identifikationsstand; er
ändert keine Statistik der 12204 Pakete und keine Laufzeitkalibrierung.
Maschinenlesbare Herkunft und Status: imu-sensor-identification.json.
Es fand keine Netzwerkabfrage, Hersteller-App-Ausführung, Registerabfrage
oder sonstige Hardware-/Systemänderung statt.

Die im eingefügten, KI-unterstützten Bericht genannten Empfindlichkeiten
sind noch nicht gegen ein hier vorhandenes ST-Original geprüft. Ihre
Kehrwerte lassen sich dennoch eindeutig berechnen:

.. list-table:: Berichtete Referenzwerte, keine gewählte Kalibrierung
   :header-rows: 1

   * - Messbereich (Grad/s)
     - Berichtete mdps/LSB
     - Rechnerische LSB/(Grad/s)
   * - ±125
     - 4,375
     - 228,571429
   * - ±250
     - 8,75
     - 114,285714
   * - ±500
     - 17,5
     - 57,142857
   * - ±1000
     - 35
     - 28,571429
   * - ±2000
     - 70
     - 14,285714

0,122 mg/LSB ergibt rechnerisch 8196,721311 LSB/g, rund +0,0576 Prozent
gegenüber 8192. Diese Nähe ist mit gerundeten Angaben vereinbar, bestätigt
aber weder den aktiven ±4-g-Modus noch unveränderte Firmwarezählwerte.
Die Beschleunigungsskala legt weiterhin keinen Gyromessbereich fest.

Die zunächst nur berichteten WHO_AM_I-/CTRL2_G-Suchanker wurden im unten
beschriebenen Folgepass anhand einer vorhandenen Linux-Treiberdatei präzisiert.
Es sind weiterhin keine am GameSir gemessenen Registerwerte oder freigegebenen
USB-Kommandos. Ein lokales ST-Originaldatenblatt wurde nicht gefunden.
Eine kontrollierte Referenzdrehung wäre ein separat freizugebender unabhängiger
Nachweis des effektiven USB-Gyrofaktors.

**Weiter offen:** aktiver Gyro-Messbereich, Sensorregister→Firmware→USB-
Skalierung, physische Achsen und Bias. Kein Faktor ausgewählt; experimentelle
8192 LSB/g und die eingeschränkte SDL-Freigabe bleiben unverändert.

Gezielte Firmwareprüfung: CTRL2_G, 16. Oktober 2026
--------------------------------------------------

**Stand dieses ersten Folgepasses: Der aktive GameSir-Gyromessbereich
ist noch nicht belegt.**
Neu abgesichert sind Registeradresse und vier normale Messbereichsbitwerte
aus einer lokalen Linux-Referenz. Die Sensorinitialisierung in der
GameSir-Firmware konnte noch keiner gültig dekodierten Routine zugeordnet
werden. Kein Standardwert oder wahrscheinlichster Faktor wird gewählt.

Als zusätzliche Primärreferenz wurde ausschließlich die gespeicherte
In-Tree-Treiberdatei st_lsm6dsx aus dem vorhandenen Garuda-Kernelpaket
7.2.10-1 statisch untersucht. Das Modul wurde nicht geladen oder ausgeführt.
Symbol-/Relokationstabellen, BTF-Typinformationen und passende IIO-Header
belegen folgende Zusammenhänge; das ersetzt kein ST-Originaldatenblatt:

* Der LSM6DSO-Eintrag erwartet WHO_AM_I 0x6c; der Probe-Code liest Register
  0x0f. Auch LSM6DSOX erwartet dort 0x6c: kein eindeutiger Typnachweis allein.
* Die durch den Namen ``%s_gyro`` zugeordnete Tabelle verwendet Register
  0x11 mit Maske 0x0c. Der Schreibpfad verschiebt die Feldwerte 0/1/2/3
  um zwei Bits und übergibt 0x00/0x04/0x08/0x0c an regmap_update_bits.
* Die vier gespeicherten Gewinne 152716/305432/610865/1221729 werden als
  rad/s pro Zähler mit Nano-Nachkommastellen ausgegeben. Die Umrechnung
  mit dem passenden IIO_DEGREE_TO_RAD-Makro ergibt unabhängig genau diese
  Ganzzahlen aus 8,75/17,5/35/70 mdps/LSB.

.. list-table:: Lokale Linux-Referenz; keine GameSir-Registermessung
   :header-rows: 1

   * - Maskierter Wert in Register 0x11
     - Bestätigter Referenzgewinn (mdps/LSB)
     - Zugehöriger berichteter Nennmessbereich
   * - 0x00
     - 8,75
     - ±250 Grad/s
   * - 0x04
     - 17,5
     - ±500 Grad/s
   * - 0x08
     - 35
     - ±1000 Grad/s
   * - 0x0c
     - 70
     - ±2000 Grad/s

Die Nennmessbereichsbezeichnungen stammen aus der berichteten Tabelle;
das lokale Binärmodul enthält die Gewinne und Registerfelder. Seine
Vierertabelle belegt keine Kodierung des gesonderten ±125-Grad/s-Modus
und schließt dessen Verwendung durch GameSir nicht aus. Auch andere
CTRL2_G-Felder oder die aktive Abtastrate sind damit nicht dekodiert.

Konkrete ELF-Fundstellen: .rodata ab Dateioffset 0x6280; LSM6DSO-ID-Eintrag
bei .rodata+0x1910, Gyrotabelle bei Dateioffset 0x7ee0 (40 Byte).
Die .text-Offsets 0x927/0x92d belegen WHO_AM_I-Lesen; 0x1db1…0x1ded den
Masken-/Schreibpfad. Das sind Abschnittsversätze eines relocatable ELF,
keine Firmwareadressen. Die dekomprimierte Moduldatei hat SHA256
cc460b79659ff53a6fd69db2444f67fe0de87bf0ace5feb3da3648934d2b6669.
Weitere Quell-/Bereichshashes stehen in imu-sensor-identification.json.

Firmwareprüfung mit diesen Suchankern:

* Alle zwölf vorhandenen G7-Pro-UFW-Quellen und 48 extrahierten Flashdateien
  erneut gegen ihre Quellenhashes geprüft. 48 gespeicherte Appinhalte und
  48 Metadatenköpfe bestehen die bekannten CRC-Prüfungen.
* Zuerst die 24 Controller-DV-Dateien, getrennt davon 24 Dongle-DG-Dateien
  untersucht: gespeicherter Körper, bereits belegte Key-/No-Key-
  Klassennormalisierung und äußerer Prefix. Nur die Metadaten gelten als
  dekodiert; Körper/Prefix werden nicht als verifizierter Maschinencode ausgegeben.
* Keine Treffer für die fünf geprüften Namen LSM6DSO, CTRL2_G, WHO_AM_I,
  gyro_fs und gyroscope in ASCII/UTF16. Kurze 0f/6c-Muster kommen wie
  Vergleichswerte 0f/6b und 0f/6d mehrfach vor. Hinter 0x11 finden sich
  Kandidaten für alle vier Maskenwerte. Kein solcher Treffer ist ein
  belegter Registerzugriff.
* Die Suche nach drei aufeinanderfolgenden Registern 0x10/0x11/0x12 in
  Byte-, 16- oder 32-Bit-Tabellen ergibt acht gespeicherte und 16
  normalisierte DV-Treffer. Es sind zwei wiederkehrende Bytefolgen über
  WFF-/ZZZ-Dateien, Dateiklassen und Bänke; keine unabhängigen
  Initialisierungsbelege. Ohne gültige Körperdekodierung und Codeverweis
  lässt sich daraus kein CTRL2_G-Schreibwert bestimmen.
* Für 36 strukturähnliche Folgerecords wurden begrenzte Headerlängen-
  und Offset-/CRC-Hypothesen geprüft. Keine bestand die jeweilige Prüfung.
  Weder eine defekte Firmware noch die Abwesenheit anderer Formate ist damit
  bewiesen. Bestehende Key-/No-Key-Inhaltsgleichheit bleibt bestätigt.

**Damals verbleibender Schritt:** die innere Appstruktur/Körperdarstellung
mit belastbarer Prüfsummenabdeckung auflösen; anschließend ausführbaren
Initialisierungspfad, letzte wirksame CTRL2_G-Konfiguration einschließlich
möglicher Rekonfiguration und Sensorregister→USB-Zählwertabbildung verfolgen.
Eine irgendwo gespeicherte Startkonstante wäre noch kein Beleg des aktiven
Laufzeitmessbereichs. Die 12.204 Pakete ohne Winkel-/Drehratenreferenz lösen
diese Auswahl nicht auf.

Private neue Belege: .local/research/20261016-lsm6dso-ctrl2g/.
Frühere Quellen und Auswertungen unverändert erhalten. Keine Hersteller-
Dateien, Masken oder Schlüssel in Git, keine Netzwerk-, Hardware-, Treiber-
oder Laufzeitänderung. 8192 LSB/g bleibt experimentell; Gyrofaktor, aktive
Range und SDL-Freigabe bleiben unverändert offen.

Nachfolge: Innere Appdateien und CRC-Abdeckung aufgelöst
------------------------------------------------------

Der anschließende Strukturpass vom 16. Oktober löst die zuvor genannte
Körper-/CRC-Blockade für app.bin und cfg_tool.bin. Eine positionsabhängige
Dekodierung ab Beginn des gespeicherten Appinhalts ergibt in allen 48
Flashdateien sechs gültige Records: app_area_head, app.bin, cfg_tool.bin,
VM, PRCT und BTIF. Das Verzeichnis belegt 0xc0 Bytes. Das Feld app_area+8
ist das Bereichsende relativ zu dessen Beginn; seine Inhalts-CRC umfasst
die dekodierten Bytes [32, Ende), nicht einen gleich langen Körper nach
dem Header. app.bin beginnt bei 0xc0, cfg_tool.bin schließt direkt an und
endet am Bereichsende. Keine VM-/PRCT-/BTIF-Adresse als Datei versetzen.

288 Header-, 48 Bereichs- und 96 Datei-CRC bestehen. Eine unabhängige zweite
Stream-/CRC-Implementierung reproduziert alle 48 Inhalte bytegenau;
24 falsche-Ursprungs-/Beschädigungsprüfungen werden zurückgewiesen.
CRC allein reicht nicht: Zwei mögliche Streamzustände pro Header passen
zur Prüfsumme; Namen, Grenzen und Inhalts-CRC bestätigen zusätzlich die
gemeinsame Positionsabbildung. Key-/No-Key-Paare und enthaltene Dateien
über die vier Flashvarianten sind ebenfalls bytegleich. Alle 727 früheren
Belegdateien sind unverändert.

In der nun lesbaren Controller-App stehen konkrete Meldungen für
LSM6DS3TR, QMI8658, Sensor-Kalibrierung und gyro factory. Das sind neue
Firmwareanker, kein Nachweis des auf [tester]' Foto identifizierten oder
zur Laufzeit gewählten Chips. Externe LSM6DSO-Zuordnung unverändert
separat erhalten. Die Meldungen belegen noch keinen Messbereich oder
Kalibrierungskoeffizienten. Im DV209-Appinhalt liegt ein Adressliteral
für Enter Sensor Cal Mode bei 0x1071a; ein ausgeführter Aufruf ist daraus
noch nicht dekodiert.

**Jetzt offen:** belegtes MCU-Befehlsformat und statischer Decoder, dann
Sensorwahl/Initialisierung, letzte wirksame CTRL2_G-Einstellung einschließlich
Rekonfiguration und Register→USB-Skalierung. Keine erneute pauschale
Chipsuche und keine Schlussfolgerung aus einzelnen Registerbytefolgen.
Aktiver Gyromessbereich/Faktor bleiben null, 8192 experimentell und das
SDL-Kalibrierungsprofil bytegleich. Keine Appausführung, Firmwareemulation,
Netzwerk-, Hardware- oder Treiberaktion.

Ausführliche Struktur-/Quelltabelle: GAMESIR_NEXUS_RESEARCH.md.
Metadaten: nexus-source-manifest.json, inner_app_structure_20261016;
private Belege: .local/research/20261016-inner-structure-followup/.

Daten und Prüfbarkeit
--------------------

Messung B: 3537:109c über den 2,4-GHz-Dongle, erfolgreiche 64-Byte-Berichte
von Endpunkt 0x82. Die 12.204 Rohwerttupel stimmen vollständig mit den
separat gespeicherten Paketbytes überein. Original-PCAPNG und relevante
Analyse-/Phasendateien wurden gegen ihre vorhandenen SHA256-Werte geprüft.
Keine Originaldatei wurde geändert.

Original-SHA256:
4045577a7a9e7a1a0f84307a45e96fd524cd7dea1d4af276ebd7db20a0994a89

Analyseprogramm: tests/analyze_imu_calibration.py (Python-Standardbibliothek).
Maschinenlesbarer Befund: docs/imu-calibration-analysis.json.
Abbildung: docs/imu-statistik.png. Sie zeigt alle Samples; die mittlere
Ansicht stellt die ausgewählten ruhigen Fenster separat dar.

Die Standardabweichungen sind Populationswerte. Perzentile verwenden den
geordneten Wert bei floor(p * (n - 1)); der Median verwendet die übliche
Mitte. Zeitlich benachbarte Werte sind nicht als unabhängige Wiederholungen
behandelt. Es wird kein statistisches Konfidenzintervall für eine absolute
Gerätekalibrierung behauptet.

Gesamtstatistik aller Samples
----------------------------

.. list-table:: Rohzählwerte, einschließlich aller Bewegungen
   :header-rows: 1

   * - Kanal
     - Minimum
     - Maximum
     - Median
     - Standardabweichung
   * - G0
     - -3688
     - 5252
     - 0
     - 452.456
   * - G1
     - -2058
     - 2555
     - 0
     - 241.415
   * - G2
     - -4604
     - 4081
     - 0
     - 522.302
   * - A0
     - -8854
     - 8715
     - 255
     - 1605.958
   * - A1
     - -953
     - 21518
     - 8199
     - 1519.043
   * - A2
     - -10341
     - 5510
     - -704
     - 1940.354

Die Gesamtmittelwerte enthalten Bewegung und sind keine Sensor-Offsets.
G0/G1/G2 liegen als signed LE16 an Byte 17/19/21; A0/A1/A2 an Byte 23/25/27.
Keine der sechs Achsen erreicht -32768 oder +32767. Das schließt interne
Begrenzung oder Firmware-Verarbeitung unterhalb dieser Werte nicht aus.
Kein benachbartes vollständiges Sechsachsentupel ist identisch; daraus folgt
weder eine interne Sensor-Abtastrate noch die Unabhängigkeit der Samples.

Beschleunigungsbetrag über alle 12.204 Samples:

* Minimum 2467.936, Maximum 21573.229 Zähler.
* Median 8232.185, Mittelwert 8420.653 Zähler.
* 5.-95. Perzentil 7887.179 bis 9297.828 Zähler.
* 5497 Samples innerhalb ±1 Prozent von 8192,
  8403 innerhalb ±5 Prozent.

Die bewegten Abschnitte enthalten zusätzliche Beschleunigung. Deshalb
werden weder ihr Gesamtmittelwert noch ihr Median zur 1-g-Kalibrierung
verwendet. Der größte Betrag entspräche beim Kandidatenmaßstab rund
2.633 g; dies ist ausdrücklich eine bedingte Umrechnung.

USB-Zeitverhalten
----------------

Zwischen erstem und letztem IMU-Bericht liegen
195.163454 Sekunden. Für die 12.203
Host-Zeitabstände ergeben sich:

* Median 16.000 ms,
  Mittelwert 15.993072 ms.
* 5.-95. Perzentil 14.000 bis
  18.001 ms.
* Minimum 1.986 ms,
  Maximum 200.007 ms.
* 30 Abstände unter 8 ms, 12.156 zwischen 8 und unter 24 ms,
  17 ab 24 ms; davon 3 ab 32 ms.
* Beobachtete mittlere Rate 62.52708 IMU-Berichte/s.

Das ist die Host-Ankunftsfolge dieses Telemetriekanals. Sie belegt keine
1000-Hz-IMU, keine interne Sensor-ODR und für einzelne lange Abstände auch
keinen bestimmten Funk-/Sensorverlust. Die 1000-Hz-Gamepad-Einstellung ist
eine andere Größe. Eine Geräteuhr ist weiterhin nicht identifiziert.

Überprüfung des 8192-LSB/g-Kandidaten
-----------------------------------

Zentrales Ruhefenster: 375 Samples in den sechs Sekunden zwischen Ruhe-
Signal +2 und +8 Sekunden. Median des Beschleunigungsbetrags:
8215.838 Zähler, also +0.291 Prozent gegenüber 8192.
Bei diesem Kandidaten entspräche der Betrag 1.002910 g. Das frühe flache
Fenster T+47..64 liefert einen Median von 8216.748 Zählern.

Zusätzlich wurden alle Daten in feste Zweiersekunden-Fenster unterteilt.
Ruheheuristik: mindestens 120 Samples und 1.9 Sekunden Zeitspanne;
Gyro-Standardabweichung je Achse höchstens 5 Rohzähler, Gyrobetrag stets
höchstens 25, Beschleunigungs-Standardabweichung je Achse höchstens 25.
29 Fenster mit insgesamt 3624 Samples erfüllen diese Bedingungen.
Ihre Betragsmediane liegen bei 8195.080 bis
8218.557 Zählern, also etwa +0.038 bis +0.324 Prozent gegenüber 8192.
Die Heuristik beweist keine bekannte statische Lage und schließt konstante
Translation nicht aus.

Die Richtungen ihrer mittleren Beschleunigungsvektoren unterscheiden sich
höchstens um 1.996 Grad. Alle sind stark auf +A1 ausgerichtet.
Die wiederholten Ruheabschnitte liefern daher hauptsächlich dieselbe flache
Lage. Es fehlen hinreichend verschiedene positive/negative Achslagen zur
Trennung von Offset, Gewinn und Montageorientierung. Ein scheinbar genauer
neu angepasster Maßstab wäre damit überinterpretiert.

Bewertung: 8192 ist ein gut passender nominaler Kandidat. Ein absoluter
Nachweis oder ein kalibriertes Profil lässt sich damit nicht freigeben.
Auch die Ableitung eines ±4-g-Sensormessbereichs gilt nur, wenn die Firmware
die passenden Sensorzählwerte unverändert überträgt.

Sensoridentifikation: geprüfte Quellen und Grenze
------------------------------------------------

Deadband, Commit 771b28ae75b0a614a6a7fec9aa606606a27b3b8d,
kennzeichnet Skalierung und Orientierung ausdrücklich als unkalibriert.
Decoder, Weitergabe und QML-Anzeige enthalten keinen belegten IMU-Typ,
keinen WHO_AM_I-Befund und keinen physikalischen Gyrofaktor.
Die fünf relevanten installierten Anwendungsdateien sind bytegleich mit
unserem gespeicherten Quellstand. Deadband wurde nicht importiert oder
verändert.

Die in g7ctl/PROTOCOL.md verwendete Beschreibung der IMU-Identifikation
belegt die Einordnung der zwei Kanalgruppen als Gyro und Beschleunigung.
Sie nennt keinen Siliziumtyp. Die dortige 8192-Annahme ist daher ebenfalls
keine Identifikation eines konkreten Sensorchips.

Die veröffentlichte FCC-Innenansicht zu 2AF9S-G7PRO, Dokument 8420178,
wurde auf allen drei Seiten sowie im eingebetteten Platinenfoto geprüft.
Der PDF-Hash stimmt mit den veröffentlichten Metadaten überein:
0b5c4e0486197af5c9bedb44ca0e96b610e170d42c854bf26f8e1402e29c0fa4.
Die Auflösung reicht nicht für einen eindeutigen IMU-Aufdruck. Die Aufnahme
weist außerdem nicht die konkrete Platinenrevision unseres Controllers nach.
Öffentlich gelistete Schaltplan-/Blockdiagramm-Metadaten liefern hier keinen
lesbaren Bauteilnachweis. Ein verlinkter weiterer Teardown betrifft laut
Autor ein Vorseriengerät und lieferte keinen auswertbaren Chipbeleg.

Herstellerdatenblätter als Gegenprobe, keine Bauteilkandidaten
------------------------------------------------------------

Bosch BMI270: Das Herstellerdatenblatt BST-BMI270-DS000-08 nennt bei ±4 g
8192 LSB/g; die Gyro-Empfindlichkeit ist separat messbereichsabhängig.
Bei ±2000 Grad/s sind 16.384 LSB/(Grad/s) angegeben, bei ±1000 Grad/s 32.768.
Fundstellen: Tabelle 2, Seite 12; Gyro-Tabelle, Seite 14.

ST LSM6DS3TR-C: DocID030071 Rev 3 nennt bei ±4 g 0.122 mg/LSB, entsprechend
rund 8196.72 LSB/g. Bei ±2000 Grad/s sind es 70 mdps/LSB, entsprechend
rund 14.2857 LSB/(Grad/s). Auch hier wird der Gyro-Messbereich separat gewählt.
Fundstelle: Tabelle 3, Seite 21.

Beide Beschleunigungsmaßstäbe liegen nahe unseren Ruhewerten, während die
Gyrofaktoren bereits bei gleichem nominalen Messbereich verschieden sind.
Diese Beispiele belegen keine Bestückung des G7 Pro. Sie zeigen, weshalb
8192 allein weder einen Chip noch einen Gyrofaktor festlegt.

Aus dem damaligen Quellenstand vom 11. Oktober folgte kein engerer,
belegter Gyro-Empfindlichkeitsbereich. Die damals fehlende Typzuordnung ist
inzwischen durch die oben dokumentierte externe Fotoidentifikation ergänzt.
Weiter erforderlich sind der aktive Gyro-Messbereich oder eine dokumentierte
bekannte Winkeldrehung. Zusätzlich bleibt zu prüfen, ob die Controller-Firmware
Sensorregisterzählwerte unverändert weitergibt oder umrechnet. Eine Chip-
identifikation allein bestimmt diese beiden Punkte noch nicht.

Folgen für die vorbereitete SDL-Ausgabe
--------------------------------------

Die Kanaldecodierung ist belegt; der gerätefreie SDL-Ausgabevertrag wurde
mit zwölf Bibliotheksfällen erfolgreich geprüft. Der gemeinsame C-Konverter
arbeitet mit rationalen Faktoren und lehnt unbestätigte Kalibrierung ab.
Die 16 beziehungsweise 16.4 Zähler/(Grad/s) in den künstlichen Testfällen
bleiben Testkonstanten. Kein Herstellerbeispiel wird automatisch übernommen.

Für echte physikalische SDL-Werte fehlen weiterhin der Gyrofaktor,
vorzeichenrichtige Controller-/SDL-Achsen und eine belegte Offset-/Skalen-
behandlung. Das vorbereitete Profil behält runtime_enable=false und
verified_flags=0. Rohdaten und normale Eingabe-/Motorprotokolle können
unabhängig davon weiter offline untersucht werden.

Aktualisierung auf Nutzeranweisung: Der experimentelle Beschleunigungswert
8192 Zähler/g ist jetzt im Profil eingetragen und über eine gesonderte
C-Funktion austauschbar nutzbar. Alle 12204 gespeicherten IMU-Samples wurden
damit offline umgerechnet. Das bestätigt die Implementierung, nicht den
physikalischen Maßstab. Gyrofaktor und endgültige SDL-Ausgabe bleiben
unabhängig davon offen. Die Suche nach dem Sensorchip blockiert diesen
Entwicklungspfad nicht. Siehe EXPERIMENTELLE-BESCHLEUNIGUNG.rst.

Details: SDL-SKALIERUNG-UND-ACHSEN.rst und sdl-sensor-calibration.json.
Es gab keine neuen Aufnahmen, USB-Befehle, Deadband-Sitzungen, erhöhten
Rechte, Treiber-, Profil-, Firmware-, System- oder Kerneländerungen.

Quellen
-------

Deadband-Decoder:
https://github.com/broroeror/gamesir-linux-tools/blob/771b28ae75b0a614a6a7fec9aa606606a27b3b8d/vendors/gamesir/models/g7pro/protocol.py

g7ctl-Protokoll, Abschnitt zum 0x10-Eingabestrom:
https://github.com/questionablesyntax/g7ctl/blob/0ea4b5223ba2191c88a3c4d1ff8d34f594bfeb1b/PROTOCOL.md

FCC-Ausstellungsseite und Original-Download:
https://fccid.io/2AF9SG7PRO/Internal-Photos/Internal-photos-8420178
https://apps.fcc.gov/eas/GetApplicationAttachment.html?id=8420178
Die Originaladresse lieferte HTTP 403. Die unveränderte PDF wurde vom
öffentlichen Spiegel geladen und per veröffentlichtem SHA256 verglichen.

Bosch-Herstellerdatenblatt:
https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmi270-ds000.pdf

ST-Herstellerdatenblatt (öffentlich über Web-Lesezugriff geprüft):
https://www.st.com/resource/en/datasheet/lsm6ds3tr-c.pdf

Teardown-Vorserienkontext (keine verwendete Chipzuordnung):
https://www.reddit.com/r/Controller/comments/1mbj0gc/g7_pro_testers_review_teardown/
