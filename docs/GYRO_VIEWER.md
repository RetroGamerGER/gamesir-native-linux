# Lokales Gyro-Diagnosefenster — Replay und vorbereitete Live-Vorschau

Stand: 18. Oktober 2026. Experimentelles Diagnosewerkzeug, keine installierte
Sensorausgabe. Der unveränderte Standardmodus öffnet ausschließlich
gespeicherte Aufnahme-Dateien. Die zusätzliche `--live`-Vorschau ist offline
implementiert, aber noch nicht an Hardware abgenommen. Fensteröffnung allein
öffnet kein Gerät. Live-Vorbereitung und temporärer Host-IIO-Puffer benötigen
eine separate Freigabe; siehe Ablauf unten. Keine neue Installation, keine
USB-Befehle und keine Dienst-/Treiberänderung. Winkelkalibrierung bleibt pausiert.

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
Euler-Winkelintegrale. Im Replay werden die Orientierungen einmal vorbereitet;
live wird derselbe Integrator Sample für Sample verwendet. Quaternionen
werden normalisiert. Die Startorientierung ist frei als Null gewählt. Zentrieren
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

## Herkunft der Bedienidee

Der Auftrag im Projektchat nannte ausdrücklich „Fadenkreuz, Drehungsanzeige
und Empfindlichkeitsregler“. Der frühere Kalibrierungsauftrag verlangte die
fünf experimentellen Messbereichsprofile; sie bestanden bereits vor der GUI.
Ihre Zahlenherkunft und die Grenzen der lokalen Gegenprüfung stehen unter
[Werkzeug und Quellenstatus](EXPERIMENTAL_GYRO_TEST.md#werkzeug-und-quellenstatus).
Der E2E-Plan wurde in Commit `2f2271a` dokumentiert; Commit `526c356` ergänzte
das Offline-Fenster. Konkretes Layout, Sichtfeld, Zentrieren und die Umsetzung
des Reglers als 0,25–4× sind Gestaltungsentscheidungen, keine Herstellerfunktion
oder Kalibrierung. Für die Live-Erweiterung wurde kein anderer Chat abgerufen.

## Live-Test zur Freigabe vorbereitet

**Noch nicht ausführen.** Der aktuelle Auftrag erlaubt nur Offline-Entwicklung.
Die spätere Freigabe umfasst frische Metadaten-/Leserprüfung, eine
Passwortabfrage und genau eine temporäre Host-Puffertransaktion bis Stopp.
Keine Modul-/Dienstaktion, USB-Konfiguration, Bindungsänderung oder Installation.
Ein bereits laufendes Offline-Fenster wird einmal durch die neue Live-Version
ersetzt; während des Live-Laufs erfordern Profil-/Gainwechsel keinen Neustart.

Voraussetzungen: genau ein bereits nativ gebundener Standard-G7-Pro unter
`3537:109c`, IF0 an `gs_native`, der bekannte kohärente Modulbuild, inaktiver
IIO-Puffer und kein konkurrierender Pufferleser. Spiele und Deadband geschlossen.
Das Fenster richtet keinen Treiber ein. Fehlt das native Gerät, wartet es
während der Vorbereitung höchstens 60 Sekunden; Mehrdeutigkeit oder eine
abweichende Instanz stoppen. Keine automatische Reparatur oder Übernahme.

Vorgesehener Start als normaler Desktopnutzer aus dem Quellverzeichnis:

```sh
python -B tools/imu/gamesir_gyro_viewer.py \
  --live --experimental --profile 2000 \
  --axis-profile g7pro-observed-20261018
```

`--profile 2000` wählt ausdrücklich den **unbestätigten** Kandidaten
`0,07 °/s pro Rohwert`. Die übrigen vier Hypothesen lassen sich im Fenster
auswählen. Ohne explizite Profilwahl verweigert der Live-CLI den Start.
Der neue private Ausgabeordner wird automatisch als
`$HOME/GameSir-Gyro-Live-<UTC-Zeitstempel>` festgelegt; alternativ
`--output /path/inside/home/new-private-run`. Bestehende Ordner werden abgelehnt.

1. Fenster öffnen und Controller normal verbinden. **Noch kein Sensorzugriff.**
2. „Verbindung vorbereiten“ prüft ausschließlich Metadaten, erstellt ein
   frisches Instanz-/Quellhash-Manifest und startet einmal den vorhandenen
   Worker mit grafischer Passwortabfrage. Dessen Startprüfung öffnet noch
   kein IIO-Gerät und aktiviert keinen Puffer.
3. Erst „Live starten“ sendet das lokale Go. Der Worker prüft erneut,
   reserviert genau einen lesenden IIO-Deskriptor und aktiviert temporär die
   vollständigen acht Scanfelder, Monotonzeit, Pufferlänge 512 und Wasserstand
   1, sofern vorhanden. Das sind Host-Pufferattribute, keine Sensorbefehle.
4. Jetzt frei bewegen, zurückdrehen, ruhig halten, zentrieren und die
   Empfindlichkeit ausprobieren. **Kein festes Zeitlimit**, kein Vorspulen,
   kein vorgegebener Winkel oder Zeitpunkt. Alle Bewegungen fließen ein.
   Profilwechsel setzt die relative Drehungsansicht zurück; Instanz, Zähler
   und Zeitkontrolle laufen weiter. Die Rohwerte werden nicht verändert.
5. „Stopp“ oder Fenster schließen beendet den Datenstrom und stellt den
   ursprünglichen Host-Puffer zurück, bevor der reservierte Deskriptor
   geschlossen wird. Das Fenster bleibt währenddessen sichtbar. Ein weiterer
   unabhängiger Metadatenvergleich und die gespeicherten Prüfsummen müssen
   die Rückstellung bestätigen. Bei einem Fehler bleibt die Meldung sichtbar.
6. Abschließend normale Gamepad-Eingaben prüfen und Ergebnis festhalten.
   Kein neuer Lauf, kein Reconnect oder Reparaturversuch ohne neue Entscheidung.

Der konkrete privilegierte Unteraufruf wird mit den neuen absoluten Pfaden
ohne Shell zusammengesetzt; dies ist das Befehlsmuster zur Freigabe:

```sh
SUDO_ASKPASS=/usr/bin/ksshaskpass /usr/bin/sudo -A -p 'Password: ' \
  /usr/bin/python -B /path/to/repository/tools/imu/gamesir_gyro_worker.py \
  --manifest /path/to/new-private-run/manifest.json \
  --output /path/to/new-private-run/capture
```

Kein separat manuell gestarteter Worker: Die GUI liefert GO/PING/STOP über
eine Pipe. Sie bleibt ohne Root-Rechte; kein passwortloser Systemdienst und
keine sudoers-Änderung. Ein späteres „Stopp“ im Chat kann über SIGINT an die
beim Start ausgegebene, zuvor geprüfte **GUI-PID** denselben Stoppweg auslösen.
Keine Prozessnamensuche mit pauschalem Kill, kein SIGKILL des Root-Workers.

### Grenzen und sichere Beendigung

Die unbegrenzte Laufzeit gilt für den gesunden Datenstrom. Fehlende Daten
(2 s), fehlender GUI-Heartbeat (3 s), blockierte Ausgabe (0,5 s), EOF,
Suspend, Gerätewechsel, Zählersprung, Zeitlücke über 250 ms oder unplausible
Rohdaten beenden ihn. Vorbereitungs-/Autorisierungs-/Go-Wartezeiten bleiben
begrenzt; das sind keine Motor- oder Sensor-Laufzeitlimits. Rückstellung und
Workerende werden bis 120 Sekunden abgewartet, danach ausdrücklich als
unbestätigt gemeldet. Kein erzwungenes Beenden und keine automatische Wiederholung.
Ein ausgeschalteter oder wegen Inaktivität verschwundener Controller beendet
die Sitzung; die Anwendung übernimmt keine neue Instanz stillschweigend.

Die Live-Pipe ist Version 1 und wird auf Reihenfolge, frische Host-Zeitstempel,
exakte Instanz, kohärente Rohkanäle und fortlaufende Zähler geprüft. Nach Fehlern
werden keine alten Drehraten fortgeschrieben. Es bleiben nur vorheriger/
aktueller Sample und Orientierung im Speicher. Der 100.000-Sample-Grenzwert
des Datei-Replays und das 108-s-Limit des alten Aufnahmeworkers gelten nicht
für diesen ausdrücklich angeforderten kontinuierlichen Vorschaumodus.

**Kein fortlaufender Rohmitschnitt:** Im privaten Ordner liegen Manifest,
Worker-Fehlerausgabe, Puffertransaktion, Layout, Abschlussbericht, SHA256SUMS
und GUI-Abschlussprüfung. Es werden keine `scans.bin`/`observations.jsonl`
angelegt. Die Berichte halten Startprofil, Endprofil/Wechselanzahl und
Sampleanzahl fest, aber nicht jede Regleränderung oder einen Messverlauf.
Damit ist diese Vorschau kein nachträglich auswertbarer Kalibrierungslauf.

### Offline-Abnahme der Live-Erweiterung

- 23 Transport-/Worker-/Lifecycle-Tests: synthetische Daten, reale anonyme
  Pipes und Fake-IIO; keine Hardware. STOP auch während blockierter Ausgabe,
  kein falscher Samplezähler und kein Erfolg ohne überprüfte Rückstellung.
- 14 Qt-Tests insgesamt, davon sechs neue Live-Fensterprüfungen: lokale
  Bereitschaft, Profilwechsel, Stopp/Schließen, Signal und Fehleranzeige.
- Alle 40.486 gespeicherten Scans getrennt durch das neue Sampleprotokoll:
  jede Orientierung exakt gleich dem Offline-Modell; Originalhashes erhalten.
- Gerätefreie Simulation beider Fenstergrößen geprüft. Der abgebrochene
  gespeicherte Versuch bleibt abgelehnt; keine gemischten Geräteinstanzen.
- Gesamte betroffene Regression: 382 Python-Tests plus C-Sensorvertrag
  bestanden (Diagnose, Stream, Puffer, Worker, Führung, GUI, Lizenz und README).

Dies belegt Implementierung und Offline-Verhalten. Echte Live-Latenz,
Langzeitstabilität, Hardware-Rückstellung dieses Modus und physikalische
Skalierung bleiben bis zu ihren jeweiligen Prüfungen unbestätigt.
SDL-/Eden-Unterstützung ist eine eigene, offene Integration.
