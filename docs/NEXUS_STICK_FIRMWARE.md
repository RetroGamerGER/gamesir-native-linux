# Stickkalibrierung: Start, Finish und Exit in der Firmware

Stand: 21. Oktober 2026. Statische Offline-Fortsetzung der
[Nexus-Dialoganalyse](NEXUS_STICK_CALIBRATION_FLOW.md). Keine Ausführung oder
Emulation von Firmware, keine Hersteller-App, Netzwerk- oder Gerätezugriffe.
Keine Änderung an Treiber, Manager, Control Center oder installiertem System.
Präzise Gyrokalibrierung bleibt pausiert.

**Fortsetzung:** Der [Speicherbericht](NEXUS_STICK_STORAGE.md) klärt inzwischen
die EE53-Record-Geometrie und verfolgt den Auftrag bis zum internen Abschluss.
Die frühere Bezeichnung „postincrement“ im zugehörigen historischen JSON-Nachweis
ist zurückgenommen. Der folgende Bericht bewahrt den damaligen Prüfungsumfang;
ein unabhängig belegter dauerhafter Speichererfolg bleibt auch nach der
Fortsetzung offen.

## Ergebnis

Für die untersuchte Controller-Firmware **DV209** ist jetzt mehr als die
PC-seitige Benennung bekannt:

- **Start** setzt den Kalibriermodus für die ausgewählten Sticks, sichert
  bisherige Werte in einem RAM-Datensatz und setzt Arbeitswerte zurück.
- **Finish** schreibt nicht unmittelbar den nichtflüchtigen Speicher. Es setzt
  für fertig gemeldete Teile Abschlussanforderungen. Ein späterer Verbraucher
  übernimmt die Ergebnisse und stellt getrennte Speicheraufgaben ein.
- **Exit** löscht bei noch aktiven Sticks die drei Kalibrierungsflags und ruft
  Routinen auf, die Werte aus der RAM-Sicherung zurückholen. Das ist ein
  konkreter Wiederherstellungspfad, kein bloßes Schließen der Oberfläche.

**Ein vollständig geprüfter Speicherabschluss und eine garantierte Rücknahme
sind weiterhin offen.** Der nachverfolgte Pfad reicht bis zum asynchronen
Speicherauftrag. Eine bereits abgeschlossene oder eingereihte Speicherung wird
im untersuchten Exit-Zweig nicht zurückgenommen. Ein Decoderproblem begrenzt
zudem den Nachweis der vollständigen Sicherung aller Tabellenwerte.

Damit lässt sich das Linux-Vorhaben genauer planen; ein sicher benutzbarer
Kalibrierbefehl wird hier noch nicht implementiert oder freigegeben.

## 1. Quellen, Adressen und Methode

[Maschinenlesbarer Nachweis](evidence/NEXUS_STICK_FIRMWARE_20261021.json) enthält
Hashes der drei unveränderten Apps DV209, DV515 und DV608, 30 Instruktionsanker,
15 geprüfte Aufrufkanten und drei bytegleiche Bereiche. Keine Firmwarebytes,
Herstellerquellen oder vollständigen Disassemblierungen werden veröffentlicht.

Die vorhandene Jieli-Analyseumgebung verwendet den zuvor korrigierten lokalen
Decoder und Ghidra 12.1.4 im geprüften, netzwerk- und geräteisolierten Sandbox-
Aufruf. Firmware wird ausschließlich als Datei dekodiert. Der abschließende
begrenzte Lauf umfasst **28 Bereiche / 692 Instruktionsdatensätze**, ohne
Dekodierabbruch in diesen Bereichen; Quellen und Decoder bleiben unverändert.
Parallelblöcke enthalten teilweise überlappende Darstellungen, daher ist dies
keine Zählung unabhängiger Maschinenbefehle und keine vollständige CFG-Abdeckung.

Alle folgenden Positionen sind **Dateioffsets in DV209**. `B = 0xf140` bezeichnet
seine RAM-Basis. Der RAM-Suffix ab Datei `0x4f718` läuft unter Basis null.
Suffix→Flash-Aufrufe werden mit dem bereits begründeten getrennten Adressmodell
aufgelöst, nicht durch pauschales Maskieren von Adressen. Siehe
[Adressmodell und Decodergrenzen](JIELI_WIRELESS_DATAFLOW.md#1-quellen-adressen-und-notwendige-decoderkorrektur).
Die verwendete Datei ist kein Nachweis der aktuell auf einem Controller
installierten Firmware oder des aktiven Edition-/Transportpfades.

Explorative Dekodierungen liefen auch an Tabellen, ungeeigneten Startgrenzen
und unbekannten Formen aus. Diese Ergebnisse wurden nicht als durchgehender
Code gewertet. Die abschließenden Bereiche enden vor solchen Stellen.
Insbesondere ist `EE53` bei `0x18a2`/`0x1924` weiterhin offen; bekannte Probleme
bei skalierten Halfword-Adressen und bedingten Parallelblöcken werden nicht
stillschweigend als gelöst behandelt.

## 2. Zuordnung der drei Operationen

Der Parser ab `0x1c98` verlangt zunächst Nachrichtentyp `0x0f` und ein Nullbyte
an Position 1. Er liest den Selektor an Position 4. Der Vergleich bei `0x1d32`
führt für `0xfe` nach `0x1fa8`; dort folgen Operationsbyte an Position 5 und
Teilmaske an Position 6. Die Operationsverzweigung ist:

| Wert | Ziel | Verhalten |
|---|---|---|
| 0 | `0x1fcc` | Start; Bit 0 für links, Bit 1 für rechts |
| 1 | `0x2268` | Abschlussanforderung aus vorhandenen Fertigflags |
| 2 | `0x21e8` | Exit für die noch aktiven Teile |
| andere | `0x1cba` | Rückkehr aus dem betrachteten Dispatcher |

Das passt strukturell zu Nexus' internem Inhalt `[fe, operation, partmask]` und
Nachrichtentyp `0x0f`. Es schließt die bisher offene **Semantikzuordnung**,
aber noch nicht die gesamte Windows-Provider-/USB-/Funkkette. Fehlende
Rahmenbytes, Längenregeln und Laufzeitzuordnung dürfen nicht ergänzt oder als
fertiges Sendepaket ausgegeben werden.

Im Stickpfad werden drei benachbarte Masken verwendet:

| RAM-Feld | Aus dem Kontrollfluss abgeleitete Rolle |
|---|---|
| `B+0x1b3a` | Kalibrierung aktiv |
| `B+0x1b3b` | Mess-/Drehablauf fertig |
| `B+0x1b3c` | Abschluss angefordert |

Diese Namen sind eigene Beschreibungen, keine Hersteller-Symbole. Finish und
Exit verwenden für die Sticks die gespeicherten Flags; sie benötigen dort
nicht erneut die Teilmaske aus dem Start. Das erklärt, warum Nexus bei diesen
beiden Aufrufen `calPart` weglassen kann. Andere Teile, insbesondere der
Motion-Zweig, werden damit nicht als identisch behandelt.

## 3. Start: Sicherung vor dem Zurücksetzen

Links (`0x1fcc…0x2028`) und rechts (`0x2028…0x2084`) werden separat ausgewählt.
Start setzt das jeweilige Aktivbit, löscht Fertig-/Abschlussbit und Zähler und
ruft vor dem Zurücksetzen der Arbeitsbereiche einen Packhelfer auf:

| Teil | Packhelfer | RAM-Datensatz | Arbeitswerte / ursprüngliche Gültigkeit |
|---|---|---|---|
| links | `0x1856` | ab `B+0x1b3e` | sechs Halfwords ab `B+0x1bba`; Gültigkeit wird bei `B+0x1b89` gesichert |
| rechts | `0x18d8` | ab `B+0x1b5d` | sechs Halfwords ab `B+0x1c22`; Gültigkeit wird bei `B+0x1b8a` gesichert |

Die sechs Halfwords werden als High-/Low-Byte-Paare abgelegt. Anschließend gibt
es eine Schleife über acht weitere Werte. Deren `EE53`-Store-Form ist noch nicht
vollständig dekodiert. Deshalb ist die **Existenz der Sicherung und ihr
Sechs-Werte-Kern** belegt, nicht die vollständige Gleichheit aller 30 Bytes bei
einem späteren Rückweg. Die Endmarkierungen `a6 6a` und der später verwendete
30-Byte-Umfang sind separat sichtbar. Die Marker sind kein nachgewiesener CRC.

Danach werden die jeweiligen 104-Byte-Arbeitsbereiche gelöscht und definierte
Startwerte gesetzt. Der untersuchte Startzweig enthält keinen Aufruf des
hier gefundenen Speicherauftragshelfers. Daraus folgt kein globaler Beweis,
dass andere Firmwareaufgaben währenddessen niemals schreiben.

## 4. Finish: Anforderung, Übernahme und Speicherung sind getrennt

Bei `0x2268` liest Finish die Fertigmaske. Die bedingten Abschnitte setzen für
bereits fertige Sticks das jeweilige Bit in der Abschlussmaske. Ein Finish bei
fehlendem Fertigbit erzwingt in diesem Pfad keinen Abschluss.

Ein späterer Verarbeitungsabschnitt prüft **aktiv, fertig und angefordert**:
links `0x542bc…0x54344`, rechts `0x54562` / `0x5463c…0x54680`.
Er löscht die zugehörigen Maskenbits und Zähler, setzt die neue Gültigkeit,
packt die nun aktuellen Werte mit denselben Helfern und aktualisiert über
`0x8e3c` die für die weitere Eingabeverarbeitung verwendeten Kalibrierwerte.
Er markiert anschließend den jeweiligen Datensatz als zu speichern:
`B+0x1b3d` links, `B+0x1b5c` rechts.

Der anschließende Speicherpfad ist inzwischen konkret nachvollzogen:

1. `0x543ec` prüft über `0x856c`, ob die Speichersteuerung bereit ist
   (Bit 0 von `B+0x81c` darf nicht gesetzt sein).
2. `0x543f2…0x54436` verarbeitet die beiden Markierungen getrennt, löscht sie
   jeweils vor dem Aufruf und übergibt einen Schreibauftrag an `0x33e`.
3. Links: logische Speicheradresse **`0x1700`**, Quelle `B+0x1b3e`, **30 Bytes**.
   Rechts: **`0x1720`**, Quelle `B+0x1b5d`, **30 Bytes**. Operation jeweils 1,
   zusätzlicher Callback-Parameter null.
4. `0x33e` baut einen 16-Byte-Auftragsdeskriptor mit Adresse, Datenzeiger,
   Länge und Callback und übergibt ihn an die Queue über `word[B+0x538]`.
   Der Deskriptor enthält einen **Zeiger**, keine vollständige Datenkopie.
5. Der Verbraucher `0x16980…0x169fa` entnimmt 16 Bytes nach `B+0xa54` und
   unterscheidet Lesen (0) und Schreiben (1). `0x16a66` ruft `0x11500` auf.
6. `0x11500…0x11564` übernimmt Operation, Adresse, Länge und Datenzeiger in
   den asynchronen Speicherzustand und setzt `B+0x81c`. Die Logtexte
   unterscheiden Start des Lesens und Schreibens. Das ist noch kein
   bestätigter Abschluss der physikalischen Schreiboperation.

Der separate Ladepfad liest bei `0xb268`/`0xb28e` genau dieselben Adressen mit
30 Bytes über `0x87f2`. Er prüft die Endmarker `a6 6a` und übernimmt die Werte
wieder in die Arbeitsstrukturen (`0xb2f8…`). Das stützt die Zuordnung als
persistente Kalibrierdatensätze. **Nicht belegt** sind der letzte erfolgreiche
Schreibzeitpunkt, vollständige Fehler-/ACK-Behandlung, Atomizität beider
Datensätze, Stromausfallsicherheit oder ein hostseitiger Rücklesebefehl.
Die Adressen sind logische Speicheradressen dieses Pfades, keine freigegebenen
Flashadressen oder Linux-Schreibanleitung.

## 5. Exit und zeitliche Abbruchgrenzen

Für jeden noch aktiven Stick löscht Exit Aktiv-, Fertig- und Abschlussbit.
Links ruft es `0x19b6`, rechts `0x1a80` auf. Diese Routinen lesen die gepackten
RAM-Werte zurück in die Arbeitsfelder und stellen das zuvor gesicherte
Gültigkeitsflag wieder her. Der betrachtete Stick-Exit-Zweig fordert selbst
keine neue EEPROM-Speicherung an.

| Zeitpunkt | Belegte Wirkung / Grenze |
|---|---|
| nach Start, vor Finish-Verarbeitung | Exit leert die drei Flags und führt den RAM-Rückweg aus; die vollständige Tabellenkopie bleibt wegen `EE53` gesondert zu prüfen |
| Fertig gemeldet, Finish noch nicht verarbeitet | Fertigbit wird durch Exit ebenfalls gelöscht |
| Exit verarbeitet, danach verspätetes Finish | Ohne neue Sitzung oder andere Flag-Schreiber fehlt das Fertigbit; Finish setzt kein neues Stick-Abschlussbit |
| Finish gesetzt, Verbraucher noch nicht gelaufen | Bei serieller Verarbeitung kann Exit die Anforderung noch löschen; zeitliche Nebenläufigkeit ist nicht bewiesen |
| Verbraucher hat Ergebnis übernommen | Aktivbit ist bereits gelöscht und RAM-Datensatz mit neuen Werten gepackt; Exit stellt darüber nicht mehr den alten Stand her |
| Speicherauftrag eingereiht / Schreiben läuft | Kein Abbruch oder Entfernen dieser Aufgabe im untersuchten Exit-Pfad nachgewiesen |
| Stromverlust / Funkverlust / Gerätewechsel | Nicht durch einen normalen Exit-Funktionsaufruf abgedeckt |

Der vorige Bericht bewies ein mögliches PC-seitiges **Exit → verspätetes
Finish** im eigenen Ablaufmodell. Der neue Firmwarebefund präzisiert dessen
Folgen: Bei vollständig verarbeitetem Exit und unveränderten übrigen Zuständen
ist diese Reihenfolge allein **kein Beweis für versehentliches Speichern**.
Der UI-Konflikt bleibt real im statischen Modell, sein Schaden darf aber nicht
behauptet werden. Andere Reihenfolgen oder eine neue Sitzung bleiben offen.

Auch ein erneutes Start könnte die RAM-Sicherung neu befüllen; eine unabhängige,
unveränderliche Transaktionssicherung ist nicht belegt. Der asynchrone Auftrag
hält einen Datenzeiger. Ein Linux-Nachbau darf deshalb keine zweite Kalibrierung
beginnen, während ein vorheriger Speicherabschluss noch ungeklärt ist.

## 6. Gegenprüfungen und nächster Schritt

- Quellenhashes aller drei Apps überprüft; 30 ausgewählte P-Code-/Instruktions-
  anker und 15 Aufrufkanten geprüft, einschließlich sieben Suffix→Flash-Kanten.
- Exit (`0x21e8…0x2268`) und Finish (`0x2268…0x22ce`) sind in DV515/DV608 an
  derselben Position bytegleich. Ein Schreibdeskriptor-Abschnitt liegt dort
  bytegleich um `0xe0` versetzt. Das beweist keine vollständige Editionsgleichheit.
- Fünf lokale Byte-Mutationskontrollen unterscheiden veränderte Aufrufziele bzw.
  Adressliterale. Keine Firmware wurde ausgeführt oder dauerhaft verändert.
- Die 13 vorhandenen synthetischen Nexus-Dialogfälle bleiben eine getrennte
  Prüfung der PC-Ablaufannahmen; sie simulieren weder MCU noch Speicherhardware.
  Alle 13 bestehen; ebenso der Test des reproduzierbaren Quellenarchivs. Acht
  neue lokale Dokumentationslinks, private Kennungen und das Projektmanifest
  wurden geprüft.

Die inzwischen vorliegende [Fortsetzung](NEXUS_STICK_STORAGE.md) grenzt `EE53`
anhand beider Kopier-/Rückwege ein und verfolgt den Speicherverbraucher bis zu
internen Abschluss- und Fehlerzweigen. Ein exakter unabhängiger ISA-Beleg,
verifizierter dauerhafter Erfolg und der tatsächliche Provider-/Transportpfad
bleiben offen. Erst damit lassen sich lesender Vergleich, Sitzungsschutz und
ein kontrollierter Kalibrierungstest sinnvoll vorbereiten. Die bislang unbekannte
Power-Loss-Recovery darf weder durch Marker noch durch einen UI-Erfolg ersetzt
werden.
