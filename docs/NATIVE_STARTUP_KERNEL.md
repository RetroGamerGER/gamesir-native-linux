# Nativer Start: Kernelanbindung, offline geprüft

Ursprüngliche Offline-Anbindung vom 12. Oktober 2026 auf Grundlage von `1e17784`.
Am 13. Oktober bestätigte [Hardwaretest 003](HARDWARE_TEST_003.md) mit Build aus
`0de9077` den eigenständigen Start ohne Deadband, 120 s Eingaben/IMU und die
Rückkehr zu xpad; das Modul wurde danach wieder entladen. Die Beschreibung
unten dokumentiert den endlichen Testmodus. Dauerbetrieb und allgemeine
Hotplug-/PM-Automatik werden separat offline zur Alpha weiterentwickelt.
Die Alpha2 ergänzt im Dauerbetrieb eine einmalige Kernel-Claim-Sperre vor jedem
100a-Probe; die unten beschriebene freie passive Probe betrifft ausschließlich
den endlichen Entwicklermodus. [Aktueller Claim-Vertrag](ALPHA_RUNTIME.md).

## Aktivierung und Umfang

Der bisherige Testmodus mit `test_interface`/`test_pid` bleibt erhalten.
Zusätzlich existiert `bootstrap_mode=1`, standardmäßig aus, zusammen mit
`enable_output=1`. Dieser Modus ist mit den beiden festen Testparametern
unvereinbar. Es gibt weiterhin keine USB-Autoload-Aliase und kein `new_id`.

Im neuen Modus nimmt Probe passende, freie 3537:100a-Interfaces an beliebigen
Anschlüssen an. Die tatsächlichen Konfigurations-/IF0-/Endpoint-Deskriptoren
werden aus bereits vorhandenen Kernelobjekten geprüft; keine zusätzlichen
Deskriptorabfragen. Es gibt keine Ausgabepakete aus einem bloßen 100a-Probe.
Die erste vorhandene xpad-Bindung wird **nicht** automatisch übernommen.

Erst `GSN_BOOTSTRAP` am exklusiven Steuer-FD des ausgewählten 100a-Geräts
fordert einen einzelnen Start an. Zusätzlich werden CAP_SYS_ADMIN, Modulmodus,
ABI und Flags geprüft. Der Aufruf hält den FD und das Modul über die
Neuanmeldung hinweg am Leben. Der alte OUT-Mutex bleibt beim Warten frei,
damit der Disconnect-Callback abschließen kann.

Der Client unterstützt folgende explizite Formen:

```text
gsnative-ctl bootstrap /dev/gsnative-<Interface>
gsnative-ctl bootstrap /dev/gsnative-<Interface> --handoff-xpad
gsnative-ctl boot-info /dev/gsnative-<Interface>
```

Ohne `--handoff-xpad` wird nur ein freies beziehungsweise bereits passend
nativ gebundenes neues Interface angenommen. Das Flag erlaubt genau einen
Übergabeversuch eines durch den laufenden Wechsel zugeordneten 109c/IF0,
falls dessen Besitzer `xpad` ist. Fremde Treiber, IF1 und Geräte anderer
Anschlüsse werden dafür nicht abgebunden. Es gibt keinen globalen
xpad-Unload und keine Schleife zum wiederholten Ablösen/Anbinden.

## Dynamische Zuordnung und Wiederverbindung

Die temporäre Zuordnung besteht aus festgehaltenem Root-Hub-Objekt,
unmittelbarem Parent-Hub-Objekt und dessen Portnummer. Das Parent-Objekt
repräsentiert bereits den vollständigen konkreten Hub-Zweig. Referenzen
verhindern, dass nach Hub-Ersatz dieselbe Speicheradresse wieder als der alte
Hub gilt. Ein abgemeldeter Root/Parent und ein anderer Port passen nicht.
Die alte Geräteinstanz bleibt ebenfalls referenziert und wird ausgeschlossen.

Jeder Probe erhält einen neuen monoton vergebenen Instanztoken. Die Busadresse
wird nicht verwendet. Neue Instanzen müssen die belegten 109c-Deskriptoren
besitzen; unzugeordnete 109c-Geräte werden im Bootstrap-Modus abgelehnt.
Die USB-Seriennummern aus unseren Logs sind unterschiedlich je Modus und
werden nicht als gemeinsame UID behandelt. [Befund](NATIVE_STARTUP_OFFLINE.md).
Wird während der Übergangsfrist ein identischer anderer Dongle am selben
Port eingesetzt, lässt er sich ohne bestätigte gemeinsame UID nicht sicher
vom erwarteten Gerät unterscheiden. Die Topologiezuordnung ist keine
Authentifizierung; ein künftiger Test muss diesen manuellen Austausch ausschließen.

Es gibt eine gesperrte Liste getrennter laufender Startaufträge. Nur ein
passender Auftrag kann eine neue Instanz übernehmen. Nach Abschluss oder
Fehler verschwindet seine Übergangsreservierung. Ein Kontroll-FD kann das
historische Ergebnis mit `GSN_GET_BOOT_STATUS` noch nach dem alten Disconnect
lesen; dieser Status ist kein fortlaufender Gesundheitsnachweis der Runtime.

Abziehen beendet die alte Runtime. Bei erneutem Einstecken entsteht eine
neue passive 100a-Sitzung, soweit USB-Core das freie Interface diesem Treiber
zuweist; ein neuer Start braucht eine neue ausdrückliche Aktivierung. Das gilt
auch an einem anderen Anschluss. Eine bereits bestehende xpad-Bindung bleibt
bestehen. Eine dauerhafte Hotplug-Bindepolitik ist noch nicht eingerichtet.
Ein während des Wechsels umgestecktes Gerät wird nicht verfolgt; der alte
Auftrag bricht spätestens an seiner ursprünglichen Protokollfrist ab.

## Einmalige Initialisierung und Runtime-Übergabe

- Der bereits geprüfte C-Kern erzeugt neun 100a-Übergangspakete, verfolgt
  Disconnect/Neuanmeldung und erzeugt drei GIP-Init-Pakete plus drei Heartbeats.
- OUT bleibt unter dem Geräte-Mutex; Kernelpuffer sind heapbasiert. Completion,
  Länge, Zeitgrenze und Besitz werden geprüft. Während `USB_INTERFACE_BINDING`
  wartet der Worker; beim Abbau werden neue Ausgaben gesperrt.
- RX übergibt echte neue Pakete an denselben Startkern. Frische IMU und
  abgeschlossene Initialisierung sind erforderlich; ruhende Gamepad-Eingaben
  sind kein Fehler. Ein unbekannter Typ 03 ist kein Initialisierungs-ACK.
- Beim Erfolg werden Sequenzzähler und nächste Heartbeat-Frist genau einmal
  in die vorhandene Runtime übernommen. Der erste folgende Heartbeat verwendet
  Sequenz 7. Der anschließende Client-START übernimmt nur die verbleibende
  begrenzte Sitzung, ohne Init-Wiederholung oder Verlängerung der Frist.
- Es werden keine Motorimpulse automatisch ausgelöst. Die bestehenden
  Motoraufrufe und STOP/END bleiben erhalten. Reine Informationsaufrufe an der
  noch nicht vom Sitzungsclient übernommenen Bootstrap-Runtime beenden sie
  beim Schließen nicht; nach Übernahme gilt wieder der bisherige Close-Stop.

Die Runtime bleibt zeitlich begrenzt: Standard 30 s ab erfolgreicher Übergabe,
maximal 315 s per Modulparameter. Dies ist kein dauerhafter Produktionsbetrieb.
Die 30-s-Startfrist, 10-s-Neuanmeldungsfrist und Transferfristen gelten im
Protokollautomaten. Wartezeiten auf Kernel-Gerätesperren, Treiber-Callbacks
oder abschließende Bereinigung sind keine zugesicherte Echtzeitobergrenze.

## Fehler, Referenzen und Rückweg

Signal/Fehler stoppen den Auftrag. Ausstehende eigene Arbeit wird bei Bedarf
unter USB-Gerätesperre geordnet beendet; keine konkurrierende Input-/IIO-
Abmeldung während der abschließenden Neutralisierung. Der alte FD, das neue
Gerät, das Interface und die Übergangsobjekte besitzen getrennte Referenzen.
Ein nach Init-Abbruch noch gebundenes Gerät bleibt angehalten und diagnostizierbar;
kein automatisches USB-Reset, Clear-Halt, Rückbinden oder Wiederholen.

Die optionale xpad-Übergabe prüft den Besitzer unter USB-Gerätesperre.
Vor `device_driver_attach` wird diese Sperre freigegeben, weil der Driver-Core
sie selbst nimmt. Gewinnt inzwischen ein fremder Besitzer, endet der Versuch.
Gewinnt der eigene passende Probe, wird dessen bestehende Bindung akzeptiert.
Grundlage: installierte Kernelheader und die Primärquellen
[Driver-Core](https://github.com/torvalds/linux/blob/master/drivers/base/dd.c),
[USB-Core](https://github.com/torvalds/linux/blob/master/drivers/usb/core/driver.c).

Für den nächsten Hardwarelauf bleiben Ausgangszustand und jede konkrete
Zustandsänderung separat freizugeben. Nach Erfolg zunächst den vorhandenen
STOP/END-Pfad verwenden, anschließend Identität und xpad-Funktion prüfen.
Bleibt 109c oder eine ungebundene Instanz zurück, anhalten und den konkreten
Rückweg freigeben lassen. Der alte, hardwaregeprüfte Modulbuild wurde vor dem
Neubau unter seinem SHA256 in `build/preserved-modules/` gesichert. Der spätere explizite Hin-/Rückweg ist in Hardwaretest 003 separat belegt.

## Nachweise und offene Punkte

`make test-startup` prüft den gemeinsamen C-Kern und 55 Szenarien mit tatsächlich
aus dem Kerneladapter entnommenen Funktionen unter ASan/UBSan. Künstliche
USB-Bäume, Geräteobjekte, Zeit und Systemaufrufe ersetzen Hardware. Enthalten:
Paketvergleich gegen 15 gespeicherte Transfers, direkte/Hub-Anschlüsse,
getrennte Übergangsreservierungen, Umstecken/Hub-Ersatz, fehlende Berechtigung,
fremder Besitzer, verlorenes Attach-Rennen, verzögerter Bindungsabschluss,
Disconnect vor/nach Neuanmeldung, Signal, kurze/fehlgeschlagene Transfers,
fehlende IMU, ausgeglichene Referenzen und genau eine Sequenzübergabe.

Der echte Client wurde zusätzlich für Bootstrap ohne/mit Übergabeflag,
Fehler und ungültige Argumente gegen künstliche Systemaufrufe geprüft.
Die Motor-Sendetests prüfen jetzt auch, dass während Unbind kein neuer Impuls
beginnt, während das abschließende Nullpaket möglich bleibt.

`make test` und `make kernel-analyze` bestehen. Der Modulbau verwendet die
vorhandenen Header für 7.2.9-2-garuda, LLVM, W=1 und Werror. Checkpatch und
Clang Static Analyzer über fünf Übersetzungseinheiten sind ohne Befund.
[Build-/Testbericht und Hashes](NATIVE_STARTUP_KERNEL_RESULTS.json).

Die Simulation ersetzt weder USB-/Input-/IIO-Core noch echte Parallelität und
Allocation-Fault-Injection. Vollständigkeit eines Cold-Start-USB-Mitschnitts, Hardware-Rennen,
Funkverlust, Suspend/Resume und dauerhafte automatische Bindung bleiben offen.
Ein Suspend/Reset hält das Gerät weiterhin an; kein automatischer Resume.
Gyro-Skalierung und kalibrierte SDL-Ausgabe bleiben unabhängig davon offen.
