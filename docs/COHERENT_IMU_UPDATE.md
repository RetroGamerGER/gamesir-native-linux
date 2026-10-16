> Public export: personal tester, host and path references were anonymized. Historical evidence hashes refer to the private originals.

# Kohärenter Sensorstrom: Updatevorbereitung am Garuda test host

## Neuester Lesebefund: native Übernahme bereits erfolgt

[tester] gab anschließend den einmaligen Resume nach frischer Prüfung frei,
meldete aber zugleich bereits verbundenen/gebundenen Controller. Vor einer
erneuten Aktion zeigte die öffentliche Prüfung tatsächlich 109c/gs_native
und erfolgreichen Bootstrap im neuen Dienst. Deshalb **kein Resume-Aufruf
durch Codex**, auch kein erneuter Start, Moduswechsel oder Bindungszugriff.

Die danach einschließlich Passwortfenster freigegebenen reinen Status-/
Zustandsabfragen bestätigen um 18:49 MESZ:

- Dienst weiterhin active/running/enabled, PID51607, NRestarts0.
- Neuer Build71D6C2E25BA80E69BB4818D; Bootstrap 100a/Adresse16→109c/Adresse17,
  READY/Fehler0 und initialer Gamepad-/IMU-Nachweis im Bootstrapbericht.
- Genau eine eigene aktive Lease; boot_id, kanonischer Geräte-/Parentpfad,
  Adresse17, Geräteinode99051, Parentinode28887 und Tokens [1,2] passen.
- paused=false, keine aktuellen Scan-/Port-/Einzelfehler oder Statuskonflikte.
- Dasselbe USB-/IIO-Gerät und derselbe Dienst vor/nach den Leseabfragen.
- IIO-Gerät0/Inode99312, dev235:0; sechs LE-s16-Kanäle, LE-u64-Hostzähler
  und nativer s64-Zeitstempel mit fortlaufenden Scanindizes 0…7 vorhanden.
- Hostuhr monotonic, Länge128/Watermark1; alle acht Kanäle, Puffer und
  Stream-Gate weiterhin0, Pushfehler0. Kein Schreibzugriff auf Einstellungen.

`returned=false` ist im aktuellen aktiven/unpausierten Besitzstand erwartet;
es wurde kein neuer Rückweg angefordert. Alte100a-Bootstrapinstanz und neue
109c-Lease dürfen unterschiedliche Adressen/Inodes haben. Die Tokens des
vorher geladenen Moduls sind nicht die Tokens des neuen Starts.

Diese Prüfung belegt Registrierung, Besitzzuordnung und die gespeicherte
erfolgreiche Initialisierung, keinen neuen Eingabe-/Motorfunktionstest und
keine einzige gelesene kohärente Pufferprobe. Pushfehler0 bei ausgeschaltetem
Puffer ist kein Übertragungsnachweis. Keine Sensorrohdaten oder Geräte-/
Control-Knoten geöffnet; keine Messung, Kalibrierung oder SDL-Freigabe.

Private Originale/SHA256:
`.local/integration/20261016T164923Z-coherent-user-resume-readback/`.
Die [Abschlussmetadaten](evidence/COHERENT_IMU_INSTALL_20261016.json)
erhalten den früheren pausierten Start und ergänzen diesen späteren Zustand.
Offen sind ausschließlich separat freizugebender Puffer-/Messaufbau und
die drei begleiteten horizontalen90°-Linksdrehungen. Kein automatischer
weiterer Resume aus der bereits erreichten Übernahme ableiten.

## Vorangegangener Abschluss: Installation und pausierter Start bestanden

Am 16. Oktober gab [tester] nach den beiden erfolgreich geprüften geschützten
Leseabfragen genau einen Release, danach das geprüfte Paketupdate und
anschließend bei erfolgreichen Prüfungen den Dienststart frei. Diese
Schritte sind abgeschlossen. Die folgende Vorbereitung bleibt als
historischer Freigabeplan erhalten; verbrauchte Befehle nicht wiederholen.

| Tatsächlicher Prüfschritt | Ergebnis |
| --- | --- |
| Einmaliger expliziter Release | Exit0, paused=true, returned=true, Leases leer |
| Reale Rückkehr | `3537:100a`, Bus8/Adresse14/Inode95355; IF0xpad, IF1usbhid |
| Pakettransaktion | Genau gamesir-native-dkms `0.1.0.alpha3-3 → 0.1.0.alpha3-5`, Exit0 |
| Nutzlast | 81 Dateien bytegleich, root:root und erwartete Modi; Qkk102Einträge/0 verändert |
| Upgrade-Schutz | Pause, sicherer Dienststop, unbenutzten alten Build entladen; keine native Bindung übrig |
| DKMS | Tatsächlich installed für `7.2.11-1-garuda`; frisches make.log mit `# exit code: 0` |
| Neuer Modulbau | Srcversion `71D6C2E25BA80E69BB4818D`, passende Vermagic, keine Autoload-Aliase |
| Abhängigkeiten | `ff-memless,industrialio,kfifo_buf` |
| Komprimiertes installiertes Modul | SHA256 `aec4a4fb585bbc8f3894ec18492020054dae503d5a7c5c6cf9753c7514111a8a` |
| Vorhandene Systemhooks | DKMS/systemd/sysusers/Garuda/dracut bestanden; Snapper91/92 |
| Getrennt freigegebener Dienststart | Ein systemctl start, Exit0; active/running/enabled, PID51607, NRestarts0 |
| Geladenes Modul | Neuer Srcversionstand, bootstrap_mode/enable_output/persistent_mode jeweilsY, kfifo_buf geladen |
| Verwaltungszustand danach | paused=true, Leasesleer, keine aktuellen Fehler, keine native Bindung/IIO-Instanz |
| USB beim pausierten Start | Derselbe100a-Dongle/Adresse14/Inode95355 an xpad/usbhid unverändert |

Der Root-Leser prüfte ausschließlich gespeicherten Zustand und Baulog;
kein Kontrollgerät wurde dafür geöffnet. Die unmittelbare Statusabfrage
nach dem neuen Managerstart meldet `returned=false`: `returned()` benötigt
mindestens eine Sekunde beobachteten Normalzustand. Diese Startabfrage vor
Ablauf der Beobachtungsfrist ist kein neuer fehlgeschlagener Rückweg. Der
zuvor real belegte Release mit `returned=true`, leere Leases und der
unveränderte xpad-Zustand bleiben gültig. Eine neue Geräteübernahme wurde
nicht angefordert; kein zusätzlicher Release wurde daraus abgeleitet.

Bekannte Hinweise: Clang23.1.1 beim Kernel gegenüber lokal23.1.3 im echten
DKMS-Baulog, DKMS `Deprecated feature: CLEAN` im Transaktionslog. Beim ersten
Passwortfenster wechselte Qt seinen Prozesszeichensatz von C auf C.UTF-8;
keine Systemlocale geändert. Keine weiteren Bauwarnungen/-fehler im geprüften
DKMS-Log. Das gelesene Kernelzeitfenster enthält die Ab-/Anmeldung des
Treiberregistrators; das belegt keinen Gamepad-/Sensorfunktionstest.

Altes Paket/Modul und sämtliche Originalbelege bleiben privat erhalten:
`.local/integration/20261016T163456Z-coherent-iio-revision5-install/`.
Eigene [Abschlussmetadaten](evidence/COHERENT_IMU_INSTALL_20261016.json)
enthalten Prüf- und Belegshashes. Kein Push und kein CachyOS test host-Eingriff.

**Damals noch offen:** einmaliges Resume/native Übernahme und danach
IIO-Pufferaufbau samt Rückstellung sowie die drei horizontalen90°-Linksdrehungen.
Die inzwischen erfolgte Übernahme ist oben lesend bestätigt. Pufferaufbau und
Drehtest bleiben separat freizugeben; noch keine Bewegungskalibrierung oder
SDL-Skalierung bestätigt.

## Historischer Vorbereitungsstand vor der Installation

Stand: 16. Oktober 2026. Ausschließlich unprivilegierte lesende Hostprüfung
und lokaler Paket-/Modulbau ausgeführt. Keine Installation, Passwortabfrage,
Dienst-/Modul-/Bindungsänderung, USB-Befehle oder Sensorrohdatenaufnahme.
Der CachyOS test host wurde nicht angesprochen. Kein Push.

## Lesender Ausgangsbefund

| Prüfung | Beobachtung |
| --- | --- |
| Kernel und vorbereitete Header | `7.2.11-1-garuda`, UTS_RELEASE passend, Module.symvers vorhanden |
| Installiertes natives Paket | `gamesir-native-dkms 0.1.0.alpha3-3` |
| DKMS | GameSir für diesen Kernel installed |
| Installiertes/geladenes Modul | `0.1.0.alpha3`, srcversion `C6818C24711721D136684D5` |
| Bisherige Modulabhängigkeiten | `ff-memless,industrialio` |
| Dienst | active/running/enabled, PID1060, NRestarts0 |
| Letzter vollständiger USB-Befund | `3537:109c`, Bus8/Adresse13, beobachteter Port8-6 |
| Interfaces | IF0 `gs_native`, IF1 ungebunden |
| IIO | `gamesir_g7pro_raw_experimental`, `iio:device0`, alter direkter Rohwertpfad |
| Neuer Standardpuffer | Im installierten Stand noch nicht vorhanden |
| Paketabhängigkeiten | `pacman -T` für alle elf erforderlichen Pakete erfolgreich |

Der erste USB-Schnappschuss sah noch Adresse11/xpad ohne natives IIO. Nach
[tester]' Bestätigung „eingeschaltet und verbunden“ zeigte die frische Prüfung
Adresse13/gs_native und IIO. Das Dienstjournal meldet um 18:21:44 MESZ
erfolgreichen Bootstrap/ready. Codex hat keinen Wechsel ausgelöst. Alte
Adressen und der beobachtete Port sind keine fest kodierte Geräteauswahl.

Im begrenzten gefilterten Kerneljournal wurden Start-/Bindungsnachrichten
und die bekannte Unsigned-/Out-of-tree-Modulmeldung gefunden; daraus keine
generelle Fehlerfreiheit ableiten. Managerstatus, gespeicherte Pause/Leases
und Modulparameter sind durch Dateirechte geschützt und noch **nicht**
frisch geprüft. Öffentlicher Dienststatus ersetzt diesen Besitznachweis nicht.
Private öffentliche Prüfausgaben mit SHA256:
`.local/integration/20261016-coherent-update-preparation/`.

## Geprüftes Updateartefakt

Paket im Repository:

```text
build/alpha3-coherent-iio-revision5-reviewed/gamesir-native-dkms-0.1.0.alpha3-5-x86_64.pkg.tar.zst
```

Paket-SHA256:
`fe2b02bbd7455525a5090bb33751d5d4c98358141526992f09aecfcbc4bc312b`.
Quellarchiv-SHA256:
`9247efc0ed9160a0dd4be4c5482515426c70790c5e699960019d0412ef2ebe82`.

84 ausdrücklich ausgewählte Quellarchivdateien stimmen bytegenau mit dem
Repository-Snapshot überein. 81 reguläre Nutzlastdateien, root:root und
geprüfte Modi 0644/0755; 80 Dateien bytegenau gegen Soll geprüft. Der
zusätzliche gebaute/gestrippte Client besteht seinen Offline-Selbsttest.
Keine fremden Installer, Firmware oder Rohmitschnitte enthalten.

24 Paket-/Rückwegregressionen bestehen. Einmaliger `makepkg` ohne Root,
Synchronisierung, Installation oder Netz. Der aus den **tatsächlich
entpackten Paketquellen** gebaute Kernelstand besteht Kbuild mit Exit0:

| Prüfung | Erwarteter neuer Stand |
| --- | --- |
| Paketversion | `0.1.0.alpha3-5` |
| Modulversion | Weiter `0.1.0.alpha3`, allein kein Buildnachweis |
| srcversion | `71D6C2E25BA80E69BB4818D` |
| Vermagic | `7.2.11-1-garuda SMP preempt mod_unload` |
| Abhängigkeiten | `ff-memless,industrialio,kfifo_buf` |
| USB-Autoload-Aliase | Keine |
| Gebautes Modul-SHA256 | `e151fb5c877f84810d77bfc0acd4afe96bd7fec656514ad6f9085de6407bd15a` |

Ein bekannter Kbuild-Hinweis bleibt dokumentiert: Kernel Clang23.1.1,
lokaler Compiler Clang23.1.3. Keine anderen Bauwarnungen oder Fehler.
Moduldateihashes können beim späteren DKMS-Bau durch Baupfad/Zeit/Metadaten
abweichen; deshalb auch Quellen, srcversion, Vermagic und Abhängigkeiten
prüfen, nicht blind bytegleiche Module behaupten.

Das Update enthält gegenüber Garuda test host-Revision3 neben dem neuen Puffer auch
die bereits vorbereitete Bootstrap-/Fehlerursachen-/Metadatenkorrektur aus
Revision4. Installierter Upgrade-Guard und Systemd-Unit sind bytegleich mit
den vorbereiteten Versionen. Die Steam-Pakete werden nicht aktualisiert.
Diagnoseleser und Referenzanalysator werden weiterhin gezielt aus dem
Repository verwendet; der Installer installiert sie nicht als Systemdienst.

Belege und eigene Prüfprogramme im Releaseordner: `package-audit.json`,
`packaged-kernel-audit.json`, `makepkg.log`, `packaged-kernel-build.log`,
`packaging-tests.log`, Prüfsummenlisten. Ein früherer ungebauter Quell-
Snapshot ohne die abschließenden Dokumentergänzungen bleibt separat unter
`build/alpha3-coherent-iio-revision5/` erhalten und ist nicht das freizugebende
Installationsartefakt. Dieses Dokument wird nach dem eingefrorenen Paket
erstellt und dient als separater Freigabebericht, nicht als Paketpayload.

## Historischer Befehlsplan: erledigte Schritte nicht wiederholen

**1. Nur geschützte Leseprüfung, einschließlich Passwortfenster:**

```sh
sudo /usr/bin/gamesir-native status
sudo /usr/bin/cat /var/lib/gamesir-native/state.json
```

Statusaufruf fragt nur den lokalen Managersocket ab und öffnet kein
Controllergerät. Aktuelle Leases, Besitzerinstanz, Pause und Fehler müssen
zum tatsächlichen USB-/Treiberzustand passen. Bei Widerspruch anhalten.
Die erste Freigabe soll ausschließlich diese beiden Abfragen umfassen.

**2. Nach erfolgreicher Prüfung, Spiele/Deadband geschlossen: separat Release.**

```sh
sudo /usr/bin/gamesir-native release
```

Dies ist eine Zustandsänderung: Übernahme pausieren, nur verwaltete Geräte
kontrolliert stoppen/zurückgeben. Erst bestätigtes `returned:true`, leere
Besitznachweise und tatsächlichen Rückkehrzustand prüfen. Ein an xpad
gebundenes109c-Gerät ist dadurch nicht automatisch100a geworden.

**3. Nur danach das exakt geprüfte Paket installieren:**

```sh
sudo /usr/bin/pacman -U -- "/path/to/gamesir-native-linux/build/alpha3-coherent-iio-revision5-reviewed/gamesir-native-dkms-0.1.0.alpha3-5-x86_64.pkg.tar.zst"
```

Die unprivilegierte `pacman -Up --print-format '%n %v'`-Vorschau nennt genau
`gamesir-native-dkms 0.1.0.alpha3-5`. Vor der wirklichen Bestätigung erneut
prüfen. Zusätzliche Pakete, Konflikte, nötige Datenbanksynchronisierung oder
Systemupgrades stoppen den Vorgang. Kein `-Sy`, kein `--noconfirm`.

Der bestehende PreTransaction-Guard prüft die Freigabe erneut, stoppt den
Dienst und entlädt ausschließlich das nachweislich unbenutzte `gs_native`.
Das ist Teil der späteren Installationsfreigabe, auch wenn der Pacman-Aufruf
selbst nur eine Zeile ist. Kein globales xpad-Entladen. Die vorhandenen
DKMS-/systemd-/sysusers-/Garuda-/Snapper-/Initramfs-Hooks gehören ebenfalls
zur Transaktion. Diese können `/boot` und Snapshots ändern; Hookfehler
niemals durch automatische Reparatur umgehen. Kein automatischer Neustart.

**4. Nach Installation nur prüfen:**

```sh
pacman -Q gamesir-native-dkms
pacman -Qkk gamesir-native-dkms
dkms status -m gamesir-native -v 0.1.0.alpha3 -k 7.2.11-1-garuda
modinfo gs_native
systemctl show gamesir-native.service -p ActiveState -p SubState -p UnitFileState -p MainPID
```

Zusätzlich erforderliche geschützte DKMS-Logs und gespeicherten Zustand
konkret zur Lese-Freigabe zeigen. Erwartet: neuer Paket-/Quell-/Modulstand,
erfolgreicher tatsächlicher DKMS-Bau, keine native Bindung/kein geladenes
altes Modul, Dienst gestoppt, Verwaltung pausiert, leere Leases. Der
Autostartlink bleibt bestehen; er ist keine Freigabe zum Reboot oder Resume.
Pacman Exit0 allein beweist keinen erfolgreichen DKMS-Bau.

**5. Erst nach getrennter Freigabe pausiert starten und kontrollieren:**

```sh
sudo /usr/bin/systemctl start gamesir-native.service
```

Dies lädt den neuen Build und Abhängigkeiten. Vorher Pause/leere Leases
bestätigen, damit der Start keine ungeprüfte Übernahme auslöst.

**6. Erst danach separat native Übernahme freigeben:**

```sh
sudo /usr/bin/gamesir-native resume
```

Erlaubt Übernahme und Bootstrap am frisch ermittelten Zielgerät. Bei Fehler
anhalten; kein neuer Lauf, Reset, Umstecken oder Rückfall auf Verdacht.
Ein Fehler-Release oder Downgrade braucht eine konkret benannte Freigabe.
Alte Pakete/Belege bleiben erhalten; ein erfolgreicher Rückweg wird nur mit
tatsächlichem Geräte-/Besitznachweis behauptet.

## Danach ausschließlich drei 90°-Linksdrehungen vorbereiten

Tastenfläche nach oben, USB-Kante zunächst vom Spieler weg. Horizontal
90° nach links drehen, bis die USB-Kante nach links zeigt. **Nicht senkrecht
hochkippen.** Externe rechtwinklige Markierungen statt Gyro als Winkelmaß.
Je Wiederholung frische Bereitschaft, 30s erste Vorbereitung, Vorruhe,
Aufnehmen-/Ablegenpuffer und ruhige Ränder; Zurückdrehen erst außerhalb der
Integration. Details im [Referenzplan](COHERENT_IMU_CALIBRATION.md).

Pufferkonfiguration/-aktivierung und Rückstellung sind eigene freizugebende
Hostzustandsänderungen. Schließen des Lesers deaktiviert den Puffer nicht.
Vorher müssen genaue neue IIO-Instanz, Zugriffsrechte und alle ursprünglichen
Einstellungen vorliegen. Kein Motorimpuls, keine Sensorkonfigurationsbefehle.
Ein ausführender Winkelassistent ist noch separat vorzubereiten/zu prüfen;
die reinen JSON-Pläne sind kein bereits startbarer Dreifachtest.
Rechts-/Vorwärts-/Rückwärts-/180°-Tests gehören nicht zu diesem nächsten Lauf.
