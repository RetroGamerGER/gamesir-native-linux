# IIO-Kanalauswahl: Offline-Korrektur und nächster Einzellauf

Stand: 18. Oktober 2026. **PRE-ALPHA, offline korrigiert und gebaut; nicht
installiert oder an Hardware getestet.** Die bekannte Winkelkalibrierung
bleibt pausiert. Der nächste Test dient nur der qualitativen Achsenzuordnung.

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
Linux-Sysfs, FIFO, Demultiplexer und IRQ-Konkurrenz nicht aus. Reales
Pufferlesen, Timing, Rückstellung und gleichzeitige Spielfunktion benötigen
weiterhin eine separat freigegebene Hardwareabnahme.

## Vorbereiteter nächster Lauf – noch nicht freigegeben

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
