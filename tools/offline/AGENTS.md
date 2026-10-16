Es gelten zusätzlich die aktuellen Regeln in `../../AGENTS.md`. Git-Einrichtung und gezielte lokale Commits sind inzwischen ausdrücklich beauftragt. Der Parser bleibt ein Dateiwerkzeug ohne Hardwaretransport.

# Arbeitsregeln für diesen Offline-Prototyp

Der gegenwärtige Nutzerauftrag erlaubt ausschließlich lokale Offline-Arbeit.
Ein späterer ausdrücklicher Nutzerauftrag kann den Umfang ändern.

- Keine USB-, HID-, evdev-, uinput- oder sonstigen Gerätezugriffe.
- Keine neuen Mitschnitte; keine Zugriffe auf usbmon oder Debug-Dateisysteme.
- Keine USB-Befehle, Treiberwechsel, Kernel-Patches oder Systemänderungen.
- Keine Installationen, Root-Befehle, udev-Regeln, Firmware- oder Profiländerungen.
- Kein Eingriff in Embercade oder ein anderes Projekt.
- Kein Git-Repository anlegen und nichts veröffentlichen, solange dies nicht
  ausdrücklich beauftragt wurde.
- Keine Module aus den recherchierten Drittprojekten importieren oder ausführen.
- Dateien dürfen nur offline ausgewertet werden; CLI-Eingaben müssen reguläre
  gespeicherte Dateien sein. Spezialdateien, `/dev`, `/proc` und `/sys` ablehnen.
- Künstliche Daten ausdrücklich kennzeichnen. Historische Nutzerberichte,
  Quellcodebefunde und neue Messungen getrennt behandeln.
- PID, Busadresse, Sitzung und Quelle nicht stillschweigend zusammenführen.
- Keine Sensor-Skalierung, Gerätezeitstempel oder Hardwarekompatibilität erfinden.
- Änderungen mit den Standardbibliothek-Tests prüfen. Benötigte Testdaten und
  ihre erwarteten Ergebnisse unabhängig vom Decoder erstellen.

Validierung im Verzeichnis dieser Datei:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
```
