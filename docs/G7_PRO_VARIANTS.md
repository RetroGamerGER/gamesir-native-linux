> Public export: personal tester, host and path references were anonymized. Historical evidence hashes refer to the private originals.

# Ein gemeinsamer Treiber: Varianten und experimenteller ZZZ-Start

## Aktueller Auftrag und Implementierung: Alpha3

Nach der Quellenprüfung und dem lesenden Vergleich beauftragte [tester] ausdrücklich
die pragmatische experimentelle Unterstützung von `3537:105e` im bestehenden
Treiber, ohne vorab einen neuen Mitschnitt zu verlangen. Diese Entscheidung
ersetzt die frühere Voraussetzung im unten erhaltenen Untersuchungsbericht.
**Ein Modul, ein Manager, gemeinsame Decoder und Ausgaben.** Das danach separat
freigegebene Alpha3-Update ist installiert. Der abgeschlossene 180-Sekunden-
Realtest bestätigt Direktstart, normale Eingaben, sechs veränderliche IMU-
Rohkanäle und Rückgabe an xpad. Zwei von vier zusätzlichen Tastencodes wurden
ausgelöst; vollständige Paddle-, Motor- und Steam-Abnahme bleiben offen.
[Installation](ALPHA_INSTALLATION.md).

- `100a` behält den bisherigen Übergang nach `109c`. `105e` startet direkt
  auf derselben Instanz mit drei GIP-Initialisierungen und drei Heartbeats;
  kein Identitätswechsel und keine Profil-/Firmwarebefehle.
- Die private `claim_105e`-Schnittstelle verwendet dieselben Instanzprüfungen
  wie `claim_100a`, jeweils mit festgelegter PID. Der Manager prüft das
  Startbudget und die Kernelunterstützung vor dem xpad-Unbind. Fremde 109c-
  Instanzen, 1022 und weitere unbekannte PIDs werden nicht übernommen.
- Bootstrap, Fehlermeldung und Runtime-Übergabe verwenden dieselben Kernel-
  Tokens. Frische IMU bleibt Voraussetzung für den erfolgreichen Start;
  Gamepad-Aktivität wird getrennt bewertet. Ausbleibende Antworten lösen
  keine alternativen USB-Befehle oder endlose Startschleifen aus.
- Gemeinsame Eingaben mit 15 Tastencodes, sechs IMU-Rohkanäle, FF_RUMBLE und
  die bestehende Viermotor-Schnittstelle bleiben erhalten. Echte PID und Name
  `GameSir G7 Pro` werden ausgegeben; keine Xbox-/Elite-Identität vorgetäuscht.
- Rückgabe des ZZZ: eigene Instanz stoppen, erfolgreichen END prüfen, gezielt
  xpad binden und `105e/xpad` erneut feststellen. Keine Behauptung eines
  Wechsels nach 100a. Unbestätigtes END oder verlorener Besitz blockiert
  automatische weitere Änderungen; der konkrete manuelle Rückweg bleibt offen.
- Dienstneustart, Suspend/Resume, Wiederverbindung und mehrere Dongles bleiben
  Teil derselben Zustandsverwaltung. Besitz- und Motorziele sind pro Instanz.

Die Hardwarebelege unten erweitern die zuvor ausschließlich offline
geprüfte, weiterhin experimentelle **Code-Unterstützung**.
Gyroskopskalierung bleibt unbekannt; 8192 LSB/g bleibt austauschbar und
experimentell. Die installierte Steam-Ergänzung enthält weiterhin nur das
bestätigte 109c-Mapping: native Tastencodes sind keine automatische Zusage
für die vier ZZZ-Paddles im Steam-Layouteditor.

### Offline-Prüfung und Bau

- Vollständiges `make test` bestanden, darunter **125 Manager-Tests**,
  Clientprüfung mit künstlichen Systemaufrufen und 24 Paketierungsfälle.
- C-Startup/-Runtime mit ASan/UBSan; tatsächliche Kernelfunktionen in
  **108 Startup-, 54 Claim-, 22 FF-Lebensdauer- und 32 Motorpaketfällen**.
  Vier negative Kontrollen erkennen weiterhin den früheren FF-Speicherfehler.
- Die 105e-Fälle sind ausdrücklich simuliert und verwenden vorhandene 109c-
  Paketbytes. Keine neuen Hardware-Fixtures oder Kalibrierungsbehauptungen.
- Modul `0.1.0.alpha3` gegen vorhandene `7.2.9-2-garuda`-Header gebaut,
  `LLVM=1 W=1 -Werror`, keine Compilerwarnungen oder Autoload-Aliase.
- Checkpatch und Clang Static Analyzer bestanden; keine Befunde in den fünf
  geprüften Übersetzungseinheiten. Sparse ist nicht installiert.
- Unabhängiger Code-Review ohne offenen Implementierungsblocker.

Prüflog: `build/results/zzz-alpha3-full-tests.log`; Modul-/Analyseberichte:
`build/results/kernel-build.json` und `kernel-static-analysis.json`.
Ein erfolgreicher Offline-Bau ist keine automatische Installationsfreigabe.
Das Arch-/DKMS-Paket wird mit den vorhandenen Werkzeugen ohne Installation
unter `build/alpha3-zzz-release/` gebaut. Dort bleiben Quellarchiv, Paket und
Prüfsummen erhalten. Der Paketbau ersetzt keinen tatsächlichen DKMS-Lauf
auf dem Zielsystem; CachyOS-Zielbuild und Hardwareabnahme bleiben offen.

### Erster gezielter ZZZ-Lauf am 14. Oktober 2026

Nach gesonderter Freigabe: installiertes Modul `0.1.0.alpha3`, globaler Dienst
gestoppt und pausiert, ausschließlich `8-5:1.0` unter `3537:105e`, Adresse 21,
USB-Inode 107548 übernommen. Der andere Dongle `8-6/109c`, Adresse 17,
blieb an xpad. Der lokale Ablauf nutzt den installierten Manager mit einer
auf diese eine Instanz begrenzten Sicht, dessen Startbudget und Besitzprüfung.

Um 16:44:59 UTC gelang der einmalige direkte Bootstrap ohne Deadband und
ohne PID-Wechsel. Der Client und eine zweite lesende Kernelprüfung bestätigten
`state=7`, `error=0`, `pad=1`, `imu=1` und dieselben positiven Besitz-Tokens.
Der Kernel registrierte `GameSir G7 Pro`, echte PID 105e, Version 0607,
die normalen sowie zusätzlichen Tastencodes und ein IIO-Gerät mit sechs
Rohkanälen. Das belegt erfolgreiche Initialisierung mit dekodierten Berichten,
noch keine manuell durchgeprüften Tasten oder vollständige IMU-Messreihe.

Der vorgesehene 180-Sekunden-Test brach beim Start des Beobachters ab:
Ein lokales Metadatenfeld `event` kollidierte mit dem gleichnamigen Argument
der Protokollfunktion. Es wurden **null IMU-Snapshots** erfasst; keine
abgeschlossene Eingabemessung oder Motorprüfung behaupten. Der Fehler lag
im lokalen Beobachter, nicht in einer fehlgeschlagenen USB-Initialisierung.

Der Rückweg wurde ausgeführt und bestätigt: genau ein END mit passenden
Kernel-Tokens, danach dieselbe 105e-Instanz wieder an xpad. Keine nativen
Bindungen, Modulreferenzzahl null, private und globale Besitzlisten leer,
globale Pause erhalten. Keine neuen kritischen Kernelmeldungen im erfassten
Fenster. [tester] bestätigt danach normale ZZZ-Eingaben im KDE-Test.
Der andere Dongle wurde nicht übernommen. Die anschließend ausdrücklich
freigegebenen neuen Läufe stehen unten; der verbrauchte erste Lauf blieb gesperrt.

Private Originalbelege:
`.local/integration/20261014T163354Z-alpha3-zzz/`, einschließlich
`scoped-run.txt`, `first-run-postflight.json` und geschütztem `scoped-state/`.

## Vollständiger ZZZ-Realtest am 14. Oktober 2026

**Begrenzt bestanden:** eigenständiger Direktstart ohne Deadband, 180 Sekunden
native Eingabe-/IMU-Verarbeitung und bestätigter Rückweg. Kein Motorimpuls,
kein Identitätswechsel, keine Firmware-/Profileinstellung. Der globale Dienst
blieb währenddessen gestoppt und pausiert; der andere Dongle wurde nicht
beansprucht. Derselbe installierte Kernel-/Managercode aus `f8ef66b` wie beim
Standardmodell, mit der 105e-Startstrategie; keine getrennte ZZZ-Treiberkopie.

### Ablauf und Nachweise

Nach Korrektur des lokalen Beobachters (`event` → `input_event`) bestanden
14 gerätefreie Helferregressionen. Die Negativkontrolle reproduziert den
ursprünglichen Konstruktorfehler. Weitere Fälle prüfen exakte Instanzgrenzen,
Fremdgeräteablehnung, erhaltene Startbudgets, bestätigten END vor Rückbindung,
fehlgeschlagene Rückwege, Abbruch vor Übernahme und geschlossene Ausgabe.
Der erste korrigierte Lauf um 16:53 UTC wurde auf [tester]' Wunsch angehalten:
Er hatte während der Ruhephase im KDE-Test bereits Tasten gedrückt.
367 IMU-Snapshots und der erfolgreiche Rückweg bleiben erhalten; dieser Lauf
zählt nicht als abgeschlossener 180-Sekunden-Test und nicht als Hardwarefehler.

Nach neuer ausdrücklicher Bereitschaft startete der letzte Lauf mit
30 Sekunden Vorbereitungszeit vor jeder Übernahme und weiteren Phasenpuffern:

| Vorgang | UTC am 14. Oktober 2026 |
|---|---|
| Einmaliger Claim, ausschließlich `8-5:1.0/105e` | 16:58:10.062 |
| Bootstrap erfolgreich, zweite Kernelbestätigung | vor 16:58:11.024 |
| Native Beobachtung aktiv | 16:58:11.025–17:01:11.170 (180,145 s) |
| END erfolgreich, gleiche Besitz-Tokens `3/3` | 17:01:11.495 |
| Rückgabe abschließend bestätigt | 17:01:13.125 |
| Frische lesende Schlusskontrolle | 17:06:19 UTC |

Bootstrap `state=7`, `error=0`, `failed_stage=0`, `pad=1`, `imu=1`,
`handover=0`; genau ein Claim und ein Bootstrap. Alle 77 beobachteten aktiven
Runtime-Zustände ohne Fehler; im evtest-Protokoll kein `SYN_DROPPED`. Letzte Zählerprobe: **39.548 Gamepad- und
11.214 IMU-Berichte**, außerdem **9 nicht angenommene Berichte**. Der letzte
Zählerstand stammt vor END, nicht exakt vom Aufnahmeende. `rejected` zählt
Berichte, die Decoder/Runtime nicht als zulässigen Eingabetyp annehmen
(`gsn_rx`/`gs_runtime_accepts`); es beweist keinen fehlgeschlagenen USB-Transfer.
Ohne Rohpaketmitschnitt lässt sich der Inhalt dieser neun Berichte nicht
bestimmen. Weder verlustfreie Übertragung noch 1000 Hz daraus ableiten.

Der Eingabeknoten hieß **`GameSir G7 Pro`**, evdev-Identität
`0003:3537:105e:0607`. Der Lauf verwendete `event19`; diese Nummer ist kein
fester Zugriffspfad. Alle 15 Zielcodes waren registriert, zusätzlich
`KEY_RECORD` (167) und `BTN_TRIGGER_HAPPY5` (708).

### Tatsächliche Eingaben

- Alle elf normalen Tastencodes 304, 305, 307, 308, 310, 311, 314, 315,
  316, 317 und 318 wurden gedrückt und wieder losgelassen.
- Zusatzcode **704: zwei** vollständige Betätigungen; **707: eine**.
  **705 und 706: keine Ereignisse**. Damit sind 13 der 15 Zielcodes in
  tatsächlichen Ereignissen belegt, nicht alle vier Zusatztasten.
- `KEY_RECORD` (167) wurde zweimal gedrückt/losgelassen; 708 nicht ausgelöst.
- Beide Sticks erreichten auf beiden Achsen **−32768 bis +32767**,
  beide Trigger **0 bis 1023**, beide Steuerkreuzachsen **−1 bis +1**.
  Das sind beobachtete Werte, nicht lediglich deklarierte Fähigkeiten.

[tester] bestätigt durchgehend normale Eingaben ohne Freeze oder Aussetzer,
weist aber darauf hin, L4/L5/R4/R5 möglicherweise nicht bewusst gedrückt zu
haben. Die Zuordnung der physischen Beschriftungen bleibt deshalb offen.
Chat-Ansagen waren gegenüber den lokalen Zeitmarken teilweise verzögert;
Paddle-Fenster sind kein verlässlicher Nachweis, welche physische Taste
zu welcher Zeit gedrückt wurde. Den Gesamtlauf deshalb nicht verwerfen,
aber auch keine fehlenden Betätigungen oder Achsenkalibrierung behaupten.
Die letzten Stickwerte waren links −550/+650, rechts 0/−1; daraus allein
folgt weder bestätigte perfekte Zentrierung noch ein Driftdefekt.

### Sechs IMU-Rohkanäle

**691 gespeicherte IIO-Snapshots**, alle sechs Kanäle veränderlich:

| Kanal | Minimum | Maximum |
|---|---:|---:|
| Beschleunigung X | −9256 | 9016 |
| Beschleunigung Y | −2414 | 10979 |
| Beschleunigung Z | −9718 | 4474 |
| Gyroskop X | −5498 | 4141 |
| Gyroskop Y | −1387 | 2879 |
| Gyroskop Z | −4123 | 5544 |

Das sind aus dem Treiber gelesene, zwischengespeicherte Rohwerte. Die sechs
Dateien wurden nacheinander gelesen und sind **keine atomaren USB-Pakete**.
Snapshot-Rate und USB-/Sensorrate unterscheiden sich; diese Stichprobe ist
kein neuer Paketmitschnitt oder Beleg für Pollingintervalle. Beschleunigung
bleibt experimentell bei 8192 LSB/g, Gyroskop eigenständig unkalibriert,
Achsenorientierung unbestätigt. Keine vollständige SDL-Sensorfreigabe.

### Rückweg und verbleibende Grenzen

END war vor der Rückbindung erfolgreich. Schlussprüfung: dieselbe ZZZ-Instanz
`8-5`, `3537:105e`, Adresse 21, USB-Inode 107548 an **xpad**, IF1 ungebunden.
[tester] bestätigt wieder normale KDE-Eingaben. Der andere Dongle blieb
`8-6/109c`, Adresse 17, Inode 96718, IF0 xpad und IF1 ungebunden; dessen
Zustand ist keine neue 100a-Rückwegabnahme. Keine neue kritische Kernelmeldung
im finalen Test-/Rückkehrfenster. Das ist ein Kurztest, kein Langzeitnachweis.

Alpha3 bleibt geladen, **ungebunden mit Referenzzahl 0**. Globaler Dienst
`inactive/dead`, `enabled` erhalten, globale und private Verwaltung pausiert,
Besitzlisten leer. Die installierte Alpha wurde damit nicht global wieder
aktiviert. Kein weiterer Lauf, Resume oder Entladen aus dieser Freigabe ableiten.

Offen bleiben die bewusste Einzelprüfung aller vier Zusatztasten und ihrer
Beschriftung, ZZZ-Motorimpulse einschließlich beider Trigger, Wiederverbindung,
Hotplug, Suspend/Resume, dauerhafte Mehrgeräteverwaltung sowie der CachyOS-
Zielbuild. Die erfolgreiche Standard-G7-Motorprüfung wird nicht auf ZZZ
umetikettiert.

Die installierte optionale Steam-Komponente `0.1.0.alpha1-1` ist unverändert
und enthält nur die geprüfte 109c-GUID. **105e wird davon noch nicht erfasst.**
Der nachfolgend beauftragte optionale Paketstand `0.1.0.alpha2-1` ergänzt die
105e-Zuordnung inzwischen offline: gespeicherte native Merkmale mit der
vorhandenen SDL-Fixture nachgespielt, GUID und Buttonreihenfolge synthetisch
bestätigt. Das ist kein gemessener realer Steam-GUID. Installation und echte
ZZZ-Steam-Abnahme bleiben offen; [tester] bewahrt den ZZZ vorerst auf und setzt
die CachyOS test host-Prüfung mit dem normalen G7 Pro fort.
[Steam-Ergänzung](STEAM_INTEGRATION.md#zzz-ergänzung-und-rückkehr-zum-CachyOS test host).
Steam oder Benutzerprofile wurden in diesem Hardwarelauf nicht verändert.

Private Belege (nicht in Git, Originale erhalten):

- `.local/integration/20261014T164623Z-alpha3-zzz-retry/`: angehaltener Lauf.
- `.local/integration/20261014T165602Z-alpha3-zzz-ready/`: abgeschlossener Lauf,
  rootgeschützte Originale unter `scoped-state/`, unveränderte Exportkopie
  `captured-state.tar` und `evidence/`, Auswertung `evidence-analysis.json`,
  `postflight.json`, Nutzerbestätigungen und SHA256-Prüfsummen.

## Historischer Untersuchungsstand vor dieser Erweiterung

14. Oktober 2026; geprüfter Produktionscode aus `1a209c4`. Nur vorhandene
Quellen, gespeicherte Metadaten/Mitschnitte und gerätefreie Tests verwendet.
Kein SSH, kein Gerät geöffnet, keine Installation oder neue Aufnahme.

## Architekturentscheidung

[tester] verlangt einen gemeinsamen Treiber für die G7-Pro-Varianten und
beschreibt Standard- und ZZZ-Ausführung als baugleich; Unterschiede betreffen
Lieferumfang, Shells und abnehmbare Sticks. Diese Nutzerangabe ist die
Arbeitsgrundlage, kein eigener Platinenvergleich.
Es bleibt bei **einem `gs_native.ko`, einem Manager und gemeinsamen
Gamepad-/Sensor-/Viermotor-Schnittstellen**. Keine separaten Module oder
kopierten Decoder pro Edition. Die bestehenden C-Kerne und der Kerneladapter
sind die Grundlage. Bestätigte Unterschiede sollen künftig als explizite
Variantenmerkmale beschrieben werden:

- Identifikation: VID/PID, Transport, Interfaces/Endpunkte; dynamischer
  Anschluss und exakte Geräteinstanz, kein fest codierter Port.
- Startstrategie: belegter Übergang mit Neuanmeldung oder belegter Direktstart
  auf derselben Instanz. Nicht jede Edition muss nach `109c` wechseln.
- Fähigkeiten: bestätigte Eingabeformate, Extras, IMU und Motoren/Wartung.
  Sensorkalibrierung bleibt eigenständig; Modellname ersetzt keine Messung.
- Rückweg: wirkliche Ausgangsidentität und vorheriger Besitzer. `END`,
  Motorstop und PID-Wechsel bleiben unterschiedliche Vorgänge.

Dies war zum Zeitpunkt dieser Untersuchung die Erweiterungsregel, **keine bereits implementierte universelle
Profiltabelle oder Freischaltung zusätzlicher Geräte**. Keine pauschale
Übernahme aller Geräte mit VID `3537`. Mehrere Dongles behalten getrennte
Besitzer, Sequenzen, Motorziele und Instanzen innerhalb desselben Treibers.

## Identitäten und Belege

| Identität | Nachweis | Bedeutung |
| --- | --- | --- |
| `100a` | erstes Exemplar, XInput und Übergang hardwaregeprüft | bestehender Einstieg |
| `109c` | erstes Exemplar, Eingaben/IMU/Extras/vier Motoren hardwaregeprüft | bestehende Runtime |
| `105e` | zweites Exemplar, ZZZ/Funk-Dongle durch Nutzer, USB-Metadaten, funktionierendes Steam-Rumble unter xpad | konkrete neue Variante; native Extras noch offen |
| `105d` | archiviertes g7ctl beschreibt erfolgreiche Konfigurationsabfrage an anderem kabelgebundenem ZZZ-Exemplar | Fremdbeleg, kein Funk-Nachweis |
| `1022` | zweites Exemplar vor eigenem manuellem Wechsel, HID-Interfaces | kein belegter nativer Einstieg |

Alle Zeilen betreffen VID `3537`. Die zweite Geräteaufnahme steht im
[CachyOS-Bericht](STEAM_INTEGRATION.md#nach-eigenem-xinput-moduswechsel-105e-bestätigt).
105e: IF0 `ff/47/d0`, Interrupt `02/82`, maximal 64 Byte; IF1 ohne Endpunkte
und HID-Treiber. Das ähnelt `109c`, nicht `100a` (`ff/5d/01`, 32 Byte).
Die Endpunkt-Maximalgröße beweist keine tatsächliche Eingabeberichtslänge.

**Hypothese zur App-Zuordnung:** [tester] vermutet, dass `109c` gegenüber
`105e` die editionsabhängige Darstellung samt Bild in der GameSir-App
ermöglicht. Eine solche Verwendung der PID ist plausibel, hier aber nicht
anhand des App-Codes oder einer Sitzung nachgewiesen. Daraus folgt weder ein
anderes Protokoll noch, dass die PID ausschließlich kosmetische Bedeutung
hat. Im ersten Exemplar ist zusätzlich der Wechsel `100a→109c` belegt.
Für unsere Erweiterung prüfen wir gezielt die beobachtete Kennung und den
Startablauf; vorhandene Datenformate und Motorlogik bleiben gemeinsam, solange
keine tatsächliche Abweichung nachgewiesen wird.

## Quellenprüfung und Startstrategie

**Direktstart ist die begründete nächste Hypothese.** Archiviertes g7ctl
verwendet eine bereits vorhandene Vendor-Instanz ohne IF1-HID direkt, statt
zuerst den `gamesirapp`-Übergang zu senden. Unser gespeicherter 105e-Aufbau
passt dazu. Das beweist keine Heartbeat-/IMU-Antwort dieses Dongles; die breite
strukturelle Suche des Fremdprojekts wird nicht ungeprüft übernommen.
Fundstellen: `pyg7/device.py:350–413,438–500,633–653`.

g7ctl `PROTOCOL.md:122` beschreibt den erfolgreichen ZZZ-105d-Lesetest.
`pyg7/variants.py:85–90` führt den Dongle dagegen als unbestätigt
(`dongle_pid=None`, 105e nur Vorhersage). Unsere Nutzer-/Gerätebestätigung
schließt die Identitätslücke, bestätigt aber noch keine Paketgleichheit.

**Deadband liefert für 105e keine aktive Referenzsitzung.**
`vendors/gamesir/models/g7pro/protocol.py:81–82,119–129,473–476` enthält diese
ID nur als unbestätigte Edition. `controller_profile.py:392–404` und
`reader.py:362–375` verwenden evdev ohne USB-Konfigurationspfad. Ein Start der
unveränderten Anwendung würde daher keine passende IMU-Referenz liefern.

**Gemeinsamer GIP-Code ist vorhanden.** Unser `gs_gip_init` erzeugt dieselben
Power-/LED-/Auth-Paketvorlagen wie die generische Xbox-One-Initialisierung im
gespeicherten Linux-xpad-Quelltext, jeweils mit eigenem Sequenzzähler. xpad
erkennt VID 3537 plus `ff/47/d0` generisch. Das stützt den gemeinsamen Pfad,
ist aber keine Aufnahme des tatsächlichen CachyOS-xpad-Verkehrs.

xpad verwendet ebenfalls 13-Byte-GIP-Rumblebefehle mit denselben vier
Kanalpositionen. Bei normalem `FF_RUMBLE` setzt dieser Quellstand beide Trigger
auf null; Zeit-/Wiederholungswerte unterscheiden sich von unseren kurzen
Leases. Steam-Rumble belegt deshalb noch keine unabhängigen Trigger.
Fundstellen: `xpad.c:491–498,571,645–646,683–693,721–729,1595–1611,2100–2110`;
unser `src/gs_protocol.c`. Deadbands gemeinsame Telemetrie-/Motorfunktionen
enthalten keine gesicherte ZZZ-Abweichung, werden für 105e aber auch nicht
aufgerufen. Keine ZZZ-Skalierungsfaktoren oder gesicherte Achsenzuordnung gefunden.

## Gespeicherte Daten und Regression

Sprint-002-Parserdaten erneut gegen die Fixture-SHA256 geprüft:
`63c928f9347bb3b262197305a2935c7060d9f95309bc690eab6bf34dfa838956`.
1.476 Einträge gehören zu `100a`, 16.781 zu `109c`, **keiner zu 105e**.
Alle 12.204 gültigen IMU-Berichte gehören zu 109c. Keine Umbenennung alter
Messdaten in vermeintliche ZZZ-Fixtures.

Die damals geprüfte Produktionsimplementierung lehnte 105e in Manager, Kernel, Startup und
Runtime ab. Kleine Regressionen ergänzen ausschließlich bestehende Tests:

- `tests/test_startup.c`: künstlicher Kandidat mit beobachteten 105e-
  Interface-/Endpunktmerkmalen abgewiesen; kein Sendeauftrag entsteht.
- `tests/test_runtime.c`: 105e weder mit noch ohne Ausgabe freigegeben.
- `tests/test_service_manager.py`: Fake-Sysfs-Scan überspringt 105e; auch
  direkt eingespeister Kandidat bewirkt keinen Claim/Start/Restore.
  Die synthetische xpad-Bindung bleibt erhalten.

Startup/Runtime mit ASan/UBSan bestanden, Manager **97 Tests**. Positive
100a-/109c-Kontrollen bleiben erhalten. Vorangehender unveränderter Adaptercheck:
88 Kernel-Startup- und 42 Claim-Szenarien bestanden. Dies belegt die aktuellen
Grenzen, **keine native 105e-Funktion**. Produktionscode/Modul/ID-Tabelle und
installierte Pakete unverändert. Kein neuer Zielkernel-Build erforderlich für
diese Test-/Dokumentationsänderung; CachyOS-Zielbuild bleibt offen.

## Ursprünglich vorgeschlagener nächster Nachweis

Dieser Vorschlag bleibt eine mögliche Paketvalidierung, ist nach [tester]'
anschließender Entscheidung aber keine Voraussetzung für den Offline-Umbau.

Ein begrenzter passiver Vergleich des funktionierenden **105e/xpad**-Betriebs
mit dem vorhandenen Protokoll ist der nächste sinnvolle Schritt. Ziel ist,
den gemeinsamen Pfad zu bestätigen und nur reale Unterschiede zu ergänzen;
keine erneute vollständige Protokollentwicklung für die Edition. Der Vergleich
ist noch nicht durchgeführt oder freigegeben:

1. Vorhandenen isolierten Recorder für den tatsächlichen Zielbus vorbereiten,
   Tools/Rechte/Instanz prüfen; kein usbfs in der Sandbox. Daten privat dauerhaft
   speichern und Zielgerät offline filtern.
2. Mit menschlichen Reaktionspuffern Ruhe, normale Eingaben, L4/R4/L5/R5 einzeln
   und einmal normales Steam-Rumble markieren. Umfang einschließlich Motoraktion
   vorab konkret freigeben. Init-Aufnahme benötigt gegebenenfalls zusätzlich
   eine ausdrücklich vereinbarte Wiederverbindung, keine heimliche Wiederholung.
3. Reportlängen, Sequenzen, Motorbefehle und Stopps gegen bestehende Decoder
   prüfen. Fehlende IMU unter xpad beweist keine fehlende IMU-Fähigkeit.
4. Erst danach einen gesondert freizugebenden begrenzten Direktstart-/
   Telemetrieversuch vorbereiten: exklusiver Besitzer, geklärte Init/Heartbeats,
   Fristen/Stopps, keine Profil-/Firmwarewrites. IMU, Extras und vier Kanäle
   getrennt belegen; USB-Completion allein genügt nicht.

Bei Erfolg wird die Startstrategie im **gleichen Treiber** ergänzt. Rückweg
muss **105e/xpad mit echten Eingaben** bestätigen. Unser END sowie g7ctl-/
Deadband-Handle-Schließen sind keine belegten Befehle zum Wechsel nach 100a.
Ungeklärten Rückweg melden, manuelle Schritte gesondert vereinbaren.

## Quellen und private Ergebnisse

Nur bereits gespeicherte Drittquellen als Text gelesen, nicht importiert
oder ausgeführt:

- g7ctl `0ea4b5223ba2191c88a3c4d1ff8d34f594bfeb1b`: oben genannte Dateien und
  `pyg7/session.py:250–263` (Freigabe/Rückbindung).
- Deadband `771b28ae75b0a614a6a7fec9aa606606a27b3b8d`: oben genannte Dateien,
  `reader.py:768–782,827–839`, `vendors/gamesir/control.py:172–192`.
- Linux `5fce161649b4d779d1b76d9fcd52dc77779774b8`:
  `drivers/input/joystick/xpad.c`.

Private Ergebnisse: `build/zzz-105e-offline-review/`; Gerätemetadaten:
`.local/compatibility/20261014T154245Z-CachyOS test host/`. Originale erhalten;
keine privaten Systemdaten oder fremden Binärdateien im Commit.

## Nachtrag: beide Dongles am Garuda-PC

[tester] steckte den zweiten Dongle selbst an diesen PC und bestätigte normale
KDE-Eingaben sowie geschlossenes Deadband. Lesende Sysfs-Prüfung am
14. Oktober um **18:13:59 MESZ**:

| Exemplar | Port / Bus / Adresse | PID / bcdDevice | IF0 / IF1 |
| --- | --- | --- | --- |
| ZZZ | `8-5` / 8 / 19 | `105e` / `0607` | xpad / ungebunden |
| bisheriges Exemplar | `8-6` / 8 / 17 | `109c` / `0153` | xpad / ungebunden |

Beide: Produkt `GameSir-G7 Pro`, beide Interfaces `ff/47/d0`, IF0 Interrupt-
OUT `02`/IN `82`, jeweils maximal 64 Byte, Intervalle OUT `04`/IN `02`;
IF1 ohne Endpunkte. Die ausgelesenen Interface-/Endpunktmerkmale sind damit
gleich. `bcdDevice` unterscheidet sich; daraus wird keine Firmwareversion
oder Protokollabweichung abgeleitet. KDE-Funktion bestätigt [tester] für das
neu angeschlossene Exemplar; der Zustand des anderen wurde hier nicht
funktionell geprüft. Keine Geräte geöffnet oder Bindungen verändert.

Die installierte Deadband-Protokollquelle hat weiterhin SHA256
`3e64572c66c657d40556df0917674605eb20baef66ed96138be0874fbbb54f52`;
105e steht nur in `UNCONFIRMED_EDITIONS`, nicht in `CONFIG_PIDS`. Daher ist
ein bloßer App-Start bei zwei angeschlossenen Dongles kein belegter
ZZZ-Konfigurations-/IMU-Test. Keine Änderung an der installierten Anwendung,
kein automatischer Start oder Mitschnitt.

Dieser nachträgliche lesende Vergleich ist getrennt von den oben beschriebenen
Offline-Tests. Private Originalausgabe mit Prüfsumme:
`.local/compatibility/20261014T161359078310Z-local-user-connected-controller/`.
