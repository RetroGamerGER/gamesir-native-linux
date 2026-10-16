# Alpha 0.1.0.alpha2: Rückwegkorrektur und Installationsaudit

Stand: 13. Oktober 2026. Ausschließlich Offline-Entwicklung, lokale Builds und
Prüfung von Dateien. Keine Installation, Modulaktion, USB-Öffnung oder Änderung
einer laufenden Treiberbindung. Das ältere Paket `0.1.0.alpha1` bleibt erhalten.
Dieses Audit dokumentiert den Zustand **vor** der später separat freigegebenen
Erstinstallation; deren Ergebnis steht in [ALPHA_INSTALLATION.md](ALPHA_INSTALLATION.md).

## Auftrag und Betriebsvertrag

`gs_native` ist der normale eigenständige Treiber. Nach erfolgreichem Start
bleibt die native Sitzung ohne Entwickler-Zeitlimit aktiv. Der Manager
verwendet `xpad` nur bei Deaktivierung, Deinstallation oder terminalem Fehler.
Ruhe und kurze Funkpausen sind keine Gründe für einen planmäßigen xpad-Wechsel.
Motorziele werden bei Datenverlust, Suspend und Clientende beendet; eine neue
Verbindung darf alte Vibrationen nicht wieder einschalten. Die kurzen USB-Leases
begrenzen nicht die vom Spiel festgelegte Effektdauer.

Das Erst-Audit von `ffb2d49` fand zwei Blocker:

1. Nach fehlgeschlagenem Bootstrap blieb der Manager auf der alten 100a-Instanz;
   die tatsächlich korrelierte neue 109c-Instanz wurde als fremd behandelt.
   Gleichzeitig sperrte der Kernel END vor erfolgreicher Runtime-Übergabe.
2. Das Startbudget wurde erst nach Übernahme geprüft. `blocked` verhinderte auch
   die Freigabe einer bekannten eigenen Instanz.

Die Korrektur erhält den bestehenden Protokollkern. Neue Gerätezuordnung wird
durch Kernel-Port-/Instanztokens attestiert, nicht aus PID oder Datenbewegung
abgeleitet. Die Berechtigung zum Aufräumen hängt nicht vom Startbudget ab.
Zusätzlich verhindert ein einmaliger privater `claim_100a` im Dauerbetrieb
jede automatische 100a-Bindung außerhalb des budgetgeprüften Managers. Ein
fehlender Autoload-Alias allein würde das bei geladenem Modul nicht erreichen.
Der Claim prüft die genaue referenzierte Instanz und beide sysfs-Inodes; er
hinterlässt keine wiederverwendbare Probe-Erlaubnis. Der historische endliche
Testmodus bleibt erhalten. [Technischer Vertrag](ALPHA_RUNTIME.md).
Das ist kein neuer USB-Moduswechsel und keine neue Linux-Force-Feedback-UAPI.

## Nachweisstufen

Der frühere eigenständige Start mit Gamepad/IMU ist hardwarebestätigt; die
Viermotorwirkung stammt aus eigenen kontrollierten Messungen. Die geänderten
Fehlerpfade, Dauerbetrieb, Dienstneustarts, Hotplug-/PM-Automatik und Paketierung
werden in diesem Auftrag ausschließlich offline geprüft. Ein erfolgreicher
Offline-Test ist kein neuer Hardwarebeleg.

Die geprüften Änderungen umfassen den echten Kerneladapter, den C-Kontrollclient,
den Manager und den Paketentfernungsschutz. Regressionen prüfen insbesondere
fehlgeschlagene Initialisierung nach bereits erfolgter Übernahme, einen zwischen
Scan und Clientabschluss eintreffenden Nachweis, Geräteersatz, Dienstneustart,
Budgetblockade, einmaligen END und fehlgeschlagene tatsächliche Rückkehr.

Ergebnisse:

- `make test`: vollständig bestanden; darunter 88 Kerneladapter-Szenarien,
  42 zusätzliche Claim-Szenarien, Manager-/Client-/Haptikfälle sowie
  24 Paket-/Entfernungsfälle. C-Fehlerpfade werden mit ASan/UBSan geprüft.
- Kernelbau für `7.2.9-2-garuda`: erfolgreich, keine Warnungen,
  `MODULE_VERSION=0.1.0.alpha2`, keine USB-Autoload-Aliase.
- Checkpatch und Clang Static Analyzer: keine gemeldeten Fehler/Warnungen
  beziehungsweise Diagnosen in allen fünf Übersetzungseinheiten.
- Gespeicherter Capture: 12.204 IMU-, 1.458 XInput- und 3.786 GIP-Berichte
  weiter erfolgreich geprüft. Gyro bleibt roh, Beschleunigung experimentell.
- Gerätefreie SDL-Prüfung: acht Zusatztastenfälle und zwölf Sensorfälle
  weiterhin erfolgreich. Keine physische Einzelbeschriftung dadurch bewiesen.
- Arch-Quellarchiv und Binärpaket: enge Dateiliste, Inhalte/Rechte/Prüfsummen,
  Quellenübereinstimmung und fehlende automatische Aktivierung geprüft.
  Auch die tatsächlich im Paket enthaltenen DKMS-Quellen werden separat gegen
  die vorhandenen Header gebaut; das ist kein Aufruf einer Systeminstallation.

Die vollständigen lokalen Prüflogs, der abschließende Paketvergleich,
Commitzuordnung und SHA256-Prüfsummen liegen im Release-Ergebnis unter `build/`.
Diese Dokumentation enthält bewusst nicht den Hash ihres eigenen Archivs.

## Tatsächliche Installationsfolgen auf dem geprüften Garuda-System

Der ausschließlich lesende Host-Audit ergab Kernel und Header
`7.2.9-2-garuda`, vorhandene Pflichtabhängigkeiten und keine bestehende
GameSir-Alpha-Installation. Diese Momentaufnahme ersetzt keine frische
Vorprüfung vor einer später freigegebenen Installation. Während der vorliegenden
Korrektur werden keine Geräte geöffnet oder Hardwarezustände verändert.

Das Paket liefert DKMS-Quellen, Kontrollclient, Manager, Viermotor-Broker,
SDL-Mappinggenerator, systemd-Unit, Sysusers-Gruppe und Entfernungsschutz.
Es liefert keine Firmware, USB-Autoload-Aliase, udev-Regeln, xpad-Blacklist
oder `.INSTALL`-Datei. Alle Zielpfade liegen unter `/usr`; Zustands-/Socketpfade
werden erst vom aktivierten Dienst angelegt. Kein Benutzergruppenbeitritt.

Eine reine Erstinstallation würde dennoch Host-Hooks auslösen:

| Reihenfolge | Wirkung |
|---|---|
| Vor Transaktion | Snapshot-Betrieb prüfen, Snapper-Vorher-Snapshot nach lokaler Konfiguration |
| Paketinstallation | Paketdateien installieren |
| Sysusers/systemd | Gruppe `gamesir-native-haptics` anlegen, Unit-Dateien einlesen, `/usr`-Zeitstempel aktualisieren |
| DKMS | Modul bauen/installieren und Modulabhängigkeiten aktualisieren |
| Garuda-Dracut | Kernelabbild und normale/Fallback-Initramfs aller paketverwalteten Kernel neu schreiben |
| Abschluss | Paket-/Pacnew-Hinweise, Nachher-Snapshot, `sync`, Garuda-Update-Markierungen |

Die Bootdateien sind aktuell `/boot/vmlinuz-linux-garuda`,
`/boot/initramfs-linux-garuda.img` und
`/boot/initramfs-linux-garuda-fallback.img`. Grund:
`/etc/pacman.d/hooks/90-dracut-install.hook` reagiert auf `usr/src/*/dkms.conf`;
`/usr/share/libalpm/scripts/dracut-install-garuda` setzt dadurch `all=true`.
Der zusätzliche mkinitcpio-Hook baut hier wegen Dracut nicht noch einmal.

Die vorhandene DKMS-Konfiguration aktiviert kein `modprobe_on_install`.
Kein zutreffender Installationshook aktiviert oder startet GameSir. Folglich
werden bei der reinen Installation kein GameSir-Modul geladen, kein Interface
übernommen und keine neuen udev-Regeln aktiviert. Das systemweite Einlesen von
Units ist kein Dienststart. Andere Xbox-Controller werden nicht gezielt verändert.

Der vorhandene DKMS-ALPM-Wrapper kann trotz gemeldeter Buildfehler 0 zurückgeben.
Pacman-Erfolg ist deshalb kein Modulbau-Nachweis. PostTransaction-Fehler nehmen
installierte Dateien oder überschriebene Bootdateien nicht automatisch zurück.
Snapper ist kein nachgewiesener vollständiger Ersatz für eine Bootdateisicherung.
Auch Paketentfernung löst den Dracut-Neubau erneut aus.

## Rückbau und Grenzen

Die genaue Anleitung einschließlich der gesondert freizugebenden Befehle steht
in [ALPHA_INSTALLATION.md](ALPHA_INSTALLATION.md). Grundregeln:

- Automatik sperren; nur nachgewiesen eigene Instanzen neutralisieren.
- END ist weder eine Bestätigung mechanischen Motorstillstands noch ein
  USB-Identitätswechsel. 109c an xpad zu binden macht daraus kein 100a.
- Freigabeerfolg benötigt bestätigtes 100a/xpad oder bestätigte physische
  Abwesenheit aller verwalteten Geräte. Abwesenheit bestätigt keine Spielfunktion.
- Ein noch ungeklärter Rückweg bleibt sichtbar und verhindert Deinstallation.
- Kein erzwungenes Entladen, keine unkontrollierte Wiederholung, keine geratenen
  Reset- oder Firmwarebefehle. Wenn der Dongle nach END 109c bleibt, ist der
  manuelle Ablauf eine eigene Freigabe; seine Hardwarewirkung ist noch offen.

Persistenter Zustand, Gruppe/Mitgliedschaften, Journal, Snapshots und Garuda-
Markierungen können nach einer Paketentfernung bleiben. Die Deinstallation
behauptet keine bitgenaue Rücknahme sämtlicher Host-Hook-Änderungen.

## Go-/No-Go-Entscheidung

**Technisches Go für eine kontrollierte Erstinstallation der Alpha2, mit
zunächst deaktiviertem Dienst und nach gesonderter Nutzerfreigabe.** Beide
ursprünglichen Audit-Blocker sind im Code und in Offline-Regressionen korrigiert.
Das Paket und der daraus gebaute Kerneladapter sind prüfbar. Die oben genannten
Bootdatei- und Systemhookwirkungen gehören ausdrücklich zur späteren Freigabe.
Nach Installation tatsächliches DKMS-Ergebnis und Modulversion prüfen; erst
anschließend die Aktivierung und einen begrenzten Integrationstest freigeben.

**Noch kein Go für unbeaufsichtigten Produktionsbetrieb.** Reale Hotplug-,
Funkverlust-/Wiedereinschalt-, Suspend/Resume- und Fehler-Rückwegtests der neuen
Automatik fehlen. Die anfängliche xpad-Abbindung und die 100a-Rückgabe besitzen
weiterhin das dokumentierte sysfs-Race-Fenster; der neue native Claim selbst
ist an das referenzierte Objekt gebunden. Ein verbleibendes 109c kann einen
bewusst auszuführenden physischen Rückweg erfordern. Kein Softwareerfolg wird
anstelle dieses noch offenen Hardwarebelegs behauptet.

Die Nutzlast enthält keine Rohmitschnitte, fremden Firmwaredateien oder
Zugangsdaten. Das von makepkg erzeugte `.BUILDINFO` enthält jedoch den lokalen
Buildpfad und den Paketbestand des Buildhosts: vor einer öffentlichen Verteilung
separat prüfen. Der Client ist PIE mit nicht ausführbarem Stack und Partial
RELRO; vollständige Übernahme aller distroüblichen Hardening-Flags bleibt eine
Paketverbesserung und wurde hier nicht als vorhandene Eigenschaft behauptet.
