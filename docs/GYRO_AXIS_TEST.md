# Qualitativer Gyro-Achsentest: zunächst nur links

Stand: 18. Oktober 2026. **Offline vorbereitet, noch nicht live ausgeführt.**
Dieser Test untersucht Rohkanalreaktion und Vorzeichen beim waagerechten
Linksdrehen. Kein bestimmter Winkel, Anschlagwinkel oder Bewegungsumfang ist
erforderlich. Die physikalische Skalierung bleibt unbestätigt; die bekannte
Winkelkalibrierung bleibt pausiert. `0,07 °/s pro Rohwert` wird hier weder
ausgewählt noch zur Winkelberechnung verwendet.

## Umfang und Vorbereitung

Geplant sind höchstens drei getrennte Wiederholungen. Jeder Aufruf führt nur
eine aus, wartet auf ein eigenes lokales Go und endet anschließend. Es gibt
keinen automatischen Folgelauf. Für den ersten Versuch zunächst ausschließlich
Wiederholung 1 freigeben; erst nach Auswertung und neuer Bereitschaft weiter.
Rechtsdrehen, Neigen und Rollen sind spätere getrennte Tests.

Vor einem Live-Aufruf frisch und lesend prüfen: Kernel/Modul-Build, native
Bindung des Standard-G7-Pro unter `3537:109c`, genaue USB-/IIO-Instanz,
Scanlayout, deaktivierter Sensorpuffer, Streamstatus, Schreibrechte und freier
Speicher im privaten Ergebnisordner sowie verfügbare KDE-/Passwortfenster.
Spiele und Deadband schließen; keine weiteren Sensorleser parallel starten.
Der vorhandene Helfer prüft weiterhin die feste geprüfte Modul-`srcversion`;
bei Abweichung stoppen und die Kompatibilität prüfen, nicht die Prüfung umgehen.
Keine Geräteöffnung oder Zustandsänderung aus der Offline-Vorbereitung ableiten.

Für die eigentliche Messung ist eine gesonderte Freigabe nötig: Passwortabfrage,
Prozess-FD-Metadatenprüfung, einmaliges lesendes Öffnen genau des IIO-Knotens,
temporäre **Host-Pufferkonfiguration** und ihre anschließende Rückstellung.
Kein neuer Treiber, Modulwechsel, Release/Resume, USB-Schreibbefehl oder
Sensorregisterzugriff. Der Kernel-Treiber und normale Spielbetrieb erhalten
keine Konfigurationsänderung. Der IIO-Puffer selbst wird während des Tests
allerdings ausdrücklich vorübergehend aktiviert.

## Ablauf pro Wiederholung

Ausgangslage: Tastenfläche nach oben, USB-/Vorderkante vom Spieler weg.
Links bedeutet eine waagerechte Drehung von oben gesehen gegen den Uhrzeigersinn.
Nicht senkrecht aufrichten, schütteln oder gegen einen Anschlag drücken.

Nach Passwortprüfung und eigener Go-Bestätigung gibt es zunächst **30 Sekunden
Vorbereitung ohne Sensoraufnahme**. Dann führen lokal getaktete KDE-Hinweise
durch die Messung; Chatnachrichten sind keine Zeitbasis.

| Phase | Zeit | Handlung |
| --- | --- | --- |
| Vorruhe | 20 s | Auf dem Tisch ruhig liegen lassen. |
| Aufnehmen | 15 s | Bequem aufnehmen und ausrichten; noch nicht drehen. |
| Startpuffer | 5 s | Stillhalten; die Ansage kündigt das kommende JETZT an. |
| Linksdrehung | 15 s Zeitfenster | Ab JETZT einmal langsam nach links drehen, nur so weit wie bequem. Danach in der erreichten Lage halten. |
| Endpuffer | 5 s | Weiter stillhalten, noch nicht zurückdrehen. |
| Ablegen | 15 s | Vorsichtig in der erreichten Ausrichtung ablegen. |
| Schlussruhe | 30 s | Ruhig liegen lassen. |
| Abschluss | 3 s passive Nachzeit, anschließend Rückstellungsprüfung | Auf die ausdrückliche Meldung warten, dass Aufnahme geschlossen und Puffer zurückgestellt sind. |
| Rücksetzen | Mindestens 15 s, beliebig länger möglich | Erst jetzt bequem zur Ausgangslage zurückkehren. Kein neuer Lauf startet. |

Eine Wiederholung umfasst 108 Sekunden Aufnahme, davor 30 Sekunden Vorbereitung
und danach mindestens 15 Sekunden Pause; Passwort-/Go-Dialog und Prüfung kommen
hinzu. Die Drehung muss nicht 15 Sekunden dauern. Nach Erreichen einer bequemen
Endlage einfach halten. Bei verpasster Ansage oder falscher Bewegung nicht
hektisch nachholen: anschließend als nicht gelungen kennzeichnen. Die Rohdaten
bleiben erhalten, ohne automatische Wiederholung oder bestätigte Auswertung.
Abbruch jederzeit mit Strg+C im Vordergrundprozess; der Worker versucht dann
die begrenzte Rückstellung und dokumentiert deren tatsächlichen Ausgang.

## Vorbereitete Befehle, noch nicht ausführen

Aus dem Projektwurzelordner lässt sich ausschließlich der Plan gerätefrei ausgeben:

```sh
python3 -B tools/imu/gamesir_gyro_guided.py plan-axis-left
```

Nach gesondert freigegebener frischer Vorprüfung die Platzhalter durch die
tatsächlich ermittelte Instanz ersetzen. Ein neues privates Elternverzeichnis
`.local/gyro-axis/` muss existieren; vorhandene Manifeste/Ergebnisse werden
nicht überschrieben. Der folgende Vorbereitungsschritt liest nur Metadaten
und speichert das Manifest, er öffnet kein Zeichengerät:

```sh
python3 -B tools/imu/gamesir_gyro_guided.py prepare \
  --iio-dir /sys/bus/iio/devices/iio:deviceN \
  --device-node /dev/iio:deviceN \
  --output .local/gyro-axis/manifest-01.json
```

Erst nach konkreter Freigabe genau eines Live-Laufs:

```sh
python3 -B tools/imu/gamesir_gyro_guided.py run-axis-left \
  --manifest .local/gyro-axis/manifest-01.json \
  --repetition 1 \
  --output .local/gyro-axis/left-01
```

Das Frontend läuft als Desktopbenutzer; ausschließlich der vorhandene begrenzte
Worker erhält über `sudo -A`/`ksshaskpass` erhöhte Rechte. Vor dem lokalen Go
und den 30 Vorbereitungssekunden wird kein Sensorpuffer geöffnet/aktiviert.
Das Manifest verwendet das bestehende Metadatenformat mit dem historischen
Namen `gamesir_yaw90left_manifest`; es enthält Instanz und Quellprüfsummen,
keinen behaupteten Drehwinkel. **Nicht** den alten Unterbefehl `run` benutzen:
dieser verlangt weiterhin eine echte externe 90°-Referenz.

## Daten, Auswertung und Grenzen

Der vorhandene kohärente Worker speichert sechs Rohkanäle desselben akzeptierten
Berichts, Host-Monotonzeit und Berichtszähler. Dateien: `capture/scans.bin`,
`capture/observations.jsonl`, Layout, Puffertransaktion, Abschlussbericht und
SHA256-Prüfsummen. Darüber hinaus bleiben die tatsächlichen Ansagezeitpunkte,
Nutzerrückmeldung und Frontendbericht privat im neuen Laufordner erhalten.

Nach bestätigter Rückstellung, geprüften Dateihashes und ausdrücklicher
Bestätigung der tatsächlich ausgeführten Linksdrehung entsteht `analysis.json`.
Sie vergleicht für G0/G1/G2 Vorruhe, Bewegungsreaktion mit Vorzeichen und
Nachruhe in **Rohwerten**. Aufnehmen, Ablegen und Rücksetzen zählen nicht zum
Bewegungsfenster. Vorruhe ist nur eine experimentelle Vergleichsbasis;
Ruhestreuung und Änderung zur Nachruhe bleiben sichtbar.

Kein `reference.json`, kein erfundener 90°-Winkel, keine Winkelintegration,
Profilwahl oder Installation einer Achsenzuordnung. Eine klar wiederholbare,
vom Nutzer bestätigte Bewegung kann einen Rohkanal samt Vorzeichen für diese
Drehrichtung zuordnen helfen. Gemischte Bewegungen, geringe Reaktion oder
unruhige Ruhephasen bleiben uneindeutig. Drei Linksdrehungen beweisen nicht
die vollständige Achsenzuordnung; Gegenrichtung und die anderen Achsen fehlen.
Die Hostzeit ist keine Sensoruhr, der Berichtszähler kein Funkverlustnachweis.

Bei Instanzwechsel, konkurrierendem Leser, fehlenden Daten, Zähler-/Zeitlücken,
Suspend, neuen Pufferfehlern oder verspäteten Ansagen stoppen. Der bestehende
Worker stellt nur die ursprüngliche Instanz zurück; keine Writes an ein
Ersatzgerät, keine Reparatur, kein Reconnect. Eine fehlgeschlagene Rückstellung
bleibt ein Fehler und verhindert die Auswertung. Grenzen: 250 ms zwischen
Samples und 2 s ohne frische Daten, wie im vorhandenen Messpfad; keine
nachgewiesenen Sensor- oder Funkraten.

Offline-Abnahme: synthetische Kanäle mit wechselnder Achse/Vorzeichen, keine
Bewegung, fehlerhafte Zeit-/Zählerfolgen und Ansagen; gemockter vollständiger
Einzellauf, verweigertes Go, nicht bestätigte Bewegung und fehlgeschlagene
Rückstellung. Keine echte GUI, Passwortabfrage oder Hardware in den Tests.
Sie bestätigen Softwaregrenzen, keine reale Sensorzuordnung.

Prüfung am 18. Oktober: `make test-imu-stream test-public-readme test-licensing`
bestanden, insgesamt 229 Tests. Davon 45 Frontend-/Achsenfälle, neun neu.
Auch der gerätefreie Planaufruf, Dokumentationslinks und `git diff --check`
wurden geprüft. Keine Installation oder Live-Abnahme durchgeführt.
