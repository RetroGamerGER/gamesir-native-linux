> Public export: personal tester, host and path references were anonymized. Historical evidence hashes refer to the private originals.

# Dauerhafte optionale Steam-Integration

Stand: 14. Oktober 2026. Neuer Paketstand **`gamesir-native-steam 0.1.0.alpha2-1`**
für `109c` und zusätzlich `105e`, ausschließlich offline vorbereitet. Auf Garuda
ist weiterhin `0.1.0.alpha1-1` installiert. Dessen realer Logout/Login mit
normalem KDE-Menüstart und Paddle-Funktion ist für `109c` bestanden.
Der native Treiber bleibt unverändert. Das installierte Dokument enthält den vorbereiteten Buildstand;
der nachfolgende Installationsnachweis wird im Repository fortgeschrieben.

## Ziel und belegte Grundlage

Nach einmaliger Installation und einer neuen Plasma-Anmeldung soll Steam bei
normalem Start vier unabhängige Zusatztasten erhalten. Keine pro Spiel
vorgefertigten Aktionen, kein Ersatz normaler Xbox-Tasten und kein Deadband.
Der Treiber funktioniert ohne diese optionale Komponente.

Der vorangegangene Realtest mit Steam-Client 1791918634 bestätigt vier separate
Paddle-Quellen einschließlich Kombinationen/Loslassen und unveränderter
Standardeingaben. Ein Normalstart ohne SDL-Hinweis und ein regulärer Mapping-
Import verloren die Paddles wieder. Das begründet die Integration über den
bereits geprüften Start-Hinweis. Historische Belege, Protokolle und API-Grenzen:
`STEAM_ELITE_PADDLES.md`. Inzwischen ist ein realer Anmelde-/Menüstart mit
diesem Paket bestanden (Ergebnis unten). Steam-Update, Boot, Autostart und
separate Gamescope-Sitzungen sind dadurch nicht automatisch abgenommen.

## Architektur und Startwege

Der Paketbesitz umfasst ausschließlich diese fünf Dateien:

| Datei | Zweck |
| --- | --- |
| `/usr/share/gamesir-native-steam/session.sh` | geprüfte, idempotente Ergänzung von `SDL_GAMECONTROLLERCONFIG` |
| `/etc/xdg/plasma-workspace/env/90-gamesir-native-steam.sh` | lädt den Helfer vor dem Plasma-Sitzungsstart |
| `/usr/bin/gamesir-native-steam` | expliziter Startweg für Tests und separate Gamescope-Konfiguration |
| `/usr/share/doc/gamesir-native-steam/STEAM_INTEGRATION.md` | diese Anleitung |
| `/usr/share/licenses/gamesir-native-steam/COPYING` | GPL-2.0-Lizenztext |

Keine systemd-Dienste, udev-Regeln, DKMS-Dateien, Installationshooks oder
automatischen Steam-Starts. Kein Austausch von Steam-Binärdateien oder
`steam.desktop`, keine Bearbeitung von Steam-Konfigurationen/Spielprofilen.
Die Dateien gehören einem eigenen Paket; normale Steam-Paketupdates ersetzen
sie nicht. Eine künftige Steam-Verhaltensänderung kann dennoch eine neue
Kompatibilitätsprüfung erfordern.

| Startweg | Abdeckung |
| --- | --- |
| KDE-Menü und angehefteter normaler Steam-Starter | normaler Menüstart nach neuer Anmeldung real bestanden; angehefteter Starter nicht separat geprüft |
| Desktop- und Steam-Spielverknüpfungen | dieselbe Sitzungsumgebung |
| regulärer KDE/XDG-Autostart | dieselbe Sitzungsumgebung; Paket richtet keinen Autostart ein |
| bereits laufendes Plasma/Steam | Installation ändert deren geerbte Umgebung nicht |
| separate Gamescope-Anmeldesitzung | explizite Einbindung des Wrappers erforderlich; nicht automatisch verändert |
| Flatpak oder anderer isolierter Launcher | nicht abgenommen, nicht automatisch zugesichert |

Plasma 6.7.5 liest globale und persönliche Umgebungsskripte vor dem Start und
gibt die Startumgebung an D-Bus/systemd weiter. Darauf beruht die gemeinsame
Abdeckung; keine unterschiedlichen Hacks pro Verknüpfung. Persönliche spätere
Umgebungsüberschreibungen behalten ihren Vorrang.
[Plasma-Startcode](https://github.com/KDE/plasma-workspace/blob/v6.7.5/startkde/startplasma.cpp),
[KDE-Umgebungsübergabe](https://github.com/KDE/kdbusaddons/blob/master/src/kupdatelaunchenvironmentjob.cpp).

Der Hinweis erreicht auch andere SDL-Anwendungen in dieser Sitzung. Er gilt
für die native G7-Pro-Zuordnung, nicht für alle angeschlossenen Controller.
Eine separate Gamescope-Sitzung verwendet ihre eigene Clientkonfiguration.
Für einen ausdrücklich gewünschten Start kann dort beispielsweise
`gamesir-native-steam -gamepadui` anstelle des Steam-Clientaufrufs stehen;
vorhandene weitere Argumente bleiben zu erhalten. Ein verschachtelter Test
kann `gamescope -e -- gamesir-native-steam -gamepadui` verwenden. Das Paket
ändert bestehende Gamescope-/CachyOS-Sitzungen nicht automatisch und behauptet
dafür noch keine reale Abnahme.

## Zuordnung, Vorrang und Grenzen

Beide Einträge verwenden den Namen `GameSir G7 Pro` und die tatsächliche PID;
keine vorgetäuschte Xbox-Elite-Identität:

| PID | SDL-GUID | Nachweis |
|---|---|---|
| `109c` | `03004535373500009c10000053010000` | reales SDL-/Steam-Mapping, unverändert übernommen |
| `105e` | `03004535373500005e10000007060000` | aus gespeicherten nativen Gerätemerkmalen abgeleitet und gerätefrei mit installiertem SDL geprüft; kein beobachteter Steam-GUID |

Für `105e` stammen Name, VID/PID, Version `0607` und 17 registrierte Codes
vom realen Alpha3-Test. Die bestehende SDL-Fixture spielt diese Merkmale in
einer Sandbox ohne Hardware nach. Beide SDL-APIs erzeugen die oben genannte
GUID und dieselbe Buttonreihenfolge. Dies belegt den Offline-Mappingpfad,
nicht die ZZZ-Anzeige im Steam-Editor. Im Hardwarelauf wurden nur 704 und 707
betätigt; die physische Zuordnung aller vier Beschriftungen bleibt offen.

Die folgende physische Zuordnung ist für das Standardmodell belegt. Der ZZZ
verwendet zunächst dieselben Code-/Paddlefelder, seine Beschriftung bleibt zu prüfen:

| physische Taste | Linux-Code | SDL-Rohbutton | Paddlefeld |
| --- | --- | --- | --- |
| L4 | 704 | 11 | paddle2 |
| R4 | 705 | 12 | paddle1 |
| L5 | 706 | 13 | paddle4 |
| R5 | 707 | 14 | paddle3 |

Andere Mappingzeilen bleiben bytegenau erhalten. Ein vorhandener Eintrag für
dieselbe native Gerätefamilie hat Vorrang, auch bei Null-/anderer Namens-CRC
oder abweichender Version; der Helfer ergänzt für diese PID nichts. Die andere
PID wird unabhängig ergänzt, sofern dafür kein eigener Eintrag vorliegt. Ein nichtleerer
`SDL_GAMECONTROLLERCONFIG_FILE` verhindert die Ergänzung ebenfalls. Der Helfer
liest solche Dateien nicht, führt keine Mappingdaten als Shellcode aus und
öffnet keine Geräte. Konflikte müssen vor Aktivierung gemeldet werden; kein
stilles Überschreiben einer Benutzerentscheidung.

`GAMESIR_NATIVE_STEAM_DISABLE=1` verhindert eine neue Ergänzung. Es entfernt
keinen bereits geerbten Eintrag. Die GUID ist kein harter Firmwarefilter:
SDL besitzt Versions-Fallbacks. Nach Änderungen an Name, Firmware, SDL-Backend
oder Buttonreihenfolge sind Zuordnung und Konfliktprüfung erneut erforderlich.
[SDL-Matchingcode](https://github.com/libsdl-org/SDL/blob/main/src/joystick/SDL_gamepad.c),
[SDL-Hinweis](https://wiki.libsdl.org/SDL3/SDL_HINT_GAMECONTROLLERCONFIG).

Steam kann weiterhin einen persönlichen Anzeigenamen verwenden. Das Paket
überschreibt diesen nicht. Vier unabhängige Steam-Quellen erweitern nicht die
begrenzte XInput-Ausgabe eines Spiels. Direkte vier zusätzliche Ingame-Buttons
sind deshalb nicht universell zugesichert. Steam Input bietet die bereits
belegten vier individuellen Belegungsplätze; keine Spielaktionen werden
vorgegeben. Embercade bleibt ein späteres Integrationsziel.

## Offline-Bau und Prüfungen

```sh
make test-steam
python -B scripts/package_steam.py source --dest build/steam-source
cd build/steam-source
makepkg --nodeps
```

Nur vorhandene Werkzeuge verwenden. Kein `makepkg -i` oder `-s`, keine
Paketinstallation während des Builds. Das Zielverzeichnis muss fehlen oder
leer sein. Archiv und Stage verwenden eine enge Dateiliste, keine rekursive
Aufnahme des Arbeitsordners. Pakettests prüfen Payload, Dateirechte, Konflikte,
unveränderte Argumentweitergabe an einen künstlichen Steam-Ersatz, Grenzen
von Paketpfaden und reproduzierbare Quellarchive. Sie starten weder echtes
Steam noch SDL-Geräteerkennung oder Hardwaretests.

Ergebnis vom 14. Oktober: 11 Session-/Konflikttests und 14 Paket-/Adaptertests
bestanden; die 14 Pakettests auch aus dem entpackten Quellarchiv in `makepkg`.
Die vollständige Regression bestand nach Ergänzung des neuen Dokumentlinks
in der nativen Dokumentations-Allowlist. Unveränderte Kern-/Parser-/Runtime-
Prüfungen liefen im ersten Durchgang; die betroffenen Alpha-Paketprüfungen
und nachfolgenden Steam-Tests anschließend erneut erfolgreich. Logs lokal
unter `build/steam-integration-regression*.log`. Kein Kernel-/Managercode
geändert. Paketinhalt: fünf eigene Nutzdateien, keine `.INSTALL`-Scriptlets.

## ZZZ-Ergänzung und Rückkehr zum CachyOS test host

[tester] hat die optionale Ergänzung für `105e` beauftragt und möchte den ZZZ
anschließend aufbewahren. Der weitere CachyOS test host-Test verwendet den normalen
G7 Pro. Keine weiteren ZZZ-Hardwaretests als Voraussetzung für das Paket
verlangen; unbestätigte physische Tasten-/Steam-Eigenschaften bleiben offen.

Der neue Stand erhält den 109c-Mappingstring bytegenau. Je PID wird geprüft,
ob bereits ein Benutzer-Mapping vorhanden ist, einschließlich anderer CRC,
Version oder Großschreibung. Beide Familien können gleichzeitig vorhanden
sein, ohne einander zu verdrängen. Dateihinweis, Opt-out, ursprüngliche
Mappingzeilen und alle übrigen Umgebungsvariablen bleiben erhalten.
Die explizite `crc:3545`-Einschränkung gehört zu beiden Einträgen. Die GUID ist
kein Sicherheitsnachweis für USB-Besitz; der Helfer öffnet kein Gerät.

Die Offline-Logwerkzeuge unterstützen jetzt beide PIDs. PID im Logpräfix,
GUID und ausgewählter Steam-Attributblock müssen zusammenpassen. Bei mehreren
GUIDs ist eine ausdrückliche Auswahl nötig. Die 105e-Ausgabe kennzeichnet die
physische Paddle-Zuordnung weiterhin als unbestätigt. Es werden keine
privaten Steam-Bits gesetzt und keine Benutzer-/Spielprofile geschrieben.

Offline-Ergebnis der Ergänzung: **77 Tests** (6 Mapping-, 20 Logaudit-,
23 Paddleaudit-, 13 Session-/Konflikt- und 15 Paket-/Adapterfälle), alle bestanden.
Zusätzlich **18 gerätefreie SDL-Fälle mit 1.520 künstlichen Eingabekanten**
über die installierte SDL3- und SDL2-Kompatibilitäts-API. Standardtasten,
Achsen, Paddles, Kombinationen und unabhängiges Loslassen geprüft. Die
105e-xpad-Negativkontrolle mit anderem Namen und elf Tasten erzeugt
`03008665373500005e10000007060000`; der tatsächlich verpackte native Hinweis
wird beim SDL-Start nicht darauf angewendet, keine künstlichen xpad-Paddles.
24 Vergleichsausgaben für 109c sind unverändert zum vorherigen Commit.
Berichte: `build/results/steam-zzz-*.log`,
`build/results/sdl-buttons/results.json`. Reale ZZZ-Steam-Abnahme bleibt offen.

Neues Paket wird unter `build/steam-zzz-alpha2-release/` erstellt. Es ersetzt
keine Datei am laufenden System; Installation und neue Sitzung bleiben eigene
Schritte. Die Paketversion gehört zur optionalen Steam-Komponente, nicht zur
nativen Alpha3. Keine Änderung an Kernel-/Managercode oder Modulparametern.

Frischer lesender SSH-Check am **14. Oktober, 19:13 MESZ**:

- Normaler G7 Pro am CachyOS test host: `3537:100a`, Port `1-3.2` über Hub,
  Bus 1/Adresse 13; IF0 xpad, IF1 usbhid. Dies ist der bekannte Einstieg des
  späteren nativen `100a→109c`-Starts; kein abweichender ZZZ-Modus.
- Kernel `7.2.9-1-cachyos-deckify` und passende Header vorhanden. Kein
  GameSir-Paket/-Dienst/-Modul installiert oder geladen.
- `dkms` und `lld` fehlen weiterhin. Rein lesende Transaktionsvorschau mit
  den vorhandenen Paketdatenbanken: `dkms 3.4.3-1` und `lld 23.1.1-1.1`,
  keine weiteren Pakete in dieser Vorschau. Vor Installation frisch prüfen;
  keine Datenbankaktualisierung oder Installation durchgeführt.
- `steam-launcher.service` aktiv, unveränderte Vendor-Unit und Launcher ohne
  Drop-ins. Der separate Gamescope-Pfad unten bleibt maßgeblich; der Plasma-
  Hook allein reicht für diese Sitzung nicht.

Nächste kontrollierte Etappen auf diesem Ziel: fehlende Buildwerkzeuge nach
konkreter Freigabe installieren; Alpha3 per DKMS gegen die tatsächlichen
Zielheader bauen und kontrollieren; anschließend die optionale Steam-Komponente
mit einer geprüften, rückbaubaren Gamescope-Launcher-Einbindung installieren.
Aktivierung/Übernahme und reale Eingabetests gesondert freigeben. Kein Garuda-
Kernelmodul auf den anderen Kernel kopieren. Keine dieser Systemänderungen
wurde durch die Offline-Ergänzung oder den lesenden SSH-Check ausgeführt.

Privater SSH-Nachweis: `.local/compatibility/20261014-CachyOS test host-standard-return/`.

Nachtrag: `gamesir-native-steam-gamescope 0.1.0.alpha1-1` ist als optionale
Ergänzung offline implementiert; sie nutzt diesen gemeinsamen Helfer und
delegiert an den unveränderten CachyOS-Starter. Anleitung und Rückbau stehen
im Projektdokument `docs/STEAM_GAMESCOPE.md` und später im eigenen Paket.
[tester] aktualisiert inzwischen das Ziel, möglicherweise einschließlich Kernel;
vor Installation nach Abschluss/Neustart alle Voraussetzungen erneut prüfen.
Die alte genaue DKMS-Download-URL lieferte HTTP 404 und wird nicht durch eine
ungeprüfte Version ersetzt. Die native Installation trifft auf CachyOS einen
Limine-/mkinitcpio-Hook; dessen genaue Folgeaktionen sind noch frisch zu prüfen.
Keine Zielinstallation, Aktivierung oder neue Sitzung ausgeführt.

## Kontrollierte Erstinstallation und Abnahme

1. Paketinhalt, Version, Prüfsumme und Transaktion prüfen; genau das optionale
   Paket, kein Update des Kerneltreibers oder ungeplante Abhängigkeit.
2. Vorhandene globale/persönliche SDL-Umgebungsquellen sowie laufendes Steam
   lesend prüfen. Fremde Zuordnungen nicht ändern. Bei Konflikt anhalten und
   dem Nutzer die konkrete Vorrangentscheidung zeigen.
3. Erst nach Freigabe `sudo pacman -U <geprüftes Paket>` ausführen. Keine
   Dienst-/Modul-/Treiberaktion. Paketintegrität anschließend lesend prüfen.
4. Für einen Test in der bestehenden Sitzung Steam regulär geschlossen halten
   und nach Freigabe genau einmal `gamesir-native-steam` starten. Dieser Test
   prüft den Paketpfad, noch nicht die normale KDE-Anmeldung.
5. In Steam L4/R4/L5/R5 einzeln, kombiniert und beim Loslassen prüfen; normale
   Tasten, Sticks und Trigger erhalten. Danach regulärer Spiel-Layouteditor:
   vier eigene Plätze. Keinen neuen Funk-Reconnect oder Motorentest auslösen.
6. Nach einer vom Nutzer durchgeführten neuen Plasma-Anmeldung Steam normal
   über Menü/Desktop starten; anschließend einen normalen Steam-Neustart
   prüfen. Erst diese reale Prüfung bestätigt die Sitzungsintegration.
   Autostart/Gamescope nur nach eigener Freigabe und tatsächlich prüfen.
7. Ergebnis getrennt protokollieren: Offline-Bau, einmaliger Wrapperstart,
   normale KDE-Startwege, Anmelde-/Updatepersistenz. Kein Erfolg allein aus
   vorhandenen Dateien oder Quellcode ableiten.

Die Installation allein erfordert keinen Rechnerneustart. Ein automatisches
Abmelden wäre jedoch ein Eingriff in die laufende Arbeit und findet nicht
statt. Wenn Steam bereits läuft, ändert ein zweiter Starter seine Umgebung
nicht; zuerst regulär beenden. Bei fehlenden Paddles nicht Treiber/USB neu
starten, sondern Hint und Steam-Mapping lesend vergleichen. Bei Freeze oder
neuen kritischen Kernelmeldungen den Test beenden und Diagnose priorisieren.

Lesender lokaler Installationsaudit, 14. Oktober: natives Steam vorhanden,
kein Steam-Prozess; alle fünf Zielpfade frei. Shell, Plasma und Benutzer-
systemd hatten keinen SDL-Mappinghinweis; die geprüften globalen/persönlichen
Plasma-/Environment-/Profildateien enthalten keinen entsprechenden Eintrag.
Vor tatsächlicher Installation erneut prüfen, weil dies eine Momentaufnahme
ist. Bash/Python sind bereits installiert, keine weitere Paketbeschaffung
erforderlich.

Trotz eigener Hookfreiheit laufen bei `pacman -U` die vorhandenen Garuda-Hooks:
Snapshot-Prüfung und Snapper vor/nach der Transaktion, Config-Agent-Metadaten,
`/usr`-Zeitmarkierung sowie Hinweise zu Fremdpaketen/Orphans/Pacnew und Garuda-
Update-Metadaten/Sync. Keine der acht gelesenen Config-Agent-Regeln trifft
unsere Nutzdateien; keine Konfigurationspipeline dafür. Für diese Transaktion
matchen keine DKMS-, Treiber-, udev- oder Dienst-Hooks. Das ist Teil des
freizugebenden Installationsumfangs, nicht die Behauptung einer hookfreien
Gesamttransaktion. Bei geändertem Hookbestand/zusätzlichen Paketen anhalten.

## Rückbau

Nach eigener Freigabe entfernt `sudo pacman -R gamesir-native-steam` nur die
Paketdateien. Individuelle Steam-Namen, Spielbelegungen und fremde SDL-Mappings
bleiben erhalten. Keine Löschung gemeinsamer Steam- oder Plasma-Konfiguration.
Bereits gestartete Prozesse behalten ihre geerbte Umgebung. Für einen komplett
sauberen Rückbau ist eine neue Sitzung nötig; bei weiterlaufendem Benutzer-
systemd/D-Bus muss zusätzlich geprüft werden, ob der Hinweis dort verblieben
ist. Nie pauschal `SDL_GAMECONTROLLERCONFIG` löschen, weil es fremde Zeilen
enthalten kann. Ein noch erforderlicher Umgebungsschritt ist konkret zu
prüfen/freizugeben. Keine vollständige Rücknahme allein wegen entfernter
Paketdateien behaupten. Der native Treiber bleibt installiert und aktiv.

## Ergebnis der kontrollierten Erstinstallation

[tester] gab ausschließlich die gezeigte Paketinstallation einschließlich
Passwortabfrage, allgemeiner Garuda-Hooks und lesender Kontrolle frei.
Die tatsächliche Transaktion wurde vor ihrer Bestätigung geprüft:
**ein Paket `gamesir-native-steam 0.1.0.alpha1-1`**, keine zusätzlichen
Installationen, Upgrades oder Entfernungen. Erfolgreich am 14. Oktober 2026,
17:21:36 MESZ (15:21:36 UTC), `pacman` Exit 0.

- Quellencommit: `39b47e282c973cb9a090f2a72df4ebc4e7393932`.
- Paket: `build/steam-integration-release-001/gamesir-native-steam-0.1.0.alpha1-1-any.pkg.tar.zst`.
- SHA256: `cc385f85400fdd22454a3db01191c16f3ca7dbe8d686391eee191e8b23cbf4cb`.
- Tatsächliche fünf Nutzdateien bytegenau gegen das Release geprüft; Eigentümer
  root:root und Modi korrekt. Paketprüfung: 17 Einträge einschließlich
  Verzeichnissen, 0 verändert.
- Erwartete Garuda-Hooks liefen, Snapper-Vorher/Nachher 71/72. Keine DKMS-,
  Modul-, Treiber-, Dienstneustart- oder Initramfs-Aktion in der Transaktion.
- Nativer Treiber unverändert `gamesir-native-dkms 0.1.0.alpha2-3`, Modul
  `0.1.0.alpha2`, srcversion `F75F36980BCE065ED853910`; Dienst weiterhin
  active/running/enabled, NRestarts=0. Keine neue Geräteöffnung oder USB-Aktion.
- Steam blieb geschlossen, kein Abmelden und keine laufende Sitzungsumgebung
  verändert. Daher noch **keine reale Abnahme** des installierten Starthelfers
  oder der dauerhaften KDE-Startwege.

Private Vor-/Nachprüfung und Pacman-Transaktionsauszug mit SHA256-Manifest:
`.local/integration/20261014T152113Z-steam-integration-install/`. Release-Audit
und Buildlog bleiben im genannten Buildordner. Keine Rohdaten veröffentlichen.
Nächster separat freizugebender Schritt: einmaliger Steam-Start und Prüfung
der vier Paddles, anschließend reale normale Startwege nach neuer Plasma-
Anmeldung. Keine ungefragte Wiederverbindung, kein Motor- oder Treibertest.

## Reale Anmeldung und normaler KDE-Menüstart bestanden

[tester] gab anschließend den Test der dauerhaften Lösung ausdrücklich frei:
manuell in KDE abmelden, neu anmelden und Steam regulär im KDE-Menü starten.
Keine Terminalzuordnung, kein Aufruf des speziellen Steam-Wrappers, kein
manueller Umgebungsimport. Der Agent führte ausschließlich lesende Prüfungen
und lokale Belegsicherung aus; keine Dienst-, Modul- oder Bindungsänderung.

Vorprüfung 17:24:57 MESZ: Paket unverändert, Steam geschlossen, Plasma-PID
1578/Sitzung 2 ohne SDL-Hinweis. Nach Anmeldung neue Sitzung 5, Plasma-PID
43040 und Steam-PID 47632, derselbe Boot. Plasma, Benutzer-systemd und Steam
enthalten jetzt die geprüfte vollständige Paddle-Zuordnung. Der normale
Menüstart ist durch [tester] bestätigt; die Umgebungsdaten belegen die
Übernahme in der neuen Sitzung.

Frisches Steam-Log **17:29:38 MESZ / 15:29:38 UTC**: native GUID
`03004535373500009c10000053010000`, alle vier Paddlefelder korrekt, normale
Mappings unverändert. Der Attributsatz derselben Sekunde bestätigt Type 30,
PID 4252/0x109c und Maske `0000000000d847ff` mit GRIPS/UPPERGRIPS. Client
1791918634 und geprüfter UI-Hash bleiben gleich. Der unveränderte alte
Controller-Logpräfix wurde per SHA256 geprüft; nur die 5.296 neu angehängten
Bytes flossen in den abschließenden Mappingnachweis ein. Logzeit ist MESZ;
gespeicherte Beobachtungszeit ist UTC. Ein erster textueller UTC-Vorfilter in
`after-login.json` enthält auch alte Attributsätze; maßgeblich ist die danach
korrekt zeitvalidierte Nachauswertung `verified-result.json`.

[tester] bestätigt im Steam-Gerätetest:

- L4, R4, L5 und R5 sichtbar und jeweils unabhängig ansprechbar;
- unabhängiges Loslassen und Kombinationen funktionieren;
- normale Tasten, beide Sticks und Trigger funktionieren weiterhin;
- zusätzlich sind die vier Zusatztasten in KDE sichtbar. Dies ist ein eigener
  Sichtbarkeitsbeleg, kein Nachweis einer durch SDL verursachten KDE-Änderung.

Bis zur Abschlussprüfung 17:32:32 MESZ bleibt dieselbe native Instanz
`3537:109c`, Adresse 16, IF0 `gs_native`/IF1 ungebunden. Dienst weiterhin
active/running/enabled, NRestarts=0. Keine erhöhte Rechteanforderung und keine
Geräteöffnung durch die Prüfschritte. Steam und Treiber bleiben aktiv.

**Abnahme erfüllt für diesen realen KDE-Anmelde-/Menüstart.** Dies ist weder
eine allgemeine Langzeitstabilitätsfreigabe noch ein neuer Ingame-Test mit
vier zusätzlichen XInput-Buttons. Rechnerneustart, Steam-Update, Autostart,
Desktop-Verknüpfungen und separate Gamescope-/Flatpak-Sitzungen wurden in
diesem Lauf nicht einzeln getestet. Keine weitere Wiederholung erforderlich,
um das vorliegende Ergebnis zu dokumentieren.

Private Belege mit SHA256-Manifest:
`.local/integration/20261014T152457Z-steam-session-persistence/`.
Der bestehende Mapping-/Capability-Auditor lief unverändert auf gespeicherten
Logs; die Nutzerbestätigung liefert den getrennten realen Funktionsnachweis.

## CachyOS Handheld: lesende Kompatibilitätsprüfung

Am 14. Oktober 2026 wurde der zweite Rechner auf [tester]' Auftrag ausschließlich
lesend über den bestehenden SSH-Zugang geprüft. Keine erhöhten Rechte, Builds,
Installationen, Geräteöffnungen, Modul-/Dienst-/Bindungsänderungen oder
Moduswechsel. Vorhandene Kerneldateien wurden nur statisch untersucht;
Ausgaben und eine Kopie des FF-Moduls ausschließlich lokal privat gespeichert.
Der zweite G7 Pro soll dort einzeln getestet werden; [tester] bestätigt den
Anschluss über seinen **2,4-GHz-Dongle**, nicht über Kabel oder Bluetooth.

### System und Kernel

| Prüfung | Tatsächlicher Befund | Bewertung |
| --- | --- | --- |
| System | CachyOS Handheld, x86_64; `cachyos-handheld 1.3.2-2` | passende Plattform für den vorhandenen Manager |
| Kernel/Header | `7.2.9-1-cachyos-deckify`, passendes Headerpaket `7.2.9-1`, erzeugte Release-Dateien und `Module.symvers` vorhanden | eigener Build gegen genau diese Header erforderlich; Garuda-Modul nicht kopieren |
| Kernel-APIs | `kzalloc_obj`, `system_percpu_wq`, USB-`shutdown`, FF-`stop` und geprüfte Exporte vorhanden | keine fehlende Schnittstelle in dieser Vorprüfung |
| Konfiguration | USB, Input/evdev, FF-memless, IIO, Modul-Laden/-Entladen vorhanden | erforderliche Subsysteme verfügbar |
| Signaturen | Secure Boot aus, Lockdown `none`, `MODULE_SIG_FORCE` nicht gesetzt | kein Signaturblocker zum Prüfzeitpunkt |
| Werkzeuge | Clang/LLVM, GCC, make, Python, systemd, kmod vorhanden; **dkms und lld fehlen** | Paketvoraussetzungen noch nicht vollständig |
| Installation | kein `gs_native`, kein `gamesir-native.service` | noch kein nativer Betrieb auf diesem Rechner |

Das Paket verwendet `LLVM=1 W=1` und `-Werror`. Der Zielkernel wurde mit GCC
gebaut; daraus allein folgt keine Inkompatibilität. Ein tatsächlicher Build
gegen die Zielheader ist noch nicht erfolgt und bleibt Voraussetzung.

Der nach dem Freeze besonders relevante FF-Abbau wurde auch hier statisch
geprüft: `input_ff_create_memless` trägt `ml_ff_stop` in `ff->stop` ein;
`ml_ff_stop` ruft `timer_shutdown_sync`. Im vorhandenen `vmlinux` ruft
`__input_unregister_device` diesen Callback vor `device_del` auf; der äußere
Aufruf liegt vor `put_device`. Damit ist der für den korrigierten geliehenen
Input-drvdata-Zeiger erforderliche Stop-Vertrag belegt. Kein Ersatz für einen
Zielbuild oder reale Wiederverbindungs-/Stabilitätstests.

Das erste Prüfskript suchte fälschlich nach einer `input_dev`-Signatur und
meldete für FF-`stop` deshalb `false`. Die vollständige Headerprüfung belegt
stattdessen korrekt `void (*stop)(struct ff_device *)`. Ursprüngliche Ausgabe
unverändert erhalten; dies ist ein korrigierter Prüfbefund, kein Kernelmangel.

### Tatsächlicher Steam-Startweg

Installiert sind `gamescope 3.16.25-1`, `gamescope-session-cachyos 1.1.6-1`
und das Steam-Paket `steam-jupiter-stable`. Die aktive Sitzung verwendet
**nicht** den zuvor als Beispiel betrachteten `gamescope-session-plus`-Pfad:

1. `gamescope-session.target` hält `steam-launcher.service` aktiv.
2. Der Benutzerdienst liest `%t/gamescope-environment` und startet
   `/usr/lib/steamos/steam-launcher`.
3. Dieser startet Steam mit `-steamos3 -steampal -steamdeck -gamepadui`
   beziehungsweise einen vorhandenen Devkit-Starter.

Beide abgefragten Sitzungsdienste sind aktiv, ohne Drop-ins. Im beobachteten
Steam-Prozess ist kein `SDL_GAMECONTROLLERCONFIG` gesetzt. Der Plasma-Hook
unseres bisherigen Pakets deckt diesen eigenständigen Startweg nicht ab.

Die inzwischen offline implementierte optionale CachyOS-Ergänzung bindet den
vorhandenen Mappinghelfer vor **diesem** Steam-Start ein. Ein eigenes Drop-in
ersetzt nur `ExecStart`; der kleine Launcher lädt den Helfer und führt den
originalen Starter mit `exec` aus. Argumente, Devkit-Zweig, Umgebungsdatei
und Stop-/Sitzungsverfolgung bleiben erhalten. Noch nicht installiert oder
real aktiviert. Vendor-Dateien und Spielbelegungen werden nicht überschrieben;
bestehende Mappingkonflikte bleiben zu beachten. Nach Änderungen des
Vendor-Startvertrags erneut prüfen, keine pauschale Updategarantie behaupten.

### Zweites Exemplar und Modusgrenze

Der erste gespeicherte Sysfs-Befund zeigt `3537:1022`, Produkt `GameSir-G7 Pro`,
`bcdDevice=0100`, beide USB-Interfaces bei `usbhid`, über einen Hub. Die
Hub-Topologie ist keine grundsätzliche Sperre der dynamischen Erkennung.
`bcdDevice` ist keine bestätigte Firmwareversionsangabe. Unsere Probe und
ID-Tabelle unterstützen derzeit ausschließlich `100a` und `109c` mit den
geprüften Interface-/Endpunktmerkmalen. **Kein blindes Ergänzen von `1022`.**

Der von [tester] verlinkte [xpadneo-Bericht #610](https://github.com/atar-axis/xpadneo/issues/610)
enthält einen anderen G7-Pro-Dongle mit `1022`/HID und anschließend
`10bb`/XInput. Der Nutzer dort berichtet funktionierendes Rumble unter
CachyOS. Das passt zum aktuellen HID-Befund, beweist aber weder den Zielmodus
unseres zweiten Exemplars noch die Anwendbarkeit unseres `100a→109c`-Bootstraps.
Die im Thread ebenfalls diskutierte Kernel-Quirk-Zeile ist keine geprüfte
Lösung für unseren Dongle und wurde nicht übernommen.

Der zuvor verlinkte [Reddit-Erfahrungsbericht](https://www.reddit.com/r/linux_gaming/comments/1pqzvhk/gamesir_g7_pro_vibration_doesnt_seem_to_work_in/)
beschreibt manuelle Tastenkombinationen und anschließend Rumble in Steam;
er enthält keine belastbare Zuordnung dieser Schritte zu unseren USB-IDs.
Beide Berichte ersetzen keine Prüfung von IMU und vier unabhängigen Motoren.

### Nach eigenem XInput-Moduswechsel: 105e bestätigt

[tester] meldete anschließend, den Controller selbst in XInput umgeschaltet
zu haben; Steam zeigt Vibration an und sie funktioniert. Die folgende
SSH-Prüfung um **17:54:25 MESZ** blieb vollständig lesend:

| Merkmal | Bestätigter Befund |
| --- | --- |
| Identität | `3537:105e`, Produkt `GameSir-G7 Pro`, `bcdDevice=0607` |
| Anschluss | derselbe Hubpfad `1-3.2`, Bus 1, neue Adresse 11 |
| Interface 0 | `xpad`, Klasse/Subklasse/Protokoll `ff/47/d0` |
| Endpunkte IF0 | Interrupt OUT `02` und IN `82`, jeweils maximal 64 Byte |
| Interface 1 | ungebunden, `ff/47/d0`, keine Endpunkte im gelesenen Sysfs-Befund |
| Funktion | normales Steam-Rumble vom Nutzer bestätigt; keine Motorbefehle durch die Prüfung |

Damit ist die tatsächliche neue ID dieses Exemplars **105e**, nicht die
`10bb` aus dem Fremdbericht und nicht unsere bisherige Start-ID `100a`.
Die USB-Merkmale unterscheiden sich von der gespeicherten 100a-Konfiguration
(`ff/5d/01`). Daraus keine identische Startsequenz oder Firmwareversion
ableiten. Noch kein Nachweis für sechs IMU-Kanäle, alle vier einzelnen Motoren
oder unabhängige Zusatztasten auf diesem Exemplar.

[tester] bestätigt ausdrücklich, dass dieses Exemplar die **Zenless-Zone-Zero-
Ausführung** ist. Das passt zum bereits archivierten Deadband-Quellstand
`771b28ae75b0a614a6a7fec9aa606606a27b3b8d`:
`vendors/gamesir/models/g7pro/protocol.py:118–129` führt `105e` unter
`UNCONFIRMED_EDITIONS`; `controller_profile.py:398–405` verwendet für diese
Gruppe `write_style='none'`, `input_style='evdev'`; `RESEARCH.md:497` hält die
fehlende Konfigurationsvalidierung fest. SHA256 der Protokollquelle:
`3e64572c66c657d40556df0917674605eb20baef66ed96138be0874fbbb54f52`.
Die Edition ist somit durch [tester] bestätigt, die native Protokollgleichheit
weiterhin nicht. Hier wurde nur vorhandener Quelltext gelesen; kein Deadband
gestartet oder abgeändert. Native PID-Grenzen liegen zusätzlich in
`tools/service/gamesir_native.py`, `src/gs_startup.c` und `src/gs_runtime.c`.

Die erste Nachprüfung um 17:53:53 MESZ erfasste dieselbe Zielinstanz, meldete
aber irrtümlich eine Topologieänderung: das Skript versuchte `idVendor` auch
an USB-Interfaceeinträgen zu lesen. Nach Korrektur ausschließlich dieses
Lesefilters bestätigt die zweite Prüfung dieselbe Adresse/Bindung und keine
Lesefehler. Beide Originalausgaben bleiben erhalten; kein belegter Disconnect.

**Entscheidung:** Gute Grundlage für die weitere Vorbereitung, noch keine
Freigabereife für die native Aktivierung auf diesem Rechner. Der manuelle
Moduswechsel ist erfolgt und normales Rumble unter xpad bestätigt. Nun ist
`105e` die konkrete zusätzliche Protokoll-/Startgrenze: Die damals geprüfte
Alpha2-Probe, ID-Tabelle und Bootstrap unterstützen sie nicht; keine fremde Startsequenz
auf Verdacht senden oder bloß eine ID ergänzen. Die anschließende
[Offline-Prüfung](G7_PRO_VARIANTS.md) stützt einen gemeinsamen GIP-Pfad und
einen möglichen Direktstart; konkrete 105e-Pakete fehlen noch. Danach hat [tester]
die experimentelle gemeinsame Alpha3-Erweiterung ohne vorgeschalteten Capture
beauftragt; deren aktueller Stand steht im verlinkten Variantenbericht.
Zielbuild, optionale
Gamescope-Anbindung und kontrollierte Installation/Aktivierung bleiben
gesonderte Schritte. Funktionierenden xpad-Zustand erhalten.

Private Belege mit SHA256-Manifest:
`.local/compatibility/20261014T154245Z-CachyOS test host/`. Dazu gehören Header-/
Paket-/Sysfs-Ausgaben, gespeicherte Startskripte und statische FF-Disassemblies.
Keine fremden Binärdateien oder privaten Systemausgaben werden versioniert.

## Upstream getrennt behandeln

[Valve-Issue #13510](https://github.com/ValveSoftware/steam-for-linux/issues/13510)
beschreibt einen ähnlichen Mappingverlust bei einem anderen PDP-Controller.
Das stützt den Vergleich, beweist aber weder dieselbe Ursache noch eine
zugesagte GameSir-Korrektur. Unsere lokalen Belege bleiben verfügbar; kein
Issue, PR oder privater Mitschnitt wird ohne Freigabe veröffentlicht.

[SDL_GameControllerDB](https://github.com/mdqinc/SDL_GameControllerDB#contributing)
muss von einer Anwendung geladen werden; daraus folgt keine automatische
Übernahme durch Steam. Die dortige Beitragsrichtlinie lehnt KI-generierte
Issue-/PR-Inhalte ab. Kein automatisierter Beitrag oder dafür erstellter
KI-Einreichungstext. Eine spätere eigene Meldung durch [tester] und ein belegter
Upstream-Fix können die lokale Ergänzung langfristig entbehrlich machen.
