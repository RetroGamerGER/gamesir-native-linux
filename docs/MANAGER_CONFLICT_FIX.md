> Public export: personal tester, host and path references were anonymized. Historical evidence hashes refer to the private originals.

# Manager-Konflikt: Offline-Korrektur und erneute Aktivierung

Stand: 14. Oktober 2026. Paketrevision `0.1.0.alpha2-2`, Kernel-/DKMS-Version
weiterhin `0.1.0.alpha2`. Keine Änderung des Kernelcodes oder der privaten UAPI.
Die Korrektur entstand ausschließlich offline. Am 14. Oktober folgte das
gesondert freigegebene Paketupdate und danach die getrennt freigegebene
Wiederaktivierung. Damals war die Pause aufgehoben und normale KDE-Eingaben
bestätigt. Nach dem späteren zweiten Freeze ist die Automatik wieder pausiert;
der aktuelle Fehler und Updatefortschritt stehen in [FF_LIFETIME_FIX.md](FF_LIFETIME_FIX.md).
Die folgenden Nachweise beschreiben den früheren Manager-Updatevorgang.

## Belegter Fehler und Umfang

Die laufende Revision `0.1.0.alpha2-1` prüfte vor einer periodischen
Statusabfrage denselben Fremdzugriffs-Guard wie vor einer Mutation.
Ein offener usbfs-Deskriptor genügte für eine dauerhafte Sperre, selbst bei
weiterhin eigener nativer Bindung. Ein historischer Sperrauslöser ist per PID
dem Constance-Prozessverbund zugeordnet. Welcher Unterprozess welche USB-
Operation ausgeführt hat, wurde nicht aufgezeichnet und bleibt unbekannt.
[Reale Befunde und bestätigter Rückweg](STEAM_PROTON_BUTTONS.md).

Ein usbfs-FD allein beweist keine Übernahme des gebundenen Interfaces.
Die Korrektur trennt deshalb passive Statusbeobachtung und aktive Operationen.
Es gibt keine Prozessnamen-Ausnahme für Steam, Proton oder Deadband und keine
pauschale Abschaltung der Schutzprüfung.

Der vorhandene Kerneldecoder, alle 15 geforderten Tastencodes, sechs IMU-
Rohkanäle, vier Motoren und die Spiel-Effektdauer bleiben unverändert.
Ein behobener Managerfehler ist noch kein Beleg freier Paddle-Belegung in
Constance. Die Gyro-Skalierung bleibt eigenständig ungeklärt.

## Umsetzung und Sicherheitsgrenzen

- `info` und `boot-info` verwenden einen eigenen Beobachtungspfad. Er prüft
  die vollständige sysfs-Instanz und native Bindung vor und nach dem
  Prozessscan. Ein fremder usbfs-FD allein verhindert diese Getter nicht.
  Ein fremder nativer Kontroll-FD bleibt exklusiv und verschiebt die Abfrage.
- Periodisches 109c-`info` erhält die gespeicherten Kernel-Tokens. Der echte
  C-Client prüft `GET_BOOT_STATUS` und anschließend `GET_INFO` auf demselben
  geöffneten FD. Token-, ABI- oder Statusabweichungen werden nicht als
  erfolgreiche Laufzeit ausgegeben. Nach dem Clientabschluss prüft der
  Manager die USB-Instanz erneut, bevor er das Ergebnis verwendet.
- Ausschließlich `open(EBUSY)` der beiden Getter liefert Client-Exitcode 4.
  Fehler beim IOCTL, `fstat`, Schließen oder bei anderen Kommandos bleiben
  echte Fehler. Die Entscheidung hängt nicht vom Text einer Fehlermeldung ab.
- Ein vorübergehend belegter Statuskanal wird als `status_conflict` mit
  `status_retry_in` sichtbar. Nur Getter werden mit Abständen von 1, 2, 4,
  8 und höchstens 10 Sekunden weiter beobachtet. Die bisherige Phase und
  Besitznachweise bleiben erhalten; eine erfolgreiche Abfrage entfernt die
  Warnung. Keine neuen Startversuche, Motorpakete oder USB-Resets entstehen.
  Bei dauerhaft belegtem Kanal bleiben aktuelle Statuswerte unbekannt;
  eine aktive Phase allein ist dann kein frischer Gesundheitsnachweis.
- Bootstrap, Claim/Bindung, Rückgabe, PM-Resume und Haptik behalten den
  bisherigen strengen Fremdzugriffsschutz. Eine echte Konkurrenz während
  dieser Operationen kann daher weiterhin blockieren. Diese Revision ist
  keine allgemeine Erlaubnis für parallele native und libusb-Steuerung.
- Terminales `blocked` wird jetzt konsistent gespeichert und über einen
  Dienstneustart erhalten. Neustart hebt eine Quarantäne nicht auf und
  löst nicht wegen der früheren `failed`/`blocked`-Diskrepanz unerwartet END aus.
  Alte gespeicherte Fehler werden nicht automatisch in aktive Sitzungen
  umgewandelt. Der bereits geprüfte manuelle Rückweg bleibt verfügbar.

Die Kernel-Getter selbst kopieren lediglich Status. Der allgemeine historische
Kontrollclient kann beim Schließen außerhalb des persistenten Handoff-Betriebs
jedoch STOP auslösen. Die Beobachtungsregeln beziehen sich deshalb auf die
vom Manager geprüften nativen Zustände, nicht auf beliebige Kontrollknoten
oder auf den endlichen Entwicklermodus. Kernel-Quellcode und ABI bleiben gleich.

## Offline-Nachweise

- `make test` besteht vollständig: darunter 95 Manager-/Adaptertests,
  66 Szenarien des echten C-Statusclients in drei Testmethoden unter
  ASan/UBSan, 23 Haptik- und 24 Pakettests. Der gemeinsame Protokoll- und
  Laufzeitkern, alle 15 Tastenmasken, Viermotor-Fristen/Stopps sowie die
  bisherigen Start-/Claim-Regressionen bestehen ebenfalls.
- Die gezielten neuen Fälle prüfen usbfs-Beobachter, beide Prüfstellen beim
  ersten 100a-Status, späteren Kontroll-FD-Konflikt, Client-`open(EBUSY)`,
  erfolgreiche Fortsetzung, begrenzte Abfragefrequenz, Token-/Parent-/
  Treiberwechsel vor Ergebnisverwendung, echte Statusfehler, Zeitüberschreitung,
  Pause/Shutdown und gespeichertes `blocked` über einen Dienstneustart.
- `make test-sdl-buttons`: acht gerätefreie Bibliotheksfälle bestanden.
  Das bestätigt den unveränderten SDL-Paddlepfad mit künstlichen Ereignissen,
  keine tatsächliche Spielebelegung.
- `make kernel`: lokaler Bau für `7.2.9-2-garuda` erfolgreich, keine Warnung,
  keine USB-Autoload-Aliase. Kein Laden oder Installieren. Der Vergleich mit
  dem installierten Quellencommit `8d566f0` bestätigt unveränderte Dateien
  unter `kernel/`, `src/`, `include/uapi/` sowie unveränderte DKMS-Konfiguration
  und Modulversion.
- Unabhängiger Code-Review abgeschlossen. Die dabei gefundene Lücke beim
  ersten Statusabruf nach Claim wurde korrigiert und mit beiden möglichen
  Guard-Konflikten regressionsgeprüft. Keine weiteren konkreten Findings.

Lokale Prüflogs: `build/manager-conflict-validation/`. Die Paketierung ist
abgeschlossen; Quell-/Binärpaket und vollständige Prüflogs bleiben lokale
Bauartefakte. Kein Paket und keine vollständigen Systemprotokolle in Git.

### Abgeschlossener Paketaudit

Fix- und Paketquellencommit: `3326e02ac70a0269875287113a06f9b167b0b8b8`.
Die Paketierung verwendete einen unveränderlichen Git-Snapshot dieses Commits.
Dieser nachfolgende Audittext dokumentiert dessen Ergebnis; er verändert die
bereits gebauten Paketquellen nicht.

- Paket `build/alpha2-manager-fix-release/gamesir-native-dkms-0.1.0.alpha2-2-x86_64.pkg.tar.zst`
  ohne Installation erfolgreich gebaut; enthaltene Versionsangabe bestätigt.
- Alle 61 Dateien des erlaubten Quellarchivs stimmen bytegenau mit dem Snapshot
  überein. Zweiter Archivbau mit demselben `SOURCE_DATE_EPOCH` ergibt dasselbe
  Archiv. Dies behauptet keine geprüfte Bitreproduzierbarkeit des Binärpakets.
- 58 Nutzdateien und drei Paketmetadatendateien geprüft. Manager, Client,
  Kernelquellen, Dokumente, Unit und Upgrade-/Rückweghelfer stimmen mit den
  jeweiligen gebauten beziehungsweise freigegebenen Quellen überein.
  Keine Installer/Firmware/Rohmitschnitte, `.INSTALL` oder fertigen `.ko` im
  Paket; keine Setuid-/Setgid- oder gruppen-/weltbeschreibbaren Nutzdateien.
- Der **aus dem Paket extrahierte** Statusclient besteht `--self-test`, ohne
  Geräteöffnung. Die **extrahierten DKMS-Quellen** wurden zusätzlich gegen
  `7.2.9-2-garuda` gebaut: keine Warnung, Modulversion `0.1.0.alpha2`, passendes
  vermagic und keine USB-Autoload-Aliase. Kein DKMS-Aufruf auf dem Live-System.
- Paket-SHA256:
  `5fe1bbe1909db25aaf729a065358404398daadeb76b4af6668dc46a22c2b4823`.
  Quellarchiv-SHA256:
  `cd0b522486e7185cdda6aef3502fb454e36d952d7ddb7ecdbf4e1037e60a8ed9`.
  Vollständige Befunde in `build/manager-conflict-validation/package-audit.json`
  und `package-kernel-build.json`, mit eigenen Prüfsummen gesichert.

**Technisches Go für eine kontrollierte Aktualisierung nach frischem
Vorabcheck, kein Go für eine ungefragte Aktivierung.** Die neue Konfliktbehandlung ist offline belegt;
normaler Steam-/Proton-Betrieb mit der Korrektur benötigt weiterhin den realen,
separat freigegebenen Test. Der AMDGPU-Fehler ist damit nicht behoben.

## Kontrolliertes Update am 14. Oktober 2026

Die konkret gezeigte Pakettransaktion einschließlich Passwortabfrage,
Dienst-/Modul-/DKMS-/Garuda-Hooks und lesender Nachkontrolle wurde separat
freigegeben. Installiert wurde genau das oben auditierte Paket aus `3326e02`,
SHA256 unverändert `5fe1bbe1909db25aaf729a065358404398daadeb76b4af6668dc46a22c2b4823`.
Die vollständige interaktive Transaktion enthielt ausschließlich
`gamesir-native-dkms 0.1.0.alpha2-1 → 0.1.0.alpha2-2`; erst danach bestätigt.
Keine weiteren Pakete, Datenbankaktualisierung oder automatische Reparatur.

**Vorprüfung und geklärte Abweichung:** Der Dongle war seit dem aktuellen
Hostboot in `3537:109c`, Bus 8, Adresse 4, Port `8-6`, IF0 an xpad und IF1
ungebunden. Deshalb wurde die Installation zunächst angehalten. Die separat
freigegebenen Leseabfragen bestätigten `paused=true`, `devices={}`, leere
`leases` und keine Scan-/Portfehler. Es gab keine native Bindung und
`gs_native` hatte Referenzzähler 0. Der installierte Rückgabe-/Shutdownpfad
wurde unabhängig geprüft: Ohne eigene Einträge/Leases sendet er kein END
und übernimmt die fremde 109c-Instanz nicht. Das reine Paketupdate konnte
deshalb unter Beibehaltung dieses Zustands ausdrücklich freigegeben werden.
`returned=true` bezog sich nur auf verwaltete Instanzen und war **kein**
Nachweis eines Wechsels zu 100a. Wiederaktivierung bleibt davon getrennt.

Um 12:53 UTC stoppte der vorhandene Hook den Dienst und entlud ausschließlich
das ungebundene `gs_native`. DKMS entfernte und installierte die gleiche
Modulversion erneut. Garuda erneuerte Kernelabbild sowie normale und
Fallback-Initramfs; Snapper legte die Snapshots 67/68 an. Pacman endete mit 0.
Der bereits dokumentierte Hinweis `Deprecated feature: CLEAN` erschien erneut;
keine automatische Konfigurationsänderung daraus abgeleitet.

Nachkontrolle um 12:55 UTC / 14:55 MESZ:

| Prüfung | Ergebnis |
|---|---|
| Installiertes Paket | `gamesir-native-dkms 0.1.0.alpha2-2` |
| Paketintegrität | 77 Einträge, 0 veränderte Dateien |
| Manager und Kontrollclient | bytegenau mit dem freigegebenen Paket identisch |
| Installierter Client-Selbsttest | bestanden, keine Geräteöffnung |
| DKMS | `gamesir-native/0.1.0.alpha2, 7.2.9-2-garuda, x86_64: installed` |
| Frischer realer Modulbau | Exit 0, keine Compilerwarnungen/-fehler |
| Modulmetadaten | Version `0.1.0.alpha2`, passendes vermagic, keine USB-Autoload-Aliase |
| Dienst | `inactive/dead`, MainPID 0, Result success, Autostart weiterhin enabled |
| Laufendes Modul | `gs_native` nicht geladen, keine native Bindung |
| Gespeicherter Zustand | `paused=true`, leere Leases/Versuche/Budgets |
| USB-/Bindungsmetadaten | dieselbe Instanz/Adresse, unverändert 109c/xpad, IF1 ungebunden |

Keine neue GameSir-Kernelwarnung, kein neuer Oops im kontrollierten Fenster.
Kein neuer Eingabe-, Motor-, Steam- oder Bootstraptest. Insbesondere bestätigt
die unveränderte 109c/xpad-Bindung keine neue Spielfunktion. Bestehende
Offline-Regressionen bleiben die Grundlage; neu geprüft wurde der tatsächlich
installierte Paket-/DKMS-Zustand. Keine weiteren Quellcodeänderungen gegenüber
dem offline geprüften Paket; daher kein erneuter vollständiger Offline-Testlauf
nur für die Installation.

Private Belege einschließlich Transaktion, Vor-/Nachzustand, DKMS-Baulog und
Prüfsummen: `.local/integration/20261014T125038Z-manager-fix-upgrade/`.
Keine vollständigen Hostlogs oder Paketdateien in Git.

**Das Paketupdate allein ließ die Verwaltung pausiert.** Der Dienst wurde
dabei nicht wieder gestartet, die unverwaltete 109c-Instanz nicht übernommen.
Erst die folgende neue Freigabe erlaubte die Wiederaufnahme aus einer frisch
geprüften 100a-Instanz. Kein Systemneustart gehörte zu diesen Schritten.

## Kontrollierte Wiederaktivierung am 14. Oktober 2026

Frische Vorprüfung um 12:59 UTC: Der Dongle hatte sich bereits vor unseren
neuen Eingriffen um 12:59:01 UTC als `100a`, Bus 8, Adresse 7 am Port `8-6`
angemeldet. IF0 xpad, IF1 usbhid, Modul ungeladen, Dienst inaktiv/aktiviert.
Die Ursache dieser vorherigen Neuverbindung wurde nicht zusätzlich erhoben;
sie ist keine vom Manager bewirkte Rückkehr. Paket/Headers/DKMS passend zu
`7.2.9-2-garuda`, Paketintegrität unverändert. [tester] bestätigte verbundenen
Funkcontroller sowie geschlossenes Deadband und geschlossene Spiele.

1. Nach eigener Freigabe gespeicherte Pause/leere Leases geprüft und den Dienst
   um 13:01:14 UTC einmal gestartet. Native Betriebsparameter jeweils `Y`,
   Dienst active/enabled, Manager weiterhin pausiert, 100a/xpad/usbhid unverändert.
2. Anschließend separat lesenden Prozess-/Gerätecheck, genau ein `resume`
   und Überwachung freigegeben. Der bestehende Lesehelfer wurde auf den
   aktuellen Pausen-/Paket-/Instanzzustand angepasst. Er bestätigte genau
   ein Zielgerät und keinen fremden USB-/Kontrollhandle vor der Übernahme.
   Der dokumentierte einmalige Fehler-`release` war zusätzlich freigegeben,
   wurde aber nicht benötigt und nicht ausgeführt.
3. Um 13:03:56 UTC erfolgte der native Claim der 100a-Instanz. Der Manager
   wartete zunächst in `waiting_input`; das erste 35-s-Beobachtungsfenster
   enthielt noch keinen Bootstrap. Nach erneuter menschlicher Eingabeansage
   bestätigte [tester] A und Stickbewegungen. Es gab kein zweites `resume`.
4. Um 13:05:11 UTC begann die Neuanmeldung. Um 13:05:13 UTC erschien `109c`,
   Adresse 8, und der Kernel meldete `native bootstrap finished: 0`.
   Managerphase anschließend active, ohne Fehler oder Statuskonflikt.

Die bekannte xpad-Abbaumeldung `usb_submit_urb ... -2` erschien beim ersten
Unbind. Sie gehört zum bereits untersuchten Abbaupfad; danach native Bindung
und Bootstrap erfolgreich, kein nativer Laufzeitfehler oder neuer Kernel-Oops
im kontrollierten Fenster. Kein globales xpad-Entladen, kein Deadband-Start,
kein Firmware-/Profilzugriff und keine Motorimpulse.

Abschlussprüfung um **13:07:18 UTC / 15:07:18 MESZ**:

| Prüfung | Ergebnis |
|---|---|
| Paket | `0.1.0.alpha2-2` |
| Dienst | active/running, enabled, Result success, NRestarts 0 |
| Manager | paused false, 8-6/109c active, keine Scan-/Port-/Statusfehler |
| Gespeicherter Zustand | Pause aufgehoben, Besitznachweis für genau 8-6 |
| USB/Bindung | 3537:109c, Bus 8, Adresse 8; IF0 gs_native, IF1 ungebunden |
| Input-Gerät | GameSir G7 Pro, in diesem Lauf event14 |
| Fähigkeiten | alle 15 geforderten Codes einschließlich 704–707 registriert |
| Nutzerbestätigung | korrekter Name, normale Tasten, D-Pad, beide Sticks und Trigger im KDE-Test |

Die Fähigkeitstabelle enthält zusätzlich 167 und 708; diese wurden hier nicht
getestet. Dieser Lauf enthält keine neue evtest-Aufzeichnung oder isolierte
Betätigung jeder Zusatztaste. Registrierung, frühere echte Einzelereignisse
und heutige KDE-Bestätigung bleiben getrennte Nachweise. Direkte Paddle-
Belegung sowie die Konfliktkorrektur beim tatsächlichen Steam-/Proton-Spielstart
sind weiterhin nicht praktisch abgenommen. Auch Boot-/Suspend-/Hotplug-
Zuverlässigkeit wird durch diese einmalige Wiederaufnahme nicht bewiesen.

Private Belege mit SHA256:
`.local/integration/20261014T130110Z-manager-reactivation/`.
Vorhandene Lese-/Beobachtungshelfer wiederverwendet, keine neue Testlaufzeit,
keine Änderung am installierten Code. Dienst und native Bindung bleiben für
den normalen Betrieb aktiv; weitere Hardware-/Spieletests separat abstimmen.

## Dokumentierter Ablauf für Update und Wiederaufnahme

Die folgenden Schritte sind durch die beiden Ergebnisabschnitte oben für
diesen Lauf abgeschlossen. Nicht erneut installieren/starten/resumieren.
Sie bleiben als nachvollziehbarer Ablauf für künftig gesondert freigegebene
Wartung erhalten. Die historische Ausgangslage vor der Offline-Korrektur folgt.

Nach dem bestätigten Rückweg wurde das System durch [tester] neu gestartet.
Die letzte lesende Prüfung vor dieser Offline-Arbeit zeigte `3537:100a`,
Interface 0 an xpad und Interface 1 an usbhid. Der Dienst war aktiv/aktiviert,
das native Modul geladen; die zuvor gespeicherte Pause verhindert weiterhin
die native Übernahme. Diese Momentaufnahme ersetzt keine frische Vorprüfung.

Vor **jedem** folgenden Eingriff ist die konkrete Freigabe nötig. Die heutige
Offline-Freigabe umfasst keinen dieser Schritte. Pfade sind vom Projektwurzel-
verzeichnis aus angegeben; den absoluten Paketpfad vor Ausführung bestätigen.

### 1. Frischer lesender Vorabcheck

Ohne Geräteöffnung Kernel/Headers, installierte Paket-/DKMS-/Modulversionen,
Dienst, Modulparameter, USB-Instanzen/Interfaces und aktuelle Bindungen prüfen.
Deadband und Spiele sollen geschlossen sein. Mit gesonderter Passwortfreigabe:

```sh
SUDO_ASKPASS=/usr/bin/ksshaskpass sudo -A -p 'Password: ' /usr/bin/gamesir-native status
SUDO_ASKPASS=/usr/bin/ksshaskpass sudo -A -p 'Password: ' /usr/bin/cat /var/lib/gamesir-native/state.json
```

Voraussetzungen sind `paused=true`, keine offene Lease, kein laufender
Managerauftrag, keine native Bindung und der beabsichtigte Dongle in
`100a/xpad/usbhid`. Mehrere Dongles, unerwartete Bindungen, erneute Kernel-Oops
oder unklare Eigentümerschaft bedeuten anhalten. Die früheren AMDGPU-Oops
werden durch diesen Manager-Fix weder erklärt noch behoben.

### 2. Upgrade ausdrücklich einschließlich seiner Hooks freigeben

Das bestehende Paket enthält bereits einen PreTransaction-Upgrade-Hook.
Er verwendet den installierten Rückweg, pausiert die Übernahme, prüft die
Rückgabe, stoppt den Dienst und entlädt ausschließlich das ungebundene,
referenzfreie `gs_native`. Bei einem offenen Rückweg bricht er vor dem
Austausch ab. Daher ist dieses Paketupgrade **nicht modulneutral**, obwohl
der Kernelquelltext unverändert ist.

Der später freizugebende Aufruf lautet:

```sh
SUDO_ASKPASS=/usr/bin/ksshaskpass sudo -A -p 'Password: ' /usr/bin/pacman -U \
  ./build/alpha2-manager-fix-release/gamesir-native-dkms-0.1.0.alpha2-2-x86_64.pkg.tar.zst
```

Transaktion vor Bestätigung vollständig prüfen: ausschließlich erwartetes
GameSir-Upgrade von Revision 1 auf 2. Keine zusätzlichen Pakete/Upgrades,
kein Datenbank-Refresh, kein `--noconfirm`, keine automatische Reparatur.
Die vorhandenen DKMS-Hooks bauen/installieren die gleiche Modulversion erneut;
Garudas Dracut-/Snapshot-Hooks können dabei Kernelabbild und Initramfs sowie
Snapshots erneuern. [Bestehendes Installationsaudit](ALPHA_INSTALL_AUDIT.md).
Diese Auswirkungen müssen Teil der Upgradefreigabe sein.

Das Paket führt kein `resume` aus. Die persistente Pause und bisherige
systemd-Aktivierung bleiben erhalten. Nachher **nur lesend** Paketinhalt,
Client-/Manager-Prüfsummen, DKMS-Bauprotokolle, Modulversion und inaktiven
Dienst prüfen. Pacman-Erfolg allein ist kein DKMS-Erfolgsnachweis.

### 3. Korrigierten Dienst zunächst pausiert starten

Erst nach erfolgreichem Upgrade-Audit und eigener Freigabe:

```sh
SUDO_ASKPASS=/usr/bin/ksshaskpass sudo -A -p 'Password: ' \
  /usr/bin/systemctl start gamesir-native.service
```

Dieser Schritt lädt über die Unit `industrialio` und `gs_native` mit den
geprüften Dauerbetriebsparametern. Er ist keine bloße Statusabfrage.
Die zuvor frisch bestätigte gespeicherte Pause muss erhalten bleiben;
`100a/xpad/usbhid` darf noch nicht übernommen werden. Die vorhandene
Autostart-Aktivierung wird geprüft, nicht blind neu gesetzt.

### 4. Native automatische Übernahme separat freigeben

Bei unverändertem Zielzustand und geschlossenem Deadband:

```sh
SUDO_ASKPASS=/usr/bin/ksshaskpass sudo -A -p 'Password: ' /usr/bin/gamesir-native resume
```

Dieser Auftrag hebt die Pause auf und erlaubt die normale automatische
Übernahme samt eigenständigem Bootstrap nach 109c. Bei mehreren passenden
Geräten könnte er mehrere Instanzen verwalten; deshalb vorher die tatsächlich
freigegebene Geräteauswahl prüfen. Keine Start-/Motorbefehle parallel ausführen.

Danach native Bindung, aktiven Managerzustand, Gerätenamen `GameSir G7 Pro`,
alle 15 Tastencodes sowie Kernelmeldungen prüfen. Für manuelle Eingaben
mindestens 30 Sekunden Vorbereitung, zehn Sekunden Wechselpuffer und
ausreichend Zeit je Zusatztaste einräumen. Der anschließende Steam-/Constance-
Test bleibt ein eigener Schritt: Fortbestehen der nativen Sitzung beim
Spielstart und direkte Paddle-Belegung getrennt nachweisen. Keine Motor-
Belastungstests oder Änderungen an Spiel-/Steam-Profilen einschließen.

## Abbruch und Rückweg

Bei falscher Pakettransaktion, Buildfehler, unerwarteter Identität, fremder
Bindung, Tokenabweichung oder neuem Kernel-Oops anhalten. Keine Wiederholung
von Bootstrap, Resume oder END auf Verdacht. Die getestete passive
Status-Wartebehandlung ist kein automatischer USB-Reparaturversuch.

Vor Beginn der realen Aktivierung den vorhandenen Rückweg erneut konkret
freigeben: Manager-`release`, Zustand prüfen, bei weiterhin offenem 109c-Besitz
manuelle Dongle-Entfernung separat abstimmen, auf Besitzauflösung warten,
dann neu einstecken und `100a/xpad` sowie normale Eingaben bestätigen.
Die Rückbindung an xpad allein ist kein PID-Wechsel. Modul-/Paket-Rollback
bleibt eine weitere ausdrückliche Entscheidung; alte Artefakte erhalten.

Die administrative Wiederaufnahme ist einmalig nach diesem Wartungseingriff.
Im freigegebenen normalen Betrieb soll Controller-Einschalten wieder ohne
Deadband, Terminal oder Passwort genügen. Langzeit-, Hotplug- und Suspend-
Zuverlässigkeit bleiben reale Abnahmepunkte.
