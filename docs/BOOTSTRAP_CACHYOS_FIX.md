> Public export: personal tester, host and path references were anonymized. Historical evidence hashes refer to the private originals.

# Bootstrap: Vergleich Garuda/CachyOS und Offline-Korrektur

Stand: 15. Oktober 2026. **Der korrigierte Revision-4-Bootstrap mit 150 Sekunden
nativen Eingaben/IMU ist auf dem CachyOS test host bestanden.** Native Verwaltung
bleibt aktiv, Autostart bleibt aus. [Aktuelle Ergebnisse und Grenzen](#revision-4-korrigierter-bootstrap-realtest-bestanden).
Dieser chronologische Bericht erhält auch die früheren Fehlstarts, Rückwege,
Offline-Korrekturen und einzelnen Freigaben. Deren damalige Zustände sind keine
aktuellen offenen Aktionen oder wiederverwendbaren Testfreigaben.

## Gesicherte Ausgangsbefunde

| Beleg | Beobachtung | Grenze |
| --- | --- | --- |
| Garuda, Hardwaretest 003 vom 13. Oktober | Bootstrap Exit 0, neue 109c-Instanz an gs_native, 120 s Eingaben/IMU, anschließend geprüfter Rückweg | Früherer Build und anderer USB-Pfad; keine Garantie für alle Ereignisreihenfolgen |
| Garuda, Nutzerangabe am 15. Oktober | [tester] führte `gamesir-native resume` nach der Diagnose selbst aus und meldete funktionierenden Betrieb | Die gezeigte unmittelbare Antwort ist paused=false/devices={}; keine zusätzliche neue Bindungs-/IMU-Messung durch Codex |
| CachyOS, zwei freigegebene Versuche vom 14. Oktober | Bootstrap endet mit -19/ENODEV; anschließend neue 109c an xpad | Keine USB-Paketaufzeichnung oder Fehlerstufe der beiden fehlgeschlagenen Starts |
| Quell-/Buildstand | Gemeinsame C-Protokollquellen; tatsächlicher GCC-/DKMS-Bau auf CachyOS bestanden, Garuda-Bau mit Clang | Compiler-/Hub-/Timing-Ursache lässt sich allein aus diesen Logs nicht beweisen |

Die gesicherten Übergangsdaten aus `fixtures/startup-capture.json` verlangen
neun vollständige erfolgreiche Acht-Byte-Transfers. Der letzte endet rund
195 ms nach dem ersten Submit, die gespeicherte Entfernung folgt rund
420 ms nach dem ersten Submit. Die vorhandene Referenz bildet einen konkreten
beobachteten Ablauf ab; Reihenfolgen zwischen USB-Callbacks und unserem Worker
müssen unabhängig davon korrekt behandelt werden.

Die CachyOS-Journale enthalten nur den Endfehler. ENODEV ist kein Timeout;
aus einem neuen PID 109c folgt weder vollständige Initialisierung noch ein
gültiger Besitznachweis. Der fehlgeschlagene alte Versuch berechtigt nicht
zur späteren Übernahme einer beliebigen 109c-Instanz.

## Reproduzierte Softwarefehler und Korrektur

Der bisherige Adaptertest rief den Disconnect direkt nach dem neunten
Übergangs-OUT auf. Drei zusätzliche künstliche Reihenfolgen schlagen mit dem
unveränderten Adapter fehl:

1. Neun OUTs sind vollständig abgeschlossen. USB-Core markiert das alte Gerät
   bereits als NOTATTACHED, der eigentliche Disconnect-Callback kommt 30 ms
   später. Ein zwischenzeitlicher Worker beschreibt das sterbende Interface
   erneut und scheitert mit EBUSY in WAIT_REMOVE.
2. Im selben Wartefenster endet ein erfolgreicher RX-Aufruf mit ENODEV beim
   erneuten Einreichen seines Empfangs-URB. Dieser Fehler setzt die Runtime
   bislang auf FAULTED, der Start endet mit ENODEV.
3. RX meldet ENODEV, während der neunte synchrone OUT noch läuft. Obwohl dieser
   danach vollständig erfolgreich endet, wurde die Runtime bereits angehalten.
   Der folgende Worker beendet den Bootstrap mit ENODEV.

Der neue Adapter behandelt diese Reihenfolge gezielt: Nach neun nachgewiesenen
Voll-Completions wartet er ohne weitere OUTs oder Deskriptorprüfungen auf den
wirklichen Disconnect und überwacht die unveränderte Frist. Die begrenzten
RX-Abbaustatus dürfen den alten Empfang im Wartefenster beziehungsweise während
des bereits laufenden letzten OUTs beenden. Das ist keine Bestätigung des
letzten OUTs: Nur dessen anschließend vollständige erfolgreiche Completion
berechtigt zum erwarteten Übergang. Fehler oder kurze OUTs bleiben Fehler.

Die Entfernung muss weiterhin durch den echten Disconnect-Callback bestätigt
werden. Neuanmeldung, Topologie-/Hub-Lebensdauer, exklusiver Interfacebesitz,
vollständige Initialisierung und frische IMU bleiben erforderlich. Weder ein
PID-Wechsel allein noch ein verzögerter Callback autorisiert eine fremde
109c-Instanz. Der gemeinsame Protokollautomat und die gesicherten Paketbytes
werden nicht gelockert; es gibt keine erneuten Sendungen oder Resets.

**Einordnung:** Diese Softwarefehler sind reproduziert und gezielt korrigiert.
Zwei reproduzierte Pfade liefern denselben Fehlercode wie die Hardwarelogs.
Welcher Pfad den historischen CachyOS-Abbruch ausgelöst hat, ist damit noch
nicht bewiesen. Ein tatsächlich fehlgeschlagener OUT würde weiterhin eine
gesonderte Ursache haben; er wird nicht zum erfolgreichen Moduswechsel erklärt.

## Manager: Fehler, Anwesenheit und Diagnose trennen

Ein neuer Test reproduziert außerdem, dass `failed` bei kurzer Geräteabwesenheit
in `gone` überging. Eine folgende unbesessene 109c-Instanz konnte dadurch die
alte Fehleranzeige und Lease verschwinden lassen. Die Berechtigung zur neuen
Übernahme fehlte weiterhin; der scheinbar leere Status erschwerte die Diagnose.

Der Manager führt die Abwesenheitsdauer jetzt getrennt vom Protokollzustand.
`failed/blocked` bleibt über die USB-Lücke erhalten; die neue fremde Instanz
wird sichtbar blockiert. Unbekannte/unvollständige Scans zählen nicht zur
kontinuierlichen Abwesenheit. Bereinigung eines ungelösten Fehlers verlangt
einen belegten Rückweg oder ausdrücklich pausierte Verwaltung mit mindestens
zehn Sekunden bestätigter physischer Abwesenheit. Eine bereits an xpad gebundene
normale Ersatzinstanz darf nur beobachtet, nicht übernommen werden.

Für abgeschlossene Bootstrapaufrufe werden Exitcode, Timeoutstatus,
Quellinstanz und ein vorhandener Kernel-Statusdatensatz einschließlich
Fehlerstufe gesichert. Pro Diagnose bleiben höchstens 4 KiB Text und dessen
Bytezahl/Hash erhalten. Der Hash gilt ausdrücklich für den bereits durch den
Supervisor begrenzten gemeinsamen stdout/stderr-Text, nicht notwendigerweise
für einen größeren ursprünglichen Prozessstrom. Bis zu acht letzte Fehler
bleiben nach bestätigter Bereinigung mit einer Auflösungsangabe sichtbar.
Neue gespeicherte Felder sind beim Laden typ- und größengeprüft.

Diagnose und Fehlerhistorie sind keine Besitznachweise. `boot_proof()` und
quergeprüfte Kernel-Tokens entscheiden unverändert über Übernahme/Bereinigung.
Die neue Historie blockiert nach bestätigtem Rückweg nicht dauerhaft
`returned=true`; sie bleibt getrennt vom aktuellen Geräte-/Fehlerzustand.

## Aussagekräftigere Diagnose beim nächsten freigegebenen Lauf

Der Kernel protokolliert einmal pro beendetem Bootstrap zusätzlich Fehlerstufe,
Schritt, ausstehende Länge, vollständigen Übergang und den letzten tatsächlich
beendeten OUT mit Status/Ist-/Solllänge und Sendezähler. Diese Angaben ändern
keine UAPI und berechtigen zu keinen neuen USB-Operationen. Das Kerneljournal
muss im späteren freigegebenen Hardwarelauf separat erhalten bleiben; es ist
nicht Teil des stdout des Steuerclients.

Die ursprünglichen Aufzeichnungen bleiben unverändert. Fehlende Fehlerstufen
werden daraus nicht nachträglich erfunden.

## Nachweise und Ergebnis

- Vollständiges `make test` bestanden; darunter 135 Managerfälle, 154 Tests mit
  tatsächlich aus dem Adapter entnommenen Funktionen unter ASan/UBSan, 54
  Claim- und 22 FF-Lebensdauerfälle. Gemeinsamer Startupkern weiterhin gegen
  15 gespeicherte Sendeaufträge und 75 Transferfehlerfälle geprüft.
- Drei Altcode-Negativkontrollen: EBUSY/ENODEV/ENODEV; dieselben Reihenfolgen mit
  Korrektur erfolgreich und genau 15 Sendeaufträgen bis zur Übergabe.
  Alte Kernelquelle: SHA256
  `746bc2a8e31c01f9fc1f960cf0e3352d79f71fc7bfe751699e35398efd504cfd`,
  Commit `9e8e531`. Die Kontrolle nutzt echte entnommene Adapterfunktionen,
  künstliche USB-Objekte und vorgegebene Ereignisreihenfolgen.
- Neue Adapterfälle umfassen die vier RX-Abbaustatus, erfolgreiche Completion
  und fehlgeschlagenes Resubmit, Fehler vor OUT9, kurzen/fehlgeschlagenen OUT9,
  fehlenden Callback mit Fristablauf, Port-/Hub-Ersatz, fremden Besitzer,
  Abbruch, Suspend und manuelles Unbind.
- Managerregressionen prüfen kurze/lange USB-Lücken, unbekannte neue 109c an
  xpad oder gs_native, Dienstneustart, keine erneute Ausgabe/Übernahme,
  kontinuierlichen Abwesenheitsnachweis, beobachteten normalen Rückweg sowie
  begrenzte/ungültige/mehrdeutige Diagnose- und Zustandsdaten.
- `make kernel-analyze` bestanden: Modul gegen `7.2.10-1-garuda` mit Clang,
  `W=1/-Werror`, keine Compilerwarnung, keine Autoload-Aliase, checkpatch ohne
  Quellwarnungen und keine Befunde des Clang-Analyzers in fünf Einheiten.
  Neues Modul wurde weder geladen noch installiert. Neuer CachyOS-/GCC-Zielbau
  und echte USB-Parallelität wurden in diesem Offline-Auftrag nicht geprüft.

Ein checkpatch-Hinweis auf einen fehlenden Kommentar zur Acquire-Publikation
wurde durch die Erklärung des vorhandenen Publish/Acquire-Vertrags behoben;
die Barriere selbst bleibt unverändert. Die vollständige funktionale Suite
bestand vor dieser reinen Kommentarkorrektur; Adaptertest und Kernelbau/
statische Analyse wurden anschließend für den endgültigen Quellstand erneut
geprüft.

Lokale Berichte: `build/bootstrap-fix-full-tests.log`,
`build/bootstrap-fix-kernel-analysis.log`, `build/results/kernel-*.json`,
`build/results/bootstrap-removal-negative-control.json` und
`build/results/bootstrap-removal-fixed-control.json`.

**Entscheidung:** Die reproduzierten Softwarefehler sind offline korrigiert.
Ein neuer positiver CachyOS-Hardwarebeleg fehlt. Vor einer späteren Freigabe
zuerst den tatsächlichen Zielzustand und einen Build mit dessen passenden
Headern prüfen; danach genau einen kontrollierten Start mit der erweiterten
Diagnose planen. Keine Schleife, kein unbesessenes 109c übernehmen und keine
Änderung des laufenden Garuda test host-/CachyOS test host-Betriebs in diesem Auftrag.

## Folgeschritt am 15. Oktober: Zielbau und getrennte Installation

Der anschließende Nutzerauftrag erlaubte zunächst neue lesende SSH-Prüfungen
und den unprivilegierten Modulbau auf dem CachyOS test host. Separat gab [tester]
erst das Garuda test host- und danach das CachyOS test host-Paketupdate sowie einen pausierten
Dienststart frei. Resume und neuer Bootstrap auf dem CachyOS test host bleiben gesperrt. Diese Freigaben
ändern die Grenzen der vorangegangenen Offline-Arbeit nicht rückwirkend.

| Rechner | Frisch geprüfter Stand | Ergebnis dieses Folgeschritts |
| --- | --- | --- |
| CachyOS test host | `7.2.9-2-cachyos-deckify`, Kernel-/Headerpakete jeweils `7.2.9-2`, GCC 16.2.1 | Zielbau, Paketupdate Revision 2 → 3 und danach separat freigegebener pausierter Dienststart bestanden; active/running, weiter Autostart deaktiviert |
| Garuda test host | `7.2.10-1-garuda`, passende vorbereitete Clang-Header | Separat freigegebenes Paketupdate Revision 1 → 3 einschließlich tatsächlichem DKMS-Neubau bestanden |

### CachyOS vor dem Paketupdate: Bau bestanden, System unverändert

Vor und nach dem Bau: genau ein GameSir-Dongle am Hub-Port `1-3.2`,
`3537:100a`, Bus 1/Adresse 4, IF0=xpad, IF1=usbhid. Dienst `inactive/dead/disabled`,
kein geladenes `gs_native`. Kernel, Boot-ID, Headerhashes, Paketbestand,
Dienst- und USB-Zustand stimmen zwischen beiden Prüfungen überein. Die private
Managerdatei war ohne erhöhte Rechte nicht lesbar; ihre Pause/leeren Leases
sind deshalb vor einer späteren Installation erneut privilegiert zu prüfen.

Der vorhandene gemeinsame Compilerhelfer baut die unveränderten Paketquellen
aus Commit `bffdeea` gegen die tatsächlichen Zielheader, mit GCC/Binutils und
`W=1/-Werror`. Kein `modules_install`, DKMS-Aufruf, Modulladen, Dienststart oder
Geräteöffnen. Modulmetadaten: `0.1.0.alpha3`, vermagic
`7.2.9-2-cachyos-deckify SMP preempt mod_unload`, keine Autoload-Aliase,
srcversion **`C6818C24711721D136684D5`**. Modul-SHA256:
`0c6c9c6d31c48895df0cb2f40f9d910ffaae41cdc0099123ddf48c0548fed4dd`.
Dies ist ein echter GCC-Zielbau, aber weiterhin kein Bootstrap-Hardwarebeleg.

Das identische Arch-Paket ist im Benutzer-Bauordner dauerhaft bereitgelegt;
`pacman -Up` zeigt ausschließlich `gamesir-native-dkms 0.1.0.alpha3-3`.
Paket-SHA256 auf beiden Rechnern:
`7c36d480d6e0fbb205738c5b8054f7d38cf94528aaf0f3d02de7a8cc854106e7`.
Die bereits geprüften 18 Boot-Hook-/Konfigurationsdateien stimmen mit dem
vorherigen Zielaudit überein. Für das kompilierte interne Limine-Werkzeug lag
zuvor wegen eines Textlesefehlers kein Hash vor; sein jetziger Hash ist
inventarisiert, keine nachgewiesene Änderung daraus ableiten.

Private Belege und Bauartefakte:
`.local/compatibility/20261015T125906Z-CachyOS test host-bootstrap-revision3/`.
Remote-Bauordner:
`/home/example/gamesir-native-build/20261015T125906Z-bootstrap-revision3/`.

### Garuda test host: freigegebenes Update bestanden

Die vollständige interaktive Transaktion zeigte genau ein Paket,
`gamesir-native-dkms 0.1.0.alpha3-1 → 0.1.0.alpha3-3`; erst danach wurde
bestätigt. Vorher keine GameSir-Geräte, keine native Bindung, Referenzzähler
null, leere gespeicherte Leases und fehlerfreie aktuelle Managerabfrage.
Der unveränderte Upgrade-Hook pausierte/stoppte den Dienst und entlud nur
das unbenutzte `gs_native`. Kein globales Entladen von xpad/industrialio.

Nachher: DKMS für `7.2.10-1-garuda` installiert, tatsächliche Baulogs ohne
Compilerwarnungen/-fehler, korrekte vermagic und dieselbe neue srcversion
`C6818C24711721D136684D5`. 71 Nutzdateien byte-/rechtegeprüft;
`pacman -Qkk` meldet 91 Einträge, null verändert. Installierte Kernelquelle
stimmt mit der geprüften Korrektur überein. Andere Pakete, insbesondere die
Steam-Komponente, blieben unverändert. Der bekannte DKMS-Hinweis zu `CLEAN`
ist kein neuer Baufehler und wurde nicht automatisch repariert.

Vorhandene Garuda-Hooks erzeugten Snapper 81/82 und bauten beide
Dracut-Initramfs. Die nachlaufende Snapshot-Menüerzeugung endete erfolgreich;
`grub-btrfs.cfg` ist vorhanden. Im Kerneljournal des Updatefensters nur die
erwartete Deregistrierung des entladenen Treibers, keine neue Warnung/Oops.
Abschluss der Installation: Dienst `inactive/dead`, Autostart **enabled
erhalten**, Modul ungeladen, `paused=true`, Leases leer, weiterhin kein
GameSir-Gerät. Codex hat danach keinen Start/Resume ausgeführt. [tester] fragte
anschließend nach den manuellen Startbefehlen; eine erfolgreiche erneute
Übernahme wird daraus noch nicht behauptet.

Private Sicherungen von altem Modul, Manager/Upgrade-Helfer, Baulogs,
Vor-/Nachzuständen und geprüften Hashes:
`.local/integration/20261015T130245Z-Garuda test host-bootstrap-revision3/`.

### CachyOS test host: freigegebenes Paketupdate bestanden

Nach gesonderter Freigabe inklusive Passwortabfrage und der benannten Hooks
wurde am 15. Oktober genau **ein Paket von Revision 2 auf 3** installiert.
Die vollständige interaktive Transaktion wurde vor der Bestätigung gelesen;
keine zusätzlichen Pakete, System-/Kernelupgrades oder Datenbankaktualisierung.
Privilegierte Vorprüfung: gespeicherte Pause aktiv, Leases leer, Dienst
inactive/dead/disabled, kein Manager-Socket, Modul ungeladen, keine native
Bindung, Paketlock/Jobs/Neustartmarkierungen leer.

Die erste lesende Prüfung traf nach laut [tester] ausschließlich manueller
Funk-Wiederverbindung 109c/Adresse 10 mit xpad und ungebundenem IF1 an.
Dies wurde vor der Passwortabfrage gemeldet. Während der Passwortphase
erschien das Gerät wieder als 100a/Adresse 11 mit xpad/usbhid. Der auf die
alte Adresse festgelegte Helfer brach vor `pacman -U` ab. Für das reine
Paketupdate wurde diese unnötig starre Vorprüfung korrigiert: genau ein
bekannter 100a- oder 109c-Zustand mit passenden xpad-Interfaces am ausgewählten
Port, aktuelle Adresse frisch erfassen, keine Modul-/Dienst-/Besitzfreigabe
lockern. Der neue private Laufordner erhält den vorherigen Abbruchbeleg.
Die einzige tatsächliche Pakettransaktion begann und endete unter derselben
100a/Adresse 11. Kein USB-Befehl, Identitätswechsel oder Rückbindevorgang
durch Codex. Die strengere Instanz-/Besitzprüfung eines Hardware-Bootstraps
ist davon unabhängig und unverändert.

Prüfergebnis nach dem Update:

- DKMS meldet `installed` für `7.2.9-2-cachyos-deckify`. Das tatsächliche
  neue Baulog belegt GCC/Binutils, `W=1/-Werror`, Exit 0, keine Compilerwarnung
  oder Fehler. Der bekannte separate DKMS-CLEAN-Hinweis bleibt dokumentiert.
- Installiertes Modul mit passender vermagic, ohne Autoload-Aliase und mit
  neuer srcversion `C6818C24711721D136684D5`. Installierte Kernelquelle
  bytegleich zur Korrektur; SHA256
  `9be8da48d50efcefd7cbcf793120754e2d7a781afb7417180d09c2e1fb7142fc`.
  Komprimiertes installiertes Modul: SHA256
  `d01a392b881c0bc22db18df0a901570aed9a2c8167a2dc37227ed0f65b445179`.
  Kein Vergleich verschiedener Kernelmodule auf Bytegleichheit behauptet.
- 71 Paketnutzdateien byte-/rechtegeprüft; `pacman -Qkk`: 91 Einträge,
  null verändert. Nur natives Paket 2→3; Steam-/Gamescope-Pakete unverändert.
- Snapper 81/82, tatsächliche Initramfs-Erzeugung und Limine-Aktualisierung
  erfolgreich; Änderungen an `/boot/limine.conf` und Snapshot-Verlauf mit
  Vor-/Nachhashes gesichert. Kein Neustart.
- Dienst **inactive/dead/disabled**, Modul **ungeladen**, vollständiger
  gespeicherter Managerzustand inhaltlich unverändert, **paused=true/Leases leer**. 100a/Adresse 11,
  Port 1-3.2, IF0/xpad und IF1/usbhid vor/nach Update sowie beim Abschluss
  identisch. Steam-PID/Startzeit und vorbereitete Header unverändert.
- Im Kernelprüffenster zwei bereits bekannte AMDGPU-CRB-Konfigurationswarnungen
  mitgesichert; kein anderer Warnungs-/Oops-/Absturzbefund. Sie sind kein
  GameSir-Stacktrace; daraus keine neue Ursachendiagnose ableiten.
  Ein parallel gestarteter `plocate-updatedb`-Index endete erfolgreich.
  Abschließend keine offenen Systemd-Jobs/Neustartmarkierungen.

Private Originalzustände, alte Modul-/Manager-/Baulogsicherungen, vollständiger
Transaktionstext und geprüfte Hashliste:
`.local/integration/20261015T131551Z-CachyOS test host-alpha3-revision3/`.
Ergebnis: Beide Rechner haben den nativen Paketquellstand Revision 3.
Die neue CachyOS-Bootstrapabnahme ist weiterhin offen; während dieses
Paketupdates kein Dienststart, Autostart, Modulladen, Motor-/Sensor-/Eingabetest
oder Bootstrap ausgeführt. Der danach separat freigegebene Start folgt unten.

### CachyOS test host: Dienst pausiert gestartet

[tester] gab anschließend ausschließlich den einmaligen Dienststart inklusive
Passwortabfrage frei; danach nur lesende Prüfungen. Vorher erneut Revision 3,
passender installierter Modulhash/srcversion, unveränderte Unit-/Manager- und
Kernelquellen, keine Drop-ins, inactive/dead/disabled, fehlendes Modul und
Manager-Socket sowie private Pause/Leases geprüft. Keine Freigabe aus dem
Paketupdate für den Start vorausgesetzt; eigener neuer Auftrag.

Am 15. Oktober um 15:40 MESZ wurde genau einmal
`/usr/bin/systemctl start gamesir-native.service` ausgeführt. Die Unit lädt
industrialio und gs_native mit bootstrap_mode=1, enable_output=1 sowie
persistent_mode=1. Fehlende Modaliases allein wären keine vollständige
Übernahmesperre: Die statische USB-ID-Tabelle ist vorhanden. Entscheidend sind
die erforderlichen einmaligen Claims für persistente 100a/105e-Probes und der
nachgewiesene Pending-Handoff für 109c. Ein frisch geladenes Modul besitzt
keine solchen Freigaben; der aus der Datei pausiert gestartete Manager
erzeugt keine neuen.

Nachweis:

- Dienst active/running, Result=success, MainPID 16541, NRestarts=0;
  Autostart weiter disabled. Kein `enable`, `resume`, `release` oder zweiter Start.
- Industrialio und gs_native tatsächlich geladen, neue srcversion
  `C6818C24711721D136684D5`, alle drei genannten Parameter Y,
  Referenzzähler 0, keine native USB-Bindung.
- Fünf lesende Statusproben: paused=true, devices={}, keine Scan-/Portfehler.
  Gespeicherte Leases leer, keine neuen attempted-Tokens oder Budgeteinträge.
  `devices={}` beschreibt den leeren Verwaltungsumfang, keine physische
  Abwesenheit des Dongles.
- USB-Zustand und Geräteinstanz exakt erhalten: 100a/Adresse 11, Port 1-3.2,
  Inode 51005, IF0/xpad, IF1/usbhid. Steam-PID/Startzeit unverändert.
- Der erste Manager-Tick pflegte boot_id, alte budgets/attempted und das neue
  recent_failures-Feld. Dies ist keine neue Controllerinitialisierung und
  keine Kalibrierungs-/Firmwareänderung. Pause und Besitzstand bleiben erhalten;
  eine bytegleiche Zustandsdatei ist nach legitimem Bootwechsel nicht erforderlich.
- Kerneljournal: Registrierung des USB-Treibers sowie Meldungen über ein
  externes Modul und fehlende Signatur beziehungsweise Schlüsselvertrauen
  (Kernel-Taint). Das nachgewiesene Laden war erfolgreich. Kein Oops-,
  Lockup- oder WARN-Befund im aufgezeichneten Fenster. Keine Signaturreparatur
  oder Systemkonfiguration geändert.

Private Vor-/Nachzustände, Einmalaktion, vollständige Status-/Journalbelege
und geprüfte Hashliste:
`.local/integration/20261015T133659Z-CachyOS test host-paused-start-revision3/`.
Die Prüfung belegt den pausierten Bereitschaftszustand, noch keinen neuen
nativen Bootstrap, keine tatsächlichen nativen Gamepad-/IMU-Ereignisse und
keinen Eingabe-/Motor-/Wiederverbindungstest. Nach dem Start ausschließlich
lesend geprüft; der Dienst bleibt pausiert laufen.

### Gestufte Freigaben am CachyOS test host

Stufen 1 und 2 sind inzwischen jeweils nach eigener Freigabe abgeschlossen;
die betreffenden Befehle sind Belege, keine Wiederholaufträge. Stufen 3–4 sind
**vorbereitet und nicht ausgeführt**. Sie gelten auf dem CachyOS test host.
Kein automatisches Fortsetzen von einer Stufe zur
nächsten, keine Aktivierung des Autostarts und keine Steam-/Gamescope-Installation.

1. **Paketupdate abgeschlossen**, nach gesonderter Freigabe einschließlich Passwortabfrage:

   ```sh
   sudo /usr/bin/pacman -U -- /home/example/gamesir-native-build/20261015T125906Z-bootstrap-revision3/gamesir-native-dkms-0.1.0.alpha3-3-x86_64.pkg.tar.zst
   ```

   Unmittelbar vorher Kernel/Header, Paket-Hash, aktuellen Gerätetoken,
   inaktiven/deaktivierten Dienst, fehlendes Modul, keine nativen Bindungen,
   Paketlock/Jobs/Neustartmarkierungen und die private Zustandsdatei nur lesend
   kontrollieren. Pause und leere Leases nachweisen; bei Abweichung anhalten.
   Vollständige Transaktion muss genau Revision 2 → 3 enthalten, ohne zusätzliche
   Pakete/Upgrades/Entfernungen. Zum Update gehören der sichere Rückgabe-/
   Stopp-Hook, DKMS-Entfernung/Neubau, depmod und vorhandene Snapper-/Limine-/
   mkinitcpio-Hooks einschließlich Änderungen von Bootdateien. Keine Datenbank-
   aktualisierung, Reparatur oder Dienstaktivierung. Danach echte DKMS-Baulogs,
   installierte Quellen/Nutzdateien, vermagic und neue srcversion gegen den
   Zielbau prüfen. Modulversion allein genügt nicht. Dienst muss weiterhin
   inaktiv/deaktiviert, Modul ungeladen und xpad-Zustand unverändert sein.
2. **Pausierter Dienststart abgeschlossen**, nach separater Einmalfreigabe:

   ```sh
   sudo /usr/bin/systemctl start gamesir-native.service
   ```

   Erlaubt das Laden von industrialio und des geprüften Moduls in
   bootstrap/output/persistent-Modus. Die vorher nachgewiesene gespeicherte
   Pause verhindert die Übernahme. Danach nur lesend Modul-/Dienstzustand,
   `paused=true`, leere Leases und dieselbe 100a/xpad-Instanz prüfen.
   Start ist kein `enable` und hebt die Pause nicht auf.
3. **Einmaliger Bootstrap-/Eingabelauf inzwischen separat freigegeben und
   verbraucht; Ergebnis im folgenden Abschnitt**:

   ```sh
   sudo /usr/bin/gamesir-native resume
   ```

   Vorher erneut genau einen passenden Dongle am ausgewählten Port, dessen
   aktuelle Instanz und exklusive Zugriffsmöglichkeit prüfen. Spiele/Deadband
   bleiben geschlossen; eine laufende Gamescope-Steam-Sitzung wird nicht
   neugestartet oder umkonfiguriert. Die Freigabe gilt für gezielte IF0-Übernahme,
   einmaligen 100a→109c-Bootstrap und native Eingabe-/IMU-Prüfung, keine
   Motorimpulse. Bei `waiting_input` nach Ansage A/Stick bewegen.

   Höchstens 90 s bis zum bestätigten nativen Zustand; keine Wiederholung.
   Danach 150 s mit menschlichen Puffern: 30 s zum Ablegen, 20 s Ruhe,
   10 s Reaktionspuffer, 60 s Tasten/Sticks/Trigger und Zusatztasten,
   10 s Rückkehrpuffer, 20 s Schlussruhe. Name `GameSir G7 Pro`, native Bindung,
   15 registrierte Codes, tatsächliche Eingaben und frische IMU getrennt
   nachweisen. Phasen ansagen, UTC/Monotonzeit und vollständige neue
   Bootstrapdiagnose/Kernelmeldungen privat sichern. Noch keine neue
   Gyro-Skalierung, Motor- oder Ingame-Paddle-Abnahme behaupten.
4. **Rückweg ausdrücklich festlegen**, bevor Stufe 3 beginnt: Genau ein
   `sudo /usr/bin/gamesir-native release` für den Fehlerfall benötigt eigene
   oder ausdrücklich eingeschlossene Freigabe. STOP/END nur auf nachgewiesen
   besessener Instanz; bei unbesessener 109c stoppen. Physisches Dongleentfernen,
   Wiedereinstecken, weitere Bindungs-/Modul-/Dienstaktionen separat freigeben.
   Erst tatsächliches 100a/xpad/usbhid plus normale Nutzereingaben bestätigt
   den Rückweg. Ein Hookabbruch kann bereits erfolgte Pause/Stopps erhalten;
   keine automatische Reparatur. Über dauerhafte Aktivierung erst nach dem
   erfolgreichen Test gesondert entscheiden.

## Revision-3-Realtest: Übergabe vor Neuanmeldung abgebrochen

Am 15. Oktober gab [tester] genau einen Resume-/Bootstraplauf und separat genau
einen Fehler-Release einschließlich Passwortabfrage frei. Spiele/Deadband
geschlossen, Gamescope-Steam unverändert, Autostart ausdrücklich aus. Nach
seinem STOP-Auftrag vorhandene Laufdateien lesend gesichert und anschließend
Belege und Code offline untersucht; kein weiterer Start, Modulladen,
Bindungswechsel, Reset oder Neustecken.

Die frische Vorprüfung bestätigte den unveränderten Kernel, installierte
Revision 3, passende DKMS-/Quell-/Modulhashes, neue geladene srcversion und
alle drei Opt-in-Parameter. Dienst active/running/disabled, NRestarts=0,
Pause/leere Leases und dieselbe 100a-Instanz an xpad/usbhid. [tester] installierte
evtest 1.36 selbst. Ein privater Helfer stoppte zunächst vor jedem Resume an
einer unnötig exakten Versionszeichenkette: `/usr/bin/evtest --version`
enthält den Programmpfad als Vorspann. Dies war ein Helferfehler, kein
Controllerbefund. Beide gültigen Vorspannformen und abweichende Versionen
wurden offline geprüft; Originalbelege erhalten. Die anschließend fortgesetzte
freigegebene Hardwareaktion enthielt genau einen Resume und einen Fehler-Release.

### Gesicherter Ablauf

Quellzeilen in diesem historischen Realtestabschnitt beziehen sich auf Commit
`19ff2ce` und den oben genannten unveränderten Kernelquellhash. Die nachfolgende
Offline-Korrektur verschiebt diese Zeilen und ist getrennt dokumentiert.

Auszug aus dem Kerneljournal; Zeiten MESZ. Das kleine
[bereinigte Belegprotokoll](evidence/CACHYOS_BOOTSTRAP_20261015.json) enthält
UTC-/Monotonzeiten und trennt Real- von künstlichen Befunden.

| Zeit | Nachweis |
| --- | --- |
| 16:06:42 | IF0 von xpad gezielt an gs_native unter 100a; natives Input-Gerät registriert; später 371 normale Padpakete vor Bootstrap gemeldet |
| 16:06:52,647826 | Bootstrap endet -19/ENODEV in `WAIT_REMOVE`; step=9, pending=0, transition=1, tx_count=9, tx_step=8, tx_status=0, tx_actual=8, tx_expected=8 |
| 16:06:52,739705 | USB-Core protokolliert Abmeldung der alten Adresse 11 |
| 16:06:53,941708 | Neue USB-Adresse 12 am selben Hub-Port |
| 16:06:54,197725 | Neue Identität 3537:109c erkannt |
| 16:06:54,271707 | Generic-X-Box-Input-Gerät; abschließend IF0 tatsächlich an xpad |

Der Core erreicht `WAIT_REMOVE` erst nach neun vollständig bestätigten
Acht-Byte-Übergangs-OUTs (`src/gs_startup.c`, `gs_boot_complete()`). Damit ist
die Übergangssequenz gesendet; ein aktueller USB-Paketmitschnitt wurde dabei
nicht erstellt. Kein Timeout: Status -19 und `timed_out=false`. Keine fertige
109c-Initialisierung, keine native Gamepad-/IMU-Abnahme und keine Motorimpulse.
Die geplanten 150 Sekunden mit menschlichen Puffern begannen nicht.

Der Bootstrap-Abschluss steht im Kerneljournal 91,879 ms vor dem
USB-Disconnect-Eintrag. Der Fehler-Release beginnt erst rund 326 ms nach dem
Bootstrap-Abbruch und verursacht diesen ersten Fehler daher nicht. Die
Eintragsreihenfolge beweist nicht den früheren elektrischen Linkzustand oder
den exakten internen USB-Core-Zustandswechsel. Kein Freeze-/Oops-/Lockupbefund
im gesicherten Fenster; die bekannte xpad-Abbaumeldung -2 ist getrennt vom
Bootstrapfehler und kein Nachweis seiner Ursache.

### Warum anschließend xpad erscheint

Die eine Ab-/Neuanmeldung ist Bestandteil des gewünschten 100a→109c-Wechsels.
Der Fehler liegt davor in unserer noch nicht abgeschlossenen Übergabe:

1. Der Bootstrap endet fehlgeschlagen und entfernt seine ausstehende Sitzung
   aus `boot_list` (`gsn_bootstrap()`, Kernelquelle Zeilen 1273–1300).
2. Eine 109c-Probe verlangt einen passenden `WAIT_ADD`-Eintrag ohne angehängtes
   Altgerät (`gsn_boot_pending()`, Zeilen 901–917; Probe 1783–1784). Dieser
   Besitznachweis fehlt nach dem Abbruch.
3. Die neue Instanz wird als normales USB-Gerät an xpad gebunden. Ein
   gezielter erfolgreicher Restore auf 109c wurde vom Manager nicht ausgeführt.
4. Der Manager behält den Fehler und die Lease. `return_one()` blockiert den
   neuen Token mit `Unowned new 109c instance; no END attempted`, statt ohne
   nachgewiesenen Besitz END oder eine Bindungsänderung zu senden
   (`tools/service/gamesir_native.py`, Zeilen 653–655).

Das erklärt die beobachtete Fallback-Anzeige. Es beweist keinen erfolgreichen
Wechsel zurück nach 100a und keinen wiederholten Hardware-Disconnectloop:
In diesem Lauf ist genau eine USB-Abmeldung mit folgender Neuanmeldung belegt.

### Reproduzierte Diagnoselücke und verbleibende Ursache

Ein privater Test verwendet unverändert extrahierte echte Adapterfunktionen
und den vorhandenen Fake-USB-Testunterbau unter ASan/UBSan. Nach OUT9 wird
künstlich entweder eine RX-Completion oder RX-Neueinreichung mit -EPIPE (-32)
beziehungsweise -EPROTO (-71) vorgegeben. Alle vier Fälle reproduzieren exakt
die reale Bootstrap-Abschlusszeile mit -19, WAIT_REMOVE und neun vollen OUTs,
bevor der künstliche Disconnect aufgerufen wurde:

- `gsn_boot_rx_teardown()` lässt in diesem Fenster nur ENOENT, ECONNRESET,
  ESHUTDOWN und ENODEV als begrenzten alten Empfangsabbau zu (Zeilen 953–980).
- Andere RX-Fehler laufen über `gsn_fault()` und setzen Runtime/Originalfehler
  auf FAULTED (Zeilen 166–176, 433–435, 478–480).
- `gsn_boot_service()` ersetzt eine nicht mehr laufende Runtime anschließend
  pauschal durch ENODEV, bevor es das WAIT_REMOVE-Fenster prüft
  (Zeilen 1056–1062). Damit geht der ursprüngliche Empfangsfehler in der
  Abschlussdiagnose verloren.
- Zwei ENODEV-Kontrollfälle, ebenfalls Completion/Neueinreichung, bestehen
  dagegen den vollen künstlichen 15-Transfer-Start. Keine Sanitizerfehler.

**Bewiesen:** Der passende Softwarepfad einschließlich der Fehlerüberschreibung
ist reproduziert; die bisherige Korrektur deckt diese Statuswerte nicht ab.
**Offen:** Der tatsächlich erste RX-/Runtime-Status des realen Versuchs wurde
nicht protokolliert. EPIPE/EPROTO sind künstlich eingesetzte Gegenbeispiele,
keine nachträglich gemessenen Hardwarewerte. Auch ein anderer früherer
Runtimefehler darf nicht ausgeschlossen werden. Kein Defekt des Controllers,
Hubfehler, Timeout oder Stromsparfehler als Ursache behaupten.

Ein zusätzlicher Managerbefund ist `invalid literal for int() with base 10: ''`
in der USB-Lücke: `Host.value()` erhielt beim Lesen eines dezimalen
sysfs-Metadatenfelds einen leeren String. Der Attributpfad fehlt; welches der
Felder `bConfigurationValue`, `bAlternateSetting`, `busnum` oder `devnum` es war,
ist offen. `Host.scan()` isoliert den ValueError als Portfehler. Er kann den
sichtbaren Fehlertext vorübergehend überlagern; die separate Bootstrapdiagnose
und Lease bleiben erhalten. Dieser Folgefehler erklärt nicht den früheren
Kernelabbruch. Der Manager stürzte nicht ab, NRestarts bleibt 0.

### Abschlusszustand, Belege und nächster Schritt

Der genau einmal freigegebene Fehler-Release endet mit Exit 1:
`paused=true`, `returned=false`, Phase blocked, neue 109c/Adresse 12 an xpad.
Keine native Bindung, gs_native geladen mit Referenzen 0; Dienst bleibt
active/running/disabled. END und Cleanup auf der neuen unbesessenen Instanz
wurden nicht versucht. **Rückkehr zu 100a und normale Funktion nicht bestätigt.**
Keine Reparatur, Deinstallation, Modulaktion oder physische Rückkehr nach dem
STOP-Auftrag. Ein manueller Rückweg benötigt eine gesonderte Freigabe; eine
weitere unbekannte 109c wird nicht einfach übernommen.

Private Originale, ausführbare Helfer, Zeitmarken, Journale und Managerzustände:
`.local/integration/20261015T135014Z-CachyOS test host-bootstrap-revision3/`, dort
`version-format-correction/records/` für den tatsächlichen Lauf und
`private-rx-cause-repro/` für die sechs gerätefreien Fälle. SHA256-Listen
sichern Originale und Reproduktion; Serien-/Boot-/Besitztokens und vollständige
Journale bleiben außerhalb von Git. Der gemeinsame Produktcode wurde in dieser
Untersuchung nicht geändert. Kein Paket gebaut/installiert, kein Push.

**No-Go für einen weiteren Hardwareversuch oder Autostart.** Zuerst muss eine
gezielte Offline-Korrektur den frühesten Transportstatus/Ort erhalten und das
erwartete Abbau-/Übergabefenster samt echten Fehlern getrennt prüfen. Eine
pauschale Freigabe aller RX-Fehler oder Übernahme nur aufgrund von PID109c wäre
keine belastbare Korrektur. Der erste reale Transportstatus bleibt bis zu einer
später separat freigegebenen aussagekräftigen Messung offen.

## Offline-Folgekorrektur: erste Ursache und echte Übergabe erhalten

[tester] hat nach der Untersuchung ausdrücklich die Offline-Korrektur mit Tests
beauftragt. Der folgende Quellstand wurde nicht installiert oder geladen;
kein neuer Hardwareversuch und keine SSH-/USB-/Systemaktion für diese Prüfung.
Die nachträglich beauftragte Paketierung/Übertragung wird separat dokumentiert.

### Fehlerbehandlung

`gsn_fault()` übernimmt den ersten fatalen Runtime-/Transportfehler jetzt
unmittelbar am Auslöser in den Bootstrap-Core. Die Lockfolge entspricht dem
bestehenden Adoptpfad: Runtime vor Bootstrap. Ein noch laufender letzter OUT,
ein Disconnect oder ein Worker darf diesen Fehler nicht nachträglich zum
erfolgreichen Handoff machen. Der Core erhält seine bereits vorhandene
First-Failure-Semantik; keine UAPI-Änderung.

Der Worker und der Adoptpfad übernehmen `rt.error` statt pauschalem ENODEV,
sofern ein negativer Originalstatus vorhanden ist. Am Ende des Supervisors
wird dessen Rückgabewert mit dem bereits festgehaltenen Corefehler abgeglichen.
Damit kann auch ein gleichzeitig eintreffendes Signal den früheren RX-Fehler
nicht im Rückgabewert, Journal oder Cleanup durch EINTR ersetzen.

Die bestehende Abschlusszeile erhält zusätzliche reine Diagnosefelder:

| Feld | Bedeutung |
| --- | --- |
| `first_rx_status` | Erster nicht lokal erzeugter negativer RX-Befund; 0 ohne solchen Befund |
| `first_rx_source` | 1 = Completion, 2 = erneutes Einreichen; 0 ohne Befund |
| `first_rx_stage`, `first_rx_step`, `first_rx_pid` | Zustand, Schritt und Geräteidentität direkt am RX-Auslöser |
| `first_rx_us` | Monotone Kernelzeit in Mikrosekunden am Auslöser |
| `first_rx_deferred` | Dieser RX-Befund wurde nur im nachgewiesenen alten Übergabefenster zurückgestellt |
| `old_rx_quiesced` | Alter Empfang nach neun vollständigen OUTs logisch stillgelegt |

Diese erste RX-Beobachtung ist unveränderlich. Ein späterer Timeout oder
fehlgeschlagener OUT bleibt als separater terminaler Corestatus beziehungsweise
letzte TX-Completion sichtbar. Eine zurückgestellte RX-Beobachtung ist nicht
zwangsläufig ein fehlgeschlagener Bootstrap; ihr tatsächlicher Status bleibt
auch bei anschließend erfolgreicher Übergabe dokumentiert. Selbst erzeugtes
ENOENT/ECONNRESET und ein lokales EPERM beim Einreichen während der Stilllegung
werden nicht als ursprünglicher Transportfehler ausgegeben.

### Begrenzter Übergabepfad

Nach genau neun vollständig bestätigten Übergangs-OUTs wird ausschließlich der
Empfang der exakt zugeordneten alten 100a-Instanz logisch beendet und deren
eigener URB einmal gezielt abgebrochen. Das geschieht außerhalb der Spinlocks;
auch ein erfolgreicher alter Callback reicht nichts mehr erneut ein. Bereits
früher erkannte fatale RX-Fehler bleiben fatal und verhindern diese Fortsetzung.

Für das kleine Rennen zwischen OUT9-Completion und Stilllegung dürfen EPIPE
und EPROTO ausschließlich in WAIT_REMOVE nach neun Voll-Completions als
dokumentierte Beobachtung des alten Empfangs zurückgestellt werden. Während
eines noch ausstehenden OUT9 bleiben diese beiden Fehler fatal. Die bisherigen
vier eng begrenzten Abbaustatus während OUT9 bleiben erhalten; sie bestätigen
niemals dessen Erfolg. Ein kurzer/fehlgeschlagener OUT verhindert den Handoff.

Stilllegung und RX-Status bestätigen keine Geräteabmeldung. Der echte
Disconnectcallback, die ursprüngliche unverlängerte Frist, dieselbe
Parent-/Root-Lebensdauer, Port-/Instanztokens, neue Geräteinstanz und exklusive
Besitzprüfung bleiben erforderlich. Fehlt die Abmeldung, endet der Versuch
weiter mit ETIMEDOUT; ein früher zurückgestellter RX-Status bleibt daneben
sichtbar. Keine Übernahme einer fremden 109c, kein Reset oder Wiederholungsloop.
Der 105e-Direktstart und die normale native Runtime werden nicht stillgelegt.

### Manager und Regressionen

Leere oder ungültige sysfs-Zahlen melden jetzt den genauen Attributpfad und
die Zahlenbasis. Der Manager hält temporäre Scanfehler in `port_errors`, ohne
den ursprünglichen Protokoll-/Runtimefehler zu überschreiben. Unbekannte
Anwesenheit, Quarantäne, Absenzfrist, Lease und strenge Besitzprüfung bleiben
erhalten; ein Metadatenfehler wird nicht zum Beleg für Geräteabwesenheit.

Bestandene Prüfungen des endgültigen Quellstands:

- `make test`: vollständige vorhandene Offline-Suite bestanden. Darunter
  246 tatsächliche extrahierte Adapterfälle mit ASan/UBSan und 139 Managerfälle.
- Die neuen Fälle prüfen RX-Completion und Einreichen vor OUT9, während OUT9,
  nach voller Completion und bei READY; kurze/fehlgeschlagene TXs erhalten
  ihre eigene Diagnose. Fehlender Disconnect, echter späterer Callback,
  unveränderte Fristen, falsche Topologie/Instanz/Besitzer, PM, Cancel und
  manuelles Unbind bleiben getrennt geprüft.
- Erfolgreiche alte RX-Callbacks, lokales Cancel und der EPERM-Submit-Race
  erzeugen weder erneutes Einreichen noch einen falschen Transportfehler.
  Parallel eintreffendes Signal bewahrt den vorherigen Originalfehler.
- Private Negativkontrolle entfernt ausschließlich die abschließende
  Supervisor-Normalisierung aus der Extraktion: Die neue Signalregression
  schlägt dann gezielt fehl. Produktquelle dabei unverändert.
- 32 bestehende tatsächliche Motor-Sendefälle und 22 FF-Lebensdauerfälle mit
  vier erwarteten ASan-Negativkontrollen bleiben grün. Die isolierte Motor-
  Fixture hält Bootstrap absichtlich NULL; unerwarteter Zugriff auf deren
  Bootstrap-Stubs schlägt per Assertion fehl. Echte Bootstrapfunktionen sind
  im separaten Adaptertest abgedeckt.
- `make kernel-analyze`: Build gegen die lokal vorhandenen Garuda-Header
  `7.2.10-1-garuda` mit Clang 23.1.1, W=1/-Werror, keine Compilerwarnung.
  Checkpatch ohne Quellwarnung, fünf Clang-Analyseeinheiten ohne Befund.
  Srcversion `499FB2049A64E55F54B712C`, Modul-SHA256
  `2632ace62a10c990f1a64f07cbe941e5b6fd44308eec1a97238c135662a7deb0`.

Logs: `build/bootstrap-rx-full-tests.log`,
`build/bootstrap-rx-kernel-analysis.log`, `build/results/kernel-startup-*`,
`build/results/kernel-build.json`, `build/results/kernel-static-analysis.json`.
Private Negativkontrolle im ursprünglichen Laufordner unter
`private-supervisor-regression/`. Die erste breite Suite deckte eine fehlende
Bootstrap-Abhängigkeit der isolierten Motor-Fixture auf; deren Shim wurde
begrenzt ergänzt, die vollständige Suite anschließend erfolgreich wiederholt.

**Entscheidung:** Softwarepfade und Fehlererhaltung sind offline korrigiert und
gebaut. Paketvorlage für den folgenden Bau: `0.1.0.alpha3-4`; Versionswechsel
verhindert eine Verwechslung mit dem installierten alten Quellstand. Der reale
erste RX-Status des Revision-3-Laufs bleibt unbekannt. Keine neue CachyOS-
Hardwareheilung oder allgemeine Racefreiheit behaupten; ein neuer GCC-Bau mit
den passenden CachyOS-Headern und die echte Abnahme bleiben getrennte Schritte.
Die zuletzt bestätigte CachyOS test host-Verwaltungspause und der ungeklärte Rückweg
werden von dieser Offline-Arbeit nicht verändert.

## CachyOS test host: Revision 4 installiert, noch nicht aktiviert

[tester] gab nach dem Offline-Fix Paketbau und Installation ausdrücklich nur am
CachyOS test host frei; Garuda test host erst nach dortiger positiver Abnahme. Aus Commit
`08bc857aaeb060a8222ed84be3b1669959db9568` wurde unprivilegiert das Arch-/DKMS-
Paket gebaut, geprüft und per SSH übertragen. Kein Upload/Push.

- Paket: `gamesir-native-dkms-0.1.0.alpha3-4-x86_64.pkg.tar.zst`, SHA256
  `af3d6f8016e9e1e3e8515270411f52a61af3b7eb246cffeb3d8f1a08d4cdcbec`.
- Quellarchiv: SHA256
  `085cdc7043b7cd8e64d3388a429463893621cad4b90ed4c383d851273059665b`;
  75 Quelldateien mit dem Commit verglichen, 72 Paketnutzdateien byte-/rechte-
  und eigentümergeprüft. Kein Install-Scriptlet, eingebettetes Modul,
  Fremdinstaller oder Rohmitschnitt. Der bereinigte eigene Realtestbeleg wird
  mitgeliefert, damit dessen Dokumentationsverweis im Paket funktioniert.
- Lokale Artefakte: `build/alpha3-bootstrap-rx-fix-revision4/`, auf dem Ziel
  `/home/example/gamesir-native-build/20261015-revision4-bootstrap-rx-fix/`.

### Erster Installationsversuch durch Upgrade-Schutz abgebrochen

Frische privilegierte Vorprüfung: Revision 3, Kernel/Header unverändert,
100a/Adresse 14 an xpad/usbhid, Pause aktiv, returned=true, Leases leer,
Modul ungebunden/Referenzen0, Dienst active/running/disabled. Die vollständige
interaktive Transaktion enthielt genau ein Update 3→4 ohne weitere Pakete.
Bekannte Dienst-/Modul-/DKMS-/Snapshot-/Initramfs-/Limine-Hooks waren vorher
benannt. Garuda test host wurde nicht angefasst.

Während der Vorbereitung meldete sich das Gerät am 15. Oktober um 16:42 MESZ
von Adresse14 ab und als 109c/Adresse15 erneut an. [tester] meldete dazu, dass
der Funkcontroller durch Inaktivität ausgeschaltet war. Keine neue Bootstrap-
oder direkte USB-Modusaktion durch Codex; welche sonstigen USB-Anfragen oder
Firmwarebedingungen die Neuanmeldung auslösten, wurde nicht aufgezeichnet.
Der alte Manager hatte keine Lease mehr, aber noch einen released-Eintrag für
den verwalteten Port mit Ursprung100a. `returned=false` blockierte deshalb den
Upgrade-Release. Das ist kein neu gescheiterter Lauf des korrigierten Treibers:
Revision4 war noch nicht installiert oder geladen.

Pacman brach **vor der Paketänderung** ab, Exit1. Revision3 blieb mit 91
Paketdateieinträgen/0 verändert erhalten; Dienst/Modul weiter geladen wie zuvor,
Pause aktiv, keine native Bindung/Modulreferenzen, Leases leer. Die erwarteten
Vor-Hooks hatten bereits Snapshot85 und die dazugehörige Limine-Synchronisierung
erzeugt; kein DKMS-Neubau oder Initramfsbau dieses Versuchs. Originale erhalten,
keine automatische Wiederholung und kein Umgehen des Upgrade-Schutzes.

### Kontrolliertes Update bei abgezogenem Dongle bestanden

[tester] kündigte das physische Abziehen an. Die lesende Kontrolle bestätigte
keinen GameSir-Dongle und keine native Bindung. Nach abgeschlossener
Absenzbereinigung verlangte der vorbereitete getrennte Anlauf zusätzlich
einen leeren Managerstatus, Pause/returned=true und leere Leases. Der Dongle
blieb während der gesamten Installation draußen; keine Geräteöffnung oder
Modus-/Bindungsaktion zum Herstellen einer passenden Identität.

Nach erneuter Passwortabfrage erneut genau ein Paket 3→4 geprüft und bestätigt.
Der vorhandene Pre-Transaction-Hook bestätigte den Rückweg, stoppte den Dienst
und entlud nur das ungebundene native Modul; xpad und industrialio wurden nicht
global entladen. Paketupdate, tatsächlicher GCC-/DKMS-Bau, Initramfserzeugung,
Limine-Aktualisierung und Snapper86/87 erfolgreich, Pacman Exit0.

Abschlussprüfung:

- Installiert `gamesir-native-dkms 0.1.0.alpha3-4`, ausschließlich dieses Paket
  geändert. 93 Paketdateieinträge, 0 verändert; 72 Nutzdateien im Vergleich
  zum geprüften Archiv ohne Byte-/Rechte-/Eigentümerabweichung.
- DKMS für `7.2.9-2-cachyos-deckify` installed. Tatsächliche GCC-Baulogs ohne
  Compilerwarnungen/-fehler, passende vermagic und keine Autoload-Aliase.
  Neue srcversion **499FB2049A64E55F54B712C**, Kernelquelle passend zum Fix.
  Der bekannte separate DKMS-CLEAN-Deprecation-Hinweis blieb unverändert.
- Dienst **inactive/dead/disabled**, Result=success, MainPID0; neues Modul
  **nicht geladen**, keine native Bindung, physisch kein GameSir-Gerät.
  Pause/Leases und gesamter gespeicherter Managerzustand unverändert erhalten.
- Header und Steam-Sitzung unverändert. Kerneljournal ausschließlich
  Deregistrierung des alten gs_native, kein Oops-/Lockup-/WARN-Befund.
  Keine Aktivierung, Resume, neue Hardwareabnahme, unbeaufsichtigter Neustart
  oder Garuda test host-Systemänderung.

Die ursprüngliche -19-Diagnose bleibt historisch; der tatsächliche erste
RX-Status dieses alten Laufs ist weiterhin unbekannt. Die erfolgreiche
Installation ist kein Bootstrap-Hardwarebeleg. [tester] hat anschließend Start
und Test gewünscht; konkrete nächste Freigabeschritte getrennt durchführen.

Private Prüfungen/Transaktionen, erstes Abbruchfenster und erfolgreicher
abgezogener Anlauf mit SHA256-Ketten:
`.local/integration/20261015-revision4-CachyOS test host-delivery/`, insbesondere
`disconnected-attempt/installed-records/after.json`. Der Paketquellstand ist
Commit08bc857; spätere lokale Commits ergänzen nur den Installationsbericht.

### Frische Vorprüfung für den nächsten pausierten Start

[tester] bestätigt: Dongle weiterhin abgezogen, Funkcontroller aus. Die lesende
SSH-Prüfung am 15. Oktober um 14:56:51 UTC bestätigt erneut Revision 4,
passende Kernel-/Headerdaten, DKMS installed und srcversion
`499FB2049A64E55F54B712C`. Komprimierte installierte Moduldatei: SHA256
`91f38cd5f044701327b78fcfd911f0a33186757372b37dfaa6d53d642dec4aff`.
Dienst inactive/dead/disabled, MainPID 0, keine Jobs/Neustartmarkierungen,
kein geladenes gs_native, keine native Bindung und kein GameSir-Gerät.
Die laufende Gamescope-/Steam-Sitzung wurde nur lesend erfasst.

Der vorhandene pausierte Starthelfer ist lokal für diese Revision und die
Geräteabwesenheit angepasst und syntaxgeprüft. Ein unabhängiger Offline-Review
bestätigt: Die Unit lädt industrialio/gs_native und startet den Manager;
gespeicherte Pause und leere Leases sperren die Übernahme. Kein Dongle bedeutet
außerdem keinen USB-Probe. Vor der einzigen Aktion werden Pause, Besitz,
Boot-ID, Paket, Modulhash, Quellen und Dienstzustand erneut geprüft.

Nächste einzeln freizugebende Zustandsänderung am CachyOS test host:
`sudo /usr/bin/systemctl start gamesir-native.service`. Kein Enable oder
Resume. Danach Modul/Parameter, weiter deaktivierten Autostart, fünf pausierte
Managerstatusproben, Geräteabwesenheit und Kerneljournal prüfen. Bei Abweichung
anhalten und dokumentieren; kein automatisches Stoppen/Entladen/Reparieren.
Erst danach Dongle-Wiederanschluss und den konkreten Bootstraplauf getrennt
vorbereiten/freigeben. Der Dienststart wurde bisher **nicht ausgeführt**.
Private Vorbereitung: `.local/integration/20261015-revision4-paused-start/`.

### Revision 4: Pausierter Dienststart bestanden

[tester] gab genau den pausierten Einmalstart einschließlich grafischer
Passwortabfrage und lesender Vor-/Nachkontrolle frei, weiterhin kein Resume,
Bootstrap oder Enable. Die frische unprivilegierte Vorprüfung fand unverändert
keinen GameSir-Dongle, keinen geladenen nativen Treiber und den inaktiven/
deaktivierten Dienst. Der angepasste bestehende Helfer wurde vor Verwendung
unabhängig offline geprüft und nach SSH-Übertragung per SHA256 verglichen.

Am 15. Oktober 2026 um 17:00:45 MESZ wurde nach bestätigter privater Pause,
leeren Leases und exakten Paket-/Boot-/Modul-/Quellnachweisen genau einmal
`systemctl start gamesir-native.service` ausgeführt, Exit 0. Nachkontrolle:

- Dienst active/running, **Autostart weiterhin disabled**, MainPID 28673,
  NRestarts 0, keine Jobs/Drop-ins/Neustartmarkierungen.
- Richtige neue srcversion `499FB2049A64E55F54B712C`; industrialio und
  gs_native geladen, native Referenzen 0, bootstrap/output/persistent Y.
- Fünf Statusproben pausiert, keine verwalteten Geräte oder Scan-/Portfehler.
  Gesamter gespeicherter Zustand unverändert, insbesondere keine neuen
  Startversuche, Leases oder Fehlerhistorieneinträge. Die vorhandene kurze
  Absenzbestätigung wechselte `returned` nach zwei Proben auf true.
- Kein GameSir-Gerät und keine native Bindung im Startfenster. Steam-Prozess
  und Startzeit unverändert; Journal ausschließlich erfolgreiche
  Dienststartmeldungen und Registrierung des nativen USB-Treibers.
  Kein neuer Oops-/WARN-/Lockup-Befund, kein Bootstrap oder Motorbefehl.

Root-Records und unveränderter ausgeführter Helfer lokal gesichert; alle zehn
privaten SHA256-Einträge und ein unabhängiger lesender Ergebnisreview bestanden.
Private Belege: `.local/integration/20261015-revision4-paused-start/`, darunter
`records/{before,action,after}.json`, `verification.json` und `SHA256SUMS`.
Die Einmalfreigabe ist verbraucht. Dienst bewusst pausiert laufen lassen;
kein Stop/Unload/Enable/Resume als automatische Folgeaktion.

Auf anschließende Ansage steckte [tester] den Dongle wieder ein und bestätigte
den verbundenen Funkcontroller. Die rein lesende Prüfung um 17:03:38 MESZ
ergab 3537:100a, Bus 1/Adresse 18, Port 1-3.2, USB-Inode 57867,
IF0/xpad und IF1/usbhid. Dienst unverändert active/running/disabled,
native Referenzen 0 und keine native Bindung. Dieser Ausgangszustand ist
kein nativer Eingabetest. Nächster Schritt ist die konkrete Freigabe eines
neuen einmaligen Resume-/Bootstraplaufs samt begrenztem Fehler-Rückweg.

### Revision 4: Testhelferabbruch während der USB-Neuanmeldung

[tester] gab genau einen Lauf einschließlich Passwortabfrage, Resume, lesender
Eingabe-/IIO-Beobachtung und höchstens einem Fehler-Release frei. Autostart
blieb aus. Vor dem Start erneut exakte 100a/Adresse 18, USB-Inode 57867,
xpad/usbhid, Kernel/Header, Revision 4, neuer Modulhash/srcversion und
pausierter/leerer Besitzstand geprüft. Der vorhandene Runner wurde mit
aktualisierten Instanzmerkmalen verwendet; Observer unverändert.

Um 17:08:01 MESZ erfolgte genau ein Resume. Der Treiber wartete auf Eingaben;
[tester] erhielt die Ansage für A/Sticks. Noch während des Bootstraps lieferte
der Manager kurzzeitig `port_errors` für ein leeres
`/sys/bus/usb/devices/1-3.2/bConfigurationValue` (Basis 10). Gleichzeitig:
phase=bootstrapping, busy=true, error leer, present unbekannt. Der Manager
behandelt dies als Beobachtungsquarantäne; der Testhelfer wertet dagegen jedes
`port_errors` sofort fatal und startete den freigegebenen Fehler-Release.
Diese Helferprüfung war für die erwartete Neuanmeldung zu streng.

Die Zeitfolge ist anhand der ursprünglichen Kernelzeit
`_SOURCE_MONOTONIC_TIMESTAMP` und der Runner-Cues rekonstruiert. Journalds
`__MONOTONIC_TIMESTAMP` ist die spätere Empfangszeit und wurde nicht mit der
Kernelquelle verwechselt. Bezugspunkt ist die **Release-Ansage**, nicht eine
separat gemessene Signalzustellung:

| Ereignis | Relativ zur Release-Ansage |
|---|---:|
| Tatsächlicher USB-Disconnect Adresse 18 | −251,225 ms |
| Helferabbruch wegen leerem Konfigurationsfeld | −0,079 ms |
| Ansage des einmaligen Fehler-Release | 0 ms |
| Kernel meldet Bootstrapende mit −4/EINTR | +6,928 ms |
| Neue USB-Adresse 19 | +971,128 ms |
| Neue Identität 3537:109c | +1227,082 ms |

Neue Kerneldiagnose: failed_stage=3/WAIT_ADD, step=9, transition=1,
tx_count=9, letzter OUT status=0/actual=8/expected=8,
old_rx_quiesced=1. first_rx_status/source=0: kein erster RX-Fehler in dieser
Diagnose aufgezeichnet. Die neun Übergangs-OUTs sind durchlaufen, bevor der
Testhelfer den noch laufenden Start abbrach. Der Managercode beendet beim
Release den Bootstrapclient; `signal_pending` ergibt im Kernel EINTR. Zeitfolge,
Code und Status passen dazu. Ein separates Signal-Audit fehlt; der nach dem
Release protokollierte EINTR wird nicht zum ursprünglichen Hardwarefehler
erklärt. Das historische −19 gehört weiterhin zum alten Lauf/Adresse 11.

Kein erfolgreicher nativer 109c-Handoff, keine aktive Observerinstanz und keine
150-Sekunden-Eingabe-/IMU-Phase. Keine Motorimpulse. Die bekannte xpad-ENOENT-
Abbaumeldung ist erhalten; im Journal kein neuer Oops-/WARN-/Lockup-Befund.
Die Belege zeigen weder eine neue fatale RX-Ursache noch eine bestandene
CachyOS-Bootstrapabnahme. Ohne den Helferabbruch wäre der weitere Verlauf
dieses konkreten Versuchs nicht mehr beobachtbar.

Abschluss um 17:09:10 MESZ:

- Dongle 3537:109c, Adresse 19 am selben Hub-Port, IF0 an xpad.
- Keine native Bindung; geladenes Modul ungebunden, Referenzzähler 0.
- Dienst active/running/disabled, PID/NRestarts unverändert.
- Manager paused=true, blocked, **returned=false**; alte 100a-Lease mit
  leeren Kernel-Tokens erhalten. Neue 109c nicht nachträglich übernommen,
  kein END an eine nicht besessene Instanz geschickt.
- Einmaliger Release Exit 1: Pause erreicht, Rückgabe nicht bestätigt.
  **109c/xpad ist kein bestätigter Wechsel zu 100a oder Funktionsnachweis.**

Alle Originalrecords und der exakt ausgeführte Helfer sind privat lokal
gesichert, Remote-/Lokaldigests verglichen und die SHA256-Kette geprüft:
`.local/integration/20261015-revision4-bootstrap-test/`, insbesondere
`records/observations.jsonl`, `records/kernel-observed.jsonl`,
`records/{before,resume,release,after}.json` und `analysis.json`.
Unabhängiger lesender Review bestätigt Chronologie und Beweisgrenzen.
Garuda test host-System unverändert, kein Push, keine automatische Wiederholung.

Nächster sicherer Schritt ist ein **separat freizugebender manueller Rückweg**:
nur den GameSir-Dongle abziehen und zunächst draußen lassen; anschließend
Geräteabwesenheit, Pause und bereinigten Besitzstand lesend bestätigen.
Erst nach diesem Nachweis wieder einstecken und 100a/xpad/usbhid sowie normale
Eingaben prüfen. Kein neuer Reset-/Modusbefehl, kein zweiter Release, keine
unbesessene 109c übernehmen. Die Helfer-Quarantänebehandlung danach gezielt
offline korrigieren/testen, ohne echte Fehler, Fristen oder Besitzprüfungen
zu lockern; ein neuer Hardwarelauf benötigt eine neue Einmalfreigabe.

### Revision 4: Abwesenheitsprüfung nach manuellem Abziehen bestanden

[tester] bestätigte den abgezogenen Dongle und gab ausschließlich die beiden
Leseabfragen `gamesir-native status` und `cat /var/lib/gamesir-native/state.json`
einschließlich grafischer Passwortabfrage frei. Frische unprivilegierte
Sysfs-/Dienstprüfung: kein GameSir-Gerät, keine native Bindung, neues Modul
geladen/ungebunden/Referenzen 0, Dienst active/running/disabled ohne Neustart.
Der kleine Lesehelfer führt genau diese beiden privilegierten Befehle aus;
unabhängiger Offline-Review vor Verwendung und Transferhash bestanden.

Leseschritt am 15. Oktober um 17:16:15 MESZ, beide Befehle Exit 0:

- Vor und nach den Abfragen kein angeschlossenes GameSir-Gerät.
- Status paused=true, **returned=true**, devices leer, scan_error leer,
  port_errors leer. Gespeicherter Zustand paused=true und Leases leer.
- Keine native Bindung, Referenzzähler 0. Keine neue USB-/Treiber-/Dienst-
  oder Modulaktion; der Manager bereinigte nach bestätigter Abwesenheit.
- Historische Fehler werden nicht als neuer Fehler ausgegeben. Die alten
  Originalrecords bleiben unverändert erhalten.

Root-Original und exakt ausgeführter Helfer privat lokal gesichert, Remote- und
Lokaldigests verglichen. Private Belege und SHA256-Liste:
`.local/integration/20261015-revision4-return-absence/`, insbesondere
`records/read-result.json` und `verification.json`.

Dies bestätigt **Abwesenheit und bereinigten Besitz**, noch keine neue normale
100a/xpad-Funktion. Der Dongle bleibt zunächst draußen. Kein Resume oder
Bootstrap, keine Wiederholung und kein automatisches erneutes Einstecken
aus dieser Lesefreigabe ableiten. Der Helferabbruch des vorherigen Laufs und
die noch offene native Eingabe-/IMU-Abnahme bleiben bestehen.

### Offline-Korrektur des Beobachtungshelfers und vorbereiteter neuer Lauf

[tester] beauftragte nach bestätigter Abwesenheit ausdrücklich nur die
Offline-Korrektur und Tests. Der Dongle bleibt draußen; keine SSH-Abfrage,
Hardwareaktion oder Systemänderung in diesem Arbeitsschritt.

Die Beobachtungslogik des bestehenden Runners ist als reine Policy v1 mit
tatsächlicher Warteschleife nach `tools/native/bootstrap_observation.py`
übernommen. Sie führt selbst keine Befehle aus. Die neue Runnerkopie ruft
dieselbe getestete Schleife auf; Modul, Manager, UAPI und Pakete bleiben
unverändert. Eine Treiberinstallation oder ein neuer Kernelbau ist dafür
nicht erforderlich.

Begrenzte Korrektur:

- Nur am explizit gewählten Port und während bootstrapping, locating oder
  attesting gelten exakt passende leere Root-Felder als Beobachtungsquarantäne:
  idVendor/idProduct mit Basis 16, bConfigurationValue/busnum/devnum mit Basis 10.
  Zusätzlich die exakte Managerphrase `USB metadata changed during enumeration`.
- Andere Felder, falscher Pfad/Port/Basis, ungültige Zahlen, Rechtefehler,
  globale Scanfehler, neue Bootstrap-/Gerätefehler und fremde Geräte bleiben
  fatal. Vor waiting_input und nach Beginn der aktiven Beobachtung gibt es
  keine Übergangsausnahme. Alte recent_failures werden nicht zu neuen Fehlern.
- Quarantäne löst keinen Release aus, setzt keine Bereitschaft und liefert
  keinen Besitznachweis. Kerneljournal und dieselbe 90-Sekunden-Frist werden
  weiter geprüft; die Frist wird niemals neu gestartet oder verlängert.
- Sauberer gecachter active-Status mit anschließendem frischem Scanfehler
  führt erneut durch die vollständige Validierung. Neue 109c/gs_native-Instanz,
  gleicher Parent, geänderter Instanztoken, aktive eigene Lease und Kernel-
  Tokens bleiben Pflicht. Erst danach darf der Eingabeobserver starten.
- Die Frist gilt vor aktiver Annahme und nach potenziell blockierenden Status-,
  Inventur-, Journal-, Lease- und Ausgabeschritten; zusätzlich prüft der Runner
  sie unmittelbar vor und nach dem Observeraufbau.

Bestandene Offline-Prüfungen:

- 31 neue Regressionen, darunter acht Fälle der tatsächlichen Warteschleife
  mit virtueller Zeit. Temporär leer → vollständig validiert; dauerhaft leer
  → unveränderte Deadline; echter Fehler trotz Lücke → Abbruch. Eine erst nach
  90 Sekunden eintreffende aktive Meldung ist kein Erfolg. Auch verzögertes
  Logging über die Frist hinaus verhindert den Erfolg.
- `make test-hardware-helper` bestanden: 29 Test-002-, zwei Test-003-, 31 neue
  Beobachtungs- und 34 Recorderfälle sowie 15 C-Client-Fälle mit ersetzten
  Systemaufrufen unter ASan/UBSan. Kein dumpcap, sudo oder Gerät gestartet.
- Alle 139 Manager-Regressionen bestanden; keine Produktmanageränderung.
- Gespeicherten echten Abbruchstatus aus dem vorigen Lauf offline gelesen:
  alter bad_status-Pfad bricht ab, neue Policy klassifiziert dieselbe Meldung
  korrekt als Quarantäne bei noch laufendem Bootstrap. Die weitergehende
  erfolgreiche Übergabe wird nur synthetisch geprüft.
- Neue Runner-/Observer-/Wrapperkopie syntaxgeprüft, geteilte Policy
  bytegleich zur getesteten Datei. Observer und Originalrecords unverändert.
  Fehlendes frisches Instanzmanifest verhindert bereits Passwortabfrage und
  SSH-Start; mit ersetzten Subprozessfunktionen sind null Aufrufe nachgewiesen.
  Unabhängiger Review bestätigt die Anbindung und unveränderten Besitzprüfungen.

Logs: `build/metadata-gap-helper-tests.log`,
`build/metadata-gap-manager-regressions.log`. Neue private Vorbereitung:
`.local/integration/20261015-revision4-bootstrap-metadata-gap-fix/`, inklusive
`offline-verification.json`, `NEXT_RUN_PLAN.json` und SHA256-Liste. Die alten
Test- und Rückwegaufnahmen wurden per vorhandenen Prüfsummen erneut unverändert
bestätigt. Kein Push und kein Update des Garuda test host-Systems.

**Vorbereiteter nächster Freigabeplan, noch nicht ausgeführt:**

1. Nach gesonderter Ansage den Dongle wieder einstecken und Funkcontroller
   verbinden. Zunächst nur lesend 3537:100a, xpad/usbhid, Kernel/Modul/Dienst,
   Pause und leeren Besitzstand frisch bestätigen; normale Eingaben prüfen.
2. Den konkreten Lauf an die **neu beobachtete** Geräteinstanz binden:
   vollständiger Host.Device-Datensatz, canonical USB-Pfad, beide Interface-
   Inodes/Treiber und frische Dienst-PID in privatem `approved-instance.json`
   (Schema 1). Das Manifest fehlt derzeit absichtlich; alte Adresse 18 und
   alte Inodes werden nicht als neue Messung übernommen. Die vorhandenen
   Kernel-/Boot-/Paket-/Modulhashprüfungen bleiben zusätzlich bestehen.
3. Erst dann diesen einen Lauf einschließlich Passwortabfrage konkret
   freigeben. Der vorbereitete Runner führt intern genau einmal
   `gamesir-native resume` aus. Das erlaubt gezielte Übernahme und Bootstrap;
   keine neue Modulaktion, Installation oder Autostartaktivierung.
4. 15 Sekunden Vorlauf; bei waiting_input Ansage für A und Sticks. Höchstens
   90 Sekunden bis bestätigter nativer Übernahme. Danach unveränderte 150
   Sekunden: 30 Ablegepuffer, 20 Ruhe, 10 Vorbereitung, 60 Eingabe/IMU,
   10 Ablegepuffer und 20 Schlussruhe. Alle 15 Zielcodes inklusive vier
   Zusatztasten erfassen; IMU bleibt Rohwert-Snapshot, kein voller USB-Stream.
   Keine Motorimpulse. Erfolg erhält nativen Betrieb, Autostart bleibt aus.
5. Nur mit vorheriger gesonderter Freigabe im Fehlerfall nach versuchtem Resume
   genau einmal `gamesir-native release`, anschließend Zustand lesen und
   anhalten. Kein automatischer neuer Lauf oder Modus-/USB-Reset. Falls
   returned=false bleibt, keinen normalen Rückweg behaupten.

Der spätere konkrete Aufruf auf dem CachyOS test host lautet nach Übertragung und
Freigabe `sudo /usr/bin/python -B /home/example/gamesir-native-build/20261015-revision4-bootstrap-metadata-gap-fix/resume-test.py`;
intern `sudo /usr/bin/gamesir-native resume`, im genehmigten Fehlerfall einmal
`sudo /usr/bin/gamesir-native release`. Die GUI-/SSH-Passwortweitergabe bleibt
unverändert ohne Passwort in Argumenten, Umgebungsvariablen oder Dateien.
Aktueller Auftrag erteilt **keine** dieser Hardwarefreigaben.

### Frische Vorprüfung nach Wiedereinstecken bestanden

[tester] gab zuerst das manuelle Wiedereinstecken und eine frische lesende
Vorprüfung frei, weiterhin kein Resume/Bootstrap und kein Autostart. Danach
bestätigte er den eingesteckten Dongle und verbundenen Funkcontroller.

Der unprivilegierte SSH-Check um 17:36:42 MESZ erfasste mit dem vorhandenen
Host.scan-Adapter ausschließlich Sysfs-Metadaten. Ein erster Leseschritt
stieß an einen rootgeschützten Modulparameter; im vollständigen öffentlichen
Bericht sind die drei geschützten Parameter als nicht gelesen markiert.
Auch die Manager-CLI verweigerte ohne Root-Rechte den Zugriff. Keine
Rechteänderung oder eigenständige Erhöhung; diese Grenzen sind dokumentiert.

Öffentlich bestätigt: Kernel 7.2.9-2-cachyos-deckify und passende Header,
gamesir-native-dkms 0.1.0.alpha3-4, DKMS installed, Modul-Srcversion
499FB2049A64E55F54B712C, passender komprimierter Modulhash und keine Aliase.
Unit-/Manager-/Modulquellenhashes und Steam-Prozess/-Startzeit unverändert.
Frische vollständige Quelle: 1-3.2, 3537:100a, Bus 1/Adresse 21,
USB-Inode 59146, Parent-Inode 36127; IF0-Inode 59197/xpad und
IF1-Inode 59319/usbhid. Keine Scanfehler oder native Bindung, Referenzen 0.
Diese Werte sind die gezielte Testzuordnung, keine festen Produktionsports.

[tester] gab anschließend genau den vorbereiteten einmaligen privilegierten
Lesehelfer inklusive Passwortabfrage frei. Nach erneuter unveränderter
öffentlicher Instanzprüfung wurde nur dieser Helfer übertragen, per Hash
verglichen und am 15. Oktober um 17:40:11 MESZ genau einmal ausgeführt:

- `gamesir-native status`, Exit 0.
- `cat /var/lib/gamesir-native/state.json`, Exit 0.
- Ein `cat` der Parameter bootstrap_mode, enable_output, persistent_mode,
  Exit 0; Ergebnis jeweils Y.

Status und Zustandsdatei bestätigen paused=true, returned=true, devices und
Leases leer, keine aktuellen Scan-/Portfehler. Die vollständige USB-Instanz,
canonical Topologie, beide Interface-Inodes/Treiber sowie fehlende native
Bindung/ref0 sind vor und nach den Abfragen unverändert. Dienst weiterhin
active/running/disabled, PID 28673, NRestarts 0, keine Jobs/Neustartmarkierungen.
Historische Fehler bleiben als frühere Belege erhalten. Kein USB-Gerät oder
native Kontrollnode geöffnet, kein Resume/Bootstrap, keine Systemänderung.

[tester] bestätigt danach normale Tasten, beide Sticks und Trigger im
Steam-Gerätetest. Damit ist der normale 100a/xpad-Rückweg nach dem vorherigen
abgebrochenen Versuch jetzt bestätigt. Das ist keine native Eingabe-/IMU-
oder Motorabnahme des korrigierten Helfers.

Root-Originale und exakt ausgeführter Helfer lokal privat gesichert,
Remote-/Lokaldigests und SHA256-Liste geprüft; unabhängiger lesender Review
bestanden. Belege: `.local/integration/20261015-revision4-metadata-gap-preflight/`,
insbesondere `records/privileged-read-result.json`, `verification.json`
und `normal-input-user-confirmation.json`. Keine Originale überschrieben.

Das neue `approved-instance.json` des vorbereiteten korrigierten Runners
wurde lokal aus diesem echten Nachzustand erstellt: kompletter Device-
Datensatz/Topologie/Interface-Inodes/Dienst-PID, Modus 0600. Unabhängig mit
den Originalrecords verglichen; keine alten Adresse-18/Inodewerte verwendet.
Der Dateiname bezeichnet die geprüfte Gerätezuordnung, **keine Freigabe für
einen Teststart**. Testhelfer und Manifest wurden noch nicht auf das Ziel
übertragen oder ausgeführt. Neue konkrete Freigabe nötig für genau einen
Resume-/Bootstrap-/150-Sekunden-Lauf und höchstens einen Fehler-Release;
Zeitplan/Motorverbot/Autostart-aus bleiben wie oben. Bei einer inzwischen
geänderten Geräteinstanz erneut lesend prüfen und anhalten; keine automatische
Anpassung der Zuordnung und keine Blindwiederholung.

### Revision 4: Korrigierter Bootstrap-Realtest bestanden

[tester] gab nach der frischen Vorprüfung genau einen Lauf des korrigierten
Helfers einschließlich Passwortabfrage, lesender Eingabe-/IIO-Erfassung und
höchstens einem bedingten Fehler-Release frei. Er nutzte den Steam-Gerätetest,
um während der Eingaben keine Spiele oder anderen Aktionen zu starten.
Dieser einmalige Lauf ist am **15. Oktober 2026, 17:45–17:48 MESZ**, erfolgreich
beendet. Genau ein Resume, kein Fehler-Release, keine Wiederholung und keine
Autostartaktivierung. Kernel/Manager/Paket wurden dafür nicht erneut verändert.

**Verwendeter Stand:** `gamesir-native-dkms 0.1.0.alpha3-4`, Kernel/Header
`7.2.9-2-cachyos-deckify`, Modul-Srcversion `499FB2049A64E55F54B712C`;
Produktkorrektur aus `08bc857`, reine Beobachtungspolitik aus `1f90e89`.
Die tatsächlich ausgeführte Policy ist bytegleich mit der versionierten,
offline getesteten Datei. Observer und vorhandener Ablauf wurden wiederverwendet.

| Schritt | Tatsächliche Zeit (MESZ) | Beleg |
| --- | --- | --- |
| Frischer Vorabcheck | 17:45:10,777 | 100a/Adresse 21, xpad; Autostart aus |
| Einmaliges Resume | 17:45:25,826 | genau ein Aktionsdatensatz |
| Warten auf normale Eingabe | 17:45:26,057 | Ansage für A und Sticks |
| Metadatenquarantäne | 17:45:32,322–32,883 | bootstrapping; danach cleared |
| Nativ aktiv, Observer bereit | 17:45:34,615 | 109c/gs_native, volle Instanz-/Leaseprüfung |
| Ablegepuffer | 17:45:34,615 | 30 Sekunden |
| Anfangsruhe | 17:46:04,684 | 20 Sekunden |
| Vorbereitungspuffer | 17:46:24,634 | 10 Sekunden |
| Eingaben und vorsichtige Bewegung | 17:46:34,690 | 60 Sekunden |
| Ablegepuffer | 17:47:34,690 | 10 Sekunden |
| Schlussruhe | 17:47:44,657 | 20 Sekunden |
| Beobachtung beendet | 17:48:04,690 | 150,075 Sekunden nach nativ aktiv |

UTC, monotone Zeit und die unveränderte evdev-Standardzeitbasis bleiben in den
Originalen erhalten. Phasengrenzen sind Ansagezeiten; Reaktionszeit wird nicht
als Treiberfehler interpretiert. Der Test enthielt ausdrückliche Puffer.

#### Übergabe und Metadatenlücke

Quelle war genau die freigegebene `3537:100a`, Bus 1/Adresse 21,
USB-Inode 59146, IF0-Inode 59197/xpad und IF1-Inode 59319/usbhid.
Ziel ist die neue `3537:109c`, Adresse 22, USB-Inode 59763, am selben
beobachteten Hub-Port `1-3.2`, unveränderter Parent-Inode 36127, IF0 gs_native.
Port und Adressen sind Messwerte dieses Laufs, keine Produktionskonstanten.
Neue Instanz, aktive eigene Lease und Kernel-Tokens `[2, 3]` wurden gemeinsam
validiert; die neue PID allein genügte nicht.

Die reale Metadatenquarantäne endete nach **561,459 ms** (monotone Zeit).
Sie führte weder zu vorzeitigem Release noch zu Bereitschaft ohne Prüfung.
Resume bis bestätigt nativ aktiv: rund **8,789 Sekunden**, innerhalb derselben
90-Sekunden-Beobachtungsfrist. Kein Verlängern oder Zurücksetzen der Frist.

Kernel: `native bootstrap finished: 0`, `failed_stage=0`, `step=6`,
`transition=1`, `tx_count=15`, letzter OUT Status 0 und 64/64 Byte,
`first_rx_status=0`, `old_rx_quiesced=1`. Managerdiagnose: `READY`/State 7,
Fehler 0, pad=1, imu=1, handover=1. Die genaue Ursache der älteren Fehlstarts
wird dadurch nicht nachträglich als gemessener RX-Status bekannt.

#### Tatsächliche Eingaben und IMU-Rohdaten

Gerätename **GameSir G7 Pro**. 14.691 dekodierte EV_ABS-/EV_KEY-Ereignisse
(14.465/226); keine unlesbaren Ereigniszeilen und kein gemeldetes SYN_DROPPED.
Alle 15 geforderten Tastencodes sind registriert und mit tatsächlichem Druck
und Loslassen belegt: 304, 305, 307, 308, 310, 311, 314, 315, 316, 317, 318
und 704–707. Alle zuletzt beobachteten Tastenwerte sind 0.

| Zusätzlicher Code | Drücken | Loslassen |
| --- | ---: | ---: |
| 704 | 7 | 7 |
| 705 | 9 | 9 |
| 706 | 8 | 8 |
| 707 | 11 | 11 |

Zusätzlich KEY_RECORD/167 zweimal mit Druck/Loslassen. Dies ist kein Ersatz
für einen der 15 Zielcodes. Die freie Eingabephase bestätigt keine neue
isolierte physische L4/R4/L5/R5-Zuordnung und noch keine Steam-Paddle-Erkennung.

Alle vier Stickachsen erreichen jeweils **−32768…32767**, beide analogen
Trigger **0…1023**, beide D-Pad-Achsen −1/0/+1. Zuletzt beobachtete Stickwerte
sind 0/−1 je Stick, Trigger und D-Pad 0. Während Anfangs- und Schlussruhe
wurden keine evdev-Wertänderungen aufgezeichnet. Das ist kein gesonderter
Kalibrierungs-/Driftnachweis; Anfangsachsen wurden nicht atomar abgefragt.

611 IIO-Snapshots enthalten jedes Mal alle sechs ganzzahligen Rohkanäle;
alle sechs variieren im Lauf. Tatsächlicher Snapshotabstand min/median/max
**0,227502/0,242525/0,315346 s**. Jeweils sechs nacheinander gelesene,
zwischengespeicherte Sysfs-Werte, keine atomaren USB-Pakete und kein Beleg
für 1000-Hz-USB- oder Sensorabtastung.

| Rohkanal | Minimum | Maximum |
| --- | ---: | ---: |
| Beschleunigung X | −5534 | 4280 |
| Beschleunigung Y | 4710 | 9767 |
| Beschleunigung Z | −7439 | 1853 |
| Gyroskop X | −2489 | 1335 |
| Gyroskop Y | −1323 | 1541 |
| Gyroskop Z | −1347 | 1650 |

8192 LSB/g bleibt experimentell; eigenständiger Gyrofaktor, Achsenvorzeichen,
Bias und korrekte physikalische SDL-Sensoreinheiten sind damit nicht bestimmt.

#### Abschlusszustand und Geltungsgrenzen

Dienst active/running/disabled, PID 28673, NRestarts 0. Paused=false,
109c/Adresse 22 weiterhin an gs_native, eigene aktive Lease mit denselben
Instanz-/Kernel-Tokens, aktuelle Scan-/Port-/Gerätefehler leer. 88 Statusproben,
davon 73 active, ohne neuen Zustandsfehler. `returned=false` bedeutet bei
diesem erfolgreichen aktiven Besitz, dass das Gerät nicht zurückgegeben wurde;
es ist hier kein Rückwegfehler. Aufgelöste ältere Fehlereinträge bleiben Historie.

Im erfassten Kernelzeitfenster keine neuen kritischen Warnungen/Oops/Lockups.
Die bekannte xpad-Abbaumeldung `usb_submit_urb -2/ENOENT` bleibt dokumentiert;
sie verhinderte weder Bootstrap noch Eingabetest. [tester] bestätigt ausdrücklich:
**„Ja, alles stabil und Eingaben normal“**. Der native Betrieb bleibt wie im
freigegebenen Erfolgsplan aktiv, Autostart bleibt aus. Den bedingten
Fehler-Release nicht nachholen. Einmallauf verbraucht, keine weiteren
Hardware-, Modul-, Bindungs-, Installations- oder Sitzungsaktionen ausgeführt.

**Ergebnis:** Begrenzter eigenständiger CachyOS-Bootstrap mit Gamepad und sechs
IMU-Rohkanälen bestanden. Kein neuer Motor-, Spiele-, Funk-Reconnect-, Hotplug-,
Boot-, Suspend- oder Mehrgerätebeleg. Garuda test host-System unverändert, kein Push.
Nächster Nutzerauftrag ist die dauerhafte Steam-Paddle-Zuordnung in Gamescope:
bestehende optionale Erweiterung offline prüfen, Installation/Sitzungsneustart
danach separat freigeben. Der Treiberkern muss dafür nicht erneut geladen werden.

#### Originale, Auswertung und Integrität

Privat lokal: `.local/integration/20261015-revision4-bootstrap-metadata-gap-fix/`.
Remote Originalordner: `/home/example/gamesir-native-build/20261015-revision4-bootstrap-metadata-gap-fix/`.
15 gesicherte Originaldateien, zusammen 2.086.914 Byte, lokal unter `records/`;
alle Größen/SHA256 gegen `remote-record-hashes.json` geprüft. Ausgeführte
Skripte/Manifest stimmen mit den freigegebenen lokalen Artefakten überein.
Der bestehende Analyzer wurde mit diesen Dateien ausschließlich offline
wiederverwendet; Ergebnis `analysis.json`, Userbeleg separat. Unabhängiger
Subagent-Review bestätigt Originalhashes, Übergabe, alle 15 tatsächlichen
Tastencodes, sechs Rohkanäle und aktiven Endzustand mit deaktiviertem Autostart.

| Originaldatei | SHA256 |
| --- | --- |
| evtest.txt | `bf67cb585c5fa7ceb3cd7b4edc806308336557057494d1a2a0a5bfe58661b52a` |
| imu-raw.jsonl | `87caabac3670e5bc87056c4984cb914fcf760622008122dc1b4f832a2b72f22a` |
| observations.jsonl | `2db215af0a0c5465cb40c801d3878ac28484e8820542b4ed67901c6b240a3adb` |
| kernel-observed.jsonl | `de06d654351db2647c885658b51ac56517e5b49063ba6eb9f56b66b87137cc4d` |
| after.json | `061e30a6ec0e16ab06163a4c8280ef828de2bb60987f30a9026d62fd23ff26f7` |

Rohdaten enthalten private Gerätekennungen und bleiben ignoriert; keine
ungefilterten Originaljournale oder Serien-/Bootkennungen in Git. Lokale
SHA256-Liste umfasst Originale und abgeleitete Prüfdaten; frühere Originale
wurden weder gelöscht noch überschrieben. Dokumentationsänderung benötigt
keinen erneuten Kernelbau oder Hardwarelauf.
