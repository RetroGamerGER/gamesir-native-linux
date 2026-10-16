> Public export: personal tester, host and path references were anonymized. Historical evidence hashes refer to the private originals.

# Kritischer FF-Lebensdauerfehler nach Wiederverbindung

Stand: 14. Oktober 2026. Revision `0.1.0.alpha2-2` enthielt einen bestätigten
Use-after-free-/Double-free-Fehler im Geräteabbau. Die Korrektur wurde als
Paketrevision `0.1.0.alpha2-3` nach bestandenen Offline-Tests und Nutzerfreigabe
installiert. Anschließend nach zusätzlicher Freigabe aktiviert: normale
Eingaben und ein vollständiger Funk-Aus-/Einschaltzyklus mit automatischem
erneutem Bootstrap bestanden. Der korrigierte Treiber bleibt aktiv/enabled.
Das Paketupdate selbst erhielt die Pause; die Aktivierung erfolgte erst nach
erfolgreicher Nachkontrolle und einem frischen 100a/xpad-Ausgangszustand.

## Erneuter Rechnerstillstand und gesicherter Zustand

[tester] bestätigt einen vollständigen Freeze nach Einschalten/Wiederverbinden
des Funkcontrollers. Der USB-Dongle blieb eingesteckt. Der Rechner wurde mit
der Reset-Taste neu gestartet. GPU-Undervolting war zuvor vom Nutzer
zurückgenommen worden; gespeicherte Einstellungen siehe
[erster Diagnosebericht](SYSTEM_FREEZE_20261014.md).

Uhrzeiten am 14. Oktober, MESZ:

| Zeit | Gesicherter Befund |
|---|---|
| 16:27:22,277 | Native 109c-Instanz trennt sich; abschließender Motor-STOP danach `-19`/ENODEV |
| 16:27:23,657 | Neue 109c-Instanz zunächst bei xpad |
| 16:27:28,736 | Erneute USB-Trennung |
| 16:27:30,340–580 | 100a, xpad-Abbau mit `-2`, anschließend native Bindung |
| 16:27:35,848 | USB-Trennung während Bootstrap |
| 16:27:37,451–880 | Neue 109c-Instanz, native Bindung, Bootstrap-Ergebnis 0 |
| 16:27:38,052 | Manager meldet `ready`; letzter gespeicherter Managerbefund |
| 16:29:03 | Neuer Boot nach Reset |
| 16:36:04 | Gesondert freigegebene Verwaltungspause bestätigt |

Das zweite Kerneljournal enthält keinen Oops-/Lockup-/OOM-/GPU-Reset-Stack;
seine letzte Zeile ist der erfolgreiche Bootstrap. Das ist kein Nachweis
unbeschädigten Speichers. Beim Reset können letzte Meldungen verloren gehen.
Der konkrete Codefehler unten ist unabhängig davon bewiesen; ohne Dump ist
nicht bewiesen, dass er jeden bisherigen Freeze verursacht hat.

Weitere Auffälligkeit: vor der Wiederverbindung 1.634 sichtbare Userspace-
Bus-Lock-Meldungen, überwiegend `CHTTPClientThre`, und 2.861.424 unterdrückte
`handle_bus_lock`-Meldungs-Callbacks. Starkes Aufkommen bereits 16:10–16:24,
letzte Einzelmeldung 16:26:17, auch ohne Mapping-Hinweis. Das ist keine
vollständige CPU-Auslastungsmessung und kein Beweis der Absturzursache.
Solche Bus-Locks können andere CPUs ausbremsen; sie sind selbst kein Kernel-
Speicherfehler. [Kernel-Dokumentation](https://docs.kernel.org/arch/x86/buslock.html).

Nach Reset war der Dienst active/enabled, der Manager unpausiert, aber ohne
Geräte/Besitznachweise. Der Dongle lag unter `109c/xpad`, keine native Bindung.
Nach erneuter Prüfung genau dieses Zustands erlaubte [tester] einmalig
`gamesir-native release`. Ergebnis: `paused=true`, leere Geräte/Leases,
unveränderte USB-Instanz und xpad-Bindung. Kein Modul entladen und keine
Geräteoperation durch den pausierten Manager. Dessen `returned=true` betrifft
nur verwaltete Instanzen; **kein Beleg für einen Rückweg zu 100a oder normale
Spielfunktion**. Die Pause muss beim Update erhalten bleiben.

## Bestätigter Fehler und Besitzvertrag

Der bisherige Adapter registriert:

```c
input_ff_create_memless(g->input, g, gsn_play_effect);
```

`g` ist das gesamte `struct gsn_device`. Seine Lebensdauer wird durch `kref`
für Bindung, Bootstrap und offene Kontroll-FDs verwaltet. Der memless-FF-Core
übernimmt dagegen den übergebenen privaten Zeiger und führt beim Zerstören
`kfree(ml->private)` aus. Damit wird `g` außerhalb seiner Referenzzählung
freigegeben. `gsn_disconnect()` verwendet es danach weiter und gibt seine
Bindungsreferenz ab; `gsn_delete()` kann denselben Speicher nochmals freigeben.
Offene Kontroll-FDs können ebenfalls auf den freigegebenen Speicher zugreifen.
Bei verzögerter Input-Freigabe verschiebt sich der doppelte Freigabezeitpunkt.
**Ein abgespielter Vibrationseffekt ist dafür nicht erforderlich.**

Der Vertrag wurde am tatsächlich installierten Kernel `7.2.9-2-garuda`
bestätigt: vorhandenes `ff-memless.ko.zst` in anonymen Arbeitsspeicher
dekomprimiert und statisch disassembliert, nicht geladen. `ml_ff_destroy`
beendet den Timer synchron und gibt anschließend `ml->private` frei.
Das vorhandene `vmlinux` bestätigt `input_dev_release → input_ff_destroy`
und vorher `__input_unregister_device → ff->stop → timer_shutdown_sync`.

SHA256 des komprimierten Moduls:
`b983b0b090b954e946ba2a9aba518a175a4551155b19cf8e89a37aea9eb16d5b`.
SHA256 des dekomprimierten ELF:
`60159ff13e06285ffd950b8cfdd3ee9810b33d089687c7f544df096077e5baa8`.
Die erste statische Prüfung übersah diesen fremden Besitzvertrag. Ihr damaliger
Negativbefund wird nicht als Entlastung fortgeschrieben.

## Minimale Korrektur

Nach Input-Allokation `input_set_drvdata(g->input, g)` setzen; dem FF-Core
`NULL` als private Daten übergeben; der Callback verwendet
`input_get_drvdata(input)`. Der Pointer bleibt geliehen; nur `gsn_delete()`
gibt das Geräteobjekt nach der letzten kref frei. Die bestehende Reihenfolge
„stopping setzen → URB/Worker beenden → Input abmelden → Bindungsreferenz
abgeben“ bleibt bestehen. Das synchron beendete FF-Timer-/Callback-Leben darf
die Bindungsreferenz nicht überdauern.

## Offline-Abnahme und geplante Installation

Die neue Regression extrahiert tatsächliche Adapterfunktionen und prüft sie
unter ASan/UBSan mit künstlichem Input-/FF-Core. Elf Fälle bestehen:
sofortige/verzögerte Input-Freigabe, offene Kontroll-FDs und beide
Freigabereihenfolgen, Playback, Input-/FF-Allokationsfehler,
Input-Registrierungsfehler nach FF-Erfolg sowie 100a ohne FF.
Vier Negativkontrollen stellen ausschließlich im generierten Test-Header
die alten Besitzzeilen wieder her: dreimal Use-after-free, einmal Double-free
werden erwartungsgemäß erkannt. Bestehende Startup-Tests simulierten den
Input-/FF-Besitzvertrag nicht; der neue Test schließt gezielt diese Lücke.

`make test` besteht vollständig, einschließlich 88 Startup-/Runtime-
Adapterfällen und der neuen Lifetime-Regression. `make kernel-analyze`
baut gegen `7.2.9-2-garuda` mit LLVM/W=1/Werror ohne Warnungen; Checkpatch und
Clang-Analyse aller fünf Übersetzungseinheiten bestehen ohne Diagnose.
Keine USB-Autoload-Aliase. Lokales Modul-SHA256:
`abb412f5ef5bdac44335f987a2e4a94b04db5449d621eb56e8efc4ea44e8172a`.
Testlogs unter `build/ff-lifetime-*.log` und `build/results/kernel-ff-lifetime*`.
Das prüft den konkreten Besitzfehler, nicht allgemeine Race-Freiheit oder
reale Hotplug-/Freeze-Stabilität. Ein Realtest bleibt erforderlich.

Paketrevision 3 verändert keine Steam-Konfiguration und aktiviert keine neue
Sitzung. Der vorhandene PreTransaction-Hook verifiziert die leere Rückgabe,
stoppt den pausierten Dienst und entlädt nur das ungebundene, unbenutzte native
Modul. DKMS und die vorhandenen Garuda-Hooks gehören zum Paketupdate; ihre
konkrete Transaktion ist unmittelbar vorher erneut zu prüfen. Keine
zusätzlichen Pakete, Datenbankaktualisierungen oder automatische Reparaturen.

Nach dem Update: Paket-/DKMS-/Modulquellstand, neuer Build, erhaltene Pause,
inaktiver Dienst, fehlende native Bindung und unveränderte USB-Identität prüfen.
Dienststart/Resume/Verbindungstest folgen erst als gesondert angekündigter
Schritt der inzwischen zusätzlich beauftragten Realprüfung. Eine unverwaltete
109c-Instanz wird nicht auf Verdacht übernommen; gegebenenfalls zuerst den
bekannten manuellen Rückweg zu frischem 100a/xpad verwenden.

## Abgeschlossene Installation

Quellencommit `1f91ccb7d00916ed65d717268d79005d157da469`.
Paket-SHA256 `a717644cd7c9d4fdacdc42e1d5246f1e73af3605ceb38d038b3f817cc0073de1`;
Quellarchiv-SHA256 `958a4ce3f679809afb24869f063fe26f9b33a63c663cd166d5b8f8ccc135f709`.
64 Quelldateien bytegenau mit Commit verglichen, Quellarchiv reproduziert;
61 Nutzdateien und drei Metadatendateien geprüft. Nur Kerneladapter als
Laufzeitquelle verändert; Client, Manager, Unit und Hooks unverändert.
Extrahierter Client-Selbsttest und separater Modulbau aus den tatsächlichen
Paketquellen bestanden. Kein fertiges Modul, Mitschnitt oder Steam-Zusatz im Paket.

Die vollständig geprüfte Pacman-Transaktion enthielt ausschließlich Revision
2→3. Vorhandener Upgradehook stoppte den pausierten Dienst und entlud das
ungebundene alte Modul. DKMS baute/installierte neu; Garuda erneuerte normale
und Fallback-Initramfs, Snapper erzeugte 69/70. Exit 0. Bekannter Hinweis
`Deprecated feature: CLEAN`; keine neue Konfigurationsänderung daraus abgeleitet.

Nachkontrolle **14:51:04 UTC / 16:51:04 MESZ**:

- Paket `0.1.0.alpha2-3`, 80 Einträge, 0 verändert.
- DKMS für `7.2.9-2-garuda` installiert, tatsächliches Baulog ohne Warnung/Fehler.
- Modulversion weiterhin `0.1.0.alpha2`; neue `srcversion F75F36980BCE065ED853910`,
  passendes vermagic, keine Autoload-Aliase; installierte Quelle entspricht dem Fix.
- Dienst inactive/dead, enabled; gs_native ungeladen, keine native Bindung.
- Pause und leere Leases erhalten; dieselbe unverwaltete 109c/xpad-Instanz.
- Keine neuen kritischen Kernelmeldungen im Updatefenster.

Installation erfolgreich; das ist noch kein realer Wiederverbindungstest.
Die anschließende Aktivierung ist beauftragt und wird getrennt dokumentiert.

## Kontrollierte Aktivierung und abgeschlossene Realprüfung

[tester] entfernte den Dongle nach Ansage, wartete fünf Sekunden, steckte ihn
am selben Port wieder ein und verband den Funkcontroller. Lesende Prüfung
um 14:52:32 UTC: frische 100a/xpad-Instanz, IF1 usbhid, keine fremden
USB-/Kontrollhandles, Dienst noch inaktiv und Pause erhalten. Kein
automatischer Übernahmeversuch der vorherigen unverwalteten 109c-Instanz.

Einmaliger Dienststart um 14:53:07 UTC lud den korrigierten Build. Die direkt
anschließende Statusabfrage traf vor Bereitstellung des Unix-Sockets ein und
lieferte ENOENT; deshalb zunächst keine Übernahme. Erneute reine Lesekontrolle
um 14:53:49 bestätigte laufenden Dienst ohne Neustart, Pause/leere Leases und
unveränderte xpad-Bindung. Dies war eine zu frühe Beobachtungsabfrage,
kein erneuter Start- oder Reparaturversuch.

Nach frischer Instanz-/Besitzprüfung genau ein `resume`. Ohne Deadband
erfolgreicher Bootstrap 100a→109c; um 14:56:00 UTC Manager active ohne Fehler.
Die bekannte xpad-Abbaumeldung `-2` erschien, kein nativer Bootstrapfehler.
Der erste Eingabetest erhielt ein 120-Sekunden-Fenster ohne vorausgesetzte
präzise Reaktionszeit. `evtest` öffnete ausschließlich das vorher anhand von
sysfs/name/Bindung geprüfte GameSir-Inputgerät, ohne Grab oder FF-Upload.
Ergebnis: 33.066 Ereignisse, 132 vollständige Druck-/Loslasspaare. 14 der 15
Zielcodes tatsächlich betätigt, zusätzlich KEY_RECORD; Guide zunächst nicht.
Alle vier Zusatzcodes 704–707 mit unabhängigen Druck-/Loslassereignissen;
beide Sticks erreichen auf beiden Achsen −32768..32767, beide Trigger 0..1023,
beide D-Pad-Achsen −1..1. Letzte Stickwerte 0/−1, aber kein ausgewiesener
Ruhe-/Langzeitdrifttest. [tester] bestätigt normale KDE-Eingaben/flüssiges System.

### Ein kontrollierter Funk-Wiederverbindungszyklus

Der Dongle blieb eingesteckt. [tester] bestätigte zunächst den ausgeschalteten
Funkcontroller und schaltete ihn erst nach Ansage wieder ein. Kein zweiter
`resume`, kein Dienstneustart, kein Deadband, kein manueller Treiberwechsel.

| Zeit UTC | Beobachtung |
|---|---|
| 15:00:19,691 | Native 109c-Instanz getrennt; FF/Input-Abbau ohne Speicherwarnung |
| 15:00:19,691 | Abschließender STOP nach USB-Trennung: `-19`/ENODEV, kein Retry |
| 15:00:21,082 | Dongle während ausgeschaltetem Funkcontroller als neue unverwaltete 109c/xpad-Instanz |
| 15:01:13,427 | Nach Einschaltansage erneute Neuanmeldung |
| 15:01:15,032 | Frische 100a-Instanz, automatisch gezielt durch Manager übernommen |
| 15:01:22,135 | Neue 109c-Instanz an gs_native |
| 15:01:22,502 | Bootstrap erfolgreich, anschließend Manager active |

Ein einzelner Status während der Entfernung meldete `gone` und einen
Konvertierungsfehler wegen eines bereits leeren sysfs-Werts; die folgende
Probe enthielt eine leere Geräteliste, keine `blocked`-/`failed`-Quarantäne.
Dieser transiente Befund wird erhalten, nicht als neuer behobener Managerfehler
ausgegeben. Die unverwaltete 109c-Instanz im ausgeschalteten Zustand wurde
nicht beansprucht. Neue Starts im gespeicherten Budget: genau initiale
Aktivierung und Wiederverbindung, keine Wiederholungsschleife.

Der getrennte 90-Sekunden-Nachtest prüfte das neu enumerierte GameSir-Inputgerät.
11.247 Ereignisse mit 88 vollständigen Druck-/Loslasspaaren erfasst.
Alle 15 Ziel-Tastencodes einschließlich Guide und 704–707 wurden tatsächlich
gedrückt/losgelassen. Auch nach Wiederverbindung volle Stick-/Triggerbereiche
und beide D-Pad-Richtungen; alle beobachteten Tasten enden losgelassen.
[tester] bestätigt anschließend normale Eingaben und alle vier
Zusatztasten ohne Freeze oder Aussetzer. Beide zeitbegrenzten Leser endeten
wie geplant mit Timeoutcode 124; kein Gerätefehler daraus abgeleitet.

Abschlusskontrolle **15:04:07 UTC / 17:04:07 MESZ**: Dienst active/running/enabled,
NRestarts 0, korrigierter srcversion, drei Dauerbetriebsparameter aktiv,
Manager active ohne Konflikt, Pause aufgehoben, Besitznachweis der neuen
109c-Instanz. IF0 gs_native, IF1 ungebunden, Name `GameSir G7 Pro`.
217 Statusproben über 442 Sekunden plus Kerneljournal, keine kritischen
Kernelmeldungen oder Beobachter-Abbrüche. Beobachtung 15:04:42 UTC beendet;
Treiber und Dienst bleiben aktiv. Keine Motorimpulse angefordert, kein Steam-Neustart und
keine Änderung von Firmware/Profilen im Realtest.

**Bestanden:** Offline-Fix, Installation, eigenständige Aktivierung, normale
Eingaben und genau eine reale Funk-Wiederverbindung mit anschließendem
Eingabenachweis. **Weiter offen:** Langzeitstabilität, weitere Hotplug-/Suspend-/
Bootzyklen und eindeutige Zuordnung aller früheren Freezes. Der konkrete
Speicherfehler ist behoben; ein einzelner erfolgreicher Zyklus ist kein
allgemeiner Nachweis, dass sämtliche Freeze-Ursachen beseitigt sind.

## Private Belege

`.local/integration/20261014T143135Z-second-freeze-readonly/`: vollständige
vorherige/aktuelle Kernel- und Managerjournale, zusätzliche freigegebene
Root-Lesungen, gespeicherter Managerzustand, statischer FF-Nachweis und
freigegebenes Pausenergebnis. Rechte 0700/0600, SHA256-Sicherung; keine
Geräte-UIDs oder ungefilterten Journale im Git-Repository.

`.local/integration/20261014T144704Z-ff-lifetime-upgrade/`: Vor-/Nachprüfung,
vollständige Transaktion, DKMS-Log und anschließende Aktivierungsnachweise.
Paketaudit und extrahierter Modulbau: `build/ff-lifetime-validation/`.
