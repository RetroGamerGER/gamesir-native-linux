# TMR-Kalibrierung: USB-Paket und Empfangspfad

Stand: 22. Oktober 2026. Ausschließlich statische Offline-Analyse.
[Fundstellen und Prüfung](evidence/TMR_USB_FRAMING_20261022.json).
Fortsetzung der [nativen Schnittstelle](TMR_NATIVE_INTERFACE.md) und des
[Nexus-/Funkpfads](NEXUS_STICK_WIRE_PATH.md).

## Ergebnis

**Der vorhandene Linux-Testentwurf ist vollständig beschreibbar und durch den
untersuchten Firmware-Empfangspfad gestützt.** Die zuvor offene Dongle-Kante
vom USB-Endpunkt zum GIP-Zweig ist jetzt zugeordnet: Interrupt OUT `0x02`,
64-Byte-Konfiguration, Callback `0x94e`, tatsächlich gelesene Länge und Kopie
in die zweite Funkwarteschlange. Für `0x0f/0xfe` erreichen die Nutzbytes den
bekannten Start-/Finish-/Exit-Verteiler des Controllers.

Das ist **kein Mitschnitt des von Windows erzeugten Originals**. Nexus gibt
drei Nutzbytes an einen externen Windows-GIP-Provider; dessen Implementierung
liegt nicht im untersuchten App-Paket. Seine exakte USB-Transferlänge,
Auffüllung und Sequenzauswahl bleiben unbeobachtet. Der folgende Rahmen ist
eine vollständig festgelegte, empfängerseitig gestützte Linux-Rekonstruktion.
Hardwarezustellung und erfolgreiche Kalibrierung sind noch nicht bestätigt.

Treiber, Manager, GUI, installierte Pakete und AppImage bleiben unverändert.
`experimental_tmr` bleibt aus. Keine Hersteller-App oder Firmware ausgeführt
oder emuliert, kein Netzwerk- oder Gerätezugriff, keine Aktivierung. Präzise
Gyrokalibrierung und die zurückgestellte untere Funkanalyse bleiben pausiert.

## 1. Vollständiger Linux-Testentwurf

Ein einzelner **64-Byte-Interrupt-OUT** an Endpunkt `0x02` der bereits nativ
übernommenen G7-Pro-Schnittstelle. Kein HID-Report-ID-Präfix, kein Control-
Transfer und kein eigener Funkrahmen vor den folgenden Bytes:

| Byte | Inhalt | Beleg / Einordnung |
|---|---|---|
| 0 | `0f` | Nexus-Nachrichtentyp und Firmwareprüfung |
| 1 | `00` | Der Controller-Kalibrierparser verlangt null |
| 2 | `seq` | Gemeinsamer nativer Sequenzzähler; im betrachteten FE-Pfad kein Funk-Duplikatschlüssel |
| 3 | `03` | Drei Nexus-Nutzbytes als kurzes GIP-Längenfeld; lokal fixierte xone-Referenz, kein beobachteter Windows-Header |
| 4 | `fe` | Nexus-Selektor und Controller-Verzweigung |
| 5 | `00`, `01`, `02` | Start, Finish, Exit |
| 6 | `03` bei Start; sonst `00` | Beide Sticks; Nexus übergibt bei Finish/Exit keine neue Teilmaske |
| 7–63 | 57 Nullbytes | Gewählte native Auffüllung; der untersuchte FE-Verteiler liest die Befehlsfelder nur bis Byte 6 |

Beispiele mit Sequenz `01`; **jeweils mit genau 57 weiteren Nullbytes**:

```text
Start:   0f 00 01 03 fe 00 03  + 57 × 00
Finish:  0f 00 01 03 fe 01 00  + 57 × 00
Exit:    0f 00 01 03 fe 02 00  + 57 × 00
```

Damit sind logische Nutzlänge **3** und USB-Transferlänge **64** getrennt.
Byte 3 ist nicht `40` oder `3c`; `3c` gehört zur eingehenden E0-Meldung.
`gs_tmr_packet()` erzeugt bereits genau diesen Entwurf und wurde nicht geändert.

Die Firmware beweist nicht, dass Windows genau 64 Bytes und diese Auffüllung
sendet oder dass kürzere Transfers grundsätzlich unmöglich sind. Ihr Leser
fordert bis zu 64 Bytes an und zählt empfangene Bytes. Der gewählte volle
Transfer passt dazu; Kurztransfer-/Zeitabläufe sind nicht hardwarevalidiert.

## 2. Nexus-Nutzinhalt und Grenze zum Windows-Provider

In `HJC.GameSir.Nexus2_0.dll` allokiert RVA `0x198b563` ein Array der Länge
drei. RVA `0x198b578` setzt `fe`, `0x198b581` die Operation und `0x198b584`
die Teilmaske. RVA `0x198b5a5` setzt Nachrichtentyp `0f`; `0x198b5be`
wählt den direkten Sendeweg. Diese Stellen wurden erneut am Original geprüft.

D4X RVA `0x1bf8…0x1c06` reicht Datenzeiger, Länge, Typ und einen Nullparameter
an Provider-Slot 6 weiter. Der Wrapper erzeugt dort keinen USB-Kopf und keine
USB-Prüfsumme. Dem Nullparameter wird kein ungeprüfter Enum-Name gegeben.
Providerzuordnung und HRESULT-Prüfung aus dem
[vorherigen Bericht](NEXUS_STICK_TRANSPORT.md) bleiben erhalten.

Die fehlende Windows-Schicht wird nicht durch die Behauptung ersetzt, Nexus
sende nachweislich genau unsere 64 Bytes. Ein eigener Rahmen lässt sich aber
anhand der bekannten Empfänger begründen.

Zusätzliche **bereits lokal gespeicherte** Primärreferenz:
[xone `bus/protocol.c`, Commit `3484f603`](https://github.com/medusalix/xone/blob/3484f603484782dd7551c64e5a33fc602b127051/bus/protocol.c),
SHA256 `08bc9980acdf3346a6ca5fda9a0e5ca1a87deb1ec44e1d00e356bfb2ec1a235d`.
Kein neuer Download, Import, Ausführen oder Kopieren von Drittcode.
`gip_encode_header()` (Zeile 244) schreibt Typ, Optionen, Sequenz und eine
variable Nutzlänge. Bei Länge drei und ohne Chunk-Option sind das vier
Kopfbytes, das Längenbyte ist `03`; es ist kein erweitertes Längenfeld nötig.
`GIP_OPT_ACKNOWLEDGE` ist Bit 4: Option null fordert diese GIP-Quittierung
nicht an und passt zur Nullprüfung des GameSir-Kalibrierparsers.

Die Referenz vergibt ebenfalls positive Sequenzen und setzt ihre tatsächliche
generische Sendelänge auf Kopf plus Nutzlänge, hier sieben. Sie beweist somit
**keine universelle 64-Byte-Auffüllpflicht** und keine Windows-Implementierung.
Die 64-Byte-Wahl bleibt die getrennte, von unserem GameSir-Empfangspfad und
bisherigen nativen Wartungstransfers gestützte Transferentscheidung.

## 3. Dongle: Endpunkt, Modus, Länge und Kopie

Dateioffsets zunächst in **DG144**, `D = 0x62c0`.
Codezeigerabbildung: `0x01e000c0 + Dateioffset`.

| Schritt | Fundstelle | Aussage |
|---|---|---|
| Modusbasis | Literal `0x4a44`, Zugriff `0x4c2c` | Konfiguration verwendet D und Modusfeld `+3` |
| GIP-Modus wählen | `0x4c46`, `0x4ca0…0x4cde` | Modus `10` erreicht die Konfiguration ab `0x4e44`; andere Zweige nicht pauschal übernehmen |
| Callback vorbereiten | `0x4cbe` | Zeiger `0x01e00a0e` entspricht Datei `0x94e` |
| Endpunkt konfigurieren | `0x4e4c…0x4e76` | Größe `40`, OUT `02`, Typwert 3, Callback und Puffer; Aufruf `0x15d0` |
| Puffer / Empfang lesen | `0x95c`, `0x964` | Endpunktpuffer über `0x104`, Lesen über `0x31e` |
| Empfangslänge | `0x31e…0x332`, `0x270…0x31c` | Leser mit 64-Byte-Grenze; Längenbytes aus dem USB-Registerweg werden aufsummiert und zurückgegeben |
| Endpunkt / GIP-Modus | `0x96c`, `0xa4c` | OUT 2 und D+3=`10` führen zum allgemeinen GIP-Zweig |
| Kalibrierselektor | `0xb2a…0xb32` | Typ `0f`, Byte 4 ungleich `f0`, somit auch `fe` → `0xbca` |
| Warteschlange | `0xbca…0xbd4` | Ursprünglicher Puffer und tatsächliche Empfangslänge an `0x680`; Queuezeiger D+`2dc` |
| Bytekopie | `0x680…0x6ce` | Queue-Längenpräfix, danach unveränderte Nachrichtenbytes; kein neuer USB-Kopf |

Im `0f/fe`-Zweig wird **Paketbyte 3 nicht als USB-Kopierlänge verwendet**.
Die vier USB-Kopfbytes bleiben Bestandteil der Nachricht. Ein voller Transfer
gibt somit alle 64 Bytes an den bekannten Funkblock weiter. Queuekapazität,
Zustand und Funkverbindung bleiben Laufzeitbedingungen; USB-Erfolg bestätigt
sie nicht automatisch. Nachbarzweige und Tabellenbytes sind kein Ersatzbeleg
für den nativen Weg.

## 4. Controller und Rückmeldung

Im [zweiten Funkblock](NEXUS_STICK_WIRE_PATH.md) ergänzt der Dongle bei
`0xa82e…0xa844` `a0` und eine **eigene Funksequenz**. Der Controller prüft den
Transportblock, entfernt zwei Zusatzbytes und erreicht über `0xde2a` den
Verteiler `0x23ae`, dann `0x1c98`.

Der Kalibrierparser prüft Typ `0f` und Option null (`0x1c9a…0x1cb8`), liest
Byte 4 (`0x1cbc`) und verzweigt bei `fe` nach `0x1fa8`. Dort werden Operation
5 und Teilmaske 6 übernommen. 0/1/2 erreichen die bekannten Start-/Finish-/
Exit-Pfade. USB-Sequenzbyte 2 und Längenbyte 3 werden in diesem ausgewählten
Kalibrierpfad nicht als Kalibrierparameter oder Funk-Duplikatkennung verwendet.

Eine zusätzlich vom Host anzuhängende Kalibrier-CRC ist in dieser Kette nicht
vorhanden. Funk-Prüffelder erzeugt die Firmware; sie sind von USB-Linkprüfung
und Inhalt des Linux-OUT-Pakets zu unterscheiden.

Die [Funkantwort `14` / `15`](NEXUS_STICK_RECONNECT.md) gehört zum Transport,
nicht zum USB-Sequenzbyte und nicht zu bestätigter dauerhafter Speicherung.
Der kurze USB-Queuezweig erzeugt selbst keine separate kalibrierungsbezogene
USB-Erfolgsquittung. Das beweist nicht die globale Abwesenheit anderer Meldungen.
Die App nutzt weiterhin frischen E0-Aktiv-/Fertigstatus. Finish stößt den
Firmware-Speicherweg an; eine zusätzliche NVM-Rücklesequittung wird nicht erfunden.

## 5. Varianten und Prüfung

Gegenprüfung an **DG144/DV209**, **DG510/DV515**, **DG604/DV608**: derselbe
relevante Nachrichtenaufbau, Dongle-Callback `0x94e` und Controllerparser
`0x1c98`. Diese Parserpositionen sind nicht pauschal um zwei Bytes verschoben.
Neuere Dongles verwenden D+`2e0` statt D+`2dc` als Queuezeiger; einige
Konfigurationsstellen verschieben sich. Private RAM-Adressen gehören nicht in
die Linux-Nachricht. Damit sind Codepfade dieser Dateien belegt, nicht die
installierte Version oder aktive Ausführung jedes realen Controllers.

Der isolierte Abschlusslauf umfasst **39 Bereiche / 515 Datensätze** ohne
Dekodierabbruch in diesen Bereichen. 88 Firmwareanker, elf Nexus-Anker,
13 unabhängige Aufrufzielprüfungen samt veränderten Operanden und drei
veränderte Callback-Zeigerkontrollen wurden geprüft. Suchläufe an Tabellen
oder ungeeigneten Startgrenzen sowie ein abgewiesener Vier-Image-Aufruf zählen
nicht dazu. Der Decoder ist unverändert; seine Parallel-/Bedingungsgrenzen
bleiben bestehen. Überlappende Exporte sind keine wiederholte Ausführung.

Offline-Tests vergleichen den tatsächlichen C-Paketbauer für 256 Sequenzwerte
und drei Operationen mit unabhängig festgelegten Bytevektoren und dem
vorhandenen Providercodec. Andere Operationen werden ohne Ausgabeveränderung
abgewiesen. **Kein Firmwareemulator und kein Hardware-Erfolgsnachweis.**
Sequenz null ist ein Bauer-Grenztest; der native Eigentümer vergibt 1 bis 255.
`make test-alpha` besteht mit 455 Fällen einschließlich der drei neuen
Byteformat-Tests. Weitere 26 Lizenz-/README-/Kalibrierablauffälle bestehen.
Herstellerdateien, vollständige Disassemblierungen und private Pfade bleiben
außerhalb von Git. Neue Tests und Beschreibungen sind eigener GPL-2.0-only-Code
beziehungsweise Projektdokumentation.

## Nächster Schritt

Der Entwurf benötigt keine zusätzliche Host-Prüfsumme oder Funksequenz.
Er bleibt ausgeschaltet. Vor dem kontrollierten Test sind die auf das Gerät
begrenzte GUI-/Berechtigungsanbindung und der Geräte-/Sitzungszustand zu prüfen.
Installation und Hardwarekalibrierung erfordern eigene Freigabe. Kein
automatisches Wiederholen eines unklar zugestellten Finish. Der geplante
Vergleich absichtlich ungenauer Kalibrierung mit dem bisherigen 0,0-Anzeigewert
bleibt ein noch nicht ausgeführter Hardwaretest.
