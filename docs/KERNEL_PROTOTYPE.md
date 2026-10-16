# Sprint 003: implementierter Kernel-Prototyp

Stand: 12. Oktober 2026. Implementierung, Offline-Prüfung und erster kontrollierter
100a-Eingabetest abgeschlossen. Tatsächliche evdev-Ereignisse belegen die native
Gamepad-Verarbeitung; die xpad-Rückkehr ist lesend und durch Nutzerbestätigung
im KDE Center belegt. Grenzen: [Hardwaretest 001](HARDWARE_TEST_001.md).
Test 002 belegt inzwischen einen kontrollierten 300-s-Lauf mit nativen
109c-Eingaben, sechs veränderlichen IMU-Rohkanälen und zwölf spürbaren,
beendeten Einzelimpulsen an allen vier Motoren. USB-Pakete und parallele
Datenströme geprüft, Rückkehr zu xpad und normale KDE-Funktion bestätigt.
[Ergebnisbericht](NATIVE_MOTOR_COMPARISON_RESULTS.md). Deadband war noch für
den Übergang 100a→109c nötig. Ein expliziter eigenständiger Start ist inzwischen
[im Kernel angebunden und offline gebaut](NATIVE_STARTUP_KERNEL.md);
sein Hardwaretest und SDL/Steam bleiben offen.

## Build

```sh
make kernel
make kernel-analyze
make test
make test-capture
```

Ziel: installierter Garuda-Kernel und Header `7.2.9-2-garuda`, clang/LLD 23.1.1.
Kbuild baut mit `LLVM=1 W=1 -Werror` nach `build/kernel/gs_native.ko`.
Keine Installation, kein DKMS, keine udev-/modprobe-Konfiguration, kein `depmod`.
`make kernel` lädt kein Modul. Berichte: `build/results/kernel-*.{json,log,txt}`.
Das Modul benötigt `industrialio`; beide wurden für Hardwaretest 001 einzeln
freigegeben geladen. Nach dem Test ist gs_native entladen; industrialio blieb
ohne Referenzen geladen. Es wurde keine dauerhafte Installation vorgenommen.

## Tatsächlich implementiert

| Teil | Implementierung | Noch nicht hardwarevalidiert |
|---|---|---|
| Bisherige Testbindung | Exakter Interface-Name und PID erforderlich, nur Interface 0, ein Probeversuch pro Modulladung, keine USB-Autoload-Aliase/new_id; kontrollierte 100a-/109c-Bindung und Rückkehr getestet | Eigenständiger Start, Konkurrenz und allgemeiner Hotplug |
| Dynamischer Bootstrap | Standardmäßig aus; pro Gerät expliziter Auftrag, dynamischer Root/Hub/Port, neue Instanz nach Neuanmeldung, begrenzte optionale xpad-Übergabe nur dort | Gesamter eigenständiger Hardwarestart und Hotplug |
| 100a | Interrupt-IN 0x82; nur 20-Byte-XInput; echte Linux-Gamepad-Ereignisse für elf Tastencodes, D-Pad, Sticks und Trigger belegt | Native GUI/Spiel-Zuordnung, physische Tastenbeschriftung, vollständige Schlussruhe |
| 109c | Separater GIP-/IMU-/Guide-Pfad, derselbe RX-URB; echte gleichzeitige native Ereignisse und IMU belegt | Guide-Varianten, Dauerbetrieb und allgemeiner Hotplug |
| IMU | Sechs IIO-Rohkanäle, atomarer ioctl-Snapshot, Host-Monotonzeit, Frischeprüfung ≤1 s; echte veränderliche Rohdaten belegt | Kalibrierung und Hotplug |
| Beschleunigung | Gemeinsamer C-Kern mit experimentell 8192 LSB/g; rationale read-only Modulparameter; µm/s² | Physikalische Kalibrierung/Achsen |
| Motoren | Vier unabhängige Kanäle, 1..100 %, Impuls 1..1000 ms; ein exklusiver Entwickler-FD, Standard 30 s, explizite Sitzungsgrenze ≤315 s; zwölf 100-%-/1000-ms-Impulse mit Wirkung/Stopp bestätigt | Andere Intensitäten/Dauern, exakte mechanische Laufzeit, Fehlerfälle |
| OUT | Nur 109c + enable_output=1 + explizites START; drei belegte GIP-Init-Pakete, Heartbeats alle 450 ms, Guide-Ack falls angefordert; 300-s-Sitzung mit 697 erfolgreichen OUT-Transfers belegt | Dauerbetrieb und Guide-Ack auf echter Hardware |
| Ende/Fehler | Nullpaket bei regulärem Ende/FD-Schließen; einmaliger Stopversuch bei Fehler/Unbind; keine Reparaturschleife | Verhalten bei realem Linkverlust |

`kernel/gs_native_usb.c` ist der USB-/Input-/IIO-/misc-Adapter.
`src/gs_protocol.c` und `src/gs_sensor.c` werden direkt gemeinsam übersetzt,
keine Decoderkopien. `src/gs_startup.c` ist ebenfalls gemeinsam angebunden.
`src/gs_runtime.c` ist dieselbe geprüfte Zustands-/Moduslogik
für Userspace-Tests und Kernel. `include/uapi/gs_native.h` beschreibt die private
experimentelle ABI 1; sie ist noch keine langfristige öffentliche Treiber-ABI.

IIO `in_accel_x/y/z_raw` meint **Wire-A0/A1/A2**, `in_anglvel_x/y/z_raw`
**Wire-G0/G1/G2**. Die Namen behaupten keine bestätigte Gehäuseorientierung.
Es gibt bewusst keine IIO-SCALE/ODR und kein kalibriertes evdev-Sensorgerät.
`accel_experimental_um_s2` und `calibration_status` sind ausdrücklich experimentelle
Attribute. Gyrowerte bleiben unverändert; Gyrofaktor/Bias/Achsen bleiben offen.
Rationale Parameter `accel_counts_per_g_num/den` sind nur bei Modulladung änderbar.
Die Standardwerte entsprechen dem vorhandenen Profil 8192/1.

## USB- und Objektlebensdauer

Ein heapbasierter RX-Puffer und ein Interrupt-URB; Neuübermittlung mit GFP_ATOMIC
nur im laufenden Zustand. Einzelne fehlerhafte/unklare Berichte werden gezählt
und nicht als Eingaben interpretiert. Transportfehler stoppen die Neuübermittlung.
Der Fehlerworker beendet RX und neutralisiert Tasten/Achsen; kein Clear-Halt,
USB-Reset, Identitätswechsel oder automatischer Wiederanlauf.

Alle OUT-Vorgänge laufen unter einem Mutex, außerhalb von IRQ-/Input-Callbacks.
`usb_interrupt_msg` verwendet einen heapbasierten TX-Puffer und 250-ms-Timeout;
kurze Transfers gelten als Fehler. Runtime/Samples/Zähler sind spinlockgeschützt.
GIP-Guide-Acks nutzen einen begrenzten Platz; Überlauf führt zum Fehlerzustand.
Ein Treiber-Callback überträgt keine Pakete unter diesem Spinlock.

Die vier Neuplanungsstellen verwenden `system_percpu_wq`, den vom installierten
7.2.9-Header benannten Ersatz für das veraltete `system_wq`. Diese gezielte
Korrektur nach der Hardwarewarnung ändert keine Fristen, Sperren oder USB-Pakete.
Build und Symbolauflösung sind geprüft, ein echter 90-s-Lauf bleibt ohne diese
Warnung. Andere Kernelversionen und Langzeitverhalten sind noch nicht validiert.

Disconnect/Suspend/Reset/Shutdown setzen zuerst einen terminalen Zustand, töten
RX und warten auf den Worker **ohne gehaltenen OUT-Mutex**. Danach einmaliger
bestmöglicher Stop, Abmeldung der Geräte und Freigabe. `soft_unbind=1` erhält
beim manuellen Unbind die Möglichkeit des abschließenden OUT-Pakets.
Offene Entwickler-FDs halten einen kref; nach Quiesce/Disconnect liefern ihre
ioctls ENODEV. Die USB-Gerätereferenz bleibt bis zum letzten FD erhalten.
Ein offener FD verhindert außerdem das Entladen des Moduls; vor rmmod schließen.
Nach Suspend/Reset gibt es absichtlich keinen automatischen Empfangsneustart.

Ein physischer Stopp lässt sich bei abgezogenem USB, defektem Funklink, Firmware-
fehlern oder blockiertem Host nicht garantieren. Die Software begrenzt Impuls und
Sitzung; die gespeicherten Referenzpakete enthalten 400 ms ohne Wiederholung.
Für den neuen Motorvergleich kodiert der Kernel verbleibende Impulsfristen bis
1000 ms in 10-ms-Einheiten. Zwölf Ein-Sekunden-Pakete und erfolgreiche
Nulltransfers sind aufgezeichnet; ihre Spürbarkeit und ihr Ende bestätigt.
Ein fehlgeschlagener
Stop wird gespeichert und auch beim späteren END als Fehler gemeldet, nicht als Erfolg.
Scheduler-/Transferlatenz kann den softwareseitigen Stop verzögern. Kein Hardware-
Watchdog oder bestätigtes mechanisches Feedback wird behauptet.

## Entwicklerwerkzeug

```sh
make tools
build/gsnative-ctl --help
build/gsnative-ctl --self-test
```

Diese beiden Optionen öffnen keine Geräte. Erst explizite Unterbefehle mit
`/dev/gsnative-INTERFACE` öffnen den 0600-Testknoten. Ein Besitzer, O_NOFOLLOW,
ABI-/PID-Kontrolle, keine beliebigen USB-Pakete und keine Profil-/Firmwarefunktion.
Die interaktive `session` startet Ausgaben ausdrücklich, führt aber **keinen**
Motor automatisch aus. Kommandos: `info`, `sample`, `pulse lt|rt|left|right PERCENT MS`,
`stop`, `quit`. `stop` nullt alle Motoren, die Wartungssitzung bleibt aktiv;
`quit`/Timeout/Signal/EOF beendet sie. Überlappende Einzeltests lehnt das Werkzeug
ab. Auch SIGKILL führt beim FD-Schließen zum Kernel-Stopversuch; die Sitzung
ist unabhängig vom Userspace-Prozess auf maximal 315 s begrenzt. Standard
bleibt 30 s; längere Werte erfordern einen ausdrücklichen Ladeparameter.
Der Client erlaubt jetzt 1..300 s (Standard weiter 20 s), damit menschliche
Reaktionszeit und Puffer in [Test 002](HARDWARE_TEST_002.md) Platz haben.
Die Zeitgrenzen sind offline geprüft; der spätere 300-s-Lauf ist im
oben verlinkten Motorbericht dokumentiert.

Noch nicht implementiert: Standard-FF_RUMBLE im Kerneladapter, SDL/Steam-
Impulse-Trigger-API, IIO-Buffer, native Konfigurationsschnittstelle für Deadband
und dauerhafte automatische Modusverwaltung. Der explizite Bootstrap ist
inzwischen implementiert. Der vorhandene portable FF-Kern bleibt geprüft,
ist aber nicht mit einem unbegrenzten Kernel-FF-Callback verbunden.
Deadband darf während einer nativen Bindung nicht gestartet werden.

## Nachweise und Grenzen

- 44 vorhandene Python-Tests, C-Sensor-/Motor-Tests und neue Runtime-Tests unter ASan/UBSan.
- Runtime: PID-Isolation, Ausgabesperre, Besitzer, feste Sitzungs-/Impulsgrenzen,
  ungültige ABI, Zeitüberlauf, terminale Fehler-/Suspend-/Disconnect-Zustände.
- Capture: 12.204 IMU, 3.786 GIP, 1.458 XInput; zehn Motor-, 521 Wartungs-,
  21 GIP-Initialisierungs- und neun Identitätsübergangspakete. 17.448 Eingaben
  passieren die korrekte PID-Policy. Diese damalige Prüfung aktivierte keinen
  Übergang. Der neue Kerneladapter kann die Sequenz nach explizitem Bootstrap
  senden; seine Hardwareausführung steht noch aus.
- Die tatsächliche Gamepad-Ausgabefunktion wird mit künstlichen Input-Callbacks
  übersetzt und gegen den unabhängigen Parser geprüft: alle 5.244 gespeicherten
  Gamepad-Berichte, zwei ausgewählte echte Fixtures und 32 ausdrücklich künstliche
  Fälle für einzelne Tasten und Achsengrenzen. Kein Kernel-Input-Core wird ausgeführt.
- Clang Static Analyzer auf inzwischen fünf Kernel-Übersetzungseinheiten
  einschließlich des Startkerns: keine Befunde.
- Unabhängige Kopie des geprüften Git-Dateibestands: `make test` und `make kernel`
  bestehen auch ohne private Pfadkonfiguration. Das belegt verschiebbare Build-/
  Grundtestpfade, nicht identische Binärhashes bei unterschiedlichen Debugpfaden.
- checkpatch --strict: keine Fehler/Warnungen/Checks; nur CAMELCASE für die
  vorgeschriebenen USB-Deskriptornamen wird ausdrücklich ausgenommen.
- Sparse ist nicht installiert und wurde nicht ausgeführt. KUnit ist im
  installierten Kernel deaktiviert. Kein KUnit-Testmodul wurde geladen.
- Kontrollierte 100a-Bindung, Empfang und Unbind mit Beendigung des RX-URB
  sowie Rückgabe an xpad durchgeführt; kein Transportfehler gezielt injiziert.
  Workqueue-Races, Allocation-Fault-Injection, Suspend-/Reset-Integration,
  physischer Linkverlust bleiben ungetestet. Native mechanische Einzelmotortests
  sind inzwischen im oben verlinkten 300-s-Lauf bestätigt.

Beim ersten Build wurden veraltete Namen (BTN_RECORD/no_llseek) durch das
Zielkernel-API korrigiert. Ein neuer Test hatte zunächst eine falsche Erwartung
für den bereits terminalen Disconnect-Fehlercode; die Erwartung wurde korrigiert,
die terminale Logik blieb erhalten. Ergebnisse dieser Offline-Prüfung:
`SPRINT003_RESULTS.json`; spätere Hardwarebefunde: [Hardwaretest 001](HARDWARE_TEST_001.md).

Verwendete Primärreferenzen zusätzlich zu den installierten Headern:
[USB-Treiber/URBs](https://docs.kernel.org/driver-api/usb/writing_usb_driver.html),
[Kbuild für externe Module](https://docs.kernel.org/kbuild/modules.html),
[IIO-Kern](https://docs.kernel.org/driver-api/iio/core.html).

Weitere Hardwaretests benötigen neue Freigaben nach dem
[Hardwareplan](HARDWARE_TEST_PLAN.md); der abgeschlossene Test erlaubt keine
automatische Aktivierung oder Wiederholung.
