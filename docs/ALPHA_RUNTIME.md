# Alpha-Laufzeit und Besitzregeln

20. Oktober: Eine enge Offline-Korrektur löst die Sperre einer neuen,
noch unversuchten `100a`-Instanz nach nachgewiesen beendetem direktem
`109c`-Start mit fehlenden Daten und VERIFY-Timeout. Erst ein neuer vollständiger
Scan und die üblichen Besitz-/Budgetprüfungen erlauben den nächsten Start.
Keine Wiederholung auf der fehlgeschlagenen Instanz oder Migration alter Sperren.
[Abgrenzung und Tests](REVISION13_FIRST_START.md#offline-manager-correction--20-october-2026).
Noch nicht installiert; der folgende Architekturstand ist historisch.

PRE-ALPHA-Architekturstand: 19. Oktober 2026, Modul `0.1.0.alpha3`,
vorbereitete Paketrevision 12. Die korrigierten Startfälle sind nur offline
geprüft; ihre Hardwareabnahme steht aus. [Änderungsumfang](STANDALONE_STARTUP.md).
Dieser Text beschreibt Besitz- und Laufzeitregeln, keinen aktuellen Zustand
eines bestimmten Rechners. Der Standardpfad ist in begrenzten Hardwareläufen
mit eigenständigem Start, Eingaben und Roh-IMU bestätigt; ein Boot mit späterem
Controller-Einschalten und Steam-Paddles ist dokumentiert. Der 105e-Pfad ist
inzwischen begrenzt auf Hardware geprüft, bleibt aber experimentell. Allgemeine
Boot-, Hotplug-, Suspend-/Resume- und Langzeitzuverlässigkeit sind nicht belegt.

Öffentlicher Einstieg und aktuelle Funktionsgrenzen: [README](../README.md),
[Release-Audit](RELEASE_AUDIT.md). Allgemeine Installation und Rückbau:
[INSTALLATION.md](INSTALLATION.md). Die älteren Aktivierungs-, Statuskonflikt-
und Rückwegberichte bleiben als zeitgebundene Nachweise erhalten; sie gelten
nicht als aktuelle globale Betriebszustände. Gyrokalibrierung bleibt pausiert.

Die lokale Paketrevision 6 korrigiert den [Reconnect-Statuslauf](MANAGER_RECONNECT_FIX.md)
offline. Ein veralteter passiver Getter einer gesunden 109c-Sitzung darf eine
frisch erkannte 100a/xpad-Instanz nicht als bereits abgegeben blockieren. Das
alte Ergebnis gewährt keinerlei Besitz am Ersatzgerät; die nächste frische
Enumeration, normale Guards und das Startbudget bleiben erforderlich.
Unvollständige Metadaten werden zurückgestellt, globale Beobachtungsfehler
stoppen weitere Aktionen im selben Tick. Echte Fehler bleiben persistent
verriegelt. Bereits vom alten Manager gespeicherte Fehler werden nicht allein
anhand ihrer Meldung automatisch gelöscht. Noch keine neue Hardwareabnahme.

## Aktivierung und Gerätezuordnung

`gs_native` bleibt für normale native Spielsitzungen zuständig. `xpad` ist
ausschließlich Fallback bei Deaktivierung, Deinstallation oder terminalem
Fehler; weder Wartung noch kurze Funkpausen führen planmäßig zu xpad zurück.
Das Aufräumen einer eigenen Instanz ist unabhängig von der Berechtigung,
einen neuen Start auszulösen.

Das Paket bleibt nach Installation inaktiv. Erst die separat freizugebende
Dienstaktivierung lädt den Adapter mit `bootstrap_mode=1`, `enable_output=1`
und `persistent_mode=1`. Ohne diese ausdrückliche Kombination bleibt der
bisherige endliche Entwicklermodus erhalten. Keine xpad-Blacklist und keine
pauschale Abbindung anderer Controller. [Paket und Rücknahme](ALPHA_INSTALLATION.md).

`tools/service/gamesir_native.py` untersucht unterstützte VID/PID-Kombinationen
mit den erwarteten Interfaces und Endpunkten. Er verwaltet jeden dynamisch
gefundenen Anschluss getrennt; `8-6` ist keine Produktionsvorgabe.
Bootkennung, Geräteinstanz und Lebensdauer des übergeordneten USB-Objekts
verhindern die Wiederverwendung alter Sitzungen nach einem Neustart oder
Hubwechsel. USB-Adresse und Produktname sind keine individuelle UID.
Die vorhandenen Serienstrings sind nicht als stabile modusübergreifende UID
bestätigt. Ein passendes Gerät an einem fremden Port ist kein Übergangskandidat.

Beim Standardexemplar übernimmt der Manager ein geprüftes freies oder optional
xpad-gebundenes 100a-Interface 0, prüft den passiven Laufzeitstatus und
beauftragt einmal den vorhandenen Bootstrap. Seit Revision 12 ist dafür kein
vorheriger Tastendruck oder akzeptierter Gamepad-Bericht mehr erforderlich. Der Kernel korreliert die neue 109c-Instanz am aktuellen Anschluss
und initialisiert sie genau einmal. Ein bereits als 109c erkanntes Gerät kann
seit Revision 12 mit einem eigenen exakten Übernahmeauftrag direkt initialisiert
werden, sofern IF0 frei oder xpad-gebunden ist. Fremde/native Besitzer werden
weiterhin ausgeschlossen; keine Übernahme allein aufgrund der PID. Interface 1
bleibt unverändert. Direkter 109c-Start und 105e benötigen keinen Moduswechsel.
Für `105e` übernimmt er ebenfalls ausschließlich das geprüfte freie oder
xpad-gebundene Interface 0. xpad wird weder geladen noch vorab zur Initialisierung
gebunden. Der einmalige Bootstrap beginnt direkt auf dieser Instanz mit der
gemeinsamen GIP-Initialisierung und den Heartbeats. Keine Übergangspakete,
keine neue PID, kein `--handoff-xpad`; frische IMU und eindeutige Kernel-Tokens
bleiben Voraussetzungen der Runtime-Übergabe. Ausbleibende IMU führt zu einer
begrenzten Fehlerbehandlung, nicht zu einer geratenen alternativen Sequenz.
Der Manager prüft fremde Zugriffe vor Änderungen; normale evdev-Spielzugriffe
sind erlaubt. Reine Statusgetter prüfen exakte native Instanz und Kontroll-
Exklusivität, behandeln aber einen offenen usbfs-FD allein nicht als
Besitzverlust. Belegter Kontrollkanal verschiebt nur die Getter-Abfrage;
Statuswarnung und begrenzter Abfrageabstand sind sichtbar. Aktive Operationen
behalten den strengen Guard. [Statusvertrag](MANAGER_CONFLICT_FIX.md).
Pro Instanz gibt es einen Startversuch und zusätzlich ein Budget
von drei Starts pro Anschluss innerhalb von zehn Minuten. Das Budget wird vor
der Übernahme geprüft und der Versuch unmittelbar vor dem Bootstrap persistent
verbucht. Eine noch nicht mögliche Statusprüfung verbraucht keinen Startversuch;
eine fehlende Tastenänderung verhindert den Start nach gültiger Prüfung nicht.
Die Startberechtigung ist von der Bereinigung eigener Instanzen getrennt.

Korrektur vom 21. Oktober in Revision18 (auf beiden Testrechnern installiert
und aktiviert; Funktions-/Reconnect-Abnahme noch offen): Eine vor der Übernahme
abgelehnte Instanz wartet in `cooldown`; `start_retry_in` zeigt die Restzeit.
Nach Ablauf folgt eine frische Geräteprüfung. 60 Sekunden durchgehend bestätigter,
fehlerfreier aktiver Betrieb geben das Anschlussbudget wieder frei. Kurze
Startfolgen bleiben begrenzt; bloßes Warten auf den Controller genügt nicht.
Echte Fehler und ungeklärter Besitz werden nicht durch Zeitablauf aufgehoben.
[Regeln und Tests](MANAGER_RECONNECT_FIX.md).

Im Dauerbetrieb lehnt der Kernel jeden gewöhnlichen Start-Probe ohne passenden
Übernahmeauftrag ab; für den korrelierten Übergang gilt dessen Besitznachweis. Fehlende
Autoload-Aliase allein würden dies bei bereits geladenem Modul nicht verhindern.
Erst der budgetgeprüfte Manager darf die private, versionierte Schreibschnittstelle
`/sys/bus/usb/drivers/gs_native/acquire_100a`, `acquire_105e` oder `acquire_109c`
verwenden (0200 und CAP_SYS_ADMIN). Jeder Eingang prüft seine exakte PID;
es gibt keine pauschale Gerätefreigabe.
Ihr Format ist `1 IFNAME BUS ADDRESS DEVICE_INODE PARENT_INODE` mit abschließendem
Zeilenumbruch. Der Kernel prüft das referenzierte Interface, die aktuelle
USB-Identität und beide sysfs-Inodes unter der USB-Gerätesperre. Er hält eine
Referenz auf dieses Interface und löst ausschließlich dort einen optionalen
xpad-Besitzer. Freie Interfaces werden direkt übernommen. Die anschließende
Probe prüft die Identität erneut. Die Probe-Erlaubnis gilt nur einmal innerhalb dieses synchronen Aufrufs
für genau dessen Task und Interface; Hotplug und generisches `bind` erhalten
keine solche Freigabe. Es bleibt kein ungenutztes Claim-Ticket zurück.
Der spätere korrelierte 109c-Probe verwendet weiterhin den vorhandenen Bootstrap-
Besitznachweis. Ein direkt übernommenes 109c muss dagegen auf derselben
referenzierten Instanz bleiben; ein Ersatz ist kein gültiger Direktstart.
Der endliche historische Testmodus bleibt unverändert.
Die bisherigen `claim_100a`-/`claim_105e`-Attribute bleiben unverändert auf freie
Interfaces begrenzt. Der neue Manager verlangt die neuen Attribute; ein altes
geladenes Modul wird nicht durch einen unsicheren Kompatibilitätspfad umgangen.
Eine vor dem Schreibzugriff abgelehnte Übernahme gewährt keinen Rückgabebesitz.
Bei Prozessabbruch oder Fehler vor bestätigter Übernahme einer nativen Bindung
bleibt diese gesperrt zur manuellen Klärung. Der ursprüngliche Übernahmefehler
bleibt auch bei späteren Bereinigungsfehlern und Manager-Neustarts gespeichert.

**Verbleibende Grenze:** Eine spätere 100a-/105e-Rückgabe des Managers ist
zwischen letzter Metadatenprüfung und Schreibzugriff nicht atomar gegen
extrem schnelles Abziehen/Ersetzen am selben Anschluss. Nachprüfungen und der
Kernel-Probe verhindern einen ungeprüften Bootstrap; eine zwischenzeitliche
Abbindung eines Ersatzgeräts ist dadurch nicht vollständig ausgeschlossen.
Die anfängliche optionale xpad-Abbindung findet dagegen seit Revision 11 am
geprüften, referenzierten Kernelobjekt statt. Konkurrierende Probes oder
Entfernung beim anschließenden Attach können weiterhin zum Abbruch führen.
Diese Alpha ist keine Zusicherung atomarer Geräteübernahme. Die spätere
Produktionsfreigabe benötigt hierfür eine gezielte Lösung oder nachweisbar
engere Besitzgarantien. Auch ein gleichartiger Ersatzdongle ohne authentisierte
UID kann nicht allein aus Hersteller-/Produktkennung unterschieden werden.
Fehlt die xpad-Rückbindeschnittstelle, stoppt der Manager vor dem Abbindeschritt
mit ausdrücklichem Fehler; er lädt xpad nicht implizit nach und behauptet keine
Rückkehr. Auch bei vorhandenem xpad muss der reale Rückkehrzustand bestätigt werden.

## Dauerbetrieb, Funkverlust und Suspend

Die persistente Sitzung hat kein Entwicklerzeitlimit. Ein einziger Kernelpfad
serialisiert Initialisierung, Wartung, Antworten und alle Motorpakete.
Gamepad und sechs IIO-Rohkanäle teilen den eingehenden Strom.

Fehlende Gamepad-Änderungen bei Ruhe sind kein Fehler. Erst wenn sowohl
akzeptierte Gamepad- als auch IMU-Daten mehr als zwei Sekunden ausbleiben,
neutralisiert der Adapter die Eingaben und verwirft Motorziele einmalig.
Er behält die Gerätezuordnung und Wartung bei. Neue akzeptierte Daten heben
die Datensperre auf; alte Vibrationen starten nicht erneut. Eine tatsächliche
USB-Neuanmeldung erzeugt dagegen eine neue Geräteinstanz und eine neue Prüfung.
Funkverhalten ohne USB-Neuanmeldung ist noch auf Hardware zu validieren.

Suspend beendet Ausgaben und neutralisiert den Zustand. Nach abgeschlossenem
Kernel-Resume kann der Manager genau einen geprüften Wiederaufnahmeauftrag
für dieselbe vorher initialisierte 109c-/105e-Instanz senden. Dieser wiederholt nur
die bekannte native Initialisierung mit Frist und frischer IMU-Bereitschaft,
keinen Identitätswechsel. Ein Fehler bleibt terminal; keine blinde Schleife.

## Spiele-Force-Feedback

Standard-`FF_RUMBLE` nutzt den Linux-Memless-Core für Effektlaufzeit,
Wiederholungen, Überlagerung und Ende beim Entfernen/Schließen des Effekts.
Der Callback merkt nur den gewünschten Zustand der zwei Griffmotoren; USB
wird anschließend außerhalb des Input-Spinlocks übertragen. Der Worker
erneuert nötigenfalls alle 500 ms die höchstens 1.000 ms lange Hardware-Lease.
Ein fünfsekündiger Spieleffekt bleibt damit fünf Sekunden beauftragt.
Die Sekundenbegrenzung ist eine Transfer-/Ausfallsicherung, kein Effektlimit.

Die Trigger sind eigene Kanäle. Ein Stopp der Griffmotoren darf sie nicht
beenden und umgekehrt. Fehler, Suspend, Disconnect und ausdrücklich befohlenes
END löschen alle Motorziele; fehlgeschlagene Stopps werden gemeldet und nicht
durch endlose Wiederholungen verdeckt. Das Abspielen über reale Spiele und die
Mechanik bei langen Effekten benötigen einen gesondert freigegebenen Test.

Der integrierte [Haptik-Broker mit API v1](HAPTICS_API.md) vermittelt vier
Anwendungskanäle über einen gruppengeschützten lokalen Socket. Apps erhalten
keinen USB-Zugriff. Jede Verbindung besitzt eine begrenzte Lease, jede Instanz
einen eigenen Auswahlwert und jeder Motor seine eigene Effektfrist. Die
Python-Clientbibliothek erneuert die Verbindungslease automatisch. Standard-FF
an den Griffen und Broker-Trigger können nebeneinander laufen; konkurrierende
Aufträge auf demselben Griff folgen dem dokumentierten Last-Writer-Vertrag.
Ein späterer privater Kanalstopp beendet keine inzwischen von FF übernommenen
Griffe. [Kernelvertrag und tatsächliche FF-Core-Grenze](FOUR_MOTOR_KERNEL.md).

SDLs Linux-Backend unterstützt Trigger-Rumble hier noch nicht. Die lokale API
ist deshalb eine verwendbare Anwendungsanbindung, keine automatische
Kompatibilität für unveränderte Spiele. [SDL/Steam/Wine und Zusatztasten](SDL_EXTRA_BUTTONS.md).

## Freigabe, Fehler und Rückkehr

Der Manager speichert die Ausgangs-PID zusätzlich zu Instanz, Kernel-Tokens,
Start- und Bereinigungsstatus. Ein Budgetlimit blockiert weiterhin nur neue
Starts. Beim 105e-Direktstart bleiben Ursprung und Runtime dieselbe Instanz.
Nach bestätigtem END darf genau diese Instanz gezielt an xpad zurückgegeben
werden; ein neuer Scan muss `105e/xpad` bestätigen. Fehlendes oder gescheitertes
END erlaubt keine Wiederholung oder automatische Abbindung. Bei einem vor
dem Bootstrap gescheiterten Claim bleibt die begrenzte Rückgabe der eigenen
Instanz möglich. Ein Ersatzgerät, fremder Besitzer oder unklarer Besitznachweis
berechtigt nicht zur Übernahme. Ein tatsächlich bereits an xpad zurückgekehrtes
oder physisch entferntes Gerät wird nur beobachtet. Funktionierende Eingaben
müssen bei der Hardwareabnahme zusätzlich bestätigt werden.

Die folgenden Übergangsdetails betreffen den bisherigen 100a→109c-Pfad:

Nach einem fehlgeschlagenen Bootstrap bleiben die Kernel-Port-/Instanztokens
der tatsächlich übernommenen 109c-Instanz verfügbar. Der Manager prüft sie
erneut über `boot-info` am neuen Kontrollknoten und akzeptiert nur den zur
eigenen Übergabe passenden Nachweis bei unveränderter USB-/Hub-Instanz. Der
END-Client prüft dieselben Tokens auf dem bereits geöffneten FD, bevor er END
sendet. Ein gleichnamiger neuer Knoten reicht nicht als Besitznachweis.

Der Kernel erlaubt END vor erfolgreicher Runtime-Übergabe ausschließlich für
den eigenen korrelierten, bereits stillgelegten fehlgeschlagenen 109c-Start.
In diesem Zustand wurden keine Motorbefehle freigegeben: END neutralisiert
lokal und sendet keinen geratenen Moduswechsel. Die bestehende erfolgreiche
Runtime führt weiterhin ihren begrenzten Motor-STOP aus. Das Bootstrap-
Fehlerprotokoll bleibt erhalten. Fehlgeschlagener Start ist keine Bereitschaft.

`gamesir-native release` setzt zuerst eine persistente Übernahmesperre und
beendet nur verwaltete Sitzungen. Der Manager betrachtet den Rückweg erst als
erfolgreich, wenn die verwalteten Anschlüsse stabil wieder 100a/xpad mit den
erwarteten Metadaten zeigen oder physisch entfernt sind. Eine andere
Deadband-Sitzung an einem niemals übernommenen Dongle wird nicht beendet.
Ein unsicherer eigener Anschluss bleibt gesperrt und verhindert eine falsche
Erfolgsmeldung. Fehler eines zweiten Anschlusses werden getrennt behandelt.
Besitz, offene Rückwege und bereits begonnener END-Versuch werden über
Dienstneustarts erhalten. Ein Startlimit verbietet nie die Rückgabe einer
nachgewiesen eigenen 100a-Instanz; fremde Ersetzungen bleiben unangetastet.

Bleibt das Gerät nach END unter 109c, meldet der Manager einen offenen manuellen
Rückweg. Er behauptet weder einen Wechsel zu 100a noch normale Spielfunktion.
Die bekannte native Bindung bleibt dem Recovery-Zustand zugeordnet und wird
nicht als aktive Spielsitzung ausgegeben. Kein weiteres END auf Verdacht,
kein automatischer USB-Reset. Ein physischer Rückweg und seine Grenzen stehen
in [ALPHA_INSTALLATION.md](ALPHA_INSTALLATION.md).

Ein vorher geöffneter Kontroll-FD darf nach Disconnect keinen freigegebenen
Input-Speicher verwenden. Langsame Clientprozesse werden begrenzt abgebrochen,
aber nicht per SIGKILL aus einem unbekannten Kernelzustand gerissen. Ein
fehlgeschlagener END-Aufruf wird nicht auf Verdacht wiederholt. Rückkehr wird
weiter lesend geprüft und ein konkreter Fehler gemeldet.

Vor Deadband die erfolgreiche Freigabe abwarten. Danach darf die unveränderte
Anwendung wieder ihren bisherigen exklusiven libusb-Pfad verwenden. `resume`
ist eine ausdrückliche administrative Wiederaufnahme. Eine integrierte
Deadband-Konfigurations-API bei laufendem nativen Gamepad bleibt ein weiterer
Entwicklungsschritt.

## Nachweisgrenzen

Der reale Start und die frühere Viermotor-Wirkung sind in separaten kontrollierten
Hardwareläufen belegt. Der erste automatische Dienststart und reale Eingaben
sind inzwischen ebenfalls geprüft. Weitere Automatikfälle, FF-Laufzeit, PM-Wiederaufnahme,
Paketentfernung und Mehrgerätefälle sind mit künstlichen Backends, tatsächlichen
C-Kernelfunktionen sowie lokalen Builds geprüft. Das ersetzt keine echten
Workqueue-/USB-Core-Races, Suspend/Resume- oder plattformübergreifenden Tests.
Installation und Aktivierung sind bisher nur auf dem vorhandenen Garuda-System
real geprüft. Sensorwerte bleiben roh; 8192 LSB/g ist experimentell und liefert
keinen Gyroskopmaßstab.
