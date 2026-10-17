# Steam/Proton-Trigger-Bridge: Offline-Machbarkeit

Stand: 17. Oktober 2026. Ausschließlich lokale Dateien, gespeicherte
Referenzquellen und gerätefreie Tests untersucht. Kein Steam-/Proton-/Wine-
Start, Containerlauf, Netzwerk-, Geräte- oder Zugriff auf den laufenden Broker. Keine Änderung
an Steam, installierter Bridge, Dienst, Kerneltreiber oder Controller.

## Entscheidung

**Technisch begründeter Ansatz vorhanden; kein fertiger Steam-Adapter.**
Das installierte Proton Experimental enthält denselben SDL2-Triggeraufruf,
an dem die funktionierende Nexus-Bridge ansetzt. Das ist ein belastbarer
Ansatzpunkt für weitere Offline-Entwicklung, kein Nachweis von Spieleeffekten
unter Steam. Ein geeignetes Spiel steht derzeit nicht zur Abnahme bereit.

Der bestehende Adapter `steam-proton-sdl2` bleibt ausdrücklich **plan-only**.
Die Nexus-Validierung einfach freizuschalten oder ihren Startzusatz unverändert
als Steam-Lösung auszugeben wäre falsch. Kernel, Broker und bestehende
Paddle-Einbindung sollen erhalten bleiben. Der nächste Schritt ist ein eigener
Userspace-Adapter mit belegter Startposition, Runtime-/IPC-Prüfung und
synthetischem Abnahmeprogramm; noch keine Installation oder Aktivierung.

## Belegte lokale Ausgangsbasis

| Untersucht | Tatsächlich gefunden |
| --- | --- |
| Valve Proton Experimental | `experimental-11.0-20261014-x86_64`, Steam-Build `25936768` |
| Weitere installierte Starter | GE-Proton11-7, GE-Proton11-9; Proton-GE Latest mit bytegleichem GE11-9-Starter; CachyOS `cachyos-11.0-20261005-slr` |
| Tool-Manifeste | Version 2, `/proton %verb%`, `use_sessions=1`, Runtime-App `4183110` |
| Steam Linux Runtime 4 | `4.0.20260928.262390`, pressure-vessel `0.20260925.0` |
| Experimental Winebus | ELF64 und ELF32 mit SDL2-Bibliotheks-/Trigger-Symbolen |
| Vorhandene Bridge | ausschließlich glibc/x86_64, SDL2-`dlsym`, realer nativer Gerätepfad, Broker API 1 |
| Untersuchte Linux-Header | `FF_RUMBLE` vorhanden, `FF_TRIGGER_RUMBLE` weder in System-UAPI noch den Headern für `7.2.11-1-garuda` vorhanden |

Die disassemblierte ELF64-`winebus.so` löst den SDL2-Triggerzeiger über
`dlsym` auf und ruft ihn im Haptikpfad auf: Zuweisung bei `0x5f57`, indirekter
Triggeraufruf bei `0x4117`. Das belegt enthaltene Programmlogik, nicht deren
Ausführung durch ein bestimmtes Spiel. SDL3 im selben System ersetzt diesen
SDL2-Winebus-Aufruf nicht automatisch.

Gespeicherter Wine-Quelltext zeigt dazu getrennte Griff- und Triggerwerte in
`dlls/winebus.sys/bus_sdl.c:481–483`. Die genaue Quell-/Buildkorrespondenz zu
allen installierten Proton-Binärdateien ist nicht bewiesen; Quellbefund und
direkte Binärbeobachtung bleiben getrennte Belege.

## Welche Spielebefehle können ankommen?

| Eingangspfad | Offline-Befund und Grenze |
| --- | --- |
| Windows.Gaming.Input `GamepadVibration` | Gespeichertes `gamepad.c:250–263` übernimmt vier Werte; `provider.c:390–410` schreibt vier HID-Intensitäten. Ein passender Winebus-SDL2-Pfad kann die Trigger weiterreichen. Erreichbarkeit und gemeldete Fähigkeiten im konkreten Titel bleiben zu prüfen. |
| Klassisches `XInputSetState` | `XINPUT_VIBRATION` enthält nur zwei Motorwerte (`include/xinput.h:192–195`). Daraus lassen sich keine unabhängigen Trigger-Spieleffekte rekonstruieren. |
| Microsoft GameInput | Vier Felder allein genügen nicht: `SetRumbleState` ist im untersuchten Wine-Quellsnapshot ein Stub (`gameinput.c:148–151`). Das untersuchte Experimental-`gameinput.dll` bestätigt einen Debug-/Rückkehrpfad ohne Motorweiterleitung. Andere Spiel-DLLs oder spätere Builds können abweichen. |
| Steam Input API | Der lokal vorhandene SDK-165-Header deklariert `TriggerVibrationExtended` mit zwei Griff- und zwei Triggerwerten (`isteaminput.h:1169–1170`). Das ist ein eigener Steam-Ausgabepfad; eine Verbindung zu unserem Broker oder SDL2-Hook ist damit nicht belegt. |
| Natives SDL3 / direkte SDL-Aufrufe | Nicht vom bisherigen SDL2-`dlsym`-Hook abgedeckt. SDL3 hat andere Namen und Rückgabe-ABI. Keine automatische Kompatibilität behaupten. |

Keine Effekte aus Triggerposition, Beschleunigung oder Griff-Rumble erfinden.
Für Steam zunächst neutrales Profil LT 1x / RT 1x; Forzas RT-3x bleibt eine
ausdrückliche, getrennte Auswahl und wird nicht global übernommen.

## Konkrete Integrationsgrenzen

### 1. Proton-Aufruf und Spielende

Der Nexus-Launcher erwartet ein absolutes `wine`/`wine64` und bereits
gesetztes `WINEPREFIX`. Proton erhält dagegen seinen vollständigen Aufruf
von Steam und bildet `WINEPREFIX` aus `STEAM_COMPAT_DATA_PATH/pfx/`.
Der künftige Adapter muss die Argumentliste unverändert weiterreichen,
keine Shell-Zeichenkette zusammensetzen und keinen eigenen parallelen
Wine-Prozess auf denselben Prefix starten.

Im untersuchten Valve-Starter wartet `waitforexitandrun` auf einen bestehenden
Wineserver **vor** `run()`, nicht nach dem Spiel. Es ersetzt keinen
Nachlaufwächter. Auch `runinprefix` ist kein lesender Diagnoseaufruf:
Proton-Initialisierung und gegebenenfalls Fork-spezifische Fixups können davor
stattfinden. Diese Programme wurden hier nicht ausgeführt.

Ein künftiger Lifecycle-Vertrag muss tatsächlichen Winebus-/Produzenten-
Lebenszyklus, EOF/CLOSE, Signal/Abbruch und kurze Launcher-Hilfsprozesse
unterscheiden. Keine endlosen Neustarts oder automatische Wiederholung ohne
Hook/USB-Besitzschutz als vermeintlicher Rückfall.

### 2. Container, Pfade und Berechtigungen

Empfohlen: bestehendes Relay als normaler Benutzer auf dem Host, dort am
vorhandenen Broker. Im Container nur den passenden Hook und den privaten
Sitzungs-IPC-Pfad verfügbar machen. Weder Brokerverzeichnis noch vollständiges
`/run` oder zusätzliche USB-Geräte exportieren; keine Root-Spieleprozesse.

**Die Startposition ist noch zu belegen.** Eine beliebige Steam-Startoption
mit `%command%` garantiert keinen Hostprozess außerhalb des Containers.
Zuerst den tatsächlichen Startweg prüfen. Liegt ein bestätigter Host-Einstieg
vor, kann ein kleiner eigener Wrapper die bestehende Relay-Sitzung verwalten.
Liegt er innerhalb der Runtime, ist eine getrennt geprüfte Host-Anbindung
erforderlich; nicht stillschweigend auf eine Container-Relay-Kopie ausweichen.

Die vorhandenen Runtime-Dateien zeigen Export-/Preload-Mechanismen, beweisen
aber nicht die Sichtbarkeit unseres privaten `/run/user/<uid>`-Sockets oder
die tatsächliche UID-/GID-Abbildung. Gleiche effektive UID, restriktive
Verzeichnis-/Socketrechte und Zugriff ohne zusätzliche Passwortabfrage müssen
für die konkrete Sitzung nachgewiesen werden. Gruppenrechte nicht aufweiten.

### 3. PID-Namensraum und Quellenbindung

Der Hook schreibt `getpid()` in jedes Paket (`sdl2_hook.c:164`); das Hostrelay
vergleicht damit die Kernel-Peer-PID aus `SO_PEERCRED` (`relay.py:142,295`).
Bei getrennten PID-Namensräumen können diese Nummern voneinander abweichen.
Dann verweigert das aktuelle Protokoll schon den ersten Effekt korrekt.
Das installierte pressure-vessel enthält sowohl Share- als auch Unshare-
Optionen; die aktive Policy ist aus den untersuchten Dateien nicht belegt.

Den PID-Check nicht abschalten. Entweder gemeinsame PID-Sicht nachweisen oder
einen ausdrücklich geprüften, gegebenenfalls versionierten Mappingvertrag
auf Kernel-Peer-Metadaten aufbauen. Sessiontoken, UID, genaue Geräteinstanz,
SDL-Quelle, Sequenz, Frische und Stopbarrieren bleiben verpflichtend.

### 4. Steam Input und die vier Paddles

Der gesicherte Winebus-Code ignoriert Steam Inputs virtuelle Identität
`28de:11ff` im SDL-Pfad (`bus_sdl.c:939`); der zugehörige evdev-Pfad erzeugt
gewöhnliches Zweiwert-`FF_RUMBLE` (`bus_udev.c:1118–1121`). Dieser Weg kann
den SDL2-Triggerhook umgehen. Eine virtuelle Identität oder ein anderer
Eventpfad erfüllt zudem absichtlich nicht unsere native `3537:109c`-Prüfung.

Daher Steam Input nicht automatisch deaktivieren und keine Identitätsprüfung
lockern: Die vorhandenen unabhängigen Paddles müssen erhalten bleiben.
Eine belegte virtuelle-zu-physischer-Gerät-Zuordnung oder eine eigene
Steam-Ausgabeintegration wäre ein zusätzlicher Entwicklungsschritt. Ein
einziges angeschlossenes GameSir-Gerät ersetzt keine solche Zuordnung.

### 5. Preloads und ABI

Steam Runtime übernimmt `LD_PRELOAD`, entfernt es zunächst und übergibt es
über eigene `--ld-preloads`-/`--env-if-host`-Mechanismen. GE behandelt zusätzlich
`WINE_LD_PRELOAD`. Overlay, bestehende Vorladungen, Paddle-Mapping und andere
Controller dürfen weder überschrieben noch global verändert werden.
Der heutige Nexus-Adapter lehnt bestehendes `LD_PRELOAD` absichtlich ab;
für Steam braucht es eine gezielt geprüfte Komposition und Pfadabbildung.

Der aktuelle Hook benötigt nach statischer ELF-Prüfung nur `libc.so.6` mit
Symbolversionen bis GLIBC 2.34; die lokale steamrt4-libc definiert diese.
Das ist ein positiver ABI-Hinweis, kein erfolgreicher Ladetest. Für tatsächlich
geladene ELF32-Produzenten fehlt eigene Unterstützung: x86_64-Guard,
ELF64-Prüfung und `GLIBC_2.2.5`-Auflösung lassen sich nicht durch blindes `-m32`
erledigen. Die Windows-EXE-Bitness allein bestimmt bei WoW64 nicht zwingend die
benutzte Unix-Bibliotheksarchitektur; diese muss separat geprüft werden.

## Abnahme ohne vorhandenes Trigger-Spiel

Ein unterstütztes Spiel ist für die nächsten technischen Nachweise nicht
zwingend nötig. Sie bleiben von einer echten Spieleabnahme getrennt:

1. **Bereits gerätefrei bestanden:** 82 bestehende Bridge-Tests in sechs
   Teilprüfungen, einschließlich echtem ELF-Hook → Unix-Transport → Relay →
   Repository-Broker mit künstlichen Motoren. Keine installierte API, Steam,
   Wine, Runtime oder Hardware verwendet. Launcher-Fakes bestätigen unter
   anderem, dass Steam-Liveaufrufe weiterhin abgewiesen werden.
2. **Nächste Offline-Implementierung:** eigener geschlossener Steam-Planer,
   Argument-/Prefix-/Preload-Prüfung, Fake-Containerpfade, PID-Zuordnung,
   Quellenersatz, STOP/EOF/Abbruch und erhaltene Griffzustände testen.
   Den bestehenden Nexus-Pfad unverändert durch seine Regressionen prüfen.
3. **Später separat freizugeben:** ein eigenes kleines Windows-/SDL2-
   Diagnoseprogramm in der ausgewählten Proton-Runtime, zuerst ausschließlich
   gegen Fake-Relay/Fakebroker. Damit Startposition, ABI, Socketzugriff,
   Peer-PID und den realen APIpfad ohne Spiel und ohne Motorbefehle prüfen.
   Das startet Proton/Runtime und kann Prefix-/Steam-Dateien erzeugen; es ist
   ausdrücklich kein Bestandteil der heutigen rein lesenden Untersuchung.
4. **Erst danach gesonderter Hardwaretest:** begrenzte LT-/RT-Befehle,
   Nullpausen, Neustart, Prozessende und erhaltenes Griff-FF/Paddles prüfen.
   Ohne unterstützten Titel weiterhin keine pauschale Spielefreigabe.

## Quellen und Nachvollziehbarkeit

Lokale Primärquellen, ohne Nachladen oder Mitübernahme fremder Dateien:

- Installiertes Proton Experimental: `proton:633–635,1532,1761,2142–2172,2213–2217`
  und `toolmanifest.vdf:3–8`; GE11-9 `proton:2600–2613,2940`, CachyOS
  `proton:2572` für die getrennten Start-/Umgebungsbefunde.
- SteamLinuxRuntime_4: `VERSIONS.txt:2–6`, `run:13`,
  `_v2-entry-point:21–22,283–285`. Das Einstiegsskript bezeichnet seine
  Schnittstelle selbst als Prototyp; keine stabile öffentliche API versprechen.
- Gesicherter Wine-Snapshot `11.0-20261015-g132d7a88`, relevante Pfade unter
  `dlls/` und `include/` wie oben; keine exakte Binärzuordnung behauptet.
- Lokal vorhandener Steamworks-SDK-165-Header `isteaminput.h:1169–1170`;
  kein SDK-Code übernommen oder mit dem Projekt weiterverteilt.
- Bestehender [Bridge-Vertrag und Forza-Abnahme](TRIGGER_BRIDGE.md),
  [Broker API](HAPTICS_API.md) und [Paddle-/Spiel-API-Grenzen](STEAM_PROTON_BUTTONS.md).

Ausgewählte vollständige SHA256 der untersuchten Dateien:

| Datei | SHA256 |
| --- | --- |
| Experimental `proton` | `2304e055b98c0016b54273bfe67633a0fb122913fabcdd4857639b3835a23d75` |
| Experimental `x86_64-unix/winebus.so` | `620cc5e843220e118fc3b419d0e13e2978960402444cfe1a0b284ecfe7c12c85` |
| Experimental `i386-unix/winebus.so` | `2b88187881c8f645d883e7709d2440f76d0a55043e6fdab2e1361ba4be4995c8` |
| Gesichertes `winebus.sys/bus_sdl.c` | `d2e0a69c1ebdd9f49fb5d9c01ab878e0b26f4ab92121e02c741f344b25eb3be1` |
| Gesichertes `gameinput/gameinput.c` | `f679d8768d93ab479cb90cf4c0063e4cae0332493998091454842607c458ff13` |
| Experimental `gameinput.dll` | `4334eff7cb22d382b478fb8340b16011c26624a79536fd6a88f38fe744743f2e` |
| SDK-165 `isteaminput.h` | `4cc1887e02d829633385c07582279a5712fbcd5e1b046eade01efba376237093` |

**Go:** gezielte Offline-Entwicklung eines separaten Steam-/Proton-Adapters.
**Noch kein Go:** Installation, Steam-Startänderung, Live-Adapter, Hardwaretest
oder universelle Trigger-Unterstützung. Kein Push oder neuer Release aus
dieser Untersuchung; die Gyrokalibrierung bleibt pausiert.
