> Public export: personal tester, host and path references were anonymized. Historical evidence hashes refer to the private originals.

# Nativer Motorvergleich: fünf Minuten, Ablaufplan

12. Oktober 2026. Ursprünglich offline vorbereitet; anschließend einmal
schrittweise freigegeben und erfolgreich durchgeführt:
[Ergebnisse und Grenzen](NATIVE_MOTOR_COMPARISON_RESULTS.md).
Dieser Plan ist **keine Freigabe für weitere Läufe**. Er setzt [tester]' jüngste
Vorgabe um: drei Impulse je Motor, **je 1.000 ms und danach mindestens fünf
Sekunden Pause**, weiterhin 60 Sekunden pro Motor. Er ersetzt für diesen
neuen Lauf den Vorschlag mit 400 ms und 15 Sekunden Startabstand.
Die frühere 120-s-Variante und alle Aufnahmen bleiben erhalten.

Ziel ist der direkte Vergleich mit den zwölf erfolgreichen Deadband-Impulsen
aus [MOTOR_COMPARISON_RESULTS.md](MOTOR_COMPARISON_RESULTS.md). Dabei ändert sich
bewusst die angeforderte Dauer von 400 auf 1.000 ms. Eine bessere Spürbarkeit
darf deshalb nicht automatisch als behobener Sequenz- oder Treiberfehler gelten.
Der bisherige gemeinsame native Sequenzzähler wird nicht spekulativ geändert.

## Zeitplan und Ansagen

Die Uhr beginnt am tatsächlichen nativen START-Aufruf, nicht bei einer
Chatnachricht. Vor der Übergabe lokales `bereit` (Groß-/Kleinschreibung egal)
und 15 Sekunden Countdown; Passwort und Recorderstart liegen davor bzw. vor
dem Countdown. Erst wenn der isolierte Recorder nachweislich läuft, darf
der Helfer zum Schließen von Deadband und zur genehmigten Übergabe auffordern.

| Zeit ab START | Phase | Nominale Impulsstarts |
|---|---|---|
| 0–30 s | Initialisierung, Ruhe und Vorbereitung | keine |
| 30–90 s | Linker Griff | 45 / 51 / 57 s |
| 90–150 s | Rechter Griff | 105 / 111 / 117 s |
| 150–210 s | Linker Trigger | 165 / 171 / 177 s |
| 210–270 s | Rechter Trigger | 225 / 231 / 237 s |
| 270–300 s | Abschlussruhe, danach END | keine |

Je Motor ein 60-s-Fenster mit 15 s Vorlauf zum ersten Impuls. Deutliche lokale
Ansagen nennen Motor, Wiederholung und die nötige kleine Stickbewegung für den
gleichzeitigen Eingabenachweis. Außerhalb dieser ausdrücklich angekündigten
Eingabefenster sind Pausen ohne Stickbewegung zulässig. IMU-, Status-, Identitäts-
und Recorderkontrollen laufen durchgehend; Ruhe ist keine Gerätefehlermeldung.

Jeder Impuls: genau ein Motor bei 100 %, alle anderen null. Nach mindestens
einer Sekunde ab Impulsbestätigung wird zusätzlich STOP angefordert. Der nächste
Impuls darf frühestens fünf Sekunden **nach bestätigtem STOP** beginnen.
Geringe Verschiebungen durch USB-/Clientlatenz werden protokolliert; kein
Zusammenpressen oder Nachholen verspäteter Befehle. Die nominellen Startabstände
betragen sechs Sekunden. Die restliche Zeit im Motorfenster ist Rückmeldepause.
Zwölf Sekunden angeforderte Vibration insgesamt, keine Dauervibration.

Die Firmware-Dauer wird in 10-ms-Einheiten kodiert: eine volle Sekunde entspricht
Byte 10 = 100 (`0x64`). Der Kernel kodiert beim Senden die noch verbleibende
Frist, auf zehn Millisekunden aufgerundet, statt jede spätere Zustandsausgabe
erneut um eine volle Sekunde zu verlängern. Softwarefrist, USB-Zeitpunkte und
tatsächlich gefühlte Dauer bleiben getrennte Messgrößen. Die Ein-Sekunden-Pakete
sind inzwischen im oben verlinkten Lauf aufgezeichnet; alle zwölf Wirkungen
und Stopps wurden vom Nutzer bestätigt.

## Vorbereitung und spätere Freigaben

Die Offline-Variante des vorhandenen Helfers heißt `motor-comparison-300`.
Es gibt keinen automatischen Start, keinen neuen eigenen USB-Recorder und
keinen Hardwarezugriff im Modus `show-plan` oder in den künstlichen Tests.
Der vorhandene Client erlaubt maximal 300 s, der Kernel maximal 315 s;
die Standards bleiben 20 s bzw. 30 s. Die Impulsgrenze beträgt jetzt 1.000 ms.
400-ms-Aufrufe und die aufgezeichneten 400-ms-Encoderpakete bleiben gültig.
Der bisherige Modulbuild bleibt mit SHA256 unter `build/preserved-modules/`.

Offline geprüft: 29 Ablaufhelfer- und 31 Recorderadaptertests, elf synthetische
Clientfälle sowie 15 Fälle mit den tatsächlichen Kernel-Sendefunktionen und
künstlichem USB-/Zeitverhalten bestanden. Parser, Sensorvertrag, Protokoll,
Runtime und Fixtures bleiben erfolgreich; der gespeicherte Datenvergleich
umfasst weiterhin 12.204 IMU-Pakete und 5.244 Gamepad-Pakete im Kernelmapping.
Kernelbuild ohne Warnungen, Checkpatch und statische Analyse erfolgreich.
Hashes, Testbefehle und Grenzen: [Offline-Nachweis](NATIVE_MOTOR_COMPARISON_OFFLINE.json).
Diese Simulation ersetzt keinen realen Lauf des neuen Builds.

Beim anschließenden lesenden Vorabcheck korrigiert: Die installierte
dumpcap-Datei gehört root mit einer eigenen Paketgruppe. Der Adapter darf
keine feste GID 0 verlangen; er pinnt die frisch freigegebene numerische
Gruppe zusammen mit Eigentümer, Modus, Hash und Capabilities. Keine
Systemrechte geändert. Jetzt 34 Recorderadaptertests bestanden;
[Folgenachweis mit aktuellen Adapterhashes](NATIVE_MOTOR_METADATA_FIX.json).

Vor einer Durchführung weiterhin schrittweise konkret freigeben:

1. Frischen lesenden Vorabcheck mit aktuellen Kernel-/Artefaktdaten, Port,
   Bus/Adresse, Interfaces, Besitz, freien Ressourcen und fremden Zugriffen.
   Ausgangslage 100a/xpad/usbhid, Funkcontroller verbunden, Deadband geschlossen.
   Keine alten Adressen oder alten Freigabemanifeste übernehmen.
2. Fehlende Module nur einzeln nach eigener Freigabe laden. Kein automatisches
   Nachladen durch Helfer oder Recorder.
3. Bekannten manuellen Deadband-Übergang nach 109c separat freigeben, ohne
   Einstellungen zu schreiben oder Motoren in Deadband zu testen.
4. Neuen gs_native-Build nur nach Freigabe registrieren, während IF0 nachweislich
   von Deadband/usbfs belegt ist. Exaktes Zielinterface, PID 109c, Output-Gate,
   `session_ms=315000`; keine automatische Übernahme anderer Geräte.
5. Genau einen kombinierten Lauf ausdrücklich freigeben: isolierte Aufnahme,
   direktes reguläres Schließen von Deadband, xpad-Abbindung → native Bindung →
   START, zwölf Impulse, STOP/END und begrenzter passiver Aufnahme-Nachlauf.
   Übergabe nur am verifizierten IF0, innerhalb der vorhandenen Zwei-Sekunden-
   Grenze und nach vollständiger Freigabe der fremden Handles.
6. Nötige native Abbindung, Rückbindung an xpad und Entladung weiterhin einzeln
   freigeben. Normale Funktion abschließend im KDE Center bestätigen.

Unerwartete PID/Adresse oder Bindung, fehlender exklusiver Besitz, neue
Kernelwarnung, fehlende/stale Daten, ausgefallener Recorder, zu wenig Aufnahme-
Restzeit, Speicherknappheit, verspätete Abläufe oder fehlende STOP-Bestätigung
beenden den Lauf. Keine weiteren Impulse, keine Wiederholung oder Reparatur.
Der bestehende END-Pfad versucht das Nullpaket, beendet Heartbeats und schließt
den Client. Ein ausgebliebener mechanischer Stopp ist ausdrücklich zu melden;
eine erfolgreiche USB-Rückgabe beweist ihn nicht.

## Isolierter USB-Mitschnitt

Der Recorder übernimmt die bereits validierte Bubblewrap-/dumpcap-Kette als
kontrollierte Kopie. Nur `/dev/usbmon8`, niemals `/dev/bus/usb`; sechs getrennte
Namespaces, fünf Capability-Sätze null, NoNewPrivs=1, private Mounts,
unveränderte Knotennummer/Rechte und kontrollierte Dateideskriptoren. Damit hat
libpcap keinen usbfs-Zugriff für automatische Deskriptorabfragen.

Aufnahme nach lokalem `bereit`, während 109c noch sicher von Deadband gehalten
wird; vor der zeitkritischen Übergabe bereits aktiv und geprüft. Sie erfasst
native Initialisierung, Wartung, Eingaben, IMU, zwölf Motorpaare und END/Rückkehr.
Der frühere 100a→109c-Handshake liegt vor dieser Aufnahme und wird in diesem
Lauf nicht erneut als USB-Paketfolge aufgezeichnet.

Harte Aufnahmegrenze 450 s, äußerer Timeout 480 s. Vor jedem Übergabeschritt
und während des nativen Laufs muss genug Zeit für die verbleibende Testsitzung
plus 30 s Nachlauf vorhanden sein. Aufnahmeende während des nativen Tests ist
ein Abbruchgrund. Nach END mindestens 30 s passiver Nachlauf, danach nur den
eigenen eindeutig zugeordneten Recorder beenden; keine USB-Steuerung.

PCAPNG, USB_LINUX_MMAPPED, volle Nutzdaten (`-s 0`), vollständige Busereignisse
einschließlich Submit/Complete/Fehler. Neue private Datei im dauerhaft
gespeicherten Laufordner, keine temporäre Aufnahme und kein Überschreiben.
Original unverändert behalten; UTC und monotone Zeitbasis, tatsächliche Ansagen,
Client- und USB-Zeiten, Geräteepochen und SHA256 sichern. Fremden Busverkehr
privat halten. Später Zielgerät über Port-/Zeit-/Adressfolge filtern, nicht
allein über eine alte Geräteadresse; IN und OUT erhalten.

Offline anschließend vollständige Längen, Dropzähler und URB-Status prüfen,
Starts/Stopps eindeutig paaren, Motorwerte/Dauer/Sequenz und tatsächliche
Abstände mit den gespeicherten Deadband-Daten vergleichen. Ein-Sekunden-Dauer
als bewusste Abweichung dokumentieren. Eingaben und sechs IMU-Rohkanäle während
jedes Motorfensters belegen. Wahrnehmung jeder Wiederholung separat erfragen.
Gyrofaktor, Sensorachsenkalibrierung und endgültige SDL-Freigabe bleiben offen.

## Konkrete Aufrufe für die spätere Freigabe

Heute erlaubt und rein offline:

```sh
python -B tools/native/hardware_test_002.py show-plan --variant motor-comparison-300
make test
make test-capture
make kernel-analyze
```

Vorlage für einen neuen Hardwarelauf, **nur nach neuer konkreter Freigabe**.
`PROJECT` ist die bestehende
Projektwurzel; `RUN_DIR` ein neuer leerer Ordner unter `build/hardware-tests/`
mit Modus 0700 und Eigentümer [tester]. `MANIFEST` ist ein frisch vorbereiteter,
geprüfter Datensatz gemäß
[Vorlage](NATIVE_MOTOR_COMPARISON_MANIFEST_TEMPLATE.json), mit aktueller
Geräteadresse, Journalcursor, Build-/Helferhashes und dumpcap-Metadaten.
Die Vorlage enthält absichtlich fehlende Live-Werte und ist nicht ausführbar.
Das Manifest ersetzt keine menschliche Freigabe.

Einzeln freizugebendes Laden des geprüften Builds während Deadband IF0 hält:

```sh
SUDO_ASKPASS=/usr/bin/ksshaskpass /usr/bin/sudo -A -p 'Password: ' -- \
  /usr/bin/insmod "$PROJECT/build/kernel/gs_native.ko" \
  test_interface=8-6:1.0 test_pid=0x109c enable_output=1 session_ms=315000
```

Nach weiterer konkreter Freigabe in einem sichtbaren Terminal:

```sh
SUDO_ASKPASS=/usr/bin/ksshaskpass /usr/bin/sudo -A -p 'Password: ' -- \
  /usr/bin/python -B "$PROJECT/tools/native/hardware_test_002.py" \
  execute-authorized --variant motor-comparison-300 \
  --manifest "$MANIFEST" --output "$RUN_DIR"
```

Der Helfer lädt kein Modul. Er wartet auf `bereit`, startet genau eine
isolierte Aufnahme und führt erst nach erfolgreicher Recorderprüfung die
vorab genehmigte Übergabe aus. Der Recorder nutzt intern:

```sh
/usr/bin/dumpcap -i usbmon8 -y USB_LINUX_MMAPPED -s 0 -F pcapng \
  -a duration:450 -a filesize:2000000 -q -w -
```

Diesen inneren Befehl niemals direkt auf dem Host ausführen. Der Adapter
startet ihn über den privaten Mount-Namespace und die geprüfte Sandbox;
das vollständige argv und die geprüften Quellkopien werden gespeichert.
Mindestens 5 GiB freier Speicher vor Start, Abbruch unter 1 GiB oder bei
2.000.000.000 Byte Aufnahmegröße. Ein vorzeitiges Dateigrößen-/Zeitlimit ist
ein unvollständiger Lauf, keine still akzeptierte Teilaufnahme.

Daten unter `RUN_DIR/usb-capture/`: `original-usbmon8.pcapng`,
`capture.log`, `usb-udev-events.log`, Vor-/Nachprüfungen, Recorder-Nachweise,
`capture-outcome.json` und `SHA256SUMS`. Daneben native Ereignis-, IMU-,
Motor-, Client- und Kernelprotokolle mit eigener Zusammenfassung/Prüfsumme.
Der Capture-Ergebnisbericht entsteht erst nach erfolgreicher Prüfung der
stabilen Aufnahmedateien; sein eigener Hash wird im übergeordneten
`result.json` und dessen Prüfsummenkette gesichert. Fehlgeschlagene Sicherung
wird als Fehler dokumentiert, niemals als erfolgreicher Mitschnitt.
Zum regulären Ende wird nur der über Prozessbaum, Startzeit, Namespaces und
pidfd zugeordnete eigene dumpcap beendet; danach prüft der Sandbox-Gast
weiterhin Rechte, Mounts und geschlossene Monitor-FDs. Kein globales `pkill`.

## Rückweg

Wie im bestehenden [Hardwareplan](HARDWARE_TEST_002.md): END und Ende der
Heartbeats, danach nur lesend die Neuanmeldung beobachten. Bei 100a/xpad/usbhid
normale Eingaben bestätigen. Bleibt gs_native gebunden oder fehlt xpad,
anhalten und den passenden einzelnen Rückweg ausdrücklich freigeben lassen.
Keine automatische Bindung, kein globales xpad-Entladen, kein Wechselkommando.
