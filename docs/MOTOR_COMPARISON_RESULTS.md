> Public export: personal tester, host and path references were anonymized. Historical evidence hashes refer to the private originals.

# Aufgezeichneter Deadband-Motorvergleich

Historischer Bericht zum Deadband-Lauf. Der anschließend separat freigegebene
native Ein-Sekunden-Vergleich ist inzwischen ebenfalls erfolgreich abgeschlossen:
[nativer Ergebnisbericht](NATIVE_MOTOR_COMPARISON_RESULTS.md). Die folgenden
Befunde und damaligen offenen Fragen bleiben als ursprünglicher Stand erhalten.

12. Oktober 2026, 16:52:18–16:56:48 UTC (18:52–18:56 MESZ).
Der separat freigegebene Lauf aus `3c64312` ist abgeschlossen. [tester] bestätigt:
**Alle zwölf Impulse waren spürbar und endeten wieder. Normale Eingaben
funktionieren anschließend im KDE Center.** Hardwaretest 002 bleibt wegen der
noch ungeklärten nativen linken Griffvibration offen.

## Aufnahme und Rückkehr

Privater Originalordner, relativ zum bisherigen Arbeitsbereich:
`outputs/sprint-002/captures/20261012T165154770784Z-motor-comparison-deadband/`.
`original-usbmon8.pcapng`: 1.067.005.244 Byte, SHA256
`140c658b3615a7aa9e04571503d9f4fe1cb13df000ef3f8cb35cec91533ae954`.
Originale, Quellen, Ansagen, Vor-/Nachprüfungen und ursprüngliche Prüfsummen
bleiben unverändert. Rohdaten anderer Busgeräte bleiben privat. Zielauszüge
liegen dort in `derived/`; strenge Motorprüfung und weitere Nachweise in
`build/motor-comparison-20261012T165154770784Z/` im Git-Projekt.
Kompakte, geprüfte Zielgerätedaten und Quellenhashes:
[MOTOR_COMPARISON_RESULTS.json](MOTOR_COMPARISON_RESULTS.json).
57 ursprüngliche Belegdateien wurden gegen das unveränderte SHA256-Manifest
geprüft. Ableitungen und Abschlussauswertung haben eigene zusätzliche Manifeste.

Die isolierte dumpcap-Kette endete mit Status 0. Sechs Namespaces, fünf leere
Capability-Sätze, NoNewPrivs=1 und ausschließlich usbmon8 sind nachgewiesen;
kein `/dev/bus/usb` in der Sandbox. Keine verbliebenen Recorderprozesse oder
Monitor-FDs. Host-Mounts, Namespaces und Geräteknoten blieben unverändert.
Deadband wurde regulär geschlossen.

| Zeitpunkt | Identität am Port 8-6, Bus 8 | Interface 0 / 1 |
|---|---|---|
| vorher | 3537:100a, Adresse 27 | xpad / usbhid |
| Deadband | 3537:109c, Adresse 28 | usbfs / ungebunden |
| nachher | 3537:100a, Adresse 29 | xpad / usbhid |

Dies sind gespeicherte Beobachtungen dieses Laufs. gs_native war nicht geladen;
usbmon und industrialio wurden anschließend nicht automatisch entladen.
Die anschließende Auswertung arbeitet ausschließlich offline.

## Pakete und Wahrnehmung

| Motor | Erfolgreiche Start-/Stopp-Paare | Vom Nutzer gespürt und beendet |
|---|---:|---:|
| Linker Griff | 3 | 3 |
| Rechter Griff | 3 | 3 |
| Linker Trigger | 3 | 3 |
| Rechter Trigger | 3 | 3 |

Alle 24 Motorübertragungen: vollständige 13-Byte-Nutzdaten, passende
Submit-/Completion-Zuordnung über Epoche/Endpunkt/URB-ID, Completion-Status 0
und übertragene Länge 13. Jeder Start hat einen eigenen folgenden Nullstopp
innerhalb seines Testfensters; keine zusätzlichen Motorpakete oder Überlappung.
Sequenzen durchgehend 1–24. Je Start ein Motorwert 100, die übrigen null,
Dauer 40 × 10 ms, Pause/Wiederholung null. Stopps: alle Motorwerte und Dauer null.

**Alle 24 Pakete stimmen bytegenau mit dem frisch als Userspace-Code
kompilierten nativen C-Encoder überein**, bei gleicher Sequenz und gleichen
Motorwerten. Der frühere native Hardwarelauf hat keine USB-Rohaufnahme;
dessen tatsächlich gesendete Bytes sind damit nicht nachgewiesen.

- Start-Submit bis Stopp-Submit: 413,984–418,052 ms.
- Start-Completion bis Stopp-Submit: 410,082–416,134 ms.
- Abstand aufeinanderfolgender Starts: 7,918–11,558 s.
- Paketbeginn nach protokollierter Ansage: 0,598–2,899 s.

USB-Zeiten messen keine mechanische Impulsdauer. Ansagezeiten stammen aus dem
Helfer, nicht aus einer Messung der sichtbaren Benachrichtigung. Die gesonderte
Nutzerbestätigung spricht gegen einen dauerhaften linken Motorausfall;
die Ursache des stummen nativen Impulses ist weiter ungeklärt.

## Qualität und Grenzen

198.207 Busereignisse, davon 26.648 anhand Bus/Port/Adresse/Zeit zugeordnete
Zielereignisse. PCAPNG/USB_LINUX_MMAPPED, Mikrosekunden-Zeitauflösung,
270,005003 s zwischen erstem und letztem Paket. Keine gekürzten Frames.
Interface-Zähler: `ifdrop=0`, `ifrecv=198207`; fehlender Betriebssystem-
Dropzähler bedeutet unbekannt. Enumeration vor Zuordnung einer neuen Adresse
und Adresse 0 bleiben im Original, nicht pauschal im Zielauszug.

Neun Zielereignisse mit nicht erfolgreichem Completion-/Error-Status:
fünfmal `-ESHUTDOWN` (-108), viermal `-ENOENT` (-2). Alle liegen in den
Start-/Schließfenstern (etwa T+38–40 und T+237–240 s), außerhalb der
Motorprüfungen. Darunter ein OUT-Error beim Start. Der nutzdatenorientierte
Parser zählt sieben dieser Ereignisse als `transfer_error`, die vollständige
USB-Ereignisprüfung neun. Kein pauschaler Erfolg aller USB-Transfers behauptet.

Parser: 13.305 Datensätze, 13.275 dekodiert, sieben ignorierte Fehlerdatensätze,
23 unbekannte. Darunter 12.364 IMU-Telemetriepakete und ein GIP-Gamepadpaket.
IMU-Hostintervalle median 16 ms, beobachtet 62,517 Hz; keine Aussage zur
internen Sensor-ODR oder Gyro-Skalierung. Neun `x360_rumble_output`-Datensätze
sind bekannte `00 08`-Übergangspakete, keine weiteren Motortests.
Keine erkannten Profil-Schreibbefehle. Kein vollständiger Gamepad-Abdeckungstest.

## Native Abweichung und nächster Vorschlag

Im nativen Lauf aus `743407f` wurde der linke 100-%-/400-ms-Impuls akzeptiert,
der explizite STOP folgte nach etwa 603 ms. Gamepad/IMU liefen weiter, ohne
gemeldeten Treiberfehler. Falscher Kanal oder vorzeitiger expliziter STOP
sind anhand dieser Daten nicht belegt. Das genaue native USB-Timing fehlt.

Konkrete Vergleichsvariable im Quellcode: gs_native teilt einen Sequenzzähler
für Init, Heartbeat und Motoren (`kernel/gs_native_usb.c`). Deadband trennt
`_gip_seq` für Motoren von `_g7_seq` für Vendor-/Heartbeatbefehle
(`vendors/gamesir/control.py`, Stand 771b28a).
**Dass dies den linken Motor blockiert, ist eine Hypothese.** Kein spekulativer Fix.

[tester] wünscht mehr Zeit pro Motor. Vorschlag für einen späteren **nativen**
Vergleich mit isolierter USB-Aufnahme: 30 s Vorbereitung, vier Motorblöcke
à 60 s und 30 s Abschluss = 300 s Testsitzung. Reihenfolge linker Griff,
rechter Griff, linker Trigger, rechter Trigger. Je Block Ansage am Anfang,
Impulse bei +15/+30/+45 s: dreimal 100 % / 400 ms, bestätigter expliziter STOP
nach 0,6 s und Pause bis zum nächsten Puls. Die zusätzliche Aufnahmezeit muss
Übergabe und Rückkehr mit abdecken.

**Vorschlag, noch nicht implementiert oder freigegeben.** Der Helfer erlaubt
derzeit vier Impulse/120 s, der Client maximal 120 s, der Kernel 135 s.
Erst offline eine begrenzte Variante, Sitzungsgrenzen und Eingabefenster prüfen.
Die bisherige Eingabefrischeprüfung verlangt fortlaufende Stickbewegung;
Rückmeldepausen dürfen diese Pflicht nicht unbemerkt behalten. IMU-, Identitäts-,
Fehler- und Stoppkontrollen bleiben erforderlich. Die Impulse bleiben vorerst
bei 400 ms, damit Dauer und Ablauf nicht gleichzeitig verändert werden.
Längere Einzelvibration wäre eine eigene Encoder-/Grenzen-/Teständerung.

Frischer Vorabcheck und konkrete Freigaben für Aufnahme, Modulladen, Übergabe,
Motorlauf und Rückweg bleiben erforderlich. Keine automatische Wiederholung.
Kontrollierte Rückkehr zu 100a/xpad und KDE-Funktionsbestätigung einplanen.
Keine dauerhafte Installation freigegeben.
