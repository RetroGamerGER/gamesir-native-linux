# Hardwaretest 001 — 100a-XInput

Stand: 12. Oktober 2026. **Native 100a-XInput-Eingaben und kontrollierte Rückgabe
an xpad sind nachgewiesen.** Die normale Funktion nach der Rückbindung bestätigte
der Nutzer im **KDE Center**. Der Test ist mit den unten beschriebenen Grenzen
abgeschlossen; insbesondere ist die vollständige Schlussruhe nicht validiert.

Maschinell lesbare, für Git geprüfte Zusammenfassung:
[HARDWARE_TEST_001_RESULTS.json](HARDWARE_TEST_001_RESULTS.json).

## Bestätigter Verlauf am 11. Oktober

- industrialio und gs_native nach jeweils konkreter Freigabe geladen.
- IF0 einmal erfolgreich von xpad abgebunden. Dabei eine xpad-Meldung:
  `usb_submit_urb failed with result -2` (-ENOENT); Test angehalten.
- IF0 anschließend einmal eigens freigegeben an xpad zurückgebunden.
  IF1 blieb usbhid, 3537:100a / Port 8-6 / Adresse 52 unverändert.
  Input-Gerät neu registriert, keine neuen Kernelwarnungen/-fehler.
- gs_native wurde nie gebunden; kein Eingabetest, keine Motorausgabe.

Private Originalbelege liegen unter
`build/hardware-tests/001-20261011T180547699721Z/`; alle 72 SHA256-Einträge
wurden bei der heutigen Fortsetzung unverändert verifiziert. Das Feld
`rebind_attempts=2` im alten Abschluss-JSON ist ein Zählfehler: das Glob nahm
auch den Logabruf-Intent auf. Das tatsächliche Bind-Intent/Result-Paar belegt
genau eine Rückbindung. Originaldateien bleiben erhalten.

## Historischer lesender Vorabcheck vom 12. Oktober

Erfasst am 12. Oktober um 12:49 UTC (14:49 Europe/Berlin):

| Eigenschaft | Befund |
|---|---|
| Kernel / Header | 7.2.9-2-garuda / passende Header vorhanden |
| Zielgerät | VID 3537, PID 100a, Port 8-6, Bus 8, Adresse 6 |
| IF0 / IF1 | xpad / usbhid |
| IF0-Endpunkte | IN 0x82 und OUT 0x02, Interrupt, jeweils 32 Byte |
| industrialio / gs_native | beide nicht geladen |
| Modul | unverändert, passende vermagic, keine Autoload-Aliase |
| Modul-SHA256 | `6cf68587aa951d95c84ec8bd30f14dd0a751e034ed10c2865eba208c4cd397d8` |
| Kerneljournal | ohne erhöhte Rechte lesbar; vorhandene HID-Meldung als Baseline erfasst |
| industrialio-Trockenlauf | ausschließlich vorhandenes industrialio.ko.zst |

Vollständige private Baseline, Vorabcheck, Modulinformationen und Bewertung:
`build/hardware-tests/001-continued-20261012T124928294422Z/`.
Keine erhöhten Rechte, Module, Bindungen oder Hardwarezugriffe wurden bei
diesem Vorabcheck verwendet bzw. verändert. Diese Tabelle beschreibt den
damaligen Stand und nicht den späteren Testzustand.

Ein anschließender Vorabcheck fand 109c/Adresse 7; der damals geplante
industrialio-Ladeschritt wurde **vor Ausführung** angehalten. Nach erneuter
Nutzerbestätigung der Funkverbindung wurde 100a/Adresse 8 frisch geprüft.
Der kontrollierte native Bindungs-/Eingabelauf und der Rückweg verwendeten
danach durchgehend 3537:100a, Bus 8, Adresse 8, Port 8-6. PID allein belegt
keinen Funkzustand. Eine bereits vorhandene HID-Meldung
`ignoring exceeding usage max` blieb Teil der Baseline.

## Bewertung der xpad-Meldung

Für `usb_submit_urb()` bezeichnet -ENOENT einen fehlenden/deaktivierten
Endpunkt oder ein entsprechendes Interface; es ist hier kein Completionstatus.
Im Upstream-Kernel v7.2.9 deaktiviert der USB-Core beim Unbind ohne soft_unbind
die Endpunkte vor disconnect. xpad setzt soft_unbind nicht; LED-Abmeldung kann
in dieser Phase noch eine OUT-Einreichung versuchen. Der genaue Garuda-
Aufrufpfad ist ohne passenden vollständigen Quellcode oder Stack nicht bewiesen.

Die erfolgreiche Rückbindung ohne neue Fehler spricht gegen einen anhaltenden
Defekt. Für diesen Test blockiert die einzelne identische Meldung im engen
Unbind-Fenster allein nicht. Bedingungen und übrige Abbruchregeln stehen im
[Hardwareplan](HARDWARE_TEST_PLAN.md); kein allgemeines Ignorieren von Fehlern.

Quellen: [USB-Fehlercodes](https://docs.kernel.org/driver-api/usb/error-codes.html),
[USB-Abbau v7.2.9](https://github.com/gregkh/linux/blob/v7.2.9/drivers/usb/core/driver.c#L428),
[xpad v7.2.9](https://github.com/gregkh/linux/blob/v7.2.9/drivers/input/joystick/xpad.c#L1666).

## Durchgeführte Fortsetzung am 12. Oktober

Jeder Modul-/Bindungsschritt wurde einzeln freigegeben und einmal ausgeführt.
Der Modulbuild aus Quellstand `4e76ff7` blieb unverändert; kein Neubau nötig.

| Schritt | Beginn UTC | Ergebnis |
|---|---|---|
| industrialio laden | 13:05:41 | erfolgreich; xpad/usbhid unverändert |
| gs_native laden | 13:09:06 | erfolgreich; keine automatische Geräteübernahme |
| IF0 von xpad abbinden | 13:12:40 | erfolgreich; genau eine bekannte -ENOENT-Abbaumeldung |
| IF0 an gs_native binden | 13:18:58 | erfolgreich; native Input-Registrierung, OUT=0 |
| Native Eingaben aufzeichnen | 13:25:07 | 60 s, tatsächliche evdev-Ereignisse |
| IF0 von gs_native abbinden | 13:33:16 | erfolgreich; native Geräteknoten entfernt |
| gs_native entladen | 13:35:54 | erfolgreich; nur dieses Modul entfernt |
| IF0 an xpad zurückbinden | 13:39:34 | erfolgreich; xpad-Input wieder registriert |

Modulparameter: `test_interface=8-6:1.0 test_pid=0x100a enable_output=0`.
Das externe, unsignierte Modul erzeugte beim Laden die erwarteten
Kernel-Taint-/Signaturmeldungen. Die einzelne xpad-Abbaumeldung erfüllte
die enge Ausnahme im Hardwareplan. Native Bindung, Eingabetest, native
Abbindung/Entladung und xpad-Rückbindung erzeugten keine neuen Warnungen
oder Fehler in den gesicherten Journalabschnitten.

## Eingabemessung und Zentrierung

Auf Nutzerwunsch wurde der ursprüngliche 12-s-Vorschlag vor Ausführung durch
**10 s Ruhe, 40 s manuelle Eingaben und 10 s vorgesehene Schlussruhe** ersetzt.
Der 12-s-Test wurde nicht ausgeführt. Die tatsächliche Messung lief von
13:25:07,637 UTC bis 13:26:07,641 UTC (15:25/15:26 Europe/Berlin),
einschließlich Abschlussoperationen 60,004 s.

Der aus IF0 ermittelte Knoten war `/dev/input/event13`, zugehörig zu
`GameSir G7 Pro native TEST gamepad`, USB 3537:100a. Öffnung ausschließlich
`O_RDONLY|O_NONBLOCK` als normaler Nutzer mit vorhandener Input-Berechtigung:
kein Grab, keine Writes oder Änderung der evdev-Uhr. Keine USB-/Entwickler-
Geräteknoten wurden vom Testprogramm geöffnet; `gsnative-ctl info`/`session`
und `jstest` wurden in diesem Lauf nicht verwendet.

Erfasst wurden **83.475 Ereignisse**: 65.420 EV_ABS, 107 EV_KEY und 17.948 EV_SYN.
Kein Lesefehler oder SYN_DROPPED wurde beobachtet; Prozessende erfolgreich,
Input-FD geschlossen. Das JSONL erhält Kernel-sec/usec, Host-UTC und
Monotonzeit, Phasenmarken und lesende Achsen-/Tastenzustands-Snapshots.

| Eingabe | Beobachteter Bereich | Anfangs-/Endsnapshot |
|---|---|---|
| Linker Stick X / Y | beide -32768 bis 32767 | 0 / -1 |
| Rechter Stick X / Y | beide -32768 bis 32767 | 0 / -1 |
| Linker / rechter Trigger | beide 0 bis 1023 | 0 / 0 |
| Steuerkreuz X / Y | jeweils -1, 0, 1 | 0 / 0 |

Alle elf registrierten Tastencodes wurden mindestens einmal gedrückt und
losgelassen: BTN_SOUTH/EAST/NORTH/WEST, TL/TR, SELECT/START/MODE und THUMBL/THUMBR.
Die physische Zuordnung jeder Tastenbeschriftung wurde dabei nicht unabhängig
protokolliert. Im letzten Snapshot blieb BTN_EAST/B (305) gedrückt; seine
Freigabe nach dem letzten Druck liegt außerhalb der Aufnahme und ist unbelegt.

Die ersten zehn Sekunden enthalten keine Stickänderungen; beide Sticks
melden stabil X=0/Y=-1 bei `fuzz=0`, `flat=0`. Die Y-Werte entstehen durch
Bitinversion (`~raw_y`), weshalb Rohwert null als -1 erscheint. Die Endwerte
kehren auf dieselben Werte zurück. Dies belegt die beobachtete Zentrierung,
keine physikalische TMR-Kalibrierung oder Langzeitdriftfreiheit; mögliche
Firmware-Deadzones wurden nicht bestimmt.

**Die Schlussruhe ist nicht vollständig validiert.** Im vorgesehenen Fenster
50–60 s wurden weiter Sticks bewegt und 19 Tastenereignisse erfasst. Der Nutzer
erklärte dies mit seiner Reaktionszeit auf die Chatansage. Die Übermittlungs-
verzögerung des Chats wurde nicht gemessen. Für einen späteren freigegebenen
Test lokal sichtbare/hörbare Phasensignale vorbereiten; keine automatische
Wiederholung. Eingabefunktion und Grenzwerte bleiben durch echte Ereignisse
belegt. EV_SYN zählt geänderte Input-Frames und belegt keine USB-Pollingrate.

## Rückkehr zu xpad

Die lesende Nachprüfung der Rückbindung am 12. Oktober um 13:39 UTC bestätigt:

- 3537:100a, Bus 8, Adresse 8, Port 8-6; IF0 xpad / IF1 usbhid.
- Input-Registrierung `Generic X-Box pad`, `/dev/input/event13` und `/dev/input/js1`.
- gs_native-Modul/-Treiber und native Entwicklerknoten entfernt.
- Keine neuen Kernelwarnungen/-fehler; IF1 und dessen Input-Metadaten unverändert.

Anschließend bestätigte der Nutzer ausdrücklich, dass der Controller wieder
wie gewohnt funktioniert, **getestet im KDE Center**. Dies ist eine
Nutzerbestätigung zusätzlich zur lesenden Bindungs-/Registrierungsprüfung;
es wurde keine weitere automatisierte evdev-Aufnahme unter xpad gestartet.

industrialio blieb geladen, zuletzt Referenzzähler 0. Es wurde mangels
Entladefreigabe nicht entfernt. Kernel-Taint zuletzt 12292; das Entladen des
Testmoduls entfernt diese Markierung nicht. Keine dauerhafte Installation,
Firmware-/Profiländerung, native Motorausgabe, Deadband-Sitzung oder aktive
Identitätsumschaltung wurde im Test ausgeführt. Native 109c-IMU/Motoren,
gleichzeitiger Betrieb, Hotplug, Suspend/Reset und SDL/Steam bleiben offen.

## Dauerhafte Belege und Abschluss

Private Daten bleiben unter
`build/hardware-tests/001-continued-20261012T124928294422Z/`, außerhalb von Git.
Rohjournal enthält auch fremde Systeminformationen und wird nicht veröffentlicht.
Die Ereignisdatei `input-test-60s.jsonl` umfasst 17.046.391 Byte; SHA256:

```text
8302158c478b2d446220dc6c40a85a0c20b797b1137bb9f357bbfbe63dde04f0
```

Der geprüfte Eingabebericht ist `input-test-60s-reviewed.json`. Er korrigiert
eine unzutreffende Formulierung zur Schlussruhe im früheren abgeleiteten
Bericht; beide Dateien und die Originalaufnahme bleiben unverändert erhalten.
Die früheren Zwischenstände vor der Rückkehr sind keine Abschlussberichte.
`user-return-confirmation.json` und `hardware-test001-completion.json` ergänzen
die Nutzerbestätigung und den Abschluss. Alle 150 privaten SHA256-Einträge
wurden bei der Abschlussdokumentation verifiziert. Die kompakte versionierte
JSON-Zusammenfassung enthält Referenzen/Hashes, keine Rohaufzeichnung.

Die bestehenden Offline-Grundtests (`make test`) wurden beim Dokumentations-
abschluss erfolgreich ausgeführt: 44 Python-Tests sowie C-Sensor-/Protokoll-/
Runtime-, Mapping-, Fixture- und Entwicklerwerkzeug-Prüfungen. Dabei wurden
keine Hardwaregeräte geöffnet und kein Kernelmodul gebaut oder aktiviert.

Ergebnis: **Native 100a-Grundeingaben und kontrollierter Rückweg erfolgreich;
Schlussruhe und weitergehende Integration bleiben eingeschränkt/offen.**
Die Abschlussdokumentation verwendet gespeicherte Daten und Nutzerangaben;
keine weiteren Hardwarezugriffe oder Hardwareänderungen. Weitere Läufe
benötigen neue konkrete Freigaben nach dem [Hardwareplan](HARDWARE_TEST_PLAN.md).
