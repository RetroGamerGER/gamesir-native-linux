# Control Center alpha2: geführte Stickkalibrierung

Stand: 22. Oktober 2026. **Lokal vorbereitet, noch nicht veröffentlicht oder
installiert.** Das normale Control Center erhält die bereits am G7 Pro und ZZZ
getestete TMR-Anbindung. Der veröffentlichte alpha1-Download bleibt unverändert.

## Bedienung

Im Hauptfenster steht „TMR-Sticks kalibrieren“ als eigene Funktion. Es braucht
keinen besonderen Startbefehl mehr. Der Dialog führt durch drei Schritte:

1. Spiele und Controller-Werkzeuge schließen, „Stickkalibrierung öffnen“ wählen
   und die Berechtigung ausschließlich im Passwortfenster des Systems erteilen.
   Den gewünschten G7 Pro oder ZZZ ausdrücklich auswählen.
2. Beide Sticks loslassen und starten. Nach drei Sekunden Vorbereitung beide
   Sticks jeweils dreimal langsam am äußeren Rand kreisen. Die grünen Bereiche
   zeigen die besuchten Randbereiche; entscheidend bleibt die aktuelle
   Bereitschaftsmeldung beider Sticks.
3. Beide Sticks loslassen und abschließen. Der Abschluss wird einmal an den
   Controller gesendet. „Fertig“ schließt nur den Dialog. Danach Mittelstellung
   und vollen Ausschlag im normalen Controllertest prüfen.

Die Stickanzeigen werden nach dem Abschluss ausgeblendet, damit eingefrorene
Kalibrierdaten nicht wie ein laufender Funktionstest aussehen. Es wird keine
zusätzliche Speicherquittung verlangt oder eine unabhängige NVM-Prüfung behauptet.
Die [ZZZ-Messung](evidence/TMR_ZZZ_CALIBRATION_20261022.json) bestätigt die
Verbesserung und ihren beobachteten Erhalt nach normalem Aus-/Einschalten;
die [erste G7-Pro-Abnahme](evidence/TMR_FIRST_LIVE_CALIBRATION_20261022.json)
bestätigt den Ablauf und die Funktion an derselben Verbindung.

## Weniger Informationen auf einmal

Das Hauptfenster zeigt Treiber, Dongle und Controllerstatus. Kernel,
Modulzustand, Verwaltungsdienst und genaue Uhrzeit stehen unter „Systemdetails“.
Die Statusaufnahme prüft weiterhin keine Funkverbindung: „Hier nicht geprüft“
ist keine Meldung, dass ein Controller ausgeschaltet oder defekt sei.
Unverfügbare Firmwarefunktionen stehen eingeklappt unter „Als Nächstes geplant“.
Deutsch/Englisch, Tastaturbedienung und getrennte Installationspläne bleiben
erhalten. Ein Fehler oder eine laufende Paketprüfung wird weiterhin angezeigt.

## Voraussetzungen und Zuständigkeiten

Ein AppImage mit separat geprüfter `tmr-helper.json` bietet die Kalibrierung
im normalen Start an. Fehlt die Datei oder ist sie ungültig, bleibt die Funktion
gesperrt. Demo und Offline-Probeläufe laden keine echte Kalibrieranbindung.
`--experimental-tmr` bleibt für vorhandene Entwicklungsstarts kompatibel.

Benötigt werden der passende native Treiber/Manager mit TMR-Schnittstelle,
aktivierter TMR-Option und die passende installierte Kalibrierhilfe. Der
getestete lokale Stand ist Core alpha3-20 mit TMR-Helfer alpha1-2. Die aktuell
veröffentlichten älteren Treiberpakete erhalten diese Fähigkeiten durch einen
neuen AppImage-Start allein **nicht**. Dieser Schritt erstellt keine neuen
signierten Treiberpakete und verändert den Updatekanal nicht.

Die gebündelten TMR-Dateien bleiben Daten zur Vorbereitung und Hashprüfung.
Der vorhandene Erststart-/Pakethelfer installiert sie nicht automatisch und
erhält keine zusätzliche Berechtigung. Das AppImage installiert keinen Helfer,
lädt kein Modul und aktiviert keinen Dienst, um die Kalibrierung freizuschalten.
Es führt ausschließlich den festen, geprüften Systemhelfer nach einem
ausdrücklichen Klick aus. Die GUI selbst bleibt ohne Administratorrechte.

Paketinstallation, Deinstallation, Helfereinrichtung und Updatesuche können
keine Kalibriersitzung überholen. Umgekehrt blockieren laufende Prüfungen,
Paketpläne, Installation und unklare Paketergebnisse die Kalibrierung. Diese
Sperren gelten auch für direkte Methodenaufrufe, nicht nur für Buttons.
Nach Schließen bleibt die Sperre bestehen, bis der Hintergrundhelfer wirklich
zurückgekehrt ist. Bei unklarem Kalibrierergebnis bleibt sie vorsichtshalber
für das aktuelle App-Fenster bestehen. Es gibt keinen automatischen Neuversuch.

Die bewährten Schutzgrenzen bleiben unverändert: explizite Geräteauswahl,
frische E0-Daten, exakte Instanz-/Stream-/Sitzungsbindung, drei erlaubte
Kalibrieraufträge, einmaliger Abschluss und keine Wiederholung nach Verlust.
Die bekannte Grenze kurzer unsichtbarer Funkunterbrechungen bleibt dokumentiert
im [Berechtigungsweg](CONTROL_CENTER_TMR_PERMISSION.md). Die Korrektur für
ruhige Startknöpfe und geringe Abfragelast bleibt erhalten.

## Offline-Prüfung und AppImage

Die zusätzliche QML-Regression prüft die normale Kombination aus Paketverwaltung
und Kalibrierung, gegenseitige Sperren, verzögerte Rückgabe, Fehler, einmaligen
Abschluss, „Fertig“, kleine Fenster und DE/EN. Ein eigener Prozess prüft den
normalen Start ohne automatische Autorisierung. Alle Geräte-/Manager-/Paket-
Zugriffe dieser Prüfungen sind nachgebildet.

`--bundle-calibration-self-test` prüft im tatsächlichen AppImage die gebündelten
Manifestdaten und den Hintergrund-Worker mit vollständig simulierten Antworten.
Es startet keinen Systemhelfer und liest keinen Controller. Die bestehenden
Paket-, Erststart-, Download- und Status-Probeläufe bleiben getrennt verfügbar.
Die Oberflächenbilder aus `tests/render_control_center_normal_calibration.py`
sind ebenfalls vollständig synthetisch.

Die lokale AppImage-Version lautet `0.1.0.alpha2`. Sie verwendet den bereits
geprüften offiziellen Runtime-Präfix; das Buildmanifest bindet sämtliche
lokalen Dateien und markiert die Ausgabe weiterhin als nicht zur
Veröffentlichung freigegeben. Eine neue Quellen-/Lizenzzuordnung für die
exakten gebündelten Bibliotheken und die endgültigen Release-Artefakte erfolgt
vor einer späteren Veröffentlichung; der historische alpha1-Lock wird nicht
als Freigabe für neue Binärdateien übernommen. Kein Netzwerk, Hardwarezugriff,
Installieren, Dienststart, Firmwareupdate oder Push gehört zu diesem Schritt.

## Ergebnis des lokalen Builds

- 456 bestehende Python-Prüfungen in 21 Gruppen bestanden.
- 112 Qt-/QML-Prüfungen in elf Gruppen bestanden, einschließlich 13 Prüfungen
  der normalen Kombination und eines zusätzlichen echten Start-/Schließprozesses.
- 35 weitere Lizenz-, README- und Treiber-Dokumentpaketprüfungen bestanden.
- Alle fünf Probeläufe im finalen AppImage bestanden: Status, Pakete,
  Erststart, Release-Download und Kalibrierung; ausschließlich simulierte
  Daten, keine privilegierten Aufrufe oder Controllerzugriffe.
- DE/EN und kleine Fenster offline gerendert und visuell geprüft. Die
  Tastaturführung berücksichtigt auch nachträgliche Layoutänderungen.
- Ein gezielt reproduziertes Zeitfenster zwischen Threadende und zugestellter
  Rückgabe bleibt gesperrt. Verspätete Fehler beziehungsweise unklare
  Sitzungsrückgabe nach Dialogschluss können die Paketaktionen nicht freigeben.

Lokales Artefakt: `GameSir-Control-Center-PRE-ALPHA-0.1.0.alpha2-x86_64.AppImage`.
SHA256: `bf1e9578a214867927aa908e2e31a4ece486b5a62abdcc4212a66e532127ea46`.
Die Build-, Prüf- und Bilddateien bleiben lokal. Es fand kein neuer Live-Test
statt; die früheren Hardwareabnahmen behalten ihren abgegrenzten Umfang.
