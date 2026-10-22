# Stickkalibrierung: Abschalten, Aufwachen und alte Befehle

Stand: 22. Oktober 2026. Offline-Fortsetzung der
[Reconnect-Analyse](NEXUS_STICK_RECONNECT_ROUTES.md).
[Fundstellen und Prüfbeleg](evidence/NEXUS_STICK_WAKE_RETENTION_20261022.json).

## Ergebnis

**Der untersuchte Schlafauftrag führt in einen Abschaltpfad mit Reset-Rückfall.**
Der nun vollständig abgegrenzte äußere RAM-Abschnitt hat keinen normalen
Rücksprung in den Kalibrierdialog oder die Befehlsverarbeitung. Falls die
Ausführung nach den Abschaltanforderungen weiterläuft, wiederholt er die
Abschaltsequenz und fordert ab einer Zählerschwelle zusätzlich einen Reset an.
Das ist keine Endlosschleife zum erneuten Senden von Start, Finish oder Exit.

**Welche physischen RAM-Bänke beim Aufwachen erhalten bleiben, ist damit noch
nicht vollständig bestimmt.** Belegt ist die Wirkung eines abgeschlossenen
normalen App-Starts: Er löscht den zuletzt angenommenen Sequenzwert und die
untersuchten Kalibrierflags, Sicherungen und Arbeitsbereiche im Controller.
Ob jeder reale Aufwachfall diesen Startcode durchläuft, bleibt ohne vollständige
Boot-ROM-/Chip-Zuordnung offen. Ein Controller-Neustart löscht kein Dongle-RAM.

Eine weitere Eingrenzung betrifft Finish: Der Stickzweig setzt seine
Abschlussanforderungen nur für bereits gesetzte Bereitschaftsbits. Sind diese
nach einem vollständigen Start noch null, setzt ein allein verspätet empfangener
Finish keine neue Stick-Abschlussanforderung. Das ist ein Zustandsfilter,
keine nachgewiesene Stornierung aller alten Transportbefehle.

## Quellen und Arbeitsumfang

Unveränderte lokale Firmware **DV209** und die bereits ausgewertete
Dongle-Firmware **DG144**, vorhandener isolierter statischer Decoder und
bereits gespeicherte offizielle Jieli-Referenzen. Quellenherkunft und Hashes
stehen im Prüfbeleg und im [vorherigen Resetbericht](NEXUS_STICK_RESET_LIFETIME.md).
Herstellerdateien und vollständige Disassemblierungen bleiben außerhalb von Git.

Codeadressen sind Dateioffsets. Ausdrücklich bezeichnete RAM-Adressen verwenden
für DV209 die bereits belegte Suffixabbildung: Datei `0x4f718` entspricht RAM
null. `B = 0xf140` ist die Controller-Zustandsbasis.

Keine Hersteller-App-/Firmwareausführung oder Emulation, kein Netzwerk-, SSH-,
USB-, Funk- oder Input-Zugriff. Kein installierter Treiber, Decoder oder
Firmwareinhalt wurde verändert. Beide Installationen und die zurückgestellte
Treiberdiagnose bleiben erhalten; präzise Gyrokalibrierung bleibt pausiert.

## 1. Was hinter dem Schlaf-Einstieg liegt

Der zuvor aufgelöste Weg `0x40000c → 0x9694 → 0x987c` erreicht **RAM `0xc7a`,
Datei `0x50392`**. Der äußere Abschnitt bis einschließlich `0x50620` ist jetzt
lückenlos abgegrenzt; die nachfolgende Funktion beginnt bei `0x50622`.

| Abschnitt | Nachverfolgte Wirkung |
|---|---|
| `0x50392 → 0x9568` | Abschaltvorbereitung mit Peripherie-/P33-Aufrufen; vorhandene Meldung „Enter Power off(Soft)“ passt zum Code, ist allein aber kein Beweis |
| `0x9580…0x958c` | Optionaler indirekter Aufruf über das Wort an `0x23db0`; dessen vollständige Ziel-/Schreiberzuordnung bleibt offen |
| `0x50396…0x503a8` | Bytezähler an `0xeb39` wird auf null gesetzt; danach P33-Vorbereitung |
| `0x50530…0x50600` | Peripherie-/Taktfolge und Abschaltanforderungen; keine direkte Verteilung eines Kalibrierbefehls in diesem Abschnitt |
| `0x50604…0x50614` | Bytezähler erhöhen; bei aktualisiertem Wert kleiner `0x65` zurück nach `0x50530` |
| `0x50618…0x5061c` | Andernfalls Register `0xa0`, Maske `0x10` an P33-OR-Helfer RAM `0xab6` übergeben: Resetanforderung |
| `0x50620` | Auch nach Rückkehr dieses Helfers zurück nach `0x50530` |

Die Bedeutung der Resetanforderung ist durch die bekannte P33-Semantik und
den unabhängigen offiziellen `chip_reset`-Beleg gestützt. 17 Nicht-Sprungbefehle
des OR-Helfers stimmen bytegenau mit dem benannten offiziellen Helfer überein;
Aufrufziele sind separat geprüft. **Eine angeforderte Abschaltung oder ein
Reset ist kein ausgeführter Hardwaretest ihres Erfolgs.**

`0x65` bedeutet hier 101 Zählerstände, keine belegte Anzahl Millisekunden.
Der Zähler ist acht Bit breit; ein nicht wirksamer Reset könnte daher auch
einen Überlauf zulassen. Daraus folgt keine Wiederholung von Kalibrierbefehlen.

Der Aufruf bei `0x50540` erreicht den bekannten ROM-`memset`-Stub mit Ziel
`0x1e2900` und Länge `0xf4`: nach dem vorangehenden Registeraufbau liegt das
Ziel im Peripherieadressbereich, nicht in den Kalibrier-Arbeitsbereichen.
Ein dortiger Löschaufruf ist kein pauschaler RAM-Reset oder Backup-Rückweg.
Auch das Literal `0x80a5` bei `0x5039e` bezeichnet hier ein nachfolgendes
P33-Helferargument, keinen belegten zweiten RAM-Löschzugriff an dieser Adresse.
Parallel ausgegebene Befehlsmitglieder werden nicht doppelt ausgeführt gezählt.

## 2. RAM-Lebensdauer: Was tatsächlich belegt ist

| Fall/Bereich | Belegte Aussage | Grenze |
|---|---|---|
| Vollständig durchlaufener normaler DV209-Start | `[0xda60, 0x240e8)` wird gelöscht; darin liegen `B+0x50`, Kalibrierflags `B+0x1b3a…0x1b3c`, Backups und Stick-Arbeitsbereiche | Kein Beweis, dass jeder Funk-Reconnect oder Aufwachfall diesen Start durchläuft |
| RAM-Code-Suffix `[0, 0xd1ec)` | Der normale Start kopiert das vorhandene Firmware-Suffix dorthin | Keine Aussage über physische Retention vor dem Kopieren |
| Vorinitialisierung bei `0x45cfa` | Unter anderem zwei Acht-Byte-Kopien aus übergebenen Bootdaten nach `0xda30` und `0xda40`, außerhalb des BSS-Löschbereichs | Kein belegtes Wiederherstellen alter Stick-Arbeitswerte; nicht alle übrigen RAM-Bereiche dadurch klassifiziert |
| Gespeicherte Kalibrierung | Wird durch den BSS-Löschlauf nicht gelöscht; der bereits untersuchte Rücklesepfad ist getrennt | Ein Neustart macht eine eventuell falsch gespeicherte Kalibrierung nicht automatisch richtig |
| Dongle bleibt versorgt | Controller-Reset löscht nicht dessen ausstehende Befehlsdaten | Ob eine konkrete Kopie über Verlust/Schlaf erhalten bleibt und später zugestellt wird, ist weiterhin nicht beobachtet |

Der vollständige physische Aufwachweg, Boot-ROM-Entscheidungen, mögliche
SRAM-Retentionsbänke und sämtliche indirekten Vorbereitungscallbacks sind nicht
abgedeckt. Die Familienreferenzen ersetzen kein exaktes Chip-Handbuch. Es wird
weder „alles bleibt erhalten“ noch „jeder Reconnect löscht alles“ behauptet.

## 3. Kann ein alter Finish nach dem Aufwachen noch wirken?

Der Sequenzvergleich bei `0xe244…0xe25c` bleibt der bereits belegte Vergleich
mit einem einzigen letzten Byte. Nach vollständigem Startup ist dieser Wert
null: null wird im untersuchten Pfad übersprungen, ein anderer Wert kann unter
den übrigen Paketbedingungen verteilt werden. Das ist noch keine Speicherung.

Der Stick-Finish-Zweig bei `0x2268…0x2290` liest zusätzlich `B+0x1b3b`:
Nur bei gesetztem Bit null beziehungsweise eins wird das passende
Anforderungsbit in `B+0x1b3c` gesetzt. Der spätere Finalisierer benötigt auch
den passenden aktiven Kalibrierzustand; siehe
[Firmwareablauf](NEXUS_STICK_FIRMWARE.md) und
[Speicherauftrag](NEXUS_STICK_STORAGE.md).

Damit gelten zwei getrennte Aussagen:

- **Nach vollständigem Neustart, solange die Bereitschaftsflags noch null
  sind:** Ein allein verspäteter Finish setzt in diesem Stickzweig keine neue
  Abschlussanforderung. Das belegt weder, dass er nie übertragen wird, noch
  eine globale Wirkungslosigkeit sämtlicher Kalibrierbefehle.
- **Bei erhaltenem Zustand oder während eines späteren, bereits bereiten
  Durchlaufs:** Ein verspäteter Befehl ist durch diesen Nullzustandsbeleg nicht
  ausgeschlossen. Ein tatsächlich verspäteter Finish mit Speicherung wurde
  bislang nicht beobachtet. Ein möglicherweise alter Start ist ebenfalls von
  einem Finish zu unterscheiden.

## 4. Praktische Konsequenz für die geplante Oberfläche

Eine fehlgeschlagene Kalibrierung, die der Nutzer neu beginnt, ist der
naheliegende Fehlerfall. Die ungünstigere plausible Folge wäre eine falsch
gespeicherte Kalibrierung: falsche Mittelpunkte oder Ausschläge auch nach einem
Neustart, bis erneut kalibriert wird. Ein solcher Zusammenhang mit Funkverlust
und erst recht ein dadurch verursachter Brick sind hier **nicht nachgewiesen**.
Diese Untersuchung rechtfertigt keine Behauptung einer garantierten
Schadensfreiheit, aber auch keine Gleichsetzung von Kalibrierung und Firmwareflash.

Der geplante Ablauf bleibt einfach: Start, beobachtete Bereitschaft, Finish
oder bewusstes Exit im bestehenden Durchlauf. Bei Verbindungsverlust endet
dieser UI-Durchlauf. Die Anwendung sendet keinen alten Finish automatisch nach
und beginnt eine neue Kalibrierung erst auf ausdrücklichen Nutzerwunsch.
Auch Start oder Exit werden nicht blind beim Reconnect nachgeholt. Ein Stopp
der Oberfläche storniert keinen bereits im Dongle angekommenen Auftrag.

Es wird **keine zusätzliche Speicherbestätigung erfunden**. Finish löst den
bereits nachverfolgten firmwareeigenen Abschluss-/Speicherweg unter dessen
Zustandsbedingungen aus. Die offenen physischen Aufwachdetails sind dokumentierte
Grenzen; sie werden nicht als bewiesener Fehler oder Grund für eine endlose
Fortsetzung derselben Suche behandelt. Diese Arbeit implementiert noch keinen
schreibenden Kalibrierungszugriff.

## Validierung

- 22 begrenzte Bereiche, 539 Datensätze, keine Fehler im finalen Decoderlauf;
  davon 218 Datensätze im lückenlos abgegrenzten äußeren Abschaltabschnitt.
- 171 Literal-, 179 kurze, 293 lange Transferformen und sechs unsigned
  Vergleichssprünge gegen das gespeicherte offizielle Listing geprüft.
- 106 konkrete Aufruf-/Sprungziele mit 106 veränderten Kontrolloperanden;
  zusätzlich zwei veränderte Operanden der Zählerschleife erkannt.
- 17 exakte P33-OR-Instruktionsbelege, sechs Kalibrier-/Sequenz-RAM-Intervalle
  und 18 begrenzte Nichtüberschneidungsprüfungen.
- 1.024 eigene Kombinationen aus Bereitschaftsmaske und Eingangssequenz als
  Konsistenzprüfung der beschriebenen Bedingungen; keine Firmwareemulation.
- 16 bestehende Offline-Tests des Nexus-Kalibrierungsablaufs bestanden.

Bekannte Decodergrenzen bleiben: NOT-/REP-Stellen verwenden die unabhängigen
Belege aus dem vorherigen Bericht; DV `0xe976` bleibt ausgeschlossen. Saubere
Dekodierung beweist nicht alle Befehlsformen oder alle indirekten Laufzeitpfade.
Kein realer Aufwach-, Wiederverbindungs- oder Kalibrierversuch wurde ausgeführt.
