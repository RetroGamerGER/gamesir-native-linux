# Sprint 003: Hardwareplan zur ausdrücklichen Freigabe

**Dieser Plan erteilt keine Freigabe.** Den tatsächlich erreichten Stand
dokumentiert [Hardwaretest 001](HARDWARE_TEST_001.md). Abschnitt 6 des Nutzerauftrags
verlangt vor jedem Schritt mit Modul-, Bindungs-, USB-Zustands- oder Hardware-
änderung eine eigene Freigabe. Für Test 001 startet kein zusammenhängendes
Skript diese Schritte. Der neue [Test-002-Plan](HARDWARE_TEST_002.md) benennt
eine zeitkritische Übergabe als gesondert vollständig freizugebende Folge;
ohne diese konkrete Zustimmung bleibt sie gesperrt.

Hardwaretest 001 wurde am 12. Oktober mit einzeln freigegebenen Schritten
abgeschlossen. Auf Nutzerwunsch ersetzte eine 60-s-Messung (10/40/10 s) den
ursprünglichen 12-s-Vorschlag unten; dieser wurde nicht ausgeführt. Ergebnis,
Grenzen der Schlussruhe und die im KDE Center bestätigte xpad-Rückkehr stehen
im [Testbericht](HARDWARE_TEST_001.md). Historische Freigaben erlauben keinen
neuen Lauf. Für weitere Messungen Dauer und lokale Phasensignale neu festlegen.

## Ursprüngliche Entscheidung zur Testvorbereitung

**Bedingtes Go für einen ersten 100a-XInput-Test**, sobald der frische lesende
Vorabcheck passt. Kein Go für eine pauschale Komplettmessung aller Funktionen.

**109c-IMU/Motoren: noch No-Go für Durchführung.** Der Code ist gebaut/geprüft,
aber dieser Prototyp ändert die Identität nicht. Die gespeicherte 109c-Sitzung
entstand durch Deadband. Ein frischer, ausdrücklich freigegebener Übergang und
zuverlässiger Rückweg 109c→100a müssen zuerst festgelegt werden. `xpad/bind`
und Modulentladung sind keine nachgewiesenen ausdrücklichen Firmware-Rückschaltbefehle.
Es wird kein Rückschaltbefehl erfunden. Deadband und nativer Besitzer dürfen
nicht gleichzeitig Interface 0 beanspruchen.

## Schritt 1 — ausschließlich lesender Vorabcheck

Im Repository starten. `8-6` ist der **historische** Port des Dongles; wird er
nicht unverändert bestätigt, stoppen und den tatsächlichen Port zuerst klären.

```sh
python -B tools/native/preflight.py --port 8-6
uname -r
modinfo -F vermagic build/kernel/gs_native.ko
sha256sum build/kernel/gs_native.ko
```

Das Werkzeug liest vorhandene Sysfs-Attribute, öffnet keinen USB-Knoten und
sendet keine Deskriptorabfrage. Es meldet PID, Bus, Adresse, Port, Interfaces,
Treiber, Endpunkte und bereits geladene relevante Module; keine Seriennummern.
Erforderlich: VID 3537, PID 100a, Interface 0 xpad, Interface 1 usbhid, passende
Interrupt-Endpunkte, Kernel exakt 7.2.9-2-garuda und passender Modulhash laut
aktuellem Buildbericht. Deadband und Spiele schließen; Nutzer bestätigt normalen
Funk-/Eingabebetrieb. Dies ist keine neue USB-Aufnahme.

Bei mehreren Geräten, fehlenden Interfaces, abweichender PID/Bindung, Kernel-
wechsel, defektem Normalbetrieb oder offenem Deadband stoppen. Keine Reparatur.

## Schritt 2 — Modulvorbereitung, eigene Freigabe

Die folgenden Variablen stammen ausschließlich aus dem bestätigten Vorabcheck.
Vor Verwendung im Terminal die konkreten Werte zeigen und bestätigen lassen:

```sh
PROJECT="$(git rev-parse --show-toplevel)"
IFACE='8-6:1.0'
NODE="/dev/gsnative-$IFACE"
```

`industrialio` war bei der Offline-Prüfung nicht geladen. Nur falls der frische
Check das bestätigt, dafür eigens freigeben:

```sh
sudo /usr/bin/modprobe industrialio
```

Dann separat freizugebendes Laden des Testmoduls **bei noch gebundenem xpad**:

```sh
sudo /usr/bin/insmod "$PROJECT/build/kernel/gs_native.ko" \
  test_interface="$IFACE" test_pid=0x100a enable_output=0
```

Kein Installieren/Kopieren nach /lib/modules, kein depmod, kein DKMS. Der exakte
Port/PID ist nötig; andere Interfaces werden abgewiesen. Laden verdrängt keinen
bereits gebundenen Treiber. Bei ungebundenem passenden Ziel könnte das registrierte
Modul dagegen bereits binden; deshalb ist der vorherige xpad-Nachweis zwingend.
Keine Autoload-Aliase/new_id und kein zweiter Probeversuch in derselben Modulladung.
Ein externes/unsigniertes Modul kann den Kernel dauerhaft bis zum Neustart als
verändert markieren. Signatur-/Secure-Boot-Prüfungen werden nicht abgeschaltet.
Bei Ladefehler bleibt xpad gebunden; stoppen.

Danach nur lesend bestätigen, dass Interface 0 weiterhin xpad und Interface 1
usbhid gehört. Ohne diesen Nachweis keine Abbindung.

## Schritt 3 — kontrollierte Bindung, eigene Freigabe

Zuerst unmittelbar nochmals Identität/Port/Bindung prüfen. Diese zwei Aktionen
werden einzeln durchgeführt, mit Rückmeldung dazwischen:

```sh
printf '%s' "$IFACE" | sudo /usr/bin/tee /sys/bus/usb/drivers/xpad/unbind >/dev/null
```

Prüfen: ausschließlich Interface 0 ungebunden, Interface 1 weiterhin usbhid.
Die am 11. Oktober beobachtete einzelne Meldung
`xpad_try_sending_next_out_packet - usb_submit_urb failed with result -2`
kann im xpad-Abbau bei bereits deaktiviertem Endpunkt auftreten. Für den
erneuten kontrollierten Test ist ausschließlich diese identische einzelne
Meldung im unmittelbaren xpad-Unbind-Fenster erwartbar, sofern der Schreibbefehl
erfolgreich war, IF0 ungebunden und IF1/Identität/Adresse unverändert sind und
keine zusätzlichen Fehler, USB-Resets oder Disconnects auftreten. Sie allein
erzwingt keinen erneuten Forschungsstopp. Diese Ausnahme gilt nicht für
gs_native, laufenden Empfang oder andere/wiederholte Transportfehler.
Dann ausdrücklich freigeben:

```sh
printf '%s' "$IFACE" | sudo /usr/bin/tee /sys/bus/usb/drivers/gs_native/bind >/dev/null
```

Erwartet: PID unverändert 100a, Interface 0 gs_native, Interface 1 usbhid,
ein neues Testgamepad und ein 0600-Knoten `$NODE`. Probe startet Interrupt-IN,
keine OUT-Pakete, Initialisierung, Sensoraktivierung oder Identitätsänderung.
Bei Fehlern sofort stoppen und Rückweg separat freigeben; keine Wiederholung.

## Schritt 4 — Eingaben, eigene Freigabe

```sh
sudo "$PROJECT/build/gsnative-ctl" info "$NODE"
```

Erwartet: PID 100a, state=1, error=0, OUT=0; pad-Zähler steigt bei Eingaben,
imu bleibt null. Der Sysfs-Pfad **dieses Interfaces** bestimmt den Joystickknoten:

```sh
python - "$IFACE" <<'PY'
from pathlib import Path
import sys
root = Path('/sys/bus/usb/devices') / sys.argv[1]
for node in root.glob('input/input*/js*'):
    print('/dev/input/' + node.name)
PY
```

Den tatsächlich ausgegebenen Knoten einsetzen, niemals `/dev/input/js0` raten.
`jstest` ist vorhanden. Für zwölf Sekunden manuelle Tasten, D-Pad, Sticks und
Trigger prüfen:

```sh
sudo /usr/bin/timeout --signal=INT 12s /usr/bin/jstest --normal "$JS_NODE"
```

Der ursprüngliche Vorschlag für die Fortsetzung am 12. Oktober sah zusätzlich
tatsächliche evdev-Ereignisse des aus IF0 ermittelten `eventN` vor. Die vorhandene
Python-Bibliothek evdev unterstützt `InputDevice(path, readonly=True)`; kein Grab,
keine Writes und keine Änderung der Input-Uhr. Der ursprüngliche Aufruf war
für zwölf Sekunden vorgesehen: 3 s Ruhe, 6 s manuelle Eingaben, 3 s Ruhe.
Tatsächlich freigegeben und einmal ausgeführt wurden stattdessen 60 s mit
10 s Ruhe, 40 s Eingaben und 10 s vorgesehener Schlussruhe; siehe Testbericht.
Anfangs-/Endwerte per lesendem EVIOCGABS und zeitgestempelte EV_ABS/EV_KEY/
EV_SYN-Ereignisse sichern. Bei SYN_DROPPED, Geräteverlust oder Lesefehler
stoppen. Anfangswerte allein belegen keine frischen Controllerdaten. Keine
Input-Geräte vor der entsprechenden Freigabe öffnen. `jstest` allein belegt
keine unverfälschten Kernel-Input-Ereignisse oder TMR-Hardwarekalibrierung.

Timeout-Exit 124 ist bei erreichtem Zeitlimit erwartbar. Fehlt der Joystickknoten,
stoppen; keinen weiteren Input-Treiber automatisch laden. Keine Spiele-/Steam-
Integration als bestanden behaupten. In 100a werden **keine IMU/Motortests**
ausgeführt: diese Daten/Befehle sind dort nicht nachgewiesen.

## Schritt 5 — Rückweg zu xpad, jeweils eigene Freigabe

Alle Testprogramme/FDs schließen. Erst Status/Logs lesend sichern, dann separat:

```sh
printf '%s' "$IFACE" | sudo /usr/bin/tee /sys/bus/usb/drivers/gs_native/unbind >/dev/null
```

Nach bestätigter Abbindung separat:

```sh
sudo /usr/bin/rmmod gs_native
```

Danach separat:

```sh
printf '%s' "$IFACE" | sudo /usr/bin/tee /sys/bus/usb/drivers/xpad/bind >/dev/null
```

Das gilt nur für weiterhin bestätigtes 3537:100a am selben Port. Wurde die native
Bindung nie erfolgreich, nur den tatsächlich erreichten Zustand zurücknehmen.
Ist xpad bereits gebunden, keine erneute Bindung schreiben. Fehlt der xpad-
Treiberpfad, stoppen; ein nötiges `modprobe xpad` erst eigens freigeben.

Falls industrialio nur für diesen Test geladen wurde und danach keine Referenzen
hat, kann nach gesonderter Freigabe `sudo /usr/bin/rmmod industrialio` erfolgen.
Keine fremden Modulabhängigkeiten entladen. Unterschrift/Kernel-Taint wird durch
Entladen nicht rückgängig gemacht; die Controller-Rückkehr wird separat geprüft.

Abschluss nur lesend: Vorabcheck erneut, 100a/xpad/usbhid am selben Port und
normale manuelle Eingaben mit dem ursprünglichen xpad. Bei Abweichung Bericht,
kein automatischer Reset, Rebind-Versuch, Dongle-Replug oder Profilwechsel.

## Historischer 25-s-Entwurf für 109c — durch Test 002 ersetzt

Für neue Läufe gilt ausschließlich [HARDWARE_TEST_002.md](HARDWARE_TEST_002.md):
120 s mit Puffern, Clientgrenze 120 s/Kernelgrenze 135 s, gesondert freizugebende
Übergabe und kontrollierter Rückweg. Die untenstehenden alten Parameter und
Einzelaktionen sind kein aktueller Ausführungsplan; keine Freigabe daraus ableiten.

Erst nach separater Freigabe des Übergangs/Rückwegs und erfolgreichem 100a-Test.
Neuen Interface-Zustand und Endpunkte feststellen; niemals alte Adresse/PID
wiederverwenden. Deadband vollständig freigeben/beenden, tatsächlichen Besitzer
prüfen. Falls das Beenden auf 100a zurückschaltet, nicht als 109c-Erfolg behandeln.

Für einen bestätigten, konfliktfreien 109c-Zustand wird mit neu freigegebenem
Modulladen `test_pid=0x109c enable_output=1 session_ms=30000` gearbeitet.
Die Bindung alleine empfängt Daten, sendet aber keine Initialisierung.
Erst ein eigener freigegebener Schritt:

```sh
sudo "$PROJECT/build/gsnative-ctl" session "$NODE" 25
```

START sendet drei capturebestätigte GIP-Initialisierungspakete mit je 50 ms
Abstand, drei Heartbeats mit je 50 ms Abstand und anschließend Heartbeats alle
450 ms. Keine Profil-/Firmware-/Polling-Einstellung, keine Konfigurationswrites.

Die konkreten Einzelaktionen können vor START ausdrücklich freigegeben werden.
Ohne deren Freigabe die Sitzung nicht für weitere Aktionen nutzen. Die
Freigabedialoge verlängern die 25/30-Sekunden-Grenzen nicht; ein unvollständiger
Lauf wird beendet und nicht automatisch wiederholt.

Innerhalb derselben Sitzung, nach erfolgreichem `info` und `sample`, normale
Gamepad-Eingaben parallel prüfen. Rohgyro unverändert, Accel-Werte nur als
experimentell 8192 LSB/g bewerten; keine kalibrierten Achsen/1000-Hz-IMU behaupten.
Danach **jede Zeile einzeln freigeben**, jeweils spürbare Wirkung bestätigen und
mindestens eine Sekunde bis zur nächsten warten:

```text
pulse left 100 400
stop
pulse right 100 400
stop
pulse lt 100 400
stop
pulse rt 100 400
stop
quit
```

Kein Motor startet automatisch. STOP nullt alle Motoren; QUIT/EOF/Signal/Timeout
beendet die Sitzung und sendet das Nullpaket. Eine Sitzung pro Bindung; keine
automatische Wiederholung. 25 s Werkzeuglimit, spätestens 30 s Kernel-Sitzungsende,
400 ms Paketdauer ohne Wiederholung. Ein USB-erfolgreiches Nullpaket ist kein
mechanisches Feedback. Bei Fehler bleibt physischer Stopp bestmöglich.

Anschließend explizite Rückgabe/Entladung, der zuvor freigegebene manuelle
109c→100a-Rückweg und Nachweis xpad/usbhid. Ein bloßes xpad-Bind an 109c ist
kein gültiger Ersatz. Solange dieser Rückweg offen ist, bleibt dieser Abschnitt No-Go.

## Gemeinsame Abbruchbedingungen

Kernel-Oops/Warnung, USB-Transportfehler außer der eng begrenzten einzelnen
xpad-Abbaumeldung in Schritt 3, abweichende Identität/Port/Bindung,
Verlust von Interface 1, unstimmige Eingaben, keine frischen IMU-Daten, ungewollte
Dauer-Vibration, Erwärmung oder ein fehlgeschlagener Stop: sofort keine weiteren
Testbefehle, vorhandene Sitzung regulär beenden soweit möglich, Zustand sichern
und den passenden freizugebenden Rückweg verwenden. Keine Firmwareänderung,
USB-Reparatur oder Wiederholung. Original-Captures bleiben unberührt.
