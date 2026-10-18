# Lokales Gyro-Diagnosefenster — Offline-Replay

Stand: 18. Oktober 2026. Experimentelles Diagnosewerkzeug, keine installierte
Sensorausgabe. Es öffnet ausschließlich gespeicherte Aufnahme-Dateien.
Kein USB, IIO-Gerät, Sensorpuffer, sudo, Netzwerk, Dienststart oder Treiberwechsel.
Die Winkelkalibrierung bleibt pausiert. Ein Live-Test benötigt einen noch
zu ergänzenden, begrenzten Worker-Transport und eigene Hardwarefreigabe.

## Start und Bedienung

Python 3 und das optionale, lokal vorhandene **PySide6** werden benötigt.
Das Programm installiert nichts. Aus dem Quellverzeichnis:

```sh
python -B tools/imu/gamesir_gyro_viewer.py
```

1. Einen Testfaktor ausdrücklich auswählen. Beispielsweise bedeutet das
   Profil ±2000 °/s **nur die Hypothese** `0,07 °/s pro USB-Rohwert`.
   Weder der aktive Messbereich noch dieser Faktor sind damit bestätigt.
2. „Gespeicherte Aufnahme öffnen“ und den privaten `capture`-Ordner eines
   erfolgreichen kohärenten Worker-Laufs auswählen. Darin müssen `scans.bin`,
   `layout.json`, `observations.jsonl`, `buffer-transaction.json`, `report.json`
   und `SHA256SUMS` unverändert vorhanden sein. Privates Eigentum und die
   vorhandenen strengen Datei-/Verzeichnisrechte werden geprüft.
3. Die Wiedergabe startet **pausiert**. „Abspielen“ gibt sie wieder, die
   Zeitleiste springt zu einer beliebigen Stelle. Kein Controller nötig.
   Bei den sechs Richtungsaufnahmen liegt die eigentliche Bewegung ungefähr
   zwischen Sekunde 40 und 55. Vorbereitung und Rückbewegung bleiben sichtbar;
   es werden keine vermeintlich schlechten Messabschnitte herausgeschnitten.
4. „Ansicht zentrieren“ setzt die aktuelle dargestellte Orientierung auf die
   Mitte, ohne Rohwerte, Bias oder den Testfaktor zu verändern. Für den
   Vergleich kann man vor der Bewegung bei etwa Sekunde 35 zentrieren.
5. Der Regler **Fadenkreuz-Empfindlichkeit** (0,25–4×) verändert ausschließlich
   den Ausschlag links. Die räumliche Drehungsanzeige rechts bleibt bei 1×
   des ausgewählten Testprofils. Wiedergabetempo 0,5–4× ändert ausschließlich
   die Abspielgeschwindigkeit, nicht die integrierten Winkel.
6. Am Ende friert die Anzeige ein. Keine Wiederholung und keine Fortschreibung
   der letzten Drehrate. „Zum Anfang“ pausiert und löscht die Zentrierreferenz;
   erneutes Abspielen ist eine ausdrückliche Bedienhandlung. Fenster schließen
   beendet nur die lokale Darstellung.

Mit bereits ausdrücklich ausgewähltem Profil und Aufnahme:

```sh
python -B tools/imu/gamesir_gyro_viewer.py \
  --experimental --profile 2000 \
  --axis-profile g7pro-observed-20261018 \
  --capture-dir /path/to/private/yaw-left/capture
```

Ohne diese expliziten Optionen darf der CLI keinen Faktor für eine Aufnahme
annehmen. Die grafische Profilauswahl bietet alle fünf vorbereiteten
LSM6DS3TR-C-Hypothesen. Ein Wechsel lädt die Aufnahme neu, verwirft die alte
Orientierung und pausiert. Ein Ladefehler entfernt die bisherige Wiedergabe,
statt alte Werte unter einer neuen Quelle anzuzeigen. Keine Aufnahme wird
verändert oder automatisch exportiert. Das Fenster benötigt mindestens
900×880 Pixel; es verwendet Softwarezeichnung ohne OpenGL oder Geräteinput.

## Was angezeigt und berechnet wird

Der bestehende [experimentelle Achsenvertrag](EXPERIMENTAL_GYRO_TEST.md#beobachtetes-achsenprofil-v1-offline)
bleibt maßgeblich: Gehäuse `(X,Y,Z)=(G0,−G2,G1)`, X rechts, Y vorne, Z aus
der Tastenfläche. Positive benannte Bewegungen: Vorderkante hoch, links
drehen und linker Griff ab. G0/G1/G2 und A0/A1/A2 bleiben unverändert.
Die Beschleunigungsachsen werden weder umgedeutet noch zur Korrektur benutzt.
Das Profil gilt für das beobachtete Standardmodell `3537:109c`, nicht
automatisch für ZZZ. Dies ist kein SDL-Koordinatensystem.

`gyro_view_model.py` integriert die mittlere Drehrate zwischen aufeinander-
folgenden Samples als Quaternionen-Inkrement im Gehäusesystem. Die gespeicherte
Host-Monotonzeit bestimmt Δt; kein GUI-Timer und keine drei unabhängigen
Euler-Winkelintegrale. Die Orientierungen werden einmal vorberechnet und
normalisiert. Die Startorientierung ist frei als Null gewählt. Zentrieren
berechnet ausschließlich die relative Ansicht zu einem neuen Bezug.

Das Fadenkreuz folgt der projizierten Vorderkante: Linksdrehung nach links,
Vorderkante hoch nach oben. Reines seitliches Kippen zeigt die Controllerfigur,
ohne eine künstliche Zielbewegung hinzuzufügen. Bei 1× reicht das Sichtfeld
je ±45°. Außerhalb wird der Marker begrenzt und gelb markiert; eine nach
hinten gerichtete Vorderkante wird nicht als mittiges Ziel ausgegeben.
„Abstand zur Mitte“ ist die kürzeste räumliche Orientierungsdifferenz von
0–180°, **nicht** die Summe aller bisher zurückgelegten Drehungen.

Keine Bias-Schätzung, Sensorfusion oder automatische Driftkorrektur.
Das sind illustrative relative Orientierungen mit unbestätigtem Faktor,
keine Messung des tatsächlich gedrehten Winkels. Eine gute Empfindlichkeit
oder plausible Animation bestätigt weder `0,07` noch den verbauten Chip.
Größere Winkelabweichungen dürfen nicht durch einen Regler kaschiert als
Kalibrierungsnachweis gelten.

## Dateiprüfung und Zeitgrenzen

Der Viewer verwendet den vorhandenen `replay_buffer`-Import: SHA256 aller
Originaldateien, erfolgreicher Abschluss, Puffer-Rückstellung, Geräteinstanz,
Scanlayout sowie exakte Übereinstimmung von Binärdaten und JSON werden geprüft.
Gespeicherte `/sys`-Pfade werden ausschließlich als Metadaten behandelt.
Jede Aufnahme bleibt eine getrennte Instanz; keine aneinandergehängten Läufe.

Das Modell akzeptiert 2–100.000 kohärente Samples pro Aufnahme. Zählersprünge,
Instanzwechsel, nicht steigende Zeitstempel, Intervalle über 250 ms oder
Gyrowerte am int16-Endpunkt stoppen den Import. Es überspringt solche Daten
nicht. Median/max Δt und die Anzahl der Intervalle über 2× Median werden
sichtbar. Kleinere längere Intervalle mit fortlaufendem Zähler bleiben in
dieser illustrativen Integration enthalten; es werden keine fehlenden
Samples erfunden. Das unterscheidet sie vom älteren statistischen
`analyze()`-Winkelindikator, der >2×-Intervalle ausnimmt.

Host-Empfangszeiten sind keine bestätigten Sensorzeitstempel. Zählerkontinuität
beweist nicht, dass intern kein Sensor-/Funkpaket verloren ging. Die Anzeige
misst keine Sensorlatenz oder gesamte Eingabelatenz.

## Offline-Abnahme

- 15 Modelltests: analytische Drehungen, nicht vertauschbare räumliche
  Kombinationen, sechs Richtungen, variable Rate, Normstabilität, Rückbewegung,
  unveränderte Rohwerte, Zentrieren, Displaygain, Timing und Fehlerfälle.
- 8 Qt-Tests offscreen: echte Bedienelemente, Profil-/Quellenwechsel,
  Fehleranzeige, Timerende ohne Extrapolation, Schließen und Fenstergeometrie.
- Alle sechs gespeicherten Richtungsaufnahmen: 40.486 Scans aus zwei getrennten
  freigegebenen Aufnahmeblöcken importiert; Originalprüfsummen danach identisch.
  Der fehlgeschlagene vierte Versuch aus dem ersten Block wurde abgewiesen.
- Fensterrendering in normaler und minimaler Größe visuell geprüft. Keine
  Originalmitschnitte oder privaten Screenshots werden ins Repository übernommen.

```sh
make test-imu-diagnostic
make test-gyro-viewer  # optionale vorhandene PySide6-Abhängigkeit
```

Die neue GUI ist eigene GPL-2.0-only-Implementierung. Es werden keine
Herstellergrafiken, Qt-Binärdateien oder fremden Quellcodes beigelegt. Lokal
geprüft: PySide6/Shiboken6 6.12.0 nennen GPL-2.0-only als Lizenzalternative;
die verwendeten QtCore-/QtGui-/QtWidgets-Header ebenfalls. Die Python-/Qt-
Bibliotheken bleiben separat bereitgestellte Laufzeitabhängigkeiten.

## Nächster E2E-Schritt

Zuerst den lokalen Sample-Transport vom vorhandenen begrenzten IIO-Worker
offline ergänzen und testen: GO/PING/STOP, frische Instanz, sauberes Ende,
Abbruch bei Datenverlust/Disconnect und bestätigte Puffer-Rückstellung.
Danach kann ein gesondert freigegebener Live-Lauf ohne genaue Winkelvorgabe
Richtung, Empfindlichkeit und Drift in diesem Fenster prüfen. Dafür ist
keine neue Kernelimplementierung vorgesehen. SDL-/Eden-Unterstützung und
physikalische Skalierung sind weiterhin eigene, offene Abnahmen.
