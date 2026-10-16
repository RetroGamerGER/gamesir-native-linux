SDL-Kompatibilität der geplanten GameSir-Sensorausgabe
=====================================================

Ergebnis, Stand 11. Oktober 2026
--------------------------------

IIO allein genügt für SDLs Linux-Gamepad-Sensorpfad nicht. Der native
Treiberentwurf benötigt zusätzlich ein separates Linux-Input-Sensorgerät.
Die installierte SDL-Bibliothek erkennt daran Gyro und Beschleunigung und
ordnet beide dem normalen Gamepad zu. Eine Änderung an SDL ist für diesen
evdev-Pfad nach den Offline-Tests nicht erforderlich.

Geprüft wurden SDL 3.4.18-1, Laufzeitrevision
SDL-release-3.4.18-0-g829a65d76, und SDL2-Compat 2.32.74-1,
Laufzeitrevision SDL-release-2.32.74-0-ge4df8a5. SDL2-Compat verwendet SDL3;
dies sind zwei API-Pfade, keine zwei unabhängigen SDL-Implementierungen.
Anwendungen mit mitgeliefertem SDL oder einem anderen Backend können sich
abweichend verhalten. Der Linux-Code der ursprünglichen SDL 2.32.10 hat
denselben evdev-Zuordnungsansatz; diese Version wurde nur gelesen.

Durchgeführter Test
------------------

Die unveränderten installierten Bibliotheken wurden mit eigenen, lokal
kompilierten Testprogrammen aufgerufen. Künstliche evdev-Antworten ersetzten
nur im jeweiligen Testprozess die Geräteaufrufe. Es wurde kein uinput-Gerät
erzeugt und kein echtes Gerät geöffnet. Ein vorhandenes erfolgreiches
IMU-Paket aus Messung B lieferte sechs reale Rohwerte; Gerätekennung,
Metadaten, Ereignisse, Auflösung und Beispielskalierung waren künstlich.
Die Skalen 8192 Einheiten/g und 16 Einheiten/(Grad/s) sind ausdrücklich
Testparameter und keine ermittelte G7-Pro-Kalibrierung.

Jeder Lauf erfolgte ohne erhöhte Rechte in Bubblewrap: alle sechs Namespaces
getrennt, alle fünf Capability-Sätze null, NoNewPrivs=1. /dev/input,
/dev/bus/usb, hidraw und usbmon waren nicht eingebunden. Das künstliche
/dev/iio:device0 war eine reguläre Datei. /sys enthielt ausschließlich
künstliche IIO-Attribute, /run war leer; damit waren auch Host-udev-Daten
ausgeschlossen. Nur Standard-Pseudogeräte waren vorhanden. Die Freigaben
für Messungen wurden nicht benutzt; es gab keine Aufnahme und keine
Kernel-, Treiber-, Rechte-, Deadband- oder Profileinstellung.

Je sechs Fälle über SDL3 und SDL2-Compat: 12/12 erfolgreich geprüft.
Ein erfolgreicher Negativtest bedeutet, dass SDL wie erwartet keinen
Sensor erkennt oder ungültige Daten liefert.

.. list-table:: Ergebnis für beide API-Pfade
   :header-rows: 1

   * - Fall
     - SDL-Ergebnis
     - Bedeutung
   * - Gamepad + IIO allein
     - kein Sensor
     - Kein direkter IIO-Import
   * - Input-Sensor, gleiche uniq
     - Gyro + Accel
     - Beide Werte korrekt umgerechnet
   * - Input-Sensor, andere uniq
     - kein Sensor
     - Zuordnung benötigt gleiche uniq
   * - Gyro-Achse ABS_RZ fehlt
     - nur Accel
     - Alle drei Achsen nötig
   * - Auflösung null
     - Gyro + Accel
     - Daten werden unendlich, unbrauchbar
   * - Gemeinsamer C-Umrechnungskern + künstliches evdev
     - Gyro + Accel
     - Künstlich vorgegebene 90 Grad/s und 1 g korrekt in SDL

Der zusätzliche Fall prüft die rationalen Faktoren, Vorzeichen und Bias des
gemeinsamen Umrechnungskerns bis zur SDL-Ausgabe. Auch sein Gyrofaktor
16.4 Zähler/(Grad/s) ist eine künstliche Referenz und kein G7-Pro-Messwert.
Die echte Skalierungs-/Achsenprüfung steht in SDL-SKALIERUNG-UND-ACHSEN.rst.

Die Positivfälle ergaben genau ein Gamepad. Die Sensor-Achsen wurden nicht
als weitere Stickachsen dieses Gamepads behandelt. GetGamepadSensorData
beziehungsweise GameControllerGetSensorData lieferte die erwarteten
umgerechneten Werte. Der Test erzwingt eine explizite Gamepad-Zuordnung,
deaktiviert HIDAPI und prüft den Linux-evdev-Pfad. Das validiert weder
SDLs Controllerdatenbank noch automatische Auswahl gegen konkurrierende
HIDAPI-Treiber, Geräteberechtigungen, Hotplug oder den fertigen Kernel-Treiber.

Folgerungen für den nativen Entwurf
---------------------------------

* Ein normales Gamepad-Input-Gerät für Tasten, Sticks, Trigger und FF_RUMBLE.
  INPUT_PROP_ACCELEROMETER darf an diesem Gerät nicht gesetzt werden.
* Ein getrenntes Input-Gerät für beide IMU-Sensoren, ohne Gamepad-Tasten:
  INPUT_PROP_ACCELEROMETER, ABS_X/Y/Z für Beschleunigung sowie ABS_RX/RY/RZ
  für Gyro. Beide Geräte bekommen dieselbe eindeutige, nicht leere uniq.
  Die Kennung muss je physischem Controller/Dongle verschieden sein und
  darf nicht bloß aus Hersteller- und Produkt-ID bestehen.
* Je Achse muss input_absinfo.resolution positiv und nachgewiesen sein:
  Einheiten/g für Beschleunigung, Einheiten/(Grad/s) für Gyro. SDL wandelt
  anschließend nach m/s² beziehungsweise rad/s um. Orientierung, Vorzeichen
  und Bias müssen zum dokumentierten SDL-Koordinatensystem passen.
* IIO bleibt ergänzend für rohe Werte und Analyse erhalten. Es ersetzt das
  Input-Sensorgerät für SDL nicht. Beide Ausgaben stammen aus demselben
  empfangenen Paket; kein zusätzlicher USB-Empfänger oder Deadband-Prozess.
* Bis Skalierung und Achsenorientierung verifiziert sind, wird kein
  kalibriertes Input-Sensorgerät veröffentlicht. Keine Auflösung null, keine
  aus dem Test übernommenen Skalen und keine erfundenen SI-Einheiten.
  IIO darf währenddessen die belegten Rohwerte anbieten.
* Host-Ereigniszeit und belegte Gerätezeit getrennt behandeln. Ohne belegte
  Geräteuhr keinen Gerätezeitstempel erfinden. MSC_TIMESTAMP ist optional
  und wird erst mit dokumentierter Zeitbasis verwendet.
* Sensoren separat aktivieren: SDL_SetGamepadSensorEnabled für SDL3 oder
  SDL_GameControllerSetSensorEnabled für SDL2. Erkennung allein aktiviert
  noch keine Sensorausgabe für ein Spiel.

Das ändert weder die vier unabhängig angesteuerten Motoren noch die geplante
versionierte Steuerungsschnittstelle für Deadband. Bestehendes Deadband
bleibt unverändert. Die spätere Zusammenarbeit soll über die native
Schnittstelle erfolgen, ohne den Gamepad-Treiber abzulösen.

Nachweis und Grenzen
-------------------

Die JSON-Datei sdl-validation/results.json enthält Paketprovenienz,
Testparameter, Befehle und Ergebnisse. Daneben stehen zwölf Laufprotokolle
mit Namespace-, Capability- und Geräteprüfung sowie das Übersetzungsprotokoll.
tests/run_sdl_sensor_test.py führt ausschließlich diesen gerätefreien
Test aus. Die Probeprogramme niemals unmittelbar auf dem Host starten.

Dies ist ein ausgeführter Bibliotheks-Kompatibilitätstest mit künstlichen
Geräteschnittstellen, kein Hardware- oder Kernel-End-to-End-Test.
Ein späterer ausdrücklich freigegebener Integrationstest muss zwei echte
Input-Knoten, die gemeinsame uniq, Berechtigungen, Hotplug, kalibrierte
Werte und gleichzeitige Gamepad-/Sensor-/Motorausgabe bestätigen.
Die 90-Sekunden-Messung A wird dadurch nicht freigegeben.

Primärquellen
-------------

SDL 3.4.18, geprüfter Linux-Backend-Stand:
https://github.com/libsdl-org/SDL/blob/829a65d769d935c4852f8159e964312c0957260a/src/joystick/linux/SDL_sysjoystick.c

Maßgebliche Funktionen: IsSensor, GetSensor, ConfigJoystick,
LINUX_JoystickOpen, LINUX_JoystickSetSensorsEnabled, HandleInputEvents.

SDLs Klassifizierung des Sensorgeräts:
https://github.com/libsdl-org/SDL/blob/829a65d769d935c4852f8159e964312c0957260a/src/core/linux/SDL_evdev_capabilities.c

Allgemeine SDL-Sensorbackends und Build-Auswahl (kein Linux-IIO-Backend):
https://github.com/libsdl-org/SDL/blob/829a65d769d935c4852f8159e964312c0957260a/src/sensor/SDL_sensor.c
https://github.com/libsdl-org/SDL/blob/829a65d769d935c4852f8159e964312c0957260a/CMakeLists.txt

Sensor-API und Einheiten:
https://wiki.libsdl.org/SDL3/SDL_GetGamepadSensorData
https://wiki.libsdl.org/SDL3/SDL_SensorType

Linux-Input-UAPI, lokal installierte Header:
/usr/include/linux/input.h, Kommentar vor struct input_absinfo.
Die Einheitenkonvention ist auch im offiziellen Linux-Header dokumentiert:
https://github.com/torvalds/linux/blob/v6.18/include/uapi/linux/input.h
