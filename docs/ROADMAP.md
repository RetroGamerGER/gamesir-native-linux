> Public export: personal tester, host and path references were anonymized. Historical evidence hashes refer to the private originals.

# GameSir Native Linux: Roadmap

Stand: 18. Oktober 2026. Prioritäten ergänzen den
[aktuellen Projektstand](PROJECT_STATE.md); historische Tests behalten ihren
jeweiligen begrenzten Nachweisumfang. Ein Roadmap-Eintrag ist keine Hardware-,
Installations-, Veröffentlichungs- oder Netzwerkfreigabe.

## 1. Stabile Alpha und Release-Abnahme

Lokal installiert: Manager-Reconnect-Korrektur in Paketrevision 6,
unverändertes Kernelmodul/ABI. Nach bestandenen Offline-Regressionen wurde das
ausdrücklich freigegebene Update installiert und lesend geprüft. Danach wurde
der Dienst vom Benutzer gestartet; ein erfolgreicher nativer Bootstrap ist
inzwischen beobachtet. Kontrollierte reale Wiederverbindung weiterhin
getrennt freigeben und abnehmen. Der freigegebene integrierte Forza-/Xodus-Test
nutzt zunächst die bestehende Verbindung und ersetzt diese Reconnect-Abnahme
nicht. Alter Fehlerzustand
wird nicht automatisch entsperrt. [Korrektur und Rückweg](MANAGER_RECONNECT_FIX.md).

Öffentliche Fassung ausdrücklich als **PRE-ALPHA** vorbereiten. Vollständigen
Warntext, Project Goals, unabhängige Referenzwürdigung sowie belegte
Funktions-/Plattformgrenzen in der README erhalten. Portable Installation,
Prüfung, Fehler-Rückweg und vollständige Entfernung stehen getrennt von den
historischen Laborberichten. [Release-Audit](RELEASE_AUDIT.md) trennt bestandene
Vorbereitungsprüfungen von offenen Artefakt-/Publikations- und Hardwareabnahmen.
Das ist keine neue Hardware-, Installations- oder Push-Freigabe.

Lizenzgrundlage für die Pre-Alpha: eigener Bestand GPL-2.0-only, vollständige
`COPYING` und UAPI-Ausnahme auch im DKMS-Paket, geprüfte Herkunft und klare
Grenze zu g7ctl/Herstellerreferenzen. Für spätere Kernel-Einreichung Herkunft,
Standard-Schnittstellen, Maintainerreview und wahrheitsgemäßen DCO nachweisen;
die Lizenz allein bewirkt keine Mainline-Aufnahme. [Lizenzbericht](LICENSING.md).

Den bestätigten autonomen CachyOS-/Gamescope-Betrieb, vier unabhängigen
Paddles, normale Eingaben, IMU-Rohdaten und Viermotor-Runtime erhalten.
[tester] testet Ship of Harkinian in Ruhe; währenddessen keine Treiber-/
Systemänderungen. Ein Boot-E2E-Fall ist bestätigt, keine allgemeine
Boot-/Suspend-/Hotplug- oder Langzeitzuverlässigkeit daraus ableiten.

Weitere Bootkonstellationen, Wiederverbindungen, Suspend, konkurrierende
Anwendungen, Kernel-/Steam-Updates und gegebenenfalls mehrere Dongles
getrennt planen, ausdrücklich freigeben und mit geprüftem Rückweg testen.
Garuda test host erst nach gesonderter Updatefreigabe angleichen. Release und Push
bleiben bis zur ausdrücklichen Entscheidung gesperrt.
Belege: [Gamescope](STEAM_GAMESCOPE.md),
[Bootstrap-Korrektur](BOOTSTRAP_CACHYOS_FIX.md).

## 2. Spielintegration und kalibrierte Sensoren

**Architekturvereinfachung offline bewerten:** Den
[xpad-/HID-Vergleich mit PandaPro8K](XPAD_HID_FEASIBILITY.md) weiterverfolgen.
Gespeicherte normale `100a`-Deskriptoren und einzelne IF1-Telemetriepakete
stützen einen möglichen Zusatzpfad bei erhaltenem XInput. Zuerst den
behaupteten Linux-Patch und die modellspezifische Aktivierung prüfen;
keine dauerhafte Ausgabe von Paddles/IMU oder vier Motoren daraus ableiten.
Ein gemeinsames Input-Gerät und koordinierte Motorstopps müssen beim
Entwurf erhalten bleiben. Kein Austausch der funktionierenden Runtime,
kein neuer USB-Befehl oder Hardwaretest aus diesem Analyseauftrag.

Der [separate Dateiprototyp](XPAD_HID_PROTOTYPE.md) ist inzwischen umgesetzt:
acht vorhandene Mitschnitte, 14 strukturell passende IF1-Berichte in drei kurzen
Rückkehr-Bursts, aber kein belegter Aktivierungsbefehl. Keyboard-LED-Ausgabe
`03 01`, framed IF0-Heartbeat und Pandas `0f f2` bleiben getrennt. Nächste
offene Hürde ist ein belastbarer normaler G7-Pro-IF1-Aktivierungsvertrag;
danach separat freigegebene Dauerstrom-/Paddle-/Release-/Reconnect-Nachweise.
Keine laufende Architektur ersetzen, bevor Input-Zusammenführung und alle
vier Motoren samt Besitz/Stopps gleichwertig gelöst sind. Kalibrierung pausiert.

Die [passiven 90-/300-Sekunden-Adapter](HID_PASSIVE_CAPTURE.md) sind separat
offline vorbereitet. Der spätere, eigens freigegebene Rückweg bestätigte eine
saubere `100a`-Ausgangsinstanz; der erste Aufnahmeversuch brach vor Modulladen
an der Prozesszugriffsprüfung ab. Die lesende Diagnose vom 18. Oktober konnte
diesen Fehler nicht reproduzieren. Genaue künftige Fehlerdiagnostik ist ergänzt;
Zugriffsfehler werden nicht ignoriert. Zwei später separat freigegebene
90-Sekunden-Läufe sind abgeschlossen. Erst der zweite mit geprüft offenem
Eingabeclient zeigte normale XInput-Berichte; IF1 lieferte nur kurze andere
HID-Berichte. Kein beobachteter Vendor-IMU-Strom oder Einzeltasten-Nachweis.
[Auswertung und Grenzen](HID_PASSIVE_CAPTURE_RESULTS.md).
Nächster Schritt ist gezielte Offline-Arbeit am belegbaren Aktivierungsvertrag,
ohne das 8K-Protokoll auf Verdacht zu senden oder den nativen Treiber zu ersetzen.
Manager pausiert/ohne Besitz, vollständige Zugriffsprüfung, usbmon-Verfügbarkeit
und frische Hash-/Instanzmetadaten bleiben Voraussetzungen. Offline-Tests ersetzen
keine Aufnahmefreigabe; Aktivierungsbefehle bleiben unbestätigt/gesperrt.

**Trigger-Bridge:** Der geprüfte eigenständige Forza-/Xodus-Nachweis wird als
optionale Userspace-Komponente integriert, nicht in den Kernel verschoben.
Die neue Fassung ergänzt eindeutige Instanz-/Quellzuordnung, versionierten
Transport, Frischeprüfung, Stopbarrieren und Geräteersatz-Abbruch sowie einen
getrennten Paketquellhelfer. Offline-Regressionen und die separat freigegebene
lokale Installation sind abgeschlossen. Xodus-Startzusatz vorbereitet;
effektive Benutzerberechtigung und native Brokerzuordnung geprüft.
Der erste integrierte Forza-Test zeigte keine Trigger-Vibration. Nach
Offline-Korrektur und gesondert freigegebenem Update/Lauf hat Revision 2
beide Trigger samt Pausen/Neustart und ruhigem regulärem Spielende bestätigt;
normale Eingaben und Griff-Rumble blieben erhalten. Die genaue Live-Ursache
des ersten Fehlversuchs bleibt unbekannt. Bestehende Eingaben,
Paddles, Griff-FF und Roh-IMU erhalten. [Umfang](TRIGGER_BRIDGE.md).

Nächste getrennte Schritte: weitere Xodus-Lifecycle-Fälle und den
Steam-/Proton-Ausgabepfad/ABI/Container prüfen. Unterstützte
Launcher-Hooks für automatische Nutzung entwickeln; keine globale Preload-
Umgebung oder unkontrollierten Konfigurationsänderungen. Fehlende getrennte
Spiel-Triggerbefehle nicht aus Achsen/Griff-Rumble erfinden. Reconnect, PM und
mehrere Geräte gesondert belegen. Forza-RT3x nicht global übernehmen.

Die [Offline-Machbarkeit für Steam/Proton](STEAM_PROTON_TRIGGER_BRIDGE.md)
ist inzwischen untersucht: SDL2-Einstieg in Proton vorhanden, aber aktuelle
Startvalidierung, Container-Pfade/Peer-PID und virtuelle Steam-Input-Geräte
verhindern eine pauschale Freischaltung. Als Nächstes einen separaten
geschlossenen Adapter mit Fake-Runtime/IPC-Tests entwickeln. Danach eine
ausdrücklich freigegebene technische Proton-Probe mit eigenem API-Test und
Fake-Ausgabe durchführen; dafür ist kein Trigger-Spiel erforderlich. Ein
solches Spiel steht derzeit nicht bereit, reale Spieleabnahme bleibt offen.
Paddles, Griffe und normale Eingaben erhalten; keine neuen Kernel-Patches.

**Referenzkalibrierung pausiert:** [tester] hat derzeit keinen geeigneten
Anschlagwinkel. Die vorbereitete IIO-Puffertransaktion und der einzelne
KDE-geführte 90°-Linkslauf bleiben als offline geprüfter Zwischenstand
erhalten. Erst nach neuem Auftrag, externer Winkelreferenz und frischer
Geräte-/Befehlsfreigabe weiterarbeiten. Keine automatische Wiederaufnahme;
der produktive Treiber und die bisherige SDL-Grenze bleiben bestehen.

Der separate [experimentelle Gyrodiagnosepfad](EXPERIMENTAL_GYRO_TEST.md)
bereitet fünf LSM6DS3TR-C-Hypothesen vor; kein Messbereich wird automatisch
ausgewählt. Gespeicherte IMU-Pakete sind unter allen fünf Faktoren vergleichbar,
ohne daraus eine bestätigte Kalibrierung zu machen. Die
[kohärente Standard-IIO-Pufferquelle](COHERENT_IMU_CALIBRATION.md) ist nun
offline implementiert: sechs Werte desselben Berichts, Host-Monotonzeit,
Annahmezähler, Pushfehler und PM-Gate. IIO-Einzelattribute genügen weiterhin
nur für die Live-Anzeige. Nächster Schritt ist nach gesonderter Freigabe
der Abgleich dieses neuen Pufferpfads auf Hardware, noch keine SDL-Freigabe.
Der private Control-Snapshot ist wegen Besitz-/STOP-Semantik keine harmlose
Abkürzung. Erst nach gesonderter Freigabe bekannte Drehwinkel mit Puffern,
Wiederholungen und sechs Ruhelagen messen. [tester]' Reihenfolge: erst eine
eigene Sitzung mit drei einzelnen 90° links, dann getrennt rechts, vorne,
hinten; Bereitschaft vor jeder Wiederholung, Rücksetzen außerhalb Integration.
180° und Rollen erst später separat. Danach Bias/Achsen/Faktor prüfen,
evdev-Sensorgerät ergänzen und lokalen SDL3-Tester vor Eden verwenden.
Weder heutige Implementierung noch Plan erlauben Hardware-/Systemänderungen.
Der inzwischen separat freigegebene 90-s-KDE-/IIO-Anzeigelauf ist bestanden:
alle drei Gyro-Rohkanäle reagieren. Der nächste Schritt bleibt die kohärente
passive Referenzmessung, keine Auswahl des realen Faktors aus diesem Anzeigetest.

- Unabhängige Paddle-Quellen erhalten; direkte Spielbelegung von Steam-
  Übersetzung und den Grenzen der jeweiligen Spiel-API unterscheiden.
- Spiele-FF_RUMBLE und die versionierte Viermotor-Schnittstelle erhalten;
  Trigger-Anwendungsadapter gezielt integrieren. Keine zusätzliche Kernel-UAPI
  oder universelle Steam-/Proton-Triggerunterstützung behaupten.
- IIO-Rohdaten weiter anbieten. Eigenständigen Gyrofaktor, Bias,
  physische Achsen/Vorzeichen, Zeitbasis und Accel-Kalibrierung belegen.
  8192 LSB/g bleibt austauschbarer experimenteller Wert. Danach zusätzliche
  kalibrierte evdev-Sensoren mit nachvollziehbarer SDL-Gamepad-Zuordnung prüfen.

Neuer externer Identifikationsbeleg am 16. Oktober: [tester] bestätigt die
DigiKey-Zuordnung LSM6DSO/LSM6DSOTR zu seinem Controllerfoto. [tester] stellt
inzwischen die exakte Variante infrage; Fotoauskunft erhalten, tatsächliches
Modell wieder offen. Keine erwiesene Korrektur auf TR-C. Originalfoto,
QR-Inhalt und Vendorantwort sind hier noch nicht lokal geprüft. Die fünf
berichteten Gyro-Sensitivitäten sind mögliche Referenzen, keine Auswahl.
Die lokale Linux-ST-Referenz bestätigt inzwischen 0x11/0x0c und vier
Gyrogewinne, nicht den aktiven GameSir-Messbereich oder die ±125-Kodierung.
Die innere Appstruktur ist nun über 288 Header-, 48 Bereichs- und 96
Datei-CRC aufgelöst; `app.bin`/`cfg_tool.bin` sind prüfsummengültig lesbar.
Drei MCU-Teilformate sind nun empirisch geprüft, aber Kompaktoperanden,
Speicher-/Vergleichsbefehle und ABI fehlen. Diese gezielt vervollständigen,
WHO_AM_I 0f mit Referenz 6a(TR-C)/6c(DSO) zum ID-/Sensorwahl-/Init-Pfad
verfolgen, dann letzte wirksame CTRL2_G-Einstellung und Sensorregister→USB-
Skalierung belegen. Kompilierte LSM6DS3TR-/QMI8658-Meldungen sind keine
neue Bestückungsfeststellung. Keine erneute
breite Chipsuche voraussetzen; weitere Varianten nicht automatisch mitidentifizieren.
[Quellenstatus und Rechnung](IMU-STATISTIK-UND-SENSORIDENTIFIKATION.rst).

Firmwareseitig erwartete IDs von der tatsächlichen ID des konkreten
Controllers trennen. Ein generischer ST-Pfad für mehrere Varianten bleibt
eine Hypothese. Später kann ein bereits vorhandener dokumentierter
Sensor-ID-Diagnoseweg gesondert bewertet werden; keine unbekannten
Gerätebefehle oder experimentellen I2C-Schreibzugriffe und keine aktuelle
Hardwarefreigabe daraus ableiten.

Abnahme: korrekte physikalische Einheiten und nachvollziehbare Achsen, keine
Ableitung des Gyrofaktors aus Accel oder ungeprüften Sony-Werten. Neue
Referenzmessungen brauchen eigene Freigabe. Embercade bleibt ein späteres
Integrationsziel, ist nicht installiert und kein Alpha-Blocker.
Referenzen: [SDL-/DualSense-Vergleich](DUALSENSE_SENSOR_COMPARISON.md),
[Haptik-API](HAPTICS_API.md), [Steam-Grenzen](STEAM_PROTON_BUTTONS.md).

## 3. Nexus als statische Referenz weiter nutzen

Ausgangsbasis: [Nexus 2.1.23.0](GAMESIR_NEXUS_RESEARCH.md), identifizierte
GIP-Update-DLL, getrennte Edition-/Controller-/Dongle-Paketkandidaten,
Windows-Versionsschnittstelle und Motion-/Kalibrierungsdialog.
Noch keine bestätigte Gyro-Skalierung oder sichere Firmwareimplementierung.

Nächste eng begrenzte Offline-Arbeit nach vorheriger Erläuterung des Ansatzes:

1. Native Modell-/DFU-Verbraucher, Live-Versionsquellen, Updatevergleich und
   Controller-/Dongle-Paketpaarung vollständig zuordnen. Konstruktoren und
   Dateinamen-Katalogversionen sind bereits statisch belegt. Paketnamen sind keine geprüfte
   VID/PID-/Hardwarekompatibilität. Gemeinsamen Standard-/ZZZ-Treiber behalten.
2. Mögliche weitere Sensorproduzenten und Kalibrierungsantworten
   verfolgen. [Belegte Datenflüsse](NEXUS_SENSOR_DATAFLOW.md): alle sechs
   Int32-Zugriffe aufgelöst, sieben geprüfte Eingabe-Zustandspfade lassen sie
   null; C2-Profilblock und /255 betreffen Konfiguration. D4X-Sendeweg und
   F1-Firmwarebridge sind zugeordnet. Folgepass vom 18. Oktober: typgebundene
   Profilantworten und generische JSON-/WebView-Weitergabe belegt. MessageC
   liefert im geprüften D4X-Körper auf normalen Rückwegen E_FAIL; tatsächlicher
   Caller und Sensor-Tag bleiben unbelegt. Diesen hypothetischen Abruf
   nachrangig behandeln. Gezielt offen: globale JSON-Settings/Converter,
   weitere Provider und vollständige Header-/Modellzuordnung. Kein Gyrofaktor
   oder Koeffizientenabruf; keine globale Abwesenheit behaupten.
   Profil-/EEPROM-Schreiben von Rohdaten- und Kalibrierungsabrufen trennen.
3. Äußerer Firmwarecontainer inzwischen mit eigenem Offline-Leser geöffnet:
   zwölf Header/Tabellen und 126 logische Eintrags-CRC bestätigt. Weitere
   Firmware-Sensorsuche hat inzwischen den Packed-Split (Feld `+8`) und
   48 gespeicherte Appcontainer belegt; 24 komplette Inhaltspaare sind nach
   Key-/No-Key-Normalisierung gleich. Der anschließende Positionsdecoder
   bestätigt app.bin/cfg_tool.bin vollständig einschließlich Inhalts-CRC.
   **Für den Gyrofaktor jetzt vorrangig:** MCU-Instruktionen und
   Sensorinitialisierung bis zum IMU-Report verfolgen: Sensor-ID/gewählter
   Pfad → letzter wirksamer Messbereich → mögliche Nachskalierung → USB.
   Den aktiven Registerwert nicht ohne Nachweis mit der USB-Skala gleichsetzen;
   Paketfirmware und tatsächlich installierte Version getrennt behandeln.
   Bestehende Werkzeuge weiter nutzen. Nach späterer ausdrücklicher Freigabe
   ist REA zusätzlich lokal und wiederverwendbar eingerichtet, mit
   kopierten Eingaben, privater Ausgabe und Netzwerk-/Geräteisolation.
   Keine Ausführung oder Emulation des untersuchten Herstellercodes.
   REA 6.5.0 unterstützt Jieli-Rohcode nicht direkt; der lokale Quarkslab-
   Pi32v2-Beschreiber ist an drei App-Versionen
   teilvalidiert: 150 Literal- und 150 Transferstellen stimmen mit bekannten
   Ankern überein; die geprüften Transfers verwenden `inst_next`. Die frühere
   `E041`-Nullerweiterungsdeutung ist korrigiert: Die ursprüngliche
   SLEIGH-Regel sagt Nullerweiterung,
   während 44/44 `E040`-Immediates im offiziellen Jieli-Pi32v2-ROM-Listing
   zur Vorzeichenerweiterung passen; 14 negative Werte widerlegen dort
   Nullerweiterung. Ein isolierter privater Decoderlauf findet je 16
   Maskeneinträge, die zu einem gemeinsamen maskierten Update-Helfer führen
   (Laden, AND mit Maske, Zurückschreiben). Das ist kein Sensorpfad.
   Ein Scan der getesteten kompakten und 22-Bit-Sprungformen fand keine
   eingehenden direkten Sprünge zu diesen Einträgen; indirekte Tabellen und
   die Erreichbarkeit bleiben offen. Der Kalibrierungslog erreicht den
   gemeinsamen Textlogger und wird gefolgt von einem Nullwort-Store an
   `((r0 + 0x115) << 1)` mit ungeklärter Basis-/Objektsemantik. **Korrektur
   vom 18. Oktober:** Der Code bei `0x10730`/`0x10738` referenziert
   `eeprom read over:`, nicht den ADC-Text; die EEPROM-Lese-/Schreibblöcke
   enthalten bedingte indirekte Aufrufe über einen ungeklärten Slot. Der echte
   `adc scan not over!!`-Text wird bei `0x7426` direkt geladen und zum
   Textlogger geführt; die folgenden Speicher-/Schleifenausdrücke haben
   ungeklärte ABI-/Registerwirkung und keinen belegten IMU-Bezug. Geprüfte
   direkte Sprung- und Zeigerformen fanden keine eingehenden Kandidaten zu den
   Kalibrierungs- und EEPROM-Lese-Logblöcken. Nächster Schritt ist die
   Zuordnung der Adressraum-/Codeabbildung und des EEPROM-Callback-Slot-Ursprungs,
   ohne diesen Aufruf als Sensorfunktion zu etikettieren.
   Die 64-Byte-Capture-IMU ist nicht mit einem Firmwareproduzenten oder den
   60-Byte-Nexus-Parsern verbunden; deren untersuchte Pfade lassen die
   Sensorfelder ungesetzt. WHO_AM_I, Sensorwahl, letzter CTRL2_G-Schreibwert
   und IMU-Reportpfad bleiben unbelegt. Der Beschreiber sowie Code-/Daten-
   segmentierung sind weiterhin unvollständig.
   [Werkzeugstand und neue Primärreferenzen](GAMESIR_NEXUS_RESEARCH.md#lokales-rea-und-neuer-jieli-referenzkandidat-18-oktober).
   Der MCU-Folgepass vom 18. Oktober belegt zusätzlich begrenzte kompakte
   Zielfelder/Maskenoperanden und eine getrennte Suffix-Adressabbildung.
   Darauf aufbauen, ohne eine vollständige ISA anzunehmen. Sensoranker
   liegen außerhalb des Suffix; fehlende Speicher-/Vergleichs-/Argument-
   semantik und eine belastbare Bytekodierungsreferenz bleiben die konkrete
   Grenze. Keine weiteren beliebigen Zahlenfunde als Registerwriter ausgeben.
   Globale Bank-/Modellauswahl und der DV-Inhalt hinter dem
   inneren Appbereich bleiben getrennt offen. MCU-Label
   AC695X und Flashversatz EOFFSET sind keine IMU-Kalibrierung. Key-/No-Key-/Kompatibilitäts- und
   Authentizitätsfragen bleiben getrennt offen. Keine Firmwareausführung
   oder Hardwareaktion aus der Dateidekodierung ableiten.
   Synthetische beschädigte/falsche Pakete müssen sicher zurückgewiesen werden.

Abnahme dieser Phase: reproduzierbare eigene Decoder und belegte
Anfrage-/Antwortspezifikationen auf gespeicherten Daten. Keine Ausführung
proprietären Codes, Online-Abfrage, USB-Kommandos, Bootloaderaktion oder
Weiterverteilung von Herstellerpaketen aus diesem Auftrag.

## 4. Spätere Firmwareunterstützung: eigene Entscheidung erforderlich

Ein Offline-Containerprüfer oder erkannter CRC ist keine Flashfreigabe.
Vor einem Linux-Updater fehlen vollständige Transport-/Antwortkorrelation,
Versions-/Hardware-/Paketprüfung, Authentizitäts-/Integritätsbewertung,
Bootloaderidentitäten, Abbruch-/Stromausfallbehandlung und ein belastbarer
Rückweg für Controller **und** Dongle. Ein geprüfter Entwicklerplan und eine
gesonderte konkrete Freigabe sind Voraussetzung für jeden realen Versuch.

Architekturziel: separate optionale Userspace-Anwendung mit exklusiver,
expliziter Übergabe durch den nativen Manager. Kein Flashen im Kernel oder
Alpha-Autostart, keine automatischen Firmwareupdates und keine parallelen
USB-Besitzer. Keine proprietäre Firmware in Repository oder Linux-Paket;
die Bezugsmöglichkeit und Rechte müssen vor einer Veröffentlichung geklärt
sein. Firmwareforschung blockiert den bereits funktionierenden Spielbetrieb
oder die unabhängige Entwicklung der Sensor-/Spielintegration nicht.
