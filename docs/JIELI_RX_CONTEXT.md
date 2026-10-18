# Jieli: bedingte Empfangsauswahl und unterer Pakethelfer

Stand: 18. Oktober 2026. Fortsetzung der
[Sendepfadauswahl](JIELI_LINK_ROUTING.md). Nur statische Analyse privater
Dateikopien, keine Ausführung oder Emulation der Firmware, kein Netzwerk,
Hardwarezugriff oder Eingriff in den Treiber. Gyrokalibrierung bleibt pausiert.

## Ergebnis

Die zuvor fehlenden Bedingungen der DG144-Callback-Auswahl stammen aus
einem **Fehler unseres statischen Exporthelfers**. Mit adressbezogener
Kontextübernahme und Gegenprüfung am gespeicherten offiziellen Jieli-Listing
lassen sich die beiden Zuweisungen unterscheiden:

| Zustand am betrachteten DG144-Einstieg | Callback-Dateioffset |
| --- | --- |
| Byte bei Eingangsregister `r14+9` **ungleich 1** | `0x1d81c` |
| Dasselbe Byte **gleich 1** | `0x1c8fe` |

Das ist eine statische Auswahlregel, kein beobachteter Laufzeitzustand.
Die Zeiger werden nicht nacheinander wirksam überschrieben. Beide Kandidaten
können den bereits untersuchten Deskriptorhandler `0x1c850` erreichen; der
zweite abhängig von weiteren Flags.

Der vorgeschaltete Helfer `0xfe42` arbeitet mit einem gemeinsamen
als Hardware-Registerblock interpretierten Adressbereich, Paketzeigern und
variabler Länge. Ein zweiter
Aufrufer hängt vier Ergebnisbytes an. Das stützt **paketweise
Transportverarbeitung**, nicht eine hier neu gefundene Gyro-Skalierung.
Die Kombination ist mit einem kryptografischen Paketverfahren wie AES-CCM
vereinbar, aber **Algorithmus, Registeridentität und erfolgreiche
Authentifizierung sind nicht unabhängig belegt**. Eine byteidentische
Durchleitung durch diesen Helfer wird ausdrücklich nicht behauptet.

## 1. Woher kamen die Decodergrenzen?

REA, Ghidra, die private Pi32v2-Prozessorbeschreibung und unser Exporthelfer
sind unterschiedliche Komponenten. Die installierte REA-Version ist nicht
die Ursache aller beobachteten Abweichungen. Es wurde nichts nachinstalliert.

| Befund | Nachweis und Behandlung |
| --- | --- |
| Fehlende bedingte Wrapper | Unser Helfer benutzte `ProcessorContextImpl`. Im lokal vorhandenen Ghidra-12.1.4-Quellcode speichert `ContextCache.setContext` zukünftige Werte nur für `DisassemblerContext`. Der bisherige Kommentar „parse commits carried“ war dafür unzutreffend. |
| Korrigierte Kontextübernahme | Privater Helfer verwendet jetzt `ProgramContextImpl` und `DisassemblerContextImpl`, expliziten Startzustand und adressbezogenen Flow. Unveränderte Decoderbeschreibung für bedingte Blöcke. |
| Verkürzte Stack-Abstände | Die vorhandene E9D4-Beschreibung ließ mittlere Offsetbits weg. 13 unabhängige SDK-Beispiele bestätigen die geprüften Load-/Store-Operanden; zwei unterscheiden die alte Formel von der Korrektur. Privat korrigiert. |
| Bewusst ausgelassene Befehle | Die Wiederholungs-Befehlsfamilie wurde wegen eines nicht kompatiblen variablen Delay-Slots ausgelassen. Das ist eine dokumentierte Einschränkung des privaten Decoders, keine Erklärung für alle anderen Fehler. |
| Nicht erkannte Negativ-Konstante | SDK `0x1103ec` und `0x11042a` verwenden eine bedingte Form mit `-1`, die schon von der unveränderten Bedingungsbeschreibung nicht abgedeckt wird. Decodeabbruch bleibt sichtbar; keine geratenen Ersatzoperationen. |
| Bedingter Parallelblock | SDK `0x110126` zeigt weiterhin eine Abweichung: Der Sprung bei `0x110130` gehört laut Listing zur Bedingung, der Export lässt dort den Wrapper weg. Nicht durch diesen Pass repariert oder allgemein freigegeben. |

Die alten Ergebnisse bleiben als historische Ausgaben erhalten. Ihre
Kontextangabe beweist keine vollständige Bedingungsübernahme; Schlussfolgerungen
über abhängige Blöcke benötigen eine erneute gezielte Prüfung. Unbedingte
Einzelbefehls-Kontrollen werden davon getrennt behandelt. Der Empfangsentscheid
oben enthält zwei einfache 48-Bit-Literale, keinen Parallelblock.

Referenzen bleiben die lokal gespeicherten Versionen: Quarkslab-Beschreiber
`e1bd0707874b77b759401555d24839ad43af1267`, offizielles Jieli-Tech-ROM-Listing
`fdc018de81629e21e594d677cf05f87d288be0f0` und Ghidra 12.1.4. Es wurden keine
Quellen neu heruntergeladen und keine fremden Quellen in diesen Commit übernommen.

## 2. Auswahl vor dem Empfangshelfer

Alle folgenden Positionen sind **Dateioffsets in DG144**; RAM-Adressen und
Textzeiger behalten die getrennten Modelle der Vorgängerberichte.

- `0x1c7a0`: Zustandsbyte aus `r14+9` laden.
- `0x1c7a6`: bedingter Block für **ungleich 1**. Die inverse P-Code-Prüfung
  auf Gleichheit überspringt die Setzung des Wahrheitszustands; sie darf
  nicht als Gleichheitsbedingung des Quellblocks gelesen werden.
- `0x1c7aa`: Then-Zuweisung des Textzeigers auf `0x1d81c`.
- `0x1c7b0`: Else-Zuweisung des Textzeigers auf `0x1c8fe`.
- `0x1c7b6`: Aufruf `0x1af88` außerhalb beider Zuweisungsbedingungen.
- Der Helfer bewahrt das Callback-Argument in `r8`; Aufruf bei `0x1b04e`.

Die Auswahl ist mit den getesteten einfachen SDK-Blöcken konsistent.
Bedeutung und Schreiber des Zustandsbytes sowie dessen tatsächlicher Wert
im GameSir-Betrieb sind weiterhin offen.

## 3. Was `0xfe42` vor dem Callback macht

Der Empfangshelfer `0x1af88` entnimmt einen Deskriptor `Q` über `0xf46e`.
Ohne Deskriptor endet dieser Durchlauf. Wenn Kontextbyte `+0x1a0` oder
Deskriptorlänge `Q+0x0a` null sind, überspringt er den untersuchten
Verarbeitungszweig und geht zum Callback. Sonst:

1. Aus Kontextzähler, einem weiteren Byte und acht Kontextbytes wird ein
   13-Byte-Feld vorbereitet. Aus Deskriptorbits entsteht ein separates Byte.
2. `0x1b010`–`0x1b018` zieht vier von der Paketlänge ab und speichert die
   Byte-Länge zurück. Datenquelle ist `Q+0x14`.
3. Aufruf `0xfe42` mit Kontextblock `+0x1b4`, dem 13-Byte-Feld, dem einzelnen
   Byte sowie Paketpuffern, Länge, Ergebnisbereich und weiteren Parametern.
4. `0x1b046` kopiert die verarbeiteten Daten aus dem temporären Bereich
   zurück nach `Q+0x14`; danach wird der ausgewählte Callback aufgerufen.

Der Helfer selbst weist folgende Struktur auf:

| DG144-Abschnitt | Beobachtete Operationen |
| --- | --- |
| `0xfe50`–`0xfeae` | Registerbasis `0x1e4300`; 16 Bytes des ersten Eingabeblocks werden als vier zusammengesetzte Wörter an Offset `+8` geschrieben. |
| `0xfe56`, `0xfee2` | Längen-/Parameterwerte an Registeroffsets `+0x2c` und `+0x30`. |
| `0xfee4`–`0xff2a` | 13 Bytes des zweiten Eingabeblocks an Offset `+0x1c`; keine Interpretation als IMU-Achsen. |
| `0xff2c`–`0xff30` | Ein Byte des dritten Eingangs an Offset `+0x20`. |
| `0xff32`–`0xff48` | Auswahl der Pufferzuordnung und der Kontrollbits `0x40000` bzw. `0x10000`; Zeiger an `+0x24/+0x28`. |
| `0xff4c`–`0xff52` | Warten auf ein Statusbit und anschließend weiterer Kontrollzugriff. |
| `0xff56`–`0xffb0` | 16 Ergebnisbytes aus Registeroffsets `+0x34..+0x40` in einen gesonderten Ergebnisbereich übertragen. |

Die Zuordnung als Hardwareblock ist eine Interpretation der Registerfolge;
eine unabhängige Definition für `0x1e4300` fehlt noch. Die externen Helfer
mit Decode-Zielen `0x201384`/`0x2013a0` am Ein-/Austritt und `0x20008c`
sind hier nicht vollständig aufgelöst. Kein Vollbeweis aller Seiteneffekte
oder der gesamten ABI allein aus dieser Funktion.

Die zuvor fehlerhaften Stack-Loads bei `0xfecc`/`0xfed6` sind nun
`sp+0x34`/`sp+0x20`, nicht `sp+4`/`sp+0`. Zusammen mit dem 32-Byte-Prolog
ordnen sie den Auswahlparameter und den Ausgabepuffer den Caller-Argumenten
zu. Ohne diese Korrektur wäre die Pufferzuordnung falsch.

Ein zweiter direkter Aufruf liegt bei `0x1a29c`. Dieser verwendet den anderen
Auswahlparameter; nach dem Nutzdatenkopieren hängt `0x1a2c6` vier Bytes aus
dem Ergebnisbereich an und erhöht die Länge um vier. Gegenüber dem
Empfangszweig mit Längenabzug ist das ein konkretes Indiz für ergänzende
Transportbearbeitung. Die vollständige Erreichbarkeit dieses zweiten
Aufrufers und ein identischer Controller-Gegenpfad sind noch nicht bewiesen.

**Hypothese:** 16-Byte-Block, 13-Byte-Feld, einzelne zusätzliche Headerdaten,
variable Nutzlast und vier Trailerbytes passen zu Schlüssel, Nonce, AAD und
MIC eines CCM-artigen Verfahrens. Die neutrale Register-/Pufferbeschreibung
oben ist der belegte Befund. Es fehlen eine unabhängige Registerdefinition
und die vollständige Fehler-/Authentifizierungsbehandlung. Daraus folgt
weder ein nachgewiesener Sicherheitsfehler noch ein bestätigter Algorithmus.

## 4. Prüfung und verbleibende Grenze

- **81 Forschungstests bestanden**, elf neu: Kontextgrenzen, Then/Else,
  falsche Skip-Ziele, mutierte Callback-Zeiger, fehlende Guards und
  Stack-Abstände. Negative Kontrollen reproduzieren die alten Fehler.
- **140 SDK-Einzelbefehls-Kontrollen**: die bisherigen 127 bestehen auch
  mit dem neuen Helfer/Decoder; 13 zusätzliche Stack-Beispiele, zwei davon
  mit gegenüber der alten Formel unterscheidenden Abständen.
- Fünf einfache SDK-Bedingungsblöcke bestehen die Wrapper-Prüfung,
  einschließlich Return, 48-Bit-Literal und Else. Ein zusätzlicher
  Parallelblock bleibt ausdrücklich als bekannte Abweichung erfasst.
- Abschließende DG-Fenster: sieben mit 285 Datensätzen plus ein begrenztes
  Trailerfenster mit neun Datensätzen; kein Decodeabbruch darin.
  Explorative Fortsetzungen hinter Funktionsenden werden nicht ausgewertet.
- Vier App-Hashes und Isolation/Unverändertheit bestätigt. Privater
  Auditindex: `build/jieli-validation-20261018/anchors/context/review.json`.
  Eigene Prüfhelfer, Firmware, SDK-Ausschnitte und fremder Decoder bleiben
  privat. Der öffentliche Commit enthält ausschließlich Dokumentation.

**Entscheidung nach diesem Analysepass (18. Oktober): Funkanalyse
zurückgestellt.** Registerblock, Transportparameter, Deskriptorursprung und
Schreiber von Empfangsfreigabe/Zustandsbyte bleiben dokumentierte offene
Fragen. Die belegten oberen Kopien bis zum `A2`-/USB-Pfad bleiben von dieser
unteren Bearbeitung getrennt. Reale IMU-Pakete wurden bereits empfangen;
welche internen Firmwarezweige dabei aktiv waren, ist nicht nachgewiesen.
Die vollständige Funkrekonstruktion ist keine Voraussetzung für eine spätere
Referenzkalibrierung der USB-Werte.

**0,07 °/s pro USB-Rohwert ist ein unbestätigter Testkandidat**, abgeleitet
aus der ST-Arbeitshypothese und der Annahme unveränderter Verstärkung bis USB.
[Herkunft und Prüfgrenzen](PROTOCOL.md#unbestätigter-gyro-testkandidat).
Keine automatische Übernahme in den Treiber. Letzte wirksame
Sensorkonfiguration und physische Kalibrierung bleiben offen;
**Gyrokalibrierung bleibt pausiert.**
