> Public export: personal tester, host and path references were anonymized. Historical evidence hashes refer to the private originals.

# Hardwaretest 003: eigenständiger Start ohne Deadband

13. Oktober 2026. Vorbereitung auf Modulbuild aus `0de9077`, SHA256
`d70e3687ce4c1d4eb6af6701490327343932cde381c0b2dab36e2f3fc94c8b51`.
Der folgende freigegebene Ablauf wurde am 13. Oktober erfolgreich durchgeführt.
Der Ergebnisabschnitt unten trennt Messung, Rückkehr und Nutzerbestätigung.

## Historischer Vorbereitungsstand

- Lesend bestätigt: Kernel 7.2.9-2-garuda, 3537:100a, Port 8-6, Adresse 11.
  Die zuvor beobachtete Adresse 6 wurde nach nutzerbestätigter Wiederverbindung
  verworfen. Erster Leseschritt stoppte vor dem Zugriffstest; keine Wiederholung
  ohne neue Freigabe. Frühere Resume-Warnungen und eine 0575-Enumeration stehen
  im privaten Ausgangslog; sie sind kein Ergebnis des neuen Treibertests.
- Root-Prozesscheck erfolgreich: kein Deadband, kein fremder usbfs-Handle,
  keine unlesbaren Prozesse. Normale xpad-Eingaben im KDE Center nutzerbestätigt.
- industrialio und anschließend gs_native einzeln freigegeben geladen.
  `bootstrap_mode=1 enable_output=1 session_ms=180000`; kein festes Testinterface.
  Externes/unsigniertes Modul: erwartete Taint-Hinweise, keine neue USB-Warnung.
- IF0 einzeln freigegeben von xpad gelöst; genau die bekannte einzelne
  xpad-Abbaumeldung -2. Anschließend separat freigegeben an gs_native gebunden:
  weiterhin 100a/11, IF1 usbhid, `OUT=0`, Input-Gerät vorhanden.

## Einmalig freigegebener und durchgeführter Lauf

`hardware_test_003.py` nutzt den vorhandenen Test-002-Backend für evdev,
Clientantworten, Status-/Identitätsprüfungen, Kernelmeldungen und END.
Er lädt keine Module und schreibt keine Sysfs-Bindungen. Er startet einmal:

```text
build/gsnative-ctl bootstrap /dev/gsnative-8-6:1.0 --handoff-xpad
```

Dieser Auftrag sendet die gespeicherte Übergangsfolge 100a→109c und native
Initialisierung. Das Flag erlaubt dem Kernel genau eine Übergabe des neu
zugeordneten 109c-IF0 von xpad an gs_native. Anderer Port, IF1 und fremde
Treiber werden dafür nicht abgebunden. Keine manuelle Deadband-Vorbereitung.

Nach bestätigtem Bootstrap, frischer IMU und geprüfter exklusiver 109c-Bindung
übernimmt `gsnative-ctl session ... 125` die bestehende endliche Runtime ohne
erneute Initialisierung. Davon werden 120 Sekunden gemessen; danach END.
Die Kernel-Sitzungsgrenze bleibt 180 Sekunden ab Bootstrap-Übergabe.

Vor Start: sichtbares Terminal, ausdrückliches `bereit` (beliebige Schreibweise),
15 Sekunden Countdown. Während Initialisierung ruhig halten, keine Guide-Taste.
Ansagen und Uhr beginnen am tatsächlichen Lauf, nicht an einer Chatnachricht.

| Messzeit | Tätigkeit |
|---|---|
| 0–15 s | Anfangsruhe |
| 15–30 s | Reaktionspuffer, aufnehmen |
| 30–65 s | Sticks, Trigger, Tasten und Steuerkreuz |
| 65–80 s | Reaktionspuffer für Bewegungsmessung |
| 80–100 s | Langsam um alle drei Achsen kippen/drehen |
| 100–110 s | Reaktionspuffer, ablegen |
| 110–120 s | Schlussruhe |

Gespeichert werden native evdev-Ereignisse, Input-Fähigkeiten, sechs rohe
IMU-Kanäle als abgefragte Snapshots, Status, Kernelmeldungen und Zeitmarken.
Keine Motorimpulse und kein neuer usbmon-Mitschnitt. Snapshots sind nicht der
vollständige IMU-Paketstrom und kein Nachweis physikalischer Gyro-Kalibrierung.
Originale bleiben privat unter `build/hardware-tests/`, mit SHA256.

## Abbruch und Rückweg

Abbruch bei geänderter Ausgangsidentität, fremdem Zugriff, neuen Kernelwarnungen,
fehlgeschlagenem Bootstrap/START, falscher 109c-Bindung, SYN_DROPPED, fehlenden
IMU-Snapshots, vorzeitigem Clientende oder sonstigem Laufzeitfehler.
Laufenden Bootstrap mit SIGTERM abbrechen, keinen zweiten Versuch starten.
Ein bereits gestarteter Sitzungsclient beendet über seinen bestehenden END-Pfad.
Ist Bootstrap erfolgreich, aber der folgende Guard schlägt noch vor Clientstart
fehl, werden keine weiteren Aktivierungsbefehle auf Verdacht gesendet: die bereits
laufende Runtime bleibt durch ihren 180-s-Watchdog begrenzt. Dies ausdrücklich
als Fehler und ausstehenden Rückweg melden. Ein hängender Bootstrap-Prozess
wird weder zwangsgetötet noch als vollständig gesicherter Lauf ausgegeben.

Nach END zuerst lesend beobachten. Die vorherigen Hardwareläufe belegen eine
Rückkehr zu 100a nach Ende der Wartung; dies ist für diesen Start noch kein
garantierter Rückschaltbefehl. Falls 100a/xpad wieder vorliegt: normale Eingaben
im KDE Center bestätigen lassen, gs_native separat freigegeben entladen.
Falls 100a noch nativ gebunden ist: Abbindung, Entladen und xpad-Rückbindung
einzeln freigeben. Bei verbleibendem 109c/fehlendem Gerät erst Zustand berichten
und einen konkreten Rückweg freigeben lassen. Keine Firmware-/Profiländerung,
kein Reset, automatischer Rebind, Deadband-Start oder Wiederholungsversuch.

## Zusatztasten: anschließende Prüfung

[tester] berichtet normale Eingaben, aber keine Zusatztasten in evtest. Lesend
bestätigt im aktuellen 100a-Zustand: event13 ist das native GameSir-Gerät,
Codes 704–707 fehlen tatsächlich im registrierten Key-Bitmap. Der Treiber
registriert sie nur für 109c und speist sie aus den Telemetriebytes 57/58.
Der Kernel-Bootstrap wurde zu diesem Zeitpunkt noch nicht ausgeführt.

Nach erfolgreichem Start die neuen Input-Fähigkeiten und Ereignisse mit
Hardwaretest 002 vergleichen. Die dortige Softwarezuordnung L4/R4/L5/R5
zu 704–707 ist belegt, ihre physische Einzelzuordnung weiterhin offen.
Ein beschrifteter Einzeltest wird separat geplant, ohne normale Xbox-Tasten
umzuwidmen. KDE/SDL/Steam/Embercade-Belegung ist ein nachfolgender eigener Schritt.

## Ergebnis vom 13. Oktober 2026

**Hardwaretest 003 ist im freigegebenen Umfang erfolgreich abgeschlossen.**
Modul aus `0de9077`, Testhelfer aus `4a603cd`; kein Deadband-Start und keine
Motorimpulse. Der Controller ist anschließend wieder im normalen xpad-Betrieb;
[tester] bestätigte normale Eingaben im KDE Center. Das ungebundene Testmodul
wurde gesondert freigegeben entladen. Damit ist die Voraussetzung für die
beauftragte ausschließlich offline entwickelte Plug-&-Play-Alpha erfüllt.

Zeiten in UTC (lokal Europe/Berlin an diesem Tag: UTC+2):

- Bootstrap-Aufruf 14:02:29,862174; erfolgreicher Abschluss 14:02:32,172006
  nach 2,310 s. `state=7 error=0 failed_stage=0`, `handover=1`.
- Nachgewiesener Übergang: 100a/Adresse 11 → 109c/Adresse 12, gleicher Port;
  IF0 exklusiv gs_native, IF1 ungebunden. Frische Gamepad-/IMU-Daten beim Start.
- Messung 14:02:32,225880 bis 14:04:32,234958, Dauer 120,009 s.
  Alle sieben Ruhe-/Puffer-/Eingabe-/Bewegungsphasen durchlaufen.
- END bestätigt; der Client bestätigt einen erfolgreichen Nullmotortransfer.
  Keine mechanische Motorprüfung in diesem Lauf.
- Nach der asynchronen Neuanmeldung: 100a/Adresse 13, IF0 xpad, IF1 usbhid.
  Dafür wurde kein zusätzlicher Umschalt- oder Rückbindebefehl ausgeführt.
- `gs_native` um 14:08:22 UTC separat entladen, Rückgabestatus 0, nur die
  erwartete Kernel-Info zur Abmeldung. industrialio bleibt geladen.

### Eingaben und Zusatztasten

22.337 Linux-Input-Ereignisse wurden gespeichert. Der letzte abgefragte
Treiberstatus enthält 5.711 Gamepad- und 7.498 IMU-Berichte. Diese Zahlen
bezeichnen verschiedene Ebenen; sie sind keine USB-Paketstatistik.

Beide Sticks erreichen auf allen vier Achsen −32768 bis 32767, beide Trigger
0 bis 1023, das Steuerkreuz auf beiden Achsen −1 bis 1. Am Anfang der
Schlussruhe und im abschließenden Snapshot: Sticks `[0, -1, 0, -1]`, Trigger
und Steuerkreuz null, keine gedrückten Tasten. Die Y-Werte −1 entsprechen der
vorhandenen Komplement-Abbildung von Rohwert null; dies ist keine Aussage
über langfristige Drift oder physikalische TMR-Kalibrierung.

Alle elf normalen Tastencodes und die vier geforderten Zusatztasten liefern
Drücken und Loslassen. Für die Zusatztasten wurden aufgezeichnet:

| Code | Drücken | Loslassen | Softwarezuordnung aus Deadband/Decoder |
|---|---:|---:|---|
| 704 | 9 | 9 | L4, Byte 57 / Bit 3 |
| 705 | 13 | 13 | R4, Byte 57 / Bit 4 |
| 706 | 17 | 17 | L5, Byte 58 / Bit 0 |
| 707 | 25 | 25 | R5, Byte 58 / Bit 1 |

Vor dem Bootstrap war das Gerät noch 100a, und diese vier Codes waren nicht
registriert. Nach dem Start in 109c sind sie registriert und liefern echte
Ereignisse. Der Kernel-Datenpfad für die vier Zusatztasten ist damit auch beim
Start ohne Deadband belegt. Der Ablauf enthält keine beschrifteten Zeitfenster
für jeweils genau eine physische Taste: Die Tabelle ist weiterhin die belegte
Softwarezuordnung, keine abschließende individuelle Beschriftungsprüfung.

Das 109c-Gerät registriert insgesamt 17 Tastencodes; 15 davon wurden betätigt.
Zusätzlich registrierte KEY_RECORD (167) und BTN_TRIGGER_HAPPY5 (708) wurden
hier nicht beobachtet. KDE-/SDL-/Steam-/Embercade-Belegbarkeit wurde nicht geprüft.

### IMU und Fehlerprüfung

451 zeitgestempelte IMU-Abfragen enthalten sechs veränderliche Rohkanäle:

| Rohkanal | Minimum | Maximum |
|---|---:|---:|
| Gyro X | −8302 | 4861 |
| Gyro Y | −2774 | 2012 |
| Gyro Z | −3321 | 3786 |
| Accel X | −8211 | 8723 |
| Accel Y | −8369 | 10657 |
| Accel Z | −9361 | 4386 |

Die Zählerdifferenz über die gespeicherten Abfragen ergibt im Mittel etwa
16,007 ms je IMU-Bericht. Das ist keine Verteilung tatsächlicher USB-Intervalle:
Hier wurden Snapshots abgefragt, kein vollständiger USB-Mitschnitt erstellt.
8192 LSB/g bleibt experimentell; Gyro-Empfindlichkeit und Achsenkalibrierung
bleiben offen. Keine Freigabe physikalisch kalibrierter SDL-Sensoren daraus ableiten.

Alle 13 im nativen Messfenster gespeicherten Kernelmeldungen sind Info-Meldungen;
keine Warnung, kein SYN_DROPPED, keine Clientfehler. Der letzte Status enthält
`rejected=7`; ohne Rohpakete lässt sich deren Typ in diesem Lauf nicht beweisen.
Die früher beobachteten unbekannten 0x03-Berichte sind eine mögliche Erklärung,
keine hier nachgewiesene Klassifikation. Nach END endet der Kernelmonitor;
für die gesamte anschließende Neuanmeldung liegt hier kein lückenloses Log vor.
Die spätere Zustandsprüfung und das protokollierte Entladen sind separat belegt.

### Belege und unveränderte Originaldaten

Private Originaldateien unter:

- `build/hardware-tests/003-native-startup-run-20261013T134727350519Z/`
- Vorprüfungen, Freigabeschritte und Entladen:
  `build/hardware-tests/003-native-startup-20261013T132831853891Z/`
- Abgeleitete Statistik: `build/results/hardware-test003-analysis.json`.

SHA256-Manifeste der Lauf- und Kontrollordner sind geprüft. Originaldaten
bleiben unverändert und außerhalb von Git. Das ursprüngliche `result.json`
enthält `xpad_restored=false`: Der Helfer führte selbst keinen Rebind aus,
und sein unmittelbar nach END erstellter Snapshot zeigt noch 109c. Dies wird
nicht nachträglich umgeschrieben; die separat gespeicherte spätere Kontrolle
belegt die Rückkehr zu 100a/xpad. Hardwaregeprüftes Modul und Client wurden
vor den nächsten Builds unter ihrem jeweiligen SHA256 in
`build/preserved-modules/` gesichert.

Die neuen Alpha-Funktionen, insbesondere Dauerbetrieb, allgemeiner Hotplug,
Suspend/Resume und Installation, werden ab jetzt ausschließlich offline
entwickelt. Dieser Test genehmigt keine weitere Hardware- oder Systemänderung.
