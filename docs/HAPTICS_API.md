# Lokale Viermotor-Schnittstelle — experimentelle Version 1

Der native Kernel bleibt alleiniger USB-Besitzer. Der bestehende Root-Manager
enthält jetzt einen lokalen Haptik-Broker; Spiele sprechen mit diesem Broker
über einen Unix-Socket. Die Schnittstelle erzeugt weder Linux-FF-Effektcodes
für Impulse-Trigger noch eine vermeintlich vorhandene SDL-Trigger-Unterstützung.
Ein Spiel oder Adapter muss diese API ausdrücklich integrieren.

Implementiert und offline getestet: vier unabhängige Amplituden, vom Programm
bestimmte endliche Dauer, einzelne Kanalstopps, Verbindungsbesitz, Wiederverbindungs-
schutz und begrenzte Hardwarebefehle. Die integrierte Anwendungskette benötigt
noch ihre eigene Hardwareabnahme. Eine getrennte projektinterne Forza-/Xodus-
SDL2-Bridge meldet inzwischen fühlbare LT-/RT-Spieleffekte über diesen Broker.
Ihre abgesicherte [Integration](TRIGGER_BRIDGE.md) ist nur offline geprüft;
Steam/Proton, Reconnect und Suspend sind dadurch nicht belegt. Die früheren
manuellen Viermotor-Nachweise belegen die zugrunde liegenden USB-Pakete.

## Zugriff

- Socket: `/run/gamesir-native-haptics/control.sock`.
- Verzeichnis: `root:gamesir-native-haptics`, Modus `0750`.
- Socket: `root:gamesir-native-haptics`, Modus `0660`.
- Die dedizierte Gruppe erlaubt ausschließlich diese lokale Motor-API. Sie gibt
  weder USB-/Input-Gerätezugriff noch Root- oder Manager-Steuerungsrechte.
- Die eigene Root-Steuerung `gamesir-native release/resume` bleibt getrennt.
- Die Paketierung legt die Gruppe an. Ein Benutzer muss bei der später ausdrücklich
  freigegebenen Installation einmal gezielt hinzugefügt werden und neu anmelden.
  Während der Offline-Entwicklung wurde keine Gruppe oder Mitgliedschaft verändert.
- Fehlt die Gruppe oder ist der Socketpfad unsicher, meldet der Manager
  `haptics_unavailable`; der normale Gamepad-Dienst kann weiterlaufen.

Die Dateirechte begrenzen die Verbindung auf berechtigte lokale Prozesse.
`SO_PEERCRED` liefert dem Broker die tatsächliche Benutzerkennung. Eine Anwendung
kann kein USB-Paket, keinen beliebigen ioctl und keinen Gerätepfad übergeben.
Die Anwendungskennung ist ein SHA256-basierter undurchsichtiger Instanzwert;
er enthält keine nach außen sichtbare Seriennummer und ist keine Hardware-UID.

## Drahtformat

UTF-8-JSON, genau eine Zeile pro Nachricht. Jede Anfrage enthält `version: 1`
und `op`. Antworten enthalten `version`, `ok` und bei Fehlern `error`.
Unbekannte oder fehlende Felder werden abgewiesen. Begrenzungen: 4.096 Byte pro
Anfrage, 8.192 Byte ausstehende Antworten pro Verbindung, 16 gleichzeitige
Verbindungen und 50 Anfragen pro Sekunde je Verbindung.

| Operation | Zusätzliche Pflichtfelder | Bedeutung |
|---|---|---|
| `list` | keine | Aktive native Instanzen, Anzeigename, Port und Manager-Auslastung |
| `heartbeat` | keine | Anwendungslease um zwei Sekunden verlängern; `last_error` abfragen |
| `play` | `instance`, `amplitudes`, `duration_ms` | Gewählte Kanäle setzen; noch keine mechanische Bestätigung |
| `stop` | `instance`, `mask` | Gewählte eigene Kanäle stoppen; Maske `1..15` |
| `release` | `instance` | Eigene Kanäle stoppen und Anwendungsbesitz freigeben |

Kanalreihenfolge und Masken:

| Index | Maske | Motor |
|---|---|---|
| 0 | 1 | linker Trigger |
| 1 | 2 | rechter Trigger |
| 2 | 4 | linker Griff |
| 3 | 8 | rechter Griff |

`amplitudes` enthält genau vier Werte: Ganzzahlen `0..100` oder `null`.
Null Prozent stoppt den Kanal, `null` lässt seinen bisherigen Wert und seine
Ablaufzeit unangetastet. Mindestens ein Kanal muss angegeben werden.
`duration_ms` ist eine Ganzzahl von `1` bis `4294967295` und gilt ausschließlich
für die in dieser Anfrage gesetzten Kanäle. Jeder Kanal besitzt seine eigene
Ablaufzeit; eine Änderung am linken Trigger verlängert nicht den rechten.
Damit sind beispielsweise fünf Sekunden, eine Minute oder eine Stunde möglich.
Boolesche Werte, negative Werte und nichtganzzahlige Angaben werden abgewiesen.

Die erste `play`-Anfrage reserviert die Geräteinstanz exklusiv für diese
Socketverbindung. Eine zweite Verbindung kann sie erst nach Freigabe oder
abgeschlossener Bereinigung übernehmen. Ein Ersatzdongle am selben Port besitzt
eine andere Instanzkennung. Ein altes Anwendungshandle wird nicht automatisch
auf dieses Gerät übertragen; die Anwendung muss erneut `list` verwenden.

## Dauer und Ausfallsicherung

Die vom Spiel gewünschte Dauer wird nicht auf eine Sekunde beschnitten.
Der Broker übersetzt sie in erneuerte Einzelpakete mit höchstens 1.000 ms Dauer
und erneuert aktive Kanäle normalerweise nach 400 ms. Nahe dem gewünschten Ende
wird nur die tatsächlich verbleibende Dauer kodiert.

Unabhängig davon muss die Anwendung ihre Zwei-Sekunden-Lease erhalten.
Die Python-Bibliothek übernimmt dies mit einem Heartbeat-Thread im Abstand von
500 ms. Verbindungsende, abgelaufene Lease, Protokollüberlastung oder ein
abgewiesener Gerätezustand verhindern weitere Erneuerungen und veranlassen
kanalbezogene Stopps. Kann der Broker gerade nicht auf seinen privaten
Steuer-FD zugreifen, laufen die bereits gesendeten begrenzten Pakete ab.
Es gibt keinen unbegrenzt laufenden, unverwalteten Motorauftrag.

Diese Fristen sind Software-/Protokollgrenzen. Eine zeitliche Echtzeitgarantie
für mechanische Wirkung oder einen blockierten Kernel wird daraus nicht abgeleitet.

Der Broker teilt den Manager-Zustand und verwendet kurze Root-Steuer-FDs nur,
wenn keine andere Manageroperation diesen Zugang benötigt. Bootstrap, END,
PM-Wiederaufnahme oder ein Deadband-`release` können somit nicht durch einen
zweiten konkurrierenden Steuerdienst überlagert werden. Bei Pause, Fehler oder
Gerätewechsel werden alte Haptikzuordnungen verworfen, ohne Ersatzgeräte anzusprechen.

## Kernelvertrag und Standard-FF

Es wird ausschließlich die vorhandene private ABI 1 mit `GSN_PULSE` verwendet:
32-Byte-Struktur, `motor=0..3`, `percent=1..100`, `duration_ms=1..1000`,
`flags=0`, Reserven null. Ein individuelles Ende verwendet die definierte
Erweiterung `GSN_PULSE_CANCEL=1`, Prozent und Dauer null; dies ist keine neue
Linux-FF-UAPI. Details: [Kernelvertrag](FOUR_MOTOR_KERNEL.md).

Der Kernel unterscheidet den jeweils letzten privaten beziehungsweise
Standard-FF-Schreiber. Ein Broker-CANCEL entfernt keine neuere, von normalem
FF_RUMBLE gesetzte Griffwirkung. Bei konkurrierenden Nichtnull-Aktualisierungen
gilt für denselben Motor der letzte Schreiber. Für Standard-FF an den Griffen
plus private Impulse-Trigger sollte die Anwendung in dieser API nur die
Triggerkanäle setzen und beide Griffwerte auf `null` belassen.

Die Rückgabe `accepted: true` bedeutet einen angenommenen Anwendungsauftrag.
Sie beweist weder einen abgeschlossenen USB-Transfer noch fühlbare Vibration.
Backendfehler erscheinen im nachfolgenden Heartbeat als `last_error`; die
Clientbibliothek beendet dann die Verbindung und erneuert keine Motoren mehr.

## Python-Integration

`tools/haptics/gamesir_haptics.py` benötigt ausschließlich die Python-
Standardbibliothek. Das Modul kann als Anwendungskomponente importiert werden;
die Paketierung stellt außerdem eine Kopie unter
`/usr/lib/gamesir-native/gamesir_haptics.py` bereit. Dieser Importpfad wird nur
für die betreffende Anwendung gesetzt; kein globales `PYTHONPATH` wird verändert.
Beispiel für eine spätere autorisierte
Anwendung, hier nicht ausgeführt:

```python
from gamesir_haptics import Client, LEFT_TRIGGER, RIGHT_TRIGGER

with Client() as haptics:
    devices = haptics.devices()
    instance = devices[0]["instance"]  # Anwendung soll die Auswahl sichtbar anbieten.
    haptics.set_motor(instance, LEFT_TRIGGER, 75, 5000)
    haptics.set_motor(instance, RIGHT_TRIGGER, 40, 60000)
    # Die normale Ereignisschleife des Spiels läuft hier weiter.
    # haptics.stop(instance, mask=1) beendet nur den linken Trigger.
```

Das Verlassen des Kontextes schließt die Verbindung und beendet ihre Wirkungen.
Lange Effekte setzen daher voraus, dass der Anwendungskontext bestehen bleibt.
Die Bibliothek lädt keine Module, öffnet keine Geräte und startet keine
Passwortabfrage. Eine fehlende Gruppenberechtigung führt zu einem normalen
Verbindungsfehler, niemals zu automatischer Rechteerhöhung.

## Offline-Nachweise

`python -B tests/test_service_haptics.py` prüft Broker, Schnittstelle,
virtuelle Zeit, echte lokale Socketpuffer sowie den realen Python-Client gegen
künstliche Backends. Der direkte Root-Adapter wird mit abgefangenen Datei-/
ioctl-Aufrufen geprüft: ausschließlich der erwartete private Opcode,
korrekte 32-Byte-Payloads, keine START-/USB-Passthrough-Aufrufe und Ablehnung
ungültiger Anforderungen vor dem Öffnen eines Geräts.

Hardwaretests bleiben gesondert freizugeben: Anwendung → Broker → nativer
Treiber → vier fühlbare unabhängige Motoren, lang laufende Effekte, Clientabbruch,
konkurrierendes Standard-FF, USB-Abziehen und Suspend/Resume.
