> Public export: personal tester, host and path references were anonymized. Historical evidence hashes refer to the private originals.

# Rechnerstillstand am 14. Oktober 2026

**Nachtrag zum zweiten Freeze:** Gegen 16:27 MESZ fror der Rechner nach
Funk-Wiederverbindung erneut ein; der Dongle blieb eingesteckt, Reset nötig.
Die gezielte Folgeprüfung fand einen konkreten kritischen Fehler in
`gs_native`: der FF-Core gibt den als private Daten übergebenen, anderweitig
referenzgezählten Gerätespeicher frei. Damit ist die frühere statische
Prüfung unten unvollständig. Automatik wurde danach ausdrücklich freigegeben
pausiert. [Nachweis, Korrektur und Installationsstand](FF_LIFETIME_FIX.md).
Die Zuordnung jedes einzelnen beobachteten Freezes bleibt ohne Dump offen.

Der folgende Bericht erhält den damaligen Stand des **ersten** Absturzes.
[tester] gab später die Steam-Fortsetzung mit zurückgestellter GPU ausdrücklich
frei; [temporärer Paddle-Erfolg und Persistenzlücke](STEAM_ELITE_PADDLES.md).

## Ergebnis und Teststatus

[tester] meldet einen vollständig eingefrorenen Rechner mit erforderlichem
Neustart. Das Journal bestätigt beschädigte Kernel-Speicherstrukturen im
DRM/TTM-Grafikpfad, mehrere Oops und anschließend einen Soft-Lockup.
**Der ursprüngliche Verursacher ist nicht bestimmt.** GPU-Undervolting ist
eine konkrete mögliche Einflussgröße; weder AMDGPU noch `gs_native` sind
als Ursache abschließend belegt oder ausgeschlossen.

Der freigegebene Steam-Paddle-/Anzeigenamentest wurde bereits bei der
Vorprüfung angehalten: unerwartet `109c/xpad` statt nativer Bindung.
Das vorbereitete Mapping und die Namensänderung wurden nicht angewendet.
Der Test bleibt nach dem Freeze pausiert. Keine Wiederholung oder
Systemreparatur wurde ausgeführt.

## Gesicherte Zeitfolge

Alle Uhrzeiten am 14. Oktober 2026, **MESZ = UTC + 2 Stunden**.
Zeitstempel bezeichnen den Journalbefund, nicht zwingend den Zeitpunkt des
ursprünglichen Schreibfehlers oder den Beginn des sichtbaren Einfrierens.

| MESZ | Befund im vorherigen Boot |
|---|---|
| 15:27:49–50 | Dongle trennt sich, neue 109c-Instanz; spätere Vorprüfung sieht xpad |
| 15:36:55 | Weitere USB-Trennung |
| 15:36:56,913 | Neue 100a-Instanz wird durch `gs_native` gebunden |
| 15:36:58,360 | Erste `list_del corruption`, Prozess `kwin_wayland`, DRM/TTM-Abbaupfad |
| 15:37:00,901 | Zwei NULL-Zugriffe in `ww_mutex_lock_interruptible`, Xwayland und Steam-Webhelper, AMDGPU-Aufrufketten |
| 15:37:03–04 | Neue 109c-Instanz, native Bindung, Bootstrap-Ergebnis 0 und Manager-`ready` |
| 15:37:17,842 | Erneute Listenkorruption und General-Protection-Fault beim Grafikobjekt-Abbau; Kernel verlangt Neustart |
| 15:37:19 | USB-Trennung, abschließender Motor-STOP schlägt mit `-19` fehl |
| 15:37:42,535 | Watchdog meldet CPU 0 seit 26 Sekunden blockiert; Worker-Stack nicht mehr gespeichert |
| 15:38:13 | Nächster Boot beginnt |

Die erste Warnung liegt nur rund 1,447 Sekunden nach der nativen
100a-Bindung. Diese zeitliche Nähe rechtfertigt die Prüfung unseres
Lebenszyklus, beweist aber keine Verursachung. Das spätere `ready` widerlegt
den schon eingetretenen Kernelfehler nicht. Der Motor-STOP-Fehler nach der
Trennung erklärt die vorherige Speicherbeschädigung ebenfalls nicht.

## Was die Fehlerketten aussagen

Erster gespeicherter Pfad:
`rm_hole → drm_mm_remove_node → drm_vma_offset_remove → ttm_bo_put →
drm_gem_dmabuf_release`. Spätere Fehler betreffen `amdgpu_gem_va_ioctl`,
`amdgpu_cs_parser_bos` und `amdgpu_drm_release`.
Keine `gs_native`-Funktion erscheint in diesen Aufrufketten.
Die Liste geladener Module ist kein Verursachernachweis.

Derselbe beschädigte Slab-Knoten erscheint bei beiden Listenwarnungen.
Später enthalten erwartete Zeigerfelder als Little-Endian-Text lesbare
Fragmente `:00.0/us` und `VER=usb\0`. Das ist mit wiederverwendetem Speicher
beziehungsweise einem Use-after-free vereinbar. Es identifiziert weder den
ursprünglichen Allokator noch den fehlerhaften Freigabe-/Schreibpfad.
Ein USB-Textfragment allein beweist keinen GameSir-Fehler.

Auch am 13. Oktober sind zwei Grafikpfad-Oops nachweisbar: 19:08:04 und
19:32:24 MESZ, `dma_resv_iter_first_unlocked` über `amdgpu_vm_sdma_update`.
Es gab damit bereits vor dem neuen Paddle-Vorschlag schwerwiegende Fehler;
derselbe Ursprung ist dadurch noch nicht nachgewiesen.

Im gesicherten vorherigen Boot keine Meldung über einen tatsächlichen
Machine-Check-/EDAC-Speicherfehler, OOM-Kill oder GPU-Ring-Timeout gefunden.
Das schließt Hardwareinstabilität oder einen Treiberfehler nicht aus.
Die MCE-/EDAC-Initialisierungsmeldungen sind keine gemeldeten Speicherfehler.

## GPU-Einstellungen und Nutzer-Rückstellung

[tester] bestätigt aktives **LACT-Undervolting mit −120 mV**. Die erste
lesende Konfigurationsprüfung fand `voltage_offset: -120` und
`power_cap: 374.0`. LACT 0.10.1-1 war aktiv und meldete in diesem Boot
das erneute Anwenden seiner Konfiguration. Das ist keine Spannungsmessung
zum exakten Absturzzeitpunkt.

Der Kernel meldete bereits beim Boot aktiviertes Overdrive. Dieser Hinweis
allein sagt nicht, welcher Offset angewendet wurde. Ebenso beweist der
Taint-Name `CPU_OUT_OF_SPEC` keinen CPU-Defekt oder CPU-Undervolting;
Taint-Bits beschreiben Diagnosebedingungen, nicht die Fehlerursache.
[Kernel-Dokumentation zu Taint](https://docs.kernel.org/admin-guide/tainted-kernels.html).

**Während der Untersuchung stellte [tester] selbst auf GPU-Standardwerte
zurück.** LACT protokolliert Konfigurationsspeicherungen um 15:45:27 und
15:45:33. Die anschließende Datei enthält keinen `voltage_offset` mehr,
`power_cap: 340.0`, `performance_level: auto`, keine automatische
Profilumschaltung. Aktuelle Spannung/Taktraten wurden nicht an der Hardware
ausgelesen; die Aussage „Standardwerte“ stammt vom Nutzer und wird durch
die geänderte gespeicherte Konfiguration gestützt.

Damit änderten sich mindestens Offset und Leistungsgrenze. Ein später
fehlerfreier Vergleich würde zunächst die gesamte Rückstellung stützen,
nicht isoliert −120 mV als Ursache beweisen. AMD empfiehlt Standardwerte
als Grundlage für die Stabilitätssuche; ein Spannungs-Offset verändert die
Zielspannung gegenüber der Takt-/Spannungskurve.
[AMD-Stabilitätshinweise](https://www.amd.com/en/resources/support-articles/faqs/TS-TIPS.html),
[AMDGPU-Spannungsschnittstelle](https://docs.kernel.org/gpu/amdgpu/thermal.html#pp-od-clk-voltage).

## Begrenzte statische Prüfung unseres Treibers

Unabhängiges Offline-Review des unveränderten `kernel/gs_native_usb.c`:
Referenzzählung von Gerät/Interface/Kontroll-FDs, Bootstrap-Liste und
Sperren, URB-/Worker-Abbau vor Input-/IIO-Freigabe, Reportlängen,
IOCTL-Kopiergrößen und FF-Callback geprüft. **Kein konkreter Fehler
gefunden, der diesen Absturz erklärt; kein Ausschluss durch Codelektüre.**

Arbeitsquelle und installierte DKMS-Quelle sind SHA256-identisch:
`a33f55a4652d06e0bfaf30a53e22e66c9e1c43b843eec12975b8f647eadb60a6`.
Paketprüfung: 77 Dateien, keine veränderte Datei. Kein spekulativer
Kernelpatch, kein Neubau oder Lasttest während dieser Diagnose.

## Zustand nach Neustart und Beweisgrenzen

Kernel `7.2.9-2-garuda`, Paket `gamesir-native-dkms 0.1.0.alpha2-2`;
Mesa/Vulkan-Radeon `1:26.2.4-1`, Firmwarepaket `20260916-1`.
Der bereits aktivierte Dienst startete beim Reboot selbstständig und
meldete um 15:38:55 native Bereitschaft. Lesende Nachkontrolle:
`active/running`, `enabled`, keine Dienstneustarts; `3537:109c`, IF0
`gs_native`, IF1 ungebunden. Das ist kein neuer Eingabe- oder Langzeitbeleg.

Im aktuellen Kerneljournal bis **15:46:35 MESZ** keine neuen Oops,
Listenkorruptionen oder Lockups gefunden. Seit der letzten
LACT-Speicherung waren erst rund 62 Sekunden vergangen: kein belastbarer
Stabilitätsnachweis. Keine Userspace-Coredumps im untersuchten Absturzfenster.
`/sys/fs/pstore` ist unprivilegiert nicht lesbar; archivierter
systemd-pstore-Ordner leer. Kein Kernel-Speicherabbild verfügbar.

## Nächster Schritt, noch nicht ausgeführt

Zunächst einen separat vereinbarten Vergleich mit den jetzt zurückgestellten
GPU-Einstellungen und unverändertem GameSir-/Steam-Stand beobachten.
Kein neues Paddle-Mapping, kein absichtliches Wiederherstellen des
Undervoltings und kein Absturz-/Stresstest gleichzeitig. Erst danach den
Paddle-Test erneut bewerten. Bei einem erneuten Oops keine Testserie
fortsetzen; neue Logs sichern und den kontrollierten Rückweg abstimmen.

Bei Wiederholung trotz Standardwerten gezielt Grafikobjekt-Lebensdauer und
Kernel-/Treiberinteraktion untersuchen. Ein Vergleich ohne `gs_native`
oder instrumentierter Kernel könnte Ursachen trennen, erfordert aber
separaten Plan und Freigabe. Keine solche Änderung hier durchgeführt.

## Lokale Belege

Private Originaljournale, Paket-/Dienstmetadaten, LACT-Nachherdateien und
SHA256-Prüfsummen liegen unter
`.local/integration/20261014T134302Z-system-freeze-readonly/`.
Die erste −120-mV-Konfiguration wurde vor der Nutzeränderung gelesen;
die später gesicherte Datei `lact-config.yaml` enthält bereits die
Rückstellung und darf nicht als Vorher-Datei ausgegeben werden.
Die Werte der ersten Lesung sind separat als Beobachtung dokumentiert.

Verzeichnis 0700, Dateien 0600; keine Rohjournale, Geräte-UIDs oder
Maschinenkonfigurationen in Git. Alles ohne erhöhte Rechte gelesen.
Durch den Agenten keine Geräte geöffnet, Dienste/Module/Bindungen oder
GPU-Einstellungen geändert. Die unabhängigen Reviews verwendeten nur
gespeicherte Logs, Quellen und vorhandene Moduldateien.

Validierung der Dokumentationsänderung: 43 private Belegdateien per SHA256
verifiziert, 24 vorhandene Offline-Paketierungs-/Rückbautests bestanden.
Dabei werden Rückbauaktionen simuliert; kein Dienst- oder Modulaufruf
am laufenden System. Nur der Bericht wurde der Paket-Dokumentliste ergänzt,
kein aktualisiertes Paket installiert.
