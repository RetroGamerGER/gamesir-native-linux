> Public export: personal tester, host and path references were anonymized. Historical evidence hashes refer to the private originals.

# Vier Zusatztasten bis zur Anwendung: Offline-Nachweis und Integrationsgrenzen

Stand 14. Oktober 2026. **Alle vier Codes 704–707 bleiben eigenständige
Kernel-Eingaben. Keine normale Xbox-Taste wird für eine Zusatztaste verwendet.**
Die physische Zuordnung wurde inzwischen mit realen evdev-Einzelfenstern
und nachträglicher Nutzerkorrektur dokumentiert: [tester] hatte L4/L5 und
R4/R5 bei den Ansagen vertauscht gedrückt. [Beleg und Grenzen](ALPHA_INSTALLATION.md#eingaben-und-korrigierte-physische-tastenbeschriftung).
Der folgende SDL-Nachweis bleibt ein gerätefreier Bibliothekstest.

Aktueller Auftrag: direkte Belegung im Spiel ohne vorab festgelegte Aktionen
oder Profile je Spiel. Konkrete Steam- und Constance-Logs, API-Grenzen und der
vorbereitete gerätefreie Mappingprüfer: [Steam/Proton](STEAM_PROTON_BUTTONS.md).
Die folgenden Bibliotheksnachweise ersetzen diese noch offene Spieleabnahme nicht.

## Mit den installierten SDL-Bibliotheken geprüft

`python -B tests/run_sdl_buttons_test.py` baut auf der bestehenden
SDL-Sensor-Fixture auf. Zehn erfolgreiche Fälle prüfen SDL 3.4.18 und
SDL2-Compat 2.32.74 mit je zwei synthetischen Geräteprofilen und automatischer
beziehungsweise expliziter Zuordnung. Zwei weitere Varianten prüfen die Form
des konkreten Steam-Vorschlags (misc1 erhalten, misc2 nicht neu eingeführt).
SDL2-Compat nutzt SDL3; das sind zwei
API-Pfade, keine zwei unabhängigen Implementierungen.

Die Profile enthalten die bisherigen elf normalen Tasten plus 704–707
(`native15`) beziehungsweise zusätzlich 708 und KEY_RECORD (`alpha17`).
Letzteres entspricht der erweiterten nativen Registrierung. Für insgesamt
944 künstliche Druck-/Loslasskanten prüft die Probe echte SDL-Joystick-Zustände
und Ereignisse sowie die jeweils erwarteten Gamepad-Zustände und Ereignisse.
Bei jedem Einzeltest müssen alle anderen Tasten unbetätigt bleiben.
Pro Fall werden außerdem alle 32 Kombinationen aus A und vier Paddles geprüft:
unabhängiges Loslassen, gehaltene Tasten und keine doppelten Kanten bei
unverändertem Zustand. 18 Achsen- und neun D-Pad-Zustände prüfen die wirkliche
SDL-Ausgabe der normalen Steuerelemente statt nur deren Mappingtext.

| Linux-Code | SDL-Joystick | Mit explizitem Mapping | Physische Bezeichnung nach Nutzerkorrektur |
|---|---|---|---|
| 704 | b11 | `LEFT_PADDLE1` / `paddle2` | L4 |
| 705 | b12 | `RIGHT_PADDLE1` / `paddle1` | R4 |
| 706 | b13 | `LEFT_PADDLE2` / `paddle4` | L5 |
| 707 | b14 | `RIGHT_PADDLE2` / `paddle3` | R5 |

Die Zahlen in `paddle1` bis `paddle4` sind SDL-Mappingnamen. Ihre Reihenfolge
ist nicht links/rechts sortiert. Das ist durch die installierte SDL-API
geprüft. Die physische Spalte ist ein separater evdev-/Nutzerbeleg; noch kein
gemeinsamer Test von Plastik-Taste und tatsächlichem SDL-Spielereignis.

Ohne Mapping erscheinen alle vier als rohe Joystick-Buttons, aber **keine
vier Gamepad-Paddles**. Mit dem neuen Mapping erscheinen alle vier getrennt,
zusätzlich zu den elf unveränderten Standardtasten. Der echte D-Pad bleibt
Hat 0; Sticks und Trigger behalten ihre sechs Achsenzuordnungen.
KEY_RECORD wird im Alpha-Profil als `misc1` und Code 708 unter SDL3 als
`misc2` abgebildet. SDL2 bietet keinen entsprechenden `misc2`-Button;
Code 708 bleibt dort als zusätzlicher roher Joystick-Button erhalten.

Der Test verwendet keine echte Geräteschnittstelle. Bubblewrap isoliert alle
sechs Namespaces; alle Capability-Sätze sind null, NoNewPrivs ist gesetzt.
Es gibt kein `/dev/input`, `/dev/bus/usb`, hidraw oder usbmon. Die Fixture
ersetzt Geräteaufrufe nur im Testprozess durch reguläre Dateien und einen
synthetischen Ereignispuffer; kein Host-uinput, keine Motorbewegung und keine
Änderung von Geräteprofilen oder Systemkonfigurationen.

Protokolle: `build/results/sdl-buttons/results.json` (Schema 2) sowie zehn
Einzellogs. `steam_ui_verified` und `game_binding_verified` bleiben false.
Der reine Generatorvertrag wird zusätzlich mit
`python -B tests/test_sdl_mapping.py` geprüft.

## Überprüfbarer Mappingpfad

`tools/sdl/gamesir_mapping.py` öffnet keine Geräte. Es erzeugt eine SDL-Zeile
für die **von der Zielanwendung gemeldete native evdev-GUID unter 3537:109c**.
Es lehnt 100a, andere Hersteller und erkennbare andere Backend-GUIDs ab.
Die GUID der synthetischen Fixture darf nicht ungeprüft für echte Hardware
übernommen werden: Name, Geräteversion und Backend können sie verändern.
Auch das gewählte Fähigkeitsprofil muss zum nativen Input-Gerät passen.

Nach später freigegebenem Auslesen der tatsächlichen SDL-GUID lässt sich
beispielsweise eine private Mappingdatei erstellen:

```sh
python -B tools/sdl/gamesir_mapping.py --guid "TATSAECHLICHE_32STELLIGE_GUID" --profile alpha17 > gamesir-native-mapping.txt
```

Eine SDL-Anwendung kann sie selbst mit `SDL_AddGamepadMappingsFromFile()`
laden oder den Prozesshinweis `SDL_GAMECONTROLLERCONFIG_FILE` verwenden.
Die installierte Alpha stellt den Generator bereit; sie überschreibt keine
Steam-, Spiele- oder Benutzerkonfiguration. Für einen künftigen Anwendungs-
Start wäre beispielsweise ein explizit konfigurierter Prozessstart mit dieser
Datei geeignet. Dies wurde hier nicht auf eine echte Anwendung angewendet.
Der Test erzwingt Linux-evdev und deaktiviert HIDAPI nur im isolierten
Testprozess. Ein tatsächlich von HIDAPI oder Steam vermitteltes Gerät braucht
zunächst eine eigene Backend-Prüfung.

Der Grund für die Lücke ist konkret: SDLs Linux-Automapping kennt
`BTN_GRIPL/GRIPR/GRIPL2/GRIPR2` und einen besonderen Microsoft-Elite-Pfad;
unsere Codes 704–707 werden darin nicht als Paddles eingeordnet. Das explizite
Mapping ergänzt diese Anwendungsebene, ohne die Kernelcodes zu verändern.
[SDL-Linuxbackend, geprüfter Stand](https://github.com/libsdl-org/SDL/blob/829a65d769d935c4852f8159e964312c0957260a/src/joystick/linux/SDL_sysjoystick.c).
Die API und Dateikonfiguration sind in
[SDL_GamepadButton](https://wiki.libsdl.org/SDL3/SDL_GamepadButton) und
[SDL_GAMECONTROLLERCONFIG_FILE](https://wiki.libsdl.org/SDL3/SDL_HINT_GAMECONTROLLERCONFIG_FILE)
dokumentiert.

## Motoren: SDL-Griffvibration und Impulse-Trigger getrennt

In allen zehn Bibliotheksfällen erreicht `SDL_RumbleGamepad` beziehungsweise
SDL2s `SDL_GameControllerRumble` die künstliche Linux-FF_RUMBLE-Schnittstelle:
Ein Effekt wird hochgeladen und gestartet. Das belegt den API-Pfad, nicht die
Wirkung eines echten Motors in diesem Entwicklungsschritt.

`SDL_RumbleGamepadTriggers` schlägt in denselben Fällen mit „not supported“
fehl. Das passt zur Linux-evdev-Implementierung von
`LINUX_JoystickRumbleTriggers`, die keine Triggerausgabe implementiert.
Vier belegte native USB-Motoren allein machen diese SDL-Funktion daher nicht
funktionsfähig. Der neue native Viermotor-Broker ist eine eigenständige API;
ein Spiel oder Adapter muss ihn ausdrücklich integrieren. Ein veränderter
SDL-Linuxbackend wäre eine weitere Entwicklungsoption, keine vorhandene
Kompatibilität. [SDL-Linuxbackend](https://github.com/libsdl-org/SDL/blob/829a65d769d935c4852f8159e964312c0957260a/src/joystick/linux/SDL_sysjoystick.c),
[SDL-Trigger-API](https://wiki.libsdl.org/SDL3/SDL_RumbleGamepadTriggers).

## Steam, Wine/Proton und Embercade

Die aktuelle Elite-Referenzanalyse, statisch geprüfte Steam-UI-Fähigkeiten
und der neue Praxistest sind in [STEAM_ELITE_PADDLES.md](STEAM_ELITE_PADDLES.md)
zusammengeführt. Neue GameInput-Paddleflags und weiterhin offene Wine-Pfade
sind dort getrennt dokumentiert; kein bloßer Name-/Identitätswechsel.

**Steam Input:** Steam besitzt eigene Eingabegeräte- und Mappingpfade.
Eine erfolgreiche SDL-Probe beweist deshalb keine Paddle-Erkennung im
Steam-Client. Legacymappings können erkannte Eingaben unter anderem in
Tastaturereignisse umsetzen; der emulierte XInput-Gamepadpfad besitzt die
üblichen Standardtasten. Eine Belegung auf zusätzliche Tastaturaktionen
kann für Spiele ein Weg ohne Ersatz bestehender Gamepadtasten sein, erfordert
aber zuerst die gesonderte Erkennung aller vier Quellen im Steam-Client.
Hier wurden keine Steam-Konfigurationen verändert.
[Steam Input](https://partner.steamgames.com/doc/features/steam_controller),
[Legacy Mode Bindings](https://partner.steamgames.com/doc/features/steam_controller/legacy_mode).

**Wine/Proton:** In den gespeicherten und statisch geprüften Ständen
Wine `a15ee2ccf20e2fc9f470badd916855801933d31f` und Proton-Wine
`e60892cc2398b0a83c332a2078c7b85e47bdb42b` berücksichtigt der
`set_report_from_controller_event`-Schalter nur normale Controllerbuttons;
Paddle-Enums gelangen in den unbehandelten Zweig. Der rohe Joystickpfad
kann eine andere Zahl von Buttons beschreiben, ist aber kein Nachweis dafür,
dass ein konkretes Windows-Spiel sie verwendet. Der Haptikpfad reicht
Triggeranforderungen an SDL weiter; ein fehlender SDL-evdev-Triggerbackend
wird dadurch nicht ergänzt. Keine Wine-/Proton-Ausführung oder Änderung.
[Wine-Quelle](https://github.com/wine-mirror/wine/blob/a15ee2ccf20e2fc9f470badd916855801933d31f/dlls/winebus.sys/bus_sdl.c),
[Proton-Wine-Quelle](https://github.com/ValveSoftware/wine/blob/e60892cc2398b0a83c332a2078c7b85e47bdb42b/dlls/winebus.sys/bus_sdl.c).
Standard-XInput selbst definiert keine vier zusätzlichen Paddle-Tasten;
seine Vibration beschreibt zwei Motoren.
[Microsoft XINPUT_GAMEPAD](https://learn.microsoft.com/en-us/windows/win32/api/xinput/ns-xinput-xinput_gamepad),
[Microsoft XInput-Einführung](https://learn.microsoft.com/en-us/windows/win32/xinput/getting-started-with-xinput).

**Embercade:** Laut Nutzer derzeit nicht installiert; die Installation ist für
eine gesonderte Videoaufnahme zur Reddit-Veröffentlichung vorgesehen. Keine
Installation oder Projektänderung vorwegnehmen. Embercade bleibt späteres
Integrationsziel und ist ausdrücklich kein Blocker für die GameSir-Alpha.
Erst später ist dessen Eingabepfad festzustellen: rohe SDL-Joystick-
Buttons 11–14 oder gemappte Paddle-Enums. Beide Eingabefälle sind jetzt auf
Bibliotheksebene überprüfbar. Die Oberfläche und Konfigurationsspeicherung
müssen vier zusätzliche, voneinander unabhängige Aktionen zulassen und diese
auch beim Start der jeweiligen Spiele/Emulatoren weitergeben. Ein Menü, das
nur Standard-Xbox-Aktionen speichert, wird durch mehr Kernelcodes allein
nicht erweitert.

## Was vor der Anwendungsfreigabe noch fehlt

1. Die dokumentierte physische evdev-Zuordnung mit tatsächlichen SDL-Ereignissen
   gemeinsam prüfen; keine Anwendungserkennung aus der Anzahl ableiten.
2. Tatsächliche native GUID und Fähigkeitsprofil mit der Zielanwendung prüfen.
3. Vier unabhängige direkte Spielbelegungen zunächst mit Constance unter
   Steam/Proton testen, einschließlich Loslassen und unveränderter A/B/X/Y-/
   D-Pad-/Stickfunktion. Embercade gehört nicht zum aktuellen Testumfang.
4. Für Impulse-Trigger einen wirklichen Spiel-/Brokeradapter oder ergänzten
   SDL-/Wine-Pfad implementieren und anschließend freigegeben testen.

Diese Schritte benötigen spätere konkrete Freigaben. Die Bibliothekstests
bleiben vollständig offline. Die separat aktivierte native Spielsitzung
wurde für diese Dokumentationsänderung nicht verändert.
