# Stickkalibrierung: ausstehende Befehle bei Funkverlust

Stand: 21. Oktober 2026. Offline-Fortsetzung des
[USB-/Funkberichts](NEXUS_STICK_WIRE_PATH.md).
[Fundstellen, Quellenhashes und Prüfgrenzen](evidence/NEXUS_STICK_RECONNECT_20261021.json).
Keine Hersteller-App-/Firmwareausführung oder Emulation, kein Netzwerk- oder
Hardwarezugriff, keine Änderung am laufenden Treiber oder System.

Fortsetzung: Der [Rücksetzpfad-Bericht](NEXUS_STICK_RESET_PATHS.md) ordnet nun
interne Disconnect-Ereignisse und die getrennte Ausgabesperre zu. Der unten
noch offene Helfer `0x7960` fordert Page Scan an; `0x53f8` gehört zur
USB-Wiederaufnahme. Die vollständige Speicherlebensdauer bleibt offen.

## Ergebnis für die geplante Kalibrierung

**Der Dongle kann einen bereits gesendeten Befehl erneut übertragen lassen.**
Er behält dafür eine eigene Kopie. Neu identifiziert sind die passende
Transportantwort, das Löschen des Ausstehend-Flags im Dongle und ein
Sequenzfilter im Controller, der unmittelbar wiederholte Befehle abfängt.

**Ob ein alter Befehl einen tatsächlichen Funk-Reconnect überlebt, ist damit
noch nicht abschließend geklärt.** Die geprüften Warteschlangen-Resets löschen
nicht zugleich die separate Kopie. Überlebt sie den vollständigen Verlustweg
und wird das Senden wieder freigegeben, kann sie erneut in einen Funkrahmen
gelangen. Ob der Controller sie dann ausführt, hängt auch von seinem erhaltenen
Sequenz- und Kalibrierzustand ab. Weder eine tatsächlich beobachtete späte
Zustellung noch ein garantiertes Verwerfen wird hier behauptet.

**Ein Funkverlust ist weiterhin kein nachgewiesener automatischer Exit.**
Exit stellt bei noch aktiver Kalibrierung gesicherte Arbeitswerte im RAM wieder
her. Ohne Finish startet der untersuchte Abschlussweg keinen neuen
Speicherauftrag; dies setzt die durch Start veränderten RAM-Werte allein
nicht zurück. Bereits angefordertes Finish mit unklarer Zustellung ist von
„Finish wurde nie angefordert“ zu unterscheiden.

Die gewünschte einfache Bedienung bleibt **Start → bewegen → bereit → Finish**,
alternativ **Exit** bei Abbruch. Die Firmware übernimmt die Speicherung.
Eine zusätzliche Bestätigung dauerhafter Speicherung wird nicht als neue
Protokollanforderung eingeführt.

## Quellen und Grenzen

Untersucht wurden die unveränderten **DG144**-Dongle- und **DV209**-Controller-
Dateien aus dem vorhandenen Offline-Bestand. Adressen sind Dateioffsets;
`D = 0x62c0` und `B = 0xf140` bezeichnen die jeweiligen RAM-Bezugspunkte.
Die Zuordnung zur tatsächlich installierten Firmware beider Editionen ist
hier nicht geprüft. Proprietäre Dateien und vollständige Disassemblierungen
bleiben außerhalb von Git; veröffentlicht werden eigene Beschreibungen,
Adressen und Hashes.

Der vorhandene Decoder bleibt unverändert. Seine bekannten Grenzen bei
Parallelbefehlen und bedingten Blöcken gelten weiter. Insbesondere ist der
doppelte Export eines Parallelmitglieds keine zweimalige Ausführung. Für die
zwei entscheidenden einfachen Bedingungen wurden ursprüngliche Operanden,
Blocklänge und ausgegebene Guards gesondert gegengeprüft.

## 1. Drei unterschiedliche Dongle-Zustände

| Zustand | DG144-Feld | Bedeutung im untersuchten Weg |
|---|---|---|
| Wartende neue Nachrichten | Zeiger `D+0x2dc` | Noch aus der GIP-Warteschlange zu entnehmende Daten |
| Bereits entnommener Auftrag | Kopie `D+0xb64`, Länge `D+0x4a`, Sequenz `D+0x48` | Daten für eine mögliche erneute Ausgabe |
| Noch ausstehend | Flag `D+0x2d0` | Auswahl der gehaltenen Kopie statt einer neuen Nachricht |
| Ausgabe in diesem Durchlauf | Flag `D+0x2cc` | Freigabe des zweiten Funkblocks; nicht das Ausstehend-Flag |
| Wiederholungszähler | `D+0x118` | Schwellenprüfung im Ablauf; Zeiteinheit nicht nachgewiesen |

Bei einer neuen Nachricht (`0xa7f2…0xa844`) entnimmt `0x31e2` die Daten,
der Dongle kopiert sie in den separaten Puffer, erhöht die Sequenz und setzt
das Ausstehend-Flag. Die vorherige Analyse verbindet diese Queue mit dem
normalen GIP-Zweig für den Kalibrierselektor `0xfe`.

Ist der Auftrag noch ausstehend, verwendet `0xa7c6…0xa7f0` dieselben Daten,
dieselbe Länge und **dieselbe Sequenz** erneut. Der Zähler wird zurückgesetzt;
dieser Zweig erhöht die Sequenz nicht. Der Rahmenbauer erhält wieder den
`0xa0`-/Sequenzvorspann und die gehaltenen Nutzbytes.

Die Arbeitsroutine prüft bei `0xc814…0xc82a` das Ausstehend-Flag und den
Zähler gegen `0x64`. Ab dieser Schwelle gelangt sie zur Sendefreigabe bei
`0xc8dc…0xc8e8`; der betrachtete Folgezweig ruft Rahmenbau und Transport auf.
`0xc9b6…0xc9ba` löscht anschließend **nur die Durchlauf-Freigabe `D+0x2cc`**.
Das ist kein Nachweis für ein Löschen des ausstehenden Auftrags. `0x64` darf
ohne geklärten Takt weder als 100 Millisekunden noch als maximale Lebensdauer
des Befehls bezeichnet werden.

## 2. Transportantwort und Wiederholungsfilter

Nach den bereits beschriebenen Blockprüfungen und der `0xa0`-Kennung liest
DV209 bei `0xe244` die Sequenz aus dem zweiten Block und bei `0xe246` den
gespeicherten Vergleichswert `B+0x50`.

Die Bedingung bei **`0xe24a` lautet „ungleich“**. Nur dann werden die vier
folgenden Befehle ausgeführt: Sequenz speichern, Vorspann entfernen, Länge
verkürzen, GIP-Verteiler über `0xde2a` aufrufen. Bei gleicher Sequenz wird
dieser Teil übersprungen. Anschließend wird in beiden Fällen Status **`0x14`**
an den Antwortbauer `0xda96` gegeben. Ein Fehler des vorherigen Blockprüfwerts
führt dagegen über `0xe262…0xe26c` zu **`0x15`**.

Das erklärt einen sinnvollen Normalfall: Geht die Antwort verloren, kann der
Dongle denselben Auftrag wiederholen. Solange der Controller dessen Sequenz
noch gespeichert hat, führt er ihn hier nicht nochmals aus, antwortet aber
erneut. Das ist **keine globale Exactly-once-Garantie**: Sequenzüberlauf,
Neustart, Rücksetzen des Vergleichswerts und andere Zustandswechsel sind
damit nicht vollständig abgedeckt. Auch ein neuer Aufruf des GIP-Verteilers
beweist nicht, dass dessen Kalibrierbedingungen erfüllt sind.

Im Modus-1-Zweig des Antwortbauers liegen das niedrige Status-Nibble an
Position 8 und das hohe an Position 9. Die Felder 6/7 kommen aus konfiguriertem
Zustand `B+0x9cd`/`B+0x9cc`; ein weiterer Modus verwendet ein anderes Format.
Der Weg führt über `0xdb2a` in den unteren Transport. Dessen Zustellerfolg und
die Laufzeitwerte der Kopffelder werden hier nicht vorausgesetzt.

Auf der Dongleseite verlangt der passende Empfangszweig `0x9144…0x915e`
unter anderem Byte 6 = `0x4e`, Byte 7 = 0 und den passenden Nachrichtenzweig.
Tabelleneintrag 0 bei `0x9160` führt nach `0x9398`. Dort wird der Status aus
den Nibbles rekonstruiert. **Nur bei `0x14`** löscht der einfache bedingte
Block `0x93ac…0x93b6` das Flag `D+0x2d0`. `0x15` führt in einen getrennten
Protokollierungszweig; dieser begrenzte Zweig löscht das Flag nicht.

Damit sind die zusammenpassenden Antwortstrukturen und ihre lokalen Wirkungen
belegt, unter den genannten Kopf-/Modusbedingungen. Die vollständige
Zuordnung einer Antwort zu einer Sitzung und der tatsächliche Funkweg bleiben
offen. Im begrenzten `0x14`-Handler ist kein Vergleich mit der A0-Sequenz sichtbar;
daraus folgt ohne die vorgelagerte Zuordnung kein nachgewiesener Fehler.

Diese Antwort bestätigt **keine dauerhafte Kalibrierungsspeicherung**. Sie wird
auch für ein herausgefiltertes Duplikat erzeugt und hängt nicht an einem
nachgewiesenen erfolgreichen Speicherabschluss.

## 3. Was die geprüften Rücksetzpfade tatsächlich löschen

Für einen gültigen Queue-Zeiger setzt der vollständige kleine Helfer
`0x699a…0x69ae` die beiden Wörter bei `Queue+4` und `Queue+8` sowie das Byte
bei `Queue+0x10` auf null. Er erhält den Zeiger auf das Queue-Objekt, nicht
auf die separate Kopie `D+0xb64`. Bei einem Nullzeiger existiert ein eigener
Fehleraufruf; er wird nicht als normaler Reset interpretiert.

Der Moduswechsel-Abschnitt `0x8094…0x80b4` ruft diesen Helfer für die Queues
`D+0x2dc`, `D+0x2e0` und `D+0x2e4` auf. Weitere solche Aufrufe finden sich
im begrenzt geprüften Abschnitt `0xba3c…0xba6e`. **Das Leeren dieser Queues
allein setzt weder das separate Ausstehend-Flag noch dessen Kopie zurück.**
Andere Aufrufe, spätere Reset-/USB-Ereignisse und ganze Speicherinitialisierungen
können zusätzliche Wirkungen haben; der vollständige Pfad ist nicht geschlossen.

Ein weiterer Kandidat ist `0x7960…0x7978`: Er löscht `D+0x1bc` und verzweigt
in die Nachrichtenvermittlung `0x18950`. Ein Aufrufer bei `0x8a94` liegt im
protokollierten Verbindungsfehler-/Reconnect-Zweig. Die direkten Schreibstellen
löschen den ausstehenden Auftrag nicht; indirekte oder spätere Empfänger der
Nachricht sind damit jedoch nicht ausgeschlossen. Ein HCI-Disconnect-
**Befehlsverteiler** ist ebenfalls kein Beweis für den gesamten Funkverlust-
**Ereignisweg**. Diese beiden Rollen wurden nicht gleichgesetzt.

## 4. RAM-Rückweg im Controller

Neu begrenzt verfolgt wurden ein zählerabhängiger Abschnitt bei
`0x7ffa…0x80a2` und ein unterer Zustandsabschnitt bei `0xcf06…0xcf38`.
Beide können den schon untersuchten Helfer `0x4820` erreichen. Dieser kleine
Helfer ruft keinen der bekannten Stick-Restore-Helfer auf und schreibt nicht
die Kalibrierflags `B+0x1b3a…0x1b3c`.

Die untersuchten direkten Zustandslöschungen sind daher **noch kein RAM-Exit**.
Die genaue Bedeutung ihrer Auslöser sowie weitere aufgerufene Helfer,
Nachrichtenempfänger und Schlaf-/Neustartfolgen bleiben offen. Daraus wird
weder „RAM bleibt bei jedem Funkverlust unverändert“ noch „es wird immer
automatisch wiederhergestellt“ abgeleitet.

Der belastbare bekannte Rückweg bleibt der explizite Exit für aktive Sticks,
wie im [Firmwarebericht](NEXUS_STICK_FIRMWARE.md) beschrieben. Er nimmt keine
bereits abgeschlossene Kalibrierung und keine eingereihten Speicheraufträge
zurück. Ein späterer Start mit Laden gespeicherter Records ist außerdem ein
anderer Vorgang als ein sofortiger RAM-Rollback beim Funkverlust.

## 5. Können alte Befehle nach dem Reconnect noch ankommen?

| Fall | Was sich derzeit sagen lässt |
|---|---|
| Befehl angenommen, nur Antwort verloren; Sequenz bleibt erhalten | Wiederholung wird im geprüften Controllerzweig nicht nochmals verteilt; erneute Antwort wird aufgebaut. |
| Befehl bisher nicht angenommen; Kopie und Freigabe überleben den Verlust | Er kann erneut formatiert werden. Bei anderer Sequenz und passenden Zustandsprüfungen kann der Controller ihn später verteilen. Ob genau dieser Gesamtpfad beim realen Reconnect eintritt, bleibt offen. |
| Queues geleert, separate Kopie bleibt ausstehend | Queue-Reset allein reicht nicht als Beleg für Stornierung. |
| Kompletter Reset verwirft Kopie/Flag oder ändert Empfängerzustand | Das Ergebnis hängt vom noch ungeklärten vollständigen Resetpfad ab; keine pauschale Zustell- oder Verwerfgarantie. |
| Exit angefordert, Verbindung weg | Anforderung ist kein Beleg, dass der RAM-Rückweg erreicht wurde. |

Für die spätere Linux-Anwendung folgt daraus: Bei Geräteverlust eigene
verzögerte Aktionen stoppen und die Sitzung als unterbrochen kennzeichnen.
Ein bereits übergebener Auftrag lässt sich durch Schließen des Dialogs allein
nicht als zurückgenommen behandeln. Nach Reconnect weder Finish blind
wiederholen noch ohne Zustandsprüfung Start/Exit nachsenden. Ein tatsächlicher
Abbruch- oder Neuaufnahmeweg muss erst an die geklärten Gerätebedingungen
gebunden werden. Hier wird kein solcher schreibender Pfad implementiert.

## Prüfung und nächster gezielter Schritt

Der abschließende isolierte Decoderlauf umfasst **22 begrenzte Bereiche und
331 Instruktionsdatensätze**, ohne fehlgeschlagene Zeile in diesen Bereichen.
Geprüft wurden 95 gehashte Anker, 15 unabhängig aus den Operanden bestimmte
Sprung-/Aufrufziele samt 15 veränderten Gegenbeispielen, zwei einfache
Bedingungsblöcke samt vier veränderten Gegenbeispielen, der Tabelleneintrag
und 256 eigene Statusfeld-Geometrien. Die Bedingungen wurden gegen die lokale
Grammatik geprüft; das ist kein neuer unabhängiger ISA-Nachweis. Die 16
bestehenden synthetischen Dialogtests bestanden ebenfalls.

Suchläufe trafen auch ungeeignete Startgrenzen, Tabellen und nicht dekodierte
Formen. Diese zählen nicht als vollständige Codepfade oder Erfolge. Alle
Herstellerdateien und der Decoder blieben unverändert. Es wurde keine
Firmware ausgeführt oder emuliert und kein neuer Hardwaretest vorgenommen.

Die nächste konkrete Lücke ist der **vollständige Verlust-/Wiederanlaufweg**:
Wer schreibt oder löscht `D+0x2d0`, dessen Kopie und `B+0x50` bei welchem
Ereignis, einschließlich indirekter Rücksetzungen? Parallel bleibt die
Verknüpfung eines tatsächlichen Funkverlusts mit den aktiven Stickflags und
Restore-Helfern offen. Die bereits belegte Transportantwort und die getrennten
Puffer müssen dafür nicht erneut von vorn untersucht werden.
