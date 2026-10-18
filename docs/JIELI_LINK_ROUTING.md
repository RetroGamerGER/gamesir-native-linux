# Jieli: Sendepfadauswahl und Dongle-Empfang

Stand: 18. Oktober 2026. Fortsetzung der
[Callback-Registrierung](JIELI_RADIO_CALLBACK.md). Ausschließlich statische
Offline-Analyse unveränderter lokaler Firmwarekopien. Keine Zielausführung
oder Emulation, Netzwerk-/Hardwarezugriffe, Installation oder Treiberänderung.
Gyrokalibrierung bleibt pausiert.

**Fortsetzung:** Der [Empfangs-/Kontextfolgepass](JIELI_RX_CONTEXT.md)
korrigiert inzwischen den Exporter, ordnet die einfache Callback-Auswahl zu
und grenzt `0xfe42` als hardwaregestützte Paketverarbeitung ein. Die unten
beschriebenen offenen Stellen geben den Stand dieses früheren Passes wieder.

## Ergebnis

**Die Auswahlregel der beiden Controller-Sendepfade ist eingegrenzt:**
Eine zwölf Bit breite Verbindungskennung aus dem Rahmenkopf wird zuerst in
einer dynamischen Liste gesucht. Nur ohne Treffer wird eine zweite Tabelle
mit zwei Einträgen durchsucht. Die Sensorwerte entscheiden dabei nicht über
den Pfad. Welcher Eintrag beim aufgezeichneten Betrieb tatsächlich existierte,
ist weiterhin unbekannt. Die beiden Pfade werden deshalb nicht ungeprüft
mit Bluetooth, BLE oder einer bestimmten GameSir-Betriebsart gleichgesetzt.

Auf dem Dongle ist die Kette vom **aufbereiteten Empfangsdeskriptor über
Transporttabelle, Nachrichtenwarteschlange und Anwendungsworker bis zum
A2-Parser** zugeordnet. Damit ist dessen Einstieg kein isolierter Codefund
mehr. Die vollständige Funkstrecke ist trotzdem nicht geschlossen: Vor dem
Deskriptorhandler liegen noch bedingte Callback-Auswahl und ein ungeklärter
Verarbeitungsschritt. Keine Behauptung einer gemessenen Funkzustellung oder
eines bestätigten USB-Gyrofaktors.

## 1. Quellen und Adressräume

Verwendet wurden DV209 und DG144 aus dem bisherigen privaten Bestand;
die drei Controller-App-Hashes und der DG144-Hash wurden erneut geprüft.
Herkunft, vollständige Hashes und Decodergrenzen stehen in den
[Vorgängerberichten](JIELI_WIRELESS_DATAFLOW.md).
Alle Codepositionen unten sind **Dateioffsets** in der ausdrücklich genannten
App. Textzeiger werden mit `0x01e000c0` umgerechnet; RAM-Zellen sind keine
Dateioffsets. ROM- und RAM-Suffix-Aufrufe behalten ihre getrennten Modelle.

Der private Decoder wurde nicht verändert. Die neue vertiefte Routinganalyse
gilt für **DV209/DG144**; die zuvor geprüfte Callback-Gleichheit in DV515/608
ist kein Nachweis identischer vollständiger Funkpfade in allen Versionen.

## 2. Controller: welche Verbindung entscheidet?

Mit `B=0xf140` liest DV209 bei `0xd54e`–`0xd56a` die zwei Bytes
`B+0x20bc/0x20bd`. Der Rahmenkonstruktor `0x1b162` übernimmt sie in die
Kopfpositionen 0/1 und ergänzt im oberen Byte `0x20`.
Der Callback `0x320d2` liest diesen Zweibytewert; `0x320d6` entfernt dessen
obere vier Bits. Der verwendete Maskenwert ist `0xffff0fff`; bei dem
zweibyteigen Eingang entspricht das der Kennung `0x000..0xfff`.

| Reihenfolge | DV209-Fundstelle | Auswahlregel |
| --- | --- | --- |
| Liste A | `0x320dc` → `0x34f7e` | RAM-Basis `0x22898`; Statusbyte `+0x22` muss ungleich null sein. Liste ab `+0x24`, Ende am Kopf. Verglichen wird das Halfword bei Knoten `+0x94`; Rückgabe bei Treffer: Knoten minus `0x2c`. |
| Pfad A | `0x320e0`–`0x320e6` | Treffer führt unmittelbar nach `0x365e0` → `0x36260`. B wird dann nicht geprüft. |
| Tabelle B | `0x320ec` → `0x3a34a` | RAM-Basis `0x23aa8`, zwei Slots im Abstand `0x98`, Ende bei Basis `+0x130`. Halfword bei Slot `+0x60` muss ungleich null sein und zur Kennung passen. |
| Pfad B | `0x320f0`–`0x320f6` | Nur nach fehlendem A-Treffer und vorhandenem B-Treffer nach `0x3a370`. |
| Kein Treffer | `0x320fa` | Rückkehr ohne belegte Weitergabe an einen dieser Sendepfade. |

A hat damit Vorrang, falls beide Zuordnungen existieren. Das ist eine
Transportauswahl, keine Rückkehr zum Linux-Treiber `xpad` und keine
Sensorerkennung. Schreiber der Kennung und der Verbindungsmitgliedschaft
sowie deren tatsächliche Werte bleiben offen. Die in diesem Pass gefundenen
direkten Referenzen auf die Kennungsbytes waren Leser; das schließt
zusammengesetzte oder indirekte Schreibzugriffe nicht aus.

Die schon belegten Kopierstellen beider Pfade entfernen vier äußere
Kopfbytes und behandeln die verbleibenden Nutzdaten abschnittsweise bzw.
als Kopie. Diese vier Bytes enthalten keine der zwölf Sensorbytes.

## 3. Dongle: Empfangsdeskriptor zur Anwendungsnachricht

DG144 verwendet die Transporttabelle bei `0x18928`. Ihre Auswahl wird bei
`0x18ba0`–`0x18bac` in RAM `0x1556c` gespeichert. Slot `+0x18` zeigt auf
`0x19042`; der getrennte Setter in Slot `+0x10` ist `0x19034`.
Der Transportworker `0x18e7a` registriert über diesen Setter den
anderen Datenrichtungs-Callback `0x190a8`. Diese Richtungen nicht vermischen.

| Station in DG144 | Statische Beziehung |
| --- | --- |
| Deskriptor aufbereiten `0x1c850`–`0x1c87e` | Eingang `Q` aus Argument 1, Länge aus `Q+0x0a`; null überspringt die Weitergabe. Paketzeiger `P=Q+0x10`. Vier Kopfbytes werden dort aus Verbindungsdaten/Flags und Länge gebildet; die danach liegenden Nutzdaten werden in diesem Abschnitt nicht umgerechnet. |
| Transport aufrufen `0x1c880`–`0x1c88e` | Ausgewählte Tabelle, Slot `+0x18`, indirekter Aufruf mit `2, P, Länge+4`. |
| Nachricht erzeugen `0x1908c`–`0x1909e` | Operationswert 2 stellt Paketzeiger und 16-Bit-Länge für Nachricht `0x400002` an `btstack` bereit. Operationswert 4 verwendet einen getrennten Ereignispfad. |
| Anwendungsworker registrieren `0xa660`–`0xa670` | Entry-Textzeiger auf `0x89e4`, Taskname ebenfalls `btstack`, Übergabe an Task-Helfer. |
| Nachricht auswählen `0x8f0c`–`0x8f1e` | Warten auf Nachricht; nach geprüftem Rückgabewert wird `0x400001` abgezogen. Sprungtabelleneintrag 1 führt für `0x400002` nach `0x8f4c`. Die sechs Tabellenbytes sind Daten, kein linearer Code. |
| Paket übernehmen `0x8f4c`/`0x8f58` | Paketzeiger und Länge aus derselben Nachrichtenstruktur laden. |

Die Dongle-Listensuche bei `0x1c386` hat dieselbe hier relevante Struktur
wie Controller-Liste A: Kennung bei Knoten `+0x94`, Kontext bei Knoten
minus `0x2c`. Das entspricht Kontext `+0xc0`, aus dem der DG-Kopfaufbau
seine Kennung bezieht. Das stützt die Strukturzuordnung, beweist aber
keine identischen Handles auf beiden Geräten oder die reale Wahl von A.

### Neu eingegrenzte Grenze unterhalb des Deskriptorhandlers

`0x1d81c` reicht an `0x1c850` weiter. Ein zweiter Kandidat `0x1c8fe`
ruft denselben Handler bei bestimmten Deskriptorflags auf; andere Flags
führen in weitere Zweige. Beide Textzeiger stehen bei `0x1c7aa`/`0x1c7b0`
vor dem Helferaufruf `0x1af88`.

Dieser Helfer bewahrt das übergebene Callback-Argument und verwendet es
bei `0x1b04e` indirekt. Auf einem vorgeschalteten Zweig liegen jedoch
`0x1b03c` → **`0xfe42`** und danach eine Kopie zurück in Deskriptor-
Nutzdaten. Zweck und Eingangsbedingungen dieses Verarbeitungsschritts
sind noch nicht validiert. Er wird weder als bloße Kopie noch als
Sensor-Skalierung oder bewiesene Entschlüsselung bezeichnet.

Hinzu kommt eine konkrete Analysegrenze: Der private P-Code zeigt nach der
bedingten Blockanweisung `0x1c7a6` beide Zeigerzuweisungen ohne ihre
erforderlichen bedingten Wrapper. Daraus darf weder „beide werden
ausgeführt“ noch „immer der zweite Callback“ folgen. Die SLEIGH-Beschreibung
kennt bedingte Blöcke; ihre Kontextübernahme im verwendeten statischen
Exporter ist an dieser Stelle separat zu prüfen. Kein neuer Decoderpatch
und keine stillschweigende Auflösung dieser Auswahl.

## 4. Welche Pakete erreichen den A2-Sensorpfad?

Mit `D=0x62c0` und Paketzeiger `P` passiert der betrachtete Zweig:

1. `0x8f50`–`0x8f68`: niedrige zwölf Kopf-Bits mit gespeicherter DG-Kennung
   aus `D+0x670/0x671` vergleichen. Ein unpassendes Paket geht nicht direkt
   in diesen Sensorzweig.
2. `0x9144`/`0x9184`/`0x918e`: für den untersuchten Zweig `P[6]=0x4f`
   und `P[7] != 0`; andere Kanäle/Zustände haben eigene Pfade.
3. `0x919c`–`0x91d6`: `P[9]=0x11`, Aufruf eines Prüfsummenhelfers über
   den inneren Bereich und Vergleich mit zwei Trailerbytes. Ein Fehlschlag
   verlässt diesen Zweig. Vollständige CRC-Semantik und Längensicherheit
   aller Fälle sind damit **nicht** nachgewiesen.
4. Ab `0x91f0`: variable Teilabschnitte durchlaufen. Ausgangscursor `P+18`;
   Längen aus Positionen 10/11 (Bytes), 12/14/16 (Little-Endian-Halfwords).
   Der vierte Abschnitt hat gesonderte Bereichs-/Queuebehandlung. Die
   synthetische Probe beschränkt ihn auf den geprüften Bereich 0–64.
5. `0x9844`–`0x9848`: verbleibender Abschnitt vorhanden und Typ `0xa2`.
   `0x98be`–`0x98c4` prüft sein Sequenzbyte; ein bereits gespeicherter
   Wert wird in diesem Zweig nicht erneut in die Reportqueue geschrieben.
6. `0x98ce`/`0x9908`–`0x9912`: Quelle Abschnitt `+2`, Queue `D+0x2e0`,
   Länge ohne die zwei Abschnittskopfbytes. Der Sonderkopf `02/20/…/1c`
   hat einen separaten Zweig; unser Bericht beginnt mit `0x10`.

Damit erreicht der passende `10/3c/e0`-Bericht den bereits untersuchten
[Queue-/USB-Pfad nach IN `0x82`](JIELI_WIRELESS_DATAFLOW.md#3-dongle-a2-entpacken-in-queue-speichern-an-in-0x82-senden).
Die zwölf Sensorbytes bleiben in diesen ausgewählten oberen Transport-
und Queueabschnitten an Reportpositionen 17–28. Keine dort gefundene
zusätzliche Verstärkung, Achsenumordnung oder Offsetsubtraktion.
Vorgeschaltete Sensorbearbeitung und ungeklärte untere Transportbearbeitung
sind davon ausdrücklich ausgenommen.

## 5. Prüfung und nächste gezielte Lücke

- **70 lokale Forschungstests bestanden**, neun neu. Mutationen von
  Tabellenslot, Worker-Zeiger, Nachricht, Sprungtabelle und Taskname werden
  abgewiesen. Synthetische Framing-Proben erhalten sechs unterscheidbare
  Sensorwerte bei unterschiedlichen Abschnittslängen und Sequenzbytes.
  Sie berechnen keinen Funk-CRC und emulieren keine Firmware.
- Abschließender isolierter statischer Lauf: **30 begrenzte Fenster,
  461 Decode-Datensätze, kein Decodeabbruch**. Kein Vollständigkeitsbeweis
  der ISA. Fehlstarts in Instruktionsmitten, überlaufene Sprungtabellen und
  Fortsetzungen hinter den ausgewählten Funktionsenden sind ausgeschlossen
  und privat protokolliert. Parallelmitglieder werden nicht doppelt gezählt.
- Vier App-Hashes und Sandbox-/Unverändertheitsprüfungen bestätigt.
  Der Decoder bleibt unverändert; die offenen EDD8-/Signed-Formen sind
  weiterhin nicht unabhängig validiert.
- Privater Auditindex: `build/jieli-validation-20261018/anchors/routing-review.json`.
  Öffentlicher Commit ausschließlich Dokumentation; keine Firmware,
  fremden Decoderquellen oder Disassemblies.

Als Nächstes gezielt die bedingte Callback-Auswahl und `0xfe42` klären,
danach Ursprung der Empfangsdeskriptoren sowie Kennungs-/Kanalschreiber.
Die reale Verbindung, letzte wirksame Sensorkonfiguration und physikalische
Kalibrierung bleiben offen. **0,07 Grad/s je ST-Sensorzählwert bleibt ein
bedingter Kandidat, kein bestätigter Faktor für USB-Rohwerte.**
