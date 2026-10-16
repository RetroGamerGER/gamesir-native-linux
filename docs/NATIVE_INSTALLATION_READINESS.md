> Public export: personal tester, host and path references were anonymized. Historical evidence hashes refer to the private originals.

# Bereitschaft für eine native Alpha-Installation

Stand: 13. Oktober 2026. Entwicklungsergebnis und Voraussetzungen;
**keine Installations-, Aktivierungs- oder Hardwarefreigabe**.

Installation und dauerhafte Aktivierung wurden inzwischen separat freigegeben
und auf Garuda erfolgreich geprüft. Der Dienst bleibt aktiv und für den
nächsten Boot aktiviert. [Aktueller Nachweis](ALPHA_INSTALLATION.md#ergebnis-der-dauerhaften-aktivierung).
Die folgende Checkliste bleibt für spätere Installationen und offene
Integrationstests relevant; sie ist kein Auftrag zu weiteren Systemaktionen.

## Erreichte Grundlage

[Hardwaretest 003](HARDWARE_TEST_003.md) belegt den eigenständigen Start von
100a nach 109c ohne Deadband, tatsächliche Gamepad-/IMU-Daten und die bestätigte
Rückkehr zu xpad. Der frühere [native Motorvergleich](NATIVE_MOTOR_COMPARISON_RESULTS.md)
belegt zwölf spürbare und beendete Impulse aller vier Motoren bei gleichzeitig
laufenden Eingaben und IMU. Die früher für den Teststart notwendige manuelle
Deadband-Sitzung ist damit keine Voraussetzung mehr für den nativen Bootstrap.

Die Alpha erweitert diesen vorhandenen Pfad offline um Dauerbetrieb,
portunabhängigen Sitzungsmanager, Wiederverbindung/PM, Spiele-FF für die
Griffmotoren und Paketierung. [Laufzeit und Grenzen](ALPHA_RUNTIME.md),
[DKMS-/Arch-Paket und Deinstallation](ALPHA_INSTALLATION.md).

## Vor der ersten Installation und Aktivierung

| Bereich | Noch benötigter Nachweis beziehungsweise Entscheidung |
|---|---|
| Paket/Kernel | Exaktes gebautes Paket, Hash, laufende Kernelversion, passende Header, DKMS-Abhängigkeiten und mögliche Signierung frisch prüfen. Installation gesondert freigeben; zunächst ohne Dienstaktivierung. |
| Host-Hooks | Auf Garuda baut die Installation auch Kernelabbild und normale/Fallback-Initramfs neu. DKMS-Erfolg separat prüfen; Paketentfernung löst den Neubau ebenfalls aus. [Audit](ALPHA_INSTALL_AUDIT.md). |
| Automatische Übernahme | Aktivierung getrennt freigeben. Das bekannte nicht atomare sysfs-Fenster bei schnellem Ersatz am selben Port ist eine Alpha-Grenze, keine zugesicherte Racefreiheit. |
| Rückweg | `release` muss verwaltete Geräte stabil unter 100a/xpad bestätigen. Einen fehlgeschlagenen Rückweg konkret untersuchen; keine spekulativen USB-Resets oder Wiederholungsschleifen. |
| Dauerbetrieb | Längere Spielsitzung, Funk-Aus/Ein, Abziehen/Umstecken, Hubs, zwei Dongles, Suspend/Resume und Dienstende auf echter Hardware prüfen. Keine alten Hardwarefreigaben wiederverwenden. |
| Spiele und Motoren | FF_RUMBLE-Dauer, Überlagerung und Ende bei Spielabbruch testen. Viermotor-Anwendungsschnittstelle und SDL-/Steam-/Proton-Anbindung sind getrennte Nachweise; lokale API bedeutet keine automatische Spielunterstützung. |
| Zusatztasten | Codes 704–707 real nachgewiesen; L4=704, R4=705, L5=706, R5=707 mit nachträglicher Nutzerkorrektur dokumentiert. Direkte Spielbelegung zunächst unter Steam/Proton mit Constance prüfen, ohne vorab Spielaktionsprofile festzulegen. Embercade ist nicht installiert und kein Alpha-Blocker. [Analyse und Testplan](STEAM_PROTON_BUTTONS.md). |
| Sensoren | IIO-Rohdaten bleiben nutzbar; 8192 LSB/g experimentell. Gyrofaktor, Achsen und Bias unabhängig kalibrieren, bevor finale SDL-Sensoreinheiten freigegeben werden. |
| Deadband | Administrative native Freigabe vor exklusivem Deadband-Betrieb; später eine definierte Konfigurationsintegration. Keine parallelen USB-Schreiber. |
| Entfernung/Update | ALPM-Hook und Manager-Rückweg zunächst kontrolliert testen. Bei fehlgeschlagenem Stop/Referenzen Transaktion anhalten; Moduldateien müssen verfügbar bleiben. |

Zielplattformen sind Garuda KDE und CachyOS/Gamescope. Bisherige lokale Builds
gegen 7.2.9-2-garuda sind kein Nachweis einer bereits ausgeführten Installation
auf beiden Plattformen. Die unbekannten Typ-03-Berichte und der frühere
400-ms-Linksmotorbefund bleiben dokumentiert; sie entwerten nicht den
bestätigten längeren Motorvergleich.

Historischer, durch Eingaben bestätigter Hardwarezustand nach Test 003: 100a/xpad/usbhid,
`gs_native` entladen, normale KDE-Eingaben von [tester] bestätigt. Während der
Alpha-Entwicklung wurden keine weiteren Hardwareänderungen vorgenommen.
Das spätere ausschließlich lesende Alpha1-Audit fand dagegen 109c/xpad an IF0,
IF1 ungebunden und kein geladenes gs_native. Die Funktion dieser Momentaufnahme
wurde nicht getestet. Vor Aktivierung aktuelle Identität und Funktion frisch
prüfen; eine fremde bereits vorhandene 109c-Sitzung wird nicht übernommen.
