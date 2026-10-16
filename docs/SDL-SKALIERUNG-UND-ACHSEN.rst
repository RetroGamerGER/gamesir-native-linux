G7 Pro: Skalierung und Achsenorientierung für SDL
================================================

Ergebnis der Offline-Prüfung, 11. Oktober 2026
--------------------------------------------

Die Kanalbelegung und Rohdaten sind belegt. 8192 Zähler/g ist ein gut
passender Kandidat für die Beschleunigungsskalierung. Eine verifizierte
physikalische Gyroskalierung und die vollständige vorzeichenrichtige
Zuordnung zum SDL-Koordinatensystem lassen sich aus diesen Quellen jedoch
nicht bestimmen. Deshalb ist noch kein vollständiges SDL-Kalibrierprofil erstellt.
Auf ausdrückliche Nutzeranweisung ist 8192 Zähler/g inzwischen als
experimenteller, austauschbarer Beschleunigungswert implementiert und
gegen alle gespeicherten IMU-Pakete geprüft. Dieser Entwicklungspfad
benötigt keine Chipidentifikation. Details und aktueller Testnachweis:
EXPERIMENTELLE-BESCHLEUNIGUNG.rst und experimental-accel-validation.json.
Das ist eine Grenze der Kalibrierdaten, keine erneute Machbarkeitsprüfung
von Deadbands bereits praktisch bestätigten Funktionen.

Geprüfte Quellen und Integrität
------------------------------

Ausgewertet wurden alle 12204 erfolgreichen 64-Byte-IMU-Pakete der
abgeschlossenen Messung B, Identität 3537:109c über den Funk-Dongle.
Die Rohwerte wurden unabhängig erneut aus den gespeicherten Paketbytes
gelesen und gegen die vorhandene Telemetrie-Auswertung verglichen.
Original-PCAPNG, Telemetrie, Parserdaten und Phasenprotokoll wurden anhand
der vorhandenen SHA256-Werte geprüft. Die Originaldateien wurden nicht geändert.

Original-SHA256:
4045577a7a9e7a1a0f84307a45e96fd524cd7dea1d4af276ebd7db20a0994a89

Deadband-Stand: 771b28ae75b0a614a6a7fec9aa606606a27b3b8d.
Decoder, Reader, Bridge, Zustandsdefinition und Sensoranzeige im gespeicherten
Quellstand sind bytegleich mit den entsprechenden installierten Dateien.
Die Anwendung wurde weder gestartet noch importiert oder verändert.
Fundstellen und Prüfsummen stehen in imu-calibration-analysis.json.
Die ergänzte Gesamtstatistik und der Stand der Chipidentifikation stehen in
IMU-STATISTIK-UND-SENSORIDENTIFIKATION.rst; die Grafik imu-statistik.png zeigt
alle Samples sowie die getrennt ausgewählten ruhigen Fenster.

Was Deadband tatsächlich umrechnet
---------------------------------

protocol.py, parse_input, liest drei signed little-endian 16-Bit-Kanäle
ab Byte 17 als Gyro und drei ab Byte 23 als Beschleunigung. Der Decoder
kennzeichnet Skalierung und physikalische Orientierung ausdrücklich als
unkalibriert. reader.py reicht gültige Berichte an diesen Decoder.
bridge.py, _poll_sensors, übernimmt die Tupel ohne Achsentausch, Vorzeichen-
änderung, Bias-Korrektur oder physikalischen Faktor.

MotionSensors.qml bezeichnet die Anzeige als Rohzählwerte. Die Beschriftung
X/Y/Z entspricht lediglich den drei Arraypositionen. Division durch 32768
dient der Balkenbreite und ist keine Umrechnung in g, Grad/s oder rad/s.
Die Motion/Aim-Einstellungen für Empfindlichkeit, X-Achse und Invertierung
betreffen das im Controller konfigurierte Gyro-zu-Stick-Verhalten. Sie
belegen keine Kalibrierung der separat übertragenen Roh-IMU.
Auch Deadbands Tests prüfen die unveränderten Rohwerte; die dort verwendete
Zahl 8192 ist kein Nachweis eines physikalischen Sensormaßstabs.

Belegte Rohkanäle und Ruhewerte
------------------------------

.. list-table:: Paketpositionen, nullbasierte Bytes
   :header-rows: 1

   * - Gruppe
     - Rohkanäle
     - Beleg
   * - Gyro
     - G0@17, G1@19, G2@21; jeweils LE16 signed
     - nahe null in Ruhe, deutliche Reaktion bei Bewegung
   * - Beschleunigung
     - A0@23, A1@25, A2@27; jeweils LE16 signed
     - behält in Ruhe einen Schwerkraftvektor

Im zentralen sechssekündigen Ruhefenster nach dem Ruhe-Signal liegen 375
Samples vor. Mittelwerte der Gyrokanäle: (-0.123, +0.485, +0.304) Zähler;
Standardabweichungen: (1.337, 0.665, 2.127) Zähler. Das liefert einen lokalen
Nullpunkt-/Rauschbefund für diesen Lauf, keine temperaturunabhängige
Gerätekalibrierung.

Beschleunigungsmittelwerte: (258.805, 8211.392, -107.968) Zähler.
Der Median der Vektorlänge ist 8215.838 Zähler. Gegenüber 8192 sind das
+0.291 Prozent. Ein früheres ruhiges Fenster ergibt 8216.748 Zähler;
im späteren Fenster T+235..240 liegt der Median bei 8197.019 Zählern,
bei stärkerer Gyrostreuung als in der ersten Ruhephase.

Diese Größen passen zu einem nominalen Maßstab von 8192 Zählern/g.
29 nach einer ausdrücklich dokumentierten Ruheheuristik ausgewählte
Zweiersekunden-Fenster enthalten 3624 Samples. Ihre Norm-Mediane liegen
zwischen 8195.080 und 8218.557 Zählern. Die mittleren Schwerkraftrichtungen
dieser Fenster unterscheiden sich höchstens um 1.996 Grad. Damit werden
hauptsächlich sehr ähnliche flache Lagen wiederholt, keine sechs unabhängigen
statischen Achslagen. Die Heuristik beweist weder völlige Ruhe noch
Abwesenheit einer konstanten Translationsbeschleunigung.

Es fehlt jedoch eine bekannte Serie verschiedener statischer Lagen,
mit der sich Maßstab, Achsengewinne, Offset und Montagewinkel getrennt
bestimmen lassen. Den beobachteten Betrag 8215.838 einfach als neue
Zähler/g-Konstante zu übernehmen wäre keine belastbare Kalibrierung.
Ebenso dürfen die kleinen A0/A2-Ruhewerte nicht pauschal als Bias
abgezogen werden: Sie können durch die reale Neigung verursacht sein.

Warum die Achsen noch nicht feststehen
------------------------------------

Die Ereignisdatei protokolliert Aufforderungen. Sie enthält keine bestätigten
Zeitpunkte jeder tatsächlichen Bewegung und keine positive Referenzrichtung.
Das zentrale Fenster für die erste Links-/Rechtsdrehung, T+77.079..83.079,
ist praktisch noch ruhig: Gyro-Standardabweichungen (1.184, 0.644, 1.948).
Der erste anhaltende starke Gyroausschlag nach dieser Aufforderung beginnt
erst 8.708 Sekunden später, unmittelbar vor dem nächsten Signal.
Hierfür wurde ausschließlich die dokumentierte Heuristik Betrag >100
Rohzähler über mindestens 250 ms verwendet; sie bestimmt keine Drehrichtung.

Spätere Aufforderungsfenster zeigen gemischte Rotationen. Beispielsweise
dominiert im nominalen Roll-Fenster G0 mit rund 88.7 Prozent der
Gyrovarianz. Im nominalen Links-/Rechts-Verschiebefenster dominiert G2
mit rund 94.8 Prozent: Dieses Fenster enthält deutliche Rotation und ist
keine saubere isolierte Translationsreferenz. Eine blinde Zuordnung
"Yaw-Fenster = Y-Achse" oder "Roll-Fenster = Z-Achse" wäre deshalb falsch.

Der dominante positive A1-Wert beim flachen Ablegen ist ein Hinweis auf
die Vertikalkomponente in dieser Lage. Eine einzelne Lage bestimmt jedoch
nicht die zwei übrigen Richtungen, deren Vorzeichen oder die SDL-Abbildung.
Die X/Y/Z-Beschriftung in Deadband schließt diese Lücke nicht.

Warum der Gyromaßstab noch fehlt
-------------------------------

Es gibt keine im Mitschnitt dokumentierte Winkeldrehung, bekannte Drehzahl
oder bestätigte Sensorempfindlichkeit. Freie Handbewegung lässt sich daher
nicht direkt in Zähler/(Grad/s) umrechnen. Eine Schätzung aus Änderungen des
Beschleunigungsvektors wäre zudem von Translation, Achsenzuordnung, Filtern
und der nicht bekannten zeitlichen Ausrichtung beider Sensoren abhängig.
Sie ersetzt unter diesen Bedingungen keine verifizierte Winkelreferenz.

16 aus dem ersten SDL-Test und 16.4 aus dem neuen Umrechnungsbeispiel sind
ausschließlich künstliche Testkonstanten. Keine davon stammt als bestätigte
Gyrokalibrierung aus Deadband oder diesem Mitschnitt.

Die ergänzende Prüfung öffentlicher Platinenunterlagen hat bisher keinen
eindeutig lesbaren IMU-Typ ergeben. Der in g7ctl beschriebene Nachweis der
IMU betrifft die Unterscheidung von Gyro- und Beschleunigungskanälen, nicht
die Identifikation eines Sensorchips. Die ungefähr 8192 Zähler/g sind kein
eindeutiger Bauteilfingerabdruck. Auch bei bekanntem Chip wären die aktive
Gyro-Messbereichseinstellung und die Übernahme der Sensorzählwerte durch
die Controller-Firmware separat zu belegen. Details und Herstellerbeispiele
stehen im ergänzenden Statistikbericht.

Vorbereitete SDL-Umrechnung
--------------------------

src/gs_sensor.c und gs_sensor.h enthalten einen gemeinsamen, rein lokalen
Umrechnungskern. Für jede Ausgabeachse werden ein Rohkanal, Vorzeichen,
Roh-Bias und rationaler Verstärkungsfaktor angegeben. Rechenfolge::

    input_count = round(sign * (raw[source] - bias_raw) * numerator / denominator)

Die Ausgabeauflösung gibt Zähler/g für Beschleunigung oder Zähler/(Grad/s)
für Gyro an. SDL rechnet anschließend::

    accel_m_s2 = input_count * 9.80665 / accel_resolution
    gyro_rad_s = input_count * (pi / 180) / gyro_resolution

Gebrochene Roh-Sensitivitäten lassen sich damit abbilden, obwohl Linux-Input
eine ganzzahlige Auflösung verwendet. Rein künstliches Testbeispiel:
16.4 Rohzähler/(Grad/s), Faktor 250/41 und Ausgabeauflösung 100 ergeben aus
1476 Rohzählern 9000 Input-Zähler und daraus in SDL pi/2 rad/s, also 90 Grad/s.
Eine künstliche 1-g-Beschleunigung ergibt in SDL 9.80665 m/s².

Der Kern prüft positive Auflösung, eindeutige Kanalzuordnung, Vorzeichen,
Faktorgrenzen, Überlauf und erforderliche Prüfkennzeichen. Bei unvollständigen
Metadaten bleibt die Ausgabe unverändert. Prüfkennzeichen drücken einen
extern belegten Freigabestand aus; der Code kann physikalische Richtigkeit
nicht selbst feststellen. Es wird kein verifiziertes G7-Pro-Profil mitgeliefert.

Das maschinenlesbare Profil sdl-sensor-calibration.json enthält
runtime_enable=false und verified_flags=0 für die endgültige SDL-Ausgabe.
Sein Beschleunigungsfaktor 8192/1 wird inzwischen vom Offline-Replay gelesen
und an gs_accel_convert_experimental übergeben. Dieser getrennte C-Pfad
rechnet in Mikrometer/s² in Rohachsenfolge um und meldet den Ergebnisstatus
GS_SENSOR_EXPERIMENTAL. Er setzt keine Prüfkennzeichen. Der Gyrofaktor bleibt
null, ohne Ersatzwert oder Ableitung aus der Beschleunigung. Eine Kernel-
Ladeschnittstelle oder ioctl-ABI ist weiterhin nicht implementiert.

Ausgeführte Prüfungen
--------------------

* Alle 12204 aufgezeichneten IMU-Samples stimmen mit den neu gelesenen
  Paketbytes überein; Original- und relevante Analyseprüfsummen stimmen.
* C-Konvertierung mit künstlichen Referenzen: Einheiten, gebrochene Faktoren,
  Vorzeichen/Achsentausch, Bias, Rundung, fehlende Prüfkennzeichen, ungültige
  Metadaten und Überlauf. AddressSanitizer und UndefinedBehaviorSanitizer
  melden keinen Fehler.
* Alle 24408 Gyro-/Beschleunigungsgruppen aus dem Capture-Replay werden
  mit unbestätigtem Kalibrierprofil vom strengen SDL-Umrechnungspfad abgewiesen.
  Der ausdrücklich experimentelle Beschleunigungspfad konvertiert zusätzlich
  alle 12204 Samples. Rohdaten und Gyro bleiben unverändert. Der ursprüngliche
  Rohdatenbefund wird dadurch nicht nachträglich zur Kalibrierung erklärt.
* SDL3 und SDL2-Compat: insgesamt zwölf gerätefreie Tests erfolgreich,
  einschließlich der zwei neuen Durchläufe vom gemeinsamen C-Umrechnungskern
  über künstliches evdev bis zur SDL-Sensor-API. Die G7-Kalibrierung wird
  dadurch ausdrücklich nicht als bestätigt behandelt.

Was vor einer echten SDL-Sensorfreigabe fehlt
-------------------------------------------

1. Vorzeichenrichtige Zuordnung jedes Rohkanals zur physischen Controller-
   und SDL-Achse. SDL definiert +X nach rechts, +Y nach oben und +Z zum Nutzer;
   positive Rotation folgt seiner dokumentierten Drehrichtung.
2. Ein belegter Gyrofaktor je Achse, aus einer bestätigten Sensorspezifikation
   oder einer bekannten Winkeldrehung mit überprüften Messintervallen.
3. Bestätigung der Beschleunigungsskalierung und der Offsets in mehreren
   bekannten ruhigen Lagen. Ein Gesicht/Lage genügt nicht zur Trennung dieser
   Größen; sechs bekannte positive/negative Achslagen wären eine geeignete
   spätere Referenz.
4. Eine dokumentierte Nullpunkt-/Rauschbehandlung, einschließlich der Grenzen
   einer nur im aktuellen Lauf geschätzten Gyro-Nullage. Keine Schwerkraft-
   entfernung bei der SDL-Beschleunigung: SDL erwartet sie einschließlich g.

Für eine spätere Datengewinnung würden bekannte statische Lagen sowie
jeweils positive/negative, bekannte Winkel um die drei Controllerachsen
genügen. Tatsächlicher Anfang, Ende und Richtung müssten dokumentiert werden.
Das wäre gezielte Kalibrierung, keine Wiederholung der allgemeinen Funktions-
oder Motorprüfung. Hier werden weder eine neue Messung noch Befehle dafür
gestartet oder freigegeben.

Eine belegte Geräteuhr ist keine Voraussetzung für SDL: Host-Ereigniszeit
bleibt zulässig. Ohne Nachweis wird jedoch kein Gerätezeitstempel behauptet.
IIO-Rohdaten und normale Gamepad-/Motorfunktionen hängen nicht von einer
fertigen physikalischen Sensorkalibrierung ab. Der Treiberentwurf bleibt
unabhängig von Deadband; dessen vorhandener Betrieb bleibt unangetastet.

Primärquellen
-------------

Deadband-Decoder und Motion-Konfiguration:
https://github.com/broroeror/gamesir-linux-tools/blob/771b28ae75b0a614a6a7fec9aa606606a27b3b8d/vendors/gamesir/models/g7pro/protocol.py

Unveränderte Weitergabe und Sensoranzeige:
https://github.com/broroeror/gamesir-linux-tools/blob/771b28ae75b0a614a6a7fec9aa606606a27b3b8d/bridge.py
https://github.com/broroeror/gamesir-linux-tools/blob/771b28ae75b0a614a6a7fec9aa606606a27b3b8d/qml/App/MotionSensors.qml

SDL-Einheiten und Koordinaten:
https://wiki.libsdl.org/SDL3/SDL_SensorType

SDLs evdev-Auflösung und Umrechnung:
https://github.com/libsdl-org/SDL/blob/829a65d769d935c4852f8159e964312c0957260a/src/joystick/linux/SDL_sysjoystick.c
