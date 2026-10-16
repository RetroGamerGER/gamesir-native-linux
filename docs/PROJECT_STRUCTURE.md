# Erhaltener Bestand und Pfadprüfung

Projektwurzel ist der vorhandene Ordner `gamesir-native-driver-preparation`.
Vor Einrichtung existierten weder eigenes/übergeordnetes Git-Repository noch
Remote. Neuer Branch: `main`.

## Bestand und Sicherung

Vor Änderungen wurden 46 native Dateien und 24 Dateien des älteren Offline-PoC
inventarisiert: Pfad, Größe und SHA256 in `project-inventory.json`. Alle 70
Originaldateien wurden bytegleich in `.local/pre-git/native/` beziehungsweise
`.local/pre-git/offline/` gesichert und per SHA256 geprüft.

C-Kern, Sensorprofil, Tests und wissenschaftliche Nachweise bleiben erhalten.
Der Parser wurde mit eigenen Tests/kleinen synthetischen Fixtures nach
`tools/offline/` kopiert. Sein ursprünglicher Nachbarordner
`../gamesir-offline-poc` bleibt unverändert. Keine Originalaufnahme, Anwendung
oder fremde Binärdatei wurde verschoben.

RST-Berichte bleiben erhalten. Markdown-README, PROJECT_STATE, ARCHITECTURE,
PROTOCOL und TESTING bilden den aktuellen Einstieg. PoC-Dokumentation wird
als historischer Komponentenstand gekennzeichnet.

## Pfadabhängigkeiten

Die ursprünglichen Tests enthielten absolute Pfade zum Chat-Arbeitsordner,
Capture, Recherchearchiv und Nachbarparser. Ersetzt durch Projektwurzel,
kopierten Parser und lokale Konfiguration/Umgebungsvariablen. Neue Berichte
und Binärdateien entstehen in `build/`; historische Nachweise bleiben bestehen.
`/usr`, `/proc` und `/dev` in SDL-Sandboxprüfungen sind beabsichtigte Linux-Pfade,
keine privaten Home-Abhängigkeiten.

## Bewusst außerhalb von Git

- Große Rohaufnahmen/Ableitungen und ungefilterter Verkehr anderer Geräte.
- Fremde Installer, DLLs, Firmware und vorhandenes FCC-Quelldokument in
  `docs/sensor-evidence/`, dessen Weiterverbreitung hier nicht geklärt wurde.
- Maschinenspezifische historische SDL-Logs und `evidence-verification.json`.
- Private Pfade, Sicherungen, Builds und Caches.

Diese Dateien bleiben auf dem Datenträger erhalten. Eigener Code, Tests,
kleine Fixtures, Profil und portable Nachweise werden gezielt versioniert.
Die Einrichtung erzeugt kein Remote und veröffentlicht nichts.
