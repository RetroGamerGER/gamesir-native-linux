# Eigenständiger Start: implementierter Offline-Ablauf

12. Oktober 2026, Grundlage `4a6dbea`. `src/gs_startup.c` implementiert den
Startablauf als transportfreien C-Baustein. Er verwendet die bestehenden
Paketfunktionen aus `gs_protocol.c`; die Kernel-Runtime bleibt separat erhalten.
Der Baustein erzeugt genau begrenzte Sendeaufträge und verarbeitet deren
Bestätigungen sowie Geräteereignisse. Er öffnet und bindet keine Geräte.

**Offline implementiert und getestet; noch kein eigenständiger Hardwarestart.**
Dieser Bericht beschreibt den Offline-Kern aus `1e17784`. Die anschließende
[Kernelanbindung](NATIVE_STARTUP_KERNEL.md) ergänzt inzwischen einen expliziten
Startaufruf und Probe/Disconnect. Der neue Build wurde nicht geladen;
keine Systemkonfiguration oder Autoload eingerichtet. Der ältere
hardwaregeprüfte Modulbuild bleibt gesichert.

## Verwendete Belege

Die kleine Datei `fixtures/startup-capture.json` enthält ausschließlich
Zielgerätepakete aus zwei getrennten Aufnahmen, mit Originalhashes und
Submit-/Completion-Frameverweisen. Absolute Zeiten, USB-Adressen,
URB-Zeiger und fremder Busverkehr sind nicht enthalten.

| Abschnitt | Beleg | Beobachtung |
|---|---|---|
| 100a→109c | Sprint-002-Original `4045577a7a9e7a1a0f84307a45e96fd524cd7dea1d4af276ebd7db20a0994a89` | Neun erfolgreiche vollständige Acht-Byte-Transfers an IF0/EP02; fünf Wörter und vier Flush-Pakete. |
| Abstände | Derselbe Mitschnitt | Nächster Submit jeweils 20.076–20.085 µs nach vorheriger Completion. |
| Neuanmeldung | Gespeicherte Ereignisse am physischen Port | Alte Instanz entfernt ca. 420,050 ms, neue 109c-Instanz vorhanden ca. 1.939,908 ms nach erstem Übergangs-Submit; begrenzte Genauigkeit der Host-Zeitzuordnung. |
| Native Initialisierung | Motorvergleich `ec53d79ba5ee46ccefb4df2cc1b6c67c0d083eafdf6e1d3a52258e80a338d998` | Drei GIP-Initialisierungen und drei Heartbeats; Sequenzen 1–6, vollständige erfolgreiche Transfers. |
| Bereitschaft | Derselbe native Mitschnitt | IMU bereits zu Beginn, erster GIP-Eingabebericht erst nach ca. 22,391 s. Ein ruhender Controller darf nicht allein wegen fehlender GIP-Eingaben als ausgefallen gelten. |

Beide Originaldateien wurden bei der neuen Extraktion vollständig auf SHA256
geprüft. Der Replay verbindet die beiden Abschnitte **künstlich**. Das ist keine
Aufzeichnung eines durchgängigen Starts ohne Deadband und kein Nachweis, dass
die zusammengestellte Folge bereits auf Hardware genügt. Insbesondere war
der native Mitschnitt durch Deadband vorbereitet; die sofortige IMU-Ausgabe
kann deshalb keinen unabhängigen Kaltstart beweisen.

Zusätzliche Quellen: die bereits gespeicherte Deadband-Version `771b28a`,
`vendors/gamesir/models/g7pro/protocol.py:453–483` und `reader.py:41–42,660–730`.
Sie belegen Paketfolge, 20-ms-Pausen, fünf Sekunden nach Enumeration und zehn
Sekunden Warten auf Neuanmeldung. `reader.py:735–810` zeigt drei anfängliche
Heartbeats und anschließende Wartung; es wurde keine Drittsoftware ausgeführt.
Der G7-Lesepfad enthält zusätzlich Informationsabfragen. Diese werden nicht
ohne Beleg ihrer Notwendigkeit in den nativen Start übernommen.

## Implementierte Zustandsfolge

| Zustand | Verhalten und Freigabebedingung |
|---|---|
| IDLE → TRANSITION | Genau ein ausdrücklich aktivierter Versuch; bestätigter exklusiver Besitz von 3537:100a/IF0, passende Deskriptoren, gültiger Port- und Instanztoken. Mindestens fünf Sekunden seit Enumeration abwarten. |
| TRANSITION | Neun Pakete mit `gs_transition`; immer nur ein ausstehender Auftrag. Weiter erst nach erfolgreicher vollständiger Completion und mindestens 20 ms Pause. |
| WAIT_REMOVE | Alle neun Transfers abgeschlossen; keine weiteren 100a-Pakete. Auf Entfernen genau der alten Geräteinstanz warten. |
| WAIT_ADD | Maximal zehn Sekunden ab letzter Übergangs-Completion für Entfernen und Neuanmeldung zusammen; der Timer wird durch neue Ereignisse nicht verlängert. |
| INITIALIZE | Nur die neue 3537:109c-Instanz am ausgewählten Port, IF0 und exklusiver Besitz werden angenommen. Drei GIP-Init-Pakete und drei Heartbeats, je mindestens 50 ms nach Completion. |
| VERIFY | Nach abschließenden 50 ms Pause frische gültige 64-Byte-IMU verlangen. Während des begrenzten Wartens nur Heartbeats im Abstand von 450 ms. |
| READY → HANDED_OFF | Einmalige Übergabe des Sequenzzählers, der nächsten Heartbeat-Frist und der getrennten IMU-/Gamepad-Nachweise an den späteren Runtime-Adapter. Danach erzeugt der Startbaustein keine Pakete mehr. |
| FAILED | Ersten Fehler erhalten; keine weiteren Sendeaufträge, keine Wiederholung, kein eigener Wiederherstellungsbefehl. |

`READY` bedeutet erfolgreiche Initialisierung plus frische rohe IMU-Telemetrie.
Ein tatsächlich empfangener GIP-Bericht wird mit `pad_seen` getrennt erfasst.
Gerätezuordnung, abgeschlossene USB-Transfers und beide Datenströme bleiben
getrennte Nachweise. IMU vor Abschluss der Initialisierung reicht nicht aus;
eine kurze IMU-Pause startet weder Erkennung noch Moduswechsel erneut.
Ein Ablauf der IMU-Prüffrist bedeutet fehlende Startbereitschaft: Gerätekennung,
Instanz und `failed_stage=VERIFY` bleiben für die Diagnose erhalten. Das ist
keine Aussage, dass die USB-Identität verloren gegangen ist. Diese begrenzte
Startprüfung legt noch keine Ausfallpolitik für späteren Dauerbetrieb fest.
Die bestehende Runtime akzeptiert anschließend GIP und IMU, aber keine
100a-XInput-Pakete im 109c-Modus. Sensorwerte werden dabei nicht neu skaliert.
Die geprüften Bestätigungen sind erfolgreiche vollständige USB-Completions.
Ein zusätzlicher eindeutiger Firmware-ACK für die ganze Initialisierung ist
noch nicht belegt; die unbekannten Typ-03-Berichte werden nicht dazu erklärt.

250 ms pro Transfer entsprechen der vorhandenen Kernel-Timeoutgrenze.
30 s Gesamtfrist sowie jeweils höchstens 3 s für Initialisierung und
anschließende IMU-Prüfung sind **gewählte Offline-Testgrenzen**, keine gemessenen
Firmwaregarantien. Frische IMU: höchstens eine Sekunde alt. Alle Fristen nutzen
eine monotone Mikrosekundenzeit und sind gegen Überlauf/rückläufige Zeit geprüft.
Verspätete Aufrufe verschieben die übergebene Heartbeat-Frist nicht nach hinten.

## Gerätezuordnung und Fehlerverhalten

Port und Geräteinstanz sind zwei getrennte, vom späteren Adapter vergebene
Tokens. Eine Busadresse ist kein Identitätsnachweis und gehört nicht zur API;
sie darf nach Neuanmeldung auch wiederverwendet werden. Der Instanztoken muss
jedoch neu sein, und die neue Enumeration darf nicht vor dem beobachteten
Entfernen liegen. Ereignisse anderer Ports lösen keine Übernahme aus.

**Kein fest verdrahteter Anschluss:** `gs_boot_supported()` erkennt die
unterstützten VID/PID-/IF0-Deskriptoren unabhängig vom Anschluss und vom
Besitzstatus. Erkennung allein startet keinen Übergang. `8-6` bleibt ausschließlich
die Auswahl der bisherigen Hardwaretests. Jeder ausgewählte Dongle erhält
einen eigenen Koordinator, Sequenzzähler und Fristen. Der später aus Linux-
Probe-Ereignissen erzeugte Topologietoken muss Root-/Hub-Lebensdauer und den
vollständigen Anschluss berücksichtigen; weder eine Busnummer noch ein
gekürzter Hub-Pfad oder ein ungeprüfter Hash genügt. Die Vergabe dieser Tokens
und Linux-Probe/Disconnect sind inzwischen im [Kerneladapter](NATIVE_STARTUP_KERNEL.md)
implementiert und mit künstlichen Geräteobjekten geprüft.

Der Übergang reserviert genau den dynamisch ermittelten Anschluss für seine
Frist. Eine passende 109c an einem anderen Anschluss wird nicht übernommen.
Ohne eindeutige UID lässt sich deren Ankunft nicht sicher als Umstecken
gegenüber einem zweiten Dongle unterscheiden: Der alte Versuch läuft spätestens
in seine ursprüngliche Frist, die neue Instanz wird unabhängig erkannt. Ein
anderes Gerät verkürzt oder verlängert die Frist nicht. Ein bekannter Abbruch
kann den alten Versuch sofort beenden. Keine automatische Wiederholung.
Ein neuer 100a-Versuch benötigt eine neue Sitzung und eigene Aktivierung;
eine unzugeordnete 109c wird erkannt, aber nicht auf Verdacht initialisiert.

Nach erfolgreicher Übergabe entfällt die Übergangsreservierung; die Runtime
bleibt an genau ihre neue Geräteinstanz gebunden. Beim Abziehen endet diese
Sitzung. Wiederanmeldung am selben oder einem anderen Anschluss ist eine neue
Enumeration. Root-/Hub-Ersatz darf trotz gleicher Pfadzeichenfolge nicht den
alten Topologietoken wiederverwenden. Ohne authentifizierbare UID kann auch ein
unbemerkter physischer Austausch durch einen identischen Dongle am selben
Port im erwarteten Zeitfenster nicht grundsätzlich ausgeschlossen werden.
Die Zuordnung ist eine kontrollierte Topologiezuordnung, keine kryptografische
Geräteauthentifizierung.

### Gespeicherter Seriennummernbefund

Die Aufzeichnungen enthalten unter beiden PIDs einen echten USB-Stringindex
`iSerialNumber=3` und einen ausgegebenen Seriennummernstring. Die Kernelmeldungen
und `ID_SERIAL_SHORT` stimmen innerhalb des jeweiligen Modus überein:

| Modus | Beobachteter Seriennummernstring | Bewertung |
|---|---|---|
| 3537:100a | 10 Zeichen | In den ausgewerteten Logs gleichbleibend. |
| 3537:109c | 16 Zeichen | In den ausgewerteten Logs gleichbleibend, anderer Wert als unter 100a. |

Es sind zwei unterschiedliche Werte, keine gemeinsame USB-Seriennummer über
den Moduswechsel. Ihre weltweite Eindeutigkeit, Zuordnung zu Dongle oder
Funkcontroller und Stabilität nach anderem Pairing sind nicht belegt. Eine
Produktkennung oder das zusammengesetzte `ID_SERIAL` ist ebenfalls keine UID.
Der Startbaustein verwendet deshalb keine Seriennummer als Zuordnungskriterium.
Die konkreten Werte bleiben in den privaten Logs; der Prüfbericht enthält
deren Dateihashes und Befunde. Geprüft wurden ausschließlich gespeicherte
Kernel-/udev-Daten aus Sprint 002 und dem nativen Motorvergleich, keine Geräte.

Vor Sendeauftrag, Completion, Eingabeannahme und Runtime-Übergabe werden
Identität und exklusiver Besitz geprüft. IF0-Deskriptoren entsprechen den
gespeicherten Konfigurationen: 100a `ff/5d/01`, 32-Byte-Endpunkte; 109c
`ff/47/d0`, 64-Byte-Endpunkte; Interrupt EP02/EP82 und Alternative 0.
Die Tokens und das Besitzflag sind ein Vertrag mit dem Adapter, keine vom
portablen Kern selbst ausgelesenen oder authentifizierten Hardwaremerkmale.

Fehlerhafte/kurze Transfers, falsche Completion-Tokens, alte Geräteinstanzen,
PID 109b, Rückkehr zu 100a statt erwarteter 109c-Enumeration, Besitzerverlust,
unerwartetes Entfernen, fehlende IMU, falsche Endpoint-/Paketformen,
rückläufige Zeit und Fristüberschreitungen stoppen den Versuch. Auch ein
Disconnect während eines noch unbestätigten letzten Übergangspakets gilt
konservativ als Fehler; eine neue Identität ersetzt keine fehlende Completion.

Vollständige unbekannte Typ-03-Berichte zählen nicht als IMU-Bereitschaft.
Eine während des Starts angeforderte Guide-Bestätigung stoppt derzeit mit
`EOPNOTSUPP`: Dieser nicht aufgezeichnete Nebenpfad wird nicht still ignoriert
und bekommt keinen unkoordinierten zweiten Sequenzschreiber. Der bestehende
Guide-Pfad der normalen Kernel-Runtime bleibt erhalten.

Bei Fehler/Abbruch bleibt gespeichert, ob der Übergang abgeschlossen war und
ob native OUT-Aufträge bereits erzeugt wurden, außerdem die Fehlerphase.
Der spätere Adapter muss eigene
ausstehende URBs beenden und seinen Besitz geordnet aufgeben. Ein terminaler
Softwarezustand behauptet keine wiederhergestellte xpad-Bindung.

## Prüfung und nächste Anbindung

```sh
make test-startup
make test
```

Die Tests übersetzen den tatsächlichen C-Baustein mit ASan/UBSan. 15 gespeicherte
Sendeaufträge werden bei ihren aufgezeichneten relativen Zeiten bytegenau
reproduziert. Zusätzlich 75 Fehlerfälle an jeder der 15 Sendestellen sowie
Deskriptor-/Besitz-/Neuanmeldungsfehler, Abbruch, Fristen, fehlende/stale IMU,
ruhendes Gamepad, falsche Eingabemodi, Sequenzübergabe und doppelte Aufrufe.
Vier frei gewählte Topologietokens repräsentieren zwei direkte Anschlüsse
und Hub-Anschlüsse an zwei Roots; je zwei Koordinatoren laufen gleichzeitig.
Getestet sind fremde Ankunft/IMU, Umstecken, neue Sitzung nach Wiederanmeldung,
geänderter Hub-Lebensdauertoken, verzögerte IMU und eine IMU bereits vor Ende
der Initialisierung. Das simuliert den Adaptervertrag, **keine echte
Linux-Hub-Erkennung**. Die bisherige Hardwaretest-Portbegrenzung bleibt erhalten.
Alle Grundtests bestehen; Clang Static Analyzer meldet für den Startbaustein
keinen Befund. [Prüfbericht und Quellhashes](NATIVE_STARTUP_OFFLINE_RESULTS.json).

Der folgende [Implementierungsschritt](NATIVE_STARTUP_KERNEL.md) hat
Kernel-Probe/Disconnect und einen ausdrücklich aktivierbaren Startzugang
ergänzt. Er erhält den Koordinator über die Neuanmeldung, leitet die
Zuordnung aus Kernelobjekten ab und kontrolliert IF0-Besitz sowie die
einmalige Initialisierung. Der bestehende START-Pfad darf nach
Übergabe nicht nochmals die sechs Initialisierungspakete senden oder den
Sequenzzähler zurücksetzen. Der begrenzte Sitzungs-/STOP/END-Pfad bleibt dabei
die Grundlage; eigenständiger Start und Dauerbetrieb sind getrennte Schritte.

Ein späterer Hardwaretest braucht weiterhin neue konkrete Freigaben und den
Rückweg nach dem gespeicherten xpad-Verfahren. Erst dieser Test kann zeigen,
ob die Initialisierung ohne vorherige Deadband-Sitzung vollständig ausreicht.
