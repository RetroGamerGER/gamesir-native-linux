# Stickkalibrierung: USB, Funkrahmen und RAM-Rückweg

**Fortsetzung vom 22. Oktober:** Der [USB-Formatbericht](TMR_USB_FRAMING.md)
schließt die unten noch offene DG-Callback-/Modus-/Queue-Kante. Er beschreibt
den vollständigen Linux-Testentwurf und seine Feldbelege; der externe
Windows-Provider und dessen exakter USB-Transfer bleiben unbeobachtet.
Dieser frühere Bericht behält seinen damaligen Untersuchungsumfang.

Stand: 21. Oktober 2026. Statische Fortsetzung des
[Nexus-Übertragungsberichts](NEXUS_STICK_TRANSPORT.md).
[Fundstellen, Quellenhashes und Prüfgrenzen](evidence/NEXUS_STICK_WIRE_PATH_20261021.json).
Keine App-/Firmwareausführung oder Emulation, kein Netzwerk- oder Gerätezugriff,
keine Änderung an installiertem Treiber oder System.

Weiterführung: [Ausstehende Befehle bei Funkverlust](NEXUS_STICK_RECONNECT.md)
klärt anschließend Transportantwort, Wiederholungsfilter und die Trennung von
Queue-Reset und gehaltener Kopie. Die tatsächliche Reconnect-Lebensdauer und
automatische RAM-Wiederherstellung bleiben offen.

## Ergebnis

**Der Datenweg innerhalb von Dongle und Controller ist deutlich weiter geklärt.**
Im untersuchten Dongle-Zweig werden normale GIP-Nachrichten in einen zweiten
Datenblock aufgenommen. Dieser erhält einen `0xa0`-Vorspann mit Sequenzfeld.
Der Controller prüft den Block, entfernt den Vorspann und erreicht darüber
denselben Befehlsverteiler wie über seinen USB-Eingang. Dort liegen die bereits
untersuchten Start-, Finish- und Exit-Zweige.

Das ist eine statisch gestützte Transportkette unter ihren jeweiligen
Zustandsbedingungen, **noch kein vollständig geprüfter Linux-Sendebefehl**.
Insbesondere sind Windows' vollständige GIP-Rahmenerzeugung, die Auswahl aller
USB-Modi und das Verhalten des unteren Funktransports nicht geschlossen.

**Exit besitzt einen RAM-Rückweg; Funkverlust ist weiterhin kein belegter
automatischer Exit.** Ohne Finish wird im untersuchten Abschlussweg nichts neu
gespeichert. Bereits durch Start veränderte Arbeitswerte werden dadurch allein
aber nicht zurückgesetzt. Der geplante einfache Ablauf bleibt: Start, bewegen,
Fertigstatus, Finish — oder Exit bei Abbruch. Keine zusätzliche Speicherquittung
und kein eigener Kalibrieralgorithmus auf dem PC werden vorausgesetzt.

## Quellen und Adressen

Die neuen Transportfundstellen beziehen sich auf die unveränderten Dateien
**DV209** (Controller) und **DG144** (Dongle). Alle Codepositionen unten sind
Dateioffsets; `B = 0xf140` und `D = 0x62c0` sind die jeweiligen RAM-Bezugspunkte.
Diese Dateien beweisen weder die aktuell installierten Versionen noch den
Laufzeitpfad der Standard- oder ZZZ-Ausführung. Die vorherige Nexus-/Provider-
Analyse und die vorherigen Kalibrierungs-/Speicherberichte bleiben eigene
Belege; ihre Grenzen werden nicht durch ähnliche Rahmenfelder aufgehoben.

Herstellerdateien, vollständige Disassemblierungen und private Pfade verbleiben
außerhalb von Git. Veröffentlicht werden eigene Beschreibungen, Adressen und
Hashes. Der lokale Decoder wurde nicht verändert.

## 1. Die PC-Grenze bleibt vom USB-Paket zu unterscheiden

Nexus übergibt dem Windows-GIP-Provider Nachrichtentyp `0x0f` und drei Nutzbytes:

| Anfrage | Interner Nutzinhalt |
|---|---|
| Start beider Sticks | `fe 00 03` |
| Finish | `fe 01 00` |
| Exit | `fe 02 00` |

Das sind weiterhin **keine vollständigen USB-Pakete**. Die Controller-Firmware
erwartet den Selektor an Position 4, Operation und Teilmaske an 5/6. Welche
Sequenz-, Längen- und Bestätigungsfelder Windows davor erzeugt, ist nicht durch
das App-Interface allein nachgewiesen. Keine fehlenden Bytes werden geraten.

## 2. USB-Kabeleingang des Controllers

Die DV209-Konfiguration bei `0x4e96` hinterlegt den Textzeiger auf `0x244e`.
Bei `0x4eaa` wird Endpunktnummer **2** an die Konfiguration übergeben; die
benachbarte Gegenrichtung verwendet `0x82`. Der Callback `0x244e` holt den
endpunktabhängigen Puffer über `0x13a` und bedient den Empfang über `0x2e0`.
Die Tabellen-/Registerhelfer wurden begrenzt gegengeprüft.

Nach modusspezifischen Sonderzweigen führt der allgemeine Weg bei
`0x27a4…0x27a8` nach `0x23ae`. Dieser Wrapper unterscheidet unter anderem Rumble
und Nachrichten vom Typ `0x0f`; bei `0x243a` ruft er `0x1c98` auf. Dessen
Selektor `0xfe` führt zu Start/Finish/Exit, wie im
[Firmwarebericht](NEXUS_STICK_FIRMWARE.md#2-zuordnung-der-drei-operationen) belegt.

Das ist der betrachtete USB/GIP-Pfad. Er darf nicht mit dem zuvor erforschten
Sensor-HID-Endpunkt `0x84/0x04` oder dem Funkdongle gleichgesetzt werden.
Die vorgelagerten Modusbedingungen gelten weiterhin.

## 3. Dongle: GIP-Nachricht in den zweiten Funk-Datenblock

Im DG144-Verarbeitungszweig bei `0xb2a` gilt für eine Nachricht vom Typ `0x0f`:
Selektor an Position 4 **ungleich `0xf0`** führt bei `0xb32` nach `0xbca`.
Damit fällt `0xfe` strukturell in diesen Zweig. Die ursprünglichen Bytes und
die dort vorliegende Länge werden bei `0xbd4` über `0x680` in die Warteschlange
mit Zeiger **`D+0x2dc`** gestellt. Die Auswahl dieses Zweigs aus allen
USB-Modi sowie seine vollständige Wurzel am USB-Callback bleiben offen.

Der Verbraucher `0xa7a6` nimmt diese Warteschlange auf:

| Schritt | DG144-Fundstelle | Wirkung |
|---|---|---|
| Bereitschaft/Zeit prüfen | `0xa7a8`, `0xa7bc`, `0xa802` | Zustandsfelder und Zähler begrenzen die Ausgabe; kein bedingungsloser Sofortversand |
| Nachricht entnehmen | `0xa7f2…0xa812` | Queue `D+0x2dc`; Daten landen im Ziel ab `+2` |
| Ausstehende Kopie behalten | `0xa81c…0xa824` | Länge und Kopie bei `D+0xb64` |
| Vorspann ergänzen | `0xa828…0xa844` | Sequenzfeld fortschreiben, `0xa0` und Sequenz voranstellen; Länge um zwei erhöhen |
| Vorhandene Kopie erneut formatieren | `0xa7c6…0xa7f0` | Bei gesetztem Zustand `D+0x2d0` werden die gehaltenen Bytes wieder verwendet |

**Wichtige Unterscheidung:** Die andere Queue `D+0x2a4`, gelesen durch `0xa75e`,
liefert den ersten Block. Sie darf nicht als Ersatzbeleg für den normalen
GIP-Kalibrierbefehl dienen. In der bisherigen Sensoranalyse lief der Datenfluss
außerdem überwiegend in Gegenrichtung, vom Controller zum PC.

Der Rahmenbauer `0xa8d8`, hier im Zweig für Typ `0x11`, legt zuerst den ersten
Block und unmittelbar dahinter den zweiten ab. Er ergänzt getrennte Längen
und Prüffelder. Danach kopiert er den gemeinsamen 35-Byte-Kopf vor die Blöcke.
Der Aufrufweg bei `0xc926…0xc92c` erreicht Rahmenbau und anschließend `0x7bf4`;
dieser führt nach der Längenermittlung zu `0x18b78`, dem bereits untersuchten
[Transport-Wrapper](JIELI_RADIO_CALLBACK.md). Ein Aufruf dieses Wrappers beweist
für sich weder eine erfolgreiche Funkzustellung noch deren Bestätigung.

## 4. Controller: gleicher Rahmen, Rückkehr zum GIP-Verteiler

Die DV209-Auswahl bei `0xf350/0xf354` kennt die Typen `0x11` und `0x21`.
Bei `0xf508/0xf510` wird der darin liegende Bereich ab `P+0x0d` an `0xde2e`
gegeben. Dieser kopiert 35 Kopfbytes nach `B+0xd78` und prüft einen über die
ersten 33 Bytes berechneten Wert gegen die folgenden zwei Bytes.

Mit **H** als Beginn dieses inneren Kopfes passen beide Seiten zusammen:

| Feld | Relativ zu H | DG144-Erzeugung | DV209-Verbrauch |
|---|---:|---|---|
| Länge erster Block, höheres Byte zuerst | `0x19…0x1a` | `0xa974…0xa97a` | `0xe1ae…0xe1bc` |
| Prüffeld erster Block | `0x1b…0x1c` | `0xa97c…0xa98a` | `0xe1ca…0xe1e2` |
| Länge zweiter Block, höheres Byte zuerst | `0x1d…0x1e` | `0xa98c…0xa990` | `0xe200…0xe214` |
| Prüffeld zweiter Block | `0x1f…0x20` | `0xa994…0xa99c` | `0xe222…0xe23a` |
| Prüffeld des Kopfes | `0x21…0x22` | `0xa84a…0xa868` | `0xde52…0xde76` |
| Erster Block | `0x23` | Queueverbrauch `0xa75e` | eigener direkter Aufruf von `0x1c98`, zustandsabhängig |
| Zweiter Block | `0x23 + Länge erster Block` | Queueverbrauch `0xa7a6` | `0xe218…0xe260` |

Für den ersten Block erkennt der untersuchte 16-Bit-Längentest den Bereich
1 bis 64. Daraus folgt **keine pauschale vollständige Längenprüfung für den
zweiten Block**. Dessen umgebende Puffergrenzen und vollständige Fehlerbehandlung
sind nicht abschließend geprüft.

Beim zweiten Block werden Prüffeld, `0xa0`-Kennung und Sequenzbezug geprüft.
Unter der dortigen Bedingung entfernt `0xe252…0xe258` zwei Vorspannbytes und
ruft `0xde2a` auf. Das ist ein Sprung nach `0x23ae` und damit zum gemeinsamen
GIP-Verteiler und den drei Kalibrieroperationen. **Die Kalibrier-Nutzbytes werden
in diesen Kopier-/Entpackschritten nicht umgerechnet.** Daraus folgt keine
Byteidentität des gesamten Funksignals oder aller unteren Transportstufen.

Die Bedeutung des Sequenzreferenzfelds `B+0x50` — etwa vorherige oder erwartete
Sequenz — wird nicht allein aus diesem Vergleich benannt. Auch der genaue
CRC-Algorithmus einschließlich Anfangs-/Endbehandlung ist hier nicht unabhängig
validiert. Die bekannten Decodergrenzen für bedingte Parallelblöcke bleiben
relevant; eine erfolgreiche Dekodierung ist kein vollständiger ISA-Beweis.

## 5. Was Verbindungsverlust für den RAM-Rückweg bedeutet

Der normale Exit-Zweig stellt bei aktiver Stickkalibrierung die gesicherten
Arbeitswerte wieder her und löscht die zugehörigen Flags. Bereits übernommene
Ergebnisse oder eingereihte Speicheraufträge nimmt er nicht zurück.

Neu begrenzt geprüft wurde der Zustandshelfer `0x4820…0x4842`, der aus dem
Empfangsablauf bei `0xe00e` und `0xe132` erreichbar ist. Er schreibt andere
Statusfelder und enthält **keinen Aufruf** der bekannten Restore-Helfer; die
Kalibrierflags `B+0x1b3a…0x1b3c` werden in diesem kleinen Abschnitt nicht geändert.
Die Auslöser davor sind noch nicht vollständig als Funkverlust klassifiziert.
Dieser Befund schließt daher nur diesen Kandidaten als eigenständigen
RAM-Rückweg aus, nicht jeden indirekten oder späteren Rückweg der Firmware.

Die zusätzlichen Restore-Stellen außerhalb von Exit bleiben an Tabellen- und
Statusprüfungen gebunden. Auch sie sind weiterhin kein belegter Verlust-Handler.

Der ausstehende Nachrichtenpuffer im Dongle macht zusätzlich eine Grenze
sichtbar: **Nexus' direkter Sendepfad bedeutet nicht, dass weiter unten nie eine
Wiederholung stattfindet.** Ob Funkverlust diese Kopie löscht, wie sie quittiert
wird und ob sie eine Wiederverbindung überlebt, ist offen. Deshalb gilt:

- Ohne angefordertes Finish: im geprüften Abschlussweg keine neue Speicherung;
  Start kann im RAM trotzdem noch wirksam sein.
- Finish wurde angefordert, dann Verbindung weg: Zustellung und Abschluss
  können unklar sein. Kein automatisches erneutes Finish durch die Linux-App.
- Exit wurde angefordert, dann Verbindung weg: Die Anforderung allein beweist
  noch keine RAM-Wiederherstellung im Controller.

Für die spätere Oberfläche bleiben Geräteinstanzbindung, Stoppen ausstehender
UI-Aktionen und eine verständliche Verlustmeldung sinnvoll. **Keine automatische
Rückstellung oder erneute Kalibrierung bei Reconnect** wird aus diesem Befund
implementiert. Ein Neustart kann den bekannten Ladepfad gespeicherter Records
nutzen; ein garantierter Wiederanlauf nach jedem Verlust ist damit nicht bewiesen.

## Prüfung und nächste offene Kanten

Der abschließende isolierte Decoderlauf umfasst 23 begrenzte Bereiche mit
494 Instruktionsdatensätzen ohne Abbruch in diesen Bereichen. Frühere
Suchbereiche trafen Tabellen, ungeeignete Startgrenzen oder unbekannte Formen;
sie wurden nicht als durchgehender Code gewertet. Quellen und Decoder bleiben
unverändert. Byte-/Aufrufanker, veränderte Aufrufoperanden, 195 synthetische
Block-Geometrien und der vollständige 16-Bit-Längenbereich wurden gegengeprüft.
Diese eigenen Geometrieprüfungen sind keine Firmwareemulation oder Live-Tests.
Die 16 vorhandenen Dialog-Ablauftests bleiben ein eigener, synthetischer Beleg.

Gezielt offen bleiben:

1. Windows-Provider → exakter USB-Rahmen und DG144-USB-Callback/Modusauswahl.
2. Quittierung und Lebensdauer des ausstehenden `0xa0`-Blocks über Funkverlust
   und Wiederverbindung; untere Funkzustellung und Sequenzreferenz.
3. Tatsächlicher Funkverlust-Handler → aktive Kalibrierflags → eventueller
   RAM-Restore. Bis dahin keine Zusage „automatisch Ausgangszustand“.
4. Verfügbarkeit der normalen Stickpositionsmeldungen während der Kalibrierung
   und Übertragbarkeit auf die tatsächlich verwendeten Firmware-/Editionpaare.

Keine neue Installation, Geräteaufnahme oder Kalibrierung freigegeben.
Firmware-Updater und präzise Gyrokalibrierung behalten ihren getrennten Status.
