# Jieli: Kopierhelfer, USB-Sendepfade und Decodergrenzen

Stand: 18. Oktober 2026. Offline-Fortsetzung der
[Zwölf-Byte-Analyse](JIELI_SENSOR_REPORT_DATAFLOW.md). Ausschließlich lokale
Dateien und bereits gespeicherte Referenzen; keine Firmwareausführung oder
Emulation, Netzwerk-/Hardwarezugriffe, Installation oder Treiberänderung.
Die Gyrokalibrierung bleibt pausiert.

## Ergebnis und Beweisgrenze

Der externe Kopieraufruf lässt sich jetzt konsistent dem offiziellen
Jieli-ROM-Eintrag `__stub_memcpy` zuordnen. Dessen dokumentierter Körper
kopiert die Bytes ohne Sensorarithmetik. Der anschließende Sendepfad des
**Controllers verwendet USB-IN-Endpunkt `0x84`**, nicht den in unseren
Funk-Dongle-Mitschnitten beobachteten Endpunkt `0x82`.

In der separat untersuchten **Dongle-Firmware** wurde ebenfalls ein
64-Byte-Sendepfad gefunden, dort über Endpunkt 2 / IN `0x82`. Seine Quelle
ist noch nicht als Empfangspuffer genau unserer zwölf Sensorbytes belegt.
Damit sind zwei Transportabschnitte zugeordnet, aber noch keine lückenlose
Sensor→Funk→Dongle→USB-Kette. Ein passender Endpunkt und eine passende
Paketlänge beweisen den Sensorinhalt nicht.

## 1. Quellen und Adressmodell

Die drei Controller-Apps DV209, DV515 und DV608 sind dieselben gehashten
Dateien wie in der [Initialisierungsanalyse](JIELI_SENSOR_INITIALIZATION.md).
Hinzu kommt ausschließlich für die Dongle-Codeanalyse:

| App | Bytes | SHA256 |
| --- | --- | --- |
| `JS_3103_DG_V144_No_Key` | 246552 | `b1181a4a244e885f033b281289f87a49893ea7fdfd8e70f019f681fe95aaf3e6` |

Die unabhängige Referenz ist das lokal gespeicherte offizielle
[Jieli-Tech-ROM-Listing, Commit fdc018de](https://github.com/Jieli-Tech/fw-AC63_BT_SDK/blob/fdc018de81629e21e594d677cf05f87d288be0f0/cpu/br23/tools/rom.lst),
SHA256 `650bd301951a311207aad7000fa27bdfa8fce0ae8101576eaaf302072982f1d2`.
Es wurde in diesem Arbeitsschritt nicht erneut heruntergeladen.
Es beschreibt einen SDK-ROM-Stand; es ist kein ROM-Abzug unseres Controllers.

Alle nachfolgenden App-Codepositionen sind **Dateioffsets**. Für die
geprüften relativen externen CALLs ergibt das Codeadressmodell
`Dateibasis = 0xffe000c0` in 32-Bit-Moduloarithmetik passende ROM-Adressen:

| Ziel bei Dateibasis null | Ziel mit Codebasis | SDK-Symbol |
| --- | --- | --- |
| `0x3126e8` | `0x1127a8` | `__stub_memcpy` |
| `0x3126f0` | `0x1127b0` | `__stub_memcmp` |
| `0x3126f4` | `0x1127b4` | `__stub_memset` |
| `0x3126f8` | `0x1127b8` | `__stub_strcmp` |
| `0x312700` | `0x1127c0` | `__stub_strlen` |
| `0x312704` | `0x1127c4` | `__stub_strncmp` |

Das Modell passt zugleich zu Kopier-, Nullungs-, Stringlängen- und
Vergleichsaufrufen mit entsprechenden Argumenten. Beispielsweise setzt
DV209 `0x442`–`0x44c` einen 64-Byte-Puffer mit Wert null; `0x1622` nutzt
eine Stringlänge; `0x2f2a`/`0x2f36` vergleichen Textzeiger. Der bekannte
Report-CALL `0x1aefc` löst mit der Codebasis direkt zu `0x1127a8` auf.
Die zuvor verwendete Text-/Datenbasis `0x01e000c0` liegt um `0x02000000`
versetzt. Daraus wird **keine allgemeine CPU-Adressmaske** abgeleitet;
die gesonderte Relokation anderer App-Abschnitte bleibt zu beachten.

Das SDK-Listing benennt bei `0x1127a8` den Sprung nach `memmove` bei
`0x11005e`. Dieser Körper enthält vorwärts/rückwärts laufende Byte- und
Wortkopien, einschließlich Überlappungsbehandlung. Keine Multiplikation,
Achsenumordnung oder Offsetkorrektur von Sensorfeldern. Seine Semantik
wurde aus dem offiziellen Listing gelesen; die vom privaten Decoder
nicht unterstützte Repeat-Familie wurde dafür nicht ausgeführt oder erraten.

**Bewertung:** starke unabhängige ABI-/Adresskorroboration statt einer
bloßen Vermutung anhand dreier Argumente. Die tatsächlich verbaute
Silizium-/ROM-Version und ein erfolgreicher Lauf dieses Aufrufs bleiben
unbeobachtet.

## 2. Controller: Reportkopie bis USB-IN `0x84`

Hier gilt weiter `B = 0xf140` in DV209:

| Schritt | Fundstelle | Statische Aussage |
| --- | --- | --- |
| Bericht bauen | `0x1aeda`–`0x1aefc` | Kopf `10/3c/e0`; 24 Byte von `B+0x13f5` nach Bericht+5 kopieren |
| In Queue übergeben | `0x1afd2` → `0x2e8` | 64-Byte-Bericht; byteweise Ringpufferkopie |
| Queue entnehmen | `0x1b000`–`0x1b018` → `0x114b6` | Queuezeiger `B+0x73c`; Ziel `B+0x1034` |
| Sendeparameter | `0x1b02e` → `0x1afd8` | Endpunktnummer 4, Puffer und entnommene Länge |
| USB-Wrapper | `0x1afd8` → `0x3bc8` | Argumente `(Controllerindex 0, Endpunkt 4, Puffer, Länge)` |
| Sendepuffer befüllen | `0x3c36` | Aufruf desselben ROM-Kopierhelfers |
| Paket bereitstellen | `0x3c52`–`0x3c60` | Paketlänge in endpunktindiziertes MMIO-Feld; TXCSR lesen, Bit 0 setzen, schreiben |

Das Längenfeld wird als `0x1e1808 + (Endpunkt << 2)` adressiert, bei
Endpunkt 4 also `0x1e1818`. Der Indexhelfer `0x198` schreibt die
Endpunktnummer über USB-Register `0x0e`. `0x3b9c`/`0x2b72` lesen bzw.
schreiben die indizierten TXCSR-Register `0x11` und `0x12`. Das entspricht
den separat benannten SDK-Helfern `musb_write_index`, `usb_read_txcsr`
und `usb_write_txcsr`. Diese Zuordnung folgt aus Registern und Datenfluss,
nicht allein aus einer Zahl 4 im Aufruf.

Zwei unabhängige statische Gegenproben stützen die IN-Adresse:

- Die Initialisierung `0x4ed4`–`0x4ede` übergibt `0x84` an `0x2bb0`;
  die Richtungsprüfung bei `0x2bc6` testet korrekt Bit 7 und der IN-Zweig
  maskiert anschließend die Endpunktnummer mit `0x0f`.
- Ein Interface-/HID-Deskriptorfragment bei DV209 `0x28580`, DV515/608
  `0x28660`, beschreibt Interface 1 mit Interrupt-IN `0x84`, maximal
  64 Byte, Intervallfeld 1, und OUT `0x04`, maximal 64 Byte, Intervallfeld 5.
  Die Auswahl der umgebenden Konfiguration ist damit noch nicht rekonstruiert.

Der Reportkopf und der Wrapper liegen in DV515 um `0xd8`, in DV608 um
`0xd6` versetzt; die hier geprüften unteren USB-Helfer liegen gleich.
Alle drei Varianten wurden mit der korrigierten privaten Decoderkopie
erneut statisch geprüft. Die frühere Kopiergeometrie
`5 + (0x1401 − 0x13f5) = 17` bleibt erhalten.

Das ist ein lokaler USB-Pfad der Controller-App. Er beweist weder dessen
Aktivierung im früheren Funkbetrieb noch einen Wechsel des am Linux-Host
beobachteten Endpunkts. Die bestehende Treiber-/Capturezuordnung `0x82`
wird deshalb nicht geändert.

## 3. Dongle: separater 64-Byte-Pfad zu IN `0x82`

In DG144 gilt für diesen Dispatcher `D = 0x62c0`:

1. `0xd324`–`0xd32e` kopiert **64 Byte** von `D+0xa24` nach `D+0x8a4`
   über denselben zugeordneten ROM-Stub.
2. `0xd33e` ruft den Vergleichs-/Kopierhelfer `0xcd50` mit einem
   zweiten Puffer `D+0x8e4` auf. Rückgabewert und Statusbyte steuern die
   Weiterleitung nach `0xd3b0`; es wird kein unbedingter Versand behauptet.
3. `0xd3ba`–`0xd3c0` übergibt Endpunktnummer **2**, Länge **64** und
   den Puffer an `0xcd44`. Dieser Wrapper springt zu USB-Sendehelfer `0x186c`.
4. `0x18d2` kopiert in den USB-Sendepuffer; `0x18ee` schreibt die Länge
   nach `0x1e1808 + (2 << 2)`. `0x18f4`–`0x18fc` setzt TXCSR-Bit 0.
   Die zugehörigen Helfer `0x162`, `0x1840`, `0x146c` verwenden wieder
   Indexregister `0x0e` und TXCSR `0x11`/`0x12`.

Der TX-Pfad entspricht damit Endpunkt 2 in IN-Richtung, also `0x82`.
In der Datei gibt es außerdem passende Endpoint-Deskriptorfragmente.
Die vollständige Zuordnung der Deskriptorvarianten zu den Betriebsmodi
ist weiterhin offen. Es wurde nur DG144 entlang dieser Kette analysiert;
keine entsprechende Aussage für sämtliche Dongle-Firmwareversionen.

**Die noch fehlende Verbindung:** Wer befüllt `D+0xa24`, und enthält
dieser Puffer in unserem Funkmodus genau den `10/3c/e0`-Bericht samt
Sensorfeldern? Der Dispatcher verarbeitet auch andere 64-Byte-Formate.
Die Zwölf-Byte-Zuordnung darf nicht allein aus der Paketlänge folgen.

Eine untersuchte Referenz auf `D+0xa28` bei `0xc5ea` ist kein
nachgewiesener Writer: Sie übergibt den Zeiger bei `0xc5fa` an `0x174e`.
Dort wird der zuvor zugeordnete `strlen`-Stub aufgerufen und danach über
Bytes bis zum Nullzeichen iteriert. Das ist ein Textverbraucher-Kandidat,
kein Beleg für den gesuchten Empfangspfad. Die Sprungtabelle ab `0xc60c`
wird ausdrücklich nicht als Code interpretiert.

## 4. Decoderoperationen: korrigiert und weiterhin offen

Grundlage bleibt der private, unverändert aufbewahrte Quarkslab-Stand
`e1bd0707874b77b759401555d24839ad43af1267`. Eine **separate private Kopie**
erhielt drei begrenzte Korrekturen zusätzlich zur früheren E040-Korrektur:

| Form | Fehler | Unabhängige Kontrollen im gespeicherten SDK-Listing |
| --- | --- | --- |
| Erweiterter Byte-Load | Oberes Versatz-Nibble mit 256 statt 16 gewichtet | 23 |
| Indizierter Wort-Load/Store | `(Basis + Index) << 2` statt `Basis + (Index << 2)` | 5 Loads, 6 Stores |
| Einzelbit-Sprung `e850`-Familie | Falsche Maske und verlorene Null-/Nichtnull-Bedingung | 35 |

Der Einzelbit-Sprung verwendet im zweiten Halbwort Bitposition 11–15,
Bedingung Bit 9 und einen vorzeichenbehafteten 9-Bit-Sprungversatz in
Halbwörtern relativ zur Folgeinstruktion. Bit 10 wird im geprüften Modell
als reserviert abgewiesen. Beispiel: DV209 `0x2bc6` testet `r6 & 0x80`
auf **ungleich null**. Die TXCSR-Abfragen bei `0x3c1a` ff. testen
`0x4000`, `0x04`, `0x02`, `0x01`. Mit den alten Masken wäre die
Transportdeutung falsch gewesen. Das sind Decoderfehler, kein Nachweis
eines Fehlers in GameSirs Firmware.

Zusätzlich stimmen 14 **unsigned-extract**-Kontrollen mit dem SDK überein.
Insgesamt wurden die erzeugten P-Code-Operationen von **83 SDK-Instruktionen**
gegen die unabhängigen Listing-Operanden geprüft, ohne Ausführung.

Weiterhin offen:

- Für die skalierten indizierten **Halfword**-Zugriffe fehlt ein unabhängiges
  Beispiel dieser exakten Form im geprüften SDK-Listing. Operandmuster und
  benachbarte Felder stützen den Shift, ersetzen aber keine zweite Referenz.
- **`sextra`** erzeugt weiterhin eine wirkungslose 32→32-Bit-
  Vorzeichenerweiterung. Die unsigned-Kontrollen bestätigen diese andere
  Operation ausdrücklich nicht. Aussagen zur Verarbeitung negativer
  Akkumulationswerte bleiben insoweit unbestätigt.
- Parallelmitglieder, Repeat-/Delay-Slot-Semantik, Tabellen und Codegrenzen
  sind nicht allgemein validiert. Ein erfolgreich decodierbares Halbwort
  kann auch mitten in einem längeren Befehl liegen.

Die Privatkopie kompiliert, mit weiterhin dokumentierten Warnungen zu
Delay-Slots, 50 NOP-Konstruktoren und einer unnötigen Erweiterung/Kürzung.
Die bereits ausgeschlossene Repeat-Familie bleibt ausgeschlossen. Kein
allgemein reparierter Jieli-Decoder und keine Firmwareemulation.

## 5. Prüfung und nächster Schritt

**37 lokale Forschungstests bestanden**, davon zwölf neue Transporttests.
Sie prüfen unter anderem mutierte/trunkierte Aufrufe, reservierte Felder,
beide Bitbedingungen, negative Sprungweiten, Adressierungsreihenfolge,
Deskriptorgrenzen und die Trennung von DG-Sendepfad und Sensorinhalt.
Die bestehenden synthetischen Sensor-/Parser-Gegenproben bleiben enthalten.
Dies ist keine neue Hardwareabnahme oder vollständige Treibertestsuite.

Der begrenzte Controller-Abschlusslauf: 24 Fenster, **324 Decode-Datensätze**,
keine Decodeabbrüche. Der getrennte DG-Abschlusslauf: sieben Fenster,
**65 Datensätze**, plus ein gezieltes Kontrollflussfenster mit 15 Datensätzen.
Die explorativen Fehlstarts, unbekannten Positionen und überlaufenen Tabellen
sind im privaten Audit festgehalten und aus den Belegen ausgeschlossen.
Auch zwei scheinbar decodierbare Fensterstarts mitten in CALLs wurden
verworfen und anhand korrekter Grenzen nachgeprüft.

Isolation und unveränderte Inputs wurden bei allen Analyseaufrufen geprüft;
die Originalhashes der vier verwendeten Apps stimmen weiterhin. Private
Feldleser, Tests, Decoderkopie und Rohresultate verbleiben unter
`build/jieli-validation-20261018/`; aktueller Auditindex
`anchors/transport-review-final.json`. Keine Firmware, SDK-Codekopien oder
Disassemblies in Git. Der öffentliche Commit enthält nur Dokumentation.

Der nächste begrenzte Offline-Schritt ist der **Writer von DG `D+0xa24`
und sein Funk-/Pakettypbezug**, anschließend der Abgleich mit dem
Controller-Sendepfad und den bekannten Sensoroffsets. Parallel offene
Halfword-/Vorzeichenformen und spätere Sensor-/Offsetschreiber absichern.
`0,07 Grad/s je ST-Sensorzählwert` bleibt ein bedingter Kandidat; ein
bestätigter Faktor der tatsächlich empfangenen USB-Daten folgt daraus
noch nicht. Kalibrierung und produktiver Treiber bleiben unverändert.
