# Control Center: TMR-Stickkalibrierung offline vorbereiten

**Current follow-up:** The [scoped GUI and permission path](CONTROL_CENTER_TMR_PERMISSION.md)
is now implemented and tested offline. It has a distinct explicit continuity
contract; it does not attest physical RF lifetime. The normal app, published
AppImage, installed driver and default-off kernel feature remain unchanged.
The historical implementation scope below is retained for provenance.

Stand: 22. Oktober 2026. **Offline-Prototyp mit simuliertem Controller.**
[Validierung und Umfang](evidence/CONTROL_CENTER_STICK_CALIBRATION_OFFLINE_20261022.json).
Die normale Anwendung und das bereits veröffentlichte AppImage bieten damit
noch keine Hardwarekalibrierung an. Die Stickkalibrierung bleibt dort weiterhin
als zukünftige Funktion gekennzeichnet. Kein Treiber, Dienst, Pakethelfer,
Firmwareinhalt oder installiertes AppImage wurde geändert.

Die anschließende [Vorbereitung des Controlleradapters](CONTROL_CENTER_CALIBRATION_ADAPTER.md)
verbindet den Ablauf inzwischen mit echten Berichtslayouts und bekannten
Provider-Nutzinhalten in Offline-Tests. Die native Live-Schnittstelle fehlt
weiterhin; Vorschau und normale App greifen damit auf keine Geräte zu.

## Vorschau öffnen

Mit einer bereits vorhandenen Python-/PySide6-/Qt-6-Umgebung im Quellverzeichnis:

```sh
make control-center-calibration PYTHON=python3
```

Im Hauptfenster unter „TMR-Sticks kalibrieren“ auf **Kalibrierung ansehen**
klicken. Der Dialog ist deutlich als **SIMULIERTER CONTROLLER** gekennzeichnet.
Es werden keine Systemdaten abgefragt, Geräte geöffnet, Pakete geladen oder
Berechtigungen angefordert. Ein eventuell mitgelieferter Paketbestand wird
in diesem Startmodus ebenfalls nicht angebunden.

1. **Vorschau starten:** Drei Sekunden Vorbereitung, beide Sticks zunächst
   unberührt. In dieser Vorschau kommen sämtliche Bewegungen aus Beispieldaten.
2. **Kreise ansehen:** Links und rechts werden unabhängig dargestellt. Grün
   zeigt, welche Randbereiche bereits besucht wurden; der Punkt zeigt die
   aktuelle Stickposition. Die Anleitung sieht drei langsame Runden je Stick vor.
3. **Kalibrierung abschließen:** Erst verfügbar, wenn beide simulierten
   Firmware-Fertigmeldungen vorliegen. Ein vollständiger grüner Kreis allein
   genügt nicht. Der Abschluss erzeugt ausschließlich einen aufgezeichneten
   Finish-Testauftrag; es wird nichts auf einem Controller gespeichert.
4. **Abbrechen / Escape / Fenster schließen:** Beendet den Durchlauf und alle
   dafür ausstehenden Aktionen. Das Schließen des Dialogs lässt das Hauptfenster
   offen. Nach bereits begonnenem, weiterhin verbundenem Durchlauf wird einmal
   der semantische Exit-Testauftrag aufgezeichnet.
5. **Verbindungsverlust simulieren:** Beendet den Durchlauf sofort. Finish ist
   danach nicht mehr verfügbar. Alte Start-/Finish-/Exit-Aufträge werden nicht
   nachgeholt. „Neuen Durchlauf vorbereiten“ erzeugt ausdrücklich eine neue
   Verbindung/Sitzung und verlangt erneut den Start durch den Nutzer.

DE/EN gelten auch im Dialog. Kleine Fenster verwenden eine eigene scrollbare
Ansicht mit sichtbarer Tastaturnavigation; Status und Prozentwerte ergänzen die
Farben. Vorschau-, Abbruch- und Erfolgsseiten behaupten keinen echten
Speichervorgang oder eine Hardwareabnahme.

## Technischer Aufbau

- `tools/control_center/stick_calibration.py`: Qt-unabhängiger Sitzungsablauf,
  normalisierte Beispiele und rein speicherbasierter Auftragsrekorder.
- `calibration_bridge.py`: explizit aktivierter Qt-Adapter mit synthetischen
  Bewegungen und Verbindungsausfall. Im normalen Status-/Paketmodus deaktiviert.
- `qml/CalibrationDialog.qml` und `qml/StickView.qml`: Dialog, Stickpunkte,
  Fortschrittsringe, Bereitschaft, Abbruch und eigener Abschlussknopf.
- `main.py --rehearse-calibration`: ausschließlich isolierte Beispieldaten;
  gegenseitig ausgeschlossen mit Paket-Probelauf beziehungsweise normalem
  Status-/Paketbetrieb. `create_engine` weist Vermischung mit echter Erfassung
  oder Paketkoordinatoren zurück.

Die bekannten Operationen heißen im Prototyp nur **Start, Finish und Exit**.
Es werden keine GIP-/USB-/Funkpakete konstruiert oder gesendet. Start meint
beide Sticks; die spätere echte Kodierung und Geräteübernahme sind nicht Teil
dieser Arbeit. Die Quellen bestehen aus eigener Implementierung unter
GPL-2.0-only und verwenden keine kopierten Herstellerquelltexte/-ressourcen.

Jeder Durchlauf ist an Gerätekennung, Verbindungsinstanz und eine neue lokale
Generation gebunden. Rückmeldungen und verzögerte Vorbereitung sind an diesen
Schlüssel gekoppelt. Fremde Geräte, alte Verbindungen/Generationen und
doppelte oder rückwärts laufende Rückmeldungen können keine Bereitschaft setzen.
Sequenz und monotone Zeitstempel gehören zum **lokalen Adaptervertrag**; dies
behauptet keinen zusätzlichen vom Controller gelieferten Sitzungstoken.

Samples enthalten zwei normalisierte XY-Paare in `[-1,1]`, einen monotonen
Zeitstempel, eine lokale Sequenz und Aktiv-/Fertigmasken für beide Sticks.
Die Plotkonvention ist +X rechts, +Y oben. Ein echter Adapter muss Achsen,
Richtung, Skalierung und Geräteidentität passend übersetzen und separat prüfen.

Der Ring hat 24 Sektoren; Positionen mit Radius mindestens 0,8 markieren einen
besuchten Randbereich. Diese Schwelle ist **nur eine Anzeigeentscheidung**.
Sie berechnet keine TMR-Korrekturwerte und ist kein Genauigkeitsnachweis.
Finish erfordert beide Aktiv-/Fertigbits aus der aktuellen Rückmeldung.
Die Demo setzt ihre erfundenen Statusbits nach ihrer Drei-Runden-Animation;
der Sitzungsablauf leitet sie ausdrücklich nicht aus der Ringabdeckung ab.

Ein explizites Verlustereignis oder eine Berichtslücke über 1,5 Sekunden beendet
die Sitzung. Die Frist ist eine **Vorschau-/Adapterregel**, keine ermittelte
Funkfrist der Firmware; sie muss vor einer realen Anbindung mit deren
Berichtsintervallen abgestimmt werden. Ungültige aktuelle Daten und simulierte
Übertragungsfehler stoppen ebenfalls ohne automatische Wiederholung.

## Abgleich mit Nexus und Grenzen

Grundlagen sind die eigenen Analysen von
[Dialogablauf](NEXUS_STICK_CALIBRATION_FLOW.md),
[Firmwareoperationen](NEXUS_STICK_FIRMWARE.md),
[Status und Rücklesen](NEXUS_STICK_READBACK.md) sowie
[Aufwachen und alten Befehlen](NEXUS_STICK_WAKE_RETENTION.md).

Die Firmware erledigt die Kalibrierberechnung und Speicherung. Dafür wird keine
neue Speicherbestätigung erfunden. Gegenüber dem beobachteten Nexus-Dialog
verwenden wir einen ausdrücklichen Abschlussknopf statt eines ungebundenen
510-ms-Finish-Timers. Schließen invalidiert die Vorbereitung sofort; es gibt
keinen Abschluss nach Exit und kein automatisches Fortsetzen beim Reconnect.

Die Oberfläche kann bereits übertragene Dongle-Aufträge nicht rückwirkend
stornieren. Ein UI-Abbruch behauptet daher keine bestätigte Wiederherstellung
des Controller-RAM. Der neue Offline-Dialog hat überhaupt keinen solchen
Transport und verändert keine Kalibrierdaten. Fehlkalibrierung bleibt von
Firmwareflash getrennt; die offenen Flash-/Bootloader-Fragen sind kein
zusätzlicher Blocker für diesen rein simulierten Stickdialog.

Vor Hardwarebetrieb fehlen insbesondere der geprüfte Linux-Transportadapter,
exklusive Zuordnung/Abstimmung mit dem Manager und anderen Controllerwerkzeugen,
zuverlässige Verbindungs-/Statusbeobachtung und ein freigegebener Hardwaretest.
Es gibt keinen eingebauten Live-Schalter oder neuen Kalibrierbefehl im Kernel.
Das veröffentlichte AppImage und seine Signaturen/Releasepakete wurden nicht
neu gebaut oder ersetzt. Eine spätere Aktivierung erfolgt als eigener Schritt.

## Offline-Prüfung

```sh
make test-control-center PYTHON=python3
make test-control-center-ui PYTHON=python3
python3 -B tests/render_control_center_calibration.py
```

Die neuen Tests prüfen ausdrücklich Abbruch während der Vorbereitung, einmaliges
Start/Finish/Exit, beide Fertigbits, zurückfallende Bereitschaft, fremde und
veraltete Sitzungen, Berichtslücken, fehlerhafte Werte, simulierte Sendefehler
und das Ausbleiben verspäteter Aktionen. Qt-Tests bedienen die echten
QML-Knöpfe, Escape, kleine Fenster, DE/EN und den Hauptfenster-Abschluss;
ein zusätzlicher Prozess testet den echten Launcher mit Paketpfad ohne
Helfer-/Statuszugriff. Bestehende Paket-/Berechtigungsabläufe bleiben abgedeckt.

Der Renderer legt ausschließlich Screenshots eigener synthetischer Daten unter
`build/control-center-calibration/` ab. Er verwendet temporäre Einstellungen
und Software-Rendering. Keine Hardware-, Netzwerk- oder Installationstests.

Ergebnis: **376 Control-Center-Tests und 79 Qt-/Lebenszyklustests bestanden**,
darunter 36 neue Fälle (25 Sitzungs-, zehn QML- und ein Launcher-Fall).
Zusätzlich bestanden drei Lizenz-, sieben README- und 16 Nexus-Modelltests.
DE/EN-Ansichten für Messung, Bereitschaft und Verlust sowie eine kompakte
Ansicht wurden per Software gerendert und visuell geprüft.

Ein ergänzender **Kernpaket-Dokumentationscheck** hat einen bestehenden Fehler:
24 von 25 Fällen bestehen; der Link von `ZZZ_GYRO_EXTENSION.md` auf
`evidence/ZZZ_GYRO_ACCEPTANCE_20261021.json` fehlt im bisherigen Dokumenten-
Lieferumfang. Derselbe Fall scheitert auch mit der unveränderten HEAD-Lieferliste
vor dieser Arbeit. Er wird nicht durch eine Änderung am Treiber kaschiert.
Die Paketänderung dieses Schritts ergänzt ausschließlich diesen neuen
Kalibrierungsleitfaden zur Dokumentenliste. Kein neues Kernpaket wurde gebaut
oder als vollständig geprüft freigegeben.
