# Jieli: zwölf Sensorbytes bis zum Telemetriebericht

Stand: 18. Oktober 2026. Statische Offline-Fortsetzung der
[Sensorinitialisierung](JIELI_SENSOR_INITIALIZATION.md), mit denselben drei
gehashten `app.bin`-Dateien und lokal gespeicherten Referenzen. Keine
Firmwareausführung oder Emulation, Netzwerk-/Hardwarezugriffe,
Treiberänderung oder Wiederaufnahme der Gyrokalibrierung.

## Ergebnis

Der Datenfluss ist jetzt wesentlich weiter eingegrenzt:

- Der ST-Zweig bereitet das Lesen von zwölf Byte ab Registerargument
  `0x22` in einen gemeinsamen Empfangspuffer vor; die Verarbeitung ordnet
  die sechs 16-Bit-Werte um.
- Ein durch ein Statusbyte bedingter Block zieht sechs gespeicherte
  16-Bit-Offsets ab. Unveränderte Sensorregisterwerte darf man deshalb
  auch bei gleichbleibendem Maßstab nicht pauschal behaupten.
- Der ST-Ausgabezweig enthält zwischen diesen korrigierten Feldern und
  seinem Telemetriepuffer keine zusätzliche Gyro-Multiplikation oder
  Division. Ein anderer Sensorzweig verwendet dagegen `976/1000`.
- Ein Berichtskonstruktor setzt die bekannte Kennung `10/3c/e0`, bereitet
  eine 24-Byte-Kopie vor und übergibt 64 Byte an eine Warteschlange. Die
  Adressrechnung dieser Kopie ergibt exakt die bekannten Sensorpositionen
  **17, 19, 21, 23, 25, 27**.
- Ein zweites Ausgabeformat negiert Gyroachsen und halbiert
  Beschleunigungswerte. Diese Transformation darf nicht auf unseren
  `10/3c/e0`-Bericht übertragen werden.

**Fortschreibung:** Der [nachfolgende Transportpass](JIELI_USB_TRANSPORT.md)
ordnet den externen Aufruf unabhängig dem SDK-ROM-Stub `memcpy`/`memmove`
zu und verfolgt die Controller-Queue bis IN `0x84`. Ein separater
Dongle-Puffer erreicht IN `0x82`; seine Verknüpfung mit genau diesen
Sensorbytes über Funk bleibt offen. Dies ist eine statisch gestützte Produzentenkette,
kein ausgeführter End-to-End-Nachweis und keine Freigabe eines Gyrofaktors.
Einige benötigte indizierte Speicherzugriffe sind im verwendeten Decoder
fehlerhaft modelliert; die betroffenen Aussagen sind unten eingegrenzt.

## 1. Empfang und Reihenfolge

Alle Codepositionen im Text sind zunächst **DV209-Dateioffsets**. `B` steht
für die gemeinsame Datenbasis `0xf140`, die im Sensorpfad bei `0x10796`
und im Berichtskonstruktor bei `0x1ace6` geladen wird. Das sind
Firmwareadressausdrücke, keine Linux-Geräteadressen.

Die Initialisierung setzt den Sensorselektor `B+0x674` zunächst auf eins
(`0xac34`–`0xac38`); der Fehler-/Alternativpfad setzt ihn auf null
(`0xad8c`–`0xad92`). Derselbe Selektor steuert sowohl die Empfangszuordnung
als auch die spätere Auswahl der Gyroumrechnung. Seine tatsächliche
Laufzeitbelegung auf einem Controller wird damit nicht gemessen.

Beim ST-Zweig wird `r2 = B+0x980` bei `0x1092a` vorbereitet. Im Lesezweig
folgt der bereits bekannte Aufruf `0x10a16`: Geräteargument `0xd6`,
Startregister `0x22`, Länge zwölf. Der gemeinsame Busabschluss bleibt
eine eigene offene Transportfrage.

Unter der LSM6DS3TR-C-Registerbelegung enthält der Sensorpuffer:

`Gx, Gy, Gz, Ax, Ay, Az` — jeweils Low-Byte, High-Byte.

Der ST-spezifische Zeigerblock `0x10930`–`0x10952` springt direkt in die
gemeinsame Zusammensetzung bei `0x10a60`. Er darf nicht durch den
QMI-Zeigerblock `0x10a3e` ersetzt werden. Die Zusammensetzung bei
`0x10a74`–`0x10ac8` ergibt:

| Zwischenfeld ab `B+0x20a` | Bytepaar im ST-Empfangspuffer | Sensorregisterachse |
| --- | --- | --- |
| `+0` | 6/7 | Ax |
| `+2` | 10/11 | Az |
| `+4` | 8/9 | Ay |
| `+6` | 0/1 | Gx |
| `+8` | 4/5 | Gz |
| `+10` | 2/3 | Gy |

Diese Zuordnung bezeichnet Sensorregisterachsen. Sie benennt **keine
physisch bestätigten Controller- oder SDL-Achsen**. Insbesondere wird keine
frühere Messansage nachträglich als Orientierungskalibrierung gewertet.

## 2. Kalibrierungszweig und Offset-Abzug

Der Tabellensprung bei `0x10ad4` hat vier Einträge. Seine Ziele sind
`0x10ada`, `0x10b26`, `0x10b42`, `0x10b6c`; die vier Tabellenbytes bei
`0x10ad6`–`0x10ad9` sind keine Instruktionen. Die Zweige treffen sich
bei `0x10b7c` oder verlassen diesen Verarbeitungspfad.

Die folgenden Blöcke enthalten das Leeren von sechs Akkumulatoren,
Addition von Sensorwerten, einen Zähler und Divisionen durch `0x104`
(260). Für einen Beschleunigungsakkumulator erscheint ein Abzug von
`0x2000` (8192). Das passt zu einer Ruhe-/Biasbestimmung mit einer
1-g-Referenzachse. Es beweist weder, dass diese Kalibrierung aktuell läuft,
noch eine allgemeine, bewegungsunabhängige Korrektheit des Verfahrens.
Die genaue Behandlung negativer Werte im Akkumulationspfad bleibt wegen
der unten beschriebenen `sextra`-Decodergrenze separat zu verifizieren.

Ein konkreter, einfacher Teil ist dagegen direkt überprüfbar:
`0x10d12`–`0x10d1a` prüft das Statusbyte `B+0x698`. Nur wenn es ungleich
null ist, folgen bei `0x10d1c`–`0x10d4a` sechs Load/Subtract/Store-Bündel:

| Messfeld | Abgezogenes Offsetfeld | Bedeutung unter der ST-Zuordnung |
| --- | --- | --- |
| `B+0x20e` | `B+0x21a` | Ay |
| `B+0x20c` | `B+0x21c` | Az |
| `B+0x20a` | `B+0x21e` | Ax |
| `B+0x214` | `B+0x220` | Gy |
| `B+0x212` | `B+0x222` | Gz |
| `B+0x210` | `B+0x224` | Gx |

Die Stores behalten die unteren 16 Bit; dieser Block enthält keine
Sättigungsbegrenzung. Herkunft und aktuelle Werte der Offsets, mögliche
Ladevorgänge aus persistentem Speicher und spätere Änderungen sind noch
nicht vollständig rekonstruiert. Der Kalibrierungszweig enthält außerdem
eine Übergabe von 14 Byte einschließlich zwei Markierungsbytes an den
Helfer bei `0x33e`. Daraus folgt hier noch keine verifizierte EEPROM-
Transaktion oder sichere Kalibrierungs-API.

## 3. Zwei Ausgabeformate auseinanderhalten

Für die folgenden Beziehungen bezeichnet ein Strich den Wert **nach** dem
bedingten Offset-Abzug, oder den unveränderten Wert bei inaktivem Abzug.

Der Pfad über `0x10d4c`–`0x10d80` und `0x10dbe`–`0x10de8` packt in
`B+0x1401` bis `B+0x140c` sechs LE16-Werte:

`Gy′, Gz′, Gx′, Ay′, Az′, Ax′`

Im ST-Zweig sind das nur Loads und Byte-Stores, ohne zusätzliche
Negierung oder Verstärkung. Für die Gyro-Loads muss dabei die indizierte
Halfword-Form als `B + (Index << 1)` gelesen werden; siehe Decodergrenze.
Die direkten Halfword-Stores der Messfelder und die Nachbarzugriffe
stützen genau diese Adressierung.

Beim Selektor null führt der Alternativpfad `0x10d82`–`0x10dba`
drei Multiplikationen mit `0x3d0` (976) und Divisionen durch `0x3e8`
(1000) vor dem Packen der Gyrowerte aus. **Diese Umrechnung gehört nicht
zum untersuchten ST-Zweig.** Sie darf weder als allgemeiner GameSir-Faktor
noch als Korrektur des LSM6DS3TR-C-Datenblattwerts verwendet werden.

Die anschließende zweite Ausgabe ab `B+0xb97` hat eine andere Beziehung:

`−Gz′, −Gx′, −Gy′, Ax′/2, Az′/(−2), Ay′/2`

Dort stehen tatsächliche Negationen und vorzeichenbehaftete Divisionen.
Ihre Transport-/Protokollzuordnung bleibt offen. Ein weiterer Verbraucher
bei `0x578ce` kopiert zudem die beiden Dreiergruppen aus `B+0x1401` in
umgekehrter Gruppenreihenfolge nach `B+0x908`, ohne die Bytes innerhalb
eines LE16-Wertes zu vertauschen. Nicht alle Sensorausgaben dieser Firmware
haben somit dasselbe Format.

## 4. Verbindung zum bekannten Bericht

Bei `0x1aeda` wird `r4 = B+0x1434` vorbereitet. Der Konstruktor setzt
Byte 0 auf `0x10`, Byte 3 auf `0x3c` und Byte 4 auf `0xe0`. Bei
`0x1aefc` wird ein externer Helfer mit diesen Argumenten aufgerufen:

- Ziel `B+0x1439` = Bericht +5;
- Quelle `B+0x13f5`;
- Länge 24 Byte.

Der beobachtete direkte CALL-Zielausdruck im Decode mit Dateibasis null
ist `0x3126e8`. Das ist **kein erreichbarer Dateioffset dieser App**.
Der [Transportfolgepass](JIELI_USB_TRANSPORT.md#1-quellen-und-adressmodell)
ordnet ihn mit Codebasis `0xffe000c0` dem SDK-ROM-Eintrag `0x1127a8`
(`__stub_memcpy` → `memmove`) zu, gestützt durch weitere API-Aufrufe.
Das SDK beschreibt eine byteerhaltende Kopie; die tatsächliche ROM-Version
im Controller bleibt unbeobachtet.

Unter genau dieser Kopiersemantik liegt das erste Sensorbyte bei:

`5 + (0x1401 − 0x13f5) = 17`.

Damit passen alle sechs Positionen zum vorhandenen
[Offline-Parser und Captureformat](PROTOCOL.md):

| Reportoffset | Hypothetischer ST-Ursprung nach Offsetkorrektur |
| --- | --- |
| 17/18 | Gy′ |
| 19/20 | Gz′ |
| 21/22 | Gx′ |
| 23/24 | Ay′ |
| 25/26 | Az′ |
| 27/28 | Ax′ |

Ein Vergleichs-/Kopierhelfer bei `0x1aa92` und der nachfolgende bedingte
Aufruf bei `0x1afd2` übergeben den 64-Byte-Puffer an `0x2e8`. Dessen
Schleife kopiert einzelne Bytes in einen Ringpuffer, ohne Sensorarithmetik.
Ein Verbraucher bei `0x1b000` nutzt den korrespondierenden Reader `0x114b6`
und reicht den entnommenen Puffer über `0x1afd8` an `0x3bc8` weiter.
Der [Transportfolgepass](JIELI_USB_TRANSPORT.md#2-controller-reportkopie-bis-usb-in-0x84)
weist diesem MMIO-Pfad Endpunkt 4 / IN `0x84` zu; die aktive Modusauswahl
bleibt offen. Dieser Controllerpfad ist vom Dongle-IN `0x82` zu trennen.
Bedingte Ausführung, Queue-Verfügbarkeit und erfolgreiche
USB-Abschlüsse sind mit diesen statischen Ausschnitten nicht bewiesen.

## 5. Gegenprüfung und Grenzen des Decoders

Zehn ausgewählte Blöcke wurden in allen drei gehashten Apps eindeutig und
bytegleich gefunden. Beispiele:

| Block | DV209 | DV515 | DV608 |
| --- | --- | --- | --- |
| ST-Empfangszeiger | `0x1092a` | `0x10932` | `0x10932` |
| Zusammensetzung | `0x10a60` | `0x10a68` | `0x10a68` |
| Offsetblock | `0x10d12` | `0x10d1a` | `0x10d1a` |
| ST-Ausgabe | `0x10d5e` | `0x10d66` | `0x10d66` |
| Berichtskopf | `0x1aeda` | `0x1afb2` | `0x1afb0` |

Die Bytegleichheit ist eine unabhängige Versionsgegenprobe, keine
Bestätigung jeder Disassemblersemantik. Zusätzlich wurden vier kompakte
Halfword-Loads, sechs Halfword-Stores, 23 erweiterte Byte-Loads und elf
Adressadditionen gegen das bereits gespeicherte offizielle Jieli-ROM-Listing
geprüft. Neue Decodergrenzen:

- Erweiterte Byte-Loads verwenden in den 23 SDK-Kontrollen den oberen
  Immediate-Nibble mit Faktor 16. Der Beschreiber setzt ihn fälschlich mit
  Faktor 256 ein. Beispielsweise ist `0x15` statt `0x105` zu lesen; die
  Zustandsbytes hier sind entsprechend `B+0xb0`/`B+0xb3`, nicht `B+0xb00`/
  `B+0xb03`. Der eigene begrenzte Feldleser kontrolliert diese Form.
- Indizierte Halfword-Loads verlieren im P-Code den in der Operandform
  angegebenen Shift. Andere indizierte Stores verschieben fälschlich die
  Summe von Basis und Index. Hier wird `B + (Index << Größe)` nur mit
  expliziter Operand-/Nachbarzugriffskorroboration verwendet. Ein separates
  unabhängiges Halfword-Index-Referenzbeispiel fehlt noch.
- `sextra` extrahiert im P-Code ein bereits 32 Bit breites maskiertes
  Ergebnis und erweitert dadurch dessen Vorzeichen nicht korrekt. Aussagen
  über Mittelwerte negativer Samples dürfen diesen P-Code nicht übernehmen.
- Parallelmitglieder werden im linearen Decode erneut ausgegeben.
  Insbesondere bei Byte-Stores und anschließender Registeränderung würde
  doppeltes Zählen falsche Daten behaupten. Hier wird jedes Mitglied nur
  einmal betrachtet; das ist keine allgemeine Decoderreparatur.

Die folgende Prüfung beschreibt diesen ursprünglichen Datenflusspass;
die spätere private Reparatur von Byte-, Wortindex- und Einzelbitformen,
83 SDK-Gegenproben und weiterhin offene Halfword-/Vorzeichenformen stehen
im [Transportbericht](JIELI_USB_TRANSPORT.md#4-decoderoperationen-korrigiert-und-weiterhin-offen).

Explorative Fenster stoppten an vier unbekannten Decodepositionen,
einschließlich einer überlaufenen Sprungtabelle und einer ungeeigneten
Startgrenze. Diese Teile wurden nicht als Codebeleg verwendet. Der danach
begrenzte Drei-Versionen-Lauf mit 24 Fenstern erzeugte 501 Datensätze ohne
Decodefehler; Isolation und unveränderte Inputs wurden bestätigt.

25 lokale Forschungstests bestanden, davon zehn neue Gegenproben für
Tabellen-/Dateigrenzen, mutierte Offsetoperationen, Operandfelder,
Vorzeichen, 16-Bit-Überlauf und Kopiergeometrie. Ein ausdrücklich
**synthetisches** Sechskanalmodell wird dabei durch den bestehenden
Protokollparser gegengeprüft; dessen 15 vorhandene Tests bestanden zusätzlich.
Der Parser bleibt unverändert und
kennzeichnet Einheiten/Achsen weiterhin als unbestätigt. Das ist keine
Treibersuite oder Hardwareabnahme.

Private Belege, eigene Feldleser/Tests und Sandboxergebnisse bleiben unter
`build/jieli-validation-20261018/`; Index `anchors/sensor-report-evidence.json`
und Prüfbericht `anchors/sensor-report-review.json`. Firmware, Disassemblies
und private Originaldaten werden nicht in Git aufgenommen.

## Konsequenz und nächster Offline-Schritt

Der Kandidat **0,07 Grad/s je ST-Sensorzählwert** wird durch den hier
rekonstruierten ST-Telemetriepfad gestützt: Es ist kein weiterer Gyro-Gain
in diesem Abschnitt erkennbar. Er bleibt bedingt auf Sensorvariante,
Registerkonfiguration, korrekte Auflösung der noch offenen Helfer und die
tatsächlich verwendete Firmware. Offsets und Achsen müssen berücksichtigt
werden. Der laufende Treiber erhält daraus **keinen neuen Faktor**.

Nach der [Zuordnung von Kopie und USB-Sendepfaden](JIELI_USB_TRANSPORT.md)
hat der [Funkrahmen-Folgepass](JIELI_WIRELESS_DATAFLOW.md) den Formatcache-
Writer und einen getrennten `A2`-/Queue-Pfad bis Dongle-IN `0x82` eingegrenzt.
Als Nächstes dessen aktive Transport-Callback-Anbindung schließen,
indizierte Halfword-/signed-extract-Semantik unabhängig absichern und weitere
Schreiber der Sensor-/Offsetfelder sowie spätere Bereichswechsel untersuchen.
Erst danach ist die statische
Kette ausreichend geschlossen, um einen künftigen, gesondert freigegebenen
physikalischen Kalibrierungstest gezielt auszuwerten. Dieser bleibt pausiert.
