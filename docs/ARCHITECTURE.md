# Architektur und Schnittstellen

Aktuelle Übersicht. Der ausführliche bestehende Entwurf bleibt in
[ARCHITEKTUR.rst](ARCHITEKTUR.rst) erhalten. Die Alpha erweitert den vorhandenen
Kern, statt einen zweiten Protokollpfad einzuführen. Konfigurationsschnittstellen
sind Entwürfe, soweit hier nicht als implementiert benannt.

## Ein Treiber für die G7-Pro-Varianten

Verbindlich: ein `gs_native`-Modul und ein Manager mit gemeinsamem Protokoll-,
Input-, IMU- und Viermotor-Code. Editionen erhalten keine eigenen Treiberkopien.
Künftige bestätigte Unterschiede werden durch Variantenmerkmale für Erkennung,
Startstrategie, Reportformate und Fähigkeiten beschrieben. Gemeinsame Regeln
für Besitz, Sequenzen, Wiederverbindung und Motorstop bleiben zentral.

Nicht jede Variante muss `100a→109c` durchlaufen: Das beobachtete ZZZ-
Exemplar `105e` erhält in Alpha3 experimentell den Direktstart auf derselben
Instanz. Die Auswahl bleibt auf die expliziten PIDs 100a/109c/105e begrenzt;
eine PID bezeichnet keine individuelle Controller-UID. Gemeinsame Runtime,
Decoder und Ausgaben erhalten die tatsächliche PID. Der 105e-Pfad ist noch
nicht auf echter Hardware abgenommen.
Keine pauschale VID-Freigabe oder Übernahme unbekannter Protokolle.
[Variantenprüfung und konkrete Beleglücken](G7_PRO_VARIANTS.md).

## Implementierter Offline-Kern

`src/gs_startup.c` koordiniert den expliziten Start von 100a nach 109c ohne
Transportzugriff: begrenzte Übergangsfolge, Port-/Instanzprüfung über die
Neuanmeldung, native Initialisierung und einmalige Übergabe des Sequenzzählers
an die Runtime. Er verwendet die bestehenden Paketbuilder. Der Kerneladapter ruft ihn im
expliziten Bootstrap-Modus auf. Der ursprüngliche Steuer-FD und eine gesperrte
Liste halten den Auftrag über den Disconnect der ersten Instanz hinweg.
Die Kandidatenerkennung `gs_boot_supported()` ist portunabhängig. Pro Dongle
werden Anschluss-/Instanztoken dynamisch zugeordnet und eine eigene Sitzung
geführt; ein Übergang darf nicht einem passenden PID an einen anderen Port
folgen. Linux-Probe/Disconnect sind angebunden, reale Hub-Tests stehen noch aus. IMU-Bereitschaft und
Gamepad-Nachweis sind von der USB-Zuordnung getrennt. Die gespeicherten
USB-Seriennummern unterscheiden sich zwischen 100a und 109c und sind bisher
keine bestätigte gemeinsame UID.
[Kernvertrag](NATIVE_STARTUP_OFFLINE.md),
[Kernelanbindung, Besitz-/Referenzregeln und Tests](NATIVE_STARTUP_KERNEL.md).

`src/gs_protocol.c` dekodiert XInput/GIP/IMU, erzeugt belegte Paketbytes und
verwaltet vier getrennte Motorwerte/Ablaufzeiten. Er öffnet keine Geräte.
`gs_frame` erhält Rohachsen, Tasten, Trigger und IMU; `gs_haptics` führt
LT, RT, linken und rechten Griff in dieser Reihenfolge.

`gs_haptic_update` prüft Maske, Werte 0..100 und Dauer 1..1000 ms vor jeder
Änderung. `gs_haptic_ff` aktualisiert nur die Griffmotoren. Ablauf betrifft
nur den jeweiligen Kanal. `gs_runtime.c` und der Kerneladapter serialisieren
Änderungen. Auf einem Griff gilt die zuletzt angenommene Anforderung;
FF_RUMBLE verändert keine Trigger. Persistente FF-Ziele werden durch kurze
Leases erneuert und bei Stopp/Fehler verworfen. [Alpha-Laufzeit](ALPHA_RUNTIME.md).

Der zeitbehaftete Encoder kodiert verbleibende Impulsfristen in 10-ms-Einheiten
(aufgerundet), abgelaufene Kanäle sind null. Die bisherige Funktion
`gs_motor_packet` behält ihr 400-ms-Format für gespeicherte Referenzpakete.
Ein-Sekunden-Pakete sind offline und im kontrollierten nativen Hardwarelauf
geprüft; zwölf Wirkungen und Stopps wurden vom Nutzer bestätigt.
[Nachweis und Grenzen](NATIVE_MOTOR_COMPARISON_RESULTS.md).

`src/gs_sensor.c` trennt zwei Verträge:

- `gs_sensor_convert` verlangt bestätigte Skalierung, Orientierung und
  Bias-Behandlung; ohne diese Freigaben bleibt die Ausgabe unverändert gesperrt.
- `gs_accel_convert_experimental` nimmt einen rationalen LSB/g-Wert an und
  liefert µm/s² einschließlich Schwerkraft in Rohachsenfolge; Rückgabe
  `GS_SENSOR_EXPERIMENTAL`, keine Gyroumrechnung oder Bias-Annahme.

`tools/offline/gamesir_offline` ist der erhaltene unabhängige Python-Dateiparser.
Er kennt keinen Live-Transport und sendet keine Befehle.

## Kerneladapter und Alpha-Manager

Der Sprint-003-Adapter in `kernel/gs_native_usb.c` registriert nach ausdrücklicher
Testbindung ein Gamepad, in 109c ein IIO-Rohgerät und einen exklusiven Entwickler-
zugang mit privater ABI 1. `src/gs_runtime.c` begrenzt PID, Sitzungen und Impulse.
Die explizite Alpha-Option `persistent_mode=1` ergänzt einen Dauerbetrieb
ohne Entwicklerzeitlimit. Der historische endliche Modus und seine Tests bleiben
erhalten. Historischer Umfang: [KERNEL_PROTOTYPE.md](KERNEL_PROTOTYPE.md).

Ein USB-Besitzer für Interface 0 empfängt IN `0x82` und verteilt denselben
Datenstrom an Gamepad/Sensoren. Ein serialisierter OUT-`0x02`-Pfad ordnet
Initialisierung, Heartbeats, Antworten und Motorpakete. Interface 1 bleibt
außerhalb dieses Besitzers. Keine USB-Übertragung aus FF-/Input-Callbacks
unter einem Spinlock.

Neuanmeldungen eines laufenden Moduswechsels werden am dynamisch ermittelten
physischen Anschluss verfolgt; kein Produktionspfad darf auf `8-6` begrenzt sein.
Nach Übergabe hält die Runtime ihre Geräteinstanz, und ein neues Einstecken
beginnt eine neue Sitzung. Im Entwicklermodus gibt es keinen automatischen
Identitätswechsel. Der gesondert zu aktivierende Alpha-Manager prüft Geräte,
Besitzer und Versuchslimits, übernimmt gezielt xpad-Interface 0 und beauftragt
den vorhandenen Bootstrap. Er koordiniert Rückkehr, Wiederanmeldung und
begrenzte PM-Wiederaufnahme. Offene Steuerungsdateien dürfen nach Disconnect
nicht auf freigegebenen Speicher zugreifen.

`gs_native` ist der alleinige normale Laufzeitbesitzer. `xpad` ist Fallback
bei ausdrücklicher Deaktivierung/Deinstallation oder terminalem Fehler,
kein periodischer Teil des Spielbetriebs. Neue Übernahmen benötigen ein
vorher geprüftes Startbudget; Cleanup eigener Instanzen ist davon unabhängig.
Ein einmaliger privater `claim_100a` bindet die erste Übernahme an das konkrete
Kernelobjekt. Normales USB-Autoprobe darf diese Prüfung im Dauerbetrieb nicht
umgehen. Der endliche Entwicklermodus bleibt hiervon getrennt.
Ein gescheiterter Bootstrap kann bereits eine neue native Instanz besitzen:
Kernel-Tokens werden am alten und neuen Kontroll-FD abgeglichen, vor END auf
dem tatsächlich geöffneten FD erneut geprüft und als Recovery-Besitz
persistiert. PID, Modus, Besitz und Bereitschaft bleiben getrennte Zustände.
END allein beweist weder 100a noch xpad. Offene Rückwege blockieren Entfernung.
[Besitz, Fehlerpfade und verbleibendes sysfs-Race-Fenster](ALPHA_RUNTIME.md).

## Ausgabegeräte und Schnittstellen

| Ausgabe | Zweck und Voraussetzung |
|---|---|
| evdev-Gamepad, implementiert | `GameSir G7 Pro`, normale Tasten und eigene Codes 704–707, D-Pad, Sticks, Trigger; FF_RUMBLE für Griffmotoren |
| separates evdev-Sensorgerät, noch gesperrt | SDL: INPUT_PROP_ACCELEROMETER, ABS_X/Y/Z und ABS_RX/RY/RZ, passende eindeutige uniq, positive verifizierte Auflösung |
| ergänzendes IIO, implementiert | Sechs signed-16-Rohkanäle; neuer Offline-Stand zusätzlich Standard-KFIFO mit kohärentem Satz, Host-Zeit und Annahmezähler, standardmäßig aus; keine erfundene SCALE/ODR/Geräteuhr |
| private ABI 1, implementiert | Begrenzte Viermotor-Leases, Status und explizite Lebenszyklusbefehle; keine allgemeine USB-Passthrough-API |

Der [Viermotor-Broker](HAPTICS_API.md) ist Teil des Managers und teilt dessen
Kontrollbesitz. Spiele erhalten ausschließlich die begrenzte lokale API v1,
keinen USB- oder allgemeinen Root-Kontrollzugriff. Verbindungs-/Instanzkennung,
Heartbeat und getrennte Kanalfristen schützen nach Prozessende oder Reconnect
vor veralteten Befehlen. Die vorhandene private ABI erhält eine bedingte
Kanal-Cancel-Variante; sie ist kein erfundener Linux-FF-Effekttyp.
[Genaue Kernel-/Besitzersemantik](FOUR_MOTOR_KERNEL.md).

Die optionale [Trigger-Bridge](TRIGGER_BRIDGE.md) bleibt im Userspace:
selektiver SDL2-/Wine-Hook, privater sitzungsgebundener Transport und Relay
auf vorhandener Broker-API1. Kernel/Manager/Standard-FF bleiben unverändert.
Die Quelle wird über evdev→native IF0→USB-Metadaten mit einer konkreten
Brokerinstanz verbunden; Port/Adresse sind nur aktuelle Sitzungsdaten, keine
globale Identität. Neue Null-/Stoppzustände sind Warteschlangenbarrieren.
Geräteersatz/EOF/Überlast beenden die Lease statt alte Befehle neu abzuspielen.
Die integrierte Fassung benötigt eine eigene Hardwareabnahme; Steam/Proton
ist zunächst nur Planmodus, nicht schon eine universelle Spielanbindung.

Codes 704–707 bleiben unverändert. Die gerätefreie SDL-Prüfung bestätigt vier
getrennte Paddle-Ereignisse mit explizitem Mapping, zusätzlich zu allen normalen
Tasten. Automatisches SDL-Mapping allein ordnet sie nicht zu.
[Mapping und konkrete Anwendungsgrenzen](SDL_EXTRA_BUTTONS.md).

Die SDL-Tests prüfen Bibliotheksverhalten, nicht echte Geräteklassifizierung,
Zugriffsrechte oder Hotplug. Finale kalibrierte Sensorausgabe bleibt gesperrt,
solange Gyrofaktor, Orientierung und Bias fehlen.

## Deadband-Verträglichkeit

Die installierte Anwendung bleibt unverändert. Ihr bestehender libusb-Weg kann
Befehle senden, neu anmelden und einen Kernel-Treiber vorübergehend ablösen.
Gleichzeitiges natives Spielen ist auf diesem alten Weg nicht zugesichert.

Ein künftiger Adapter soll Fähigkeiten/bekannte Einstellungen über eine
versionierte Schnittstelle abfragen/ändern: exklusiver Schreiber, Generation,
explizites Commit und Rückleseprüfung. Persistentes Profilschreiben bleibt
vom Motorpfad getrennt. Polling-/Identitätsänderungen mit Neuanmeldung dürfen
nicht als unterbrechungsfrei dargestellt werden.

Die manuelle 100a-Bindung mit echten Eingaben und die anschließende Rückgabe
an xpad sind in [Hardwaretest 001](HARDWARE_TEST_001.md) belegt; die normale
xpad-Funktion bestätigte der Nutzer im KDE Center. Auch der kontrollierte
109c-Lauf mit Gamepad, IMU, vier Motoren und Rückkehr zu 100a/xpad ist inzwischen
[belegt](NATIVE_MOTOR_COMPARISON_RESULTS.md). Konkurrenz, allgemeiner Hotplug
bleiben offene Integrationstests. Hardwaretest 003 belegt inzwischen den
selbstständigen Start ohne Deadband, aber noch keinen installierten Dauerbetrieb.
Die private experimentelle
ioctl-ABI für den Testzugang ist implementiert, die langfristige
Konfigurations-ABI noch nicht. Das Kernelmodul besitzt keinen Autoload-Eintrag;
nach dem Test wurde es entladen. Der Alpha-Dienst übernimmt die spätere
Aktivierung erst nach gesonderter Freigabe. DKMS-/Arch-Paketierung und
Deinstallationskontrollen sind [implementiert](ALPHA_INSTALLATION.md).


## Entscheidung zur späteren SDL-Sensorausgabe

Die lesende DualSense-/SDL3-Prüfung empfiehlt zusätzlich zu IIO ein eigenes
Input-Sensorgerät, gespeist aus demselben GameSir-Decoder. Gamepad und Sensor
benötigen im geprüften SDL-Linuxpfad dieselbe nichtleere, pro Instanz eindeutige
`uniq`; gleicher Name oder gemeinsame VID/PID genügen nicht. IIO behält
unveränderte Rohdaten, das spätere evdev-Gerät normalisierte, korrekt skalierte
und orientierte Werte. Es wird kein zweiter USB-Besitzer benötigt.

Die Umsetzung bleibt bis zur eigenständigen Gyrokalibrierung und bestätigter
Achsen-/Biaszuordnung gesperrt. Die experimentellen 8192 LSB/g sind kein
Gyrofaktor; Sony-Ausgabeauflösungen sind keine GameSir-Kalibrierung. Die
verbindlichen Details und die offen benötigten Messungen stehen im
[DualSense-/SDL-Vergleich](DUALSENSE_SENSOR_COMPARISON.md). Dieser Auftrag hat
keine weitere Geräteschnittstelle implementiert oder registriert.

## Optional SDL gyro (18 October 2026)

The accepted IMU packet can additionally feed a separate evdev sensor node
under `experimental_gyro=1`, restricted to 109c. It shares a per-binding
nonempty `uniq` with the gamepad and exposes only the observed gyro axes at
100 counts/(degree/s), seven output counts per raw count. No second USB
reader or live IIO buffer is needed. Default remains off. See
[SDL/Eden integration](SDL_EDEN_GYRO.md) for time, permissions, lifecycle and
application limits; earlier raw-only architecture descriptions are historical.
