> Public export: personal tester, host and path references were anonymized. Historical evidence hashes refer to the private originals.

# Vier Zusatztasten direkt im Spiel belegen

Stand: 14. Oktober 2026. Ziel: Spielaktion auswählen, L4/R4/L5/R5 drücken,
Belegung übernehmen. Keine vorher festgelegten Spielaktionen, keine Pflicht
zu eigenen Mapping-Profilen je Spiel. Normale Gamepad-Tasten bleiben erhalten.
Ein allgemeines **Gerätemapping** beschreibt Eingaben und ist davon getrennt:
Es entscheidet beispielsweise, dass Linux-Code 704 SDL `LEFT_PADDLE1` ist,
aber nicht, dass diese Taste in einem bestimmten Spiel springen soll.

Constance ist der konkrete Prüffall, nicht das einzige unterstützte Ziel.
Embercade ist laut [tester] nicht installiert, bleibt der separaten Videoaufnahme
vorbehalten und ist **kein Blocker für die GameSir-Alpha**. Keine Installation,
Projektänderung oder Prüfung von Embercade gehört zu diesem Auftrag.

## Ergebnis und Entscheidung

Neuer Folgeauftrag vom 14. Oktober: **zuerst vier eigenständige Paddle-Slots
im Steam-Layouteditor**, danach die direkte Spielebelegung. Der konkrete
Elite-/xone-/SDL-Vergleich und die installierte UI sind inzwischen untersucht:
fehlende Paddle-Zuordnung plus fehlende Grip-Fähigkeiten sind belegt; eine
grundsätzliche Sperre für Type 30 ist es nicht. Aktuelle Abnahme, statischer
Prüfer und virtuelle Alternative: [STEAM_ELITE_PADDLES.md](STEAM_ELITE_PADDLES.md).

Der native Kernelpfad liefert die vier zusätzlichen Eingaben bereits getrennt.
Steam verwendet im gespeicherten Lauf ein SDL-Mapping ohne Paddle-Felder.
Das ist eine konkrete zu schließende Lücke; ein weiteres Kernel-Buttonformat
oder eine bloße Umbenennung des Geräts löst sie nicht. Ein geprüfter
Mappingvorschlag ist offline vorbereitet, noch nicht in Steam angewendet.

Zusätzlich sieht Constance bislang das Layout `XInputControllerWindows`.
Dieser Pfad bietet keine vier frei hinzufügbaren Standard-XInput-Tasten.
Ein erfolgreicher Steam-Paddle-Test wäre deshalb ein Zwischenziel, **kein
Nachweis des gewünschten spielinternen Belegens**. Der nächste direkte
Kandidat ist der vorhandene rohe Joystick-/HID-Pfad von Proton. Ob Constance
ihn im Belegungsmenü akzeptiert, ist offen. Eine virtuelle Kopie des Gamepads
beseitigt diese Spiel-/API-Grenze nicht automatisch.

Bei der vorherigen Offline-Arbeit wurden keine Tastaturbrücke, kein virtuelles
Gerät und keine spielbezogenen Aktionsprofile angelegt. Alpha, Steam-
Konfiguration, Proton-Präfixe, Module und Bindungen blieben dabei unverändert.
Die reale Vorprüfung, der gesondert freigegebene Rückweg und der inzwischen
durchgeführte Constance-Test sind unten getrennt dokumentiert.

## Tatsächliche Steam-Erkennung

### Constance-Test am 14. Oktober 2026: stabiler Kurztest, Paddles nicht belegbar

Nach Installation und separat bestätigter Wiederaktivierung von Revision
`0.1.0.alpha2-2` wurde Constance regulär über Steam gestartet. Steam-Einstellungen,
Gerätemapping, Treiber und Dienst wurden für diesen Test nicht verändert.
Die ausdrücklich freigegebene Überwachung las nur Managerstatus und sysfs;
sie öffnete keine USB-/Input-Geräte und erstellte keinen USB-Mitschnitt.

- 55 Statusproben von **15:14:52 bis 15:19:24 MESZ**, ungefähr alle fünf Sekunden,
  über 272,153 Sekunden: alle gesund, Manager `active`, nicht pausiert, keine
  Gerätefehler oder Statuskonflikte. Identität `3537:109c`, Adresse 8,
  Instanz-Inode und IF0-Bindung an `gs_native` blieben in allen Proben gleich.
- [tester] bestätigt normale Eingaben **durchgehend ohne Aussetzer oder Abbruch**.
  Die vier Zusatztasten konnte er im Spiel nicht belegen. Einzelne vom Spiel
  angezeigte Tastennamen und eine erneute evdev-Aufzeichnung liegen nicht vor;
  daraus keine genaue Aussage über jede einzelne Buttonkante ableiten.
- Steam zeigt laut Nutzer **Generic Xbox Controller**. Linux und der frische
  SDL-Mappingeintrag nennen dagegen `GameSir G7 Pro`; die Ursache der
  abweichenden UI-Bezeichnung ist nicht durch einen Mappingwechsel geprüft.
- `controller-before.txt:2273` enthält um 15:11:06 die aktuelle GUID
  `03004535373500009c10000053010000`, normale Buttons und `misc1:b16`, aber
  keine vier Paddlefelder. Der Offline-Prüfer ergänzt im privaten Vorschlag
  ausschließlich `paddle1:b12,paddle2:b11,paddle3:b14,paddle4:b13` und erhält
  die bestehenden Belegungen. **Dieser Vorschlag wurde nicht angewendet.**
- Das frische `player-after.log` nennt `Using Windows.Gaming.Input` sowie
  das konkrete Unity-Gerät `Xbox Controller (XInputControllerWindows)`.
  Diese beiden Meldungen widersprechen sich nicht: WGI als Backend beweist
  kein erweitertes Layout im Spiel. Die Rebind-Meldungen für `buttonWest`
  und `buttonEast` lassen sich ohne Einzelzuordnung keiner Zusatztaste zuweisen.

Auf [tester]' Wunsch wurde die Überwachung um **15:19:25 MESZ** gezielt per
SIGTERM beendet; alle drei zugehörigen Prozesse sind beendet. Exit `-15`
bezeichnet diesen angeforderten Abbruch, keinen Managerfehler. Danach Dienst
`active/running`, `enabled`, unveränderte Hauptprozess-ID, `NRestarts=0`.
Der native Treiber bleibt zum Spielen aktiv. Kein weiterer Versuch gestartet.

Private Belege einschließlich Nutzerergebnis, Originalprotokollen und 20
SHA256-geprüften Dateien:
`.local/integration/20261014T131303Z-constance-live-002/`.
Die Beobachtung belegt diesen kurzen Spielelauf, keine lückenlose Erfassung
zwischen Statusproben, allgemeine Langzeitzuverlässigkeit oder erfolgreiche
Paddle-Integration. Insbesondere wurde kein bestimmter konkurrierender
USB-Zugriff provoziert, um jeden Konfliktpfad erneut auf Hardware zu prüfen.
Der Nutzer beendete diesen Lauf. Sein anschließender Elite-Integrationsauftrag
wird ausschließlich offline bearbeitet; siehe den oben verlinkten Bericht.

### Reale Vorprüfung am 13. Oktober 2026: Test angehalten

Der Nutzer bestätigte Controller verbunden, Deadband geschlossen, Constance
beendet und Steam geöffnet. Der folgende Leseschritt wurde einschließlich
Passwortabfrage gesondert freigegeben. Bei der Vorprüfung ab 19:20 MESZ war der Dienst
`active/running` und `enabled`, der Manager aber **`blocked`** mit
`Foreign device handle held by PID 122327`. Das sind verschiedene Zustände:
Ein laufender Dienst oder weiterhin registriertes Input-Gerät bestätigt keine
gesunde Verwaltung. Die reale Instanz war `3537:109c`, Bus 8, Adresse 21,
Port `8-6`, IF0 bei `gs_native`, IF1 ungebunden, Input `event13/input63`,
Name `GameSir G7 Pro`. Diese Metadaten wurden um 19:26 MESZ erneut bestätigt.

Der separat freigegebene Lesezugriff auf den gespeicherten Managerzustand
bestätigte dieselbe Instanz, vorhandene Kernel-Besitztokens,
`end_attempted=false` und `cleanup_attempted=false`. Gespeichert war `failed`,
im Live-Manager `blocked`: Der aktuelle Fehlerpfad speichert zuerst `fail()`
und setzt danach den Live-Zustand auf `blocked`. Ein Dienstneustart würde den
gespeicherten Besitz erneut attestieren und könnte anschließend END auslösen;
er ist deshalb keine harmlose Statuskorrektur.

Belegte Zeitfolge, alle Uhrzeiten MESZ:

| Zeit | Nachweis |
|---|---|
| 18:48:49 | Steam `gameprocess_log.txt:38` ordnet PID 115355 Constance/AppID 2313700 zu |
| 18:48:50 | Manager protokolliert ersten Fremdzugriff durch genau PID 115355 |
| 19:08:44 | Manager meldet nach neuer Geräteinstanz erneut native Bereitschaft |
| 19:14:28 | Manager protokolliert zweiten Fremdzugriff durch PID 122327 |
| 19:21:49 | Gesicherte freigegebene Statusabfrage bestätigt die zweite Sperre |

Beide Prozesse waren bei der Nachprüfung beendet. Der konkrete Prozessname
und welcher der zwei überwachten Gerätedateipfade offen war, wurden damals
nicht protokolliert. Der erste Zugriff gehört nachweislich zum Constance-
Prozessverbund; der zweite bleibt unzugeordnet. **Ein offener Deskriptor beweist
weder gesendete USB-Kommandos noch einen schädlichen oder ausschließlich
lesenden Zugriff.** Normale evdev-Deskriptoren lösen diesen Guard nicht aus.

Der installierte Manager stimmt per SHA256 mit dem untersuchten Quelltext
überein. `Host.guard()` prüft vor dem periodischen `info` auch fremde offene
usbfs-/native Kontrollhandles. Jeder entsprechende Fehler setzt eine bleibende
Sperre; `return_one()` sendet für `blocked/109c` kein END. Das Verschwinden des
Prozesses hebt die Sperre nicht auf. `resume` verweigert einen offenen Besitz,
und `release` pausiert zunächst nur die Übernahme. Dies ist ein konkreter
Integrationsblocker vor dem Paddle-Test, kein Nachweis eines defekten
Buttondecoders. Native Kernel-Eingaben können währenddessen weiterlaufen.

Zusätzlich enthält das vorhandene Kerneljournal um 19:08:04 einen echten Oops
in `dma_resv_iter_first_unlocked`, mit `amdgpu_vm_sdma_update` und weiteren
AMDGPU-Aufrufen. Um 19:32:24 folgt ein zweiter Oops mit demselben Grafikpfad.
`gs_native` steht in der Liste geladener Module, nicht in diesen Stacktraces.
Die Ursache oder Unabhängigkeit von anderen Fehlern ist
damit nicht bewiesen. Vor weiteren Spieletests ist ein regulärer Systemneustart
empfohlen; dieser wurde weder ausgelöst noch als erfolgt dokumentiert.

Steam wurde nicht neu gestartet, das Paddle-Mapping nicht angewendet und kein
Spieltest gestartet. Private Befunde liegen unter
`.local/integration/20261013T172038Z-steam-live-001/`; keine vollständigen
System-/Steam-Protokolle oder lokalen Besitzkennungen in Git übernehmen.

**Kontrollierter Rückweg, jeweils separat freigegeben und durchgeführt:**

1. Einmal `gamesir-native release`: `paused=true`, weiterhin
   `returned=false`, `blocked/109c`, `busy=false`. Der CLI-Exitcode 1 meldet
   den offenen Rückweg; die Pause ist trotzdem wirksam. Kein weiterer END-
   oder Bootstrap-Aufruf. Keine manuelle Treiberbindung und kein Modulwechsel.
2. [tester] entfernte ausschließlich den Dongle. Nach bestätigter Abwesenheit
   und zusätzlicher Wartezeit zeigten Status und gespeicherter Zustand
   `paused=true`, `returned=true`, `devices={}` und `leases={}`. Das bestätigte
   zunächst Entfernung und Besitzauflösung, noch keine xpad-Funktion.
3. Nach separat bestätigtem Einstecken/Verbinden zeigte sysfs um 19:33:13
   `3537:100a`, Bus 8, Adresse 23, IF0/xpad und IF1/usbhid. Das Journal zeigt
   davor kurz 109c/Adresse 22; Einstecken ist also kein garantierter sofortiger
   PID-Wechsel. Erst die aktuelle 100a-Instanz bestätigt den Rückkehrmodus.
4. [tester] bestätigte anschließend normale Tasten, Sticks und Trigger im
   KDE-Controller-Test. Der xpad-Rückweg ist damit technisch und funktional
   belegt. Die native Paddle-/Spieleabnahme ist weiterhin offen.

Beim physischen Entfernen meldete der Kernel `final motor stop failed: -19`
(`ENODEV`), ohne Wiederholung. Ein empfangenes STOP-Paket ist damit ausdrücklich
nicht belegt. In diesem Lauf wurden keine Motorimpulse angefordert. Keine
Fehlerfreiheit des gesamten Kernels behaupten: Grafik-Oops siehe oben.

Am Ende dieses historischen Rückwegs blieb der Dienst `active/running` und
`enabled`, das Modul geladen,
aber die Übernahme ist **persistent pausiert**. Diese Pause bleibt auch nach
einem Hostneustart erhalten. Ein Dienststop/Entladen war für diesen engen
Rückweg nicht nötig. Eine spätere native Wiederaufnahme benötigt eine neue
Freigabe und muss die nun belegte Konfliktursache berücksichtigen. Die inzwischen
freigegebene Installation und Wiederaufnahme mit Revision 2 vom 14. Oktober
stehen in [MANAGER_CONFLICT_FIX.md](MANAGER_CONFLICT_FIX.md).

Gezielter weiterer Arbeitsbedarf: Fremdzugriffsdiagnose und Konfliktverhalten
bei normalem Proton-Gerätezugriff korrigieren und offline regressionsprüfen.
Die Schutzprüfung nicht pauschal abschalten oder anhand des Prozessnamens
umgehen. Vor erneuter nativer Aktivierung und dem eigentlichen Steam-Paddle-
Test einen frischen Systemzustand prüfen. Änderungen an der installierten
Alpha und Wiederaufnahme bleiben separat freizugeben.

### Zuvor gespeicherte Erkennung und Mappingvorschlag

Vor der Einschränkung auf ausschließlich Offline-Arbeit wurden nur vorhandene
Metadaten gelesen: Steam hatte einen Dateideskriptor auf das native evdev-Gerät
`event13`; dessen Name war `GameSir G7 Pro`, IDs `0003:3537:109c:0153`.
Die Prozessabbildung führte Steams eigene `ubuntu12_32/libSDL3.so.0`.
Diese Bibliothek wurde nicht separat geladen oder ausgeführt. Der bisherige
System-SDL-Test ist somit nicht automatisch ein Test von Steams SDL-Version.
Statischer Revisionsstring: `SDL-release-3.4.0-1359-g70e9cc86d`, Datei-SHA256
`ae4e7ec75bde30e4ddf70b11c16be95ed9c28d31095798e9309ee6392b29f702`.

Vorhandene lokale Dateien belegen:

| Quelle und Fundstelle | Beobachtung |
|---|---|
| Steam `logs/controller.txt:1848–1859` | Am 13.10. um 18:26:01 Erkennung über `sdl://7`, VID/PID `3537:109c`; GUID `03004535373500009c10000053010000` |
| `controller.txt:1859` | Mappingname `Generic X-Box pad`, elf Standardbuttons, Achsen und D-Pad; keine Felder `paddle1` bis `paddle4` |
| Steam `config/config.vdf:710–714` | `SDL_GamepadBind` enthält dieselbe VID/PID/Version mit GUID `03000000373500009c10000053010000`, altem Namen und ebenfalls ohne Paddles |
| `logs/controller_ui.txt:743–754` | Type 30, Capability-Wert `00000000001843ff`, generische UI; keine selbst erfundene Interpretation dieser Zahlen |
| `controller_ui.txt:765–776` | Für Constance/AppID 2313700 wurde `controller_base/empty.vdf` geladen |
| `controller.txt:1915–1924` | Dazu `mapping uses xinput : false`; kein Beweis, dass das Spiel selbst keinen XInput-Pfad benutzt |

Der gespeicherte Mappingname erklärt die Anzeige plausibel. Ohne kontrollierten
Mappingwechsel ist nicht bewiesen, welcher Cache-/Prioritätspfad ihn endgültig
bestimmt. Ein Name ist keine Gamepad-Fähigkeit. Der offene evdev-Deskriptor
beweist, dass Steam das native Gerät benutzt, aber kein individuelles Empfangen
aller vier Buttonkanten im Steam-Layouteditor. Das aktive Mapping beschreibt
sie jedenfalls nicht. Der Browser-Test mit unabhängigen Tasten ist eine
zusätzliche Nutzerbeobachtung, kein durch uns wiederholter Test.

Die Protokolle enthalten historische 100a- und 109c-Sitzungen. Der letzte
passende 109c-Eintrag ist kein Live-Zustandsnachweis. Vor einem späteren Test
müssen tatsächliche GUID, native Instanz und Fähigkeiten erneut geprüft werden.

## Welche Schnittstellen zusätzliche Buttons erhalten können

| Pfad | Zusätzliche unabhängige Eingaben | Grenze für direktes Belegen |
|---|---|---|
| Linux evdev / SDL Joystick | Die vorhandenen Codes 704–707 beziehungsweise rohe Buttons b11–b14 | Spiel muss diese Rohbuttons benutzen und anbieten |
| SDL Gamepad | Vier definierte Paddle-Enums; unser explizites Gerätemapping besteht die gerätefreien Bibliothekstests | Anwendung darf die Enums nicht ignorieren oder auf Standardtasten reduzieren |
| Steam Input API | Erkannte Quellen können Spielaktionen zugeordnet werden | Benötigt Unterstützung und angebotene Aktionen durch das Spiel; kein allgemeiner Ersatz für dessen Belegungsmenü |
| Steam Xbox-Emulation / Standard-XInput | Standard-Xbox-Tasten | Kein Feld für vier weitere Paddles; reservierte Bits nicht zweckentfremden |
| DirectInput `DIJOYSTATE2` | Bis zu 128 Buttonfelder | Spiel muss erweitertes Format verwenden und zusätzliche Buttons im Menü zulassen |
| Raw Input / HID | Descriptor kann weitere Buttons beschreiben | Spiel muss den Descriptor und die betreffenden Reports auswerten |
| Windows.Gaming.Input `RawGameController` | Variable `ButtonCount` | Spiel muss Raw-Controller unterstützen |
| Windows.Gaming.Input `Gamepad` | Die API definiert ausdrücklich **Paddle1–Paddle4** | Proton/Provider und Spiel müssen die Flags tatsächlich weiterreichen und auswerten |

WGI darf nicht pauschal mit XInput gleichgesetzt werden. Microsoft dokumentiert
Paddleflags, während Standard-XInput keine solchen Felder besitzt. Ein Spiel
mit ausschließlich festem XInput-Layout kann diese vier neuen Controllerbuttons
nicht ohne Anpassung seines Eingabepfads anbieten. [XInput](https://learn.microsoft.com/en-us/windows/win32/api/xinput/ns-xinput-xinput_gamepad),
[WGI-Paddles](https://learn.microsoft.com/en-us/uwp/api/windows.gaming.input.gamepadbuttons?view=winrt-26100),
[DirectInput](https://learn.microsoft.com/en-us/previous-versions/windows/desktop/ee416628(v=vs.85)),
[RawGameController](https://learn.microsoft.com/en-us/uwp/api/windows.gaming.input.rawgamecontroller.buttoncount?view=winrt-26100),
[SDL-Paddles](https://wiki.libsdl.org/SDL3/SDL_GamepadButton).

Valve beschreibt die Xbox-Emulation ausdrücklich als Übersetzung in einen
Xbox-Controller; zusätzliche Quellen können dabei auf bereits vorhandene
Tasten abgebildet werden. Das erfüllt unser Abnahmekriterium nicht.
[Steam Gamepad Emulation](https://partner.steamgames.com/doc/features/steam_controller/steam_input_gamepad_emulation_bestpractices?l=english).

## Constance und Proton: Beleg statt Vermutung

Constance: AppID `2313700`, Build `25297435`; letzter untersuchter Start
13.10.2026 um 18:48:47 MESZ mit Proton Experimental, Versionstext
`experimental-11.0-20261008-x86_64`. Vorhandenes `Player.log`:

- Zeile 7: Unity `6000.3.23f1`; lokale InputSystem-DLL-Version `1.20.0.0`.
- Zeile 29: `Using Windows.Gaming.Input`.
- Zeile 54: Gerät `Xbox Controller (XInputControllerWindows)` und entsprechendes Layout.
- Zeilen 72–78: Rebinding normaler XInput-Gamepad-Pfade; kein Paddle-Nachweis.

Das vorhandene Präfix führt VID/PID 3537:109c als `Wine XInput compatible device`
mit Dienst `xinput`. Damit ist der beim Spiel angekommene Layouttyp belegt;
die exakte erste Stelle des Signalverlusts im laufenden Proton ist damit
noch nicht vollständig gemessen. Statische Namen wie `GamepadControlWhitelist`,
`KeyboardControlWhitelist` und `SwitchCurrentControlScheme` in Spielassemblies
sind Anhaltspunkte, keine vollständig analysierte Ablehnungslogik. Kein Spielcode
wurde ausgeführt oder geändert.

Der gespeicherte Proton-Wine-Quellstand
`e60892cc2398b0a83c332a2078c7b85e47bdb42b` zeigt konkrete Unterschiede:

- `winebus.sys/bus_sdl.c:870–904`: Der gemappte Controller-Schalter übernimmt
  Standardbuttons; Paddle-Enums werden nicht in den Report übernommen.
- `bus_sdl.c:300–386,819–835`: Der rohe Joystickpfad baut die HID-Buttonanzahl
  aus `SDL_JoystickNumButtons` und erhält Buttonindizes. Bei geöffnetem
  SDL-Controller wird dieser rohe Ereignispfad verworfen.
- `windows.gaming.input/gamepad.c:266–318`: Die Gamepad-Lesefunktion setzt
  Standardbuttons und D-Pad, jedoch keine WGI-Paddleflags.

Dies sind statische Aussagen zu einem fixierten Quellstand. Das ähnliche Datum
des installierten Experimental-Builds beweist nicht, dass genau dieser Code
den protokollierten Spielelauf bedient hat.
[SDL-Backend](https://github.com/ValveSoftware/wine/blob/e60892cc2398b0a83c332a2078c7b85e47bdb42b/dlls/winebus.sys/bus_sdl.c),
[WGI-Implementierung](https://github.com/ValveSoftware/wine/blob/e60892cc2398b0a83c332a2078c7b85e47bdb42b/dlls/windows.gaming.input/gamepad.c).

### Zweiter direkter Kandidat: vorhandener Raw-Joystickpfad

WineBus liest im genannten Quellstand unter
`HKLM\System\CurrentControlSet\Services\WineBus` den DWORD-Wert
`Map Controllers` (mit Leerzeichen), standardmäßig 1. Wert 0 verhindert dort
das Öffnen des gemappten SDL-Controllers; anschließend verwendet das SDL-Backend
seinen rohen Joystick-HID-Descriptor. Das könnte die vorhandenen Zusatzbuttons
ohne Tastaturumsetzung und ohne neues virtuelles Gerät erhalten.
[Optionsleser und Standardwert](https://github.com/ValveSoftware/wine/blob/e60892cc2398b0a83c332a2078c7b85e47bdb42b/dlls/winebus.sys/main.c).

**Nicht angewendet, kein bestätigter Fix.** Diese Option betrifft den WineBus
des jeweiligen Präfixes und möglicherweise andere Controller darin; sie ist
keine neue Spielaktionsbelegung. Backendwahl, bereits gespeicherte XInput-
Geräteklassifizierung, Achsen, Trigger und Force Feedback müssen separat geprüft
werden. `SDL_GAMECONTROLLER_IGNORE_DEVICES` ist kein Ersatz: der geprüfte
Proton-Code verwirft das Zielgerät damit, statt es in den Raw-Modus umzuschalten.

Ein Raw-HID-Gerät kann in Unity als Joystick statt als Gamepad erscheinen.
Die neuere Quellenprüfung zeigt allerdings: sechs Achsen und mindestens
14 Buttons genügen auch im Raw-Pfad für `is_gamepad` und `WINE_COMP_XINPUT`.
Das trifft Alpha17; `Map Controllers=0` garantiert daher keinen anderen
Constance-Gerätetyp. [Aktueller Quellenbeleg](STEAM_ELITE_PADDLES.md#steam-windows-apis-und-andere-launcher).
Ein Belegungsmenü muss auch diese Geräteklasse akzeptieren. Die zugängliche
Unity-Dokumentation 1.14 beschreibt dieses Verhalten; sie ist **kein exakter
Quellnachweis** für Constances lokale Version 1.20.
[Unity-Geräteklassen](https://docs.unity3d.com/Packages/com.unity.inputsystem@1.14/manual/Gamepad.html).

## Erweitertes virtuelles Eingabegerät und allgemeine Kompatibilität

Unser natives Gerät besitzt bereits mehr als elf Buttons. Eine virtuelle
evdev-/HID-Kopie kann einen Transport ergänzen, aber weder XInput erweitern
noch zusätzliche akzeptierte Controls im Spiel erzeugen. Zwei vollständige
Gamepads könnten Doppelereignisse oder eine andere Spielerzuordnung erzeugen.
Ein reines Zusatzbutton-Gerät müsste das Spiel gleichzeitig mit dem primären
Gamepad akzeptieren. Ein ersetzendes Gerät bräuchte außerdem geprüftes Routing
von Sticks, Triggern, Force Feedback und Geräteverlust, ohne die funktionierende
native Laufzeit zu beeinträchtigen. Dafür besteht aktuell kein belegter Bedarf,
solange der vorhandene Raw-Pfad ungeprüft ist. Keine Xbox-Elite-ID vortäuschen.

Priorität: allgemeines SDL-Gerätemapping → native Steam-Quellen nachweisen →
direkten erweiterten Proton-/Spielepfad prüfen. Ein langfristiger WGI-Ausbau
müsste Paddleinformationen durch HID, Provider, WGI und Spiellayout erhalten;
ein isolierter zusätzlicher Flagwert genügt nicht.

Falls ein Spiel ausschließlich Standard-XInput akzeptiert, wäre ein optionaler
allgemeiner Modus mit vier zusätzlichen Tastatursignalen denkbar, deren Aktionen
erst im Spiel zugewiesen werden. Auch dieser Modus wäre **keine native
Controllerbutton-Unterstützung**: Menüfilter, akzeptierte Tastencodes und
gleichzeitige Keyboard-/Gamepad-Eingaben bleiben Spielgrenzen. Deshalb wurden
keine globalen Tasten festgelegt oder ausgegeben. Eine globale uinput-Tastatur
mit nachträglicher Fokusabfrage reicht zudem nicht als Beweis gegen Desktop-
Eingaben: Prüfung und Einspeisung sind nicht atomar. KWin-/Portal-/Gamescope-
Fokus, Overlay, Disconnect und Freigabe gehaltener Tasten wären zuerst zu lösen.
Keine universelle Kompatibilität wird zugesichert.

## Offline-Werkzeug und nächster freizugebender Test

`tools/sdl/steam_mapping_audit.py` liest ausschließlich eine ausdrücklich
angegebene gespeicherte reguläre Logdatei. Es benutzt den vorhandenen
Mappinggenerator, prüft GUID/VID/PID sowie Standardtasten, Achsen und D-Pad
und erzeugt einen prüfbaren JSON-Vorschlag auf stdout. Fremde Logzeilen werden
nicht ausgegeben. Mehrere passende GUIDs benötigen eine explizite Auswahl;
abweichende Standardbelegungen führen zum Abbruch. Keine Geräte-/SDL-
Initialisierung, keine Konfigurationsänderung und kein Steamstart.

```sh
python -B tools/sdl/steam_mapping_audit.py --log-file GESPEICHERTES_CONTROLLER_LOG --guid 03004535373500009c10000053010000
```

Die konkrete Ausgabe und der allgemeine Gerätemapping-Kandidat liegen privat
unter `.local/integration/20261013T170841Z-steam-paddles/`. GUID/Fähigkeiten
müssen für einen realen Test frisch bestätigt werden; nicht blind übernehmen.

Die Prüfung des gespeicherten Steam-Logs wählte mit expliziter GUID Zeile 1859;
insgesamt sind zwei verschiedene passende GUIDs in der Historie vorhanden.
Der Vorschlag ergänzt `paddle2:b11`, `paddle1:b12`, `paddle4:b13`, `paddle3:b14`
und korrigiert den Mappingnamen. Alle Standardfelder sind identisch. Die
weiteren registrierten Codes 167/708 werden dabei nicht neu zugewiesen.
Es gibt keine Spielaktion, keinen Tastaturcode und keine neue Geräteidentität.

Historische Offline-Validierung vom 13. Oktober: `make test-alpha` bestand mit 141 Fällen, darunter 13
neue Logprüfer- und fünf bestehende Generatorfälle. `make test-sdl-buttons`
bestand damals in acht gerätefreien SDL3-/SDL2-Compat-Fällen mit 256 künstlichen
Buttonkanten. Diese Bibliotheksprobe verwendet System-SDL und synthetische
Geräte, weder Steams private Bibliothek noch ein echtes Proton-Spiel.
Keine Komponente der installierten Alpha wurde aktualisiert oder neu gebaut.

Der folgende ursprüngliche Testplan bleibt historisch. Für den neuen Auftrag
gilt die präzisierte [zweistufige Abnahme](STEAM_ELITE_PADDLES.md#offline-nachweis-und-praxistest-zur-gesonderten-freigabe),
einschließlich Capability-Prüfung und menschlicher Puffer. **Noch nicht freigegeben.**

1. Relevante Steam-Einstellungen sichern; laufendes Spiel regulär beenden und
   Steam nach Freigabe schließen. Alpha-Dienst und native Bindung weiterlaufen lassen.
2. Steam einmal mit dem dokumentierten SDL-Hinweis und genau dem geprüften
   Gerätemapping starten. Keine direkte Änderung von `config.vdf` und keine
   Geräteklassifizierung durch fremde VID/PID erzwingen. Eine Umgebungsvariable
   nur in Constances Startoptionen ändert den bereits laufenden Steam-Client nicht.
3. Steam-Log prüfen: Werden die Paddle-Felder tatsächlich verwendet oder durch
   einen Cache überschrieben? Danach mit 30 Sekunden Vorbereitung, zehn Sekunden
   Wechselpuffer und mindestens 20 Sekunden pro Taste die vier Steam-Quellen
   prüfen. Keine Aktionen auf Xbox-Tasten duplizieren.
4. Constance im sicheren Menü prüfen: vier getrennte direkte Bindungen, jede
   Taste einzeln drücken/loslassen, normale Buttons/Sticks/Trigger erhalten.
   Steam-Paddles allein nicht als erfolgreiche Spielabnahme melden.
5. Scheitert der direkte Spielpfad, Ergebnis festhalten. Raw-Proton-/Registry-
   Diagnose oder ein virtuelles Gerät benötigen eine weitere konkrete Freigabe;
   kein automatisches Umschalten oder Ersetzen von Bibliotheken.
6. Rücknahme des temporären SDL-Versuchs: Steam regulär schließen, danach ohne
   den temporären Hinweis starten. Gesicherte Einstellungen vergleichen;
   etwaige persistierte Änderungen nur gezielt nach Prüfung zurücknehmen.

Der dokumentierte SDL-Hinweis lautet `SDL_GAMECONTROLLERCONFIG` und muss den
Prozess vor dessen SDL-Initialisierung erreichen. Der Steam-Client kann eigene
Mappings höher priorisieren; die Übernahme ist zu prüfen, nicht anzunehmen.
[SDL-Hinweis](https://wiki.libsdl.org/SDL3/SDL_HINT_GAMECONTROLLERCONFIG).

Das Abnahmekriterium bleibt offen, bis ein Spiel die vier zusätzlichen Eingaben
wirklich im eigenen Belegungsmenü übernimmt. Ein erfolgreicher Offline-Test
oder eine umbenannte Steam-Anzeige ersetzt diesen Nachweis nicht.
