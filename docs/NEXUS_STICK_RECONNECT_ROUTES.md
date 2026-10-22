# Stickkalibrierung: Welche Reconnect-Zweige fordern einen Neustart an?

Stand: 22. Oktober 2026. Offline-Fortsetzung der
[Reset- und RAM-Lebensdaueranalyse](NEXUS_STICK_RESET_LIFETIME.md).
[Fundstellen und Prüfbeleg](evidence/NEXUS_STICK_RECONNECT_ROUTES_20261022.json).

Die [Folgeanalyse des Abschalt-/Aufwachpfads](NEXUS_STICK_WAKE_RETENTION.md)
grenzt inzwischen die äußere RAM-Abschaltschleife und ihren Reset-Rückfall ab.
Physische RAM-Retention und der genaue Boot-ROM-Aufwachweg bleiben offen.

## Ergebnis

**Die Firmware behandelt nicht jeden Verbindungsverlust wie einen vollständigen
Neustart.** Auf Dongle-Seite sind jetzt die Zustandsbedingungen getrennt, die
einen Chip-Reset anfordern oder lediglich wieder die Verbindungsannahme
einschalten. Auf Controller-Seite sind die beiden bislang offenen internen
Aufträge ihren Empfängern zugeordnet: Kopplungsdaten bearbeiten mit anschließendem
bedingtem Reset, beziehungsweise Schlafmodus vorbereiten.

Für alte Kalibrierbefehle bedeutet das:

- **Abgeschlossener normaler Dongle-Neustart:** Der zuvor nachgewiesene
  RAM-Löschlauf entfernt ausstehenden Auftrag, Nutzlastkopie und Sequenzwert.
- **Nur Controller-Neustart:** Dessen Sequenzgedächtnis und Kalibrier-RAM werden
  gelöscht. Eine eventuell im Dongle verbliebene Kopie wird dadurch nicht gelöscht.
- **Verbindung erneut annehmen oder Schlafpfad:** Keine allgemeine Löschung
  alter Aufträge nachgewiesen. Die direkt untersuchten Zustandsänderungen sind
  von Pending-Kopie, Sequenz und Kalibrier-RAM getrennt. Weitere interne Helfer
  und der vollständige Aufwachpfad begrenzen die Aussage.

**Ein alter Befehl ist deshalb nach einem beliebigen Reconnect weder sicher
gelöscht noch nachweislich erneut ausgeführt.** Es gibt weiterhin keinen Beleg
für eine endlose Funkwiederholung, einen tatsächlich verspäteten Finish oder
automatisches Exit bei Funkverlust. Durchlassen der Sequenzprüfung allein ist
keine wirksame Kalibrieraktion und kein Speichervorgang.

## Quellen und Aussagegrenzen

Unveränderte lokale Dateien **DG144** (Dongle) und **DV209** (Controller), der
vorhandene isolierte statische Decoder, das bereits gespeicherte offizielle
Jieli-ROM-Listing und der lokal vorhandene BlueZ-HCI-Header. Herkunft und
vollständige Quelldatei-Hashes stehen im Prüfbeleg; Herstellerdateien und
vollständige Disassemblierungen bleiben außerhalb von Git.

`D = 0x62c0` und `B = 0xf140` sind die jeweiligen RAM-Basen. Codeadressen
bezeichnen Dateioffsets; abweichende RAM-Laufadressen sind ausdrücklich markiert.
Ein direkt nachverfolgter **Resetauftrag** ist vom **erfolgreichen Reset mit
anschließendem normalem App-Start** zu unterscheiden. Letzterer wurde nicht
ausgeführt. Die RAM-Löschwirkung dieses Startcodes ist separat belegt, der
tatsächlich gewählte Zweig auf einem realen Controller hier nicht beobachtet.

Kein Netzwerk-, SSH-, USB-, Funk- oder Input-Zugriff, keine Hersteller-App- oder
Firmwareausführung beziehungsweise Emulation. Kein installierter Treiber,
Firmwareinhalt oder Decoder wurde verändert. Beide Installationen und die
zurückgestellte Treiberdiagnose bleiben erhalten; präzise Gyrokalibrierung pausiert.

## 1. Dongle: Reset oder erneute Verbindungsannahme

Der zuvor identifizierte interne Event-5-Handler bei `0x8b12` prüft Länge vier,
Erfolgsstatus null und den gespeicherten Verbindungshandle in `D+0x670/0x671`.
Erst für den passenden Fall gelten die folgenden Entscheidungen. Das ist
keine Aussage, dass jeder physische Funkverlust genau diesen Eventweg benutzt.

| Bedingung | Belegter weiterer Weg | Einordnung |
|---|---|---|
| Passendes Ereignis und `D+0x13 == 0` | `0x8b5c → 0x8ef0`; Vorbereitung `0x79a4`, Warteschleife `0x79cc`, dann `0x8f06 → 0x79fa` | Chip-Reset wird angefordert, sofern die vorgelagerten Helfer zurückkehren |
| Passendes Ereignis und `D+0x13 != 0` | `0x8b62/0x8b64` setzt Zustand sechs | Noch kein unmittelbarer vollständiger Reset |
| Worker-Zustand sechs und `D+0x238 != 0` | `0xc6ee…0xc70a → 0xa5da` | Modusbehandlung mit Resetauftrag |
| Worker-Zustand sechs, `D+0x238 == 0`, `D+0x16 == 1` | `0xc83c…0xc848 → 0xa5da` | Ebenfalls Modusbehandlung mit Resetauftrag |
| Worker-Zustand sechs, `D+0x238 == 0`, `D+0x16 != 1` | `0xc8c8` setzt Zustand null; `0xc8cc → 0x7960` | Verbindungsannahme einschalten, ohne unmittelbaren vollständigen RAM-Neustart in diesem Wrapper |

`0xa5da` benutzt den übergebenen Wert aus `D+0x15` als Modus. Die 18 Einträge
der Sprungtabelle bei `0xa5ea` führen entweder direkt oder nach Textausgabe
zu `0xa624`. Auch Werte außerhalb der Tabelle erreichen diesen Punkt.
`0xa628 → 0x6922` bearbeitet den Modus mit Kennung `0x55`; danach folgt
`0xa62e → 0x79fa`. **Der Modus wählt innerhalb dieses Helfers keinen
resetfreien Ausgang.** Die Aussage setzt die Rückkehr der vorherigen Aufrufe
voraus. Der nach `0xc70a` vorhandene Aufruf von `0x7960` ist kein Beleg, dass
die Resetprimitive tatsächlich zurückkehrt.

`0x79fa` ist der bereits aufgelöste Weg zum P33-Reset: Nullbasisziel
`0x20008c → RAM 0x14c`, Dateioffset `0x37174`. Nach abgeschlossenem normalem
Startup wird der Bereich `[0x5b60, 0x17804)` gelöscht. Er umfasst die
ausstehende Kopie und Sequenz, nicht die nichtflüchtige Kalibrierspeicherung.

Im anderen Zweig löscht `0x7960` das Ausgabefeld `D+0x1bc` und fordert
**HCI Write Scan Enable `0x0c1a`, Parameter zwei (Page Scan)** an. Das ist
kein HCI Disconnect und kein unmittelbarer Löschlauf über `D+0x2d0` oder
`D+0xb64`. Das Feld sperrt die zuvor untersuchten Ausgabepfade; eine behaltene
Kopie ist daher nicht gleichbedeutend mit dauernder Übertragung.

Der Verbindungsaufbau bei `0x8cce` übernimmt Handle/Adresse und verändert einen
Verbindungszähler. Der Worker-Zweig bei Zustand drei (`0xc718`) geht zu Zustand
fünf und bereitet weitere Kommunikation vor. Diese begrenzten Abschnitte
enthalten keinen normalen Startup-Löschlauf. Die vollständige Wirkung aller
unteren Stack-Aufrufe und Alias-Schreiber ist damit nicht ausgeschlossen.

## 2. Die bislang offenen Controller-Aufträge haben jetzt konkrete Empfänger

Die Task-Einrichtung bei `0xb764…0xb790` übergibt den Einstieg
`0x01e154ba → Dateioffset 0x153fa` an den bereits verwendeten Task-Helfer
`0x4558e`. Der Namensaufbau verwendet den Basiswert `0x01e24f50` aus
`0x9d98` plus `0x459`: die vorhandene Zeichenfolge `joypadtask`.
Die Produzenten verwenden denselben Namen beim Aufruf von `0x20a048`.

Der Consumer erhält bei `0x17098` Nachrichten über den Helfer `0x20a852`.
Nur dessen Rückgabewert `0x0d` führt zur Auswertung des Nachrichtenfeldes.
Der Eintrag wird um `0x400001` vermindert; nur Indizes null bis `0x18`
werden über die 25 Byte-Einträge bei `0x170ac` verteilt. Die Sprungziele
sind aus den Tabellenbytes unabhängig vom Decoder nachgerechnet.

| Interner Auftrag | Tabellenziel | Nachverfolgter Ablauf |
|---|---|---|
| `0x400008`, unter anderem Produzent `0xd4de` | `0x1713e` | `0x8ff6`, `B+0x4ac = 1`, `0x10580`, dann über `0x154b4` zu `0x8582` |
| `0x40000b`, Produzent `0x9882` | `0x17118 → 0x15430` | Weiteren Schlafauftrag über `0x106a2` einstellen; abhängig von `B+0x4b8` zusätzlich Trennung anfordern |
| `0x40000c`, Produzent `0x106a2` | `0x171da` | `0x9694`, anschließend Warte-/Schlafpfad mit gesondertem RAM-Einstieg |

Damit sind die zwei offenen Task-Ziele aufgelöst. Das ersetzt keinen Nachweis,
dass jede gepostete Nachricht im realen Ablauf zugestellt wird oder in welcher
Reihenfolge mehrere Tasks arbeiten. Auch die Registerlebensdauer über sämtliche
Zweige der großen Einrichtungsfunktion wurde nicht vollständig bewiesen.

## 3. Kopplungsdaten-Auftrag: bedingter Controller-Reset

`0x10580` arbeitet mit den Kopplungs-/Modusdatensätzen: abhängig von den
Modusfeldern wird ein 16-Byte-Datensatz ab `B+0x20c4` über den vorhandenen
Speicherhelfer `0x33e` unter Kennungen `0x1a50…0x1aa0` abgelegt. Weitere
Helfer bearbeiten Adresse und Modusfelder; danach wird `B+0x4ac` zurückgesetzt.
Diese Befehlsfolge ist von TMR-Finish und dem Wiederherstellen der gesicherten
Stick-Kalibrierwerte zu unterscheiden. Die Speichercompletion wird hier nicht
erneut als neue Kalibrierbestätigung interpretiert.

Danach entscheidet `0x8582` anhand folgender Werte:

- `Q`: Rückgabe von `0x854e`, aufgerufen mit dem Zeiger aus dem **Wort an
  `B+0x538`** (`0x14e` wird beim Laden mit vier multipliziert).
- `F`: Byte an `B+0x724`.
- `H`: `1 & ~Byte(B+0x81c)` aus `0x856c`.

Beide Prüfungen müssen erfüllt sein:

```text
(Q | F) != 0  und  (H | F) != 0
```

Ist `F` ungleich null, sind beide Prüfungen erfüllt. Andernfalls müssen `Q`
und `H` jeweils ungleich null sein. Den Zustandsfeldern wird hier keine
unbelegte Bedeutung wie „USB verbunden“ zugeschrieben.

Bei erfüllter Bedingung setzt der Helfer `B+0x56c`, bereitet Peripherie vor
und erreicht **`0x85d6 → Nullbasisziel 0x20004a → RAM 0x10a`**. Das ist
dieselbe zuvor belegte P33-Resetprimitive im Controller-Suffix, Dateioffset
`0x4f822`. Vollständig durchlaufener normaler Startup löscht anschließend
`[0xda60, 0x240e8)`, einschließlich `B+0x50` und der Kalibrier-RAM-Bereiche.

Andernfalls kehrt der Helfer über `0x85da…0x85ee` zurück und schreibt nur:
Byte `B+0x7c = 1`, Halbwort **`B+0x14e = 0`**, Byte `B+0x56c = 0`.
Der direkte Halbwortzugriff ist nicht das vorherige Zeigerwort `B+0x538`.
Diese drei direkten Schreibintervalle überschneiden weder `B+0x50` noch
die bekannten Kalibrierflags, Sicherungen und Arbeitsbereiche. Das beweist
den Umfang dieses Rückkehrzweigs, nicht alle vorherigen/parallel laufenden
Task- oder Stack-Wirkungen.

**Ein Controller-Reset löscht kein Dongle-RAM.** Falls dort ein Auftrag
verbleibt, kann der neue letzte Sequenzwert des Controllers die Filterentscheidung
ändern. Die zusätzlichen Kalibrierzustände bleiben entscheidend; daraus folgt
kein nachgewiesenes Speichern durch einen alten Finish.

## 4. Schlafauftrag: nicht mit vollständigem Neustart gleichsetzen

Der Auftrag `0x40000b` erreicht `0x15430`. Bei `B+0x4b8 != 0` setzt er
`B+0x574`, stellt über `0x106a2` den Auftrag `0x40000c` ein und ruft
`0xd628` auf. Letzterer verwendet den gespeicherten Handle sowie den Deskriptor
bei `0x23bac`: **HCI Disconnect `0x0406`, Grund `0x13`**. Bei gelöschtem
`B+0x4b8` führt der Zweig `0x154fc` ebenfalls zum Folgeauftrag, ohne diesen
Trennaufruf. Ein Auftrag in der Queue beweist noch keine erfolgreiche Zustellung.

`0x40000c → 0x9694` bearbeitet Peripherie und einen Wartepfad. Innerhalb dieses
Wartepfads kann bei einer weiteren Bedingung auch `0x9720 → 0x8582` aufgerufen
werden: dann gilt wieder die gerade beschriebene bedingte Resetentscheidung.
Der andere Ausgang erreicht bei **`0x987c` das Nullbasisziel `0x200bba`**.
Die etablierte Adressabbildung führt zu **RAM `0xc7a`, Dateioffset `0x50392`**.
Dies ist ausdrücklich ein anderer Einstieg als die Resetprimitive bei RAM
`0x10a`. Der begrenzt dekodierte Einstieg ruft Vorbereitungs-/P33-Helfer auf.

Die vollständige Wirkung auf Stromversorgung, RAM-Erhalt und Wiederanlauf nach
diesem Schlafpfad ist noch offen. Er wird deshalb weder als garantiert
RAM-erhaltender Reconnect noch als gesicherter normaler Neustart verbucht.
Die nach den vorgesehenen nicht zurückkehrenden Aufrufen sichtbaren lokalen
Endlosschleifen bei `0x171de` beziehungsweise `0x9880` sind **keine Schleifen
zum erneuten Senden von Kalibrierbefehlen**.

Auch der Schlafpfad-Aufruf `0x82f0` darf nicht mit dem getrennten Kalibrier-
Arbeitsbereichshelfer `0x82f4` verwechselt werden. Automatische Wiederherstellung
der gesicherten Stickwerte bei Funkverlust bleibt unbewiesen.

## 5. Folgerung für den geplanten Linux-Kalibrierablauf

Start, Finish und Exit bleiben firmwareeigene Operationen. Es wird keine neue
Bestätigung „dauerhaft gespeichert und geprüft“ erfunden. Die Anwendung soll
bei verlorenem Gerät aber keinen alten Auftrag automatisch nachholen oder
einen Reconnect als bestätigten Abbruch darstellen. Eine alte Sequenz, eine
vorhandene Pending-Kopie, aktuelle Sendefreigabe und wirksame Kalibrieraktion
sind getrennte Zustände.

Als nächste begrenzte Offline-Frage bleibt insbesondere der vollständige
Aufwach-/RAM-Erhaltungsweg hinter RAM `0xc7a`. Eine erneute Suche nach dem
generischen Reset-Ziel oder den beiden nun zugeordneten Task-Consumern ist
nicht nötig. Die reale Auswahl der Zustandszweige bleibt eine spätere,
gesondert freizugebende Beobachtung; in dieser Arbeit wurde kein Test gestartet.

## Validierung

- 44 begrenzte Decoderbereiche, 669 Datensätze, keine Fehler in den finalen
  beiden Läufen; unveränderte Eingabedateien und unveränderter Decoder.
- 171 Literal-, 179 kurze und 293 lange Transferformen gegen das lokal
  gespeicherte offizielle Jieli-Listing geprüft; Tabellenbefehl zusätzlich
  anhand eines offiziellen Bytebelegs verglichen.
- 147 konkrete direkte Sprung-/Aufrufziele unabhängig nachgerechnet;
  147 veränderte Operanden erkannt. 43 Tabelleneinträge mit 43 veränderten
  Kontrollwerten geprüft; 20 direkte Speicherintervall-Vergleiche.
- Acht Kombinationen der dokumentierten booleschen Resetbedingung geprüft.
  Das ist ein eigenes Konsistenzmodell, keine Ausführung/Emulation der Firmware.
- 16 bestehende Offline-Tests des Nexus-Kalibrierungsablaufs bestanden.

Erfolgreiche Dekodierung allein beweist keine vollständige Befehlssemantik.
Die bekannten NOT-/REP-Grenzen aus dem vorigen Bericht bleiben dokumentiert;
der ungeklärte Operand-/Parallelfall DV `0xe976` bleibt ausgeschlossen.
Suchläufe an ungeeigneten Grenzen beziehungsweise Tabellen werden nicht als
fehlerfreie Validierung gezählt. Keine vollständige Alias-, Betriebssystem-,
Boot-ROM- oder Nebenläufigkeitsanalyse und keine Hardwareabnahme behauptet.
