# TMR-Stickkalibrierung: GUI und Berechtigungsweg

**Normale Oberfläche vorbereitet:** Die getestete Anbindung ist jetzt im
lokalen alpha2-AppImage ohne besonderen Startmodus erreichbar. Die
[Integration und einfachere Bedienung](CONTROL_CENTER_NORMAL_CALIBRATION.md)
behalten die getrennte Helferberechtigung und alle bisherigen Schutzgrenzen.
Noch keine Installation oder Veröffentlichung; ältere Checkpoints folgen.

## ZZZ: Verbesserung bleibt nach Aus-/Einschalten erhalten

Am 22. Oktober wurde auch der ZZZ (`3537:105e`) am Garuda-Mainrig kalibriert.
Der Nutzer wählte ihn ausdrücklich neben dem normalen G7 Pro aus, ließ beide
Sticks vor Start los, bewegte sie am Rand und schloss nach Bereitschaft beider
Sticks ab. Die lesende Manager-Abfrage bestätigt `finished`, leere Fehlerfelder
und eine freigegebene Kalibriersitzung. Verwendet wurden die bereits
installierten Core alpha3-20, TMR-Helfer alpha1-2 und die passende GUI.

Der vorher sichtbar versetzte beziehungsweise unruhige **linke** Stick wurde
vorher, direkt danach und nach Aus-/Einschalten jeweils zehn Sekunden lang
passiv gemessen:

| Zeitpunkt | Mittelwert X | Mittelwert Y | Schwankungsbreite X / Y |
|---|---:|---:|---:|
| Vorher | −0,9743% | +1,1025% | 0,0977% / 0,1099% |
| Nach Kalibrierung | 0% | −0,0031% | 0% / 0% |
| Nach Aus-/Einschalten | 0% | −0,0031% | 0% / 0% |

Nachher lagen alle erfassten Werte bei X=0 und Y=−1 im Eingabebereich
−32768 bis +32767. Der Nutzer bestätigt nach dem Wiederverbinden eine
reagierende Stickanzeige und anschließend ruhige, zentrierte Sticks.
Der Controller war nach bestätigtem Erlöschen der Leuchte weitere zehn
Sekunden ausgeschaltet; der Dongle blieb eingesteckt. Es gab keine neue
Kalibrierung und kein manuelles Resume. USB-/Eingabegerät wurden neu angelegt;
die Messfenster gehören deshalb zu getrennten, jeweils stabilen Instanzen.

Jedes Fenster umfasst 200 aktuelle evdev-Zustandsabfragen mit Host-Zeitstempeln
bei angestrebten 20 Hz, ohne exklusiven Gerätezugriff oder Gerätebefehl.
Gemessen wurden die verarbeiteten Gamepad-Achsen wie im KDE-Test, nicht die
Rohpositionen des Kalibrierdialogs oder gespeicherte Koeffizienten.
Wiederholte Zustandswerte sind kein Nachweis neuer Funkpakete. Das Ergebnis
belegt die beobachtete Verbesserung einschließlich Erhalt nach normalem
Aus-/Einschalten dieses ZZZ, keine unabhängige NVM-Auslesung oder vollständige
RAM-Stromtrennung. Rechts wurden keine entsprechenden Zahlen erhoben.
[Messnachweis](evidence/TMR_ZZZ_CALIBRATION_20261022.json).

Weitere Geräte-/Firmwarestände, CachyOS-Kalibrierung und echte Abbruch-/Verlustfälle
sind damit nicht abgenommen. Der normale G7 Pro wurde bei diesem ZZZ-Lauf
nicht erneut kalibriert. Keine weiteren Geräte- oder Systemänderungen, kein
Push; die folgenden Abschnitte halten frühere Checkpoints fest.

**Erster echter Kalibrierungsdurchlauf bestanden:** Nach ausdrücklichem Go
führte der Nutzer Start, Stickbewegungen und Finish am normalen G7 Pro unter
Garuda durch. Beide Sticks meldeten bereit; die App meldete „Abschlussbefehl
übermittelt“. Die lesende Nachprüfung bestätigt „finished“, keine Fehler,
freigegebene Sitzung und denselben weiterhin nativ gebundenen Controller.
Im unabhängigen KDE-Test bestätigt der Nutzer saubere Mittelstellungen,
volle Ausschläge sowie normale Tasten, Trigger und alle vier Paddles.
[Kalibrierungsnachweis](evidence/TMR_FIRST_LIVE_CALIBRATION_20261022.json).

Damit sind ein einzelner Ablauf und die Funktion an derselben Verbindung
bestätigt. Die Speicherung über Aus-/Einschalten hinaus, genaue Rohwerte und
weitere Modelle/Plattformen wurden dabei nicht geprüft. Die Firmware übernimmt
das Speichern; eine zusätzliche Speicherquittung wird nicht verlangt.
Nach Abschluss stoppt die Kalibrierungsanzeige. Mittelstellung und Ausschläge
deshalb im normalen Controllertest prüfen. Kein weiteres Finish/Exit und
keine automatische Wiederholung. Die folgenden Abschnitte sind frühere
Installations-/Vorschau-Checkpoints.

**Aktueller Stand nach Update:** Core alpha3-20, TMR-Helfer alpha1-2 und passende
GUI sind am Mainrig installiert und geprüft. Der Nutzer bestätigt einen ruhigen
Startknopf und Stickanzeigen ohne wahrgenommene Verzögerung. Zehn Sekunden
Vorschau ergaben im Mittel 6,3% Manager-, 5,1% GUI- und 0,9% Helfer-CPU auf
Ein-Kern-Basis. [Installations-/Vorschauergebnis](evidence/TMR_DISPLAY_UPDATE_20261022.json).
Die Vorschau bleibt offen; Kalibrierung und Finish warten auf ein neues Go.

**Vorheriger Fehlerstand:** Die später freigegebene echte Vorschau zeigte beide Sticks.
Vor Start meldete der Nutzer jedoch einen blinkenden Startknopf, verzögerte
Anzeige und hohe Manager-CPU. Start wurde nicht gedrückt; nach Abbrechen des
Dialogs blieb das Hauptfenster offen und die gemeldete CPU-Last verschwand.
Die [Korrektur des Anzeigewegs](TMR_DISPLAY_POLLING_FIX.md) wurde danach offline
geprüft und mit gesonderter Freigabe wie oben beschrieben installiert.
Die folgenden Aktivierungs-/Offline-Abschnitte beschreiben frühere Checkpoints.

**Activation checkpoint (22 October):** The maintainer then authorized temporary
TMR module enablement, paused service start and one Resume after reconnecting
the receiver/controller. Native startup completed successfully (gamepad + IMU,
input publication confirmed). TMR is enabled for this module lifetime only;
no persistent option was written. No calibration helper/session/Start/Finish/Exit
has run. [Activation receipt](evidence/TMR_MAINRIG_ACTIVATION_20261022.json).
Wait for the maintainer's explicit Go before the real calibration GUI/test.
The initial monitor stopped on transient empty USB configuration metadata during
handover; a read-only follow-up confirmed the original bootstrap succeeded.
No second Resume or driver restart was needed. Earlier checkpoints below retain
their own historical scope.

**Deployment checkpoint (22 October):** The maintainer subsequently authorized
installation on the Garuda main system. Local test core alpha3-19 and optional
TMR helper alpha1-1 are installed and verified; module/service remain stopped,
the receiver remains removed and no calibration command ran. Gyro configuration,
Steam/bridge versions and the service's enabled preference are preserved.
[Installation receipt](evidence/TMR_MAINRIG_INSTALL_20261022.json). Activation
and hardware acceptance still need separate approval; no public release/push.

Stand: 22. Oktober 2026. **Offline implementiert und geprüft, noch kein
Hardwaretest.** Fortsetzung der [nativen Schnittstelle](TMR_NATIVE_INTERFACE.md)
und des [USB-Framings](TMR_USB_FRAMING.md).
[Prüfergebnis](evidence/CONTROL_CENTER_TMR_PERMISSION_20261022.json).

## Ablauf für den Nutzer

Die vorbereitete experimentelle Oberfläche verwendet den akzeptierten Dialog:

1. „Stickkalibrierung öffnen“ wählen. Das Desktop-Passwortfenster erlaubt genau
   eine Kalibriersitzung; die Anwendung selbst läuft ohne Administratorrechte.
2. Den gewünschten GameSir auswählen. Standard-G7-Pro und ZZZ werden getrennt
   angezeigt, einschließlich USB-Port. Auch bei nur einem Gerät ist die Auswahl
   ausdrücklich zu bestätigen. Bis hier wurde kein Startbefehl gesendet.
3. Beide Sticks loslassen und „Kalibrierung starten“ wählen. Nach drei Sekunden
   Vorbereitung sendet der Helfer einmal Start.
4. Die Sticks langsam am äußeren Rand kreisen. Zwei Anzeigen zeigen die
   Rohpositionen und unabhängig voneinander besuchte Randbereiche farbig an.
5. Erst die aktuelle Bereitschaftsmeldung **beider** Sticks schaltet
   „Kalibrierung abschließen“ frei. Ein voller Kreis allein genügt nicht.
6. Finish wird einmal übermittelt; Berechnung und Speicherung übernimmt die
   Firmware. Die Anzeige behauptet keine unabhängig geprüfte dauerhafte
   Speicherung. Danach Mittelstellung und Ausschläge separat prüfen.

Ein Passwortfenster pro Durchlauf, keines bei jedem Messwert oder Befehl.
Abbruch vor Start gibt nur die Sitzung zurück. Nach Start kann ein ausdrücklicher
Abbruch einmal Exit senden, sofern die ursprüngliche Sitzung noch frisch und
verfügbar ist. Nach Abschluss wird kein Exit nachgeschoben.

Die veröffentlichte Anwendung und die laufenden Installationen bleiben wie
zuvor. Die normale Anwendung bietet weiterhin keine echte Kalibrierung an;
die neue Anbindung benötigt einen ausdrücklich gewählten experimentellen
Modus, geprüften Helfer und die bereits gesondert aktivierte Kernel-Schnittstelle.
Es wurde kein Passwortfenster geöffnet und keine dieser Voraussetzungen am
System hergestellt.

## Getrennte Zuständigkeiten

| Teil | Aufgabe / Grenze |
|---|---|
| QML / `CalibrationLive` | Anzeige, explizite Auswahl, Start/Finish/Abbruch; kein Root und kein Gerätezugriff |
| `CalibrationWorker` | Ein serieller Hintergrundkanal; keine blockierende GUI; alte Antworten können keinen neuen Dialog verändern |
| `HelperClient` | Ein festes `pkexec`-Ziel, geprüfte installierte Dateien und Polkit-Regel; kleine nummerierte JSON-Zeilen |
| Eigenständiger TMR-Helfer | Ein ausgewähltes Gerät, bestehender Kalibrierkoordinator; keine Paket-, Treiber- oder freien USB-Befehle |
| Root-Manager / `NativeChannel` | Exakte USB-Port-/Instanz-Tokens, Stream-Epoche und exklusive zeitlich begrenzte Sitzung |
| Kernel | Bestehende native Sequenzierung und Ausgabe; Start/Finish/Exit einmalig; normale Eingaben bleiben aktiv |

Der neue Root-Manager-Aufruf `{"version":1,"tmr":"list"}` liefert nur
bereits aktiv verwaltete, fehlerfreie GameSir-Instanzen mit Auswahl-Tokens.
Er öffnet keinen Kontroll-FD und startet keinen Controller. Andere PIDs,
xpad-Geräte, wartende/pausierte oder bereits reservierte Instanzen werden nicht
angeboten. Probe/Acquire prüfen die Auswahl danach erneut; ein Austausch in
der Zwischenzeit führt zum Stopp.

Der Helfer heißt fest `/usr/lib/gamesir-control-center/tmr-maintenance/execute`.
Seine eigene Polkit-Aktion endet auf `.control_center.tmr`. Nur eine aktive
Desktop-Sitzung darf mit `auth_admin` zustimmen; keine gespeicherte Freigabe,
keine inaktive/entfernte Sitzung und keine Mitbenutzung der Installations- oder
Haptikberechtigung. Die Regel warnt, dass Finish neue Stickwerte speichern kann.
Passwörter laufen ausschließlich durch den Desktop-Agenten, nie durch JSON,
App-Logs oder die GUI.

Das isolierte System-Python startet nur root-eigene, nicht gruppen-/weltweit
beschreibbare Dateien und Verzeichnisse am festen Pfad. Der Benutzerclient
prüft zusätzlich die erwarteten Datei-Hashes. Es gibt keine erhöhte Ausführung
eines Skripts aus dem AppImage, keinen Shell-Aufruf und keine frei wählbare
Manager-Adresse. Der feste Manager-Socket wird auf geschützten Besitzer/Modus
und Root-Peer geprüft.

## Datenstrom und ehrliche Verbindungsgrenze

Das frühere abstrakte Channel-Modell forderte eine nachgewiesene tatsächliche
Funk-Lebensdauer. Das native API kann diese **nicht** beweisen. Stattdessen
verwendet nur die explizite experimentelle Anbindung den getrennten Vertrag
`fresh_e0_continuity_only` mit `e0-snapshot-v1` und
`fresh-e0-continuity-v1`. Sie meldet ausdrücklich **kein** `connected=True` als
RF-Nachweis und gibt nicht das alte `e0-stream-v1`-Versprechen ab. Der strengere
Adapter-Standard bleibt bestehen; nur der TMR-Helfer entscheidet sich ausdrücklich
für den begrenzten Kontinuitätsnachweis.

Die GUI bekommt vollständige E0-Snapshots, tatsächliche Empfangszeit und lokale
Berichtsnummer. Ein erneut gelesener Snapshot erzeugt keinen Messwert und
keinen künstlichen Herzschlag. 1,5 Sekunden ohne ausreichend frische E0-Daten
beenden den Lauf; Poll erneuert nur die Manager-Lease von zwei Sekunden.
Zählerlücken zeigen ausgelassene Snapshots, keine bewiesenen Funkpaketverluste.
Kurze Funkunterbrechungen können unsichtbar bleiben; unveränderte E0-Berichte
können firmwareseitig unterdrückt werden. Diese Grenze wird nicht durch eine
GUI-Uhr oder USB-Anwesenheit überdeckt und muss beim Hardwaretest geprüft werden.

Die Darstellung nutzt ausdrücklich Rohbytes 51–54, stückweise Normierung um
128 und Vorzeichen `+,-,+,-` für die nach oben positive Plot-Y-Achse. Das ist
eine noch nicht live bestätigte **Anzeigeannahme**. Sie verändert weder die
Kalibriermathematik der Firmware noch Gamepad-Achsen oder gespeicherte Werte.
Bereitschaft kommt ausschließlich aus den niedrigsten beiden Active-/Done-Bits
in Berichtbytes 30/31.

## Stopp, Schließen und Fehler

- Alle semantischen Aufträge und Pipe-Anfragen werden vor dem Senden konsumiert.
  Keine Wiederholung bei unklarem Ausgang; keine automatische neue Sitzung.
- Geänderte Instanz, Epoche, Besitzer, Generation, ungültige E0-Daten oder
  veralteter Datenstrom beenden den Lauf. Kein Finish/Exit auf eine neue Instanz.
- Schließen des Dialogs bricht einen frischen gestarteten Lauf einmal ab.
  Schließen während einer unklaren laufenden Übertragung schließt den Kanal;
  es sendet keinen weiteren Gerätebefehl hinterher. Schon übermittelte Aufträge
  können nicht zurückgerufen werden.
- Pipe-EOF, Helferfehler oder fehlender Client-Poll geben nur die lokale Lease
  zurück. Der Root-Helfer wartet nach Auswahl höchstens 1,5 Sekunden auf eine
  neue Anfrage; die Manager-/Kernel-Lease läuft zusätzlich unabhängig ab.
- Vor Geräteauswahl endet inaktive Eingabe nach 120 Sekunden, der gesamte
  Helferlauf spätestens nach 30 Minuten. Die normale Poll-Anzeige läuft im
  Hintergrund weiter, während der Nutzer die Sticks bewegt.
- Ursprünglicher Adapterfehler und unbestätigte Rückgabe bleiben getrennt.
  Unklare Akquisition/Rückgabe sperrt einen weiteren Lauf im aktuellen Fenster;
  ein Geräte-Neustart oder automatisches Resume ist kein Fehlerersatz.
- Ein Erlaubnisfehler wird ohne private Fehlertexte angezeigt. Der Helfer kann
  weder Treiber laden/entladen noch Dienste starten, Pakete installieren,
  Firmware flashen oder andere USB-Befehle durchreichen.

## Offline-Bau und spätere Freigabe

`scripts/stage_tmr_helper.py --dest build/tmr-helper-review` erstellt ausschließlich
einen lokalen Begleitordner: acht Dateien (fester Starter, sechs eigene
Python-Module und Polkit-Regel) plus Hashmanifest. Keine Installation.

Der AppDir-Bauer nimmt diesen ausdrücklich geprüften Begleitordner optional
über `--reviewed-tmr build/tmr-helper-review` auf. Er prüft die Hashes erneut,
legt das erwartete Manifest neben dem App-Code und den Begleitinhalt getrennt
unter `tmr-helper-payload` ab. Das vorhandene Erststart-/Paket-Setup installiert
**keine** TMR-Dateien automatisch. Für einen späteren Test braucht es eine
separate Freigabe für genau diesen Helfer, die passende Kernel-/Manager-Version
und `experimental_tmr`. Erst danach kann `--experimental-tmr` die vorbereitete
Oberfläche öffnen; ohne Manifest endet dieser Modus vor jeder Autorisierung.
Die bekannten Demo-/Probelaufmodi nehmen keine solche Factory an.

Nächster Schritt ist ein gesondert freigegebener, begrenzter Hardwarelauf:
Zielinstanz/Version, native OUT64-Annahme, frische E0-Rate, Positionen und
Active-/Done-Verlauf prüfen; zuerst Abbruch/Rückgabe, dann bewusster Finish-Test
und unabhängige Nachkontrolle nach Aus-/Einschalten. Das ist **noch nicht erfolgt**.
Es wird keine zusätzliche Firmware-Speicherquittung als Voraussetzung erfunden.

## Offline-Prüfung

43 neue reine Prüfungen verbinden GUI-Protokoll, Helfersitzung, echten
Manager-Quellcode und einen nachgebildeten nativen ABI-Adapter. Sie prüfen
Befehlsreihenfolge, Bereitschaft, einmaliges Finish/Exit, Datenstillstand,
Instanzwechsel, ZZZ-Auswahl neben weiteren Controllern, deaktiviertes/älteres
API, Fehlererhaltung, Berechtigungsregeln, isolierten Starter, tatsächliche
unprivilegierte Pipes mit fragmentierten Antworten sowie Hash-Staging.

12 neue Qt-/QML-Prüfungen verwenden die echte Oberfläche und den echten
Hintergrund-Worker mit nachgebildetem Helfer/Manager. Auswahl, Abschluss,
Abbruch, Verbindungsverlust, verzögerte/veraltete Antworten, abgelehnte
Autorisierung, Schließen während Autorisierung, DE/EN und gerenderte Zustände
sind offline geprüft. Kein Root-Helfer, System-Socket oder Gerät wurde benutzt.
Die vollständige bestehende Regression und die unveränderte Vorschau bleiben
Bestandteil der Abnahme. Siehe maschinenlesbares Prüfergebnis für Zählstände.
