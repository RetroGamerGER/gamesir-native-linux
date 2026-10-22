# Stickkalibrierung: Kopieroperation und Speicherabschluss

Stand: 21. Oktober 2026. Offline-Fortsetzung der
[Start-/Finish-/Exit-Analyse](NEXUS_STICK_FIRMWARE.md).
Untersucht wurde die unveränderte Controller-Firmware DV209; ausgewählte
Abschnitte wurden mit DV515 und DV608 verglichen. Keine Ausführung oder
Emulation von Firmware, keine Hersteller-App, Netzwerk- oder Hardwarezugriffe.
Treiber und installiertes System bleiben unverändert; präzise Gyrokalibrierung
bleibt pausiert. [Maschinenlesbare Belege](evidence/NEXUS_STICK_STORAGE_20261021.json).

**Fortsetzung und präzisierte Nachbauanforderung:**
[Statusbericht, Laden gespeicherter Werte und Firmware-Vertrag](NEXUS_STICK_READBACK.md).
Finish stößt die geräteseitige Speicherung an. Eine zusätzliche Host-Quittung
ist dafür nicht zwingend; fehlende Quittierung allein ist kein Blocker für den
Nachbau. Die folgenden Speichergrenzen bleiben Befunde, keine nachgewiesenen
Hardwarefehler. Die frühere pauschale Forderung nach Quittung/Rücklesevergleich
ist durch die differenzierte Empfehlung der Fortsetzung ersetzt.

## Ergebnis

Die frühere Bezeichnung von **EE53 als Postincrement-Store wird zurückgenommen**.
Die vier untersuchten Befehle passen stattdessen zu einer Byte-Ablage mit
**festem negativem Abstand zum Basisregister**. Die separate Zeigererhöhung in
der Schleife und beide Wiederherstellungsroutinen stützen diese Deutung. Damit
lässt sich der Aufbau beider 30-Byte-Sicherungen schlüssig erklären. Ein
unabhängiges Hersteller-Beispiel exakt für EE53 fehlt in den lokal vorhandenen
Referenzen weiterhin; diese interne Gegenprüfung ist kein vollständiger ISA-Beweis.

Der Speicherauftrag ist jetzt bis zum unteren Byte-Transfer und zur internen
Meldung **`eeprom write over`** verfolgt. Diese Meldung ist **kein ausreichender
Nachweis dauerhaft korrekt gespeicherter Kalibrierwerte**: Normales Ende und
bestimmte Status-Abweisungszweige münden in dasselbe Bus-Fertigflag. Außerdem
zählt der obere Auftrag bereits beim Anstoßen eines Abschnitts weiter.

Das belegt eine Grenze der beobachteten Bestätigungskette, keinen auf Hardware
reproduzierten Fehler und keine vollständige Aussage über alle Firmwarepfade.
Ein sicherer Linux-Kalibrierungsdialog braucht weiterhin einen belastbaren
Erfolgs-/Fehlernachweis oder einen geeigneten Rücklesevergleich.

## 1. Quellen und Grenzen der Methode

Alle folgenden Adressen sind DV209-Dateioffsets, sofern nicht anders bezeichnet.
`B = 0xf140` ist die RAM-Basis; der RAM-Suffix beginnt bei Datei `0x4f718` und
läuft unter Basis null. Die bereits geprüften getrennten Adressmodelle für
Flash, RAM-Suffix und Textzeiger bleiben erhalten.

Der abschließende, netzwerk- und geräteisolierte Ghidra-Lauf mit unverändertem
Decoder umfasst **28 begrenzte Bereiche / 745 Instruktionsdatensätze**, ohne
Dekodierabbruch in diesen Bereichen. EE53 wird darin ausdrücklich ausgespart
und separat als Operandenhypothese untersucht. Es wurde kein vermeintlicher
ISA-Beleg durch das Einbauen dieser Hypothese in den Decoder erzeugt.

Explorative Läufe stießen auch auf unbekannte Befehle, Tabellen und ungeeignete
Startgrenzen; diese sind keine durchgehenden Codebelege. Überlappende
Parallel-Darstellungen werden nicht als unabhängige Befehle ausgeführt oder
doppelt fortgeschrieben. Bekannte Grenzen bei bedingten Parallelblöcken und
anderen Operandenformen bleiben bestehen. Insbesondere wird aus dem Timerzweig
keine exakt nachgewiesene Wartezeit in Millisekunden abgeleitet.

Die lokale Primärreferenz ist weiterhin Jieli-Techs `fw-AC63_BT_SDK`, Commit
`fdc018de81629e21e594d677cf05f87d288be0f0`, Datei `cpu/br23/tools/rom.lst`;
ihr Hash steht im vorherigen [Decoderbericht](JIELI_WIRELESS_DATAFLOW.md).
Keine Online-Abfrage erfolgte. Herstellerdateien und vollständige
Disassemblierungen bleiben außerhalb des öffentlichen Repositorys.

## 2. EE53: negativer Abstand statt automatischer Zeigeränderung

Die bereits anhand von 44 offiziellen Beispielen geprüfte EE52-Form speichert
ein Byte bei `Basis + positiver Abstand`. Für EE53 ergibt die benachbarte
Kodierung folgende **strukturell gestützte Deutung**:

- Quellregister: oberes Nibble des zweiten Halfwords, alle vier Bits.
- Basisregister: Bits 4–7 desselben Halfwords.
- Abstand: zusammengesetztes 8-Bit-Feld **minus 256**; das zusätzliche gesetzte
  Bit im ersten Halfword entspricht dem negativen Teil eines 9-Bit-Abstands.
- Byte-Ablage an dieser Adresse; keine Änderung des Basisregisters durch EE53.

| Datei | Quelle / Basis | Kandidat für Abstand | Erste Zieladresse relativ zu B |
|---|---|---:|---|
| `0x18a2` | r4 / r1 | −70 | `0x1b4a`, linkes Record-Byte 12 |
| `0x18a6` | r3 / r1 | −69 | `0x1b4b`, linkes Record-Byte 13 |
| `0x1924` | r4 / r1 | −143 | `0x1b69`, rechtes Record-Byte 12 |
| `0x1928` | r3 / r1 | −142 | `0x1b6a`, rechtes Record-Byte 13 |

Links startet r1 bei `B+0x1b90`, rechts bei `B+0x1bf8`. Aus einem Halfword wird
jeweils erst das hohe, dann das niedrige Byte abgelegt. Die **eigenständigen**
Befehle bei `0x18ac` beziehungsweise `0x192e` erhöhen r1 anschließend um zwei;
der Zähler begrenzt die Schleife auf acht Werte.

Mit dieser Deutung füllt jede Schleife genau die Record-Bytes 12–27. Die ersten
zwölf Bytes enthalten sechs weitere Halfwords; die letzten beiden sind die
Marker `a6 6a`. Die Restore-Routinen lesen dieselben Paare wieder zurück in
die jeweiligen Tabellen. Auch rechts passt dies, obwohl −143/−142 nicht in
einen vorzeichenbehafteten 8-Bit-Abstand passen. Eine bloße Signed8-Deutung
würde dort an der falschen Adresse landen. Postincrement oder ausschließlich
positive Abstände passen ebenfalls nicht zur Record-Geometrie.

**Beweisstärke:** Vier konkrete Operandenstellen, beide Schleifen, beide
Rückwege und bytegleiche Packbereiche in drei Firmwaredateien stützen das
Ergebnis. Die lokale SDK-Liste enthält aber **null EE53-Beispiele**. Ihre 44
EE52- und zwei EE59-Beispiele stützen verwandte Felder, nicht die komplette
EE53-Semantik. Der gemeinsame Decoder wurde deshalb nicht geändert. Eine
vollständige ISA-Freigabe oder garantierte Rücknahme aller Gerätezustände folgt
daraus nicht.

## 3. Vom Auftrag zum Byte-Transfer

Die bisherige Kette bleibt erhalten: Finish setzt Anforderungen; die spätere
Finalisierung packt die Ergebnisse und reiht zwei getrennte 30-Byte-Aufträge
für die logischen Adressen `0x1700` und `0x1720` ein. Diese Adressen sind keine
Linux-Schreibanleitung oder freigegebene Flashbereiche.

Der ergänzte Pfad ist:

1. Der Queue-Verbraucher liest Operation 1 bei `0x169e4…0x169fa`, setzt r0 auf
   1 und springt direkt zum gemeinsamen Aufruf `0x16a66 → 0x11500`.
   Der dazwischen liegende r0=0-Zweig ist **Lesen**, nicht die Fortsetzung des
   Schreibzweigs. Lineares Weiterlesen würde diese Unterscheidung verlieren.
2. Der asynchrone Zustand enthält Operation bei `0xf0e0`, logische Adresse bei
   `0xf0e4`, Länge bei `0xf0e8`, Fortschritt bei `0xf0ec` und den Datenzeiger
   in `word[B+0x820]`; `byte[B+0x81c]` zeigt einen laufenden Auftrag.
3. Der Schreibzweig `0x109a4…0x109e2` begrenzt einen Abschnitt auf den Rest bis
   zur nächsten 32-Byte-Grenze beziehungsweise die verbleibende Länge. Für die
   beiden ausgerichteten Stick-Adressen passt jeweils ein 30-Byte-Auftrag in
   einen Abschnitt. Daraus folgt keine atomare gemeinsame Speicherung.
4. `0x109d0 → 0x8dc0` bereitet den unteren Transfer vor: Quellzeiger bei
   `B+0x814`, Adresse bei `0xf0c8`, Abschnittslänge bei `0xf0c0`, Byteindex bei
   `0xf0d4`, Unterzustand bei `0xf0da`. `0xf0dc = 5` wählt den Schreibpfad.
   `B+0x528` wird gelöscht; der Registerblock `0x1e2400` erhält zunächst `0xa0`.
5. **Schon nach dem Anstoßen** erhöht der obere Pfad `0xf0ec` um die gesamte
   Abschnittslänge und setzt `B+0x824`. Der Zähler ist folglich nicht allein
   die Zahl nachweislich dauerhaft gespeicherter Bytes.
6. `0x72dc…0x72e6` übergibt den RAM-Codezeiger `0x8f48` mit den Parametern
   `0x16` und 3 an `0x44ff4`. Dieser Zeiger entspricht Datei `0x58660`.
   Die Initialisierung samt Interrupt-Prolog und Registerzugriffen verbindet
   den bisher nur vermuteten unteren Handler strukturell mit dem Speicherpfad.
   Eine tatsächliche Ausführung dieser Registrierung wurde nicht beobachtet.
7. Der Handler wählt bei `0x586ba` den Modus 5, verarbeitet Adress- und
   Datenzustände und legt Bytes aus `B+0x814` in das Datenregister bei
   `0x1e2404` (`0x587c6`). Für weitere Bytes prüft er Länge, Index und den
   niedrigen Statusbyte-Wert des Registerblocks.

Zwischen Transfer und nächstem oberen Verarbeitungsschritt existiert zusätzlich
ein Wartezustand über `0xf0f0`/`0xf0f4` (`0x108c0…0x108dc`, `0x52d36…0x52d5c`).
Eine angenommene Zeitbasis oder ein erfolgreicher EEPROM-Schreibzyklus darf
nicht aus dem Timer allein abgeleitet werden.

## 4. Was Abschluss und Fehler tatsächlich melden

| Stelle | Statisch belegter Befund | Aussagegrenze |
|---|---|---|
| `0x58748 → 0x5882e` | Byteindex erreicht die Endbedingung; STOP-Helfer `0x10198`, Verzögerungsaufruf, danach gemeinsamer Abschluss | Kein Datenvergleich gegen EEPROM-Inhalt |
| `0x58752 → 0x5887c` | Gesetztes Bit 7 des gelesenen Statusbytes führt vor einem weiteren Datenbyte zum STOP-Pfad | ACK-/NACK-Bedeutung des Registers nicht unabhängig aus einem passenden Hardwarehandbuch bestätigt |
| `0x58880…0x5888a` | Beide Pfade setzen `B+0x528 = 1` und rufen `0x10348` auf | Gemeinsames Bus-Fertigflag, kein unterschiedlicher Auftrags-Ergebniscode an dieser Stelle |
| `0x10348` | Übergabe an den Ereignishelfer mit Kennung `0x400017` | Interne Benachrichtigung, kein belegtes USB-Erfolgspaket an Nexus |
| `0x10954…0x1098e` | Oberer Pfad verbraucht `B+0x824`, vergleicht Fortschritt mit Länge, löscht bei Gleichheit `B+0x81c` und ruft `0x1075e` | Zähler wurde bereits bei der Einreichung erhöht |
| `0x1075e…0x1078e` | Log `eeprom write over`; Queue-Besitzflag `B+0x534` löschen; optional `word[B+0xa60]` aufrufen | Im betrachteten Stickauftrag ist dieser Callback null |
| `0x1081e…0x10886` | Zeitüberschreitungs-/Reinitialisierungsweg mit `iic op time over time` und `hw i2c op over time re init %d` | Kein vollständig zugeordneter hostseitiger Fehlercode oder gesicherter Rückbau der Stickkalibrierung |

Im Datenzustand liegt die Längen-Endprüfung vor der Bit-7-Prüfung für das
nächste Byte. Auch deshalb darf man nicht behaupten, der gefundene Abschluss
beweise die Bestätigung jedes einzelnen Bytes. Ob das konkrete Register oder
andere Aufgaben zusätzliche Garantien liefern, bleibt separat zu klären.

Die untersuchten Zweige reichen aus, um **„Fertigflag = dauerhaft erfolgreich“
als unbewiesene Annahme auszuschließen**. Sie reichen nicht für die Behauptung,
dass Nexus oder ein realer Controller tatsächlich einen fehlgeschlagenen
Kalibriervorgang als erfolgreich anzeigt. Scheduler, andere Zustandswächter,
konkrete Registersemantik und die vollständige Host-Rückmeldung sind nicht
umfassend verifiziert.

Ein wichtiger Gegencheck: Ein **anderer** Firmwarepfad bei `0xb0c2…0xb152`
schreibt, liest über `0x87f2` zurück, vergleicht Bytes und erreicht bei Abweichung
`eeprom clean err!`. Die Firmware kennt also einen expliziten Vergleichspfad.
Dieser darf nicht ohne Aufrufnachweis auf die Kalibrierungs-Queue übertragen
werden. Im hier verfolgten normalen Stick-Speicherabschluss wurde ein solcher
Rücklesevergleich nicht gefunden.

## 5. Folgen für Speichern, Abbrechen und den Linux-Nachbau

Die frühere zeitliche Abbruchgrenze gilt weiter: Exit restauriert RAM-Werte
für noch aktive Kalibrierungen. Nach Finalisierung ist die alte RAM-Sicherung
bereits mit dem neuen Datensatz überschrieben; ein eingereihter Speicherauftrag
wird durch den untersuchten Exit-Zweig nicht entfernt.

Die EE53-Gegenprüfung stärkt den vorgesehenen Tabellen-Rückweg **vor** dieser
Grenze. Sie macht Exit nicht zu einem Rollback nach einer bereits begonnenen
Speicherung. Auch ein bloßes Timeout auf dem PC darf nicht als erfolgreiche
Rücknahme angezeigt werden.

Für die spätere Implementierung bleiben erforderlich:

- Start, Ergebnisübernahme, Speicherauftrag und verifizierter Abschluss als
  unterschiedliche Zustände behandeln; Geräteinstanz festhalten.
- Keine zweite Sitzung beginnen, solange ein vorheriger Auftrag ungeklärt ist;
  die Queue hält weiterhin einen Datenzeiger statt einer unveränderlichen Kopie.
- Einen tatsächlichen Host-Erfolgs-/Fehlerpfad oder einen geeigneten lesenden
  Vergleich belegen. Die internen Logs sind dafür allein ungeeignet.
- Abbruch nach begonnener Speicherung als ungeklärten Zustand behandeln, bis
  Rücklese- und Wiederherstellungsverhalten feststehen.
- ISA-Gegenbeleg für EE53, genaue Busstatus-Semantik und Transport-/Modellzuordnung
  ergänzen, bevor ein schreibender Test geplant wird.

Firmware-Updates sind ein separates, weiterhin offenes Vorhaben. Die Analyse
der Kalibrierdatensätze beweist weder einen sicheren Firmware-Updater noch
Wiederherstellung nach Stromverlust.

## 6. Prüfungen

- Drei Firmware-Hashes unverändert; 41 ausgewählte P-Code-/Byteanker und
  16 Aufrufkanten geprüft, darunter sechs mit RAM-Suffix-Adressumrechnung.
- Vier EE53-Operandenstellen und beide 16-Byte-Tabellenlayouts gegen ihre
  Rückwege geprüft; Hi-/Low-Byte-Zusammensetzung über den gesamten 16-Bit-
  Wertebereich mathematisch gegengeprüft. Keine MCU-Emulation.
- 44 EE52- und zwei EE59-SDK-Kontrollen; ausdrücklich **null** exakte EE53-
  Herstellerbeispiele. 13 Mutations-/Ablehnungskontrollen unterscheiden falsche
  Operanden, Aufrufziele sowie fremde/verkürzte Befehlsformen.
- Vier ausgewählte Bereiche sind in DV209, DV515 und DV608 bytegleich, teilweise
  versetzt. Das beweist keine vollständige Editions- oder Laufzeitgleichheit.
- Die 13 bestehenden Nexus-Dialog-Modelltests und der Test des reproduzierbaren
  Quellenarchivs bestehen. Lokale Links, private Kennungen und Projektprüfsummen
  wurden kontrolliert. Kein vollständiger Treiber-Regressionslauf erforderlich:
  Runtime-Quellen und Systemzustand wurden nicht geändert.

Dokumentation und anonymisierte Belege werden lokal committed; kein Push,
kein Paketupdate, keine neue Hardwaremessung und kein Wartungsbefehl.
