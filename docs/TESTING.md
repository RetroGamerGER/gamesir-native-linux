# Build- und Testverfahren

Alle Make-Ziele sind offline. Keine Installation, erhöhten
Rechte, USB-Kommandos, Modulaktivierung oder Treiberwechsel sind Bestandteil.
Voraussetzung: vorhandenes Python ≥ 3.11, Make und clang mit ASan/UBSan.

## Steam-SDL-Gyro ohne Steam-Start

Der vorhandene gerätefreie Sensorprüfer kann zusätzlich genau eine lokal
vorhandene SDL3-Bibliothek prüfen:

```sh
python -B tests/run_sdl_sensor_test.py --sdl3-library /path/to/Steam/ubuntu12_64/libSDL3.so.0
python -B tests/run_sdl_sensor_test.py --sdl3-library /path/to/Steam/steamrt64/libSDL3.so.0
python -B tests/run_sdl_sensor_test.py --sdl3-library /path/to/Steam/ubuntu12_32/libSDL3.so.0
```

Die Platzhalterpfade müssen zur vorhandenen Installation passen; kein Download.
Nur die SDL-Bibliothek wird schreibgeschützt in die bestehende Sandbox
eingebunden. Keine Steam-Anwendung, kein Runtime-Container und keine echte
Geräteöffnung. Der Prüfer kontrolliert geladenen Bibliothekspfad und SHA256;
ein Rückfall auf die Systembibliothek ist kein gültiger Erfolg. Die Fixture
deckt auch ältere glibc-`__fxstat`-Aufrufe ab. Pro Bibliothek sieben Szenarien,
darunter Gyro-only mit Zeitstempel und 32 A-/Paddle-Kombinationen. ELF32 wird
auf dem geprüften x86_64-Host erkannt und Fixture/SDL3-Probe mit `-m32`
gebaut; vorhandene Multilib-Header und Laufzeitbibliotheken sind Voraussetzung.
Keine Abhängigkeiten werden installiert. Die C-Konversionsprüfung für Python
bleibt im Host-ABI. Protokolle dieser erweiterten Suite liegen privat unter
`build/results/sdl-validation/sequence-v2/sdl3-<hash-prefix>/`; die alten
Protokolle bleiben erhalten. Ohne Zusatzoption werden weiterhin beide
System-SDL-APIs geprüft (14 Fälle, Bericht direkt unter `sequence-v2/`).

Der SDL3-Fall `observed-gyro` prüft zusätzlich Steams statisch beobachtete
Einschaltfolge Gyro/Accel/Gyro-L/Accel-L, Fehler für fehlende Sensoren,
fortgesetzte Gyroereignisse, Abschalten und erneutes Einschalten. Vier
künstliche Frames prüfen 1-ms-Fortschritt, identische Zeitstempel und einen
31-Bit-Überlauf. Jeder muss genau ein passendes Gyroereignis liefern. Diese
Prüfung reproduzierte einen Fixturefehler: ausgelassene Achsen hinterließen
Nullstrukturen, die als zusätzliche `SYN_REPORT` interpretiert wurden. Der
korrigierte Helfer packt nur vorhandene Achsen und einen Abschlussrahmen.
Das ist keine Korrektur des produktiven Treibers und kein Steam-Livetest.
Die Bibliotheken werden nicht ins Repository übernommen. SDL-Erfolg beweist
noch keine Freischaltung in Steam Input; [Befunde und Grenzen](STEAM_GYRO_FEASIBILITY.md).

## Manager-Reconnect und veraltete Getter

`python -B tests/test_manager_reconnect.py` verwendet die vorhandenen
Repository-Fakes für Geräte, Zeit und Kindprozesse, ergänzt durch einen
künstlichen sysfs-/Prozessbaum für die realen Guardfunktionen. Die anfängliche
16-Fälle-Version schlug vor der Korrektur in acht Fällen fehl und reproduzierte
unter anderem die dauerhaft falsche `released`-Sperre. Der aktuelle Bestand
enthält 34 gezielte Fälle und gehört zu `make test-alpha`/`make test`. Zusammen
mit den bestehenden 139 Managerfällen sind 173 bestanden; die komplette Suite
enthielt zu diesem Manager-Prüfpunkt 825 Python-Testfälle in 30 Teilprüfungen
plus C-/statische Prüfungen.

Geprüft werden Neuanmeldung während/vor/nach Getter-Abschluss, Busy-Guard,
zweite schnelle Geräteersetzung, Einzelverbrauch gepufferter Ergebnisse,
global/per-Port unvollständige Metadaten, Clientfristen, Fehlererhalt über
Managerneustart, fremde Instanzen/Hubwechsel, Pause und das unveränderte
Drei-Starts-Budget. Globale zweite Scanfehler dürfen auch an einem anderen
Port keine weiteren Aktionen mit dem alten Snapshot auslösen. Echte Fehler
bleiben verriegelt; unbekanntes EIO erlaubt keinen Neustart. Kein installierter
Manager, USB-/Input-Node, sudo, Dienst oder echter Reconnect wird verwendet.
[Korrektur und Abnahmegrenzen](MANAGER_RECONNECT_FIX.md).

## Optionale Trigger-Bridge

`make test-trigger-bridge` baut nur den Userspace-SDL2-Hook und prüft ihn
mit künstlichen SDL-/libusb-Bibliotheken. Temporäre Unix-Sockets, Fake-sysfs,
künstliche Character-Node-Metadaten und der Repository-Broker mit Fakebackend
ersetzen alle realen Geräte. Kein Wine/Steam, kein installierter Broker-/Client-
Import, kein Gruppenwechsel und keine Installation. Die Suite gehört zu
`make test`; die Buildvoraussetzungen cc/glibc/libusb-Header müssen bereits
vorhanden sein. Kein automatischer Paketnachbezug.

Regressionen prüfen genaue Quellen-/Instanzzuordnung, Geräteersatz am selben
Port, Manifestrechte, Wire-Version/Sequenz/Zeit/Session, volle und teilweise
Nullbarrieren, verspätete/überlastete Daten, EOF/CLOSE, lange Effekte, nur
Triggerkanäle bei erhaltenen Griffen sowie SDL3-/Fremdgeräte-Durchreichen,
Mehrfach-SDL, Threads/Fork und Transportfehler. Launcherprozesse sind gemockt.
Pakettests bauen/stagen nur in leere temporäre Verzeichnisse, prüfen Inhalte,
Rechte, Lizenz und reproduzierbare Quellen. Die frühere Forza-Hardwarebestätigung
und heutige Offline-Prüfung bleiben getrennt. [Details](TRIGGER_BRIDGE.md).

Bei der anschließenden reinen Steam-/Proton-Machbarkeitsprüfung wurden die
82 bestehenden Bridge-Fälle in sechs Teilprüfungen erneut ausgeführt. Kein
Steam-/Proton-/Wine-Prozess, Container oder realer Broker wurde verwendet.
Das bestätigt weiterhin den vorhandenen synthetischen Pfad und die gesperrte
Steam-Liveausführung, keinen funktionierenden Steam-Adapter.
[Statische Befunde und getrennte künftige Abnahme](STEAM_PROTON_TRIGGER_BRIDGE.md).

## Öffentliche README und allgemeine Nutzeranleitung

`make test-public-readme` bewahrt den vollständigen vorgegebenen Warnblock,
beide Project-Goals-Sätze, Original-Repositorylinks und unabhängige Würdigung.
Weitere gerätefreie Prüfungen kontrollieren lokale Links, Lizenz-/UAPI-Verweise
und das Fehlen persönlicher Angaben in README, INSTALLATION und RELEASE_AUDIT.
Die Tests lesen nur Dateien und benötigen weder Netz noch Hardware. Sie sind
Teil von `make test`. Die öffentliche Anleitung und der Auditbericht gehören
auch zur ausdrücklich aufgelisteten DKMS-Dokumentation.

## Kernelbau und Compilerwarnungen

Der lokale Kernel-Bauhelfer unterscheidet den vollständigen bekannten
Kbuild-Hinweis auf abweichende Compiler-Versionen von Quellcodewarnungen.
Eine akzeptierte Umgebungswarnung bleibt mit Anzahl und beiden Versionen im
JSON-Bericht sichtbar; sie wird nicht als warnungsfreier Build ausgegeben.
Unvollständige/zusätzliche Warnungen, Compilerfamilienabweichung und Baufehler
bleiben Fehler. Regressionen dazu laufen mit künstlichen Headern/Tools in
`test_kernel_toolchain.py`, ohne Module oder Geräte zu öffnen. Kbuild behält
`W=1` und `-Werror`. Der echte Offline-Bau ist von der gerätefreien Suite
getrennt und keine Lade-/Installationsfreigabe.

## Lizenz- und Paketbeigaben

`make test-licensing` prüft die vollständigen primären GPL-/Ausnahmetexte
anhand festgelegter Hashes, SPDX an der ersten möglichen Kommentarzeile aller
eigenen Quell-/Konfigurationsdateien und den gültigen Kernel-Modul-Lizenztag.
Nur der UAPI-Header trägt die dokumentierte Linux-syscall-Ausnahme.
Die Pakettests in `make test-alpha` prüfen Originalbytes, 0644-Rechte und
Lizenzpfade im Quellarchiv und Offline-Staging. Fehlende Lizenztexte stoppen
den Generator vor Ausgabe. Beide Prüfungen gehören zu `make test` und
installieren nichts. Herkunft und Grenzen: [Lizenzbericht](LICENSING.md).

## Lokales Gyrofenster ohne Hardware

`make test-imu-diagnostic` prüft zusätzlich das reine Wiedergabemodell:
Quaternionen, sechs Vorzeichen, Zeitintegration, Displaygain, Zentrieren,
Wiedergabetempo und Ablehnung beschädigter oder gemischter Datenströme.
`make test-gyro-viewer` benötigt das optionale PySide6 und führt Qt offscreen
mit Softwaredarstellung aus. Es prüft die tatsächlichen Bedienelemente,
Quellen-/Profilwechsel, Timerende, Schließen und überlappungsfreie Darstellung.
Kein Displayserver, keine Geräte, kein sudo und keine Paketinstallation nötig.
Die GUI-Abhängigkeit gehört nicht zum Kernel-/Manager-Paket oder zur
Pflicht-Testsuite. Die ursprünglichen 15 Modelltests und 8 GUI-Tests wurden zusätzlich an
sechs vorhandenen privaten Aufnahmen mit zusammen 40.486 Scans ergänzt;
Originalprüfsummen unverändert, fehlerhafte Aufnahme abgelehnt.
[Details und Grenzen](GYRO_VIEWER.md).

Die Live-Erweiterung ergänzt `test_gyro_live.py` im Diagnose-Testziel und
sechs weitere Qt-Tests: echte anonyme Pipes, GO/Samples/STOP, Fake-IIO,
erstes Go, Profilwechsel ohne Verlust der Transportprüfung, kein festes
Laufzeit-/Samplebudget, begrenzter Speicher, EOF/Heartbeat/Datenlücken,
blockierte Ausgabe, normale/fehlgeschlagene Rückstellung und unabhängiger
Nachcheck. Die Fensterprüfung umfasst Stopp, Schließen mit weiter sichtbarer
Rückstellung, Signal-Abbruch und Darstellung. Alle Gerätezugriffe/Startpfade
sind ersetzt; keine Live-Entdeckung oder Passwortabfrage im Test.
Alle 40.486 gespeicherten Scans wurden getrennt durch das neue Sampleprotokoll
geschickt; jede resultierende Orientierung entspricht exakt dem Offline-Modell.
Eine gerätefreie Simulation prüft 900×880 und 1080×900 Pixel. Keine Aussage
über echte Live-Latenz, Langzeitstabilität oder physikalische Kalibrierung.

## Kohärenter IIO-Strom und Winkelreferenz

Die Gyroreferenzmessungen sind auf Nutzerwunsch pausiert. Die vorbereiteten
Helfer werden nur gerätefrei geprüft: `test_iio_buffer_setup.py` simuliert
jeden Setup-Write, EBUSY, Geräteersatz und Rückstellung; `test_gyro_worker.py`
prüft GO/PING/STOP, EOF, Fehlererhalt und dauerhafte private Belege;
`test_gyro_guided.py` prüft je ein Go/eine Linksdrehung, Reaktionspuffer,
Ansagen, Dateiprüfsummen und menschliche Referenzbestätigung mit künstlicher
Zeit und GUI-Mocks. Keine echten Fenster, sudo oder IIO-/USB-Geräte. Diese
Tests sind Teil von `make test-imu-stream` und `make test`. Kein bestandener
Hardwarelauf oder bestimmter Gyrofaktor folgt aus diesen Simulationen.

```sh
make test-iio-buffer test-imu-stream
python -B tools/imu/gamesir_imu_stream.py configuration-plan
python -B tools/imu/gyro_reference.py plan --session yaw90left
python -B tools/imu/gyro_reference.py metadata-schema
```

Alles gerätefrei, ohne echte GUI. Der C-Test extrahiert die tatsächlichen
Kernel-Funktionen und prüft Pufferlayout, atomaren Sechsachsensatz, Zähler,
Hostzeit, Alignment, Fehler, Gate und Lebensdauer unter ASan/UBSan. Isolierte
Negativkontrollen müssen absichtliche Achsen-/Padding-/PM-Fehler erkennen.
Ein Durchstich führt synthetische Berichte durch den tatsächlichen C-
Produzenten, den Python-Binärleser und die Winkelanalyse. Das bestätigt die
Softwareabbildung, keinen Sensorfaktor. Keine echte IIO-Core-Nebenläufigkeit
oder Hardware wird dadurch geprüft.

Python prüft Chunkgrenzen, defekte/fehlende Scans, Fake-IIO-Metadaten,
ursprünglichen Fehlererhalt und private Binär-/JSONL-/Prüfsummenbundles.
Livezugriffe, Zeiten und Unterbrechungen sind vollständig gemockt.
Bekannte synthetische ±90°/±180°-Signale, Bias, Achsenannahmen und ungültige
Referenzfenster prüfen die Integration unter allen fünf Profilhypothesen.
Die Ziele sind Teil von `make test`. Ein echter Pufferlauf, Installation,
Aktivierung und Rückstellung brauchen neue konkrete Freigaben;
`configuration-plan` schreibt keine Attribute. [Ablauf und Grenzen](COHERENT_IMU_CALIBRATION.md).

## Experimentelle Gyrodiagnose

```sh
make test-imu-diagnostic
python -B tools/imu/gamesir_imu_diagnostic.py profiles
python -B tools/imu/gamesir_imu_diagnostic.py plan
```

Diese Aufrufe verwenden nur synthetische Dateien bzw. geben den Messplan
aus. Der Test prüft fünf Faktoren, Einheiten, Vorzeichen/Int16-Grenzen,
Rohdatenerhalt, Zeitlücken, nicht monotone Zeit, Herkunft/Streamtrennung und
Fehler bei künstlichen IIO-Dateien. Kein echtes IIO-, Input- oder USB-Gerät.
Das Ziel gehört zu `make test`; bestehende C-Umrechnung und Runtime bleiben
zusätzlich durch die bisherige Suite geprüft.

Der explizite `replay`-Modus verarbeitet reguläre gespeicherte Parserrecords;
`--profile all` vergleicht alle Hypothesen ohne automatische Auswahl. Neue
Ausgaben werden privat gespeichert, vorhandene Verzeichnisse abgelehnt.
`observe-iio` ist dagegen ein Hardwarelesezugriff und wird hier nicht ausgeführt.
Seine sechs Einzelwerte sind nicht atomar, daher keine Winkelintegration,
Gerätezeit, verifizierte Verlustrate oder SDL-Freigabe daraus ableiten.
[Aufrufbeispiele, Messphasen und spätere SDL-Abnahme](EXPERIMENTAL_GYRO_TEST.md).

Die Erweiterung `--guided-kde` wird ausschließlich mit künstlicher Zeit,
Fake-IIO und gemockten GUI-Prozessen geprüft. Reale KDE-Fenster werden in
der Suite nicht geöffnet. Geprüft werden Vorbereitung ohne Reads, lokale
Phasenfolge, Endansage ohne weitere Reads, Frist-/GUI-Fehler, Instanzwechsel
während der Vorbereitung, Erhalt von Teildaten und Aufräumen nur eigener
Prozesse. Eine erfolgreiche Simulation belegt keine echte GUI-Zustellung.

## Reproduzierbare Grundtests

```sh
make test
```

Prüft den übernommenen Python-Parser mit synthetischen positiven/negativen
Dateien, C-Sensorumrechnung und Motor-/Protokollzustände unter Address-/
UndefinedBehaviorSanitizer sowie den C/Python-Vergleich des kleinen echten
Zielgeräteauszugs. Dieser enthält keine
vollständige Sitzung und ersetzt nicht den privaten Vollvergleich.
Ausgaben/eigene Userspace-Binärdateien liegen in `build/`. Kein Kernel-Build,
uinput-Gerät oder Hardwarezugriff ist nötig.

`make test-protocol` prüft die Motor-/Protokollfälle getrennt: alle 15 Masken,
Triggerimpulse neben FF_RUMBLE, Stopps und Ablaufgrenzen, ungültige Anforderungen
ohne Teiländerung, Zeitüberlauf und unvollständige Pakete. Das ersetzt keine
nebenläufige Transport-, Hotplug- oder mechanische Prüfung.

`make test-startup` prüft den echten transportfreien C-Startautomaten mit
ASan/UBSan, 15 gespeicherten Übergangs-/Initialisierungspaketen, virtueller
Zeit und simulierten Geräteereignissen. 75 Fehlerfälle an den Sendestellen
sowie Identitäts-, Besitzer-, Frist-, Sensor- und Abbruchprüfungen verhindern
Fortsetzung nach Fehlern. Die beiden realen Paketabschnitte werden künstlich
verbunden; daraus folgt kein durchgängiger Hardwarestart ohne Deadband.
Zusätzliche Simulationen prüfen vier beliebige Topologietokens, zwei getrennte
Dongle-Sitzungen, Umstecken/Wiederverbindung sowie unabhängige IMU-Bereitschaft.
Die Linux-Anbindung erzeugt die Tokens jetzt aus neuen Probes und hält Root-/
Parent-Hub-Objekte fest. Die zusätzlichen Adapterfälle führen tatsächliche
Kernel-Funktionen mit künstlichen USB-Objekten/Systemaufrufen aus; echte
Parallelität und USB-Core bleiben außerhalb dieser Simulation.
[Kernel-Testnachweise](NATIVE_STARTUP_KERNEL.md).
[Vollständiger Testumfang](NATIVE_STARTUP_OFFLINE.md).

Zusätzlich prüft `tests/check_kernel_ff_lifetime.py` die tatsächlichen
Input-/FF-Registrierungs-, Callback- und Abbau-Funktionen mit simulierten
Linux-Referenzen unter ASan/UBSan. Elf Fälle decken sofortige/verzögerte
Input-Freigabe, offene Kontroll-FDs und Probe-Fehler ab. Vier isolierte
Negativkontrollen müssen den früheren FF-Besitzfehler als Use-after-free
beziehungsweise Double-free erkennen. Keine Gerätezugriffe; echte
Parallelität und reale Wiederverbindung bleiben gesonderte Nachweise.
[Fehler und Grenzen](FF_LIFETIME_FIX.md).

`make test-hardware-helper` prüft den Test-002-Ablauf mit virtueller Zeit,
künstlichen USB-Metadaten und einem künstlichen Client. Die 29 Prüfungen decken
vier getrennte Impulse, Puffer, fehlende Bestätigungen, Daten-/Geräteverlust,
Zeitüberschreitung, Kernelwarnungen und abschließende Datensicherung ab.
Der tatsächliche C-Client wird mit ersetzten Systemaufrufen unter ASan/UBSan
geprüft: elf Laufzeit-/Grenzfälle und vier Bootstrapfälle. Zusätzlich enthalten
sind zwei Test-003-Fälle und 34 gerätefreie Recorderkontrollen.
Es wird kein Geräteknoten geöffnet und kein echter Bindungsschritt ausgeführt.
`python -B tools/native/hardware_test_002.py show-plan` zeigt nur den Dateizeitplan.
Der getrennte Modus `execute-authorized` ist eine Hardwareoperation und braucht
die konkreten Freigaben aus [Hardwaretest 002](HARDWARE_TEST_002.md).

## Beobachtung vorübergehend leerer USB-Metadaten

```sh
python -B tests/test_bootstrap_observation.py
make test-hardware-helper
```

31 Fälle prüfen die reine Policy und die tatsächliche Warteschleife aus
`tools/native/bootstrap_observation.py`. Simulierte Zeit, Statusmeldungen und
Inventuren ersetzen sämtliche externen Zugriffe. Der Helfer selbst führt
keinen Resume/Release aus und öffnet keine Eingabe- oder USB-Geräte.

Der reale Fehlertyp `Empty USB metadata: .../bConfigurationValue (base 10)`
wird mit temporärer Neuanmeldung, vollständiger erneuter Inventur und
anschließender Validierung nachgestellt. Erfolgsszenarien sind synthetisch,
keine neue Hardwareabnahme. Geprüft sind außerdem dauerhafte Lücken ohne
Fristverlängerung, verspätete aktive Meldungen, blockierende Status-/Lease-/
Ausgabeschritte, Quarantäne trotz Kernelwarnung, fremde Ports, abweichende
Pfade/Felder/Zahlenbasen, aktuelle Fehlerdiagnosen gegenüber alter Historie
und strenge Prüfung nach Beginn der Eingabe-/IMU-Beobachtung.

Eine frische unvollständige Inventur nach einem bereits gecachten aktiven
Managerstatus führt zur erneuten vollständigen Prüfung. Erst die getrennte
exakte Instanz-/Parent-/Kernel-Token-/Lease-Validierung erlaubt den Observer;
keine Bereitschaft oder Besitzübernahme aus unbekannten Metadaten ableiten.
Der korrigierte bestehende Runner ist für den nächsten konkreten Lauf separat
vorbereitet. Eine frische Gerätezuordnung und neue Einmalfreigabe sind nötig.
[Plan und Beweisgrenzen](BOOTSTRAP_CACHYOS_FIX.md#offline-korrektur-des-beobachtungshelfers-und-vorbereiteter-neuer-lauf).

## Nativer Fünfminutenvergleich: Offline-Prüfung

Die getrennte Variante wird ohne Gerätezustand angezeigt:

```sh
python -B tools/native/hardware_test_002.py show-plan --variant motor-comparison-300
make test
make kernel-analyze
```

`make test` umfasst virtuelle Zeit für beide Ablaufvarianten, echte C-Client-
Logik mit künstlichen Systemaufrufen und Recorderkontrollen mit künstlichen
Prozessen/Metadaten. Dazu 1..1000-ms-Paketdauer, verbleibende Fristen und ein
Uhrsprung zwischen Flush und Versand im tatsächlichen Kernel-Sendepfad mit
ersetzten USB-/Lock-/Zeitfunktionen. Weder dumpcap noch Bubblewrap, sudo,
Geräteknoten oder Treiberbindung werden in diesen Tests aktiviert.
Vorhandene Header werden nur zum Modulbau verwendet; keine Installation.

Der kontrollierte Mitschnitt startet erst im separat freizugebenden
`execute-authorized`-Modus, niemals beim Anzeigen oder Importieren des Helfers.
Zeitplan, konkrete Freigabeschritte und Einschränkungen:
[NATIVE_MOTOR_COMPARISON.md](NATIVE_MOTOR_COMPARISON.md).

## Privater Vollvergleich und IMU-Analyse

Original-PCAPNG und große Ableitungen bleiben außerhalb von Git. Lokale Datei
`.local/project-paths.json`:

```json
{
  "capture_dir": "/Pfad/zum/gespeicherten/Messung-B-Verzeichnis",
  "deadband_source": "/Pfad/zum/lokalen/Deadband-Quellcode",
  "deadband_installed": "/usr/share/deadband"
}
```

Alternativ gelten `GAMESIR_CAPTURE_DIR`, `GAMESIR_DEADBAND_SOURCE` und
`GAMESIR_DEADBAND_INSTALLED`; sie haben Vorrang. Relative Pfade beziehen sich
auf die Projektwurzel. `/dev`, `/proc`, `/sys`, deren Unterordner und `/`
sind ausgeschlossen. Erwartet werden gespeicherte reguläre Dateien.

```sh
make test-capture
make analyze-imu
python -B tests/plot_imu_statistics.py  # optional: vorhandenes Matplotlib
```

Capture-Inhalt: `original-usbmon8.pcapng`, `derived/parser-records.jsonl`,
`derived/telemetry-raw.json`, `derived/initialization-0008-packets.json` und
`events.jsonl`. Relevante vorhandene SHA256-Werte werden geprüft. Die Analyse
vergleicht Deadband-Quellen ausschließlich lesend. Vollreplay vergleicht
12.204 IMU-Samples, schützt Rohwerte und blockiert unkalibrierte Sensorausgabe.
Ergebnisse: `build/results/`. Historische Berichte werden nicht überschrieben.

## Gerätefreie SDL-Prüfung

```sh
make test-sdl
```

Benötigt vorhandenes Bubblewrap, SDL3 und SDL2-Compat. Eigene Proben starten
nur in einer Sandbox mit sechs getrennten Namespaces, fünf leeren Capability-
Sätzen und NoNewPrivs=1. Keine Host-Input-, USB-, hidraw- oder usbmon-Knoten.
IIO-Datei und evdev-Antworten sind künstlich; Rohwerte stammen aus der kleinen
echten Fixture. Skalen bleiben Testkonstanten, keine G7-Pro-Kalibrierung.

Probeprogramme niemals direkt auf dem Host starten. Bei fehlendem Bubblewrap
oder fehlgeschlagener Isolation abbrechen; kein Host-Fallback, keine Reparatur.
Zwölf Fälle prüfen Erkennung, Zuordnung, fehlende Achsen, ungültige Auflösung
und synthetische Umrechnung. Neue Berichte: `build/results/sdl-validation/`.
Ältere lokale Berichte in `docs/sdl-validation/` bleiben erhalten und ignoriert.

`make test-sdl-buttons` verwendet dieselbe gerätefreie Isolierung für die
elf normalen und vier zusätzlichen Tasten sowie das erweiterte 17-Code-Profil.
Acht Fälle vergleichen SDL3 und SDL2-Compat mit/ohne Mapping. 256 künstliche
Druck-/Loslasskanten werden als echte Bibliothekszustände und -ereignisse
geprüft. Der FF_RUMBLE-Pfad endet an künstlichen ioctls; Trigger-Rumble meldet
hier weiterhin fehlende Unterstützung. Keine echte Motorwirkung.
[Auswertung und Anwendungslücken](SDL_EXTRA_BUTTONS.md).
Dieses Ziel ist auch Bestandteil von `make test-sdl`.

## Kernelbau und statische Prüfung

```sh
make kernel
make kernel-analyze
```

Erfordert die vorhandenen vorbereiteten Header des laufenden Garuda-Kernels,
clang/LLD und modinfo. Der externe Modulbau schreibt ausschließlich nach
`build/kernel/`, lädt/installiert nichts und erzeugt keine Autoload-Aliase.
`W=1 -Werror`, Clang Static Analyzer und checkpatch sind reproduzierbar.
CAMELCASE wird nur wegen der vorgeschriebenen USB-Deskriptornamen ausgenommen.
Sparse fehlt; KUnit ist im Zielkernel deaktiviert. Es wurden keine Pakete installiert.

`make test-runtime` prüft dieselbe C-Zustandslogik wie das Modul: Modusisolation,
Ausgabe-/Besitzersperren, begrenzte Sitzungen, ABI-Fehler und terminale Zustände.
Es übersetzt auch die tatsächliche Gamepad-Ausgabefunktion mit künstlichen
Input-Callbacks: zwei echte Fixtures und 32 künstliche Tasten-/Achsengrenzfälle.
`make test-capture` ergänzt diesen Vergleich um alle 5.244 gespeicherten
Gamepad-Berichte; der unabhängige Python-Parser liefert die Referenz.
`make test-tools` kompiliert den Entwicklerclient und führt nur `--self-test`
aus, ohne Geräte zu öffnen. Ganze Kernel-URB-/Workqueue-Races werden dadurch
nicht simuliert. Details: [Kernel-Prototyp](KERNEL_PROTOTYPE.md).

## Installierbare Alpha: ausschließlich Offline-Prüfung

Alpha3 ergänzt den experimentellen ZZZ-Direktstart: 125 Manager-Tests
einschließlich gemischter 100a/105e-Geräte, Startbudget, Instanzersatz,
fehlender Clientausgabe, Neustart nach END und verifizierter 105e/xpad-Rückgabe.
Die tatsächlichen Kerneladapterfunktionen werden in 108 Startup-, 54 Claim-,
22 FF-Lebensdauer- und 32 Motorpaketfällen geprüft. Vier negative Kontrollen
müssen den früheren FF-Speicherfehler weiterhin erkennen. C-Runtime und
Motorpfad laufen für 109c und 105e mit ASan/UBSan. Clienttests prüfen 105e-
Status, Direktstart ohne Handover-Flag und Ablehnung unbekannter PIDs vor OUT.

Die künstlichen 105e-Geräte verwenden die vorhandenen 109c-Protokollbytes.
Das prüft die beabsichtigte gemeinsame Implementierung, **nicht** die
Protokollgleichheit der Hardware. Reale ZZZ-Eingaben, IMU, Motorwirkung und
Rückkehr bleiben separat abzunehmen. Die historischen Hardwarehelfer 002/003
behalten ihren ursprünglichen Umfang; ihre festen PIDs nicht ungeprüft ändern.
[Umfang und Grenzen](G7_PRO_VARIANTS.md).

```sh
make test-alpha
make kernel-analyze
```

`test-alpha` ist Teil von `make test`. Es prüft den Sitzungsmanager mit
injizierter Zeit, künstlichen Topologien und Prozessen: mehrere Dongles,
Start-/Bindungsfehler, fremde Besitzer, Wiederverbindung, PM-Wiederaufnahme,
beendete oder hängende Kontrollclients, persistente Deadband-Pause und
verifizierte Rückkehr. Clienttests kompilieren den tatsächlichen C-Client
mit ersetzten Geräteaufrufen. Pakettests verwenden einen eigenen Stagingbaum
und simulieren ALPM-/DKMS-Rücknahmefehler. Importieren startet keinen Dienst.

Die Alpha2-Regression prüft besonders die tatsächliche ioctl-Sperre des
Kerneladapters bei fehlgeschlagenem Bootstrap, korrelierte END-Berechtigung,
alte/fremde/ersetzte Geräte, fehlende IMU und Initialisierungsfehler. Der
C-Client wird mit künstlichen Systemaufrufen geprüft: Besitznachweis auch
bei Fehlerstatus, positive 64-Bit-Tokens, Prüfung auf demselben FD vor END
und kein END bei abweichender Instanz. Managerfälle prüfen das Budget vor
Übernahme, Rückgabe trotz Startblockade, persistente Recovery-Daten und
Dienstneustarts ohne wiederholten Bootstrap/END. Die Entfernungsfälle prüfen
zusätzlich ungelöste Besitzdaten, verbliebene Prozesse und tatsächliche
Exitfehler nach einem scheinbar erfolgreichen systemd-Stop-Job.
Der private 100a-Claim wird mit künstlichen USB-Objekten geprüft: ungültige
Version/Metadaten, fehlende Rechte, Geräteersatz, falscher synchroner Aufrufer,
fehlende oder bereits verbrauchte Freigabe. Der Manager prüft den Claim-Vertrag
vor dem xpad-Unbind; ohne passende Kernelunterstützung bleibt xpad gebunden.
Paket- und Modulversion müssen exakt übereinstimmen.

Der lokale Viermotor-Broker und seine Anwendungsbibliothek werden mit
virtueller Zeit, künstlichen Geräten und lokalen Socketpuffern geprüft:
alle Kanäle, einzelne Stopps, lange Effekte, Clientabbruch, Leaseende,
Geräteersatz, konkurrierender Managerzugriff, ungültige Nachrichten und
begrenzte Bereinigung nach Fehlern. Datei-/ioctl-Aufrufe des Root-Adapters
werden im Test ersetzt. [API und Vertrag](HAPTICS_API.md).

Die Runtime prüft Spiele-FF auch für fünf Sekunden, eine Minute und eine
Stunde mit virtueller Zeit: fortlaufende Erneuerung kurzer Motor-Leases,
unabhängige Trigger, Nullwerte, Datenverlust und terminale Fehlerzustände.
Kerneladaptertests decken den Callback-/Worker-Vertrag und Kontroll-FDs nach
Disconnect ab. Sie ersetzen keine Kernel-Lockdep-/USB-Core-Stressprüfung.

Das Arch-Paket lässt sich mit vorhandenen Werkzeugen ohne Installation bauen;
die Befehle stehen in [ALPHA_INSTALLATION.md](ALPHA_INSTALLATION.md).
Die erzeugten Paketdateien, Hashes und Prüfergebnisse bleiben unter `build/`.
Paketbau darf keinen Dienst starten, kein Modul laden und weder sysfs-Bindungen
noch Benutzergruppen ändern. Freigabe für einen Build ist keine Freigabe für
`pacman -U`, DKMS-Installation oder `systemctl start`.

## Abgeschlossener Hardwaretest 001

Am 12. Oktober wurden native 100a-Eingaben für 60 s nach Nutzerfreigabe nur
lesend über evdev erfasst. Der ursprüngliche 12-s-Vorschlag wurde nicht
ausgeführt. Die kontrollierte Rückgabe an xpad ist lesend geprüft und vom
Nutzer im KDE Center bestätigt. Befunde und Grenzen:
[Hardwaretest 001](HARDWARE_TEST_001.md),
[kompakte Ergebnisse](HARDWARE_TEST_001_RESULTS.json).

Die vorgesehene Schlussruhe enthielt weiterhin Eingaben; der Nutzer erklärte
dies mit seiner Reaktionszeit auf die Chatansage. Für spätere freigegebene
Messungen lokal sichtbare/hörbare Phasensignale vorbereiten, reale Zeitmarken
behalten und tatsächliche Ruhefenster getrennt auswerten. Keine automatische
Wiederholung. Registrierung, Nutzerbestätigung und aufgezeichnete Ereignisse
sind unterschiedliche Nachweise und müssen als solche benannt werden.

## Künftige Hardwaretests — separate Freigabe

Der kontrollierte native Fünfminutenvergleich ist inzwischen abgeschlossen:
zwölf erfolgreiche, spürbare und beendete Ein-Sekunden-Impulse, gleichzeitig
Gamepad/IMU, isolierter vollständiger USB-Mitschnitt und bestätigte Rückkehr zu
xpad. [Ergebnis, Zeitbasen und Grenzen](NATIVE_MOTOR_COMPARISON_RESULTS.md).
Client-Snapshots sind nicht der vollständige IMU-Strom; der gespeicherte
USB-Mitschnitt ergänzt sie. Originale behalten, Folgeauswertungen getrennt
speichern und ihre Prüfsummen prüfen. Keine neue Freigabe aus alten Ergebnissen
ableiten. Der eigenständige Start ist inzwischen durch
[Hardwaretest 003](HARDWARE_TEST_003.md) validiert; die Dauerinstallation nicht.

Dies ist ein Verfahren, kein ausgeführter Test und keine aktuelle Freigabe.
Der ursprüngliche [109c-Test 002](HARDWARE_TEST_002.md) plant 120 s mit Übergangspuffern
und vier einzelnen 400-ms-Impulsen. Zeitgrenzen und Ausführungshelfer sind
[offline geprüft](HARDWARE_TEST_002_OFFLINE_CHECK.md); die Live-Ausführung bleibt
gesperrt, bis Ausgangszustand und konkrete Freigaben frisch vorliegen.
Der konkrete Sprint-003-Ablauf mit einzelnen Aktionen/Rückweg steht in
[HARDWARE_TEST_PLAN.md](HARDWARE_TEST_PLAN.md) und hat für den ersten Test Vorrang.

1. Ausgangszustand am physischen Port dokumentieren: VID/PID, Adresse,
   Funkverbindung, Interface-Bindungen, Programme. Konkrete Kommandos, Dauer,
   Stopps und Berechtigungen vorab freigeben lassen.
2. Deadband nur in eigens freigegebenem Lauf verwenden. Seine USB-Befehle
   können Identität/Treiberbesitz ändern. Profile und Firmware bleiben gesperrt,
   sofern nicht einzeln freigegeben.
3. Nur begrenzte Einzelimpulse; kein unkontrollierter Motorlauf. Keine
   automatischen Identitätswechsel, Wiederholungen oder Treiber-Rebinds.
4. Bei unerwarteter Identität/Bindung, Geräteverlust, USB-Fehlern, ausbleibendem
   Motorstopp, Erwärmung, Speicher-/Prüfsummenfehlern oder fehlgeschlagener
   Isolation sofort stoppen und Zustand dokumentieren.
5. Für einen freigegebenen Deadband-Lauf bekannten manuellen Rückweg vorher
   festlegen: „Release to games“, regulär schließen, Neuanmeldung abwarten.
   Dies garantiert keine erfolgreiche Rückgabe.
6. Anschließend lesend am selben Port prüfen: erwarteter normaler XInput-
   Zustand `3537:100a`, Interface 0 `xpad`, Interface 1 `usbhid`, normale
   manuelle Eingaben. Funkzustand separat bewerten; PID allein reicht nicht.
7. Fehlt der Ausgangszustand, keine automatische Reparatur/Rückbindung,
   USB-Reset oder erfundenen Rückschaltbefehl. Bericht und neue Freigabe.

Originaldaten behalten, Zeitbasis/Phasen/Fehler dokumentieren und SHA256 prüfen.
Fremder Busverkehr bleibt vertraulich. Git-/Offline-Arbeit erlaubt keine
neuen Aufnahmen oder Hardwareänderungen.

## Integrität

`SHA256SUMS` beschreibt die versionierten Dateien außer sich selbst. Nach
gezieltem, geprüftem Staging aktualisieren und separat aufnehmen:

```sh
python -B scripts/update_manifest.py
sha256sum -c SHA256SUMS
```

`docs/project-inventory.json` hält Hashes des ursprünglichen Bestands fest.
Zusätzliche Sicherung: `.local/pre-git/`, ignoriert und nicht zu veröffentlichen.

## Steam-/Proton-Zusatztasten: zusätzliche Offline-Prüfung

Der ergänzende `tests/test_steam_mapping_audit.py` ist in `make test-alpha`
enthalten. Künstliche Steam-Logs prüfen GUID-Auswahl, unveränderte Standard-
eingaben, nur vier neue Paddle-Felder, Fehlerfälle und begrenzte reguläre
Dateieingaben. Der Prüfer initialisiert kein SDL und öffnet keine Geräte.
`make test-sdl-buttons` prüft weiterhin die tatsächlichen System-SDL-Bibliotheken
in der gerätefreien Sandbox. Keiner dieser Tests beweist Steams Paddle-UI
oder die direkte Belegung im Spiel. Der separate Ablauf steht in
[STEAM_PROTON_BUTTONS.md](STEAM_PROTON_BUTTONS.md); echte Steam-/Constance-
Tests und Konfigurationsänderungen benötigen neue konkrete Freigaben.
Embercade ist ausdrücklich außerhalb des aktuellen Testumfangs.


## Regression: erwarteter USB-Abbau beim Bootstrap

`make test-startup` enthält nun 246 Fälle mit entnommenen tatsächlichen
Adapterfunktionen und ASan/UBSan. Entscheidend sind getrennte Ereignisse für
NOTATTACHED, RX-Completion/Resubmit, letzten OUT und den echten Disconnect.
Drei neue Reihenfolgen wurden zuerst am alten Adapter als Fehler reproduziert;
mit Korrektur erreichen sie die einmalige vollständige Übergabe. Ein fehlender
Callback muss trotzdem in die ursprüngliche Frist laufen, fehlerhafte/kurze
OUTs sowie fremde Ports/Instanzen dürfen nicht übernommen werden.

Die Folgekorrektur nach dem Revision-3-Realtest prüft zusätzlich unveränderliche
erste RX-Ursachen, logische Stilllegung nur des alten Empfangs nach OUT9,
Completion-/Submit-Rennen, ursprünglichen Fehler bei READY sowie gleichzeitigem
Supervisor-Signal. EPIPE/EPROTO während eines ausstehenden OUT9 bleiben fatal;
spätere Voll-Completion oder Disconnect dürfen diese Ursache nicht heilen.
Bei fehlender echter Abmeldung endet die unverlängerte Frist, während der
frühere RX-Befund getrennt erhalten bleibt. Lokale Cancel-/EPERM-Befunde und
erfolgreiche alte Callbacks erzeugen weder falsche Fehler noch neue RX-Submits.

`python -B tests/test_service_manager.py` prüft 139 Fälle einschließlich
fehlgeschlagenem Bootstrap, USB-Lücke, neuer unbesessener 109c, Dienstneustart
und der Trennung von verifizierter Bereinigung und erhaltener Fehlerhistorie.
Neue Metadatenfälle prüfen leere/ungültige Dezimal-/Hexfelder mit Attributpfad,
separate `port_errors` und unveränderte primäre Diagnose auch nach Neustart.
`make test` deckt außerdem bestehende Eingaben, Motoren, FF-Lebensdauer und
Paketierung ab. `make kernel-analyze` baut nur lokal und führt statische
Quellprüfung aus; es lädt kein Modul.

Details, Altcode-Negativkontrollen und Beweisgrenzen:
[Bootstrapkorrektur Garuda/CachyOS](BOOTSTRAP_CACHYOS_FIX.md).
Diese Tests ersetzen weder USB-Core-Parallelität noch einen freigegebenen
neuen Hardwarelauf und rekonstruieren keine fehlenden alten Transferdaten.

## SDL/Eden gyro extension (offline)

`make test-sensor test-sdl` covers the actual registration/report adapters,
selected profile arithmetic and installed SDL inside device-free Bubblewrap,
including simultaneous paddle combinations. `make test` retains the existing
regressions; `make kernel-analyze` builds and inspects without loading.
The optional `tests/check_eden_motion.py --source <private-sdl_driver.cpp>`
accepts only the documented pinned hash and performs no download or emulator
execution. See [SDL/Eden procedure](SDL_EDEN_GYRO.md) before any live action.
