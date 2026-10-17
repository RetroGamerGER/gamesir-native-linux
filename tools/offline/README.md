# GameSir G7 Pro – Offline Proof of Concept 0.1

**Historischer Sprint-001-Komponentenbericht.** Diese Kopie gehört jetzt zum gemeinsamen Git-Projekt. Die folgenden Grenzen beschreiben den damaligen PoC. Aktuell: [Projektstand](../../docs/PROJECT_STATE.md) und [README](../../README.md).

**Neuer separater Offline-HID-Prototyp (17. Oktober 2026):**
`python -B -m gamesir_offline hid-replay fixtures/captured_hid_returns.jsonl --strict`
wertet 14 kleine echte Telemetrieausschnitte und drei LED-Submits aus.
`fixtures/synthetic_hid_companion.jsonl` bleibt ausdrücklich künstlich.
Herkunft, Anonymisierung und Grenzen stehen im
[HID-Prototypbericht](../../docs/XPAD_HID_PROTOTYPE.md). Keine Hardwareanbindung
oder bestätigte Aktivierung; das bisherige `replay` lehnt IF1 weiterhin ab.
Die folgenden Angaben zu ausschließlich 38 künstlichen Datensätzen beschreiben
den ursprünglichen Sprint-001-Bestand, nicht diese Erweiterung.

Der Prototyp dekodiert gespeicherte Paketdaten und prüft die dokumentierten
Protokollstrukturen. Er enthält keinen USB-Transport und keinen Kernelcode.
Alle 38 mitgelieferten Datensätze sind **künstlich**. Es wurde kein echter
USB-Mitschnitt als Parser-Test verwendet.

## Ergebnis und Grenzen

- 20-Byte-Xbox-360-Eingaben werden mit ihren vorzeichenbehafteten 16-Bit-Stickwerten
  erhalten. Die Standard-Y-Transformation von `xpad` wird zusätzlich dargestellt.
- GameSir-Telemetrie, Konfigurationsantworten und Geräteinformationen werden getrennt.
- Sechs IMU-Rohkanäle und die dokumentierten Zusatzbuttons werden ausgewertet.
- Aufgezeichnete Viermotor-Ausgabepakete lassen sich nach LT, RT und beiden Griffen
  aufschlüsseln. Es gibt keine Funktion zum Senden oder zur Motorsteuerung.
- Geräteidentität, Quelle, Sitzung, Endpunkt und Zeitbasis bleiben getrennt.
- Unvollständige, fehlgeschlagene und nicht abgeschlossene Übertragungen werden
  nicht als erfolgreiche Paketbeobachtungen gezählt.

Die berechneten 1000 Hz im künstlichen Beispiel folgen den frei gesetzten
Zeitwerten. Sie sind **kein Messwert**. Die Mischung künstlicher Gamepad- und
IMU-Pakete ist kein USB-Bandbreitenmodell. Sie bestätigt weder gleichzeitigen
Hardwarebetrieb noch Sensorabtastrate, Latenz, Kalibrierung oder Anwendungskompatibilität.

## Offline ausführen

Voraussetzung: Linux und Python ab 3.10; ausschließlich Standardbibliothek.
Es sind keine Installation, zusätzlichen Pakete oder erhöhten Rechte nötig.
Die folgenden Befehle werden im Ordner dieser README ausgeführt:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
PYTHONDONTWRITEBYTECODE=1 python -m gamesir_offline replay fixtures/synthetic_valid.jsonl --events --strict
PYTHONDONTWRITEBYTECODE=1 python -m gamesir_offline replay fixtures/synthetic_negative.jsonl --events
```

Eine einzelne Identität auswählen:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m gamesir_offline replay fixtures/synthetic_valid.jsonl --pid 100a --bus 8 --address 12
```

Die negativen Testdaten enthalten absichtlich ungültige Pakete. Mit `--strict`
liefert ihre Auswertung deshalb Exitcode 1. Ohne `--events` wird nur die
Zusammenfassung ausgegeben. Exitcode 2 bedeutet einen Datei-, JSON- oder Schemafehler.
Unbekannte Formate werden als `unknown` ausgewiesen und sind kein Parserabsturz.

## Vorbereitete Ergebnisse

- [Testbericht](results/TEST_REPORT.md)
- [Auswertung gültiger künstlicher Pakete](results/synthetic-valid-replay.json)
- [Auswertung negativer künstlicher Fälle](results/synthetic-negative-replay.json)
- [Beschriftung und erwartete Werte aller Fälle](fixtures/expected.json)

## Dokumentation

- [Paketformate und Geltungsbereich](docs/PROTOCOL.md)
- [JSONL-Datenschema und Auswertungsregeln](docs/RECORD_FORMAT.md)
- [Projektstand und historische Vorbefunde](docs/PROJECT_STATE.md)
- [Fixierte Quellen und Prüfsummen](docs/source-map.json)
- [Arbeitsregeln](AGENTS.md)

## Weitere Arbeit

Der damals vorgesehene nächste Offline-Schritt war die Einbindung vollständig gespeicherter echter
Paketzeilen, sobald sie bereitgestellt werden. Die unveränderte Originaldatei,
Zeitbasis und Herkunft müssen erhalten bleiben. Das aktuelle Eingabeformat ist
JSONL; PCAP/PCAPNG und usbmon-Rohtext werden noch nicht automatisch importiert.

Neue Mitschnitte, Gerätezugriff, Treiberwechsel, virtuelle Eingabegeräte und
Kernelarbeiten gehören nicht zu diesem freigegebenen Prototyp.
