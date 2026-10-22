# Stickkalibrierung: Rücksetzen, Funkverlust und spätere Wiederholung

Stand: 21. Oktober 2026. Offline-Fortsetzung des
[Berichts über ausstehende Befehle](NEXUS_STICK_RECONNECT.md).
[Fundstellen und Prüfbeleg](evidence/NEXUS_STICK_RESET_PATHS_20261021.json).

**Fortsetzung vom 22. Oktober:** Der
[Soft-Reset-/Sequenzbericht](NEXUS_STICK_RESET_LIFETIME.md) löst das unten noch
externe Reset-Ziel in den bekannten RAM-Suffix auf. Die normale Startinitialisierung
löscht die untersuchten Pending-/Sequenz-/Kalibrier-RAM-Felder. Ob der konkrete
Funk-Reconnect diese Initialisierung erreicht, bleibt getrennt offen. Die unten
stehenden offenen Punkte beschreiben den Stand vor dieser Fortsetzung.

## Ergebnis

**Ein alter Befehl ist durch Funkverlust weiterhin nicht nachweislich storniert.**
Neu sind konkrete, zum internen HCI-Ereignis „Disconnection Complete“ passende
Handler auf beiden Seiten. Sie setzen Verbindungszustände zurück. Die dort
geprüften direkten Schreibstellen löschen jedoch weder das separate
Ausstehend-Flag im Dongle noch den Sequenzvergleich und die Kalibriersicherung
im Controller. Ihre indirekten Folgen sind noch nicht vollständig geschlossen.

**Daraus folgt keine bewiesene Endlosübertragung.** Im Dongle gibt es einen
Verlustzweig, der eine Voraussetzung für die untersuchte Ausgabe löscht.
Ein Auftrag kann also im Speicher verbleiben, während diese Ausgabe aussetzt.
Ob er später wieder freigegeben oder durch einen anderen Reset verworfen wird,
ist die verbleibende entscheidende Frage. Ein anderer, bedingter Zweig führt
zu einem laut Firmwaretext beabsichtigten Soft Reset; dessen vollständige
Speicherwirkung ist noch offen.

**Auch ein automatischer RAM-Rückweg der Stickkalibrierung bleibt unbewiesen.**
Das Zurücksetzen einzelner Verbindungsfelder, das Nullsetzen von Arbeitsflächen
und das Wiederherstellen gesicherter Kalibrierwerte sind unterschiedliche
Vorgänge. Der explizite Exit bleibt der belegte Rückweg einer aktiven
Kalibrierung. Ohne angefordertes Finish startet der bereits untersuchte
Finalizer keinen neuen Speicherauftrag. Das bedeutet allein weder einen
RAM-Rollback noch, dass ein vorher übergebener Finish-Befehl verschwunden ist.

## Quellen und Prüfumfang

Verwendet wurden die unveränderten, lokal vorhandenen **DG144**- und
**DV209**-Dateien sowie der vorhandene isolierte statische Decoder.
`D = 0x62c0` bezeichnet die Dongle-RAM-Basis, `B = 0xf140` die Controller-Basis.
Codeadressen sind Dateioffsets. Herstellerdateien und vollständige
Disassemblierungen bleiben außerhalb des Repositorys.

Die bereits lokal vorhandene BlueZ-Referenz `hci.h` liefert unabhängig die
Ereignisnummern 3/5, die vier Byte lange Disconnect-Nutzlast und den
Scan-Befehl. Ihr Hash ist im Prüfbeleg festgehalten; kein Download erfolgte.
Die Übereinstimmung betrifft **interne Ereignisformate**, nicht den Nachweis,
dass der Benutzer gerade den Bluetooth-Modus statt des 2,4-GHz-Dongles nutzt.
Die konkrete Laufzeitroute und installierte Firmware wurden nicht abgefragt.

Kein Herstellerprogramm wurde ausgeführt oder emuliert; kein Netzwerk-, USB-,
Funk-, Input- oder SSH-Zugriff. Treiber und beide installierten Systeme bleiben
unverändert. Präzise Gyrokalibrierung und weitere Treiberdiagnose bleiben pausiert.

## 1. Dongle: Ereignis, Zustandswechsel und Ausgabesperre

Der Verteiler bei `0x8a06…0x8a22` liest das Ereignisbyte an Position 1.
Die Tabelle bei `0x8a24` führt Ereignis 3 nach `0x8a8c` und Ereignis 5 nach
`0x8b12`. Der zweite Handler prüft die zum HCI-Format passende Länge 4,
Status 0 und die zwei Handle-Bytes gegen `D+0x670`/`D+0x671`.
Das ist erheblich konkreter als eine Suche nach einzelnen „Disconnect“-Texten.
Die Herkunft jedes realen Funkverlusts in diesem Handler ist damit noch nicht
vollständig bewiesen.

Der begrenzte Handler `0x8b12…0x8b68`:

- löscht zunächst `D+0x1e4` und `D+0x1d0` und ruft `0x797c` auf;
- setzt nach erfolgreicher Länge-/Status-/Handle-Prüfung einen zuvor von null
  verschiedenen Zustand `D+0x13` auf 6;
- führt bei Zustand 0 stattdessen über `0x8ef0` zu einem anderen Reset-Kandidaten.

Der vollständig betrachtete kleine Helfer `0x797c…0x79a2` schreibt Parameter
ab absolut `0x66d6`, also **`D+0x416`**. Das ist ein anderer Speicherbereich
als `D+0x2d0` und die gehaltene Nutzlast `D+0xb64`.

Die Arbeitsroutine erkennt Zustand 6 bei `0xc6b4…0xc6b8` und verzweigt abhängig
von `D+0x238` und `D+0x16` weiter. Im Pfad über `0xc8c8…0xc8d0` wird
`D+0x13` gelöscht und `0x7960` aufgerufen. Dieser Helfer:

1. setzt **`D+0x1bc = 0`**;
2. übergibt den Deskriptor `0x1e12140` und Parameter 2 an `0x18950`.

Der Deskriptor bei Datei `0x12080` enthält **`0x0c1a`**, den HCI-Befehl
**Write Scan Enable**; Parameter 2 entspricht Page Scan. Das ist kein
HCI-Disconnect-Auftrag `0x0406`. Der Sender liest dessen 16-Bit-Opcode und
zerlegt ihn in zwei Ausgabebytes. Die vollständige untere Zustellung und alle
Antwortfolgen werden daraus nicht abgeleitet.

Die zwei untersuchten Ausgabezweige bei `0xc7bc…0xc7c0` und
`0xc84e…0xc852` überspringen ihre Arbeit, solange `D+0x1bc` null ist.
Der Folgezweig bei `0xc9be` prüft dasselbe Feld erneut. **In diesem Pfad wird
also eine Ausgabevoraussetzung entzogen, nicht nachweislich der Auftrag
storniert.** Das schließt untere bereits laufende Übertragungen oder andere
Firmwarepfade nicht global aus.

Zusätzlich bestätigt `0xc88a…0xc8a6` eine zweite Prüfung von Pending und
Wiederholungszähler. Auch sie vergleicht mit `0x64`, setzt den Zähler zurück
und führt zur Ausgabeentscheidung. Kein maximaler Versuchszähler oder
Gesamtzeitablauf wurde in diesen begrenzten Retry-Abschnitten nachgewiesen.
Die Zeiteinheit von `0x64` bleibt unbekannt.

## 2. Ein Soft-Reset-Zweig verhindert eine pauschale Aussage zur Lebensdauer

Andere Ausgänge des Zustands 6 rufen `0xa5da` mit einem gespeicherten
Moduswert auf. Dessen Tabelle wählt Protokollierungstexte für einen Soft Reset
mit USB-Moduswahl, darunter Vendor-Enumeration. Anschließend führt der Weg
über `0x6922` und `0x79fa` zum externen Ziel `0x20008c` im Dateiadressmodell.

`0x6922` bereitet einen vier Byte langen Datensatz bei **`D+0x2ac`** vor und
übergibt ihn weiter. Er überschreibt dabei nicht unmittelbar das Pending-Flag
bei `D+0x2d0`. Der Protokolltext stützt die Interpretation als beabsichtigten
Soft Reset; er beweist weder dessen Erfolg noch den Umfang der danach
neu initialisierten RAM-Bereiche.

**Offen bleiben der externe Reset und die nachfolgende Startinitialisierung.**
Ohne diese darf weder „der alte Befehl bleibt immer erhalten“ noch „jeder
Reconnect löscht ihn“ behauptet werden. Auch das vollständige Aus-/Einschalten
des Controllers, ein reiner Funkabbruch und das Abziehen des Dongles müssen
unterschieden werden. Sie sind keine austauschbaren Reset-Ereignisse.

## 3. Controller: Verbindungszustand ist nicht Kalibrierzustand

DV209 verwendet eine entsprechende Ereignistabelle bei `0xe4e8`, diesmal
mit Index `Ereignis − 3`. Ereignis 5 führt nach **`0xe656`**. Der Handler
prüft ebenfalls Länge 4, Status 0 und beide Handle-Bytes, hier gegen
`B+0x20bc`/`B+0x20bd`.

Danach unterscheiden mehrere Zustandstests den weiteren Weg. In den
untersuchten Abschnitten werden unter anderem die Wörter **`B+0x4b0`** und
**`B+0x4c4`** sowie in bestimmten Zweigen das Byte **`B+0x4b8`** gelöscht.
Diese Bereiche sind vom Sequenzbyte `B+0x50`, den Kalibrierflags
`B+0x1b3a…0x1b3c` und den beiden gesicherten Stick-Datensätzen getrennt.
Das sind belegte Teilrücksetzungen, kein Löschen des gesamten Controller-RAM.

Es existieren außerdem **nachgelagerte Nachrichten**:

- Der bedingt aufgerufene Helfer `0xd4de` meldet `0x400008` an `joypadtask`.
  Sein Protokolltext ordnet das der Speicherung von Kopplungsinformationen zu,
  nicht dem Finish der Stickkalibrierung.
- Ein weiterer Zweig ruft `0x98ba` mit 14 auf. Je nach weiteren Bedingungen
  erreicht er `0x9882`, das `0x40000b` an dieselbe Aufgabe sendet.

Diese Empfänger und ihre späteren Zustandswirkungen sind **noch offene
Kanten**. Die direkte Prüfung des HCI-Handlers reicht deshalb nicht, um
sämtliche RAM-Rücksetzungen oder einen indirekten Exit auszuschließen.

Auch der erfolgreiche Verbindungsaufbau wurde begrenzt verfolgt:
Ereignis 3 geht über `0xe514` bei Erfolg nach `0xe970` und erreicht weitere
Helfer/Zustände. Eine Operanden-/Parallelform bei `0xe976` ist in der
vorliegenden Ausgabe noch nicht zuverlässig zugeordnet. Dieser Abschnitt
wird ausdrücklich **nicht** als Beweis für erhaltene oder gelöschte Sequenzwerte
verwendet; eine Decoderkorrektur wurde hier nicht vorgenommen.

## 4. RAM-Rückweg: zwei Fehlzuordnungen vermeiden

Der frühere Kandidat `0xcf30 → 0x53f8` ist jetzt genauer eingegrenzt:
`0x53f8` referenziert USB-Resume-/SOF-Meldungen, verwaltet Felder ab `B+0xa24`
und richtet verzögerte Rückrufe ein. Dieser Befund gehört zur USB-Wiederaufnahme
und ist **kein Nachweis für eine Stick-Wiederherstellung nach Funkverlust**.

Außerdem ist bei `0x82f4` ein echter Arbeitsbereich-Reset gefunden:
Zwei jeweils `0x68` Byte große Bereiche ab `B+0x1b8e` und `B+0x1bf6` werden
geleert und mit Anfangswerten versehen. Darin liegen die zuvor identifizierten
Stick-Arbeitswerte. Dies ist aber **kein Zurückkopieren der Sicherung**.
Der untersuchte direkte Aufrufer bei `0xa612` liegt in einer umfangreicheren
Initialisierung; eine Verbindung vom Ereignis-5-Handler dorthin wurde nicht
nachgewiesen. Andere Aufruf-/Zeigerformen sind damit nicht ausgeschlossen.

Der bekannte explizite Exit holt bei noch aktiven Sticks die Sicherung über
`0x19b6`/`0x1a80` zurück. Ein bereits verarbeitetes Finish oder ein schon
übergebener Speicherauftrag wird dadurch nicht rückgängig gemacht. Diese
Aussagen aus dem [Kalibrierbericht](NEXUS_STICK_FIRMWARE.md) gelten unverändert.

## 5. Was wäre bei unbegrenzter Wiederholung?

| Voraussetzung | Konsequenz im bisher belegten Modell |
|---|---|
| Pending bleibt gesetzt, Ausgabe ist freigegeben, passende Antwort fehlt | Weitere Wiederholungen sind möglich. Eine Gesamtobergrenze ist in den geprüften Abschnitten nicht belegt. |
| Pending bleibt gesetzt, `D+0x1bc` wurde gelöscht | Die betrachteten Ausgabezweige werden übersprungen; gehaltene Daten sind nicht gleich fortlaufend gesendete Daten. |
| Befehl wurde schon verteilt und `B+0x50` behält dieselbe Sequenz | Der bekannte Filter überspringt eine erneute Verteilung und baut erneut Transportstatus `0x14` auf. |
| Befehl kam nie an oder der Vergleichswert wurde verändert | Bei erneutem Empfang kann eine andere Sequenz den Verteiler wieder erreichen. Weitere Kalibrierbedingungen gelten weiterhin. |
| Ein Reset verwirft Pending oder die Kopie | Dieser alte Auftrag kann über den geprüften Kopierpfad nicht unverändert weiterlaufen; ob/wann das tatsächlich geschieht, bleibt offen. |

Wiederholtes **Senden**, wiederholtes **Verteilen** und wiederholtes **Speichern**
sind drei verschiedene Aussagen. Keine davon darf aus der bloßen Existenz des
Retry-Zweigs als endloser realer Ablauf behauptet werden. Ein verspätetes Finish
bleibt ein zu klärender Fall, kein nachgewiesener Firmwarefehler.

Für die spätere Linux-Anwendung bleibt die einfache normale Bedienung
**Start → bewegen → bereit → Finish**, alternativ Exit. Die Firmware besitzt
die Speicherung; eine zusätzliche Persistenzbestätigung wird nicht gefordert.
Bei Verbindungsverlust muss die Anwendung ihre eigenen verzögerten Aktionen
stoppen und den Ablauf als unterbrochen markieren. Sie darf einen schon
übergebenen Finish-Befehl nicht als sicher storniert ansehen oder blind erneut
senden. Automatisches Start/Exit nach Reconnect bleibt ebenfalls unbelegt.
Ein solcher schreibender Ablauf wurde nicht implementiert.

## Prüfung und nächste offene Kanten

Der abschließende isolierte Decoderlauf besteht aus **40 begrenzten Bereichen
mit 542 Instruktionsdatensätzen**, ohne fehlgeschlagene Zeile in diesen Bereichen.
135 gehashte Anker, 24 unabhängig aus Operanden bestimmte Transferziele samt
24 veränderten Gegenbeispielen, vier Ereignistabellenziele samt vier veränderten
Gegenbeispielen und 60 Speicherbereichs-Abgrenzungen wurden geprüft. Die 16
bestehenden eigenen Dialogtests bleiben separate synthetische Tests.

Suchläufe trafen auch Tabellen, ungeeignete Startgrenzen und nicht unterstützte
Formen. Eine erfolgreiche begrenzte Dekodierung beweist keinen vollständigen
Kontrollfluss. Der doppelte Export von Parallelmitgliedern ist keine doppelte
Ausführung. Quellen und Decoder sind unverändert. Es gibt keine vollständige
Analyse sämtlicher Aliase, Instruktionsformen, indirekter Writer oder Bulk-Resets.

Die nächsten gezielten Schritte sind nun:

1. Dongle-Resetziel `0x20008c` und anschließende Speicherinitialisierung:
   Werden Pending, Kopie und Sequenz gelöscht oder erhalten?
2. Empfänger der Controller-Nachrichten `0x400008`/`0x40000b` und weitere
   Reconnect-Zustände: Erreichen sie die Stickflags, Sicherungen oder Exit?
3. Zuverlässige Operandenauflösung im erfolgreichen Verbindungszweig und
   Lebensdauer von `B+0x50`. Erst danach eine Aussage über späte Zustellung
   über einen vollständigen Reconnect treffen.

Die ältere Lücke zwischen Windows-Provider, USB-Modusauswahl und tatsächlich
aktivem Firmwarepaar bleibt separat bestehen. Keine Hardwarefreigabe oder
Garantie für einen zukünftigen Kalibrier-/Firmware-Updatepfad folgt aus dieser
statischen Untersuchung.
