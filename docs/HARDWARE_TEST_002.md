> Public export: personal tester, host and path references were anonymized. Historical evidence hashes refer to the private originals.

# Hardwaretest 002 — 109c, Plan zur Freigabe

Stand: 12. Oktober 2026. **Vorbereitet, nicht ausgeführt und nicht freigegeben.**
Dieser Satz beschreibt den ursprünglichen Planstand. Die inzwischen einzeln
freigegebenen Schritte und der aktuelle Laufstatus stehen im
[Verlauf](HARDWARE_TEST_002_PROGRESS.md); der E2E-Test ist noch nicht abgeschlossen.
Dieser Plan ersetzt für Test 002 den früheren 25-s-Entwurf. Test 001 und seine
Originaldaten bleiben unverändert. Keine Hardware wurde bei dieser Vorbereitung
geöffnet; keine Module aktiviert, Treiberbindungen geändert oder USB-Befehle gesendet.
Die anschließende Offline-Prüfung und der lesende Vorabcheck sind im
[Prüfbericht](HARDWARE_TEST_002_OFFLINE_CHECK.md) dokumentiert. Sie erteilen
keine Freigabe zur Ausführung.

## Ziel und Umfang

G7 Pro am 2,4-GHz-Dongle: native Gamepad-Eingaben, zeitgleich sechs IMU-Rohachsen
und vier getrennte Motorimpulse unter `3537:109c`, ausschließlich Interface 0.
Gamepad und IMU werden auch während der Motorphase weiter beobachtet. Es ist
ein erster nativer Funktionstest, kein Hotplug-/Stresstest und keine erneute
allgemeine Deadband-Machbarkeitsprüfung. Vier Motoren gleichzeitig anzusteuern
ist nicht Teil dieses Laufs.

Beschleunigung bleibt experimentell 8192 LSB/g; Gyro bleibt signed-Rohwert.
Keine abschließende Achsenkalibrierung, Gyro-SI-Ausgabe oder SDL-Freigabe.
Keine Profil-, Polling-, Firmware- oder Systeminstallation; vorhandene
Geräteeinstellungen werden nicht gespeichert oder verändert.

## Bereits belegt und noch offen

- Test 001 validierte den 100a-Gamepadpfad und die Rückgabe an xpad. Der 109c-Pfad
  und native Motorwirkungen sind weiterhin ungetestet.
- Sprint 002 enthält die Identitätsfolge 100a/Adresse 38 → 109c/39 → 100a/40
  am Port 8-6. Nach der Aufforderung „Release to games“/Schließen bei +233,03 s
  war bei +240,41 s zunächst 109c an xpad sichtbar; bei +243,51 s wieder
  100a mit IF0 xpad und IF1 usbhid. Dies sind Beobachtungszeitpunkte, keine
  garantierte Firmware-Frist und kein Nachweis eines bestimmten Rückschaltpakets.
- **109c hat im gespeicherten Lauf IF0 ff/47/d0, Interrupt-IN 82 und OUT 02
  mit je 64 Byte; IF1 ff/47/d0 ohne Endpunkte und ohne Treiber.** usbhid an IF1
  ist hier ausdrücklich keine Voraussetzung. 100a hat eine andere IF1-Konfiguration.
- Deadband `reader.py:661–732` sendet für 100a den bekannten Übergangshandshake.
  `reader.py:735–839` hält die 109c-Sitzung mit Heartbeats. Beim Freigeben schließt
  `usb_transport.py:332–355` das Interface und versucht den zuvor abgelösten
  Kerneltreiber wieder anzuhängen. Dort steht kein eigener 109c→100a-Befehl.
- Der native Treiber sendet bei Bindung nur IN-Anforderungen. Erst START sendet
  drei belegte GIP-Initialisierungen und Heartbeats, danach Wartung alle 450 ms;
  Guide-Ack ist bedingt vorbereitet. END beendet die Wartung und versucht ein
  Null-Motorpaket. Er enthält keinen Identitätshandshake oder Rückschaltbefehl.
- **Offen:** Ob die native Übergabe rechtzeitig gelingt und END/Heartbeat-Ende
  dieselbe Rückkehr bewirkt. Keine Garantie aus dem Deadband-Lauf ableiten.
- Der freigegebene Versuch um 15:51 UTC scheiterte vor der nativen Übergabe:
  Nach Freigabe durch Deadband folgte auf die xpad-Registrierung unter 109c nach
  1,306 s ein Disconnect. Der Helfer wartete noch auf das vollständige Prozessende.
  Deshalb künftig **nur das Deadband-Fenster regulär schließen**, nicht zuvor
  „Release to games“ anklicken. Der Shutdown-Hook `deadband.py:78` ruft
  `reader.py:45–55` auf und schließt den USB-Zugriff bereits synchron.
  Das entfernt die zweite menschliche Aktion, garantiert aber keine Frist.
  Prozess-/Handle-Prüfungen bleiben unverändert. [Verlauf](HARDWARE_TEST_002_PROGRESS.md).

Quellen: vorhandener Deadband-Stand `771b28a`, `docs/PROTOCOL.md`, private
Sprint-002-Dateien `events.jsonl`, `identity-after.json`,
`derived/device-epochs.json`. Original-Capture-SHA256:
`4045577a7a9e7a1a0f84307a45e96fd524cd7dea1d4af276ebd7db20a0994a89`.
Native Fundstellen: `kernel/gs_native_usb.c` (`gsn_probe`, `gsn_start`,
`gsn_stop`, `gsn_service`, `gsn_quiesce`) und `src/gs_runtime.c`.

## Dauer und menschliche Reaktionszeit

Vor START: lokales sichtbares Fenster/Terminal, ausdrückliches „Bereit“, dann
15 s Countdown. Der Countdown darf vor der zeitkritischen Freigabe von Deadband
liegen; er darf die Übergabe nach dem Freigeben nicht verzögern. Keine Uhr startet
bereits mit einer Chatnachricht. T0 wird beim tatsächlichen START-Aufruf markiert.
Nach START gelten 120 s; die ersten 5 s enthalten Initialisierung/Datenprüfung.

| Zeit ab T0 | Phase | Aktion des Nutzers |
|---|---|---|
| 0–5 s | Initialisierung und Datenprüfung | Ruhig halten; bei Fehler kein weiterer Test |
| 5–20 s | 15 s Anfangsruhe | Flach ablegen, nichts berühren |
| 20–30 s | 10 s Übergangspuffer | Aufnehmen und auf das Eingabesignal warten |
| 30–60 s | 30 s Gamepad | Beide Sticks, Trigger, D-Pad und Tasten betätigen |
| 60–70 s | 10 s Puffer | Eingaben beenden, für Bewegungen bereithalten |
| 70–85 s | 15 s IMU | Langsam kippen/drehen; ab jetzt einen Stick leicht durchgehend im Kreis bewegen |
| 85–90 s | 5 s Puffer | Bequem halten; Stick weiter bewegen |
| 90–95 s | Linker Griff | Ein Impuls bei +91 s; Stick weiter bewegen |
| 95–100 s | Rechter Griff | Ein Impuls bei +96 s; Stick weiter bewegen |
| 100–105 s | Linker Trigger | Ein Impuls bei +101 s; Stick weiter bewegen |
| 105–110 s | Rechter Trigger | Ein Impuls bei +106 s; Stick weiter bewegen |
| 110–120 s | 10 s Schlussruhe | Ablegen, nichts betätigen |

Jeder Motor: 100 %, Anforderung 400 ms, alle anderen Motoren null. Mindestens
4,6 s Abstand zum nächsten Impuls; keine Wiederholung. Die Gesamtanforderung
beträgt vier Impulse/1,6 s, nicht 120 s Motorlauf. Während der Motorphase sind
fortlaufende kleine Stickbewegungen eine Testvoraussetzung. Dies wird bereits
vor `bereit` erklärt, ab der IMU-Phase angefordert und in jedem Motorfenster
wiederholt. 20 Sekunden Vorlauf bis zum ersten Motorfenster; kein Reaktionsrennen
beim ersten Impuls. In echter Ruhe können Gamepadberichte ausbleiben, wie der
90-s-Lauf belegt. Der Helfer hält dann weiterhin vor Motorbefehlen an, meldet
aber eine fehlende Eingabevoraussetzung und keinen behaupteten Transportfehler.
Motorbedingte
IMU-Bewegung wird getrennt von einer Kalibrierungsmessung bewertet.

Phasenanfang sichtbar, möglichst hörbar, mit fünf Sekunden Vorankündigung.
Reale Ausgabe-/Befehlszeiten protokollieren. Bei verspätetem Signal keine
Phasen zusammenpressen oder Motoren nachholen; den Lauf als unvollständig
beenden. Schlussruhe nur anhand der tatsächlich unberührten Daten bewerten.
Die maschinenlesbare Planung steht in `HARDWARE_TEST_002_PHASES.json`.

Für diesen Nutzerwunsch wurden **nur offline** die zulässigen Zeitgrenzen
angepasst: Client maximal 120 s, Kernel maximal 135 s, expliziter Testparameter
135000 ms. **Standard bleibt 30 s im Modul und 20 s im Client.** Jeder Impuls
bleibt maximal 400 ms; Output-Gate, exklusiver Besitzer und eine Sitzung pro
Bindung bleiben erhalten. Das ist eine neue Binärdatei gegenüber Test 001.
Die Kernelgrenze ist ein unabhängiger Endpunkt für Wartung/Ausgaben, keine
Echtzeitgarantie für mechanischen Motorstopp oder erfolgreiche USB-Zustellung.
`make test` und `make kernel-analyze` bestehen; Zeitplan, Grenzen und Sicherung
des alten Builds wurden offline geprüft. Nachweis mit neuem Modulhash:
`HARDWARE_TEST_002_PREPARATION.json`. Die Artefakte unter `build/` sind privat
und werden nicht versioniert.

## Freigabeschritte und Vorbedingungen

Jeder nummerierte Hardware-/Systemschritt braucht vorher eine **konkrete neue
Freigabe**. Die Vorbereitung oder eine Zustimmung zum Testziel ist keine
Ausführungsfreigabe. Graphische Passwortabfrage über ksshaskpass; keine Root-Shell.
Keine automatischen Wiederholungen, Reparaturen oder Rückbindungen.

1. **Frischer lesender Vorabcheck:** Kernel/Header, neuer Modulhash/vermagic,
   Aliase/Parameter, genau ein passendes Ziel am bestätigten Port, USB-ID,
   Bus/Adresse, Interface-/Endpunktkonfiguration, Treiber, Module, Speicher,
   Prozesse/offene Handles. Keine USB-Deskriptorabfrage. Ausgangszustand ist
   100a/xpad/usbhid mit verbundenem Funkcontroller und geschlossenem Deadband.
   Anderer Zustand: anhalten und erst beurteilen. Die alten Adressen nicht übernehmen.
2. **Offline-Ausführungshelfer fertig prüfen:** Lokale Phasenanzeigen, Startgate,
   evdev-Leser für genau dieses native 109c-Gerät, ein Besitzer für Clientbefehle
   und IMU-Snapshots, Logging, Stopps und die begrenzte Übergabe prüfen. Vorhandenen
   Test-001-Leser erweitern, nicht seine feste PID/Adresse/Dauer übernehmen.
   Dies ist inzwischen offline abgeschlossen: `tools/native/hardware_test_002.py`,
   17 künstliche Prüffälle und drei Tests des echten C-Clients mit ersetzten
   Systemaufrufen. Die echte Bindefolge und mechanische Wirkung bleiben ungetestet.
   Neue Änderungen am Helfer vor jeder Hardwarefreigabe erneut gezielt prüfen.
3. **industrialio nur falls fehlend laden:** eigene Freigabe, danach nur prüfen.
   War es schon geladen, kein erneuter Ladeversuch und später nicht entfernen.
4. **Einmaliger manueller Deadband-Übergang:** eigene Freigabe. Nutzer startet
   Deadband einmal, keine Speicher-/Test-/Firmwarefunktion. Das umfasst dessen
   bekannte USB-Abfragen, Handshake, temporäre xpad-Abgabe und Heartbeats.
   Ziel: verbundenes 109c, IF0 exklusiv von Deadband/usbfs gehalten; IF1 wie oben.
   Keine schnellen Umschaltungen, keine SHARE+MENU-Kombination (kann Remaps löschen).
   Keine erneuten allgemeinen IMU-/Motor-E2E-Tests in Deadband.
5. **Native Modulregistrierung:** eigene Freigabe, während IF0 nachweislich noch
   Deadband/usbfs gehört. Exakte PID/Interface als Parameter. Probe/ID-Tabelle
   nochmals prüfen: USB-Treiberregistrierung kann ungebundene passende Geräte
   automatisch prüfen; fehlende Autoload-Aliase verhindern das nicht. Deshalb
   nur registrieren, wenn IF0 bereits belegt ist und kein weiterer passender
   Zielpfad existiert. Unerwartete Bindung sofort dokumentieren und anhalten.
6. **Eng begrenzte Übergabe und Lauf:** Freigabe muss ausdrücklich die komplette
   unten genannte Folge sowie genau vier zeitlich festgelegte Impulse abdecken.
   Deadband direkt regulär über das Fenster schließen, ohne vorher „Release to games“;
   keine native Bindung bei
   noch offenem Deadband-USB-Handle. Nur nach Prozessende/Handle-Freigabe und
   frischer 109c-Prüfung: IF0 einmal von xpad lösen, einmal nativ binden, START.
   Zwischen diesen drei Aktionen keine Chatwartezeit; ein vorher geprüfter
   Helfer prüft nach jeder Aktion den Zustand. Ist IF0 nach Freigabe nicht an
   xpad, hat sich PID/Adresse geändert oder ist das Zeitfenster vorbei: stoppen,
   keine alternative Bindefolge versuchen. Kein blindes Binden an 100a.
7. **Rückweg:** END/Null-Motorpaket/Schließen ist Bestandteil der vorab freizugebenden
   Sitzung. Abbindung, Entladung und nötige xpad-Rückbindung jeweils gesondert
   freigeben; siehe unten. Keine automatische Fortsetzung.

Weil 109c nach Freigabe verschwinden kann, wäre eine neue Chatfrage zwischen
Abbindung, Bindung und START ungeeignet. Die ausdrücklich benannte Dreierfolge
ist nur dann erlaubt, wenn [tester] **genau diese Folge zusammen** freigibt.
Andernfalls bleibt der native Lauf gesperrt; keine stillschweigende Ausweitung
der Einzelzustimmung. Ein Abbruch vor START wird nicht automatisch neu gestartet.

## Konkrete Kommandos — Vorlagen, heute nicht ausführen

Alle Pfade/Werte beim späteren Vorabcheck konkret zeigen. `8-6` ist nur der
bisherige Port. Die Ausgabeknoten werden frisch über ihre USB-Eltern zugeordnet;
`event13` oder IIO-Nummern niemals übernehmen.

```sh
PROJECT="$(git rev-parse --show-toplevel)"
IFACE='8-6:1.0'
NODE="/dev/gsnative-$IFACE"
python -B tools/native/preflight.py --port 8-6
uname -r
modinfo build/kernel/gs_native.ko
sha256sum build/kernel/gs_native.ko build/gsnative-ctl
```

`preflight.py` prüft bisher ausschließlich den normalen 100a-Ausgangszustand.
Unter 109c schreibt es Metadaten, liefert aber Status 2. Der Ablaufhelfer besitzt
zusätzliche zustandsabhängige Prüfungen für usbfs/xpad/ungebunden/gs_native unter
109c. Status 2 des normalen Vorabchecks nicht pauschal ignorieren.

Getrennte Freigabe, nur bei fehlender Abhängigkeit:

```sh
SUDO_ASKPASS=/usr/bin/ksshaskpass /usr/bin/sudo -A -- /usr/bin/modprobe -- industrialio
```

Getrennte Freigabe, nur während belegtem 109c-IF0:

```sh
SUDO_ASKPASS=/usr/bin/ksshaskpass /usr/bin/sudo -A -p 'Password: ' -- /usr/bin/insmod "$PROJECT/build/kernel/gs_native.ko" test_interface="$IFACE" test_pid=0x109c enable_output=1 session_ms=135000
```

Nach ausdrücklich freigegebener Deadband-Freigabe und erfolgreichen Prüfungen
führt der Ablaufhelfer genau einmal diese Folge aus: IF0 von xpad lösen,
IF0 an gs_native binden und den einzigen Client mit 120 s starten. Er lädt
oder entlädt kein Modul und führt keine Rückbindung aus. Vorlage für den späteren
Aufruf in einem **sichtbaren Terminal**, noch nicht ausführen:

```sh
SUDO_ASKPASS=/usr/bin/ksshaskpass /usr/bin/sudo -A -p 'Password: ' -- /usr/bin/python -B "$PROJECT/tools/native/hardware_test_002.py" execute-authorized --manifest "$MANIFEST" --output "$RUN_DIR"
```

`MANIFEST` und `RUN_DIR` sind vor der konkreten Freigabe frisch anzulegen und mit
ihren tatsächlichen Pfaden zu zeigen. Frühere Manifeste/Adressen niemals wiederverwenden.
Das Manifest muss `scope=test002-handover-start-four-pulses-end-only`, Port,
Bus/Adresse/Devpath als Zeichenketten, die geladene `module_srcversion`, einen
frischen `journal_cursor` und SHA256 für Client, Modul, Zeitplan, Helfer und
Vorabcheck enthalten. Die Schlüssel im `sha256`-Objekt sind die Projektpfade.
Der Ordner muss neu, leer, Modus 0700 und Eigentum des aufrufenden Nutzers sein.
Das Manifest beschreibt die Grenzen; es ersetzt niemals [tester]' Freigabe.

Der Helfer prüft die Modulparameter und die bestehende exklusive Deadband-
Belegung. Erst dann lokales `bereit` (Groß-/Kleinschreibung egal, bis zu 5 Minuten
Zeit), 15 s Countdown und die Aufforderung zum direkten regulären Schließen des
Deadband-Fensters, ohne vorherige separate Freigabe per Schaltfläche.
Dafür maximal 90 s; keine Chat-Stoppuhr. Nach vollständiger
Handle-Freigabe läuft die bestätigte Bindefolge mit 2-s-Zeitgrenze vor jedem
nächsten Schritt. Passwort vor der Deadband-Freigabe abfragen; keine erneute
Abfrage innerhalb der Übergabe. Kein sudo-Konfigurations-/Rechtewechsel.

Während des Laufs: sichtbare Phasen mit Terminalglocke (Ton abhängig vom Terminal),
Kerneljournal ab Cursor, PID-/Bindungsprüfung und vollständige Prozessprüfung,
Clientstatus etwa alle 250 ms. Neue Kernelwarnungen ab Priorität 4, ein beendeter
Logmonitor oder unlesbare Prozesszugriffe führen zum Halt. Es ist keine automatische
Ausnahme für xpad-ENOENT hinterlegt. IMU-Snapshots älter als 1 s und ein während
der Motorphase länger als 1 s stillstehender Gamepadzähler brechen ebenfalls ab.
Diese Prüfintervalle und Fristen sind keine Echtzeitgarantie für blockierende
Kernelaufrufe. Vor einem Test müssen dessen Rückweg und Abbruchbefugnis vorliegen.

Im selben exklusiven Client werden `info`/`sample` und genau diese Motorbefehle
zugeführt, jeweils mit dokumentiertem Zeitpunkt:

```text
+91 s:  pulse left 100 400
+96 s:  pulse right 100 400
+101 s: pulse lt 100 400
+106 s: pulse rt 100 400
+120 s: quit
```

Nach jedem Impuls ein zusätzlicher `stop` bei +0,6 s, vor dem nächsten Impuls
erfolgreichen Stopp und fehlerfreien `info` prüfen. Fehler beendet den gesamten
Lauf; keine weiteren Impulse. `stop` beendet nicht die Heartbeats, `quit`/END
schon. Ctrl-C/Abbruch löst END aus; ein bestätigtes Nullpaket ist keine mechanische
Rückmeldung. Bei weiter spürbarer Vibration keine weitere Motoraktion.

## Datenerfassung und Erfolgskriterien

Neues privates Verzeichnis `build/hardware-tests/002-<UTC-Zeitstempel>/`,
außerhalb temporärer Ordner, nichts überschreiben oder automatisch löschen.
Vorher Schreibrechte/freien Speicher prüfen, Verzeichnis privat anlegen.

- `before.json`, `109c-handover.json`, `after.json`: Identität/Adresse/Port,
  Interfaces, Besitzer, Kernel-/Modulstatus. Hashes und exaktes Ziel stehen im
  mitprotokollierten Manifest; Parameter werden vor dem Lauf exakt geprüft.
  Vollständigen Vorabcheck mit Programmen/Parametern zusätzlich privat sichern.
- `events.jsonl`: UTC und monotone Nanosekunden, tatsächliches START/Phasen/
  Benutzerbereit/Impuls/Stop/END; geplante und tatsächliche Zeiten getrennt.
- `input.jsonl`: echte native evdev-Ereignisse, Anfangs-/Endzustand; kein Grab,
  keine Änderung der Geräteuhr, Herkunft über Sysfs-Eltern prüfen.
- `imu.jsonl`: atomare sechsachsige GET_SAMPLE-Snapshots desselben Client-FDs,
  Sample-Nummer und Host-Monotonzeit. Ab +5 s etwa alle 20 ms abfragen;
  Duplikate/Sprünge/Fehler sichtbar erhalten. Es ist ein Latest-Sample-Pfad,
  kein vollständiger IMU-Buffer. Nicht jedes USB-Paket wird dadurch gespeichert.
  Keine gleichzeitigen zweiten `gsnative-ctl sample`-Prozesse: exklusiver Besitzer.
- `motors.jsonl`, `client.stdout.txt`, `client.stderr.txt`: Annahme/Rückgabe
  der vier Befehle und Stopps, Nutzerbestätigung aller vier Wirkungen separat.
- `kernel.jsonl`: Kerneljournal ab Vorab-Cursor während des Helferlaufs;
  Journalfortsetzung bis nach dem separat freigegebenen Rückweg extra sichern.
  Warnungen/Fehler und fremde Geräteinformationen privat halten.
  Privilegierter Logabruf nur mit Freigabe.
- `result.json`, `SHA256SUMS`: SHA256 über abgeschlossene Originaldateien und
  anschließende Kontrolle. Auswertung getrennt, keine Originale korrigieren.

`passed_transport_run` allein bestätigt keine vollständige Hardwareprüfung:
Motorwahrnehmung, gleichzeitige Eingaben in den vier Motorfenstern und Rückkehr
zu xpad werden anhand der Originaldaten beziehungsweise Nutzerbestätigung
separat ausgewertet. Bei Abbruch keine automatischen Wiederholungen.

Erfolg verlangt echte Gamepad-Ereignisse, frische/wechselnde IMU-Rohwerte und
steigende Gamepad-/IMU-Zähler in denselben Zeitfenstern, auch während Motoren.
Alle vier Einzelimpulse müssen akzeptiert und laut Nutzer am richtigen Motor
spürbar sein; Stopps müssen fehlerfrei zurückkehren und Vibration enden.
Registrierte Input-/IIO-Knoten oder erfolgreiche OUT-Rückgaben allein genügen
nicht. Volle Achsenausschläge nur behaupten, wenn im neuen Lauf erreicht.
Kipp-/Drehbewegungen belegen Reaktionen, keine genaue Achsenzuordnung/Kalibrierung.

Eine neue usbmon-Aufnahme ist keine Voraussetzung dieses Plans und **nicht
implizit freigegeben**. Bei zusätzlichem Bedarf separat den validierten isolierten
Recorder freigeben; kein unisoliertes dumpcap und kein neuer USB-Recorder.

## Kontrollierter Rückweg zu xpad

Der Rückweg wird vor dem Hinweg ausdrücklich mitgeprüft und freigegeben.
Abbruch und Sitzungsschluss stoppen nur den aktuellen Test; sie autorisieren
keine neuen Bindungen oder Identitätsbefehle.

1. Über denselben Client END, Null-Motorpaket, FD schließen, Input-Leser beenden.
   Erfolgs-/Fehlerstatus speichern. Danach keine Heartbeats mehr. Bis 15 s rein
   lesend auf Rückkehr warten; eine Neuanmeldung nur **nach** END in dieser
   Rückkehrphase ist erwartbar und wird mit neuer Adresse dokumentiert.
2. Ist das alte native Interface noch vorhanden/gebunden: einmalige native
   Abbindung nach eigener Freigabe. Wenn es bereits durch die Neuanmeldung
   verschwunden ist, nicht auf den alten Pfad schreiben.

   ```sh
   printf '%s' "$IFACE" | SUDO_ASKPASS=/usr/bin/ksshaskpass /usr/bin/sudo -A -- /usr/bin/tee /sys/bus/usb/drivers/gs_native/unbind
   ```

3. Nach geschlossenen Handles und fehlender nativer Bindung separat freigegeben
   einmal entladen; kein Erzwingen und kein globales xpad-Entladen:

   ```sh
   SUDO_ASKPASS=/usr/bin/ksshaskpass /usr/bin/sudo -A -- /usr/bin/rmmod -- gs_native
   ```

4. Falls IF0 noch treiberlos ist, VID/Port/aktuelle PID und xpad-Eignung erneut
   prüfen und **separat** einmal an xpad binden. Für 109c ist das eine Rückgabe
   des Interfaces, kein bestätigter 100a-Umschaltbefehl. Bereits vorhandenes xpad
   nicht erneut binden. Bei wiedererschienenem 100a den frischen Interfacepfad nehmen.

   ```sh
   printf '%s' "$IFACE" | SUDO_ASKPASS=/usr/bin/ksshaskpass /usr/bin/sudo -A -- /usr/bin/tee /sys/bus/usb/drivers/xpad/bind
   ```

5. Abschluss nur nach 3537:100a am selben Port, IF0 xpad, IF1 usbhid, native
   Knoten verschwunden, Modul entladen, Deadband geschlossen, keine neuen
   Kernelwarnungen und normaler Eingabefunktion im KDE Center. Ein funktionierendes
   109c/xpad ist separat zu melden und ersetzt nicht den ursprünglichen 100a-Zustand.
6. Falls 100a ausbleibt: stoppen, Status/Logs sichern. **Nur mit eigener konkreter
   Freigabe** als manueller Rückweg den Dongle einmal abziehen, 10 s warten,
   am selben Port wieder einstecken und anschließend nur lesend prüfen. Kein
   USB-Reset, keine SHARE+MENU-/Pinhole-Aktion, keine Profiländerung, kein Retry.
   Auch dieser Rückweg wird nicht als garantiert behauptet. Wenn er scheitert,
   keine weitere Maßnahme ohne neue Entscheidung. Der Funkcontroller hat hier
   keinen zuverlässig nutzbaren manuellen Ausschaltvorgang; diesen nicht voraussetzen.

industrialio, das schon vor dem Test vorhanden war, bleibt geladen. Eine
entstandene Kernel-Taint-Markierung lässt sich durch rmmod nicht beseitigen.
Der alte Test-001-Build bleibt lokal unter `build/module-history/4e76ff7/`
mit seinem ursprünglichen Hash erhalten; kein automatischer Modul-Downgrade.

## Sofortige Abbruchbedingungen

Andere VID/PID/Adresse/Port innerhalb einer stabilen Testphase, falsche Endpunkte
oder Besitzer, offenes Deadband bei nativer Übernahme, unerwartete Probeübernahme,
neue Warnung/Oops/USB-Fehler, START-/Stop-Fehler, fehlende Daten nach 5 s,
veraltete Snapshots über 1 s, Datenstillstand während Motoren, Schreib-/Zeitplanfehler,
ausbleibende oder anhaltende Motorwirkung, Nutzer-STOPP: keine weiteren Tests.
Der vorab freigegebene END/Stopversuch bleibt erlaubt, danach Rückweg priorisieren.
Die enge bekannte Test-001-Ausnahme für einen einzelnen xpad-ENOENT-Abbauhinweis
gilt hier **nicht automatisch**; vor dem Lauf konkret anhand des heutigen
Abbaupfads benennen. Keine Fehler pauschal wegfiltern.

Nach Ergebnisbericht und Commit stoppen. Keine weitere Aufnahme, Wiederholung,
Deadband-Sitzung oder Treiberentwicklung am laufenden Gerät automatisch anschließen.
