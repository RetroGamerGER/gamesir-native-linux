> Public export: personal tester, host and path references were anonymized. Historical evidence hashes refer to the private originals.

# Installierbare Alpha: Paketbau und späterer Betrieb

Aktuelle allgemeine Anleitung: [INSTALLATION.md](INSTALLATION.md).
Revision 11 bereitet die [Übernahme ohne xpad-Voraussetzung](STANDALONE_STARTUP.md)
offline vor und ist noch nicht auf Hardware abgenommen. Die folgenden Berichte
bleiben historische Nachweise ihrer jeweiligen Versionen.

**Historischer Realnachweis:** Am 15. Oktober bestand der ausdrücklich geplante,
vom Nutzer selbst ausgeführte CachyOS test host-Neustart mit anschließendem
Funkcontroller-Einschalten. Automatischer Dienststart, nativer Bootstrap,
GameSir-Inputgerät und fortbestehendes Steam-Paddle-Mapping bestätigt; [tester]
bestätigt vier unabhängige Paddles und normale Eingaben ohne manuellen
Start/Resume/Deadband. Keine zusätzliche Systemaktion durch Codex.
[Kontrollierter Boot-E2E-Fall und Grenzen](STEAM_GAMESCOPE.md#kontrollierter-neustart-am-15-oktober-bestanden).

Vorangegangene Bestätigung des CachyOS test host-Stands am 15. Oktober 18:16 MESZ: nativer
Dienst active/running/**enabled**, persistenter Startlink und gesunder
unpausierter Manager mit exakt passender aktiver 109c/gs_native-Lease.
Steam/Gamescope hat das Mapping übernommen; [tester] bestätigt alle vier
Paddles unabhängig und normale Eingaben. Der Zustand war schon vor dem
freigegebenen Codex-Vorabcheck vorhanden, daher kein redundantes enable/start.
Ein erneuter automatischer Rechnerneustart wurde nicht durchgeführt.
[Aktuelle Abnahme und Grenzen](STEAM_GAMESCOPE.md#gamescope-paddles-und-autostart-am-15-oktober-bestätigt).

Die folgenden Tagesabschlüsse dokumentieren ihre damaligen Zustände.

Vorangegangener CachyOS test host-Stand vom 15. Oktober 2026: **Revision 4 installiert
und erster korrigierter Bootstrap-/Eingabe-/IMU-Lauf erfolgreich**.
`gamesir-native-dkms 0.1.0.alpha3-4`, Kernel `7.2.9-2-cachyos-deckify`,
Srcversion `499FB2049A64E55F54B712C`. Der bereits geprüfte GCC-/DKMS-Bau und
die Paketintegrität wurden für diesen reinen Helferfix nicht verändert.

Genau ein freigegebenes Resume überführte 100a/21 nach 109c/22; neue Instanz
und native Lease vollständig bestätigt. 150 Sekunden Eingabe-/IIO-Beobachtung,
alle 15 Zielcodes mit Druck/Loslassen, volle Stick-/Triggerbereiche und sechs
IMU-Rohkanäle. [tester] bestätigt stabile normale Eingaben. Der native Betrieb
bleibt aktiv: Dienst active/running, paused=false, keine aktuellen Fehler,
Autostart weiterhin **disabled**. Ein Fehler-Release war nicht nötig und wird
nicht nachgeholt. Garuda test host bleibt unverändert auf Revision 3.
[Vollständige Abnahme mit Beweisgrenzen](BOOTSTRAP_CACHYOS_FIX.md#revision-4-korrigierter-bootstrap-realtest-bestanden).

Das ist eine erfolgreiche begrenzte Start-/Eingabeabnahme unter CachyOS,
keine Freigabe für Autostart, weitere Wiederverbindungen, Boot/Suspend,
Motoren oder Spieleintegration. Vier Zusatzcodes im Kernel sind noch kein
Nachweis ihrer Steam-Paddle-Erkennung. Die bestehende optionale Gamescope-
Erweiterung wurde danach separat freigegeben installiert: genau die beiden
Steam-Mappingpakete, alle Nachprüfungen bestanden und nativer Betrieb erhalten.
Steam wurde während der Installation nicht neu gestartet; die danach
bestätigte Paddle-Abnahme und der aktuelle Autostart stehen oben. Details: [Gamescope-Installation](STEAM_GAMESCOPE.md#installation-am-15-oktober-bestanden-steam-unverändert).
Die aktuellen Originaldaten bleiben privat und unverändert; Bericht und
Prüfsummen sind lokal gesichert.

Die bisherigen Installations-/Abbruch-/Rückwegschritte sind im
[chronologischen Bericht](BOOTSTRAP_CACHYOS_FIX.md) erhalten. Die folgenden
älteren Garuda-/CachyOS-Abschnitte gelten für ihre jeweiligen Zeitpunkte;
Betriebs- und Freigabestand steht oben. Allgemeine Befehle sind keine neue
Freigabe für das laufende System.

Historischer Garuda-Ausgangsstand: **`gamesir-native-dkms 0.1.0.alpha3-1`**,
mit experimentellem 105e-Direktstart im selben Modul/Manager. Die ausdrücklich
freigegebene Installation vom 14. Oktober 2026 ist abgeschlossen und geprüft.
Der anschließende begrenzte ZZZ-Realtest ist abgeschlossen; die reale
Steam-Abnahme für 105e und die physische Prüfung aller vier Zusatztasten
bleiben offen. Die optionale Steam-Zuordnung ist inzwischen separat offline
in `0.1.0.alpha2-1` ergänzt, aber noch nicht installiert.
[Realtest und Grenzen](G7_PRO_VARIANTS.md#vollständiger-zzz-realtest-am-14-oktober-2026).

Nach separat freigegebenem Modulladen und ZZZ-Test ist der globale Dienst
`inactive/dead`, weiterhin `enabled`, pausiert und ohne Leases.
`gs_native 0.1.0.alpha3` ist geladen, ungebunden, Referenzzähler 0. Der ZZZ
ist wieder an xpad; der andere Dongle blieb während des Tests unverändert.
Die folgenden allgemeinen Betriebs-/Rücknahmebefehle sind keine neue Freigabe.
Ältere Alpha2-Installations- und Aktivierungsberichte unten dokumentieren ihre
damaligen Zustände, nicht den aktuellen Dienst- oder Modulzustand.

## Kontrolliertes Alpha3-Update am 14. Oktober 2026

Die Pakettransaktion aktualisierte ausschließlich `gamesir-native-dkms` von
`0.1.0.alpha2-3` auf `0.1.0.alpha3-1`, aus Quellenstand `f8ef66b`.
SHA256 des installierten Pakets:
`d231829a8cdce0bab4ba0e42a915a5edb22990b8474a83b9f087148c0dbda750`.

| Prüfung | Ergebnis unmittelbar nach der Installation |
|---|---|
| DKMS | `gamesir-native/0.1.0.alpha3, 7.2.9-2-garuda, x86_64: installed` |
| Tatsächlicher Modulbau | Exit 0, keine Compilerwarnungen oder Compilerfehler |
| Modul-srcversion | `67138C65BCA95D0ABEAB517`, identisch mit dem geprüften Referenzbau |
| Paketintegrität | 82 Einträge, 0 verändert; alle 63 Nutzdateien bytegleich mit dem Paket |
| Upgrade-Hook | Dienst pausiert und gestoppt, vorheriges ungebundenes Modul entladen |
| Globale Verwaltung | `paused=true`, leere Leases; vorhandenes `enabled` erhalten |
| ZZZ-Dongle | Port `8-5`, `3537:105e`, Adresse 21, USB-Inode 107548, weiterhin xpad |
| Anderer Dongle | Port `8-6`, `3537:109c`, Adresse 17, USB-Inode 96718, weiterhin xpad |
| Garuda-Hooks | Snapper 73/74; normale und Fallback-Initramfs mit dracut gebaut |
| Optionale Steam-Komponente | unverändert `0.1.0.alpha1-1`, 17 Einträge, 0 verändert; nur 109c-Mapping |

Die beiden USB-Instanzen und ihre Bindungen blieben während der Installation
erhalten. Ports, Adressen und Inodes sind Beobachtungswerte dieses Laufs,
keine festen Auswahlregeln für den Produktionsbetrieb. Der installierte
Treiber wurde dadurch noch nicht an ZZZ-Hardware geprüft.

Der bekannte DKMS-Hinweis `Deprecated feature: CLEAN` trat erneut auf; der
Modulbau war erfolgreich. Im erfassten Kernelzeitfenster wurden keine neuen
Fehler oder Oops festgestellt, jedoch vier fremde Split-Lock-Warnungen.
Es wird deshalb keine vollständige Warnungsfreiheit behauptet.

Private Transaktions-, Build-, Integritäts- und Zustandsbelege liegen unter
`.local/integration/20261014T163354Z-alpha3-zzz/`. Die Modul- und Dienstangaben
in der Tabelle beschreiben den Installationsabschluss. Danach folgten separat
freigegebenes Modulladen und begrenzte ZZZ-Prüfung. Der abschließende Lauf
erreichte 180 Sekunden Beobachtung auf derselben 105e-Instanz; erfolgreicher
END und Rückkehr zu xpad sind bestätigt. [tester] bestätigt normale Eingaben
ohne Freeze sowie normale KDE-Eingaben nach der Rückkehr. L4/L5/R4/R5 wurden
möglicherweise nicht gedrückt und gelten nicht als physisch einzeln geprüft.
Die Testfreigabe ist verbraucht; weitere Übernahme oder globales Resume sind
damit nicht beauftragt. Der Lauf belegt weder allgemeinen Dauerbetrieb noch
Motorfunktion oder Steam-Paddles auf 105e.
[Vollständiger Realtestbericht](G7_PRO_VARIANTS.md#vollständiger-zzz-realtest-am-14-oktober-2026).

## Ergebnis der kontrollierten Erstinstallation

Installiert wurde genau `gamesir-native-dkms 0.1.0.alpha2-1` aus Quellencommit
`8d566f0d742af52ca2841ac7e4d90f7530d05f0c`. Paket-SHA256:
`bc7538c19172597698f6abff3f57c4b935579fb97c572cf98e8068371d075b72`.
Vorher wurden Paket, Abhängigkeiten, Kernel/Header, freie Kapazität, fehlende
Paketdatenbanksperre und alle elf gespeicherten Hook-/Konfigurationshashes
geprüft. Die tatsächliche interaktive Pakettransaktion enthielt nur dieses
Paket, ohne zusätzliche Installation oder Upgrades. Passwortabfrage über
ksshaskpass; pacman und die Transaktion endeten mit Status 0.

Die lesende Nachkontrolle am 13. Oktober 2026 um 16:18 UTC ergab:

| Prüfung | Ergebnis |
|---|---|
| DKMS | `gamesir-native/0.1.0.alpha2, 7.2.9-2-garuda, x86_64: installed` |
| Modul | `0.1.0.alpha2`, vermagic `7.2.9-2-garuda SMP preempt mod_unload` |
| Installierter Modulpfad | `/usr/lib/modules/7.2.9-2-garuda/updates/dkms/gs_native.ko.zst` |
| Reales DKMS-Bauprotokoll | Exit 0, keine Compilerwarnungen/-fehler |
| Paketintegrität | 75 Einträge, 0 veränderte Dateien |
| systemd | `disabled`, `inactive/dead`, MainPID 0, NRestarts 0 |
| Laufendes Modul | `gs_native` nicht geladen |
| USB-/Bindungsmetadaten | Vor/nachher identisch: 3537:109c, Port 8-6, Adresse 16; IF0 xpad, IF1 ungebunden |

Das bestehende xpadneo-DKMS-Modul blieb weiterhin installiert. Die vorhandenen
Garuda-Hooks legten Snapper-Snapshots 65/66 und die Haptikgruppe an, bauten DKMS
und erneuerten Kernelabbild sowie normale/Fallback-Initramfs wie vorher geprüft.
Es wurde weder ein Dienst aktiviert noch ein Treiber geladen oder umgebunden.
Der Metadatenvergleich öffnete keine USB-/Input-Geräte und ist kein neuer
Funktions- oder Hardwaretest.

**Dokumentierte Abweichung:** DKMS meldet `Deprecated feature: CLEAN` für die
vorhandene Paketkonfiguration. Das reale Modul wurde trotzdem erfolgreich
gebaut und installiert. Keine automatische Konfigurationskorrektur, kein
Paketneubau und kein weiterer Systemschritt erfolgten. Der Hinweis ist vor
einer späteren Paketrevision zu bereinigen; er ist kein gescheiterter Modulbau.

Private vollständige Belege einschließlich Transaktionsprotokoll,
Vor-/Nachzustand, DKMS-Baulog, installiertem Modulhash und SHA256-Liste liegen
unter `.local/installations/20261013T161540Z-alpha2/`. Sie werden nicht in Git
aufgenommen. Das unveränderte Releasepaket und seine früheren Offline-Nachweise
bleiben unter `build/alpha2-release/` erhalten. Die Installation allein bestätigt
keinen Plug-&-Play-Dauerbetrieb; der folgende separat freigegebene Schritt
erweitert die Beleglage.

## Ergebnis der dauerhaften Aktivierung

Am 13. Oktober 2026 wurde das unveränderte installierte Alpha2-Paket aus
`8d566f0` nach erneuter Prüfung aktiviert. Frischer Ausgangszustand: Kernel
`7.2.9-2-garuda`, passendes DKMS-Modul, Dienst deaktiviert/inaktiv,
`gs_native` ungeladen, `3537:100a` am Port `8-6`, Bus 8, Adresse 17,
Interface 0 an xpad und Interface 1 an usbhid. Der erhöhte lesende Check
fand keinen fremden Geräte-/Kontrollzugriff. Dienstdatei, Modulparameter und
der unten dokumentierte Rückweg wurden vor dem Start geprüft.

Der vorher gezeigte und ausdrücklich freigegebene einmalige Befehl war:

```sh
sudo systemctl enable --now gamesir-native.service
```

Die grafische Passwortabfrage erfolgte über ksshaskpass. Der Befehl endete
mit Status 0 und legte den Autostartlink in `multi-user.target.wants` an.
Der Dienst lud das Modul mit `bootstrap_mode=1`, `enable_output=1` und
`persistent_mode=1`. Nach akzeptierter normaler Gamepad-Eingabe folgten
ohne Deadband der eigenständige Übergang `100a/17 → 109c/18` und die gezielte
Übernahme des neuen Interface 0. Kernelmeldung: `native bootstrap finished: 0`.
Der Manager meldete `ready` und anschließend dauerhaft `phase=active`.
Kein endlicher Hardwaretesthelfer, START/END-Entwicklerlauf oder Motorimpuls
wurde parallel zum Dienst gestartet.

Lesende Abschlusskontrolle um **16:41:14 UTC / 18:41:14 MESZ**:

| Prüfung | Ergebnis |
|---|---|
| Dienst | `active/running`, `enabled`, `Result=success`, `NRestarts=0` |
| Manager | `ok=true`, `paused=false`, keine Scan-/Portfehler, `phase=active` |
| Modul | `0.1.0.alpha2`, srcversion `C6D05D71208991F6D5900C1` |
| Parameter | Bootstrap, Ausgabe und Dauerbetrieb jeweils aktiv |
| USB | `3537:109c`, Bus 8, Adresse 18, Port `8-6` |
| Bindung | Interface 0 `gs_native`, Interface 1 ungebunden |
| Input | `GameSir G7 Pro`, in diesem Lauf `/dev/input/event13` |

`returned=false` ist hier der erwartete Zustand einer aktiven nativen
Sitzung, keine fehlgeschlagene Rückgabe. Es wurde kein Rückweg angefordert;
Dienst und native Bindung bleiben zum Spielen aktiv. Eventnummer, Adresse
und Testport sind Momentaufnahmen und keine Produktionskonfiguration.
Normales Spielen erfordert keinen Terminalstart und keine Passwortabfrage.
`enabled` bestätigt die Autostartkonfiguration, noch keinen realen Boot-Test.

### Eingaben und korrigierte physische Tastenbeschriftung

Zwei überlappende, ausschließlich lesende evtest-Beobachtungen ohne Grab
erfassten die manuellen Eingaben. Nach Entfernung von 426 gleichen Ereignissen
aus dem Überlappungsfenster bleiben 43.047 Ereignisse: 31.709 EV_ABS,
902 EV_KEY, 10.426 SYN_REPORT und 10 EV_FF. Kein SYN_DROPPED. Alle elf
normalen Gamepad-Tastencodes sowie 704–707 enthalten Drücken und Loslassen;
über die gesamte Aufnahme sind die Kanten jedes Tastencodes ausgeglichen.
Alle vier Stickachsen erreichen −32768 bis 32767, beide Trigger 0 bis 1023,
beide D-Pad-Achsen −1 bis 1. Der Treiber registriert darüber hinaus 167 und
708; diese beiden Codes wurden nicht getestet.

Die ursprünglichen Ansagen lauteten L4, R4, L5, R5. [tester] stellte anschließend
ausdrücklich klar, dass er dabei die falschen Tasten gedrückt und die Paare
L4/L5 sowie R4/R5 vertauscht hatte. Seine vorherige Bestätigung der Ansagen
ist damit korrigiert. Die folgende Zuordnung verwendet **diese nachträgliche
Nutzerkorrektur**; die gespeicherten Ansagen und Ereignisse bleiben unverändert:

| Ansage | Tatsächlich gedrückt laut Korrektur | Code | Druck-/Loslasskanten im inneren 20-s-Fenster |
|---|---|---|---|
| L4 | L5 | 706 | 50 / 51 |
| R4 | R5 | 707 | 53 / 53 |
| L5 | L4 | 704 | 50 / 51 |
| R5 | R4 | 705 | 55 / 55 |

Jedes innere Fenster beginnt zwei Sekunden nach dem gespeicherten Marker
und enthält genau einen der vier Zusatztastencodes. Einzelne ungleiche
Kantenzahlen entstehen an den Ausschnittgrenzen; vollständig sind alle
Tasten wieder losgelassen. Daraus ergibt sich L4=704, R4=705, L5=706, R5=707.
Keine Änderung der Kernelcodes, Parsernamen oder installierten SDL-Zuordnung
ist dafür erforderlich. Die Beschriftung ist nutzerzugeordnet, kein neuer
USB-Paketnachweis. [Bytepfad](PROTOCOL.md#physische-zusatztasten),
[separate SDL-/Embercade-Grenzen](SDL_EXTRA_BUTTONS.md).

Die Ansagen erfolgten mit menschlichen Reaktionspuffern. Chat-/Werkzeuglatenz
verlängerte die Phasen; gespeicherte Marker sind keine präzisen Zustellzeiten.
Der Vorbereitungsmarker wurde verspätet gespeichert. Die Aufnahme endete vor
der letzten Ruheansage: kein Nachweis einer vollständigen Schlussruhe,
Langzeitdrift oder TMR-Kalibrierung. Kein fehlerfrei nach ursprünglicher
Beschriftung durchgeführter Einzelansagenlauf wird behauptet.

### Meldungen, Grenzen und Datensicherung

Beim Ablösen von xpad erschien die bereits untersuchte Meldung
`usb_submit_urb ... -2` im xpad-Abbaupfad. Danach waren Bootstrap und Eingaben
erfolgreich. Keine neue gs_native-Fehlermeldung oder Kernel-Backtrace während
des Prüfintervalls. Daneben enthalten die privaten Hostlogs fremde
Split-Lock-Meldungen und Netzwerkmount-Ereignisse; sie werden nicht als
GameSir-Fehler ausgegeben und nicht ungefiltert in Git veröffentlicht.

Die zehn EV_FF-Ereignisse betreffen Effektplatz 0 am Beginn der Beobachtung.
Dieser Test hat keine Effekte hochgeladen oder Motorentests beauftragt.
Absender, Amplitude und mechanische Wirkung sind aus evtest nicht ableitbar;
diese Einträge beweisen keinen Spiele-Rumble-Test. Die bisherigen getrennten
Motor-/IMU-Belege bleiben erhalten. Die finale Gyro-Skalierung und allgemeine
SDL-/Steam-/Embercade-Unterstützung werden dadurch nicht erweitert.

Private vollständige Belege: `.local/activations/20261013T162431Z-alpha2/`.
Enthalten sind Vorzustand, Aktivierungsprotokoll, Manager-/Kernel-/Dienstlogs,
Input-Fähigkeiten, unveränderte evtest-Ausgaben, Ansagen, Auswertung mit
Nutzerkorrektur und Abschlusszustand. `SHA256SUMS` sichert diese Dateien;
Rohlogs bleiben lokal und werden nicht committed. Paket und laufende
Programmdateien wurden nach der Aktivierung nicht geändert.
Die fünf gerätefreien Mapping-Vertragstests bestehen weiterhin; 71 lokale
Dokumentverweise wurden geprüft. Änderungen dieses Abschlusses betreffen
ausschließlich Dokumentation und Prüfsummen, keinen neuen Modulbuild.

**Ergebnis:** Freigegebene dauerhafte Aktivierung und native Eingabeprüfung
erfolgreich. Für normalen Spielversuch bereit. Boot, Funk-Aus/Ein, USB-Hotplug,
Suspend/Resume, lange Spielsitzungen und kontrollierte Deinstallation bleiben
separate reale Integrationstests; keine allgemeine Zuverlässigkeitsfreigabe.

## Lieferumfang und Voraussetzungen

Das Arch-Paket `gamesir-native-dkms` enthält den vorhandenen C-Kern, den
externen Kerneladapter als DKMS-Quellen, den Kontrollclient und einen
Systemdienst. Es installiert keine Firmware, keine xpad-Blacklist und keine
USB-Autoload-Aliase. `xpad` und `usbhid` bleiben verfügbar. Der Dienst übernimmt
nur die vom Sitzungsmanager einzeln geprüften GameSir-Interfaces.

Zielsysteme sind Garuda KDE und CachyOS einschließlich Gamescope. Der Dienst
arbeitet systemweit und benötigt keine Desktop-Sitzung. Das beweist noch
keine erfolgreiche Installation auf beiden Distributionen oder vollständige
SDL-/Steam-/Embercade-Unterstützung. Die endgültige IMU-Sensorausgabe bleibt
von der unabhängigen Gyroskopkalibrierung abhängig.

Benötigt werden Arch-Paketwerkzeuge, `dkms`, `python`, `systemd`, `kmod`,
`clang`, `llvm`, `lld`, `make`, ein C-Compiler für den Client und **passende Header für
jeden Zielkernel**. Das kann je nach installierter Variante beispielsweise
`linux-zen-headers` oder ein zum CachyOS-Kernel passendes Headerpaket sein.
Kein generisches Headerpaket ersetzt die Prüfung der tatsächlichen Version.
Die Paketabhängigkeiten installieren nicht automatisch den richtigen Kernel.
Secure Boot beziehungsweise verpflichtende Modulsignaturen können eine
separat freizugebende Signierung erfordern; die Alpha umgeht diese Prüfung nicht.

## Offline bauen und prüfen

Die folgenden Befehle erzeugen ausschließlich Dateien unter `build/`:

```sh
make tools
python -B tests/test_packaging_alpha.py
python -B scripts/package_alpha.py source --dest build/alpha-source
python -B scripts/package_alpha.py stage --dest build/alpha-staging --client build/gsnative-ctl
```

Zielverzeichnisse müssen leer sein oder noch fehlen. Bestehende Ergebnisse
werden nicht gelöscht oder überschrieben. Der Quellarchivbau verwendet eine
enge Dateiliste und normalisiert Reihenfolge, Eigentümer und Zeitstempel.
`SOURCE_DATE_EPOCH` ist optional und beträgt standardmäßig `0`. Unveränderte
Quellen und derselbe Zeitwert ergeben identische Archive. Die generierte
`PKGBUILD` enthält die tatsächlich berechnete SHA256 des Archivs.

Die Quell- und Installationspakete enthalten die ausdrücklich aufgelistete
Markdown-Projektdokumentation sowie das experimentelle Kalibrierungsprofil.
Unter `/usr/share/doc/gamesir-native/` bleiben `README.md`, `AGENTS.md` und
die Unterstruktur `docs/` erhalten, damit die Dokumentlinks funktionieren.
Private Messdaten, historische Analyseausgaben und die vollständige
Entwicklungstestumgebung bleiben im Entwicklungsrepository; das Quellarchiv
ist ein gezielter Paketbauauszug, kein vollständiger Repository-Ersatz.

Ein Paket kann später ohne Installation gebaut werden:

```sh
cd build/alpha-source
makepkg --nodeps --cleanbuild
```

`--nodeps` erlaubt nur den Offline-Paketbau bei bereits vorhandenen Werkzeugen;
es ersetzt keine Abhängigkeitsprüfung vor einer echten Installation. Kein
`-s`, `-i`, Paketmanager-Refresh oder Aufruf mit Rootrechten gehört zum
Offline-Bau. `makepkg` baut den Client und prüft dessen Selbsttest. Der
eigentliche Modulbau erfolgt durch DKMS für jeden Zielkernel. Er muss vor
einer Aktivierung erfolgreich geprüft sein.

## Verfahren für weitere Installationen: gesonderte Freigabe

Das frühere Update von Revision 1 auf `0.1.0.alpha2-2` wurde am 14. Oktober
abgeschlossen und anschließend separat wieder aufgenommen. Dazu gehört der
[gesonderte Upgrade-/Wiederaufnahmeplan mit Ergebnisbericht](MANAGER_CONFLICT_FIX.md).
Der bestehende Upgrade-Hook stoppt den Dienst und entlädt das ungebundene
native Modul vor dem Austausch; die anschließenden DKMS-/Boot-Hooks gehören
zur ausdrücklichen Freigabe. Ein Manager-/Client-Fix ist kein modulneutrales
Paketupdate. Historische Erstinstallationsbelege oben bleiben unverändert.

Die konkreten Paketdatei- und Kernelversionen werden vor einer Installation
neu geprüft. Das folgende Beispiel verwendet den inzwischen installierten
Alpha3-Stand; es ist **keine Aufforderung, die abgeschlossene Installation zu
wiederholen**:

```sh
sudo pacman -U ./gamesir-native-dkms-0.1.0.alpha3-1-x86_64.pkg.tar.zst
dkms status
modinfo gs_native
```

Die Paketinstallation legt Quellen unter
`/usr/src/gamesir-native-0.1.0.alpha3/{kernel,src,include}` ab. Diese Anordnung
erhält die vorhandenen `../src`- und `../include`-Verweise, statt einen zweiten
Protokollkern einzuführen. Archs vorhandene DKMS-Hooks bauen und installieren
das Modul; sie starten unseren Dienst nicht. Fehlende Header oder ein
fehlgeschlagener DKMS-Bau müssen vor der Aktivierung behoben werden, nach
Prüfung und Freigabe. Es gibt keine automatische Reparatur.

Die Installation ist auf Garuda nicht auf Dateien unter `/usr` beschränkt:
die vorhandenen systemweiten Hooks bauen DKMS und erneuern Kernelabbild,
normale und Fallback-Initramfs unter `/boot`. Sysusers legt die Haptikgruppe
an, systemd liest Units ein, Snapper erstellt nach lokaler Konfiguration
Vorher-/Nachher-Snapshots. Kein Modul wird dadurch gemäß geprüfter Konfiguration
geladen, kein Dienst gestartet und kein Controller übernommen. Der vorhandene
DKMS-Hook kann trotz Buildfehlern erfolgreich zurückkehren: die Bauprotokolle
und der tatsächlich installierte Modulstand müssen separat geprüft werden.
[Vollständige Host-Hook-Folgen und Grenzen](ALPHA_INSTALL_AUDIT.md).

Der Dienst wird zunächst **nicht aktiviert**. Erst die getrennte Freigabe
der automatischen Geräteübernahme erlaubt anschließend:

```sh
sudo systemctl enable --now gamesir-native.service
```

Ab dann lädt systemd `industrialio` und `gs_native` mit
`bootstrap_mode=1 enable_output=1 persistent_mode=1`. Normales Spielen benötigt
keinen manuellen Deadband-Start, Terminal oder wiederholte Passwortabfragen.
Vorhandene, anders parametrierte Module werden nicht ungefragt ersetzt;
der Manager muss solche Abweichungen zurückweisen. Es gibt keinen unbegrenzt
wiederholenden Service-Neustart bei Fehlern.

Installierte Pfade:

| Pfad | Zweck |
|---|---|
| `/usr/bin/gamesir-native` | Status und ausdrücklich veranlasste Freigabe/Wiederaufnahme |
| `/usr/lib/gamesir-native/gsnative-ctl` | Vorhandener C-Kontrollclient |
| `/usr/lib/gamesir-native/gamesir_native.py` | Root-Sitzungsmanager |
| `/usr/lib/gamesir-native/haptics_broker.py` | Integrierte Viermotor-API des Dienstes |
| `/usr/lib/gamesir-native/gamesir_haptics.py` | Python-Bibliothek für ausdrücklich integrierte Spiele/Adapter |
| `/usr/lib/gamesir-native/gamesir_mapping.py` | Gerätefreier SDL-Mappinggenerator für native 109c-GUIDs |
| `/usr/lib/systemd/system/gamesir-native.service` | Dienst, zunächst deaktiviert |
| `/usr/lib/sysusers.d/gamesir-native.conf` | Definition ausschließlich der Gruppe `gamesir-native-haptics` |
| `/usr/share/doc/gamesir-native/docs/` | Installations-, Laufzeit-, API- und Protokolldokumentation samt historischen Berichten |
| `/usr/lib/gamesir-native/prepare_remove.py` | Sicherer Paketentfernungs-Check |
| `/usr/share/libalpm/hooks/60-gamesir-native-*.hook` | Entfernung/Upgrade nur nach erfolgreicher Freigabe |
| `/run/gamesir-native/` | Private laufende Kontrollschnittstelle |
| `/var/lib/gamesir-native/` | Persistente, private Pause für Deadband |

## Viermotor-API und SDL-Zusatztasten

Die spätere Paketinstallation lässt über Archs vorhandenen sysusers-Hook eine
dedizierte Gruppe `gamesir-native-haptics` anlegen. Sie fügt **keinen Benutzer**
automatisch hinzu. Der vom Dienst erzeugte Spielesocket liegt unter
`/run/gamesir-native-haptics/control.sock`, mit Eigentümer root und dieser
Gruppe, Verzeichnisrechten 0750 und Socketrechten 0660. Der administrative
Dienstsocket bleibt ausschließlich root zugänglich.

Ein Gruppenbeitritt verändert Benutzerrechte und benötigt ausdrücklich eine
eigene Freigabe. Der erst dann vorgesehene Befehl lautet:

```sh
sudo usermod -aG gamesir-native-haptics [tester]
```

Danach ist eine neue Anmeldung nötig. Der Benutzer- und Gruppenbestand wurde
hier nicht verändert. Die Gruppe autorisiert lokale Programme des
Mitglieds zur begrenzten Viermotor-API; sie gibt keinen USB- oder allgemeinen
Rootzugriff. Die eingebaute Sitzungskontrolle, Besitzerprüfung und Zeitgrenzen
gelten weiterhin. Ohne eingerichtete Gruppe bleibt die Haptik-API deaktiviert;
der normale Gamepadbetrieb ist davon getrennt.

Die Python-Spielbibliothek kann ein integrierter Adapter über seinen eigenen
Importpfad `/usr/lib/gamesir-native` laden, etwa mit einem ausschließlich für
diesen Prozess gesetzten `PYTHONPATH`. Das Paket behauptet keine automatische
Integration in unveränderte Spiele. Insbesondere ersetzt der Broker nicht
SDLs derzeit fehlenden Linux-evdev-Pfad für `SDL_RumbleGamepadTriggers`.

Für die vier zusätzlichen Tasten enthält das Paket einen SDL-Mappinggenerator.
Er öffnet keine Geräte und verändert keine Benutzereinstellungen. Der
[separate SDL-Nachweis](SDL_EXTRA_BUTTONS.md) beschreibt die geprüfte Zuordnung
704–707 auf vier zusätzliche Paddles, ohne eine normale Gamepadtaste zu opfern,
sowie die noch offene konkrete Embercade-/Steam-/Wine-Integration.

## Deadband und Rückkehr

Vor einer Deadband-Sitzung muss die native Sitzung freigegeben werden:

```sh
sudo gamesir-native release
```

Der Manager muss den Rückweg zu 100a/xpad beziehungsweise das physische
Entfernen des von ihm verwalteten Geräts bestätigen. Erst dann Deadband
starten. Keine parallelen Besitzer desselben Interfaces. Nach regulärem
Deadband-Ende kann die Automatik ausdrücklich wiederaufgenommen werden:

```sh
sudo gamesir-native resume
```

Diese administrative Freigabe ist von normalen Spieleingaben getrennt.
Sie ist zunächst keine in Deadband integrierte Einstellungs-API.

## Sichere Deinstallation und Updates

Die folgenden Schritte sind einzeln zu prüfen und gesondert freizugeben.
Zuerst künftigen Autostart verhindern, dann bei laufendem Manager die native
Verwaltung freigeben. `disable` allein beendet den laufenden Dienst nicht:

```sh
sudo systemctl disable gamesir-native.service
sudo gamesir-native release
```

Nur bei `returned: true` und frisch bestätigter 100a/xpad-Bindung aller noch
angeschlossenen verwalteten Controller beziehungsweise bestätigter physischer
Abwesenheit fortfahren. Abwesenheit ist kein Beleg normaler Spielfunktion.
Bei einem lediglich installierten, nie gestarteten Paket ist kein `release`
ohne Dienstsocket nötig; der Entfernungsschutz prüft den leeren Besitzstand.

```sh
sudo systemctl stop gamesir-native.service
sudo pacman -R gamesir-native-dkms
```

Vor Paketentfernung **und Upgrade** läuft jeweils ein ALPM-`PreTransaction`-Hook mit
`AbortOnFail`, vor dem DKMS-Entfernungshook. Er verlangt eine erfolgreiche
synchrone Manager-Freigabe, prüft, dass kein Interface mehr `gs_native`
verwendet, stoppt den Dienst und prüft erneut. Nur bei Referenzzähler null
wird exakt `gs_native` regulär entladen. `industrialio`, `xpad` und `usbhid`
werden nicht entladen. Bei Entfernung deaktiviert der Hook anschließend den
Autostart; bei Upgrade bleibt dessen Konfiguration erhalten. Es gibt kein erzwungenes Entladen und keinen
Fallback-Moduswechsel auf Verdacht.

Zusätzlich müssen persistente Besitz-/Recovery-Einträge aufgelöst und der
tatsächliche Dienstabschluss bestätigt sein. Ein erfolgreicher `systemctl stop`
Aufruf allein genügt nicht: verbleibende Prozesse und ein neuer Exitfehler
blockieren die Entfernung. Ein alter unveränderter Dienstfehler ohne offene
Besitzdaten und Bindungen verhindert die Entfernung nicht dauerhaft.

Bei fehlgeschlagener Freigabe oder noch laufenden Referenzen bricht die
Pakettransaktion ab; Modul- und Paketdateien bleiben verfügbar. Dann den
konkreten Zustand prüfen, nicht den Hook umgehen. Bereits erfolgreich
ausgeführte Schritte wie die native Pause werden dabei nicht automatisch
rückgängig gemacht. Nach einem Upgrade bleibt der Dienst gestoppt und die
Pause erhalten, bis neuer Build und Rückweg geprüft und die Aktivierung
freigegeben sind.

DKMS und pacman entfernen die installierten Modul-/Programm-/Unit-Dateien.
Die private Pausenmarkierung unter `/var/lib/gamesir-native` und Journalbelege
bleiben absichtlich erhalten, ebenso die lokale Haptikgruppe und bewusst
eingerichtete Mitgliedschaften. Ohne Dienstsocket gewähren diese keinen
Motorzugriff. Ihre Löschung wäre eine gesonderte bewusste
Bereinigung, kein notwendiger Schritt für den normalen xpad-Betrieb.

Lesende Nachkontrollen nach der später freigegebenen Entfernung:

```sh
dkms status
pacman -Q gamesir-native-dkms
test ! -d /sys/module/gs_native
systemctl is-enabled gamesir-native.service
```

Paket und Unit sollen dann nicht mehr gefunden werden, DKMS darf keinen
GameSir-Eintrag führen. Nur falls nach geprüftem Modul-/Bindungsende ein
verwaister DKMS-Eintrag verbleibt, lautet der separat freizugebende gezielte
Bereinigungsbefehl für den aktuellen Stand
`sudo dkms remove -m gamesir-native -v 0.1.0.alpha3 --all`.
Kein `--force`, keine pauschale Entfernung anderer Module.

## Manueller Rückweg bei verbleibendem 109c

Dieser Ablauf wurde als Zustands-/Fehlerpfad offline geprüft. Seine Wirkung
nach einem real gescheiterten Bootstrap ist noch kein Hardwarebeleg. Ein
Rückweg ohne Neustart ist deshalb nicht für jede Firmware-/Fehlerlage zugesichert.

1. `sudo systemctl disable gamesir-native.service` verhindert künftigen Autostart.
   `sudo gamesir-native release` sperrt neue Übernahmen und lässt den Manager
   genau den belegten eigenen Rückweg versuchen. Fehler und Tokens sichern.
2. Bleibt `returned: false` bei 109c: keine Bindung an xpad als angeblichen
   Moduswechsel, kein weiterer Bootstrap/END auf Verdacht. Die eigene Bindung
   bleibt als offener Recovery-Besitz sichtbar; Paketentfernung ist gesperrt.
3. Nach eigener Freigabe ausschließlich den betroffenen USB-Dongle physisch
   abziehen. Auf bestätigte Abwesenheit und Auflösung des Besitzstands warten.
   Ein erneuter `release` fragt denselben pausierten Rückweg ab; bereits
   ausgeführtes END wird nicht wiederholt. Danach den Dienst regulär stoppen.
4. Nach eigener Freigabe Dongle wieder einstecken und Controller verbinden.
   Anschluss, VID/PID und Bindungen frisch **aus sysfs** lesen. Nur tatsächlich
   beobachtetes `3537:100a` mit IF0/xpad bestätigt den normalen Rückkehrmodus.
   Anschließend normale Eingaben separat prüfen. Einstecken garantiert keine PID.
5. Bleibt 109c, ein fremder Treiber oder ein unerwarteter Gerätezustand bestehen,
   anhalten und konkret berichten. Kein geratenes Rückschaltpaket oder Reset.

Für eine bereits bestätigte eigene 100a-Instanz mit verbleibender nativer
Bindung kann nach gestoppter Automatik eine gesondert freigegebene gezielte
Ab-/Rückbindung erfolgen. **Nur für den unmittelbar zuvor geprüften Anschluss**,
hier beispielhaft der historische Testport; nicht portfest in Produktionscode:

```sh
printf '%s' '8-6:1.0' | sudo tee /sys/bus/usb/drivers/gs_native/unbind >/dev/null
printf '%s' '8-6:1.0' | sudo tee /sys/bus/usb/drivers/xpad/bind >/dev/null
```

Diese Befehle sind für 109c nicht der Rückweg. Systemd-/Paket-/DKMS-Befehle
dieser Anleitung wurden im Offline-Auftrag nicht ausgeführt.

## Grenzen der Offline-Prüfung

Paketinhalt, deterministisches Archiv, Kbuild-Anordnung und simulierte
Entfernungsfehler sind offline prüfbar. Tatsächliche DKMS-Installation,
Service-Start beim Booten, suspend/resume auf den Zielsystemen sowie
Deinstallation bei echter Funk-/USB-Trennung benötigen später freigegebene
Integrationstests. Ein erfolgreicher Build allein beweist diese Abläufe nicht.

## CachyOS-Zielbuild: Korrektur der Compiler-Auswahl

Am 14. Oktober nach dem Systemupdate: `7.2.9-2-cachyos-deckify`, passende
Header und GCC 16.2.1 als Kernel-Compiler. [tester] installierte DKMS 3.4.4-2
und lld 23.1.1-1.1; Pakettransaktion und Integrität sind lesend bestätigt.

Der anschließend freigegebene native Erstversuch installierte das Paket
`0.1.0.alpha3-1`, scheiterte aber im DKMS-Bau. Das alte Rezept erzwang `LLVM=1`;
Clang lehnte GCC-Optionen wie `-mpreferred-stack-boundary=3`,
`-mindirect-branch=thunk-extern` und `-fconserve-stack` ab. Dies war ein
Buildrezeptfehler, kein nachgewiesener Fehler im USB- oder Laufzeitcode.
Pacman meldete trotz des fehlgeschlagenen DKMS-Hooks Exit 0. Deshalb werden
DKMS-Status und tatsächliche Modulmetadaten zusätzlich geprüft.

Bestätigter Zustand danach: Paket installiert, DKMS nur `added`, kein Modul
installiert/geladen; Dienst `inactive/dead/disabled`. G7 Pro unverändert
`100a/xpad`, zweites Interface `usbhid`; keine native Übernahme. Snapshot 77/78,
Initramfs-Hook beendet; die geprüften Kernel-/Initramfs-/EFI-Dateihashes blieben
unverändert, Limine-Konfiguration und Snapshot-Verzeichnisliste änderten sich.
Kein Bootnachweis. Privater vollständiger Fehlbeleg:
`.local/integration/20261014T175629Z-CachyOS test host-alpha3-install/`.

Revision `0.1.0.alpha3-2` korrigiert ausschließlich den Bau-/Paketpfad:
`scripts/kernel_toolchain.py` liest die vorbereitete `include/config/auto.conf`
als Daten und wählt eindeutig GCC/GNU oder Clang/LLVM. Dieselbe Auswahl wird
für DKMS und `make kernel` verwendet. Compiler-/Make-Umgebungsüberschreibungen
werden entfernt, Werkzeuge und Header geprüft; `W=1` und `-Werror` bleiben.
GCC erhält ausdrücklich leere LLVM-Variablen, niemals `LLVM=0` (für Kbuild
wäre auch das ein aktivierender Wert). DKMS' automatisch angehängter
`LLVM=1`-Hinweis ist kein Vorrang vor der Zielkonfiguration. Unbekannte
Zusatzargumente, fehlende Werkzeuge oder widersprüchliche Konfigurationen
stoppen; kein automatischer Versuch mit einem anderen Compiler.
Die geprüften Kombinationen sind GCC/GNU und Clang/LLVM auf diesen beiden
Hosts; gemischte Compiler-/Linker-Konfigurationen sind nicht abgenommen.
Kernelquellen, Manager, Protokoll und Modulversion `0.1.0.alpha3` bleiben gleich.
GCC und binutils sind zusätzlich explizite Laufzeitabhängigkeiten für spätere
DKMS-Neubauten. Clang-Analyse bleibt auf Clang-Kernelbauten beschränkt.

Vor dem einmalig freigegebenen neuen Installationsversuch: Offline-Tests,
Garuda-Modulbau, Paketprüfung und unprivilegierter Bau mit den tatsächlichen
CachyOS-Headern. Danach frischer Zielcheck, genau eine native Paketaktualisierung
und Kontrolle des tatsächlichen DKMS-Ergebnisses. Der Upgrade-Hook stoppt den
bereits inaktiven Dienst, aktiviert ihn aber nicht. Leere systemd-Markierungen
müssen den globalen `enqueue-marked`-Hook ohne fremde Neustarts erlauben.
DKMS ersetzt seine alte fehlgeschlagene Registrierung; der Fehlbeleg bleibt
vorher separat erhalten. Dienstaktivierung und Controllerübernahme bleiben
separat freizugeben; Steam-/Gamescope-Pakete sind nicht Teil dieses Updates.

### Erfolgreicher korrigierter Versuch auf CachyOS

Der einmalig freigegebene neue Versuch am 14. Oktober um 20:09 MESZ ist
bestanden: genau `gamesir-native-dkms 0.1.0.alpha3-1 → 0.1.0.alpha3-2`.
Paket-SHA256 `75bf8e0de72e582e1db11ff215abc28f5c2f40c9fe817b37e045d5ed50653c30`.
Korrekturcommit `e614784`; vollständige Offline-Suite, 13 Toolchain-Regressionen,
Garuda-Clang-Bau/statische Analyse und unprivilegierter CachyOS-GCC-Zielbau
bestanden. Tatsächlicher DKMS-Bau Exit 0 ohne Compilerwarnungen/-fehler;
`installed` für `7.2.9-2-cachyos-deckify`. Modul `0.1.0.alpha3`,
srcversion `67138C65BCA95D0ABEAB517`, passende vermagic und keine Autoload-Aliase.
85 Paketeinträge/0 verändert, 65 Nutzdateien byte-/rechtegenau geprüft.
Kernel-, Manager-, Client- und Dienstdateien bleiben gegenüber Revision 1
unverändert. Zusätzlich zur Baukorrektur übernimmt das Paket die bereits in
`46adb0c` vorbereitete 105e-Erweiterung des gerätefreien SDL-Mappinggenerators;
das installiert oder aktiviert keine Steam-Sitzungsintegration.

Installation endete mit Dienst `inactive/dead/disabled`, Modul nicht geladen,
Dongle `100a/Adresse 10` am Hub `1-3.2` weiter `xpad/usbhid`. Steam-Sitzung
unverändert; keine neuen Kernelmeldungen. Snapper 79/80 und Initramfs-Hook
beendet, Kernel-/Initramfs-/EFI-Hashes unverändert; Limine-Konfiguration und
Snapshot-Liste geändert. Bekannter DKMS-CLEAN-Hinweis bleibt; kein Buildfehler.
Kein Reboot-/Hardwarebeleg allein aus dieser Installation.
Private vollständige Belege und geprüfte SHA256-Liste:
`.local/integration/20261014T180717Z-CachyOS test host-alpha3-retry/`.
[tester] hat anschließend die Aktivierung und einen ersten Funktionstest
freigegeben; deren Ergebnis wird getrennt dokumentiert.

### CachyOS-Erstaktivierung: Bootstrap blockiert, manueller Rückweg bestätigt

Die danach ausdrücklich freigegebene Aktivierung und ein separat freigegebener
neuer Versuch am 14. Oktober sind **nicht bestanden**. Installation und
DKMS-Bau sind erfolgreich; das beweist noch keinen nativen Dauerbetrieb.

| Schritt (MESZ) | Tatsächlicher Befund |
| --- | --- |
| 20:15:56, einmal `enable --now` | Dienst aktiv/enabled; 100a an gs_native, `waiting_input`, Gerätename GameSir G7 Pro und elf normale Tastencodes registriert |
| 20:16:09 | `native bootstrap finished: -19; no automatic retry`; alte 100a-Instanz verschwindet |
| 20:16:11 | Neue 109c-Instanz an xpad; keine native Übernahme |
| Nach Freigabe | Autostart deaktiviert und Verwaltung pausiert; keine native Bindung, leere Leases. Manueller Neusteckschritt frisch als 100a/xpad/usbhid bestätigt |
| 20:23:07, einmal `resume` | Neuer Versuch mit derselben geladenen Modulversion; kein Dienstneustart oder Modulladen |
| 20:23:12–13 | Wieder Bootstrap `-19`, neue 109c-Instanz an xpad |
| 20:23:57 | Freigegebener einmaliger Fehler-Release endet mit Exit 1, `paused=true`, `returned=false`, `blocked`: `Unowned new 109c instance; no END attempted` |
| Manueller Rückweg | Dongle entfernt, Abwesenheit/Leases leer/`returned=true` geprüft; wieder eingesteckt, abschließend 100a/xpad/usbhid und normale Steam-Eingaben bestätigt |

Der erste Beobachter stoppte wegen AMDGPU-`CRB Config Warning`-Meldungen.
Identische Meldungen lagen bereits um 20:15:25/26 vor dem Dienststart vor.
Nur die lesende Beobachtung wurde anschließend fortgesetzt, kein zweiter Start.
Die GPU-Meldung belegt weder einen GameSir-Fehler noch dessen Ursache; im
aufgezeichneten Fenster ist kein Oops nachgewiesen. Die bekannte xpad-
`usb_submit_urb ... -2`-Meldung trat beim gezielten Abbau auf. Der tatsächliche
Startblocker ist der zweimal protokollierte Bootstrapfehler `-19` (`ENODEV`).

Der genaue Auslöser bleibt offen: USB-Completion, Identitätsprüfung oder
Entfernung während der Übergangsfolge sind anhand des Codes mögliche Pfade.
`failed_stage` und die letzte Übertragung fehlen im gespeicherten Journal.
Hub-/Timing-Unterschiede sind bislang Hypothesen. Nach dem Fehler verwirft der
Kernel seine Übergabeberechtigung; die spätere unbesessene 109c-Instanz wird
zu Recht nicht nachträglich gebunden. Kein geratenes END-/Resetpaket senden.

Zusätzlicher Offline-Befund mit vorhandener Manager-Fixture: Nach fehlgeschlagenem
Bootstrap, kurzer Geräteabwesenheit und neuer 109c kann der allgemeine
Instanzwechselpfad den alten Eintrag entfernen. Das reproduziert den später
leeren Status des ersten Laufs, belegt aber nicht dessen einzelne Tick-Reihenfolge.
Fehler bleiben im Journal. **Leerer Status und `returned=true` für einen leeren
Verwaltungsumfang beweisen keine Rückkehr zu 100a.** Beim unmittelbaren
Fehler-Release im zweiten Lauf blieb der Konflikt dagegen korrekt blockiert.

Beim letzten Wiedereinstecken erschien zunächst 109c, erst danach 100a. Der
lesende Rückweghelfer stoppte am Zwischenzustand; die anschließende frische
Prüfung bestätigte 100a/Adresse 16 am Hub-Port 1-3.2, IF0/xpad und IF1/usbhid.
[tester] bestätigt normale Tasten-, Stick- und Triggereingaben in Steam.
Abschluss: Dienst weiter `active/running`, jedoch **paused und disabled**;
Modul geladen, ungebunden, Referenzzähler 0; keine offenen Leases bei der
bestätigten physischen Abwesenheit. Keine weitere Aktivierung, kein Entladen,
kein Motorentest oder Firmwareeingriff.

Private Originalbelege, Nutzerbestätigung und geprüfte SHA256-Listen:
`.local/integration/20261014T181529Z-CachyOS test host-activation/` und
`.local/integration/20261014T182239Z-CachyOS test host-activation-retry/`.

**Entscheidung:** Installations-/DKMS-Prüfung bestanden, nativer Dauerbetrieb
auf diesem CachyOS-Aufbau **No-Go**. Vor einem weiteren Hardwarelauf den
Bootstrapabbruch gezielt offline untersuchen und die vorhandene Fehlerdiagnose
um fehlenden Übertragungs-/Stufenbeleg ergänzen. Keine Wiederholungsschleife
oder Lockerung der Gerätezuordnung. Steam-/Gamescope-Komponenten sind weiterhin
nicht installiert; keine native IMU-, Viermotor-, Paddle-, Boot- oder
Suspendabnahme auf diesem Ziel. Der an erfolgreiche reale Prüfung gebundene
Git-Push erfolgt nicht.

## Garuda test host nach Kernelupdate am 15. Oktober 2026

Lesende Diagnose auf `garuda-test-host` um 14:24 MESZ:
`7.2.10-1-garuda`, passende `linux-garuda`-/Headerpakete `7.2.10-1` und
installiertes natives Paket `0.1.0.alpha3-1`.

**Der Treiber wurde erfolgreich neu gebaut und ist bereits geladen.**
Das Updateprotokoll nennt DKMS-Bau am 15. Oktober um 14:00:35; tatsächliches
`make.log` endet mit Exit 0 ohne Compilerwarnungen/-fehler. DKMS meldet
`installed` für den laufenden Kernel. Vermagic passt, Modulversion
`0.1.0.alpha3`, srcversion `67138C65BCA95D0ABEAB517`. Kernel, Header und
nativer Paketbestand bestehen die Integritätsprüfung. Der aktivierte Dienst
startete beim Boot um 14:20:55, lud das Modul und läuft ohne Neustarts.
Die Signaturvertrauensmeldung verhindert das nachgewiesene Laden nicht;
der bekannte DKMS-CLEAN-Hinweis ist ebenfalls kein Baufehler.

**Ursache der ausbleibenden Geräteübernahme: persistente Verwaltungspause.**
Gespeicherte Zustandsdatei und aktuelle Statusabfrage bestätigen
`paused=true`, leere Leases, keine Port-/Scanfehler und keine native Bindung.
Der Dongle steht auf `3537:100a`, Adresse 4, IF0/xpad und IF1/usbhid am
Port 8-6. Dies ist eine Zustandsprüfung, kein neuer Eingabefunktionstest.

Die globale Pause ist bereits im Garuda test host-Abschlussbeleg des Alpha3-/ZZZ-Tests
vom 14. Oktober dokumentiert. `Manager.__init__` übernimmt sie aus der
Zustandsdatei; beim Bootwechsel entfernt `Manager.tick` veraltete Besitzstände,
erhält die ausdrückliche Pause aber absichtlich. Daher ist der jetzige Zustand
kein nachgewiesener Kernelupdatefehler und vom separaten CachyOS-Bootstrapblocker
zu unterscheiden. Das Garuda test host verwendet weiterhin Revision 1; Revision 2 wurde
zuvor ausschließlich auf dem CachyOS test host installiert.

Ein später ausdrücklich freigegebenes `gamesir-native resume` kann die
Verwaltung wiederaufnehmen. Dafür vorher Geräteidentität, Besitzer und
Anwendungen frisch prüfen. Ein Dienstneustart oder erneutes Modulladen hebt
die Pause nicht auf und ist für diesen Befund nicht angezeigt. Diese Diagnose
führte kein Resume, keinen Bootstrap und keine Dienst-/Modul-/Bindungsänderung
aus. Keine neue Hardwarefreigabe daraus ableiten.

Private Messbelege und geprüfte SHA256-Liste:
`.local/diagnostics/20261015T122414Z-Garuda test host-kernel-update/`.

## Revision 3: neuer Zielbau und Garuda test host-Update am 15. Oktober

Nach der Offline-Korrektur ist der frische GCC-Bau gegen die tatsächlichen
CachyOS-Header bestanden. Dort noch keine Installation oder neue Übernahme;
nach dem zwischenzeitlichen Boot Dienst inactive/disabled und Modul ungeladen,
100a/xpad/usbhid. Das separat freigegebene Garuda test host-Paketupdate auf
`0.1.0.alpha3-3` ist inklusive realem DKMS-Bau bestanden. Installationsabschluss
auf dem Garuda test host pausiert/inaktiv/Modul ungeladen, enabled erhalten; keine
erneute Aktivierung durch Codex. Der übrige Paketbestand blieb unverändert.
Neue gemeinsame srcversion: `C6818C24711721D136684D5`.

[Vollständige frische Befunde, Beleggrenzen und nächste getrennte
Freigaben](BOOTSTRAP_CACHYOS_FIX.md#folgeschritt-am-15-oktober-zielbau-und-getrennte-installation).
Ältere Angaben oben beschreiben ihre damaligen Messzeitpunkte.

### CachyOS test host-Update auf Revision 3 abgeschlossen

Nach eigener Freigabe inklusive Passwortabfrage und benannter Hooks wurde am
15. Oktober auch der CachyOS test host genau von Revision 2 auf 3 aktualisiert.
Tatsächlicher GCC-/DKMS-Bau, Modulkennungen und Paketdateien geprüft; Dienst
bleibt inaktiv/deaktiviert, Modul ungeladen, Pause gesetzt und Leases leer.
100a/Adresse 11 und xpad/usbhid sowie die laufende Steam-Sitzung sind gegenüber
dem tatsächlichen Updatebeginn unverändert. Kein Bootstrap/Hardwaretest.
[Vollständiges Ergebnis mit Vorprüfabweichung, Hookeffekten und Beleggrenzen](BOOTSTRAP_CACHYOS_FIX.md#CachyOS test host-freigegebenes-paketupdate-bestanden).

### CachyOS test host-Dienst separat pausiert gestartet

Nach eigener Einmalfreigabe inklusive Passwortabfrage ist der Dienst gestartet:
active/running bei weiterhin disabled. Neues Modul geladen, Referenzen 0,
kein Gerät an gs_native gebunden. Pause aktiv, Leases leer, fünf unauffällige
Statusproben und dieselbe 100a/Adresse 11 an xpad/usbhid. Kein Resume oder
Bootstrap. Der Kernel meldete externes Modul sowie fehlende Signatur oder
Schlüsselvertrauen; dies blockierte das tatsächliche Laden nicht. Keine
Signatur-/Systemkonfiguration verändert.
[Ergebnis und Beleggrenzen](BOOTSTRAP_CACHYOS_FIX.md#CachyOS test host-dienst-pausiert-gestartet).

### CachyOS test host-Resume danach fehlgeschlagen; weitere Versuche gestoppt

Der separat freigegebene einmalige Resume am 15. Oktober um 16:06 MESZ
bestätigte neun vollständige Übergangs-OUTs, endete aber in WAIT_REMOVE mit
ENODEV vor der protokollierten USB-Abmeldung. Neue 109c/Adresse 12 an xpad,
keine native Übernahme oder Eingabe-/IMU-Testphase. Genau ein zusätzlich
genehmigter Fehler-Release pausierte die Übernahme, bestätigte jedoch keinen
Rückweg: Exit1, blocked, returned=false, alte Lease erhalten, keine native
Bindung/Modulreferenzen. Dienst bleibt active/running/disabled; kein Enable.
Nach [tester]' STOP-Auftrag ausschließlich Offline-Untersuchung, keine weiteren
System-/Hardwareänderungen. Passende Fehlerüberschreibung reproduziert,
reale erste Transportursache weiter offen. Kein neuer Produktfix installiert.
[Zeitfolge, Ursachenabgrenzung und Belege](BOOTSTRAP_CACHYOS_FIX.md#revision-3-realtest-übergabe-vor-neuanmeldung-abgebrochen).
