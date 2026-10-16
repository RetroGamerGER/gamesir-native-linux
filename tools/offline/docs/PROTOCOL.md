> **Historischer Protokollbericht des Offline-PoC: Sprint 001.** Aktueller gemeinsamer Stand: [PROJECT_STATE](../../../docs/PROJECT_STATE.md), [PROTOCOL](../../../docs/PROTOCOL.md).

# Dekodierte Formate und Beleglage

Alle Offsets beginnen bei Byte 0 des vollständigen Transfer-Payloads.
Endpunkte sind Teil der Metadaten; eine ähnliche Report-ID auf einer anderen
Schnittstelle wird nicht als derselbe Zugang interpretiert.

Die Implementierung wurde anhand von Protokollfakten unabhängig geschrieben.
Es werden keine fremden Projektmodule ausgeführt oder importiert.
Die fixierten Quellstände und SHA-256-Prüfsummen stehen in `source-map.json`.

## Normale Eingaben: Xbox-360-kompatibles Format

Genau 20 Byte, Präfix `00 14`, Interface 0 / IN `82`.
Tasten liegen in Byte 2/3, Trigger in 4/5 und vier vorzeichenbehaftete
Little-Endian-Stickwerte in 6–13. Der Decoder erhält die Rohwerte; zusätzlich
zeigt er die übliche `xpad`-Y-Transformation `~y`. Er legt keine neue Deadzone an.
Bytes 14–19 und das ungenutzte Tastenbit werden nicht interpretiert.

Quelle: [Linux 7.2.9, xpad360_process_packet](https://github.com/gregkh/linux/blob/5fce161649b4d779d1b76d9fcd52dc77779774b8/drivers/input/joystick/xpad.c).
Das entspricht dem vom Nutzer historisch berichteten Eingabeformat; die
mitgelieferten Pakete selbst sind künstlich.

## GameSir-Vendor-Eingaben

Präfix: Report-ID `10`, Byte 3 `3c`, Byte 4 als Diskriminator.
Die Bedeutung von Byte 1/2 wird nicht als Längenfeld, Sequenz oder Zeit interpretiert.
Das dokumentierte Transferformat umfasst üblicherweise 64 Byte. Bei Telemetrie
werden vollständig bereitgestellte Payloads mit 61–64 Byte akzeptiert, weil alle
dekodierten Felder bis einschließlich Byte 60 reichen. Das ist eine Parsergrenze,
keine Aussage über vom Gerät tatsächlich verwendete Transferlängen.
Ein laut Mitschnitt von 64 auf 61 Byte abgeschnittener Payload wird verworfen.

| Diskriminator | Dekodierung |
|---|---|
| `e0` | Telemetrie; Gyro 17–22 und Accel 23–28 als jeweils drei signed LE16-Werte |
| `05` | Konfigurationsantwort; Kategorie 5, Offset 6/7 als BE16, Länge 8, Daten ab 9 |
| `0a` | Firmware-Informationsantwort; UTF-16LE ab 5 bis zum ausgerichteten NUL |
| `0c` | Aktives Profil, Byte 5 im Bereich 1–4 |
| andere | Unbekannte Antwort; keine Interpretation als IMU |

Die Längenangabe der Konfigurationsantwort ist auf 55 Byte begrenzt und muss
vollständig vorhanden sein. Bei der Firmwareantwort ist `0a` ein Selektorecho,
keine Stringlänge. Weitere Vierergruppen im Firmwaretext bleiben unzugeordnet.

Zusatzbuttons: Byte 57 enthält Home `01`, Share `02`, L4 `08`, R4 `10`, M `20`;
Byte 58 enthält L5 `01`, R5 `02`. **Byte 60 ist ein analoger Triggerwert und
kein Zusatzbutton-Bitfeld.** Unbekannte Bits werden erhalten.

Stickdarstellungen der Telemetrie werden als 8-Bit-Werte gekennzeichnet und
ersetzen die normalen 16-Bit-Eingaben nicht. Batterie- und Ladeflags bleiben roh;
ungewöhnliche Werte werden nicht durch Begrenzung verborgen.

Quellen: [Deadband parse_input](https://github.com/broroeror/gamesir-linux-tools/blob/771b28ae75b0a614a6a7fec9aa606606a27b3b8d/vendors/gamesir/models/g7pro/protocol.py),
[g7ctl read_chunk / read_device_info](https://github.com/questionablesyntax/g7ctl/blob/0ea4b5223ba2191c88a3c4d1ff8d34f594bfeb1b/pyg7/session.py).
Dies sind Quellcodebefunde und dokumentierte Fremdtests, keine neue Bestätigung
für den konkreten Funk-Dongle des Nutzers.

## Einfaches GIP-Eingabeformat

Report `20`, Optionen `00`, einfache 4-Byte-Kopfzeile, deklarierte Nutzdatenlänge
mindestens 14 und exakt passend zur Transferlänge. Unterstützt werden rohe
Tastenbytes, zwei unsigned LE16-Trigger und vier signed LE16-Stickwerte.
Erweiterungsbytes bleiben roh. Fragmentierte, erweiterte oder andere
Optionsformate werden als unbekannt erhalten.

Quelle: [Linux xpadone_process_packet](https://github.com/gregkh/linux/blob/5fce161649b4d779d1b76d9fcd52dc77779774b8/drivers/input/joystick/xpad.c).
Die künstliche Zuordnung eines Beispiels zu `109c` beweist weder dessen
Deskriptor noch einen Betriebszustand oder einen funktionierenden GIP-Zugriff.

## Ausgabepakete ausschließlich als Dateidaten

Auf Interface 0 / OUT `02` werden folgende gespeicherte Layouts dekodiert:

- Viermotor-GIP: 13 Byte, Kopf `09 00 SEQ 09 00 0f`; Byte 6–9 sind Prozentwerte
  für LT, RT, linken Griff, rechten Griff. Jeder Wert muss 0–100 sein. Dauer und
  Pause werden als 10-ms-Ticks, Wiederholung als Rohwert ausgegeben. Unterstützt
  wird nur das dokumentierte Layout mit allen vier Motoren im Enable-Maskenfeld.
- Vendor-Ausgabe: 64 Byte, `0f 00 SEQ CMD`; Heartbeat `02`, Lesen `05`, Schreiben
  `3c`, Geräteinformation `01`. Nutzdaten werden roh angezeigt.
- Gewöhnliches Xbox-360-Rumble: 8 Byte, `00 08`; Griffwerte in Byte 3/4.

Quelle: [Deadband rumble_packet](https://github.com/broroeror/gamesir-linux-tools/blob/771b28ae75b0a614a6a7fec9aa606606a27b3b8d/vendors/gamesir/models/g7pro/protocol.py),
[Linux xpad_play_effect](https://github.com/gregkh/linux/blob/5fce161649b4d779d1b76d9fcd52dc77779774b8/drivers/input/joystick/xpad.c).
Es existieren weder ein Sender noch ein öffentliches Kommando-Erzeugungs-API.
Die dekodierten Prozentwerte bestätigen keine Bewegung eines physischen Motors.

## Offene Hardwarefragen

- IMU-Skalierung, physische Achsenrichtung, Kalibrierung und Abtastrate.
- Gerätezeitstempel beziehungsweise Sensorzähler: kein entsprechendes Feld angenommen.
- Gleichzeitigkeit mit unveränderten normalen Eingaben und unabhängigen Motoren.
- Initialisierung und Identitätswechsel des konkreten `100a/109c`-Funkgeräts.
- USB-Bandbreite, Paketfragmentierung und Änderungen der Endpunktdeskriptoren.

Es werden deshalb keine SI-Sensoreinheiten erzeugt und keine Eingaben an SDL,
Steam, Proton oder Emulatoren weitergegeben.
