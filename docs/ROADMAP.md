> Public export: personal tester, host and path references were anonymized. Historical evidence hashes refer to the private originals.

# GameSir Native Linux: Roadmap

Stand: 17. Oktober 2026. Prioritäten ergänzen den
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
   F1-Firmwarebridge sind zugeordnet. Gezielt offen bleiben MessageC mit
   getaggten UInt64-Werten ohne bekannten Kalibrierungstag, andere indirekte
   Provider sowie vollständige Header-/Modellzuordnung. Kein Gyrofaktor oder
   Koeffizientenabruf; keine globale Abwesenheit behaupten. Profil-/EEPROM-
   Schreiben weiterhin von Rohdaten- und Kalibrierungsabrufen trennen.
3. Äußerer Firmwarecontainer inzwischen mit eigenem Offline-Leser geöffnet:
   zwölf Header/Tabellen und 126 logische Eintrags-CRC bestätigt. Weitere
   Firmware-Sensorsuche hat inzwischen den Packed-Split (Feld `+8`) und
   48 gespeicherte Appcontainer belegt; 24 komplette Inhaltspaare sind nach
   Key-/No-Key-Normalisierung gleich. Der anschließende Positionsdecoder
   bestätigt app.bin/cfg_tool.bin vollständig einschließlich Inhalts-CRC.
   Jetzt MCU-Instruktionen und Sensorinitialisierung bis zum IMU-Report
   verfolgen. Globale Bank-/Modellauswahl und der DV-Inhalt hinter dem
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
