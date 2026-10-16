# Offline-Testbericht – GameSir G7 Pro PoC 0.1

Datum: 11. Oktober 2026. Ausgeführt mit Python 3.14.8 unter Linux.

**Ergebnis: 44 Tests bestanden.**

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
Ran 44 tests
OK
```

Der vollständige Testlauf steht in [unittest.txt](unittest.txt).
Es wurden keine Drittprojektmodule ausgeführt und keine Pakete installiert.

## Künstliche gültige Paketfälle

Alle 19 Datensätze wurden dekodiert. Ihre Herkunft ist jeweils `synthetic`.

| Pakettyp | Anzahl |
|---|---:|
| Xbox-360-kompatible normale Eingaben | 4 |
| GameSir-Telemetrie mit IMU-Rohwerten | 3 |
| Konfigurations-Leseantwort | 1 |
| Firmware-Informationsantwort | 1 |
| Aktives-Profil-Antwort | 1 |
| Viermotor-Ausgabelayout: vier einzelne Kanäle und Nullwerte | 5 |
| Gewöhnliches Zweimotor-Ausgabelayout | 1 |
| Vendor-Heartbeat als gespeicherte künstliche Bytes | 1 |
| Einfaches GIP-Eingabelayout | 2 |

[Vollständige Auswertung](synthetic-valid-replay.json).

## Absichtlich negative Fälle

| Behandlung | Anzahl | Beispiele |
|---|---:|---|
| `malformed` | 9 | Fehlende Felder, falsche deklarierte Länge, Motorwert über 100 |
| `truncated` | 2 | Gemeldete Transferlänge größer als gespeicherte Daten oder explizites Truncation-Flag |
| `unknown` | 3 | Unbekannte Vendor-Kennbytes, Report `12`, nicht unterstützte GIP-Optionen |
| `ignored` | 5 | Andere Schnittstelle/Endpunkt/Vendor, Submit, fehlgeschlagener Completion |

[Vollständige Auswertung](synthetic-negative-replay.json).
Die negativen Fälle erzeugen keine erfolgreiche Paket-Zeitstatistik.

## Geprüfte Regressionen und Grenzen

- Signed-LE16-Sensor- und Stickwerte einschließlich -32768 und 32767.
- Unterschied zwischen Roh-Stickwerten und der üblichen `xpad`-Y-Transformation.
- Byte 60 löst bei analogen RT-Werten keine Zusatztasten aus.
- Alle sieben ausgewerteten Zusatz-/Metatasten bleiben voneinander unabhängig.
- Telemetrie mit fehlenden benötigten Bytes wird abgewiesen.
- Ein auf 61 Byte abgeschnittener 64-Byte-Mitschnitt wird nicht als vollständiges
  Sensorpaket akzeptiert, obwohl die Sensorfelder zufällig noch enthalten wären.
- Konfigurations-Offset ist Big Endian; Nutzdaten müssen vollständig vorhanden sein.
- Firmware-Selektorecho wird nicht als Stringlänge verwendet; UTF-16LE-Fehler
  und fehlende Terminierung werden erkannt.
- GIP-Basislayout wird von unbekannten Optionen und falschen Längen getrennt.
- Viermotor-Feldreihenfolge wird dekodiert, ohne einen Sender bereitzustellen.
- 1.134 deterministische Aufrufe mit variierten Längen, Report-IDs und Inhalten
  verursachen keinen Decoderabsturz. Das ist kein vollständiger Fuzzing-Nachweis.
- Ungültiges JSON, doppelte Schlüssel, falsche Metadatentypen, überlange Zeilen
  und übermäßige Verschachtelung werden als Eingabefehler behandelt.
- `/dev`, `/proc`, `/sys`, FIFOs und Symlinks auf Geräte werden vor dem Öffnen
  abgewiesen. Auch ein `/proc/self/fd`-Umweg wird vor der Pfadauflösung blockiert.
- Der Quellpaket-Importtest findet keine USB-/HID-/Netzwerk-/Prozessmodule.
- Quellen, Sitzungen, Identitäten und Endpunkte werden nicht zusammengeführt.
- Rückläufige Zeitwerte werden nicht durch Sortieren verborgen.

## Was dieser Testlauf nachweist

Der Decoder verarbeitet die ausgewählten dokumentierten Layouts und die
künstlichen Fehlerfälle reproduzierbar. Er erhält die benötigten Rohwerte und
trennt Pakettypen, Metadaten und Zeitstatistiken.

## Was weiterhin offen ist

Es wurden **null echte USB-Paketdatensätze** wiedergegeben. Der historische
Mitschnitt wurde vom Nutzer gelöscht und war hier nicht verfügbar.
Der Testlauf weist daher keine G7-Pro-Funk-Kompatibilität, gleichzeitigen
Gamepad-/IMU-/Motorbetrieb, 1000-Hz-Hardwareleistung, Kalibrierung, Firmwarezustände
oder SDL-/Steam-/Proton-Unterstützung nach.

Die 1000 Hz im künstlichen Beispiel sind aus frei gesetzten Zeitwerten berechnet.
Die gemischten künstlichen Pakete bilden keine physikalische USB-Belegung ab.
Die Zuordnung des GIP-Beispiels zu `109c` ist ebenfalls künstlich.

USB-Befehle, neue Mitschnitte, Treiberwechsel, virtuelle Eingabegeräte,
Kernel-Patches sowie Änderungen an Controller und System wurden nicht ausgeführt.
