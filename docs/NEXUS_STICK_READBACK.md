# Stickkalibrierung: Finish, Statusbericht und Laden der Werte

Stand: 21. Oktober 2026. Offline-Fortsetzung des
[Kopier- und Speicherberichts](NEXUS_STICK_STORAGE.md), nach dem dort gesicherten
Checkpoint `50e8c13`. [Maschinenlesbare Belege](evidence/NEXUS_STICK_READBACK_20261021.json).
Keine App-/Firmwareausführung oder Emulation, kein Netzwerk- oder Gerätezugriff,
keine Änderungen an Treiber, Installation oder Steam. Präzise Gyrokalibrierung
bleibt pausiert.

**Fortsetzung:** Der [Transport- und Abbruchbericht](NEXUS_STICK_TRANSPORT.md)
verfolgt die drei Befehle zum Windows-GIP-Provider. Er trennt den belegten
Exit-Rückweg aus RAM von der noch offenen automatischen Reaktion auf Funkverlust.

## Ergebnis in verständlicher Form

**Nexus sendet Finish; die Firmware erledigt das Speichern selbst.** Der bereits
verfolgte Firmwarepfad übernimmt die fertigen Messwerte in zwei Datensätze und
reiht die Speicheraufträge ein. Nexus muss die Kalibrierwerte nicht selbst
berechnen oder einzeln schreiben. Die Erfolgsmeldung im untersuchten Dialog
wartet nicht zusätzlich auf das Ende dieses Schreibvorgangs.

Das ist ein möglicher Aufbau einer solchen Schnittstelle. Eine
zusätzliche Speicherquittung ist **keine zwingende Voraussetzung**, um den
vorhandenen Kalibrierungsablauf später unter Linux nachzubilden. Die fehlende
Quittung allein ist auch kein nachgewiesener Fehler der Hersteller-App.
Sie begrenzt lediglich, welche Speicherfehler die App selbst erkennen könnte.

Neu belegt sind die Felder für laufende/fertige Kalibrierung in einem
Firmware-Berichtspuffer und die dazu passenden Felder in Nexus' Statusparsern.
Außerdem lässt sich genauer erklären, wie die Firmware gespeicherte
Stickdatensätze wieder übernimmt: Sie prüft zwei Endkennbytes und kopiert dann
die enthaltenen Werte zurück in ihre Arbeitsbereiche.

**Status „Messung fertig“, Finish-Auftrag und später geladene Werte bleiben
drei verschiedene Beobachtungen.** Alte, weiterhin gültig markierte Werte
wären kein Beweis für eine neu abgeschlossene Speicherung. Daraus folgt kein
beobachteter Speicherfehler auf einem realen Controller.

## 1. Quellen und Beweisgrenzen

Primärquellen sind die unveränderte Controller-Firmware DV209 und Nexus
2.1.23.0. Ausgewählte identische Codeabschnitte wurden in DV515 und DV608
wiedergefunden. Dies beweist keine Gleichheit aller Firmwarepfade oder die
installierte Version eines der beiden Testcontroller.

Firmwareadressen unten sind DV209-Dateioffsets. `B = 0xf140` bezeichnet die
bereits verwendete RAM-Basis. Native PC-Adressen sind RVAs der DLL mit Imagebasis
`0x180000000`. Die vollständigen Dateien, Disassemblierungen und privaten
Arbeitsverzeichnisse bleiben außerhalb von Git; der Nachweis enthält Hashes,
Adressen und eigene Schlussfolgerungen.

Der abschließende isolierte Ghidra-Lauf verwendet den unveränderten Decoder:
**neun begrenzte Bereiche, 224 Instruktionsdatensätze, kein Dekodierabbruch**
innerhalb dieser Bereiche. Explorative Läufe scheiterten auch an ungeeigneten
Startgrenzen und unbekannten Befehlen. Insbesondere bleibt im umgebenden
Berichtscode `0x1ad4c` offen. Die Basiszuweisung bei `0x1ace6` und die späteren
Feldblöcke beweisen deshalb nicht allein den vollständigen Aufruf-/Schedulerpfad.
Überlappende Parallel-Darstellungen werden nicht doppelt ausgewertet.

Die unabhängige genaue EE53-Referenz und die externe Bedeutung des Busstatusbits
7 sind mit dem vorhandenen lokalen Material weiterhin nicht geschlossen.
Diese Untersuchung ersetzt diese Nachweise nicht durch eine Decoderänderung.

## 2. Die Kalibrierungsfelder im Bericht

Der Block ab `0x1aed8` baut einen 64-Byte-Puffer bei `B+0x1434` auf: Typbyte
`0x10`, ein vier Byte langer Kopf, darin Nutzlänge 60, anschließend Marker
`0xe0`. Für die beiden relevanten Felder gilt:

| Bedeutung aus der bisherigen Firmwareanalyse | RAM-Quelle | Voller Puffer, nullbasiert | 60-Byte-Nutzteil, nullbasiert | Übernahme |
|---|---|---:|---:|---|
| Kalibrierung aktiv / Teilmaske | `B+0x1b3a` | 30 | 26 | `0x1af10…0x1af1a` |
| Messung fertig / Teilmaske | `B+0x1b3b` | 31 | 27 | `0x1af1a…0x1af24` |

Beide Quellen sind von den Speicherfortschritts- und Bus-Fertigfeldern aus dem
[vorherigen Bericht](NEXUS_STICK_STORAGE.md#4-was-abschluss-und-fehler-tatsächlich-melden)
getrennt. Die untersuchten Zuweisungen transportieren diese Kalibrierungsmasken;
sie verwandeln sie nicht in einen Ergebniscode für dauerhaftes Speichern.

Bei `0x1afc0` wird `0x1aa92` mit dem neuen Puffer, einer 64-Byte-Vergleichskopie
und Länge 64 aufgerufen. Der Helfer vergleicht und aktualisiert die Kopie;
bei mindestens einem unterschiedlichen Byte liefert er einen gesetzten Wert.
Der Aufrufer überspringt bei unveränderten Daten die folgende Übergabe.
Andernfalls reicht `0x1afd2 → 0x2e8` den 64-Byte-Inhalt an einen Ringpuffer-
Helfer weiter. Dieser prüft Platz und kopiert die Daten. Eine erfolgte Übergabe
an diesen internen Pfad ist noch keine nachgewiesene USB-Zustellung an Nexus.

## 3. Die entsprechende PC-Seite

Die bereits untersuchten Statusparser lesen aus ihrem Bytearray Nutzteil 26
als DWORD-Feld und Nutzteil 27 als Byte-Feld. Die ersten 16 Bytes des nativen
Arrayobjekts sind dessen Verwaltung, nicht Nutzdaten:

| Parser-Fundstellen | Aktives Feld | Fertigmaske | Ziel im 0x118-Byte-Zustandsblock |
|---|---|---|---|
| Erster bekannter Pfad | `0x189590f` | `0x189591b` | `+4`, `+8` |
| Alternativer bekannter Pfad | `0x1984f49` | `0x1984f55` | `+4`, `+8` |
| Zusätzlich geprüfter gleichartiger Pfad | `0x1989f7d` | `0x1989f89` | `+4`, `+8` |

Die Array- und Strukturabstände wurden an den Originalbytes der DLL geprüft.
Die Parser übergeben ihren Zustandsblock über den Delegate-Helfer `0x18960c0`.
Der Benachrichtigungswrapper `0x198a790` kopiert den neuen Block an `+0x28`
seines Arbeitsrahmens und ruft `0x198a8d0` auf. Damit werden dessen Zugriffe
auf `+0x2c` und `+0x30` verständlich: Sie entsprechen den Strukturfeldern `+4`
und `+8`. Der Zeiger auf diesen Wrapper wird bei `0x1a64da8` aufgebaut.

Wie zuvor belegt, vergleicht der Benachrichtigungspfad diese beiden Felder mit
dem vorherigen Zustand und bildet `CalibrationStateChanged` einschließlich
`isCalMode = (Status != 1)` und der einzelnen Fertigbits. Das numerische
Vergleichskriterium wird dokumentiert, nicht zu einer allgemeinen booleschen
Semantik für sämtliche Geräte umgedeutet.

Die passenden Feldpositionen und Kopierwege verstärken die Zuordnung. Sie
schließen aber noch nicht jede Kante zwischen Controller, Funkempfänger,
Windows-Provider, Entfernung des Berichtskopfes und ausgewählter Geräteinstanz.
Auch die dynamische Delegate-Auswahl muss für den konkreten Transport gelten.
Die drei Parser werden nicht ungeprüft drei Controllereditionen zugeordnet.

## 4. Gespeicherte Stickwerte wieder laden

`0xb264…0xb2b6` veranlasst die bereits bekannten Leseoperationen über `0x87f2`:

| Stick | Logische Speicheradresse | Länge | RAM-Lesepuffer | Kennbytes | Geladen-Flag |
|---|---|---:|---|---|---|
| Links | `0x1700` | 30 | `B+0x1f2a` | `B+0x1f46/0x1f47` | `B+0x1b8e` |
| Rechts | `0x1720` | 30 | `B+0x1f49` | `B+0x1f65/0x1f66` | `B+0x1bf6` |

Diese Adressen sind interne Forschungsbefunde, keine freigegebene Linux-
Schreibschnittstelle. Der Lader wartet auf das gemeinsame Bus-Fertigflag.
Aus den Verzögerungsargumenten wird keine gesicherte Millisekundenfrist abgeleitet.

Links prüft `0xb2f8…0xb30c`, rechts `0xb37a…0xb38e` die Record-Bytes 28/29
auf `a6 6a`. Bei Abweichung wird der jeweilige Kopierblock übersprungen.
Bei passenden Kennbytes:

- Die ersten zwölf Bytes ergeben sechs Halfwords, hohes Byte zuerst; Ziel
  links `B+0x1bba`, rechts `B+0x1c22`.
- Die nächsten 16 Bytes ergeben acht weitere Halfwords; Ziel links
  `B+0x1b90`, rechts `B+0x1bf8`.
- Anschließend wird das jeweilige Geladen-Flag auf 1 gesetzt.

Die Tabellenkopie verwendet links Abstand `0x3a6`, rechts `0x35d` zwischen
Ziel und Quelle. Beide Abstände führen exakt zu Record-Byte 12. Das ist ein
weiterer Gegencheck der zuvor ermittelten Packgeometrie, jedoch noch keine
unabhängige Bestätigung der EE53-Befehlssemantik.

In diesen beiden begrenzten Marker-/Kopierblöcken wird weder eine Prüfsumme
über die 28 Nutzbytes noch ein Vergleich mit dem gerade angeforderten neuen
Kalibrierergebnis vorgenommen; es gibt dort auch keinen Funktionsaufruf für
eine solche Prüfung. Prüfungen an anderen Stellen sind damit nicht ausgeschlossen.
Die einzelnen Halfwords sind noch nicht vollständig als Mittelwert,
Endpunkt, Korrekturfaktor oder andere physikalische Größe zugeordnet.

Ab `0xb488` fließen beide Stick-Geladen-Flags zusammen mit weiteren Bedingungen
in zwei zusätzliche Zustandsbytes ein. Das ist kein isoliertes „beide Sticks
gerade neu gespeichert“-Ergebnis und kein Nachweis eines an Finish gebundenen
Rücklesevergleichs.

## 5. Was ein Linux-Nachbau daraus übernehmen kann

Der Maintainer weist zutreffend auf den geräteseitigen Vertrag hin: **Finish
ist der Auftrag; die Firmware übernimmt die Speicherung.** Für die spätere
Stickkalibrierung muss keine zusätzliche Quittung erfunden werden, wenn die
Schnittstelle keine anbietet. Die frühere pauschale Forderung nach einer
Speicherquittung vor jedem Nachbau wird hier entsprechend präzisiert.

Der spätere Ablauf kann sich an Start → geräteseitige Messung → Fertigflags →
Finish orientieren. Die Oberfläche darf den normalen Abschluss dieses Ablaufs
anzeigen. „Dauerhaft zurückgelesen und geprüft“ wäre dagegen eine zusätzliche
Eigenschaft, die erst nach einem passenden Nachweis behauptet werden dürfte.
Ein freiwilliger Rücklesevergleich könnte Fehler besser erkennbar machen;
sein Fehlen allein blockiert die weitere Kalibrierungsentwicklung nicht.

Vor einer echten Umsetzung bleiben insbesondere Transport-/Modellzuordnung,
eindeutiger Gerätebesitz, Abbruch vor Finish und die Grenze nach eingereihtem
Speicherauftrag zu klären. Ein spätes Exit ist nicht automatisch ein Rückrollen
bereits gespeicherter Werte. Die jetzige Diskussion gibt weder einen Hardwaretest
noch das Senden neuer Gerätebefehle frei.

Firmware-Updates sind ein getrenntes Vorhaben: Die Anforderungen an passende
Images, Integrität und Wiederherstellung werden dadurch nicht gelockert.

### Gewünschte Darstellung im Control Center

Der Maintainer schlägt eine einfache Führung mit sichtbarer Bewegung vor:

1. **Vorbereiten / Start:** Sticks loslassen, dann den Kalibriermodus starten.
2. **Bewegen:** Linker und rechter Stick erscheinen als getrennte Kreisanzeigen;
   der bereits abgefahrene Rand wird blau hervorgehoben. Sobald die Firmware
   den jeweiligen Stick als fertig meldet, wird dessen Kreis vollständig grün.
   Die Beschriftung „In Bearbeitung“ beziehungsweise „Fertig“ ergänzt die Farbe.
3. **Abschließen:** Nach beiden Fertigmeldungen Finish senden. Die Firmware
   übernimmt die Speicherung. Bei vorherigem Abbruch stattdessen Exit senden.

Start, Finish und Exit sind also drei verfügbare Operationen, keine immer
vollständig abzusendende Dreierfolge. Der visuelle Verlauf unterstützt den
Menschen, ersetzt aber keine geräteseitige Fertigmeldung. Die blaue Spur zeigt
nur die beobachtete Bewegung der aktuellen Sitzung, keinen berechneten
Kalibrierungs-Prozentwert. Ein vollständig abgefahrener Rand löst allein weder
Grün noch Finish aus; die Spur wird bei einem neuen Durchlauf zurückgesetzt.
Mit dieser Farbrückmeldung ist der gewünschte GUI-Umfang vorerst festgelegt.
Ob die vorhandenen
Eingaben während des Kalibriermodus durchgehend für die Anzeige nutzbar sind,
ist noch zu prüfen. Die Darstellung und der Ablauf sind hier als Ziel
dokumentiert; GUI und Berechtigungshelfer wurden nicht verändert.

## 6. Gegenprüfungen und nächster Schritt

- 40 Firmware-Fundstellen, fünf relative Aufrufziele und 14 native PC-Anker
  gegen die festgelegten Originaldateien geprüft.
- Marker-/Ladeblock, relevante Berichtszuweisungen und Vergleichshelfer jeweils
  bytegleich in DV209, DV515 und DV608 gefunden; genaue Offsets im Nachweis.
- Synthetische Record-Prüfung: 510 Veränderungen einzelner Kennbytes werden
  durch die betrachtete Markerbedingung abgewiesen. 224 einzelne Bitänderungen
  im Nutzteil lassen sie unverändert erfüllt. Das demonstriert die Grenze
  dieser Bedingung, keinen ausgeführten Firmwarefehler.
- Byte-Reihenfolge, Tabellenabstände, Berichtskopf und native Strukturabstände
  unabhängig als Datenlayout-Arithmetik geprüft. Keine Firmware emuliert.
- Die 13 vorhandenen Offline-Fälle für den Dialogablauf und der Test des
  reproduzierbaren Quellenarchivs bestehen. Relative Dokumentationslinks,
  private Kennungen in den geänderten Dateien und Projektprüfsummen wurden
  geprüft. Keine Runtime-Quelle wurde geändert.

Nächster sinnvoller Schritt: den vorhandenen Nexus-Transport für diese
Kalibrierungsoperationen und die modellbezogene Auswahl schließen, einschließlich
Abbruch und Verbindungsverlust. Zusätzlich kann nach einem bereits vorhandenen
Lesepfad für Kalibrierdaten gesucht werden. Keine neue Speicherquittung oder
unbekannte Geräteoperation voraussetzen. Die offenen ISA-/Registerfragen bleiben
mit ihren konkreten Grenzen gespeichert.
