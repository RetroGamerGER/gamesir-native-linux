> Public export: personal tester, host and path references were anonymized. Historical evidence hashes refer to the private originals.

# Steam Input: vier Paddles unter der echten GameSir-Identität

Stand: 14. Oktober 2026. Statische Untersuchung, gerätefreie Tests und der
anschließend separat freigegebene reale Steam-Test; Ergebnis unten.
Die bisherigen Spieleläufe bleiben in [STEAM_PROTON_BUTTONS.md](STEAM_PROTON_BUTTONS.md).

**Fortsetzung nach Korrektur:** Der kritische FF-Speicherfehler ist korrigiert,
Revision 3 installiert und ein realer Funk-Reconnect bestanden; der native
Treiber bleibt aktiv. [Korrektur und Grenzen](FF_LIFETIME_FIX.md). [tester] hat
die dauerhafte Steam-Integration erneut beauftragt. Das separate optionale
[Steam-Paket](STEAM_INTEGRATION.md) ist offline geprüft und separat installiert.
Anschließend reale Ab-/Anmeldung und normaler KDE-Menüstart bestanden:
vier unabhängig funktionierende Paddles einschließlich Kombination/Loslassen,
normale Eingaben erhalten, vom Nutzer bestätigt. Frische Logs und neue
Prozessumgebungen belegen die automatische Übernahme. Kein neuer Ingame-Test.

Der erste Live-Anlauf wurde bei abweichender Bindung vor jeder Änderung
angehalten; danach [Rechnerstillstand und Diagnose](SYSTEM_FREEZE_20261014.md).
[tester] gab nach eigener GPU-Rückstellung die Fortsetzung ausdrücklich frei.
**Vier Paddle-Quellen und getrennte Steam-Belegungsplätze sind jetzt real
belegt. Die damalige Lücke im normalen Steam-Start ist inzwischen durch die
separat abgenommene KDE-Sitzungsintegration geschlossen.**
[Realer Versuch und Grenzen](#realtest-am-14-oktober-paddles-erkannt-persistenz-offen).

## Entscheidung und belastbarer Engpass

**Priorität A bleibt der richtige nächste Weg:** `3537:109c`, Gerätename
`GameSir G7 Pro`, vorhandene vier SDL-Paddle-Zuordnungen. Die untersuchte
Steam-Oberfläche besitzt vier Grip-Slots, deren Freigabe von Fähigkeiten
abhängt; für den vorliegenden Type 30 verlangt dieser Filter keine Elite-ID.
Dieser zunächst statische Befund wurde im unten dokumentierten Steam-Test bestätigt.

Der gespeicherte Zustand vor dem Live-Test hatte zwei belegte Lücken:

1. Steams tatsächlich protokolliertes SDL-Mapping enthält keine Paddlefelder.
2. Die vom Steam-Backend gemeldeten Fähigkeiten enthalten weder `GRIPS` noch
   `UPPERGRIPS`; daher scheitern die vier Slots am untersuchten UI-Filter.

Der unten dokumentierte Live-Test bestätigt, dass Steam diese Fähigkeiten
mit dem expliziten SDL-Mapping setzt. Der native Backendpfad ist nicht
vollständig als Quellcode verfügbar; die Persistenz bleibt offen.
Aus der UI allein keine vollständige Erkennungslogik oder allgemeine
Freischaltgarantie ableiten. Ein anderer Name behebt diese beiden Lücken nicht.

| Mögliche Fehlerstelle | Stand des Nachweises |
|---|---|
| Steam liest rohe Zusatzbuttons nicht | Im Live-Test widerlegt: vier Anzeigen, unabhängige Kombinationen und Loslassen nutzerbestätigt |
| Zuordnung zu Paddles fehlt | Vorher und nach normalem Neustart belegt; mit Start-Hinweis alle vier vorhanden |
| Zuordnung vorhanden, aber Standardlayout erzwungen | Mit Start-Hinweis vier Steam-Quellen und Belegungsplätze nachgewiesen |
| Steam schließt GameSir grundsätzlich aus | Nicht belegt; statischer Type-30-Filter erlaubt Grip-Slots bei passenden Fähigkeiten |

Erster Meilenstein **vier unabhängig bedienbare Quellen und getrennte
Steam-Belegungsplätze** ist im Live-Test erreicht. Zweiter, separater
Meilenstein ist direktes Belegen im Spiel. Der erste erfüllt den zweiten nicht.

## Elite als Referenz: Identität, Code und Fähigkeiten

Die zum gespeicherten Steam-SDL-Revisionsstring passende Quelle ist
`70e9cc86ddbe0f6b580c3c02d1391b3dde4d11fb`. Ihre Gerätetabelle klassifiziert
Microsoft `045e:02e3` (Elite 1) und `045e:0b00/0b05/0b22` (Elite 2/Varianten)
als Elite; `SDL_IsJoystickXboxOneElite()` verwendet diese Einordnung.
Öffentlich fasst SDL Xbox One und Elite als `XBOXONE` zusammen. Das erklärt
SDLs Referenzgeräte, beweist aber nicht Steams gesamte native Erkennungslogik.
[SDL-Tabelle](https://github.com/libsdl-org/SDL/blob/70e9cc86ddbe0f6b580c3c02d1391b3dde4d11fb/src/joystick/controller_list.h#L645),
[SDL-Klassifikation](https://github.com/libsdl-org/SDL/blob/70e9cc86ddbe0f6b580c3c02d1391b3dde4d11fb/src/joystick/SDL_joystick.c#L3375).

SDLs vier Paddle-Enums sind herstellerübergreifend. Ein explizites Mapping
verknüpft unsere echten Codes mit diesen Eingaben, ohne Elite vorzutäuschen:

| Physische Taste | Linux-Code | Rohbutton | SDL-Feld | SDL3-Eingabe |
|---|---:|---|---|---|
| L4 | 704 | b11 | paddle2 | LEFT_PADDLE1 |
| R4 | 705 | b12 | paddle1 | RIGHT_PADDLE1 |
| L5 | 706 | b13 | paddle4 | LEFT_PADDLE2 |
| R5 | 707 | b14 | paddle3 | RIGHT_PADDLE2 |

Die physische Zuordnung stammt aus dem korrigierten Hardwarebeleg. Die vier
Steam-Quellen sind im unten dokumentierten Realtest unabhängig bedienbar.
[SDL-Paddledefinitionen](https://wiki.libsdl.org/SDL3/SDL_GamepadButton).

Die gleiche SDL-Quelle erkennt im Linux-Automapping `BTN_GRIPL/GRIPR/GRIPL2/GRIPR2`
herstellerneutral. Nur der ältere Pfad für `BTN_TRIGGER_HAPPY5–8` ist an Microsoft
gebunden. Unsere `HAPPY1–4` lösen keine dieser Automatiken aus. In den installierten
Userspace- und Kernelheadern stehen die allgemeinen Grip-Codes bereits als
548–551. Das ist eine langfristige Standardisierungsoption, keine notwendige
Änderung für den jetzt vorbereiteten Versuch. Ein vorhandenes SDL-Mapping hat
Vorrang vor diesem Automapping. Einfach zusätzliche Aliascodes zu senden würde
außerdem doppelte rohe Eingaben erzeugen; eine Migration braucht einen eigenen
Kompatibilitätsplan für 704–707 und bestehende Anwendungen.
[SDL-Linuxbackend](https://github.com/libsdl-org/SDL/blob/70e9cc86ddbe0f6b580c3c02d1391b3dde4d11fb/src/joystick/linux/SDL_sysjoystick.c#L2739),
[Mappingvorrang](https://github.com/libsdl-org/SDL/blob/70e9cc86ddbe0f6b580c3c02d1391b3dde4d11fb/src/joystick/SDL_gamepad.c#L2389).

Der gepflegte **dlundqvist/xone-Fork**, Stand
`f2aa9fe01103d7600553b505b298ff0bd47ff280`, registriert und meldet vier Grip-Codes
für erkannte Elite-Geräte; alte Header erhalten einen HAPPY5–8-Fallback.
Fundstellen `driver/gamepad.c`: 34–40, 224–276, 370–373. Diesen Fork nicht mit
dem ursprünglichen medusalix/xone-Stand gleichsetzen. Kein xone-Code geladen.
[xone-Quelle](https://github.com/dlundqvist/xone/blob/f2aa9fe01103d7600553b505b298ff0bd47ff280/driver/gamepad.c#L224).

USB-ID identifiziert das Referenzmodell; SDL-GUID wählt ein Mapping und hängt
auch von Backend/Version/Name ab; Anzeigename ist kein Fähigkeitsnachweis.
Der dokumentierte `SDL_GAMECONTROLLERTYPE`-Hinweis bietet keinen Elite-Typ und
kann den HIDAPI-Protokollpfad beeinflussen. Er wird nicht als UI-Schalter benutzt.
Es wurde keine dokumentierte allgemeine Steam-Option gefunden, mit der Nutzer
beliebige Hardware durch Setzen einer Capability-Maske zu Elite machen können.
[SDL-Typhinweis](https://wiki.libsdl.org/SDL3/SDL_HINT_GAMECONTROLLERTYPE).

## Zunächst untersuchter Steam-UI-Code und reproduzierbare Diagnose

Untersuchte lokale Datei: `steamui/chunk~2dcc5aaf7.js`, SHA256
`f9606b111203c9140dcdd6fc016a0ee00e4c8406aeb786187c42873f08d071fb`.
Clientversion im korrelierten Log: `1788652215`. Die Datei wurde nur als Text
gelesen, weder ausgeführt noch verändert oder ins Repository kopiert.

Statische Fundstellen, nullbasierte Textpositionen in dieser Datei:

- Position 1936155: `ATTRIBCAP_GRIPS`, Bit 10 (`0x400`).
- Position 1936663: `ATTRIBCAP_UPPERGRIPS`, Bit 22 (`0x400000`).
- Ab Position 8614000: `LeftGrip` und `RightGrip` verlangen GRIPS;
  `LeftGrip_Upper` und `RightGrip_Upper` verlangen GRIPS und UPPERGRIPS.
- Modul 52192, exportierter Filter `BX` / Funktion `H`: alle benötigten
  Capability-Bits müssen vorhanden sein. Die Grip-Ausschlüsse 39/40 betreffen
  einzelne Joy-Con-Klassen, nicht den protokollierten Type 30.
- Die grafische Darstellung ab Position 8780000 verwendet dieselben Grip-
  Fähigkeiten. Konfiguration, Ereigniszustellung und Backend bleiben zusätzliche
  Bedingungen; eine erfüllte Maske ist keine vollständige UI-Abnahme.

Im gesicherten Lauf `20261014T131303Z-constance-live-002` korrelieren
`controller-before.txt:2273` und `controller-ui-before.txt:926` exakt mit
15:11:06 MESZ. Type 30, Produkt 4252 (=109c), Maske `00000000009843ff`:
beide Grip-Bits fehlen. Serienstrings werden nicht als echte UID interpretiert.

`tools/sdl/steam_paddle_audit.py` prüft genau diese Lücke aus gespeicherten
Dateien. Es akzeptiert nur reguläre, begrenzte Dateien; keine Geräte oder
Symlinks. Es verlangt den geprüften UI-Hash, die passende Clientversion,
GUID, Controllerindex und eindeutig übereinstimmende Logzeit. Bei einem anderen
Steam-Build muss dessen Bedeutung neu geprüft werden. Es führt kein JavaScript
aus, setzt keine privaten Flags und verändert keine Konfiguration.

Beispiel ab Projektwurzel, nur gespeicherte Daten/Code lesen:

```sh
python -B tools/sdl/steam_paddle_audit.py \
  --mapping-log .local/integration/20261014T131303Z-constance-live-002/controller-before.txt \
  --ui-log .local/integration/20261014T131303Z-constance-live-002/controller-ui-before.txt \
  --ui-bundle "$HOME/.local/share/Steam/steamui/chunk~2dcc5aaf7.js" \
  --guid 03004535373500009c10000053010000 --controller-index 0
```

Ergebnis: `mapping_and_ui_capability_gap`. Der Bericht trennt fehlendes Mapping,
fehlende Fähigkeiten und erfüllte Vorbedingungen; tatsächlichen Empfang,
Layouteditor und Spielebelegung meldet er ausdrücklich als nicht gemessen.
14 synthetische Regressionstests prüfen unter anderem Teilmasken, falsche
Zuordnung, doppelte/alte Datensätze, abweichende Versionen und Datenschutz.
Die private Bitbedeutung ist Diagnosewissen dieses Builds, keine neue UAPI.

## Offline-Nachweis und Praxistest zur gesonderten Freigabe

Der vorhandene SDL-Test wurde erweitert, keine neue Host-Eingabeschicht gebaut:
**10 bestandene Fälle, 944 künstliche Tastenkanten**. Zusätzlich zu sämtlichen
Einzeltasten: alle 32 Kombinationen aus A und vier Paddles, unabhängiges Loslassen,
unverändertes Halten ohne neue Kanten, 18 Achsen- und neun D-Pad-Zustände pro Fall.
Zwei Fälle verwenden genau die Form des Steam-Vorschlags: nur vier Paddles
ergänzt, vorhandenes `misc1:b16` erhalten, kein zusätzliches `misc2`.
System-SDL3 und SDL2-Compat, gerätefreie Bubblewrap-Sandbox; Steams private
SDL-Bibliothek und der Layouteditor wurden nicht ausgeführt.
[Testverfahren und Grenzen](SDL_EXTRA_BUTTONS.md).

Validierung: `make test` vollständig bestanden, darunter 14 neue Diagnose-
und 13 bestehende Mapping-Audittests. Der erste Paket-Staging-Test fand den
neuen README-Dokumentlink noch nicht im Dokumentpaket; die explizite
Dokumentliste wurde ergänzt, danach vollständige Regression erfolgreich.
`python -B tests/run_sdl_buttons_test.py` bestätigt die zehn oben genannten
Bibliotheksfälle. Ergebnisse unter `build/steam-elite-regression-final.log`,
`build/results/sdl-buttons/` und `build/results/steam-paddle-audit.json`.
Kein Kernel-/Manager-Runtimecode geändert, kein neues Paket installiert.

**Historischer vorbereiteter Ablauf.** Anschließend separat freigegeben;
tatsächliche Durchführung und Abweichungen siehe Realtest unten:

1. Spiel regulär schließen; aktuelle Steam-Version, native Instanz und GUID
   lesend bestätigen. Private Vorherkopien der relevanten Logs/Einstellungen
   sichern. Laufenden Alpha-Dienst und seine Bindung erhalten. Keine pauschalen
   früheren Freigaben übernehmen. Abweichende Instanz, Managerfehler oder neue
   UI-Version zuerst prüfen; keine Reparatur- oder Wiederholungsschleife.
2. Steam regulär vollständig schließen und nach Freigabe genau einmal mit dem
   bereits geprüften, nur für diesen Prozess gesetzten SDL-Hinweis starten.
   Ein bestehender Hinweis für andere Geräte muss erhalten bleiben; im zuletzt
   gelesenen Steam-Prozess war keiner gesetzt. Keine direkte Bearbeitung von
   `config.vdf`, keine falsche VID/PID, keine neue virtuelle Hardware.

   Konkreter vorbereiteter Aufruf ab Projektwurzel, **jetzt nicht ausgeführt**:

   ```sh
   SDL_GAMECONTROLLERCONFIG="$(cat .local/integration/20261014T131303Z-constance-live-002/gamesir-steam-mapping.txt)" /usr/bin/steam
   ```

   Vorher Inhalt/aktuelle GUID erneut mit dem vorhandenen Mapping-Audit prüfen.
   Der Hinweis ist eine dokumentierte SDL-Schnittstelle, keine Garantie gegen
   Steams eigene spätere Mappingpriorität. Falls das tatsächliche frische Log
   die vier Felder nicht übernimmt: stoppen und Cache-/Prioritätspfad benennen.
   Keine ungefragte Änderung gespeicherter Steam-Dateien.
3. Frische Mapping- und UI-Logs auswerten. Wenn das Mapping stimmt, aber die
   beiden Grip-Fähigkeiten weiter fehlen, ist der nächste Engpass ausdrücklich
   Steam-Backend/Klassifikation. Dann nicht erneut am Kerneldecoder arbeiten
   und keine Masken patchen. Sind beide vorhanden, den Layouteditor ansehen;
   nur das Ansehen erteilt keine Freigabe zum Speichern neuer Spielaktionen.
4. Menschlicher Tastenablauf: 30 s Vorbereitung; je Taste L4, R4, L5, R5
   20 s zum mehrfachen Drücken/Loslassen und 10 s Wechselpuffer. Danach 30 s
   für L4+R4, L5+R5 und A+L4; immer einzeln loslassen und Restzustand prüfen.
   30 s für normale Tasten, Sticks, Trigger und D-Pad. Bei Bedarf auf [tester]
   warten statt das Fenster als Fehlversuch zu zählen. Namen der vier
   erkannten Quellen, sichtbare Reaktionen und Loslassen getrennt festhalten.
5. Erst wenn vier Plätze sichtbar und unabhängig nutzbar sind, Meilenstein 1
   bestätigen. Für Meilenstein 2 Constance separat starten und im eigenen
   Belegungsdialog prüfen. Ein Steam-Layout, das Paddles auf bestehende Xbox-
   Tasten legt, ist kein Nachweis zusätzlicher Spielbuttons. Bei unverändertem
   XInput-Layout das negative Ergebnis festhalten, keine universelle Zusage.
6. Rücknahme: Steam regulär schließen und ohne temporären Hinweis starten.
   Vorher-/Nachherkonfiguration vergleichen: Steam könnte Mappings speichern;
   bloßes Entfernen der Umgebungsvariable beweist keine vollständige Rücknahme.
   Persistierte Änderungen nur gezielt und freigegeben zurücknehmen.
   Treiber bleibt zuständig; kein END, release oder xpad-Rückwechsel für diesen
   Userspace-Test. Bei echtem Treiberfehler stoppen und gesonderten Rückweg klären.

[Dokumentierter SDL-Hinweis](https://wiki.libsdl.org/SDL3/SDL_HINT_GAMECONTROLLERCONFIG).
Das Ziel ist die tatsächliche Editor-Abnahme, nicht die bloße Existenz einer
weiteren Mappingdatei. Den späteren Nachweis und seine Grenzen beschreibt der Realtest unten.

## Gewünschter Anzeigename: GameSir G7 Pro

[tester] möchte zusätzlich die echte GameSir-Bezeichnung in Steam sehen.
Linux und Steams SDL-Mapping enthielten bereits `GameSir G7 Pro`;
vor der UI-Umbenennung zeigte die Oberfläche dennoch eine generische
Xbox-Bezeichnung. Der kontrollierte Wechsel über das Namensfeld ist unten belegt.

Die installierte Oberfläche hat einen regulären, editierbaren **Controllername**:
in derselben geprüften JS-Datei, Modul 69748, wird das Feld `He` in den Details
des ausgewählten Controllers eingeblendet (Textposition ca. 12450706), ohne
Elite-Bedingung. Es liest `strName` und ruft beim Bestätigen den vorgesehenen
Clientpfad `SetControllerName` auf (ca. 12462204). Die Controllerliste und der
Detailtitel verwenden `strName` (ca. 12449800 / 12450684). Die deutsche
Lokalisierung nennt das Feld `Controllername`.

Damit war ein vorhandener UI-Weg zum echten Namen **statisch belegt**;
der spätere Realtest bestätigt seine Nutzung. Der vorbereitete Weg: Steam-Einstellungen
→ Controller → Details des GameSir → Controllername `GameSir G7 Pro` eintragen,
Anzeige in Liste und Layouteditor prüfen und nach regulärem Steam-Neustart
erneut prüfen. Den vorigen Namen vorher festhalten. Exakte UI-Erreichbarkeit,
Speicherung über Wiederverbindung und sämtliche anderen Steam-Ansichten sind
noch offen; keine Firmware-/Kernelumbenennung nötig. Keine direkten Aufrufe
privater Steam-APIs, keine Bearbeitung proprietärer Dateien.

Die Namensänderung ist eine separate Steam-Einstellung und braucht die
gesonderte Freigabe des Praxistests. Sie aktiviert keine Paddle-Fähigkeiten
und erweitert keinen XInput-Spielpfad. Der Controller bleibt ein echter
GameSir unter `3537:109c`.

## Realtest am 14. Oktober: Paddles erkannt, Persistenz offen

[tester] gab die Fortsetzung nach der eigenen GPU-Rückstellung ausdrücklich
frei. Die installierte Alpha `0.1.0.alpha2-2` blieb unverändert; der einmalig
freigegebene Managerstatus war aktiv, unpausiert und ohne Konflikt. Vor und
nach den Steam-Schritten blieb dieselbe native `3537:109c`-Instanz gebunden.
Keine Geräteöffnung, kein Motorbefehl, kein Dienst-/Modul-/Bindungswechsel
und kein neuer Spielelauf durch den Testhelfer.

Steam aktualisierte sich beim Nutzerstart selbst auf Client `1791918634`.
Die vier Grip-Gates wurden vor der Fortsetzung erneut statisch geprüft:
`steamui/sp.js`, SHA256
`5a28c25041d07e69cf591a414519e0cf970b6884c1a0106659dcd9f1fb9586f9`.
GRIPS/UPPERGRIPS stehen bei Textpositionen 2076416/2076924, die vier
Slotdefinitionen bei 10057455–10058152 und der gemeinsame Filter bei 10263496.
Der Audithelfer akzeptiert ausschließlich die zwei geprüften Hash-/Clientpaare;
kein allgemeines Aufweichen der Versionsprüfung. Bytegenauen Text lesen:
Normalisierung von CRLF vor dem Hash verändert den Fingerabdruck.

### Beobachteter Ablauf

| Schritt am 14. Oktober (UTC) | Ergebnis |
|---|---|
| Normaler Steam-Start, 13:52 | Standardmapping ohne vier Paddlefelder |
| Freigegebener Start mit einmaligem SDL-Hinweis, 13:55:05 | Alle vier Paddlefelder im frischen Log, danach beide Grip-Fähigkeiten vorhanden |
| Manueller Gerätetest | [tester] bestätigt vier getrennte Eingaben, Kombinationen, Loslassen und erhaltene Standardtasten/Achsen/Trigger |
| Reguläres Controllername-Feld | Screenshot zeigt `Gamesir G7 Pro`; USB-Identität und Kernelname unverändert |
| Steam-Layout für Dark Souls III | Vier getrennte Quellen sichtbar; Nutzerzuordnung L4→Y, R4→B, L5→X, R5→A |
| Separat freigegebener Normalstart ohne Hinweis, 14:04:52 | Wieder Standardmapping ohne Paddles; [tester] bestätigt „Keine Paddels“ |
| Regulärer UI-Import der geprüften vollständigen Zeile | Laut [tester] importiert, aber weiterhin keine Paddle-Anzeigen |
| Zusätzlich ausdrücklich gewünschter Normalstart, 14:17:01 | Wieder Standardmapping ohne Paddles; [tester] bestätigt erneut fehlende Paddles |

Das aktuelle SDL-Mapping betrifft ausschließlich die native GUID
`03004535373500009c10000053010000`. Es ergänzt `paddle1:b12`, `paddle2:b11`,
`paddle3:b14`, `paddle4:b13`; alle vorhandenen Standardfelder einschließlich
`misc1:b16` bleiben erhalten. Steam ergänzt `crc:3545`. Der Mappingprüfer
erhält diese Metadaten nur bei vier Hexzeichen und Übereinstimmung mit dem
Little-Endian-Wort der GUID-Bytes 2–3; unbekannte Felder, doppelte Schlüssel
oder geänderte Standardachsen bleiben Fehler. Diese CRC ist keine individuelle
Geräteseriennummer. [SDL-Implementierung](https://github.com/libsdl-org/SDL/blob/829a65d769d935c4852f8159e964312c0957260a/src/joystick/SDL_gamepad.c#L2005).

Im erfolgreichen Start enthält das Mappinglog um 15:55:06 MESZ alle Paddles.
Die erste Attributzeile derselben Sekunde trägt jedoch einen Platzhalter;
der richtige Gerätefamilieneintrag folgt um 15:55:07 mit `0xd847ff`.
Der strenge Audit verweigert deshalb den kombinierten Einsekunden-Nachweis.
Einzelne Logbelege und die Nutzer-/Bildschirmbestätigung werden separat
ausgewiesen, nicht als vollständiger CLI-Auditpass. Beim ersten Normalstart
korrelieren die negativen Belege exakt um 16:04:56: `0x9843ff`, beide Grip-Bits
fehlen. Nach dem UI-Import liegen Mapping und Familienattribut erneut eine
Sekunde auseinander (16:17:04/05); die strenge Korrelation bleibt unverändert.

### Bedeutung und verbleibende Lücke

Der reale Nachweis gilt für **unabhängige Steam-Input-Quellen und Belegungsplätze**.
Der Screenshot mit Spielaktionen stammt aus **Dark Souls III**, nicht aus
Constance. Keine zusätzliche direkte Constance-Belegung getestet; bestehende
XInput-Ausgabe bleibt auf ihre normalen Felder beschränkt. Der Name ist eine
reguläre Steam-Anzeigeeinstellung, kein Fähigkeits- oder Persistenzbeweis.
Die UI-Schnellansicht blendet Grip-Zeilen bei vorhandenen aktiven Belegungen
ein; der Nutzer aktivierte „Erweiterte Tasten aktivieren“ selbst. Diese Aktion
kann Standardaktionen kopieren und darf nicht blind für andere Spiele erfolgen.

Vor dem ersten Normalstart enthielt Steams gespeicherte Zuordnung die native
GUID mit vier Paddles und zusätzlich eine ältere generische GameSir-GUID ohne
Paddles. Nach dem Start waren die Paddlefelder auch im spezifischen Eintrag
verschwunden. Eine bloße SDL-Reihenfolgeursache ist nicht belegt: gerätefreie
In-Memory-Importe in Original-/Umkehrreihenfolge mit System-SDL3 und SDL2-compat
behielten jeweils die Paddles. Kein `SDL_Init`, keine Hostgeräte. Steam-interne
Normalisierung oder Cachepriorität bleibt eine Hypothese.

Der reguläre UI-Pfad wurde statisch in `sp.js` bei 14382787–14383900 geprüft:
„In Zwischenablage kopieren“ exportiert einen Mappingstring; „Geräteeingaben
einrichten“ → „Aus der Zwischenablage kopieren“ reicht den Clipboardtext an
den vorgesehenen Backendsetter weiter. [tester] lieferte den regulären Export;
er entspricht der vollständigen SDL-Zeile mit `crc:3545`, ohne Paddles. Der
vorbereitete Import ergänzte ausschließlich die vier Felder. Ob der proprietäre
Setter sie verwirft oder später überschreibt, ist nicht durch den UI-Code
erklärbar. **Import und anschließender Normalstart lösten die Lücke nicht.**
Keine direkte Bearbeitung von `config.vdf`, kein Patch von Steam-Dateien,
keine fremde VID/PID und kein virtuelles Elite-Gerät.

Der zunächst vorbereitete lokale Steam-Starter allein reicht für alle
gewünschten Startwege nicht. Die anschließend beauftragte dauerhafte Lösung
ist die getrennte optionale [Sitzungsintegration](STEAM_INTEGRATION.md):
Plasma übernimmt das bestätigte Mapping bei der Anmeldung; Menü, Desktop und
regulärer Autostart erben es. Separate Gamescope-Sitzungen benötigen explizite
Einbindung. Bestehende Nutzerbelegungen und der Anzeigename bleiben erhalten;
Installation und reale Start-/Persistenzprüfung separat freigeben.

### Belege und Regression

Private Konfigurationskopien, Logs, Nutzerangaben, Bildschirmbelege und die
vorbereitete Importzeile liegen unter
`.local/integration/20261014T135234Z-steam-paddles-live-004/`.
Sie sind nicht versioniert; keine vollständige Steam-Konfiguration veröffentlichen.
Im lesend erfassten Kernelzeitfenster bis 14:18:45 UTC fanden sich keine neuen
kritischen Speicherfehler/Lockups; Geräteinstanz und native Bindung blieben
gleich. Das ist ein begrenzter Kurzzeitbefund, **kein Langzeitstabilitätsnachweis
und keine bewiesene Ursache des vorherigen Absturzes**.

`make test` bestand vollständig (`build/steam-live-004-regression.log`),
einschließlich 18 Paddle-Audit-, 17 Mapping-Audit- und fünf Mappingtests.
Die neuen Fälle prüfen Hash-/Versionskreuzungen, CRC-Erhalt und Fehlformate,
unbekannte Felder sowie weiterhin gesperrte Änderungen normaler Eingaben.
Kernel-/Manager-Runtime und installierte Pakete wurden nicht verändert.

## Priorität B: virtuelle Elite-Schicht vorerst nicht implementieren

Eine uinput-Kopie könnte Standardtasten und Grip-Fähigkeiten bereitstellen;
eine UHID-Emulation könnte komplexere HID-Berichte anbieten. Die Kopie allein
beweist aber weder Steams Elite-Klassifizierung noch zusätzliche Spielbuttons.
Eine virtuelle Microsoft-ID könnte weitere modellabhängige Protokollannahmen
aktivieren. Eine bloße Namenstäuschung ist wirkungslos als Fähigkeitsnachweis.

Vor einer Implementierung müssten ein belegtes Scheitern von Priorität A und
ein funktionierender Ersatzpfad vorliegen. Erforderlich wären genau ein für
Spiele sichtbares Gamepad, vollständige Achsen/Tasten, ausschließlich native
USB-Verwaltung, FF-Rückleitung über die vorhandene API, Neutralisierung bei
Prozessende/Disconnect und zuverlässige Wiederverbindung. `EVIOCGRAB` allein
entfernt das Original nicht aus der Geräteauflistung. Dieser Wartungsaufwand
ist derzeit nicht durch einen belegten Nutzen gerechtfertigt. Keine uinput-
oder UHID-Geräte erzeugt, keine Deskriptoren verändert.
[uinput](https://docs.kernel.org/input/uinput.html), [UHID](https://docs.kernel.org/hid/uhid.html).

## Steam, Windows-APIs und andere Launcher

Steam-Quellen können unabhängig konfigurierbar sein, während seine
Standard-XInput-Ausgabe weiterhin nur normale Xbox-Tasten enthält. Klassisches
XInput hat keine vier zusätzlichen Paddlefelder. DirectInput `DIJOYSTATE2`
kann dagegen 128 Buttons enthalten; das Spiel muss sie auswerten und zur
Belegung anbieten. [XInput](https://learn.microsoft.com/en-us/windows/win32/api/xinput/ns-xinput-xinput_gamepad),
[DirectInput](https://learn.microsoft.com/en-us/previous-versions/windows/desktop/ee416628(v=vs.85)).

Neu präzisiert: **GameInput v3 definiert vier Paddleflags** und `LayoutElite`.
Microsofts Runtime-Changelog nennt die Erweiterung unter 3.3. Das ist ein
API-Potenzial, keine Bestätigung für GameSir, Proton oder Constance.
Quelle `dce6dabd75b53fcb29db86afe4de5c917921af18`, Header Zeilen 202–205.
[GameInput-Header](https://github.com/microsoftconnect/GameInput/blob/dce6dabd75b53fcb29db86afe4de5c917921af18/include/GameInput.h),
[Runtime-Versionen](https://github.com/microsoftconnect/GameInput/blob/dce6dabd75b53fcb29db86afe4de5c917921af18/README.md).

Aktueller untersuchter Proton-Wine-Quellstand
`7fc704ef49c50e9702c9983a5250d5738697bb04` bestätigt weiterhin Lücken:
SDL-GameController-Ereignisse übernehmen keine Paddle-Enums; WGI Gamepad setzt
keine Paddleflags; Builtin-GameInput `GetCurrentReading` liefert `E_NOTIMPL`.
Das betrifft den untersuchten Quellstand, nicht automatisch den installierten
Runner oder Microsofts native GameInput-DLLs.
[WineBus](https://github.com/ValveSoftware/wine/blob/7fc704ef49c50e9702c9983a5250d5738697bb04/dlls/winebus.sys/bus_sdl.c#L870),
[WGI](https://github.com/ValveSoftware/wine/blob/7fc704ef49c50e9702c9983a5250d5738697bb04/dlls/windows.gaming.input/gamepad.c#L266),
[GameInput-Builtin](https://github.com/ValveSoftware/wine/blob/7fc704ef49c50e9702c9983a5250d5738697bb04/dlls/gameinput/gameinput.c#L446).

Der Raw-Kandidat `Map Controllers=0` erhält mehr rohe Buttonindizes, garantiert
aber keinen anderen Constance-Gerätetyp: auch dort setzt WineBus bei sechs
Achsen und mindestens 14 Buttons `is_gamepad`; `main.c` ergänzt daraufhin
`WINE_COMP_XINPUT`. Das trifft unser Alpha17-Profil. Eine gleiche virtuelle
Kopie würde diese Grenze ebenfalls nicht beheben.
[Raw-Klassifikation](https://github.com/ValveSoftware/wine/blob/7fc704ef49c50e9702c9983a5250d5738697bb04/dlls/winebus.sys/bus_sdl.c#L1006),
[Kompatibilitätskennungen](https://github.com/ValveSoftware/wine/blob/7fc704ef49c50e9702c9983a5250d5738697bb04/dlls/winebus.sys/main.c#L267).

Für Lutris, Faugus und andere Runner ist deshalb ein allgemeiner SDL-/WineBus-
oder HID-Pfad nötig, keine Steam-exklusive Einstellung. Faugus verwendet UMU,
das Proton außerhalb Steams starten kann. Spätere Abnahme mit genauem Runner
und eigenem lesendem API-Test: rohe Buttonzahl/Indizes, DirectInput, WGI und
vorhandenes GameInput getrennt prüfen, danach das tatsächliche Spielemenü.
Keine Launcher-/DLL-/Registryänderung vorgenommen. Embercade bleibt unangetastet.
[Lutris](https://github.com/lutris/lutris), [Faugus](https://github.com/Faugus/faugus-launcher),
[UMU](https://github.com/Open-Wine-Components/umu-launcher).
