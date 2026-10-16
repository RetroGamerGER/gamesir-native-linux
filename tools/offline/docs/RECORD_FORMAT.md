# JSONL-Eingabeformat, Version 1

Jede nichtleere Zeile enthält genau ein JSON-Objekt. Doppelte Schlüssel,
fehlende oder zusätzliche Felder und ungültige Typen sind Fehler.
Hexwerte enthalten keine `0x`-Präfixe und keine Leerzeichen.

```json
{
  "schema_version": 1,
  "source": {"kind": "synthetic", "id": "example-not-a-capture"},
  "session": "example-100a",
  "timestamp_us": 1000,
  "timebase": "synthetic",
  "device": {"vid": "3537", "pid": "100a", "bus": 8, "address": 12, "interface": 0},
  "endpoint": "82",
  "stage": "complete",
  "status": 0,
  "reported_length": 20,
  "capture_truncated": false,
  "data_hex": "0014000000000000000000000000000000000000"
}
```

## Herkunft

`source.kind` ist `synthetic`, `capture` oder `capture_excerpt`.
Künstliche Daten müssen `timebase: synthetic` verwenden; gespeicherte reale
Beobachtungen `host_capture`. Der Parser kann die Wahrheit dieser Metadaten
nicht verifizieren. PID und Interface müssen aus separat gesicherten
Metadaten stammen; sie werden nicht aus Paketbytes oder einer usbmon-Adresse erraten.

`source.id` benennt die konkrete Quelldatei/Erhebung. `session` trennt Sitzungen
und Zeitachsen. Bei Identitätswechseln und neuen Busadressen muss die Zuordnung
neu dokumentiert werden. USB-Adressen sind nicht dauerhaft.

## Übertragungen und Längen

`stage` ist `submit`, `complete` oder `error`. Nur `complete` mit Status 0 wird
dekodiert. Dadurch werden Submit und Completion nicht doppelt als Eingaben gezählt.
Die Version 0.1 korreliert keine URB-IDs. Falls die Originaldatei ausgehende
Nutzdaten nur beim Submit enthält, müssen Submit und erfolgreicher Completion
später anhand der URB-ID nachvollziehbar verbunden werden. Die Lücken dürfen
nicht durch erfundene Payloads oder einen angenommenen Erfolg ersetzt werden.

`reported_length` ist die abgeschlossene tatsächliche Transferlänge, nicht
die angeforderte Puffergröße oder `wMaxPacketSize`. `capture_truncated` kennzeichnet
eine bekannte Begrenzung des Mitschnitts. Weniger gespeicherte Bytes als gemeldet
führen ebenfalls zu `truncated`; mehr gespeicherte Bytes zu `malformed`.

Reguläre gespeicherte Dateien sind die einzigen Eingaben. Die CLI liest nicht
von stdin, Geräten oder FIFOs. `/dev`, `/proc` und `/sys` werden abgewiesen.
Grenzen: 65.536 Byte pro JSONL-Zeile, 4.096 gespeicherte Payload-Byte pro Datensatz,
250.000 Datensätze pro Datei. Die derzeitigen Paketdecoder unterstützen maximal
64 Byte pro vollständigem Payload. Keine automatische Fragmentzusammensetzung.

## Zeitstatistik

Gruppierung erfolgt nach Quelle, Sitzung, Zeitbasis, VID/PID, Bus, Adresse,
Interface und Endpunkt. Innerhalb jeder Gruppe erhält jeder erfolgreich
dekodierte Pakettyp eine eigene Intervallstatistik.

Die Dateireihenfolge wird erhalten. Rückwärts laufende Zeitwerte sperren die
Statistik der betroffenen Gruppe; doppelte Zeitwerte werden ausgewiesen.
Berechnet werden Minimum, Maximum, Median, p95 nach Nearest Rank sowie
`observation_rate_hz = (Anzahl - 1) / Zeitspanne`.

Das beschreibt die Beobachtungsfolge. Es ist kein Nachweis für Sensorabtastrate,
frische Samples, fehlende Pakete, Funklatenz oder Spiellatenz. Die Anwesenheit
normaler und IMU-Pakete in derselben Sitzung ist ebenfalls keine Zusage
kontinuierlichen gleichzeitigen Hardwarebetriebs.

Ein leerer oder vollständig gefilterter Datensatz ergibt einen leeren Bericht,
keinen Hardware-Nachweis. Nicht vorhandene Zählerschlüssel entsprechen null.
