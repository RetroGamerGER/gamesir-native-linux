# Jieli: zwölf Sensorbytes über Funkrahmen zum Dongle-Sendepuffer

Stand: 18. Oktober 2026. Fortsetzung von
[Sensorbericht](JIELI_SENSOR_REPORT_DATAFLOW.md) und
[Kopierhelfer/USB](JIELI_USB_TRANSPORT.md). Ausschließlich lokale statische
Analyse mit bereits gespeicherten Referenzen. Keine Firmwareausführung oder
Emulation, Netzwerk-/Hardwarezugriffe, Installation oder Treiberänderung.
Gyrokalibrierung bleibt pausiert; kein neuer Laufzeitfaktor.

**Spätere Fortsetzung:** [Callback-Registrierung](JIELI_RADIO_CALLBACK.md)
ordnet die unten noch offene Tabellen-/Setter-Verknüpfung statisch zu und
grenzt zwei untere Sendepfade ein. Tatsächliche Aktivierung und Funkzustellung
bleiben unbeobachtet. Dieser Bericht hält den vorherigen Analysestand fest.

## Ergebnis und Beweisgrenze

Ein **beidseitig passender `A2`-Transportpfad** verbindet jetzt den
Controller-Berichtskonstruktor mit einer Empfangsqueue und dem
USB-Sendepuffer des Dongles. Die zwölf Felder werden in den untersuchten
Kopierabschnitten als Bytes weitergereicht. Keine zusätzliche Multiplikation,
Vorzeichenänderung, Achsenumordnung oder Bias-Korrektur in diesen Abschnitten.
Die bereits früher gefundene Umordnung und bedingte Offsetkorrektur vor dem
Berichtskonstruktor bleiben davon unberührt.

Das ist noch kein lückenloser Nachweis der tatsächlichen Funkübertragung:
Die Controller-Seite übergibt an einen indirekten Transport-Callback. Dessen
aktive Registrierung und die darunterliegende Funkstrecke sind nicht
vollständig aufgelöst. Auf beiden Seiten sind Modus-, Zustands-, Längen- und
Empfangsprüfungen vorgeschaltet; ihre Laufzeitwerte sind nicht beobachtet.
Der Datenfluss stützt den Kandidaten, beweist aber weder den aktiven Sensor
noch den Gyrofaktor der realen USB-Aufzeichnung.

Wichtige Präzisierung des vorigen Berichts: `D+0xa24` ist **ein**
Format-Zwischenspeicher. Der hier passende `A2`-Pfad erreicht USB-IN `0x82`
über eine andere Queue direkt. Die Suche darf deshalb nicht auf diesen
Zwischenspeicher oder auf irgendeinen 64-Byte-Pfad beschränkt werden.

## 1. Quellen, Adressen und notwendige Decoderkorrektur

Verwendet wurden dieselben unveränderten, gehashten Controller-Apps DV209,
DV515, DV608 und Dongle-App DG144 wie in den beiden Vorgängerberichten.
Alle Positionen unten sind **Dateioffsets**, keine unmittelbar am Gerät
verwendbaren Adressen. `B = 0xf140` gilt für DV209, `D = 0x62c0` für DG144.

Der bereits begründete DV209-RAM-Suffix beginnt bei `0x4f718` und läuft
unter Basis null. Ein relativer CALL daraus in den Flash-Präfix benötigt
beide Adressräume: aus dem bei Dateibasis null ausgegebenen Ziel `t` wird
`(t − 0x4f718 + 0x1fff40) mod 2^32`. Dies wird ausschließlich für geprüfte
Suffix→Präfix-CALLs angewendet; interne RAM-Ziele dürfen so nicht umgerechnet
werden. Damit stimmen die Queue-Aufrufe bei `0x5841e`/`0x58434` mit den
bereits untersuchten Helfern `0x114b6`/`0x2e8` überein.

Beim Nachverfolgen des Paketkopfs fiel ein weiterer Fehler im privaten
Pi32v2-Decoder auf: Die erweiterte Byte-Store-Form **`EE52`** verwendet dort
`eregAl` statt `eregA` und verliert dadurch das vierte Quellenregisterbit.
So wurde `r13` fälschlich als `r5`, `r11` als `r3` gelesen. Der zuvor scheinbar
unbenutzte Wert `0xa2` wird tatsächlich in den Abschnittskopf geschrieben.

Eine separate private Decoderkopie korrigiert nur diese Form. Gegenprobe mit
dem schon gespeicherten offiziellen Jieli-Tech-ROM-Listing, Commit
`fdc018de81629e21e594d677cf05f87d288be0f0`:

- Alle **44** exakten Byte-Store-Beispiele stimmen in Register, Adresse und
  erzeugtem P-Code überein; **25** verwenden Quellen oberhalb von `r7` und
  unterscheiden die alte falsche von der korrigierten Deutung.
- Die bisherigen **83** SDK-Kontrollen bestehen auch mit dieser Kopie.
- Das ist ein Analysewerkzeugfehler, kein nachgewiesener GameSir-Firmwarefehler.
  Die zwei offenen Operationen unten wurden dadurch nicht mitvalidiert.

Referenzhash und Herkunft stehen im
[Transportbericht](JIELI_USB_TRANSPORT.md#1-quellen-und-adressmodell).
Keine neue Referenz wurde heruntergeladen; Quellkopien und Disassemblies
bleiben privat. Drei kurze Framing-/Kopierblöcke sind in DV209, DV515 und
DV608 jeweils eindeutig bytegleich; das ist keine vollständige
Kontrollflussprüfung aller drei Versionen.

## 2. Controller: Bericht als eigener Funkrahmen-Abschnitt

`R` bezeichnet den bereits untersuchten 64-Byte-Bericht mit
`R[0]=0x10`, `R[3]=0x3c`, `R[4]=0xe0`. Seine zwölf Sensorbytes liegen bei
`R[17:29]`, als sechs Little-Endian-Felder an 17/19/21/23/25/27.

| Abschnitt | DV209-Fundstelle | Statische Aussage |
| --- | --- | --- |
| Bericht erzeugen | `0x1aeda`–`0x1afd2` | Bekannter Konstruktor und Queue `B+0x73c`; siehe Vorgängerbericht |
| Zur anderen Queue übergeben | `0x58416`–`0x58434` | Entnahme nach `B+0x1074`, Prüfung auf erstes Byte `0x10`, Weitergabe an Queue `B+0x3dc` |
| Abschnitt befüllen | `0x1b362`–`0x1b37e` | Aus dieser Queue nach Abschnittsanfang `S+2` lesen; Länge übernehmen und auf null prüfen |
| Kopf und Kopie | `0x1b380`–`0x1b3b8` | `S[0]=0xa2`, `S[1]` Sequenzbyte; Bericht zusätzlich nach `B+0x1334` kopieren; Abschnittslänge = Berichtslänge + 2 |
| Sensortag erkennen | `0x1b3ba`–`0x1b3d4` | Explizite Prüfung der Kopfpositionen 0/3/4 auf `10/3c/e0`; Statusverwaltung, keine Sensorarithmetik |
| Rahmen abschließen | `0x1b3d8`–`0x1b41a` | Abschnittslänge, Prüfsummenhelfer und zwei Trailerbytes; Gesamtlänge ermitteln |
| Transport übergeben | `0x1b422` → `0x31b74` | Übergabe von Rahmen und Länge; Wrapper springt über den Zeiger bei `0x21e64`, mit Operationsargument 2 |

Die erste Queue hat auch andere Verbraucher. Ein eigener Abschnittskopierer
bei `0x1b248`–`0x1b294` packt ihren Inhalt byteweise in einen anderen Teil
desselben Rahmentyps. Der anfänglich untersuchte direkte USB-Pfad nach
`0x84` ist ebenfalls nur eine Alternative. Keiner dieser Zweige wird allein
aus seiner Existenz als der im Capture aktive Modus festgelegt.

**Noch offene Grenze:** `0x32018`–`0x32020` ist ein Setter des indirekten
Transportzeigers. In der begrenzten Suche nach den geprüften direkten
22-Bit-CALLs wurde kein Aufrufer gefunden. Andere Transferformen, Tabellen,
zusammengesetzte Adressen und indirekte Aufrufe sind dadurch nicht ausgeschlossen.
Die aktive Callback-Implementierung ist weiterhin zuzuordnen. Der
Prüfsummenhelfer wird hier nicht als vollständig validierter CRC-Algorithmus
oder als Integritätsnachweis einer echten Funkübertragung ausgegeben.

## 3. Dongle: `A2` entpacken, in Queue speichern, an IN `0x82` senden

Der Empfangsparser besitzt einen passenden verschachtelten `A2`-Zweig:

| Abschnitt | DG144-Fundstelle | Statische Aussage |
| --- | --- | --- |
| Abschnittstyp auswählen | `0x9844`–`0x984c` | Abschnittskopf `0xa2` führt nach `0x98b8`; `0xa3` hat einen getrennten Zweig |
| Sequenz und Nutzdaten | `0x98be`–`0x98dc` | Vergleich mit gespeichertem Sequenzbyte; Quelle `S+2`; Sonderfall für Nutzkopf `02/20/…/1c` getrennt |
| Normalen Bericht einreihen | `0x9908`–`0x9912` | Queue `D+0x2e0`, Quelle `S+2`, Länge = Abschnittslänge − 2 |
| Byteweise Queuekopie | `0x680`–`0x6d0` | Längenmarkierung und Bytekopie in Ringpuffer; keine Sensorrechnung |
| Bericht entnehmen | `0xd3e8`, `0xd432`–`0xd43e` → `0x31e2` | Dieselbe Queue; byteweise Ausgabe nach `D+0x8a4`, Länge als Rückgabewert |
| Tagabhängige Ausnahme | `0xd442`–`0xd45c` | Nur bei Berichtbyte 0=`0x10` **und** Byte 4=`0x0a` werden vier Bytes überschrieben; der untersuchte Sensortag `0xe0` überspringt dies |
| USB-Sendung | `0xd468` → `0xd3be`/`0xd3c0` | Endpunkt 2, Puffer `D+0x8a4`, entnommene Länge → Wrapper `0xcd44` → USB-Helfer `0x186c` |

Der bereits separat geprüfte untere USB-Helfer kopiert nach `0x18d2` in
den endpunktbezogenen Sendepuffer, schreibt die Länge und setzt TXCSR.
Damit bleiben für den 64-Byte-Sensorbericht die zwölf Bytes an 17–28 bis
zum **Sendepuffer von IN `0x82`** erhalten, sofern dieser Zweig mit genau
diesem Bericht durchlaufen wird. USB-Abschluss, Modusauswahl und tatsächliche
Funkzustellung sind keine statisch beobachteten Laufzeitereignisse.

Der vollständige Rahmenparser verarbeitet zusätzliche, variabel lange
Abschnitte. Seine vorgeschaltete Längen-/Prüfsummenprüfung und die
dynamische Empfangsanbindung sind nicht vollständig geschlossen. Ein
synthetisch passendes Framing ersetzt keine Funkaufzeichnung.

## 4. Abgegrenzte Nebenpfade

- Der bisher gesuchte Writer von **`D+0xa24`** ist gefunden:
  `0x8334` konstruiert modusspezifische Berichte. Im Nullmodus kopiert
  `0x837c`/`0x8380` aus `D+0x9e4` nach `D+0x8a4`; `0x8618`–`0x8620`
  kopiert anschließend 64 Byte nach `D+0xa24`. Andere Modi haben andere
  Quellen/Längen. Der spätere Dispatcher kopiert diesen Cache zurück.
  Dieser Befund allein verbindet ihn nicht mit unserer USB-IMU-Telemetrie.
- Ein weiterer zwölf Byte langer Empfangspfad beginnt beim Pakettyp `0x31`
  (`0x99a8` ff.). Er bedient andere Felder und Formatkonstruktion. Die Länge
  zwölf allein berechtigt nicht zur Gleichsetzung mit `R[17:29]`.
- Queue **`D+0x2a8`** wird bei `0x9836` gefüllt und im DG-RAM-Suffix
  `0x37d4e` ff. entnommen. Dieser Verbraucher verwendet Puffer `D+0x924`
  und Endpunkt **4**, nicht 2. DG-Startliterale `0x68`/`0x6e` begründen
  Suffixquelle `0x37028`, Länge `0x52f0`, Runbasis null; damit lösen die
  Aufrufe nach `0x31e2` und `0xcd44` auf. Diese alternative IN-`0x84`-Route
  wird nicht mit der `A2`-/IN-`0x82`-Route vermischt.

## 5. Die beiden weiterhin offenen Decoderoperationen

**Skalierter Halfword-Index (`EDD8`, Modi 8/A):** Die private Referenz
berechnet weiterhin `Basis + Index`, obwohl Kommentar und Operandmodus
`Basis + (Index << 1)` nahelegen. Konkreter Anker `0x10d6c`: Index `0x109`
würde auf `B+0x109` statt `B+0x212` zeigen. Letzteres passt zum zuvor direkt
geschriebenen Sensor-Halfword und zu den benachbarten Indizes `0x108/0x10a`.
Das stärkt die interne Konsistenz des Shift-Modells. Im gespeicherten SDK
fehlt aber weiterhin ein unabhängiges Beispiel **dieser exakten Form**.
Kein ungeprüfter Shift wird als gesicherte ISA-Semantik übernommen.

**Signed extract (`sextra`):** Bei `0x10bda` wird ein 16-Bit-Feld aus `r14`
vor einer 32-Bit-Akkumulation verwendet. Das gegenwärtige P-Code-Modell
maskiert auf 16 Bit, behält aber eine 32-Bit-Zwischengröße; die anschließende
32→32-Vorzeichenerweiterung ist wirkungslos. `0xffff` wird so 65535 statt −1,
`0x8000` wird 32768 statt −32768. Ein reines mathematisches Gegenmodell
wurde gegen **alle 65.536** 16-Bit-Werte geprüft; die Modelle unterscheiden
sich bei sämtlichen 32.768 negativen Werten. Das zeigt den Fehler unter der
angenommenen Signed-Semantik, bestätigt aber nicht die Opcodebedeutung.
Die 14 vorhandenen **unsigned**-SDK-Beispiele sind dafür kein Ersatz.

Beide Grenzen bleiben explizit markiert. Die neue Byte-Store-Korrektur
schließt sie nicht. Insbesondere die Rekonstruktion negativer
Kalibrierungsakkumulationen und der Sensorfeldquellen bleibt bedingt.

## 6. Prüfungen, Ablage und nächster Schritt

**49 lokale Forschungstests bestanden**, zwölf davon neu. Sie prüfen
u. a. hohe Byte-Quellenregister, geänderte/trunkierte Operanden,
Suffix-/Präfix-Verwechslungen, falsche Kopiergrenzen, sechs unterscheidbare
synthetische Kanäle und die Trennung des `0x0a`-Sonderfalls von `0xe0`.
Die synthetische Abschnittsprobe erhält alle zwölf Bytes exakt; sie ist kein
vollständiger Funkdecoder, keine Firmwareemulation und keine Hardwareabnahme.

Die korrigierte Decoderkopie besteht **127 SDK-Instruktionskontrollen**
(83 bestehende + 44 Byte-Stores). Der abschließende begrenzte Firmwarelauf
enthält 19 Fenster mit **286 Decode-Datensätzen**, ohne Decodeabbrüche.
Explorative Fehlstarts, unbekannte Operationen, eine überlaufene Sprungtabelle
und Fenster jenseits der untersuchten Funktionsgrenzen wurden ausgeschlossen
und im privaten Audit festgehalten. Parallelmitglieder werden nicht doppelt
als Speicheränderungen gezählt; keine allgemeine ISA-Validierung behauptet.

Privater Auditindex: `build/jieli-validation-20261018/anchors/wireless-review.json`;
eigene Feld-/Modelltests: `anchors/check_wireless.py`, `anchors/test_wireless.py`.
Alle vier ursprünglichen App-Hashes und die Sandbox-/Unverändertheitsprüfungen
wurden kontrolliert. Der öffentliche Commit enthält ausschließlich
Dokumentation, keine Firmware, fremden Decoderquellen oder Disassemblies.

Nächste gezielte Offline-Lücke: Registrierung und Implementierung des
Transport-Callbacks sowie der zugehörige Empfangseinstieg, anschließend
die noch offenen exakten Decoderformen und weitere Schreiber von
Sensorregistern/Offsets. **0,07 Grad/s je ST-Sensorzählwert bleibt ein
bedingter Kandidat, kein bestätigter USB-Gyrofaktor.** Physikalische
Kalibrierung bleibt pausiert; der laufende Treiber bleibt unverändert.
