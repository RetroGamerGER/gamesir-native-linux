Historischer Sprint-002-Architekturentwurf. Der inzwischen implementierte
Sprint-003-Umfang ist in ARCHITECTURE.md und KERNEL_PROTOTYPE.md abgegrenzt;
die langfristigen Anforderungen dieses Entwurfs bleiben bestehen.

Nativer G7-Pro-Treiber: vorbereiteter Aufbau
==========================================

Verbindliche Anforderungen
-------------------------

Deadband bleibt nutzbar. Normales Spielen, IMU und Impulse-Trigger werden
vom nativen Laufzeitpfad bedient, unabhängig von einer Deadband-Sitzung.
Langfristig verwendet ein Deadband-Adapter eine definierte Schnittstelle
des Treibers und lässt dessen Gamepad-/Sensorbetrieb weiterlaufen.
Die installierte Deadband-Anwendung wird für diese Vorbereitung nicht geändert.

Gemeinsamer Besitzer der USB-Schnittstelle
-----------------------------------------

Ein USB-Treiber besitzt Interface 0 und verarbeitet Interrupt-IN 0x82.
36-Byte-GIP-Berichte erzeugen Gamepad-Ereignisse, 64-Byte-Telemetrie erzeugt
IMU-Rohwerte und zusätzliche Tasten. Der erfolgreiche Mitschnitt belegt
beide Paketarten während derselben Sitzung; er belegt noch keine fertige
Kernel-Laufzeitimplementierung. Interface 1 bleibt außerhalb dieses Besitzers.

Ein geordneter Sendepfad serialisiert Initialisierung, Heartbeats, nötige
Antworten und Motorsteuerung auf OUT 0x02. Keine USB-Übertragung aus
Input-/Force-Feedback-Callbacks unter einem Spinlock. Fehler führen in einen
sichtbaren Fehlerzustand, ohne Reset, Identitätswechsel oder neue Versuche.
Bei Abgabe/Disconnect werden Empfang und Arbeiten beendet und alle
Ausgabegeräte sauber abgemeldet. Offene Steuerungsdateien müssen danach
ENODEV liefern, ohne freigegebene Gerätestrukturen zu benutzen.

Native Initialisierung muss die dokumentierte 100a→109c-Übergangssequenz
eigenständig beherrschen, statt Deadband als Starter vorauszusetzen.
Die neun Pakete sind im C-Kern vorbereitet und gegen den Mitschnitt geprüft.
Ein späterer Treiber muss die Übergabe über eine Neuanmeldung am selben
physischen Port verfolgen. Mindestens fünf Sekunden Abstand zwischen
Identitätswechseln, kein automatisches Wiederholen und kein erfundener
Rückschaltbefehl. Auswahl, Rückgabe und xpad-Konkurrenz werden erst in einem
gesondert freigegebenen Integrationstest geprüft. USB-IDs allein garantieren
keinen korrekten Treiberbesitz.

Ausgabegeräte nach der SDL-Prüfung
--------------------------------

1. Normales evdev-Gamepad: Tasten, D-Pad, vier Stickachsen, zwei analoge
   Trigger und FF_RUMBLE für die beiden Griffmotoren.
2. Separates evdev-Sensorgerät: INPUT_PROP_ACCELEROMETER, sechs Sensorachsen,
   gleiche eindeutige uniq wie das Gamepad, positive verifizierte Auflösungen.
   Erst nach belegter Skalierung, Orientierung und Bias veröffentlichen.
3. Ergänzendes IIO-Gerät: sechs rohe vorzeichenbehaftete 16-Bit-Kanäle,
   optional gepufferte Ausgabe mit expliziter Host-Zeitbasis. Keine erfundene
   SCALE-Angabe und keine unbelegte Gerätezeit.

Die SDL-Kompatibilität ist für den evdev-Weg offline bestätigt. Die Auswahl
dieses Wegs gegenüber HIDAPI, echte udev-Klassifizierung/Berechtigungen und
Hotplug bleiben Integrationstest-Aufgaben. Die künstlichen Skalen im
SDL-Test werden niemals in den Treiber übernommen. IIO ist keine automatische
SDL-Anbindung. Details und Nachweise stehen in SDL-SENSOR-ERGEBNIS.rst.

Der portable Umrechnungskern src/gs_sensor.c verlangt extern belegte
Skalierung, Achsenzuordnung und Bias-Behandlung. Er unterstützt rationale
Faktoren vor der ganzzahligen Input-Ausgabe. Noch ist kein verifiziertes
Geräteprofil vorhanden. SDL-SKALIERUNG-UND-ACHSEN.rst und
IMU-STATISTIK-UND-SENSORIDENTIFIKATION.rst dokumentieren die Capture-
Statistik und die noch fehlenden Nachweise. Zusätzlich stellt
gs_accel_convert_experimental den vom Nutzer angenommenen experimentellen
Maßstab von 8192 Zählern/g bereit. Der Aufrufer übergibt den austauschbaren
rationalen Faktor aus dem Profil. Ausgabe: Mikrometer/s² in Rohachsenfolge,
einschließlich Schwerkraft, ohne angenommene Bias-Korrektur. Der Rückgabewert
GS_SENSOR_EXPERIMENTAL kennzeichnet den unbestätigten Maßstab. Weder ein
Gyrofaktor noch Prüfkennzeichen oder eine SDL-Freigabe werden daraus
abgeleitet. Details: EXPERIMENTELLE-BESCHLEUNIGUNG.rst.

Vier Motoren und Deadband-Schnittstelle
-------------------------------------

Der Protokollkern verwaltet LT, RT, linken Griff und rechten Griff getrennt.
FF_RUMBLE aktualisiert nur die Griffmotoren. Eine zusätzliche versionierte
Steuerungsschnittstelle soll alle vier Kanäle mit expliziter Maske und
begrenzter Laufzeit ansprechen. Ein Stopp oder Ablauf eines Triggermotors
darf die anderen Kanäle nicht versehentlich löschen. Gleicher Motor aus zwei
Quellen benötigt eine dokumentierte Prioritäts-/Besitzregel. Gleichzeitige
FF- und Steuerungsaufrufe werden im Treiber serialisiert.

Vorgesehene ABI 1: feste Ganzzahlfelder ohne Prozesszeiger, GET_INFO mit
Version/Fähigkeiten/Zustand, SET_HAPTICS mit Kanalmaske, vier Prozentwerten,
1..400 ms und reservierten Nullfeldern. Unbekannte Versionen/Flags zurückweisen.
Dies ist eine Schnittstellenspezifikation, noch keine implementierte ioctl-ABI.
Normale SDL-Spiele kennen diese Zusatzschnittstelle noch nicht; Unterstützung
für SDL_RumbleGamepadTriggers beziehungsweise andere Spiele-APIs braucht
zusätzliche Vermittlung und darf nicht durch FF_RUMBLE vorgetäuscht werden.

Der spätere Deadband-Adapter fragt Fähigkeiten ab und ändert bekannte
Einstellungen über validierte Vorgänge mit exklusivem Schreiber, Generation,
explizitem Commit und Rückleseprüfung. Keine allgemeine USB-Passthrough-API.
Persistentes Profilschreiben gehört nicht in die normalen Motoraufrufe.
Polling-/Identitätsänderungen, die eine Neuanmeldung verursachen, dürfen nicht
als unterbrechungsfreie Konfiguration dargestellt werden.

Bis zur Adapterunterstützung muss die bisherige libusb-Übergabe an Deadband
weiter möglich bleiben. Damit kann Deadband den Treiber zeitweise ablösen;
gleichzeitiges Spielen ist auf diesem alten Weg nicht zugesichert. Der
Quellcode verwendet generisches Ablösen/Anbinden, kein festes xpad-Attach.
Welcher Treiber danach tatsächlich gewinnt, ist noch nicht hardwarevalidiert.

Stand dieser Vorbereitung
------------------------

Vorhanden sind gemeinsamer C-Protokollkern, Motorzustandslogik, ausgeführter
Capture-Vergleich, SDL-Bibliothekstests und Architektur-/Integrationsvorgaben.
Es gibt noch keinen vollständigen USB-Kernel-Treiber, keine registrierten
Ausgabegeräte und keine installierte Steuerungsschnittstelle. Daher wird
keine native Hardwarekompatibilität oder gleichzeitige fertige SDL-Unterstützung
behauptet. Die folgenden Schritte sind USB-/Lebenszyklusimplementierung,
Kernel-Übersetzungsprüfung und separat freizugebende Integration; für
kalibrierte SDL-IMU ist zuvor die physikalische Skalierung zu belegen.
