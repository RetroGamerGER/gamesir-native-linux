# IIO-Kanalauswahl: Korrektur und begrenzte Hardwareabnahme

Stand: 18. Oktober 2026. **PRE-ALPHA alpha3-7 separat freigegeben installiert;
kohärenter Pufferaufbau und Rückstellung auf einem Standard-G7-Pro bestätigt.**
Ein ausdrücklich neu angeforderter Linksdrehungsversuch wurde als ausgeführt
bestätigt. Ein vorheriger Lauf mit vorzeitiger Rückdrehung bleibt von der
Achsenauswertung ausgeschlossen. Die bekannte Winkelkalibrierung bleibt pausiert.

## Ursache und unabhängige Gegenprüfung

Der separat freigegebene Achsenlauf scheiterte nach lokalem Go beim ersten
Schreiben von `1` nach `scan_elements/in_accel_x_en` mit `EINVAL`. Die einzige
zuvor erfolgreiche Änderung, Pufferlänge 128 → 512, wurde wieder auf 128
zurückgestellt. Kein Aufnahmestart und keine Messdaten. Originalbelege bleiben
privat erhalten; siehe [Laufbericht](GYRO_AXIS_TEST.md#neuer-einzellauf-kanalauswahl-vor-aufnahmebeginn-abgelehnt).

`validate_scan_mask` wird im Linux-IIO-Core bereits für einzelne neue
Kanalauswahlen aufgerufen. Die alte Funktion `gsn_iio_scan_mask()` verlangte
sofort exakt `0x7f` (alle sechs Sensorkanäle plus Berichtszähler). Das erste
Zwischenergebnis ist jedoch `0x01`. Somit konnte die vollständige Auswahl
ausgehend von allen deaktivierten Kanälen nie erreicht werden.

Die Gegenprüfung erfolgte ausschließlich statisch an vorhandenen Dateien:
Kernelheader, BTF-Typinformationen und disassembliertes `industrialio.ko`
des lokal installierten Kernels `7.2.11-1-garuda`. Kein Netzwerkzugriff,
Modulladen, Kernelcode-Ausführen oder Gerätezugriff. Geprüfte Dateihashes:

| Datei | SHA256 |
| --- | --- |
| `industrialio.ko.zst` | `c6e39a07e2ab02fe4dfe292b46e271f5df2d29d82a9bb46dcc1611f769de9e2a` |
| Entpacktes `industrialio.ko` | `311d5d97bcad10f246c4e6fa98a272eaacf6f6d1c4a9623906e122ea896ecc4b` |

Die folgenden Adressen sind `.text`-Offsets **dieses** ELF-Artefakts, keine
Live-Kerneladressen oder portablen Versionskonstanten:

- `iio_scan_el_store`, `0x9ee5..0x9f16`: setzt das neue Bit in einer temporären
  Maske und ruft den optionalen Callback auf; false führt zum Fehlerpfad.
  BTF bestätigt `setup_ops` und dessen Callback-Offset 32.
- `0x9f1c..0x9ffe`: sucht eine passende verfügbare Maske mit
  `__bitmap_subset` und übernimmt die Anfrage erst nach erfolgreicher Prüfung.
  `0x9f8c..0x9f94`: Ausschalten eines Bits benötigt diesen Callback nicht.
- `__iio_update_buffers`, `0x79b8..0x7a71`: Auswahl aus den verfügbaren
  Produzentenmasken; für den Softwarepuffer kann eine Obermenge passen.
  `0x7c9a` setzt `active_scan_mask` **vor** dem `preenable`-Aufruf bei
  `0x8322..0x833a`. BTF bestätigt die betreffenden Strukturfelder.

Die ursprüngliche Gleichheitsprüfung wurde außerdem aus unserem echten
Treiberquelltext in den bestehenden C-Testadapter übernommen: Der neue
schrittweise Konfigurationstest schlug vor der Korrektur beim ersten Kanal
fehl. Eine bleibende Negativkontrolle setzt den alten Callback nur in einer
generierten Testkopie wieder ein. Der echte Python-Pufferhelfer reproduziert
daran denselben `EINVAL` samt erfolgreicher Rückstellung.

## Korrektur und unveränderte Daten

Der überstrenge Callback entfällt. `available_scan_masks` enthält weiterhin
nur `0x7f`: Der Treiber liefert stets alle sechs Rohkanäle und den Zähler aus
demselben akzeptierten IMU-Bericht. Die Standard-IIO-Auswahl kann Zwischenstände
und Teilanfragen annehmen; der Core übernimmt gegebenenfalls deren Demultiplexen.

Zusätzlich prüft `gsn_iio_preenable()` die **vom Core ausgewählte aktive
Produzentenmaske** auf exakt `0x7f`. Eine fehlende oder andere aktive Maske
wird vor dem Streamstart abgewiesen. Monotonic-Uhr, Frische-/Zustandsprüfungen
und Stream-Gate bleiben erhalten. Der Softwarezeitstempel ist separat wählbar.

Der Messhelfer verlangt weiterhin alle acht Scan-Elemente und das unveränderte
32-Byte-Format: sechs LE-s16-Rohwerte, Nullpadding, LE-u64-Berichtszähler und
nativen s64-Hostzeitstempel. Keine Skalierung oder Achsenumordnung. Gamepad,
Paddles, Bootstrap und Motorsteuerung werden nicht geändert.

## Offline-Abnahme und Grenzen

- Vollständige `make test`-Suite: 958 Python-Unittest-Fälle sowie die separaten
  C-/Adapter-/Protokollprüfungen, einschließlich einer frühen Ablehnung des
  alten fehlerhaften Modulstands ohne Geräteöffnung.
- IIO-Adapter: 47 Prüfgruppen mit echten extrahierten Treiberfunktionen und
  deren registrierten Setup-Callbacks. Schrittweises Einschalten/Ausschalten,
  254 Teilmengen-/Zeitstempelvarianten, leere/ungültige Auswahl, Änderungen
  am aktiven Puffer sowie fehlende/falsche aktive Produzentenmasken.
- Elf Verknüpfungen des echten Python-Aufbaus/Rückwegs mit dem C-Auswahlmodell:
  Erfolg und Fehler an jedem der zehn Konfigurationsschritte. Zusätzlich der
  historische erste-Kanal-Fehler mit unverändertem ursprünglichem Fehlergrund.
- Fünf absichtlich beschädigte C-Varianten werden erkannt, darunter der alte
  Callback und eine entfernte Produzentenmaskenprüfung. ASan/UBSan; zwölf
  bestehende synthetische C-Scan → Python-Decoder/Referenzanalyse-Fälle bleiben
  erfolgreich. Das sind keine physikalischen Kalibriermessungen.
- Modulbau für `7.2.11-1-garuda`: keine Codewarnungen, passende Vermagic und
  keine automatischen USB-Aliase. Bekannter Umgebungshinweis: Clang 23.1.3
  lokal gegenüber 23.1.1 beim Kernelbau.
- Clang Static Analyzer: null Befunde in fünf Übersetzungseinheiten.
  Checkpatch für den Patch: null Befunde. Die Gesamtdateiprüfung meldet
  weiterhin eine Warnung und drei Formatierungshinweise, die auch in der
  unveränderten Vorgängerversion auftreten; kein vollständig sauberer
  Gesamtdatei-Checkpatch wird behauptet.

Das Auswahlmodell ist anhand des vorhandenen Cores überprüft, führt aber
Linux-Sysfs, FIFO, Demultiplexer und IRQ-Konkurrenz nicht aus. Die spätere
begrenzte Live-Abnahme unten ergänzt Pufferlesen, Timing und Rückstellung;
sie ersetzt keine umfassenden Konkurrenz- oder Spieltests.

## Historischer Update- und Messplan vor der separaten Freigabe

Die folgenden Freigabehinweise beschreiben den ursprünglichen Plan.
Installation und zwei einzeln angeforderte Versuche sind inzwischen wie
unten dokumentiert abgeschlossen. Keine Freigabe weiterer Läufe.

Paketkandidat: `gamesir-native-dkms 0.1.0.alpha3-7` (weiterhin PRE-ALPHA).
Modul-`srcversion`: `A15BC39B5A21D181E4E5C49`. Der Messhelfer ist ausschließlich
auf diesen geprüften Quellstand festgelegt; der alte Stand
`71D6C2E25BA80E69BB4818D` wird bereits bei der Metadatenprüfung abgewiesen.
Keine Hash-Prüfung entfernen, kein altes Manifest weiterverwenden.

1. **Separate Updatefreigabe:** frische Kernel-/Header-, Paket-, Dienst-,
   Besitz- und Geräteprüfung; Spiele und Deadband geschlossen. Sicheren
   Rückweg mit dem vorhandenen Manager bestätigen, dann erst Paketupdate.
   Bei blockiertem Rückweg anhalten, keine USB-Resets oder Wiederholungen.
2. Der vorhandene Upgrade-Hook führt `release`, sicheren Dienststop und nur
   bei leerem Besitz/bindungsfreiem Modul dessen Entladung aus. DKMS baut neu;
   die systemeigenen ALPM-/Snapshot-/Initramfs-Hooks können zusätzlich laufen.
   Das ist ein Eingriff in den normalen Betrieb und hier **nicht** freigegeben.
3. Nach Update nur lesend Paket, DKMS, Vermagic und Modulquellstand prüfen.
   **Eigene Aktivierungsfreigabe:** pausierter Dienststart, lesende Prüfung,
   dann einmal Resume. Eingaben und neue native Instanz bestätigen.
4. **Eigene Messfreigabe:** neues privates Manifest für die frisch ermittelte
   IIO-Instanz; genau ein `run-axis-left`, Wiederholung 1. Kein genauer Winkel.
   Lokales Go, 30 Sekunden Vorbereitung, danach der unveränderte
   [108-Sekunden-Ablauf mit Reaktionspuffern](GYRO_AXIS_TEST.md#ablauf-pro-wiederholung).
   Rückdrehen erst nach bestätigtem Aufnahmeende und Rückstellung.
5. Prüfsummen, Berichtszähler/Zeitabstände, alle ursprünglichen Einstellungen,
   native Bindung und normale Eingaben nachprüfen. Kein automatischer zweiter
   Lauf. Kein bestätigter Achsen- oder Skalierungswert vor Auswertung.

Vorbereitete Befehlsformen, **nicht in dieser Arbeit ausgeführt**:

```sh
# Erst nach Updatefreigabe und erfolgreicher Vorprüfung:
SUDO_ASKPASS=/usr/bin/ksshaskpass sudo -A -p 'Password: ' \
  /usr/bin/pacman -U build/PRE-ALPHA-iio-selection/gamesir-native-dkms-0.1.0.alpha3-7-x86_64.pkg.tar.zst

# Erst nach getrennter Aktivierungsfreigabe, mit Prüfung zwischen den Schritten:
SUDO_ASKPASS=/usr/bin/ksshaskpass sudo -A -p 'Password: ' \
  /usr/bin/systemctl start gamesir-native.service
SUDO_ASKPASS=/usr/bin/ksshaskpass sudo -A -p 'Password: ' \
  /usr/bin/gamesir-native resume

# Erst nach frischer Instanzprüfung; N und neue private Pfade ersetzen:
python3 -B tools/imu/gamesir_gyro_guided.py prepare \
  --iio-dir /sys/bus/iio/devices/iio:deviceN --device-node /dev/iio:deviceN \
  --output NEW_PRIVATE_DIR/manifest-01.json
python3 -B tools/imu/gamesir_gyro_guided.py run-axis-left \
  --manifest NEW_PRIVATE_DIR/manifest-01.json --repetition 1 \
  --output NEW_PRIVATE_DIR/left-01
```

Das Go-Fenster schließt nach der bestätigten Auswahl. Die späteren KDE-Hinweise
sind zeitlich begrenzt und werden bei der nächsten Phase ersetzt. Ihr
Verschwinden ist allein kein Erfolgssignal: Nur „PUFFER ZURÜCKGESTELLT,
AUFNAHME GESCHLOSSEN“ nach verifiziertem Abschluss erlaubt die Rückdrehung.
Bei Abbruch nicht weiterdrehen oder einen neuen Versuch starten.

## Installation und Hardwareabnahme am 18. Oktober 2026

Die frische Vorprüfung fand den ausgeschalteten Funkcontroller mit neu
angemeldetem Dongle an xpad, ohne IIO-Gerät. Der Nutzer bestätigte den
ausgeschalteten Zustand. Keine aktuellen Managerfehler, Leases oder nativen
Bindungen; Modulreferenzzähler null. Kein fremdes 109c-Gerät wurde übernommen.

Die freigegebene Transaktion aktualisierte ausschließlich
`gamesir-native-dkms` von `0.1.0.alpha3-6` auf `0.1.0.alpha3-7`, aus
Quellencommit `18767d9`. Paket-SHA256:
`dba7164a138dd54e752f1e542629c1db2d7497cb576a7d12c0dcbf0ab33ab6fc`.
Der Upgrade-Hook bestätigte Release, Dienststop und Entladung des unbenutzten
Moduls. DKMS baute für `7.2.11-1-garuda` erfolgreich. Passende Vermagic und
`srcversion=A15BC39B5A21D181E4E5C49`; 130 Paketprüfeinträge unverändert,
alle 100 Paket-Nutzdateien zusätzlich bytegleich mit dem Installer.
Snapshot- und Initramfs-Hooks liefen erfolgreich. Die bekannten Hinweise
zu DKMS `CLEAN` und Clang 23.1.3 gegenüber Kernel-Clang 23.1.1 blieben
sichtbar; keine Codewarnung im erfolgreichen Modulbau. Steam-Mapping und
optionale Trigger-Bridge blieben unverändert.

Nach verifiziert pausiertem Dienststart schaltete der Nutzer den Controller
ein. Der Dongle erschien als 100a/xpad; genau ein freigegebenes Resume
erreichte 109c/gs_native mit erfolgreichem Bootstrap, `failed_stage=0` und
passender aktiver Lease. Der neue Quellstand wurde auch im geladenen Modul
geprüft. Kein Deadband-Start, Firmwarezugriff oder Motorimpuls.

### Zwei Aufnahmen, eine angenommene Bewegung

Jeder Lauf hatte ein frisches Manifest, eigene Passwort-/Go-Prüfung,
30 Sekunden Vorbereitung und 108 Sekunden kohärente IIO-Aufnahme mit lokalen
Zeitmarken. Im ersten Lauf meldete der Nutzer eine vorzeitige Rückdrehung.
Er bestätigte die Bewegung im Abschlussdialog nicht; **keine Achsenauswertung**.
Die Originale bleiben erhalten. Erst auf ausdrücklichen Wunsch nach einem
neuen Versuch, erfolgreicher Rückstellung und frischer Prüfung folgte der
zweite Lauf. Dafür bestätigte der Nutzer lokal eine waagerechte Linksdrehung
ohne Rückdrehung vor Aufnahmeende. Keine automatische Wiederholung; insgesamt
nur **eine** angenommene qualitative Wiederholung.

| Prüfung | Erster Lauf, Bewegung ausgeschlossen | Neuer bestätigter Versuch |
| --- | --- | --- |
| Vollständige 32-Byte-Scans | 6.748 | 6.749 |
| Scan-Dateigröße | 215.936 Byte | 215.968 Byte |
| Abstand erster bis letzter Scan | 107,986059 s | 107,986044 s |
| Effektive Rate in diesem Intervall | 62,4803 Hz | 62,4896 Hz |
| Median der Host-Zeitabstände | 16,000276 ms | 16,000302 ms |
| Größter Host-Zeitabstand | 32,000641 ms | 20,003183 ms |
| Sprünge im akzeptierten Berichtszähler | 0 | 0 |
| Pufferfehler / Rückstellungsfehler | 0 / 0 | 0 / 0 |

Alle Scans gehören pro Lauf derselben Instanz an. Der Zähler erfasst vom
Treiber akzeptierte IMU-Berichte. Lückenfreiheit dort beweist **keine**
Verlustfreiheit auf Funk-/Sensorseite. Host-Monotonzeit ist keine bestätigte
Sensoruhr; die IMU-Rate ist nicht die Gamepad-Pollingrate.

### Begrenzter Achsenbefund

Das Bewegungs-Auswertungsfenster enthält die fünf Sekunden Haltepuffer vor
und nach dem 15-Sekunden-Drehfenster; Aufnehmen und Ablegen sind ausgeschlossen.
Vergleich zur mittleren Vorruhe, ausschließlich in Rohwerten:

| Rohkanal | Vorruhe-Mittel / Standardabweichung | Bewegungs-Mittel minus Vorruhe | Größte positive Abweichung |
| --- | --- | --- | --- |
| G0 | +0,291 / 1,171 | +0,366 | +361,709 |
| G1 | −0,429 / 0,672 | +53,884 | +1.162,429 |
| G2 | −0,138 / 1,660 | −4,704 | +212,138 |

Die stärkste mittlere und positive Reaktion liegt in diesem Versuch auf
**G1**. G0/G2 reagieren ebenfalls; begleitende Handbewegungen sind eine
mögliche, nicht separat gemessene Ursache. Ergebnis: **Kandidat
„waagerecht links → G1 positiv“**, keine endgültige Sensor-/SDL-Achsenzuordnung.
Gegenrichtung, Neigen und weitere getrennte Wiederholungen bleiben offen.
Kein Winkel vorausgesetzt, integriert oder geschätzt; kein Skalierungsprofil
ausgewählt. `0,07 °/s` bleibt ein unbestätigter Kandidat.

### Rückstellung und Belege

Nach beiden Läufen bestätigte eine unabhängige lesende Kontrolle dieselbe
USB-/IIO-Instanz und sämtliche ursprünglichen Einstellungen: Buffer/Stream
aus, alle acht Scan-Elemente aus, Länge 128, Watermark 1, monotonic,
Push-Fehler null. Keine parallelen IIO-Leser und keine neuen passenden
Kernelmeldungen im verglichenen Journalfenster. Ein `final motor stop
failed: -19` beim früheren Ausschalten des **alten** Modulstands war bereits
vor der Installation vorhanden; kein neuer Testfehler oder STOP-Erfolgsbeleg.

Dienst active/running/enabled, Manager gesund/unpausiert, Controller weiterhin
an gs_native. Der Nutzer bestätigte normale Tasten, Sticks und Trigger sowie
einen flüssigen Rechner. Keine erneute Einzelprüfung von Paddles, Motoren,
Spielen oder Suspend/Hotplug. Originale, Dialogzeitmarken, Transaktionen und
Auswertung bleiben privat; Capture-/Frontend-Prüfsummen unabhängig geprüft.

| Beleg | SHA256 |
| --- | --- |
| Ausgeschlossener Lauf, `scans.bin` | `c35aea5c0f2f70aa327305170a66fad94db3ca6b526eddc9d9776b348bf52805` |
| Bestätigter Versuch, `scans.bin` | `5d4c91cdc4f2bdc1967f4c0a8bff3e6ce4f7a2ca5332466bface8ff8ce2bc4a3` |
| Bestätigter Versuch, `observations.jsonl` | `af900a19cd7c8a2b9c2a2fdb1cf3d036d37019362a04d05a650d1c56da913e77` |

**Abnahme:** Kanalauswahl, zusammenhängender Host-Pufferstrom und Rückstellung
in diesen begrenzten Läufen bestanden. Ein qualitativer Linksdrehungsbefund.
Keine allgemeine Stabilitätsgarantie, Gyrokalibrierung oder SDL-Freigabe.
