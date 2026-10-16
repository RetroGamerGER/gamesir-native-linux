G7 Pro: experimentelle Beschleunigung mit 8192 Zählern/g
=======================================================

Implementierungsstand, 11. Oktober 2026
--------------------------------------

Der Nutzer hat 8192 Zähler/g ausdrücklich als experimentellen,
austauschbaren Beschleunigungswert angenommen. Er ist im Profil
sdl-sensor-calibration.json unter accelerometer.counts_per_g eingetragen.
scale_verified bleibt false. Der Gyrofaktor wird davon unabhängig behandelt.
Chipidentifikation oder ein vollständiger Kalibrierungsnachweis sind keine
Voraussetzung für diese experimentelle Beschleunigungsimplementierung.

Umrechnung und Austausch des Werts
---------------------------------

src/gs_sensor.c implementiert gs_accel_convert_experimental. Der Aufrufer
übergibt eine gs_accel_experimental_scale mit Zähler und Nenner. Das
Offline-Replay liest diese beiden Werte aus dem Profil; 8192 ist nicht als
Gerätekonstante in die C-Funktion eingebaut. Der Profilwert ist die
Empfindlichkeit counts_per_g / counts_per_g_denominator. Aktuell: 8192/1.
Auch rationale Ersatzwerte sind möglich, ohne die C-Funktion zu ändern.
Beide Ganzzahlfelder müssen zwischen 1 und 1000000 liegen.

Die physikalische Entwicklungsumrechnung lautet::

    accel_m_s2[i] = raw_accel[i] * 9.80665 / sensitivity_counts_per_g

Der C-Kern arbeitet ohne Fließkomma und liefert Mikrometer/s², gerundet
auf die nächste Ganzzahl; halbe Schritte werden von null weg gerundet.
Die Erdschwere bleibt enthalten. Reihenfolge und Vorzeichen der Rohachsen
A0/A1/A2 bleiben erhalten; eine SDL-Achsenorientierung wird nicht angenommen.
Es wird kein Bias abgezogen. Bei Erfolg lautet der Rückgabewert ausdrücklich
GS_SENSOR_EXPERIMENTAL (1). Ungültige Parameter oder Überlauf verändern die
Ausgabe nicht. Der Kern öffnet keine Dateien oder Geräte.

Für einen späteren besseren Wert werden die beiden Beschleunigungsfelder
im Profil ersetzt und die Offline-Prüfung erneut ausgeführt. Die ursprüngliche
Capture-Statistik bleibt als historischer Befund erhalten. Bei einer späteren
Treiberintegration muss der Aufrufer die Werte übergeben; eine automatische
Kernel-JSON-Ladeschnittstelle ist hier nicht implementiert.

Gyro und endgültige SDL-Freigabe
-------------------------------

gyroscope.counts_per_degree_per_second bleibt null. Es gibt keinen
Ersatzfaktor, keine Ableitung aus 8192 und keine Umrechnung des Gyros in
scheinbare Grad/s oder rad/s. Die Gyro-Rohwerte bleiben erhalten.

Der bisherige strenge Konverter gs_sensor_convert und seine Prüfkennzeichen
bleiben unverändert. runtime_enable=false und verified_flags=0 betreffen
weiterhin die endgültige SDL-Ausgabe. Sobald ein eigenständiger Gyrofaktor
und die richtige Sensororientierung vorliegen, kann die gemeinsame Ausgabe
vorbereitet und geprüft werden. Die normale Eingabe- und Motorentwicklung
hängt nicht von diesen noch offenen Sensordetails ab.

Offline-Validierung
------------------

tests/check_capture_core.py liest das Profil und die vorhandenen Paketdaten,
prüft die gespeicherten SHA256-Werte der Eingabedateien und ruft den
gemeinsamen C-Protokoll- und Umrechnungskern auf. Alle 12204 IMU-Frames
werden gegen den vorhandenen Parser und die gespeicherten Rohwerte geprüft.
Die experimentelle Ausgabe wird mit einer unabhängigen physikalischen
Referenzrechnung verglichen. Rundungsfehler: höchstens 0.5 Mikrometer/s²
je Achse. Der vollständige dekodierte Frame bleibt unverändert.

Im bekannten Ruhefenster T+67.03886..73.03886 liegen 375 Samples vor.
Der Rohbetragsmedian 8215.838484 Zähler ergibt experimentell einen
Beschleunigungsbetragsmedian von 9.835187 m/s² beziehungsweise 1.002910 g.
Die Abweichung von 1 g beträgt +0.291 Prozent. Das ist ein statistischer
Plausibilitätsbefund; keine Bestätigung des Maßstabs oder der Offsets.

Der bisherige Capture-Vergleich für Gamepad-Eingaben, alle vier Motoren,
Initialisierung und Wartung besteht ebenfalls. Der strenge Konverter lehnt
weiterhin alle 24408 unbestätigten Sensorgruppen ab. Die experimentellen
Beschleunigungswerte werden ausschließlich durch die benannte Funktion
erzeugt und nicht als endgültige SDL-Sensorausgabe veröffentlicht.

tests/test_sensor_contract.c prüft zusätzlich positive und negative 1-g-
Referenzen, Skalenaustausch, rationale Faktoren, volle 16-Bit-Werte,
Rundung, ungültige Metadaten und atomare Fehlerausgabe bei Überlauf.
AddressSanitizer und UndefinedBehaviorSanitizer sind aktiviert.

Wiederholung ohne erhöhte Rechte oder Hardwarezugriff::

    python -B tests/run_sensor_contract_test.py
    python -B tests/check_capture_core.py

Maschinenlesbare Ergebnisse: experimental-accel-validation.json,
sensor-contract-test.json und core-capture-validation.json.
Die Originalaufzeichnung und ihre abgeleiteten Eingabedateien bleiben
unverändert. Es wurden keine Geräte geöffnet, USB-Befehle gesendet,
Treiberbindungen geändert, Kernelmodule gebaut/geladen oder Anwendungen
wie Deadband oder GameSir Connect gestartet.
