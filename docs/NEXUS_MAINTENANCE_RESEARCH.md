# Nexus: Stickkalibrierung und Firmwarewartung unter Linux

Stand: 21. Oktober 2026. Statische Untersuchung der bereits vorhandenen
**Nexus 2.1.23.0**. Kein Herstellerprogramm und keine Firmware ausgeführt,
kein Netzwerk-/Gerätezugriff, kein Update oder Eingriff in den laufenden Treiber.
Die Alltagstests der installierten Treiber laufen unabhängig weiter.
Die präzise Gyrokalibrierung bleibt pausiert.

## Ergebnis in verständlicher Form

- **Stickkalibrierung erscheint unter Linux nachbaubar.** Nexus steuert einen
  Kalibriermodus des Geräts und zeigt dessen Rückmeldungen an. Es gibt noch
  keinen vollständig belegten Linux-Befehl. Die spätere
  [Firmwareanalyse](NEXUS_STICK_FIRMWARE.md) findet RAM-Sicherung/-Rückweg und
  asynchrone Speicheraufträge. Der [Speicherbericht](NEXUS_STICK_STORAGE.md)
  verfolgt sie bis zur internen Abschlussmeldung; diese unterscheidet nicht
  alle betrachteten Stopppfade. Die [Fortsetzung zu Status und Laden](NEXUS_STICK_READBACK.md)
  präzisiert den Vertrag: Nexus sendet Finish, die Firmware speichert selbst.
  Eine zusätzliche Speicherquittung ist nicht zwingend für einen Nachbau;
  überprüfte dauerhafte Speicherung und vollständige Rücknahme sind damit
  allerdings nicht nachgewiesen. Ziel der späteren Oberfläche sind zwei sichtbare
  Stickanzeigen, getrennte Fertigmeldungen und Start → Finish oder Exit bei Abbruch.
  Der [Transportbericht](NEXUS_STICK_TRANSPORT.md) ordnet nun den Windows-GIP-
  Provider zu und belegt die unmittelbare native Fehlerprüfung. Ohne Finish
  startet der untersuchte Abschlussweg keine neue Speicherung; automatische
  RAM-Wiederherstellung bei Funkverlust ist damit noch nicht nachgewiesen.
- **Controller- und Dongle-Updates sind technisch plausible spätere Ziele.**
  Paketformate und wesentliche Teile des Windows-Updaters sind bekannt. Ein
  sicher verwendbarer Linux-Updater ist damit noch nicht fertig.
- **Eine hundertprozentige Garantie gegen unbrauchbare Geräte ist nicht
  möglich.** Wiederherstellung nach Stromverlust, Unterbrechung oder falscher
  Gerätezuordnung ist unbewiesen. Ohne belastbaren Wiederherstellungsweg bleibt
  die Schreibfunktion gesperrt; ein erfolgreicher Normalfall genügt nicht.

TMR-Stickkalibrierung und pausierte Gyrokalibrierung sind getrennte Vorhaben.
Die Oberfläche nennt einen allgemeinen Stickpfad; ein eigener TMR-Algorithmus
im PC-Programm ist darin nicht nachgewiesen.

## Quellen und Verfahren

Primärquellen sind die lokal erhaltenen Herstellerdateien, deren SHA256 und
Fundstellen im [Nachweis](evidence/NEXUS_MAINTENANCE_20261021.json) stehen.
Herstellerdateien, vollständige Decompilerausgaben und private Pfade werden
nicht übernommen. Grundlagen sind die bisherigen Berichte zur
[Nexus-Struktur](GAMESIR_NEXUS_RESEARCH.md) und zum
[nativen Kalibrierungspfad](NEXUS_SENSOR_DATAFLOW.md#4-kalibrierung-vom-ui-bis-zur-nativen-transportgrenze).

REA 6.5.0/Ghidra 12.1.4 untersuchten sechs Funktionen der kleinen
`JL_Upgrade_Gip.dll` über den vorhandenen lokalen, netzwerk- und geräteisolierten
Launcher. Alle sechs Läufe bestätigen unveränderte Originale und Arbeitskopien.
Die kritischen Ergebnis-/Warteschleifen wurden zusätzlich mit objdump und
exakten Instruktionsbytes abgeglichen. JavaScript wurde nur als Text gelesen.
Zehn UI-Fundstellen und sechs Instruktionsanker wurden gegen die drei
festgelegten Quelldateihashes geprüft.

Zusätzlich bestehen die Prüfung der neuen Dokumentationslinks und privaten
Kennungen sowie der vorhandene Test für reproduzierbare, ausdrücklich
ausgewählte Quellenarchive einschließlich der neuen Dokumentation. Das sind
Datei-/Dokumentationsprüfungen, keine Kalibrierungs- oder Flashabnahmen.

Adressen unten sind **RVA**, sofern nicht ausdrücklich Dateibytes genannt sind.
DLL-Imagebasis: `0x180000000`. Dekompilierte Argumenttypen und Variablennamen
bleiben Hilfsmittel, keine bestätigten Protokollnamen.

## 1. Was Nexus bei der Stickkalibrierung macht

Vertiefung dieses Abschnitts: [Dialog, automatisches Finish, Abbruchkonflikt
und offene Speichersemantik](NEXUS_STICK_CALIBRATION_FLOW.md). Dort ist jetzt
auch die native Zuordnung zu `G7Pro.Proxy` belegt. Die komplette Laufzeit-
Geräteauswahl, USB-Einbettung und das dauerhafte Speichern bleiben offen.

Der gemeinsame `CalibrationDialog` enthält folgende statisch belegte Folge:

| Phase | Nachweis im Programm | Grenze |
|---|---|---|
| Auswahl | `sticks`, `triggers`, `triggers_sticks` oder `motion` | Stick- und Gyrokalibrierung bleiben getrennt |
| Vorbereitung | Sticks/Trigger unberührt in Ausgangslage; beim Stickpfad Fortschritt bis 100 mit 30-ms-Timer | Etwa drei Sekunden UI-Puffer, keine belegte Gerätemessdauer |
| Start | `calibrate`, `calType:0`, gewähltes `calPart` | Interne Anfrage, kein vollständiges USB-Paket |
| Bewegung | Beide Sticks dreimal am äußeren Rand kreisen lassen | Vorgabe im UI-Text, kein Nachweis der internen Messformel |
| Rückmeldung | `CalibrationStateChanged`, `isCalMode`, getrennte `LS`/`RS`-Flags | Der betrachtete Listener berechnet selbst keine Achsenkorrekturen |
| Abschluss | Bei `sticks` müssen LS und RS gesetzt sein; 510 ms später folgt Schritt 4 mit `calType:1` | In diesem Übergang kein gesondertes Warten auf bestätigte dauerhafte Speicherung |
| Verlassen | Unter anderem beim Verlassen von Schritt 3: `calType:2` | Kein Nachweis, dass Exit bereits geänderte Kalibrierdaten zurücksetzt |

**Finish und Exit enthalten im UI keine erneute `calPart`-Angabe.** Ein Nachbau
darf nicht ungeprüft dieselbe Stickmaske an alle Operationen anhängen.
Fortschrittsanimation, LS/RS-Flags und erfolgreich gespeicherte Kalibrierwerte
dürfen nicht gleichgesetzt werden.

Der bereits belegte native Builder bei RVA `0x198b490` konstruiert drei
Nutzbytes: Marker `0xfe`, unteres Operationsbyte und Teilmaske.
Für `sticks` beträgt diese `0x03`; Enumwerte: Start 0, Finish 1, Exit 2.
Die Weitergabe erfolgt über D4X `SendMessage` mit internem Nachrichtenbyte
`0x0f`. **Das sind keine freigegebenen Gerätebefehle.** USB/GIP-Einbettung,
Antwortzuordnung und Auswahl der konkreten Geräteimplementierung fehlen noch.

### Folgerung und offene Punkte

Die PC-Seite ist hier ein Ablauf- und Statusdialog. Daher erscheint es sinnvoll,
unter Linux die vorhandene Gerätefunktion zu steuern, statt einen eigenen
TMR-Korrekturalgorithmus zu erfinden. Nicht belegt sind:

- Mittelpunkt-/Endpunktberechnung, Kreiskorrektur, Toleranzen und Messdauer;
- Speicherort, Schreibzeitpunkt und Lebensdauer der Kalibrierdaten;
- Verhalten bei Abbruch, Verbindungswechsel oder Stromverlust;
- Auslesen/Sichern/Wiederherstellen des bisherigen Zustands;
- identische Semantik für Standard, WFF, ZZZ, Kabel und Funk.

Eine weitere Verbindung ist sichtbar: Nach `UDiskUpgradeFinished` merkt sich
die UI bei nichtnegativem Ergebnis und `needToCalibrate=true` einen
Kalibrierungsbedarf. Eine nachfolgende Geräteauswahl berücksichtigt diesen
für bis zu fünf Minuten; der dort geöffnete Pflichtdialog wählt
`triggers_sticks`. **Das beweist keine notwendige Kalibrierung nach jedem
Update und keinen Datenverlust**, zeigt aber, dass Wartung und Kalibrierzustand
zusammen betrachtet werden müssen.

## 2. Controller und Dongle: getrennte Firmwarepfade

Die zwölf vorhandenen G7-Pro-UFW-Dateien bleiben getrennt nach PCWireless,
WFF und ZZZ sowie DV/DG und Key/No-Key. Die frühere native Objektzuordnung
stützt DV als Controller und DG als Dongle. Sie erlaubt kein Cross-Flashing.
PID, gleiches Gehäuse oder gemeinsamer Linux-Eingabetreiber reichen nicht als
Update-Kompatibilitätsprüfung.

### Neu mit REA nachverfolgter Standardzweig

`JL_upgradeDeviceByHandle` bei RVA `0x15330` wählt abhängig von einer globalen
Einstellung **`0x14a20` oder `0x17180`**. Dieser Folgepass untersucht vor allem
`0x14a20`. Der andere Zweig und seine tatsächliche Nexus-/Modellwahl sind nicht
vollständig geprüft. Befunde gelten deshalb nicht pauschal für alle Updates.

| Bereich | Statisch nachverfolgte Funktion |
|---|---|
| Informationen anfordern | `0x14a20` ruft `0x130a0` auf; unterscheidet unter anderem KEY- und Abfragefehler |
| Informationen aufbereiten | `0x14330`: codierte Verzeichnisdaten, CRC, `app_dir_head`/`app_dir_head2`, Modus-/Adressfelder |
| Geladene Teilbilder vorbereiten | `0xb3f0`: Cacheauswahl anhand von `0x100`/`0x1000` und Moduswerten; Anpassung von Verzeichnisadressen und CRC |
| Flashbereich bearbeiten | `0x140c0`: Löschen → CRC des gelöschten Bereichs prüfen → Schreiben → CRC der Nutzdaten prüfen |
| Wiederholung | Äußerer Bereichsablauf von `0x140c0` mit höchstens fünf Versuchen; begrenzt nicht alle inneren Transportschleifen |
| Reset/Neuanmeldung | Bedingter Pfad in `0x14a20`: Reset, Schließen, eine Sekunde Warten, bis zu fünf Wiederöffnungsversuche mit weiteren Wartezeiten |
| Abschlussabfrage | `0x13610`, aufgerufen bei `0x151b8`; anschließend Ergebniscallback |

**Präzisierung zum früheren „Firmware-/Gerätevergleich“:** Der Fehlertext nach
einem Fehlschlag von `0xb3f0` bezeichnet einen Mismatch. Die vollständig
betrachtete Funktion belegt vor allem Format-/Cacheauswahl und Adressanpassung,
keinen vollständigen Vergleich von Edition, Hardware-Revision und
Herausgebersignatur. Ob andere Ebenen diesen leisten, bleibt offen.

### Grenzen der Fortschritts- und Fehlerbehandlung

1. **Zeitgesteuerte Anzeige:** Der Webdialog kann Fortschritt aus
   `estimatedDuration` errechnen und bei 99 anhalten. Erst
   `UDiskUpgradeFinished` mit `ret >= 0` schaltet auf Erfolg. Diese Prozente
   sind kein Nachweis tatsächlich geschriebener Bytes.
2. **Innere Warteschleife:** Im Ergebnisabruf `0x13610` wartet ein Fragmentpfad
   1000 ms auf Bestätigung. Bleibt sie aus, springt `0x137b2` zurück zum Senden
   bei `0x13770`. Innerhalb dieser Schleife ist kein Gesamtlimit erkennbar.
   Begrenzungen äußerer Schleifen allein lösen das nicht.
3. **Getrennte Ergebnisse:** Der Abruf kopiert Antwortfeld `+0x14` an den
   Aufrufer und behandelt zusätzliche Antwortdaten mit CRC. Im Aufrufer
   `0x151b8…0x151eb` entscheidet zunächst der Funktionsrückgabewert; bei Null
   folgt ein Callback mit Status 0 und Fortschritt 100, ohne dort das separat
   ausgegebene Feld auszuwerten. Seine genaue Gerätebedeutung bleibt offen.
4. **CRC-Fehlerzweig:** Bei `0x13a0b…0x13a47` führt abweichende CRC der
   zusätzlichen Antwortdaten zu Länge 0; in diesem Zweig bleibt der
   Funktionsstatus 0. Ob übergeordnete Paketprüfungen diesen Fall praktisch
   ausschließen, ist nicht nachgewiesen.

Die letzten beiden Punkte sind **statisch belegte Kontrollflussbefunde mit
offener End-to-End-Bedeutung**, kein reproduzierter Nexus-Fehler auf Hardware.
Keine Aussage, dass ein Gerät dadurch beschädigt wurde oder Nexus bei einer
tatsächlich fehlerhaften Aktualisierung Erfolg gemeldet hat. Ein Linux-Nachbau
darf diese Stellen nicht ungeprüft übernehmen.

## 3. Voraussetzungen für einen schreibenden Linux-Updater

| Nachweis | Aktueller Stand |
|---|---|
| Modell-/Hardware-/Controller-/Dongle-Zuordnung | Unvollständig; Standard und ZZZ getrennt halten |
| Zulässige Versionspaare und Update-Reihenfolge | Offen |
| Offizielle Quelle und Firmwareauthentizität | Dateien vorhanden; CRC und Key-Bezeichnung sind keine Hersteller-Signaturprüfung |
| Vollständige Transport- und Antwortsemantik | Teilweise bekannt; kein validierter Linux-Transfer |
| Adressschutz für Bootloader, Kopplung und Kalibrierdaten | Struktur teilweise verstanden; Schutzwirkung offen |
| Stromverlustfester Commit/Dual-Bank/Recovery | Nicht nachgewiesen; Funktionsnamen reichen nicht |
| Wiederherstellung nach unterbrochenem Löschen/Schreiben, auch ohne normale Firmware | Für Controller und Dongle jeweils offen |
| Erfolg nach Wiederanmeldung | Version, Identität und normaler Betrieb zusammen bestätigen |

Keine Wiederholung von Schreibbefehlen ohne belegte Wiederholbarkeit.
Timeouts und Abbruch sind phasenabhängig: Vor dem Löschen kann ein Vorgang
abgelehnt werden; danach darf „Stopp“ nicht blind mit Stromtrennung oder Reset
gleichgesetzt werden. Ein Wechsel zu xpad repariert keine Firmware.
Unser signierter Linux-Paketkatalog bestätigt ebenfalls nicht automatisch
Echtheit oder Geräteeignung einer Hersteller-Firmware.

## 4. Empfehlung und nächste Reihenfolge

**Beide Funktionen bleiben optionale Userspace-Wartung.** Im Kernel bleibt
der Eingabe-/Sensor-/Haptikbetrieb. Eine spätere Wartung benötigt explizite,
exklusive Übergabe genau eines Geräts durch den Manager und saubere Rückgabe.
Keine Kalibrier-/Flashbefehle im Bootstrap und keine Wartung beim Anstecken.
Das Control Center zeigt die Funktionen weiterhin als geplant.

1. **Stickpfad vervollständigen:** Der Folgepass belegt `G7Pro.Proxy` und
   untersucht Dialog/Abbruch mit 13 reinen Modellfällen. Offen bleiben die
   vollständige Laufzeitzuordnung, D4X/GIP-Rahmen und vor allem Finish/Exit
   im Firmwareempfänger einschließlich Speicher-/Rückbauverhalten. Das Modell
   ist kein ausführbarer Kalibrierungshelfer und keine Hardwareabnahme.
2. **Updater offline absichern:** alternativen Zweig und Modellrouting klären;
   Datei-/Adressprüfer und Antwortzustände ohne Schreibtransport testen.
   Falsche Edition, verkürzte Datei, falsche CRC, fehlende/doppelte/veraltete
   Bestätigung und Reconnect auf ein anderes Gerät müssen blockieren.
3. **Recovery zuerst belegen:** belastbare Wiederherstellungsbelege für beide
   Komponenten beschaffen. Erst danach wären separat freigegebene Laborversuche
   mit wiederherstellbarer Testhardware sinnvoll. Keine Ausfallversuche an den
   normalen Spielgeräten aus diesem Auftrag.

Dieser Arbeitsgang implementiert und aktiviert keine Wartungsfunktion.
Auch ein erfolgreich beobachtetes Windows-Update wäre kein vollständiger
Nachweis für einen Linux-Updater oder dessen Stromausfallsicherheit.
