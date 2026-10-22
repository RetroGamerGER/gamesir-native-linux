# TMR-Kalibrierung: Controlleradapter offline vorbereitet

**Current follow-up:** The [scoped GUI and permission path](CONTROL_CENTER_TMR_PERMISSION.md)
is now implemented and tested offline. It has a distinct explicit continuity
contract; it does not attest physical RF lifetime. The normal app, published
AppImage, installed driver and default-off kernel feature remain unchanged.
The historical implementation scope below is retained for provenance.

**Fortsetzung:** Die [native TMR-Schnittstelle](TMR_NATIVE_INTERFACE.md) ist
inzwischen in Kernel und Manager offline implementiert, standardmäßig aus.
Das vollständige USB-Framing ist noch ein ungeprüfter Kandidat; die
Stream-Epoche beweist keine tatsächliche Funkidentität. Der folgende frühere
Adapterbericht bleibt als Herkunft des strengeren Channel-Vertrags erhalten.
Der normale GUI-Kanal ist weiterhin nicht für Hardware freigeschaltet.

Stand: 22. Oktober 2026. Fortsetzung der akzeptierten
[Offline-Vorschau](CONTROL_CENTER_STICK_CALIBRATION.md).
[Prüfergebnis und Quellen](evidence/CONTROL_CENTER_CALIBRATION_ADAPTER_20261022.json).

## Ergebnis und verbleibende Schnittstelle

Der neue Adapter verbindet den bestehenden Kalibrierablauf mit vollständigen
Controller-Statusberichten und den bekannten Kalibrieraufträgen. Er ist offline
mit einer speicherbasierten Gegenstelle geprüft. **Ein Livezugriff ist noch
nicht angebunden:** Der vorhandene native Treiber und Manager bieten dafür
derzeit keine passende Schnittstelle. Die GUI bleibt bei ihrer getesteten
Simulation; es gibt keinen neuen Live-Schalter.

Die Quellenprüfung zeigt konkret:

- `include/uapi/gs_native.h` und `kernel/gs_native_usb.c`: ABI 1 bietet Status,
  IMU-Samples, Motor-/Lebenszyklusbefehle und Input-Veröffentlichung. Sie bietet
  weder Stickkalibrieraufträge noch den vollständigen E0-Bericht für Userspace.
  `GSN_GET_SAMPLE` liefert IMU-Daten und ist kein Ersatz für diesen Bericht.
- `tools/service/gamesir_native.py`: Der Managementkanal akzeptiert Status,
  Release und Resume. Keiner davon ist ein Kalibrierauftrag oder eine exklusive
  Wartungsfreigabe. Die Haptikschnittstelle ist ebenfalls kein Kalibrierkanal.
- `gs_native` besitzt im Normalbetrieb Interface 0 und die gemeinsame
  IN-/OUT-Kommunikation. Ein unabhängiger USB-Schreiber würde diese Zuständigkeit
  umgehen. Dafür wird kein automatisches Ablösen, zusätzlicher Sequenzzähler
  oder allgemeiner USB-Passthrough eingebaut.

`ControllerCalibration` hat deshalb standardmäßig einen `UnavailableChannel`.
Schon die Anforderung einer Verbindung endet dort ohne Dateizugriff, Socket,
Geräteöffnung oder Schreibversuch. Das ist eine offen ausgewiesene fehlende
Live-Schnittstelle, keine weitere Forderung nach einer Speicherquittung.

## Was implementiert ist

`tools/control_center/calibration_protocol.py` enthält eigene reine Codecs;
`calibration_controller.py` bindet sie an den vorhandenen Sitzungsablauf.
Sie führen weder Firmware noch Hersteller-Code aus. Keine neue Abhängigkeit,
kein importierter Drittcode und keine proprietären Dateien. GPL-2.0-only.

| Teil | Offline implementiertes Verhalten |
|---|---|
| Gerätezuordnung | Genau eine explizite native GameSir-Instanz: VID, PID, Kernel-Port-/Instanztoken, Geräte-/Funklebensdauer und lokale Durchlaufgeneration |
| Native Varianten | `109c` und `105e` können beschrieben werden; positive Wartungs-/Streamfreigabe bleibt zusätzlich nötig. PID allein aktiviert nichts |
| Wartung | Ausschließlich eine passende, exklusive und zeitlich begrenzte Besitzerfreigabe akzeptieren; vor und nach jedem Auftrag frisch prüfen |
| Stickdaten | Unveränderte Roh- und verarbeitete Acht-Bit-Positionen getrennt lesen; ausdrücklich gewählte Anzeigequelle/Achsenvorzeichen |
| Fertigmeldung | Aktiv- und Fertigbits beider Sticks an den bestehenden Ablauf übergeben; keine Ableitung aus grüner Kreisabdeckung |
| Aufträge | Nur Start/Finish/Exit; Reihenfolge und einmalige Verwendung pro Durchlauf prüfen |
| Abbruch | Exit einmal an dieselbe noch bestätigte Instanz; bei Verlust/unklarem Versand keine automatische Wiederholung |
| Fehler | Erste Ursache behalten; Fehler bei der Besitzer-Rückgabe getrennt melden und neue Sitzung bei ungeklärtem Besitz blockieren |

## Byte- und Datenvertrag

Die [Nexus-/Provideranalyse](NEXUS_STICK_TRANSPORT.md) belegt folgende Inhalte
an der internen GIP-Providergrenze:

| Auftrag | Nachrichtentyp | Drei Nutzbytes |
|---|---:|---|
| Start beider Sticks | `0x0f` | `fe 00 03` |
| Finish | `0x0f` | `fe 01 00` |
| Exit | `0x0f` | `fe 02 00` |

`calibration_message()` erzeugt **nur diese internen Inhalte**. Es setzt keine
USB-Endpunktadresse, Sequenz, Rahmenoption, Länge oder Auffüllung dazu.
Der Adapter behauptet nicht, dass ein Windows-Provider unter Linux verfügbar
wäre. Seine Channel-Grenze ist ein vorgeschlagener lokaler Eigentümervertrag;
eine spätere Implementierung muss die noch offene
[Provider-/USB-Grenze](NEXUS_STICK_WIRE_PATH.md) belegen und die gemeinsame
Ausgabeserialisierung des Treibers benutzen.

Der Eingangsparser verlangt den vollständigen 64-Byte-Bericht mit Typ `0x10`,
Option null, Länge `0x3c` und Marker `0xe0`. Er liest:

- verarbeitete Stickpositionen aus Bytes 5–8 und Rohpositionen aus 51–54,
  entsprechend dem vorhandenen [Protokollbefund](PROTOCOL.md);
- Stick-Aktivmaske aus Byte 30 und Fertigmaske aus Byte 31, entsprechend
  [Firmware-/Nexus-Rückmeldepfad](NEXUS_STICK_READBACK.md);
- das Draht-Sequenzbyte unverändert als Zusatzinformation. Sein Überlauf
  `255 → 0` wird nicht als rückwärts laufende Host-Sequenz interpretiert.

Die Statuspositionen sind **voller Bericht 30/31**, nicht Nutzteil 26/27 oder
Tastenbytes. Aktive Trigger-/Motion- oder unbekannte Kalibrierbits führen in
diesem begrenzten Stickadapter zum Stopp. Abgeschnittene, aufgefüllte oder
unbekannte Rahmenformen werden nicht als gültiger E0-Status akzeptiert.
Andere normale Gamepad-/Guide-/Herstellerantworten setzen keine Bereitschaft
und frischen den E0-Datennachweis nicht auf.

Die Anzeige normiert Acht-Bit-Werte ohne Deadzone auf `[-1,1]`: 0 → −1,
128 → 0, 255 → +1. Roh-/verarbeitete Quelle und vier Vorzeichen müssen explizit
gewählt werden. Das ist eine **Anzeigepolitik**, keine Änderung/Berechnung der
Kalibrierwerte und kein bestätigter Achsennachweis während echter Kalibrierung.
Der gespeicherte E0-Mitschnitt bestätigt das bestehende normale Layout und
Null-Statusfelder; er ist kein Mitschnitt eines Kalibrierdurchlaufs.

## Besitzer- und Verbindungsvertrag

Die vorgeschlagenen Channel-Aufrufe `acquire`, `inspect`, `send_message` und
`release` existieren derzeit nur als injizierter Vertrag mit Testgegenstelle.
Die Capability-Namen sind **keine heute vorhandene Kernel-/Manager-ABI**.
Ein passender Rückgabedatensatz ersetzt weder einen vertrauenswürdigen lokalen
Dienst noch dessen Berechtigungsprüfung; der Adapter prüft nur dessen Vertrag.

Eine Freigabe muss exakt zum angefragten Gerät und Durchlauf passen, verbunden
und exklusiv sein, `gs_native` als Besitzer und alle benötigten Fähigkeiten
ausweisen sowie eine noch gültige monotone Ablaufzeit haben. Die Funklebensdauer
muss aus tatsächlicher Verbindungsbeobachtung kommen. Dongle-Anwesenheit und
gleichbleibende USB-Kerneltoken reichen dafür nicht aus. Beim Wechsel der
Funklebensdauer am gleichen USB-Port werden alte Aufträge ebenfalls verworfen.

Jeder Eingangsdatensatz ist mit derselben Freigabe und Instanz gekennzeichnet.
Eine lokale, monotone Berichtsnummer und der echte monotone Empfangszeitpunkt
gehören zum zukünftigen Adaptervertrag; sie dürfen nicht beim GUI-Abruf neu
erzeugt werden, um alte Daten frisch erscheinen zu lassen. Fremde oder
veraltete Datensätze verändern weder Anzeigezustand noch Bereitschaft.

Nach dem Besitzererwerb wartet der Adapter zunächst begrenzt auf den ersten
Bericht; vorher bleibt Start gesperrt. Ein früher Timeraufruf bedeutet noch
keinen Verbindungsverlust. Nach Ablauf des Wartefensters wird auch ein erst
danach eintreffender erster Bericht nicht in den alten Durchlauf übernommen.

Die bisherige 1,5-Sekunden-Regel für ersten/ausbleibenden E0-Status bleibt eine
konservative Offline-Regel. Die Firmware kann unveränderte Berichte unterdrücken. Vor Live-
Betrieb müssen deshalb tatsächliches Streamverhalten, positiver Funknachweis
und Aktualität der Statusfelder zusammen geprüft und die Frist gegebenenfalls
angepasst werden. Es wird kein erfundener Geräte-Heartbeat gesendet.

Sendeerfolg bedeutet nur unmittelbare Annahme durch den vorgeschlagenen lokalen
Owner. Es wird keine zusätzliche Flash-/Speicherbestätigung verlangt. Finish
bleibt Aufgabe der Firmware; ein Verlust während des Aufrufs kann trotzdem
einen bereits angenommenen Auftrag bedeuten. Die Wiederholung bleibt gesperrt.

Beim Abschluss/Abbruch wird nur die eigene Wartungsfreigabe zurückgegeben.
Das ist kein automatischer Release/Resume, Treiberwechsel oder USB-Moduswechsel.
Ist diese Rückgabe nicht bestätigt, bleibt die alte Freigabe im Adapter offen;
er versucht sie nicht in einer Schleife erneut. Bei unklarer oder falsch
zugeordneter Erwerbsantwort wird kein fremdes Gerät freigegeben und kein neuer
Erwerb automatisch begonnen. Ein echter Dienst muss unbestätigte Freigaben
selbst zeitlich begrenzen und einen überprüfbaren Rückweg bieten.

## Nächste getrennte Implementierung

Für den späteren Livebetrieb ist eine **gezielte native Wartungsschnittstelle**
nötig: die drei begrenzten Stickoperationen und der passende E0-Statusstrom,
mit instanzgebundenem Besitzer, gemeinsamer Sequenz-/Ausgabeordnung und echter
Funk-Verlustmeldung. Der Manager muss konkurrierende Wartung und Haptik während
des Durchlaufs ausschließen und die Berechtigung des lokalen Nutzers prüfen.
Die bestehende Paket-/Installationsberechtigung wird dafür nicht umgenutzt.

Kernel, Manager, UAPI und Berechtigungshelfer wurden in diesem Schritt nicht
geändert. Keine Geräte geöffnet oder neu gebunden; kein `sudo`, USB-Zugriff,
Dienstkommando, Moduswechsel, Netzwerk, Installation oder Hardwaretest.
Keine Firmware ausgeführt oder geflasht. Die bereits laufende Vorschau und
beide installierten Treiber bleiben im bisherigen Betrieb.

## Tests

```sh
python3 -B tests/test_calibration_controller.py
make test-control-center PYTHON=python3
make test-control-center-ui PYTHON=python3
```

35 neue Tests prüfen unter anderem die drei internen Nutzinhalte, Feldpositionen,
alle Acht-Bit-Anzeigeendpunkte, falsche Rahmenlängen/Optionen, andere
Kalibrierteile, beide beschriebenen Modelle, fremde Instanzen, USB- und
Funklebensdauerwechsel, alte Antworten, Sequenzüberlauf, Sendefehler, unklare
Besitzerzuordnung und Erhaltung der ersten Fehlerursache. Ein gespeicherter
normaler Bericht dient als unabhängiger Layoutvergleich. Alle übrigen
Antworten/Gegenstellen sind synthetisch, ohne Firmwareemulation.

Datei-/Socket-/Prozess-/ioctl-Zugriffe sind im Defaultpfad und im vollständigen
injizierten Ablauf zusätzlich durch Test-Sperren ausgeschlossen. Die bestehende
GUI-/Paket-/Fensterlebensdauer-Suite bleibt Teil der Regression. Das ist keine
Hardwareabnahme und keine Freigabe eines installierbaren Treiberupdates.

Ergebnis: **411 Control-Center- und 79 Qt-/Lebenszyklustests bestanden**,
insgesamt 490 Fälle, darunter die 35 neuen Adaptertests. Zusätzlich bestanden
drei Lizenz-, sieben README- und 16 Nexus-Ablaufmodelltests. Die bereits
dokumentierte Kernpaket-Dokumentationslücke zur ZZZ-Abnahme wurde hier nicht
verändert und ist kein behaupteter erfolgreicher Kernpaket-Releasecheck.
