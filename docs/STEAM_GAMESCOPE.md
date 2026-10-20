> Public export: personal tester, host and path references were anonymized. Historical evidence hashes refer to the private originals.

# Optionale Steam-Einbindung für CachyOS Gamescope

## Revision 14: Spiel-Gyro bestätigt, Nullanzeige als TODO

Am 20. Oktober 2026 meldet der Nutzer mit Revision 14 im laufenden Gaming-Mode-
Test: normale Eingaben und vier unabhängige Paddles funktionieren. Steams drei
Gyro-Anzeigewerte bleiben bei Bewegung null. Eden erkennt den Gyro über SDL.
Anschließend steuert die Controllerbewegung in Arc Raiders tatsächlich die
Kamera, beim angekündigten Test von Steam Input „Gyro als rechter Stick“.
Damit ist die Anwendungsnutzung in dieser Sitzung positiv; die Nullanzeige
belegt keinen allgemeinen Ausfall von Sensor oder Steam Input.

**Zurückgestelltes TODO:** Diskrepanz zwischen Steams Gyroanzeige und nutzbarer
Bewegungssteuerung untersuchen. Für den bestätigten Spielpfad kein Blocker.
Die genaue interne Ursache ist nicht nachgewiesen. Guide-Unabhängigkeit,
Ruhedrift und weitere Start-/Reconnect-Fälle wurden bei diesem Spieltest nicht
separat bestätigt. Kein universelles Spieleversprechen und keine zusätzliche
Steam-/Treiberänderung. [Prüfstand und Grenzen](RELEASE_AUDIT.md#revision-14-activation-readback--20-october-2026).

## Revision 11: positiver Steam-Gyro-Funk-Reconnect

Am 19. Oktober 2026 bestätigt der Nutzer nach eigenem Dienststart/Resume mit
Revision 11 einen erfolgreichen Funkcontroller-Aus-/Einschaltzyklus: Dongle
blieb eingesteckt, Steams Gyro-Anzeige im Gaming Mode arbeitet ohne gehaltene
Guide-Taste und ohne Steam-Neustart. Lesende Kontrollen bestätigen das neue
Modul, erfolgreichen Bootstrap und gepaarte Eingabe-/Sensorknoten.
[Genauer Nachweis und Grenzen](STEAM_GYRO_HOTPLUG.md#revision-11-user-led-radio-reconnect--19-october-2026).
Ein positiver Fall belegt noch keine allgemeine Hotplug-Zuverlässigkeit oder
Ursache der Verbesserung. Der beobachtete Start nutzte den optionalen xpad-
Übergabepfad; ein unabhängiger Kaltstart ist damit nicht geprüft.

## Eden: manueller SDL-Kompatibilitätshinweis

Am 19. Oktober 2026 ist ein Eden-Anwendungstest im Gaming Mode bestanden:
echter GameSir auswählbar, Gyro ohne gehaltene Guide-Taste aktivierbar,
vier unabhängige Paddles und normale Eingaben ohne beobachtete Dopplung.
Zuvor schloss die geerbte Variable `SDL_GAMECONTROLLER_IGNORE_DEVICES`
`3537:109c` aus. Eden öffnete nur Steams virtuellen Xbox-Controller ohne
Bewegungssensoren. Nach Entfernen der beiden Filter ausschließlich beim
Eden-Start öffnet es auch das physische Gamepad und dessen Sensorknoten;
das Protokoll bestätigt `accel=true gyro=true`.

Die [genaue manuelle Anleitung mit Sicherung und Rückbau](SDL_EDEN_GYRO.md#manual-steps-for-the-tested-launcher-shape)
gilt für die geprüfte AppImage-Verknüpfung mit `env` als Ziel. Andere
Startformen nicht ungeprüft übernehmen. Die Filterentfernung kann innerhalb
Edens weitere Controller sichtbar machen; physischen GameSir auswählen und
Doppelbelegung vermeiden. Es gibt keinen automatischen Starter, keine
Installer-/Control-Center-Funktion und keine Eden-Sonderlogik im Treiber.
Steam Input und globale SDL-Einstellungen werden nicht verändert.
Der offene Guide-/Wiederverbindungsfehler in Steams eigener Gyroanzeige ist
ein getrennter Fall und durch diesen Anwendungstest nicht behoben.

## Historischer Paket- und Boot-Teststand

Stand: 15. Oktober 2026. **Ein kontrollierter PC-Neustart mit anschließendem
Funkcontroller-Einschalten ist bestanden:** automatischer Dienststart,
eigenständiger nativer Bootstrap und dauerhaftes Steam-/Gamescope-Mapping.
[tester] bestätigt alle vier Paddles unabhängig und normale Eingaben ohne
manuellen Start/Resume/Deadband. Codex hat ausschließlich unprivilegiert
gelesen; keine zusätzliche Start-/USB-Aktion oder Wiederholung.
[Kontrollierter Neustart und Grenzen](#kontrollierter-neustart-am-15-oktober-bestanden).

Die folgenden früheren Phasen gelten für die jeweils genannten Zeitpunkte.
Weitere Bootkonstellationen, Suspend, Hotplug, Mehrfachzyklen und ein konkreter
Spieltest sind durch diesen einen Ablauf nicht allgemein abgenommen.

## Aufgabe und Paketgrenze

`gamesir-native-steam-gamescope 0.1.0.alpha1-1` ergänzt den tatsächlichen
CachyOS-Startweg. Es benötigt `gamesir-native-steam>=0.1.0.alpha2` und
`gamescope-session-cachyos`. Vorbereitet sind gemeinsam:

- `gamesir-native-steam-0.1.0.alpha2-1-any.pkg.tar.zst`
- `gamesir-native-steam-gamescope-0.1.0.alpha1-1-any.pkg.tar.zst`

Der Mappinghelfer des Basispakets bleibt die einzige Quelle der Zuordnung;
keine zweite Mappingkopie oder Änderung des Kerneltreibers. Die Plasma-
Einbindung des Basispakets gilt für den Desktopmodus; die Gamescope-Ergänzung
deckt dessen getrennte Steam-Sitzung ab.

| Eigene Datei | Zweck |
| --- | --- |
| `/usr/lib/gamesir-native-steam/gamescope-launcher` | Mappinghelfer einlesen, danach den vorhandenen Herstellerstarter mit `exec` ausführen |
| `/usr/lib/systemd/user/steam-launcher.service.d/50-gamesir-native.conf` | ausschließlich `ExecStart` auf den eigenen Wrapper umleiten |
| `/usr/share/doc/gamesir-native-steam-gamescope/STEAM_GAMESCOPE.md` | diese Anleitung |
| `/usr/share/licenses/gamesir-native-steam-gamescope/COPYING` | Lizenz |

Es gibt kein eigenes Installationsscriptlet, keinen eigenen Hook und keinen
automatischen Steam-Neustart. Paketmanager-Hooks des Zielsystems bleiben davon
unabhängig. Eine bereits laufende Steam-Instanz erhält keine neue Umgebung.

## Geprüfter Startvertrag

Der lesende Zielcheck vom 14. Oktober, 17:23:35 UTC, fand
`gamescope-session-cachyos 1.1.6-1` ohne zusätzliche Steam-Unit-Drop-ins.
Die erneute unprivilegierte SSH-Prüfung am 15. Oktober bestätigt dieselben
Dateihashes, `Type=exec`, denselben `ExecStart` ohne Argumente und weiterhin
keine Drop-ins in der zusammengeführten Steam-Unit:

- `/usr/lib/systemd/user/steam-launcher.service`: SHA256
  `db9a4802fc1e4829130e3a69b42b836cfabf81021c0e9dcb1a2787d875f34201`.
- `/usr/lib/steamos/steam-launcher`: SHA256
  `bc2e16bbff2357091f04b7049b9fa40d3fc8d75e909c09310ebe39acc5c09621`.

Frischer SSH-Check vom 15. Oktober, 17:57:39 MESZ: beide optionalen Pakete
fehlen, alle neun eigenen Dateiziele frei, Bash und Gamescope-Abhängigkeit
vorhanden, keine Steam-Unit-Ersetzung oder Drop-ins in den geprüften Vendor-,
System-, Benutzer- und Laufzeitverzeichnissen. Kein SDL-Mapping, Datei-Hinweis
oder Opt-out in Benutzer-systemd, laufendem Steam oder dessen Gamescope-
EnvironmentFile. Rund 129 GB frei, keine Pacman-Sperre. Keine erhöhten Rechte,
kein Gerätezugriff und keine Systemänderung. Private Belege:
`.local/integration/20261015-gamescope-paddles-preflight/`.

Die Unit nutzt `Type=exec` und startet den Herstellerstarter ohne Argumente.
Dieser wählt selbst zwischen dem ausführbaren persönlichen Devkit-Starter und
`steam` und fügt `-steamos3 -steampal -steamdeck -gamepadui` hinzu. Diese Logik
wird nicht kopiert. Der neue Wrapper ersetzt sich durch denselben Starter;
Argumente, PID und Rückgabestatus bleiben erhalten. `EnvironmentFile`,
Start-/Stopp-Tracker, `ExecStop`, Stoppsignal, KillMode, Zeitlimit und
Sitzungsabhängigkeiten bleiben in der ursprünglichen Unit.

Fehlt nur der Mappinghelfer, meldet der Wrapper dies und startet den
Herstellerstarter weiter. Fehlt dessen ausführbare Datei, endet er mit Fehler
127. Vorhandene SDL-Zuordnungen, Konflikte, Datei-Hinweise und die Abschaltung
`GAMESIR_NATIVE_STEAM_DISABLE=1` behandelt der gemeinsame Helfer unverändert.
Die genaue Konfliktpolitik und Grenzen stehen in der Dokumentation des
Basispakets unter `STEAM_INTEGRATION.md`.

Der gespeicherte Vertrag ist keine Garantie für künftige CachyOS-Versionen.
Insbesondere Änderungen des ursprünglichen `ExecStart`-Pfads oder seiner
Argumente könnten durch das Drop-in verdeckt werden. Nach solchen Updates
Vertrag und zusammengeführte Unit erneut prüfen. Das Paket verändert keine
Steam-Binärdateien, Benutzerbelegungen oder Herstellerdateien.

## Vier getrennte Paddle-Quellen

Das vorbereitete Mapping verwendet die native USB-/evdev-GUID
`03004535373500009c10000053010000`, den Namen `GameSir G7 Pro` und `crc:3545`.
Die bestehenden Standardtasten, Achsen und Trigger bleiben vollständig erhalten.

| Physische Taste | Linux-Code | SDL-Rohbutton | Mappingfeld |
| --- | --- | --- | --- |
| L4 | 704 | b11 | paddle2 |
| R4 | 705 | b12 | paddle1 |
| L5 | 706 | b13 | paddle4 |
| R5 | 707 | b14 | paddle3 |

Dies ist die bereits dokumentierte Zuordnung für das Standardmodell. Der neue
freie Eingabetest bestätigt die vier Linux-Codes mit Druck/Loslassen, aber
keine erneute isolierte Prüfung ihrer physischen Beschriftungen. Die SDL-
Buttonreihenfolge und der Mappingpfad sind gerätefrei geprüft; der frühere
Garuda-/Plasma-Test belegt die vier unabhängigen Steam-Paddle-Quellen dort.
Eine tatsächliche Gamescope-Abnahme am CachyOS test host folgt erst nach Installation
und neuem Steam-Start. Details: [gemeinsame Mappingpolitik](STEAM_INTEGRATION.md#zuordnung-vorrang-und-grenzen).

Vorhandene eigene Mappingzeilen behalten Vorrang. Der Helfer ergänzt für eine
PID nichts, wenn bereits ein Mapping derselben nativen Gerätefamilie vorliegt,
auch mit anderer CRC oder Version. Ein nichtleerer
`SDL_GAMECONTROLLERCONFIG_FILE` oder `GAMESIR_NATIVE_STEAM_DISABLE=1` verhindert
die Ergänzung ebenfalls. Solche Konflikte vor Installation melden und nicht
stillschweigend überschreiben.

Vier separate Quellen in Steam Input erweitern nicht die begrenzte XInput-
Ausgabe eines Spiels. Ein Spiel kann deshalb weiterhin nur die üblichen
XInput-Tasten akzeptieren. Die vier Paddleplätze sollen in Steam unabhängig
konfigurierbar sein; das Paket legt keine Spielaktionen oder Profile fest und
verspricht keine universelle direkte Ingame-Belegung.

## Offline bauen und prüfen

Diese Befehle arbeiten ausschließlich im Projektverzeichnis:

```sh
make test-steam
python -B scripts/package_steam.py source --component gamescope --dest build/steam-gamescope-source
cd build/steam-gamescope-source
makepkg --nodeps
```

Das Zielverzeichnis muss zuvor fehlen oder leer sein. Kein `makepkg -i` oder
`-s`: Der Bau installiert weder Ergebnis noch Abhängigkeiten. Die Tests prüfen
die kleine Paket-Allowlist, Rechte, Paketrezepte, Wrapper-Verhalten mit einem
künstlichen Herstellerstarter und den auf `ExecStart` begrenzten Unit-Eingriff.
Sie starten weder Steam noch einen systemd-Dienst und öffnen keine Geräte.
Ein erfolgreicher Offline-Test belegt noch keine echte Gamescope-Sitzung.

Gespeicherte Prüfungen bestanden: 13 Session-/Konfliktfälle, 15 Basispaketfälle
und 12 Gamescope-Paketfälle. Beide Pakete wurden mit `makepkg` gebaut; die
jeweiligen Pakettests liefen dabei auch im entpackten Quellarchiv. Die
Gamescope-Payload enthält vier eigene Dateien, die Basis fünf; Archivinhalt,
Dateirechte und fehlende Installationsscriptlets sind geprüft. Die gespeicherten
Artefaktmanifeste wurden am 15. Oktober ausschließlich lesend nachgeprüft und
stimmen. Builds und Nachweise liegen unter
`build/steam-zzz-alpha2-release/`, `build/steam-gamescope-alpha1-release/`
und `build/gamescope-steam-tests.log`.

Das bestehende `make test-steam` wurde am 15. Oktober erneut erfolgreich
ausgeführt (13+15+12 Fälle); Log `build/20261015-steam-gamescope-recheck.log`.
Für die aktuellen Anleitungen werden beide Komponenten in frischen
Buildverzeichnissen erneut paketiert. Laufzeitcode und Mapping bleiben
unverändert; Paketprüfsummen stehen separat bei den Artefakten, damit sich das
Dokument nicht selbst als Pakethash referenziert. Aktuelle Kandidaten:
`build/20261015-steam-base-paddles-release/` und
`build/20261015-gamescope-paddles-final/`. Alte Archive bleiben erhalten.

Die gemeinsame SDL-Fixture bestätigt zusätzlich 18 gerätefreie Fälle mit
1.520 künstlichen Eingabekanten über SDL3 und die SDL2-Kompatibilitäts-API.
Das belegt Decoder-/Mappingverhalten ohne echte Steam-Sitzung. Reale
CachyOS test host-Gamescope-, Update- und Neustartpersistenz bleiben offen.

## Verfahren für weitere Installationen

Die früher hier beschriebenen Schritte für DKMS/lld, Kernelheader und die native
Erstinstallation sind abgeschlossen. Auf dem CachyOS test host ist inzwischen
`gamesir-native-dkms 0.1.0.alpha3-4` mit erfolgreichem Zielbuild und realem
Bootstrap aktiv. Diese Schritte nicht für das optionale Mapping wiederholen.
Die Mappinginstallation verändert die native Autostart-Einstellung nicht.
Deren inzwischen bestätigte Aktivierung steht im aktuellen Bericht unten.

Die folgenden Systembefehle sind Vorlagen für weitere Installationen; der
unten protokollierte Einmallauf ist bereits abgeschlossen und wird nicht
wiederholt. Neue konkrete Pfade, Transaktion und Auswirkungen vorher zeigen
und separat freigeben lassen.

1. Die unprivilegierte Vorprüfung vom 15. Oktober bestätigt den unveränderten
   Vendor-Startvertrag ohne Drop-ins, fehlende Installation beider optionaler
   Pakete, keinen SDL-Hinweis in der geprüften Benutzer-systemd-Umgebung,
   ungefähr 129 GB freien Platz und keine Paketmanager-Sperre. Dies ist eine
   Momentaufnahme, noch keine vollständige Installationsfreigabe.
2. Unmittelbar vorher alle neun Paketdateipfade auf Kollisionen prüfen sowie
   vollständige Unit-Ersetzungen/Drop-ins in Hersteller-, System- und
   Benutzerverzeichnissen erneut vergleichen. Die aktuelle Steam-Umgebung,
   `%t/gamescope-environment` sowie globale und persönliche SDL-Umgebungsquellen
   auf eigene Zuordnungen, Datei-Hinweise und Opt-out prüfen. Fremde
   `ExecStart`-Overrides oder Mappingkonflikte nicht überschreiben.
3. Abhängigkeiten und vollständige Pakettransaktion mit den tatsächlich
   geprüften Archiven bestimmen. Erwartet werden nur die beiden optionalen
   Pakete; Bash und `gamescope-session-cachyos` müssen bereits passend vorhanden
   sein. Ziel-Hooks und ihre ausgelösten Folgeaktionen lesen und bei der Freigabe
   nennen. Die Pakete haben selbst keine Hooks; systemweite Snapshot-/sonstige
   Paketmanager-Hooks können trotzdem laufen. Keine Datenbankaktualisierung,
   Abhängigkeitsinstallation, zusätzlichen Upgrades oder Reparatur daraus ableiten.
   Die lesende Prüfung aller 80 vorhandenen Hookdateien und der drei betroffenen
   Hilfsskripte ergibt für die neun Dateien einschließlich Verzeichniseinträgen:
   Snapper vor/nachher, Limine-Snapper-Sperre, Benutzer-systemd-Konfiguration
   neu einlesen und `/usr`-Zeitmarke aktualisieren. Der Benutzer-Reload ist also
   bereits eine erwartete Paketnebenwirkung; er startet Steam nicht neu.
   Snapshot-Verarbeitung kann die vorhandene Limine-Snapshot-Synchronisierung
   auslösen. Keine passende DKMS-/Modul-/Initramfs-/udev-Auslösung durch diese
   Payload. Diese geprüften Hooks gehören ausdrücklich zur Installationsfreigabe.
4. Nach Freigabe Archive an den gewählten dauerhaften Zielpfad übertragen,
   SHA256-Werte auf beiden Rechnern vergleichen und genau die geprüfte Transaktion
   vor deren Bestätigung kontrollieren. Vorlage:

   ```sh
   sudo pacman -U -- \
     /absoluter/geprüfter/Pfad/gamesir-native-steam-0.1.0.alpha2-1-any.pkg.tar.zst \
     /absoluter/geprüfter/Pfad/gamesir-native-steam-gamescope-0.1.0.alpha1-1-any.pkg.tar.zst
   ```

   Bei Abweichungen stoppen. Danach Paketintegrität, Payload, Eigentümer/Rechte
   und den auf `ExecStart` begrenzten Unit-Eingriff lesend prüfen. Keine native
   Dienst-, Modul-, Treiberbindungs- oder USB-Aktion; kein automatischer Steamstart.
5. Nach eigener Freigabe den Benutzer-systemd-Manager der Gamescope-Sitzung
   neu einlesen lassen:

   ```sh
   systemctl --user daemon-reload
   ```

   Dies lädt noch keine neue Umgebung in das bereits laufende Steam. Anschließend
   nur nach gesonderter Freigabe und mit geschlossenen Spielen Steam beziehungsweise
   die Gamescope-Sitzung regulär beenden und neu starten. Kein automatisches
   Abmelden oder unbeaufsichtigter Rechnerneustart. Den tatsächlichen nächsten
   Sitzungsstart einschließlich Vendor-Starter, Wrapper und Steam-Umgebung prüfen.
6. In Steam L4/R4/L5/R5 einzeln, kombiniert und beim Loslassen prüfen; normale
   Tasten, Sticks und Trigger erhalten. Ausreichend Reaktionszeit geben. Danach
   im Layouteditor vier eigene Paddleplätze prüfen. Die bestehende native
   Geräteinstanz soll unverändert bleiben; kein Funk-Reconnect oder Motorentest
   aus diesem Mappingtest ableiten. Ergebnis von Paketbau, Sitzungsintegration
   und tatsächlicher Spielfunktion getrennt dokumentieren.

Für privilegierte Schritte den vorhandenen geprüften Passwortweg verwenden;
das Passwort ausschließlich in die dafür vorgesehene Abfrage eingeben, niemals
in Chat, Argumente oder Protokolldateien. Die Sitzung des CachyOS test host-PCs und
eine Passwortabfrage auf dem Garuda test host nicht verwechseln.

## Abbruch und Rückbau

Bei geändertem Startvertrag, fremdem Override, Mappingkonflikt, unerwarteter
Pakettransaktion, Hookfehler oder ungeklärtem nativen Zustand stoppen. Bei Freeze
oder neuen kritischen Kernelmeldungen den Test beenden und Diagnose priorisieren.
Keine automatischen Modulwechsel, Resets oder Wiederholungen. Der optionale
Mappingrückbau verändert den nativen Treiber nicht. Falls unabhängig davon ein
nativer Rückweg nötig wird, gilt `ALPHA_INSTALLATION.md`; xpad-Bindung allein
beweist keinen Wechsel von 109c nach 100a.

Nur die Gamescope-Ergänzung lässt sich separat entfernen:

```sh
sudo pacman -R -- gamesir-native-steam-gamescope
```

Auch dies erfordert Freigabe. Nur ihre eigenen Dateien werden entfernt; der
Basishook für Plasma und persönliche Belegungen bleiben erhalten. Nach
genehmigtem `systemctl --user daemon-reload` und regulärem nächstem Sitzungsstart
gilt wieder der Hersteller-`ExecStart`, sofern keine fremden Overrides existieren.
Keine laufende Steam-Sitzung automatisch beenden. Entfernung und spätere
Neuinstallation sind keine Freigabe für native Treiberänderungen.

Soll auch die Basiskomponente entfernt werden, dies danach gesondert freigeben:

```sh
sudo pacman -R -- gamesir-native-steam
```

Bereits gestartete Prozesse behalten ihre geerbte Zuordnung. Für einen
vollständigen Rückbau nach neuer Sitzung die verbleibende Benutzer-systemd-/
D-Bus-/Steam-Umgebung prüfen. `SDL_GAMECONTROLLERCONFIG` nicht pauschal löschen,
weil es fremde Mappingzeilen enthalten kann. Persönliche Steam-Namen und
Spielbelegungen bleiben erhalten.

## Beleggrenzen

Der normale G7 Pro mit 109c-Mapping ist unter Garuda/Plasma bereits real in
Steam geprüft. Die zusätzliche 105e-Zuordnung ist synthetisch mit SDL geprüft;
kein ZZZ-Steam-Nachweis. Der CachyOS test host wird auf Nutzerwunsch mit dem
normalen Modell getestet. Nativer Zielbuild und Bootstrap sind inzwischen
bestanden. Die beiden optionalen Mappingpakete sind inzwischen installiert;
ihre tatsächliche Steam-/Gamescope-Abnahme nach neuem Sitzungsstart bleibt offen. Ein bestehender
Kernel-Eingabenachweis allein ist kein Steam-Mappingnachweis.

## Installation am 15. Oktober: bestanden, Steam unverändert

[tester] hat nach Anzeige der genauen Befehle die Übertragung und genau diese
zwei Pakete einschließlich Passwortabfrage und benannter Systemhooks
freigegeben. Ausdrückliche Grenze: danach nur prüfen, Steam nicht neu starten.
Die Originalarchive blieben erhalten; übertragen wurde in den neuen privaten
Ordner `/home/example/gamesir-native-build/20261015-steam-paddles/`.

| Paket | Version | SHA256 des tatsächlich installierten Archivs |
| --- | --- | --- |
| gamesir-native-steam | 0.1.0.alpha2-1 | `d606a2b58e23c24a5e96ffd287028cda672908518bcda060adbdebfcbb206fa7` |
| gamesir-native-steam-gamescope | 0.1.0.alpha1-1 | `6fa1bd52eeaffeac529ca75d1b269964cb79ef5ad737edac22f25e1496088289` |

Vorprüfung/Installation/Nachprüfung am **15. Oktober 18:06:03–18:06:12 MESZ**:

- Erneut vorliegender Vendorvertrag, Paket-/Hookbestand und Dateiziele geprüft.
  Native Verwaltung gesund, aktive eigene Lease derselben realen Geräteinstanz.
  Keine Bindungs-, Modullade-, Modus- oder nativen Dienstbefehle.
- Beide Archive, Helfer und Freigabebeleg übertragen; Remote-/Lokaldigests und
  Dateigrößen identisch, privater Ordner 0700 und Dateien 0600. Passwort über
  bewährte lokale Askpass-Abfrage für user@CachyOS test host und verschlüsselten
  SSH-Standardeingang, nicht in Dateien/Argumenten/Umgebung/Protokoll gespeichert.
- `pacman -Up --print-format '%n %v'` und danach die vollständige echte
  interaktive Transaktion geprüft: genau zwei neue Pakete, insgesamt 0,08 MiB,
  keine Abhängigkeiten zusätzlich, keine Upgrades/Entfernungen. Erst dann
  die bereits genehmigte Bestätigung an `pacman -U` gesendet. Exit 0.
- Tatsächliche Hooks: Snapper vorher root 88; Limine-Snapper-Sperre; systemd-
  Benutzermanager-Konfiguration; ConditionNeedsUpdate-/usr-Zeitmarke; Snapper
  nachher root 89. Der gelesene user@.service-Vertrag verwendet RTMIN+25 zur
  Reexecution des Benutzermanagers; dessen laufende Steam-Dienste wurden dabei
  nicht neu gestartet. Keine eigene .INSTALL-Datei und keine eigenen Hooks.
- Paketprüfung: Basis 17 Dateieinträge/0 verändert, Gamescope 15/0 verändert.
  Alle fünf plus vier Nutzdateien exakt gegen installierte Archive verglichen;
  root:root und 644/755 wie vorgesehen. Alle Hookquellenhashes unverändert.
- Originale Vendorunit und Herstellerstarter unverändert. Zusammengeführte
  Unit enthält nur das neue Drop-in und den eigenen Wrapper als nächsten
  ExecStart; kein Start dieses Wrappers durch Codex. Native Kern-/Managerdateien
  und geladenes Modul unverändert, Dienst active/running/disabled, PID 28673,
  NRestarts 0. Aktuelle 109c/Adresse 25/Inode 60931 am beobachteten Port 1-3.2
  bleibt an gs_native; eigene aktive Lease und Kernel-Tokens [4, 5] vor/nach gleich.
  Das ist eine aktuelle Besitzprüfung, keine zusätzliche Reconnect-Abnahme.
- Steam-Unit-PID 1139 und echter Steam-Prozess, Startzeit sowie SDL-Umgebung
  vor/nach identisch. Aktuelles Steam erhält die neue Umgebung erst beim
  nächsten regulären Start. Kerneljournal im Installationsfenster ohne Einträge.

Alle 14 Abschlussprüfungen bestanden. Kein Steam-Neustart, keine Abmeldung,
kein Rechnerneustart, kein Spielstart und keine Autostartaktivierung. Auch
nach erfolgreicher Installation ausschließlich lesend geprüft; keine Reparatur
oder automatische Wiederholung. Installationsfreigabe verbraucht.

Sieben remote erzeugte/ausgeführte Originaldateien (123.503 Byte) inklusive
Vor-/Nachzustand, Transaktionsvorschau und tatsächlich ausgeführtem Helfer sind
lokal unter `.local/integration/20261015-steam-paddles-install/records/`
gesichert; alle Größen/SHA256 gegen `remote-record-hashes.json` bestätigt.
Vollständige Konsolenausgabe, Autorisierung, Transferbeleg und SHA256-Liste
liegen daneben privat. Keine privaten Rohzustände/Bootkennungen in Git.
Garuda test host-System unverändert, kein Push.

**Nächster Schritt:** Ein regulärer neuer Steam-/Gamescope-Sitzungsstart muss
separat freigegeben werden. Danach Prozessumgebung/Startpfad prüfen und ohne
Zeitdruck L4/R4/L5/R5 einzeln, gemeinsam und beim Loslassen sowie normale
Eingaben testen. Erst vier sichtbare unabhängige Paddleplätze sind eine
Steam-Abnahme. [tester] möchte anschließend selbst Ship of Harkinian testen;
keine besondere Spielkonfiguration oder universelle Ingame-Belegbarkeit aus
dieser Paketinstallation ableiten.

## Gamescope-Paddles und Autostart am 15. Oktober bestätigt

Nach neuer SteamOS-/Gamescope-Sitzung meldet [tester] zunächst vier sichtbare
Paddles und bestätigt anschließend ausdrücklich: **alle vier funktionieren
unabhängig, normale Eingaben ebenfalls**. Keine neue physische Tasten-
Zuordnung oder besondere Spielaktion daraus ableiten. Ship of Harkinian soll
er später selbst in Ruhe testen; es wurde von Codex weder gestartet noch
konfiguriert. Keine universelle direkte Ingame-/XInput-Belegbarkeit behaupten.

[tester] gab danach die lesende Vorprüfung und konkret
`systemctl enable --now gamesir-native.service` einschließlich Passwort,
Modulladen und nativer Übernahme frei. Die frische öffentliche SSH-Prüfung
um **18:13:39 MESZ** fand den Zielzustand jedoch bereits vor: Dienst
active/running/enabled, PID 2982, NRestarts 0, 109c/Adresse 11 an gs_native.
Deshalb kein redundantes Enable/Start/Modprobe/Bootstrap oder Bindungswechsel.
Die Herkunft der bereits erfolgten Aktivierung wurde nicht separat auditiert;
keine eigene Codex-Aktivierung behaupten.

Die danach freigegebene Passwortabfrage diente ausschließlich einer lesenden
Bestätigung am CachyOS test host um **18:16:36–18:16:37 MESZ**. Wiederverwendeter
Askpass-/SSH-Weg und vorhandener Host.scan-Adapter; keine Geräte-/Input-/USB-
Kontrollnode geöffnet, kein Motorbefehl, kein Steam-Neustart. Alle zehn Checks
bestanden:

| Prüfung | Befund |
| --- | --- |
| Dauerhafter Start | UnitFileState enabled; persistenter multi-user.target-Startlink auf `/usr/lib/systemd/system/gamesir-native.service` |
| Aktueller Dienst | active/running, PID 2982, NRestarts 0, Result success; vor/nach identisch |
| Unit und Modul | erwartete Unit bytegleich; Modul-Srcversion `499FB2049A64E55F54B712C`, drei Opt-ins Y |
| Manager | ok, paused=false, keine aktuellen Scan-/Port-/Gerätefehler, genau eine aktive Instanz |
| Eigene Geräteinstanz | beobachteter Port 1-3.2, 3537:109c, Adresse 11/Inode 50958 an gs_native; vollständiger Instanz-/Parent-/Bootnachweis passt zur aktiven Lease |
| Kernelbesitz | eigene aktive Lease mit passenden Tokens [1, 2], unveränderte native Bindung vor/nach |
| Steam | neue Gamescope-Unit PID 1100 über Mapping-Wrapper; Steam-Prozess 1282 enthält native GUID und paddle1:b12, paddle2:b11, paddle3:b14, paddle4:b13 |
| Aktueller Start | Dienstjournal 18:12:13 Start, 18:12:21 Bootstrap Ergebnis 0/READY, pad=1/imu=1/handover=1, persistente Runtime bereit |
| Kerneljournal | vollständiger erfolgreicher 100a/10→109c/11-Übergang; keine kritischen Oops/Lockups im geprüften aktuellen Bootjournal |
| Bedienung | Nutzer bestätigt alle vier Paddles unabhängig und normale Eingaben nach neuem Sitzungsstart |

Der Prüfcode fasst einzelne Tabellenbefunde in zehn booleschen Checks zusammen;
Tabellenzeilen sind keine zusätzliche Testfallzählung. Die bekannten Hinweise
zum externen unsignierten Modul und xpad-ENOENT beim Abbau bleiben erhalten;
sie verhinderten den dokumentierten aktuellen erfolgreichen Start nicht.
Port, Adressen, Inodes und Tokens sind Beobachtungen dieses Laufs und keine
Produktionskonstanten. Aufgelöste historische Fehler sind keine neuen Fehler.

**Bestätigt:** Autostart ist konfiguriert, die aktuelle native Runtime ist
bereit und Steam verarbeitet vier unabhängige Paddles gemäß Nutzerbeleg.
Das ist kein prospektiv beobachteter unbeaufsichtigter Bootlauf nach unserer
Bestätigung und keine allgemeine Boot-/Suspend-/Hotplug-/Reconnect-Garantie.
Ein neuer Boot-ID-/Startlogbeleg allein beweist den Auslöser des Dienststarts
nicht. Kein automatischer Neustart, Fehler-Release oder erneuter Hardwaretest.
Native Laufzeit und aktivierten Autostart erhalten; Garuda test host-System unverändert,
kein Push.

Private Belege: `.local/integration/20261015-CachyOS test host-autostart-confirm/`,
Rootoriginale unter `records/`. Ausgeführter rein lesender Helfer und Ergebnis
stimmen mit remote ermittelten SHA256/Größen überein; Ergebnis-SHA256
`859419d962d0e0384cef80e669458876621f096361824f2124a9f0c9809dec2d`.
Originale enthalten private Instanzkennungen und bleiben außerhalb Git.
Nutzerbestätigung, öffentlicher Vorzustand, Autorisierung und Prüfsummen sind
separat gesichert. Kein `enable --now` durch Codex ausgeführt, weil Zielzustand
schon vorhanden war.

### Warum xpad zuerst erscheint

Die aktuelle Alpha hat absichtlich keine automatischen USB-Modulaliase:
Der budget- und besitzgeprüfte Manager übernimmt gezielt das Interface.
Vor dieser Übernahme kann Linux den bekannten Dongle an xpad binden, auch
kurzzeitig bei der 109c-Neuanmeldung. Bootstrap und normale native Runtime
laufen anschließend in gs_native; xpad verarbeitet nicht parallel dieselbe
native Sitzung. Eine direkte frühere gs_native-Erstbindung ist ein eigener
künftiger Implementierungsschritt mit Erhalt der Besitz-/Startbudget- und
Rückwegsicherungen. Keine globale xpad-Sperre für andere Controller und keine
Änderung des jetzt laufenden Systems allein aus der Nutzerfrage ableiten.

## Kontrollierter Neustart am 15. Oktober bestanden

[tester] kündigte nach der bestätigten Autostartkonfiguration ausdrücklich einen
neuen PC-Neustart an, führte ihn selbst aus und bestätigte nach der Rückkehr,
dass ausschließlich der Funkcontroller eingeschaltet wurde. Kein manueller
Dienststart, kein Resume und kein Deadband. Codex führte während dieses Tests
nur unprivilegierte SSH-Leseabfragen aus, keine erhöhten Rechte, Start-/Modul-/
Bindungs-/USB-Befehle, Reparatur oder automatische Wiederholung.

**Geprüftes Szenario:** PC booten, anschließend Funkcontroller einschalten,
Steam im regulären Gamescope-Startweg nutzen. Genau dieser einzelne Ablauf
ist bestanden. Nicht mit dem vorherigen rein nachträglichen Autostartaudit
verwechseln, das noch keinen geplanten Boot-Test belegte.

### Zeitlicher Nachweis und automatische Übernahme

Die letzte verifizierte Vorher-Bootkennung stammt aus dem privaten Audit um
18:16:37 MESZ. Der erste frische SSH-Leseschritt nach der Neustartansage traf
bereits die Nicht-Erreichbarkeit; ein SSH-Timeout ist gesichert. Nach Rückkehr
bestätigt eine andere Bootkennung den Rechnerneustart. Die vollständige
Shutdownsequenz wurde nicht aufgezeichnet.

| Beobachtung | Nachweis |
| --- | --- |
| Dienststart | aktuelles Bootjournal 18:35:49, Unit-Prozess nach 13,830289 s seit Kernelboot gestartet |
| Erster erreichbarer Check | 18:36:40,608 MESZ, Uptime 64,43 s; neuer Dienst-PID 807, active/running/enabled, Result success/NRestarts 0 |
| Persistente Einrichtung | multi-user.target-Startlink auf unveränderte geprüfte Unit; Modul-Srcversion 499FB2049A64E55F54B712C |
| Reguläres Steam | neue Gamescope-Unit-PID 1107 ab 18:35:52 über eigenen Wrapper, Steam-Prozess 1246 mit beiden gespeicherten Gerätezuordnungen |
| Funkcontroller zunächst aus | erste Momentaufnahme 109c/Adresse 4 am beobachteten Port 1-3.2 an xpad; noch keine native Sitzung |
| Nach Nutzereinschalten | Dienstjournal 18:37:52 erfolgreicher Bootstrap von 100a/Adresse 9, Ergebnis 0, READY 7/Fehler 0, pad=1/imu=1/handover=1, Tokens [1, 2]; danach ready |
| Nachcheck | 18:38:25,676 MESZ, gleiche neue Bootkennung und gleiche Dienst-PID 807/NRestarts 0; 109c/Adresse 10/Inode 50901 an gs_native |
| Inputgerät | GameSir G7 Pro, in diesem Lauf event13, mit registrierten Linux-Codes 704–707 |
| Steam-Mapping | neue laufende Steam-Umgebung enthält native GUID 03004535373500009c10000053010000 und alle vier Paddlefelder |

Die Momentaufnahme bei ausgeschaltetem Funkcontroller wird ausdrücklich nicht
als Bootfehler gezählt. Erst nach seiner später bestätigten Einschaltung wird
der vollständige native Betrieb bewertet. Die zeitliche Einschaltlatenz wurde
nicht separat gemessen. Port, Adressen, Inodes, event13 und Prozessnummern sind
Laufbeobachtungen; produktive Erkennung bleibt dynamisch.

Der kontrollierte Test benötigte keine neue Root-Status-/State-Abfrage:
Dienstzustand, Startzeit, tatsächliche native Bindung, sysfs-Inputfähigkeiten,
laufendes Steam-Mapping und aktuelles Dienstjournal waren unprivilegiert
lesbar. Keine zusätzliche Aussage über privaten Manager-State, frische
interne Leases oder die Warnungsfreiheit des Kerneljournals ableiten.

### Bedienabnahme und Ergebnis

[tester] beantwortete beide gezielten Abschlussfragen mit Ja:

- Alle vier Paddles in Steam unabhängig, auch kombiniert und beim Loslassen;
  normale Tasten, Sticks und Trigger funktionieren nach diesem Neustart.
- Seit dem Neustart ausschließlich den Funkcontroller eingeschaltet; kein
  manueller Dienststart, Resume oder Deadband.

Die technische Auswertung bestätigt zwölf boolesche Kriterien einschließlich
der beiden ausdrücklich getrennten Nutzerbelege. Aktuelle native Bindung und
Steam-Umgebung ersetzen keine aufgezeichneten frischen evdev-Ereignisse;
der Bedienbeleg stammt für diesen Bootlauf vom Nutzer. Die frühere native
150-s-Ereignisaufzeichnung bleibt ein eigener Nachweis.

**Ergebnis: ein kontrollierter Boot-E2E-Fall bestanden.** Autostart, normale
native Übernahme nach Controller-Einschalten und vier Steam-Paddles blieben
nach diesem PC-Neustart funktionsfähig. Der laufende Zustand bleibt erhalten.
Keine neue Installation, Steam-Einstellungsänderung, kein Spielprofil und kein
Codex-Spielstart. Garuda test host-System unverändert, kein Push.

**Grenzen:** Kein Boot mit bereits eingeschaltetem Funkcontroller und dauerhaft
bestehender 109c ohne neue 100a-Enumeration, kein Suspend/Hotplug/Mehrgeräte- oder
Mehrfachzyklus-Test. Der bisherige Sicherheitscode übernimmt unbekannte
initiale 109c nicht auf Verdacht; dieses andere Startszenario ist getrennt zu
prüfen. Kein neuer Motor-/Kalibrierungs- oder Ship-of-Harkinian-Beleg.

Private Originalberichte, Vorherkennung, SSH-Ausfall, technische Auswertung,
Nutzerannahme und SHA256-Liste liegen unter
`.local/integration/20261015-CachyOS test host-controlled-reboot/`. Alte und neue
Boot-/Instanzkennungen bleiben außerhalb Git. Die Leseberichte wurden lokal
unverändert gesichert; keine neue Paket-/Firmware-/Kerneldatei erzeugt oder
installiert. Kein allgemeines Zuverlässigkeitsversprechen aus einem Bootfall.

## Bazzite: Machbarkeitsprüfung und Migrationsgrenze

Stand: 19. Oktober 2026. **Technisch plausibler Port, noch kein installierbares
oder auf Bazzite validiertes Angebot.** Der Nutzer erwägt Bazzite als Ersatz
für das bisherige CachyOS-Testsystem. Geprüft wurden unsere Quellen und aktuelle
öffentliche Primärquellen; kein Bazzite-Zielsystem, Zielkernelbau, Containerbuild,
Paketinstallationslauf oder Hardwaretest. Keine Änderung an laufenden Systemen,
kein Image-Push und keine Veröffentlichung. Die früheren CachyOS-Ergebnisse
belegen keine Bazzite-Abnahme.

### Was übernommen werden kann und was angepasst werden muss

| Bestandteil | Einschätzung und erforderliche Arbeit |
| --- | --- |
| Gemeinsamer Kerneltreiber | Protokollparser, Bootstrap, Gamepad/Paddles, IIO, optionaler evdev-Sensor und Viermotor-Runtime bleiben die gemeinsame Grundlage. Kein eigener Treiber je Distribution. Kompilieren gegen den exakten Zielkernel samt Konfiguration und `kernel-devel` ist noch erforderlich. Ein vorhandenes Garuda-/CachyOS-Modul ist kein Bazzite-Artefakt. |
| Manager und Steuerprogramm | Vorhandenen systemd-Dienst, Besitz-/Startbudgetregeln und einmalige Freigabe weiterverwenden. Python-Anteile als Userspace-RPM, `gsnative-ctl` neu gegen die Zielumgebung bauen. Paketpfade und Abhängigkeiten prüfen; die vorhandene Client-/Service-Pfadvereinbarung gemeinsam erhalten. |
| Paketierung und Updates | Die Arch-`PKGBUILD`-/ALPM-/DKMS-Paketierung ist nicht direkt übertragbar. Vorgeschlagen: eigener akmod/kmod-Bau und zum Zielkernel gehörendes RPM; Manager/CLI getrennt paketieren. Noch keine RPM-Spezifikation oder Bazzite-Baupipeline implementiert. |
| Desktop-Steam/Paddles | Gemeinsamen geprüften Mappinghelfer erhalten. KDE-Menü, Autostart und Direktstart in der tatsächlich installierten Startkette prüfen; Bazzites eigenen Starter nicht durch unseren bisherigen `/usr/bin/steam`-Wrapper umgehen. Bestehende Benutzermappings und Hinweise erhalten. |
| Gaming Mode | Eigener Bazzite-Adapter zur tatsächlichen Gamescope-Session erforderlich. Unser `steam-launcher.service`-Drop-in und `/usr/lib/steamos/steam-launcher` gelten ausdrücklich für CachyOS. Nicht blind auf Bazzite kopieren. |
| Gyro und SDL/Eden | Gleicher gepaarter evdev-Vertrag und bestehendes experimentelles Profil sind Kandidaten. Sichtbare drei Achsen, richtige Richtung/Einheiten, Gerätezuordnung und Zugriff separat prüfen. Die gemeldete CachyOS-Startbedingung „Controller vor SteamOS eingeschaltet“ ist als offene Zuverlässigkeitsfrage mitzunehmen, keine erwiesene Bazzite-Einschränkung. |
| Rumble/Trigger-Bridge | Griff-FF und Viermotor-Runtime erhalten. Broker-Gruppe, Socket und STOP bei Clientende/Trennung prüfen. Der Forza-/Xodus-Nachweis gilt für die bisherige Umgebung; Bazzite und Steam/Proton-Trigger sind nicht dadurch abgenommen. |

Die Hardwarefunktion steckt überwiegend in unserem bestehenden Treiber. Dass
die Schnittstellen unter Fedora grundsätzlich verfügbar sind, ersetzt weder
einen erfolgreichen Zielbau noch einen Nachweis der Anwendungsintegration.
Keine neue Sensorkalibrierung, Chip- oder Faktorsuche aus diesem Port ableiten.

### Modulbau passend zum Systemabbild

Bazzites geprüfter [Image-Bau](https://github.com/ublue-os/bazzite/blob/b13dde4526115b158e68e6861034b1c233dcf9b8/Containerfile#L35)
wählt Kernel und externe Module gemeinsam über passende akmods-Artefakte.
Universal Blues [akmods-Projekt](https://github.com/ublue-os/akmods/blob/d3958bd6c1a8301d74d46e3b1ed6d9164a434d2d/README.md)
beschreibt vorkompilierte Kernel-/Modul-RPMs für verschiedene Kernelfamilien.
Das ist ein vorhandener Integrationsweg, keine Zusage zur Aufnahme unseres
Moduls durch Bazzite oder Universal Blue.

**Empfohlener Dauerbetrieb, als Architekturvorschlag:** aus einem exakt
identifizierten offiziellen Bazzite-Abbild ableiten, `gs_native` für dessen
Kernel bauen/signieren und RPMs zusammen mit Manager und Steam-Adapter in
dieses neue Abbild aufnehmen. Kernel, Modul und abhängige Userspace-Dateien
gemeinsam prüfen und aktualisieren. Bei fehlendem Modulbau kein als
funktionsfähig freigegebenes GameSir-Abbild ausliefern. Das benötigt eine eigene
gepflegte Bau-/Updatepipeline; sie existiert derzeit nicht. Bazzite empfiehlt
für Anpassungen sein [Image-Template](https://docs.bazzite.gg/Advanced/creating_custom_image/),
ohne dafür den gesamten Distributionsquellcode zu forken.

**Alternative für einen begrenzten ersten Versuch:** Fedora-RPMs auf das
offizielle Abbild layern. Bazzite dokumentiert [RPM-Layering](https://docs.bazzite.gg/Installing_and_Managing_Software/rpm-ostree/)
mit neuem Deployment und Neustart, weist aber auf mögliche Updatekonflikte hin.
Ein RPM allein beweist keine verlässliche akmods-Neuerstellung bei jedem
Kernelupdate. Den Bau-/Scriptletpfad, passende Devel-Pakete und die Zuordnung
zum nächsten Deployment zuerst nachweisen. Keine laufende `/usr`-Schreibbarkeit
erzwingen und keine DKMS-Arch-Installation per Container als Hostinstallation
ausgeben. Ein Container eignet sich später zum Bau; der Treiber muss in den
Hostkernel und der Manager in den Host-systemd integriert werden.

### Bazzites Startkette und mögliche zweite Eingabeschicht

Der geprüfte Bazzite-Quellstand verwendet im Deck-Bau
`gamescope-session-ogui-steam`, aktiviert InputPlumber und berücksichtigt
`gamescope-session-plus@ogui-steam.service`. Der Desktop-Starter ist
[`bazzite-steam`](https://github.com/ublue-os/bazzite/blob/b13dde4526115b158e68e6861034b1c233dcf9b8/system_files/desktop/shared/usr/bin/bazzite-steam).
Er erhält unter anderem Vendor-Optionen und Wayland-Verhalten. Diese
distributionsspezifischen Schritte müssen erhalten bleiben. Der Quellstand
ist nicht mit einer bestimmten veröffentlichten oder installierten Bazzite-
Variante gleichzusetzen: tatsächlichen Image-Digest, Pakete, aktive Session,
User-Units, `steam`-/`ogui-steam`-Konfiguration und Steam-Prozessumgebung prüfen.

Die [Gamescope-Session-Referenz](https://github.com/ChimeraOS/gamescope-session/blob/73d2da84ace7f41006a0f85bd2fdb19ef593a464/usr/share/gamescope-session-plus/gamescope-session-plus#L120)
liest ergänzende Session-Konfiguration aus `/etc` und dem Benutzerverzeichnis.
Das ist ein Kandidat zum Einlesen unseres bestehenden Mappinghelfers, kein
bereits getesteter Bazzite-Hook. Die wirkliche Vererbung bis zum Steam-Prozess
nachweisen, auch wenn OpenGamepadUI oder ein separater User-Dienst Steam startet.
Kein vollständiges `CLIENTCMD` kopieren oder Herstellerargumente fest einfrieren.

InputPlumber/OpenGamepadUI können eine zusätzliche virtuelle Eingabeschicht
bereitstellen. Es ist noch **nicht** belegt, dass sie unseren G7 Pro übernehmen
oder Funktionen entfernen. Vor jeder Anpassung prüfen, ob Steam native oder
virtuelle Geräte sieht und ob alle vier Paddles sowie der gepaarte Sensor
erhalten bleiben. Bazzite enthält ein
[gezieltes Ignore-Verfahren für externe Controller](https://github.com/ublue-os/bazzite/blob/b13dde4526115b158e68e6861034b1c233dcf9b8/system_files/deck/shared/usr/libexec/bazzite-inputplumber-ignorelist).
Falls tatsächlich nötig, eine eng begrenzte Ausnahme für unsere Geräte prüfen;
keine globale Abschaltung der Handheld-Steuerung oder ungeprüfte Ignore-Datei.
Exklusiver nativer USB-Besitz und unbeeinträchtigte Wartung mit Deadband bleiben
verpflichtend. Ein zweiter Hardwareleser ist keine Gyro-Reparatur.

### Sicherheit, Updates, Rückbau und Umstiegsentscheidung

- **Secure Boot:** Signierung und auf dem Ziel vertrauter Schlüssel müssen
  zusammenpassen. Bazzites [Secure-Boot-Unterstützung](https://docs.bazzite.gg/General/Installation_Guide/secure_boot/)
  vertraut unserem zusätzlichen Modul nicht automatisch. Eine eigene sichere
  Signier-/Einmal-Enrolment-Lösung oder spätere offizielle Integration planen;
  kein privater Vendor-Schlüssel verfügbar, keine privaten Schlüssel ausliefern.
  Image-/RPM-Signatur und vom Kernel akzeptierte Modulsignatur getrennt prüfen.
- **SELinux und Zugriff:** Die tatsächliche Zielpolicy und mögliche AVC-Denials
  für Manager, Geräteknoten und Sockets prüfen. `uaccess` für den Sensor sowie
  die bestehende Haptics-Gruppe erhalten. Keine pauschale Policy-Abschaltung,
  kein Welt-Schreibrecht und keine aus einem Einzelfehler abgeleitete breite
  Freigabe. Ob eine eigene kleine Policy erforderlich ist, ist noch offen.
- **Transaktionen:** ALPM-`PreTransaction`-Hooks nicht als RPM-Scriptlets
  übersetzen, die beim Imagebau oder Staging den laufenden Controller lösen.
  Imagebau darf keine Host-Geräte betreiben. Kontrolliertes Dienstende,
  persistente Pause und die überprüfte Rückgabe für tatsächliche Deaktivierung/
  Entfernung erhalten; erste Aktivierung separat freigeben.
- **Rollback:** Bazzite dokumentiert [vorherige Deployments und deren Sicherung](https://docs.bazzite.gg/Installing_and_Managing_Software/Updates_Rollbacks_and_Rebasing/rolling_back_system_updates/).
  Das erleichtert den Rückweg nach einem fehlerhaften Systemupdate, garantiert
  aber keinen fehlerfreien Desktop. Laut [rpm-ostree](https://coreos.github.io/rpm-ostree/administrator-handbook/#filesystem-layout)
  bleibt `/var` deploymentübergreifend bestehen. Unser Managerzustand unter
  `/var/lib/gamesir-native` und lokale Moduloptionen in `/etc` benötigen daher
  eigene Kompatibilitäts-/Rückbauprüfungen. Ein OS-Rollback ist weder ein
  USB-Wechsel `109c→100a` noch das automatische Löschen einer Verwaltungspause.

Vor einem Umstieg mit zugesagter GameSir-Funktionsgleichheit erforderlich:

1. Konkretes Bazzite-Image passend zur Hardware auswählen und per Digest
   festhalten; Kernel/Devel-Konfiguration, Secure Boot, Policy und Session
   lesend prüfen. Kein solcher Zielstand wurde in dieser Untersuchung geprüft.
2. Fedora-Zielbau und RPM-Staging, Datei-/Rechte-/Abhängigkeitstests sowie
   simulierte Update-/Entfernungs-/Rollbackfälle. Keine alten Kernelmodule
   oder anderswo gebauten CLI-Binärdateien blind übernehmen.
3. Erst nach eigener Freigabe kontrolliert installieren und aktivieren;
   eindeutiger Bootstrap/Rückweg, normale Eingaben, vier unabhängige Paddles,
   SDL-/Steam-Gyro und Eden bei Bedarf tatsächlich abnehmen. Griff-FF und
   Trigger-Bridge behalten ihre eigenen Spiele-/Runtime-Abnahmegrenzen.
4. Desktop und Gaming Mode, Boot mit Controller an/aus, spätes Einschalten,
   Funk-Reconnect, USB-Hotplug und Suspend sowie ein Kernelupdate mit
   geprüftem Rückweg. Gemeldete Startbedingung offen führen, bis sie im
   jeweiligen Bazzite-Pfad gelöst oder ausdrücklich als Grenze angenommen ist.

**Entscheidung:** Go für die Portierungsvorbereitung; noch kein Go für einen
als funktionsgleich zugesagten Austausch des getesteten Systems. Es wurde kein
grundsätzlicher Architekturblocker gefunden. Paket-/Kernel-/Sessionintegration
und ihre Abnahme fehlen; ein Distributionswechsel allein belegt keine Lösung
des nachträglichen Steam-Sensorproblems. Bestehende Treiberquellen, Mapping,
Motorprotokoll und experimentelles Sensorprofil bleiben unverändert.
