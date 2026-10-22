# Nexus-Stickkalibrierung: Abschluss, Speichern und Abbruch

Stand: 21. Oktober 2026. Ausschließlich statische Untersuchung von Nexus
2.1.23.0 und ein selbst geschriebenes Offline-Ablaufmodell. Keine Ausführung
der Hersteller-App oder Firmware, keine Geräte-/Netzwerkzugriffe und keine
Änderung des laufenden Treibers. Präzise Gyrokalibrierung bleibt pausiert.

## Ergänzung: Firmware-Fortsetzung

Die [nachfolgende Firmwareanalyse](NEXUS_STICK_FIRMWARE.md) präzisiert die unten
noch offenen Fragen: RAM-Sicherung und bedingter Exit-Rückweg sind gefunden,
Finish führt über Flags und einen späteren Verbraucher zu Speicheraufträgen.
Die dauerhafte Schreibbestätigung bleibt offen. Nach vollständig verarbeitetem
Exit verhindert das gelöschte Fertigbit im untersuchten seriellen Stickpfad ein
Speichern durch verspätetes Finish; der UI-Konflikt allein beweist keinen Schaden.
Die folgende Darstellung behält ihren ursprünglichen PC-seitigen Nachweisumfang.

**Aktueller Stand:** [Status und Laden](NEXUS_STICK_READBACK.md) präzisiert
Finish als Anforderung an die firmwareeigene Speicherung; eine separate
Speicherquittung ist keine neue Pflicht. Der
[Transportbericht](NEXUS_STICK_TRANSPORT.md) ordnet den D4X-Provider zu und
unterscheidet RAM-Rückweg, verzögerte UI-Aktionen und Verbindungsverlust.
Die folgenden damaligen Offenpunkte zum Speicherpfad sind in diesem historischen
Kontext zu lesen. Das ergänzte Dialogmodell umfasst inzwischen 16 Tests.

## Ergebnis

Der **Dialogablauf bis zur nativen Sendegrenze** ist nachvollzogen:
Auswahl → unberührt lassen → Start → beide Sticks kreisen → Statusmeldungen
→ automatischer Finish-Aufruf → Erfolgsseite → Fenster schließen.

**Noch nicht vollständig geklärt ist das Speichern im Controller.** Nexus
zeigt Erfolg, ohne in diesem Dialog auf eine gesonderte Speicherbestätigung
zu warten. „Exit“ ist als Anfrage zum Verlassen vorhanden; eine Rückkehr zu
alten Kalibrierwerten ist damit nicht bewiesen. Ein vollständiger, gefahrlos
benutzbarer Linux-Kalibrierablauf ist deshalb noch nicht freigegeben.

Die vertiefte Untersuchung findet außerdem einen **statischen Abbruchkonflikt**:
Ein bereits geplanter Abschluss wird beim Schließen nicht entfernt. In unserem
isolierten Ablaufmodell kann dadurch auf `Exit` noch `Finish` folgen. Das ist
kein an der Hersteller-App oder Hardware reproduzierter Fehler und kein Beleg
für beschädigte Kalibrierdaten. Es ist ein konkreter Grund, die fremde
Ablaufsteuerung nicht unverändert nachzubauen.

## Quellen und Nachweisgrenzen

[Dateihashes, Bytepositionen und native Fundstellen](evidence/NEXUS_STICK_FLOW_20261021.json)
identifizieren vier lokal vorhandene Originaldateien. 19 JavaScript-Fundstellen,
sieben native Instruktionsanker, drei benannte Methoden-/Typzuordnungen und
eine REA-Funktionsanalyse wurden geprüft. Herstellerquellen und vollständige
Dekompilate bleiben außerhalb des Repositorys.

REA 6.5.0/Ghidra 12.1.4 lief über den vorhandenen lokalen, netzwerk- und
geräteisolierten Launcher. Original und Arbeitskopie der untersuchten DLL
blieben unverändert. REA bestätigt den indirekten Aufruf, löst aber dessen
Ziel nicht auf. Ein erfolgreich beendeter Analyselauf ersetzt diesen Nachweis
nicht. JavaScript wurde ausschließlich als Text gelesen.

Adressen unten sind RVA zur DLL-Basis `0x180000000`. Dateioffsets im JSON sind
nullbasierte **Bytes**, keine Zeichenpositionen im mehrsprachigen JavaScript.
Grundlagen: [Wartungsübersicht](NEXUS_MAINTENANCE_RESEARCH.md) und
[bisheriger nativer Pfad](NEXUS_SENSOR_DATAFLOW.md#4-kalibrierung-vom-ui-bis-zur-nativen-transportgrenze).

## 1. Vollständiger beobachteter Dialogablauf

| Schritt | UI und Auslöser | Interne Wirkung / Grenze |
|---|---|---|
| 0: Auswahl | „Sticks“ auswählen | Setzt `calPart=sticks`, wechselt zu Schritt 1, löscht beim Eintritt in 0 alte Erfolgsflags |
| 1: Vorbereitung bestätigen | Sticks/Trigger nicht berühren; weiter | Noch kein Kalibrierbefehl; „Zurück“ wechselt zu 0 |
| 2: Ruhepuffer | Fortschrittszähler mit 30-ms-Intervall | Nach Erreichen von 100 folgt Schritt 3 und `Start`; ideal etwa 3,03 s, unter Last länger. Das ist UI-Zeit, keine belegte Messdauer im Sensor |
| 3: Kalibrieren | Laut Anleitung beide Sticks dreimal am äußeren Rand kreisen | Wartet auf `CalibrationStateChanged` mit `isCalMode=true`; übernimmt LS/RS getrennt |
| 3: beide fertig | `LS && RS` wird wahr | Plant nach 510 ms einen Schrittwechsel; kein eigener Speicherdialog |
| 4: Abschluss | Schrittwechsel nach dem Timer | Ruft sofort `Finish` auf und zeigt „Calibration Successful“; kein Warten auf separaten Speichernachweis im Dialog |
| 4: Fertig-Knopf | Benutzer schließt die Erfolgsseite | Ändert nur die Sichtbarkeit; sendet keinen zweiten Finish-Aufruf |

Die 510 ms sind eine UI-Verzögerung, keine nachgewiesene Mindestzeit für einen
Flash-Schreibvorgang. Ein einzelner fertiger Stick reicht nicht. Wiederholte
identische Erfolgsflags lösen nicht erneut den Watcher aus; ein erneuter
Wechsel von unvollständig zu vollständig kann aber einen weiteren Timer planen.
Der Abschluss-Callback überprüft die Flags beim Ablauf nicht erneut.

Der Pflichtdialog nach bestimmten Firmwareupdates verwendet denselben Ablauf,
wählt aber `triggers_sticks`; dann müssen LT, RT, LS und RS gesetzt sein.
Das bedeutet nicht, dass jeder Firmwareupdate die Kalibrierung löscht.
Der getrennte `motion`-Zweig ist keine Grundlage für die Stick-Speichersemantik.

## 2. Weg zum Gerät und tatsächliche Reichweite des Nachweises

1. `deviceReq` liest bei **jedem** Aufruf die aktuell ausgewählte `deviceId`.
   `commonReq` übergibt Anfrageart, Gerätekennung und Nutzdaten an WebView.
   Der Dialog hält keine eigene feste Gerätekennung für die gesamte Sitzung.
2. Native Metadaten ordnen den `Calibrate`-Methodenrecord bei Datei `0x99882d`
   nun ausdrücklich `HJC.GameSir.Nexus2_0.Core.Devices.G7Pro.Proxy` zu
   (Typindex `0x903`, EEType-RVA `0xad4b0`). Derselbe Methodenkörper
   `0x198b490` ist auch T3Pro.Proxy und T7ProW.Proxy zugeordnet.
   Das Produktobjekt bei `0x118c125…0x118c16e` verknüpft die Literale
   `G7 Pro XBox`/`G7Pro` mit dem G7Pro-Proxytyp.
3. Der Builder setzt einen internen Drei-Byte-Inhalt aus Marker `0xfe`,
   unterem Operationsbyte und Teilmaske zusammen. Die native Enum
   `CalibrationOpration` bestätigt Start=0, Finish=1, Exit=2; `sticks`
   entspricht Maske `0x03`. Fehlende/leere Teilangabe nimmt den Defaultzweig
   mit Nullmaske. Die UI lässt `calPart` bei Finish und Exit weg.
4. Das interne Paket erhält Nachrichtentyp `0x0f` und den direkten Sendepfad
   (`+0x0c=1`, `+0x0d=0` nach vollständiger Konstruktion).
   `0x18733b0` führt über `0x148ff20` zu D4X `SendMessage`.
5. Die D4X-Funktion `0x1be0…0x1c0f` reicht Kennung, Länge und Zeiger an ein
   darunterliegendes Interface weiter (`+0x70`, virtueller Slot `+0x30`,
   Aufruf bei `0x1c06`). In diesen 47 Bytes gibt es keine Warte-/Prüfschleife
   für eine bestätigte Speicherung. Die REA-Analyse lässt das indirekte Ziel
   ausdrücklich unaufgelöst; ihr geratenes `void` ist keine verifizierte ABI.

**Diese internen Bytes sind keine Anleitung zum Senden eines USB-Pakets.**
Das vollständige Windows-Provider-/GIP-Framing und die tatsächlich gewählte
Laufzeitinstanz sind noch offen. Die nun belegte G7Pro-Methodenzuordnung
beseitigt die frühere reine Namensvermutung, aber beweist keine identischen
Kalibrier-/Speicherregeln für Standard, ZZZ, WFF, Kabel und Funk.

Der Rückmeldepfad bei `0x198a8d0` vergleicht Modus und Fertigmaske mit dem
vorherigen Zustand. Bei Änderung baut er `CalibrationStateChanged` mit
Gerätekennung, `isCalMode = (Status != 1)` und fünf Bit-Flags auf.
Das ist eine Statusbenachrichtigung, keine nachgewiesene dauerhafte
Speicherquittung. Die UI ignoriert Ereignisse mit `isCalMode=false`, statt
damit einen bestätigten Abschluss oder Abbruch zu verwalten.

## 3. Was „Speichern“ hier nachweislich bedeutet

| Beobachtung | Was daraus folgt | Was nicht daraus folgt |
|---|---|---|
| Beide Sticks melden fertig | UI-Bedingung für automatisches Finish erfüllt | Daten dauerhaft gespeichert oder nach Neustart gültig |
| Finish wird angefordert | PC stößt den Abschluss der Geräteoperation an | Zeitpunkt, Speicherbereich und atomare Speicherung bekannt |
| Erfolgsseite wird angezeigt | UI hat Schritt 4 erreicht | Antwort des Geräts auf Finish geprüft |
| Eigener `saveProfile`-Pfad existiert | Deadzones, Kurven und Profile werden über einen anderen UI-Pfad gespeichert | Stickkalibrierung benötigt dasselbe Profil-Speichern |
| Exit wird angefordert | Ein eigener Verlassenspfad ist vorhanden | Alte Mittel-/Endpunkte wiederhergestellt |

Im betrachteten Kalibrierdialog gibt es keinen Aufruf von `saveProfile`.
Die PC-Seite sammelt dort auch keine Zahlenreihe für einen eigenen
TMR-Korrekturalgorithmus. Es bleibt möglich, dass Firmware schon während der
Messung, erst bei Finish oder zu einem anderen Zeitpunkt speichert. Weder
„Finish speichert sicher“ noch „Exit verwirft sicher“ ist bisher belegt.

## 4. Abbruch und Unterbrechung

| Situation | Statisch sichtbare Reaktion |
|---|---|
| Schließen in Schritt 0 oder 1 | Kein Exit, da noch kein Start aus diesem Ablauf |
| Schließen in Schritt 3 | Sichtbarkeits-Watcher ruft Exit auf; Schritt und geplanter Abschluss bleiben erhalten |
| Rückwärtswechsel aus Schritt 3 | Schritt-Watcher ruft Exit auf |
| Schließen in Schritt 4 | Nur Fenster schließen; Finish war bereits angefordert |
| Schritt 2 | Schließen-Schaltfläche ausgeblendet; allgemeiner Gamepad-Cancel von BaseDialog prüft dieses Flag jedoch nicht |
| Komponente zerstört | Intervall wird gelöscht, Ereignislistener werden entfernt; dieser Hook sendet selbst kein Exit |
| Gerät verschwindet / Auswahl wechselt | BaseDialog bietet eine optionale Schließfunktion, Standard false; CalibrationDialog setzt sie nicht. Andere übergeordnete Reaktionen sind damit nicht ausgeschlossen |

BaseDialog und CalibrationDialog abonnieren beide die Gamepad-Cancel-Ereignisse.
Der Eventbus läuft rückwärts durch die Listener und beendet bei `false` die
Weitergabe. Die allgemeine BaseDialog-Behandlung ist daher bei der Bewertung
mitzulesen; die spezielle Zurück-Logik des Kalibrierdialogs allein beschreibt
nicht jeden erreichbaren Schließpfad. Die genaue Desktop-Interaktion wurde
nicht ausgeführt.

### Nachgewiesene Lücke am verzögerten Abschluss

Voraussetzung: Die Komponente bleibt gemountet, wie in den gefundenen
Eltern-Renderpfaden, und die folgenden UI-Ereignisse werden einzeln zugestellt:

1. In Schritt 3 werden beide Erfolgsflags wahr; ein 510-ms-Callback wird geplant.
2. Vor dessen Ablauf wird der Dialog geschlossen. Der Watcher fordert Exit an.
3. Der Callback läuft trotzdem und erhöht Schritt 3 auf 4.
4. Der Schritt-Watcher fordert Finish an, obwohl der Dialog geschlossen ist.

Die Referenz auf diesen Timeout wird nicht gespeichert, beim Schließen nicht
gelöscht und im Callback nicht gegen Sichtbarkeit, Schritt oder Geräteidentität
geprüft. Auch ein später wieder falsches Erfolgsflag verhindert den bereits
geplanten Schrittwechsel nicht. Dies ist ein konkreter Kontrollflussbefund;
welche Auswirkung `Exit → Finish` in der Firmware hätte, ist unbekannt.

Weitere bedingte Folgen am untersuchten UI-Rand:

- Wird Schritt 2 verborgen, läuft sein Intervall weiter, solange die Komponente
  erhalten bleibt. Start kann dann erst nach dem Schließen angefordert werden.
- Ein Rückwärtswechsel auf Schritt 1 während des Abschluss-Timers kann durch
  dessen späteres Inkrement erneut Schritt 2 und die Vorbereitung erreichen.
- Der IPC-Verteiler und der betrachtete Kalibrierlistener filtern
  `CalibrationStateChanged` nicht nach `deviceId`. Eine am Rand zugestellte
  fremde Fertigmeldung kann die Flags beeinflussen. Ob der native Produzent
  in der tatsächlichen Geräteauswahl solche Ereignisse liefert, ist offen.
- Wechselt die aktuelle Auswahl zwischen Start und Finish/Exit, wird die neue
  Kennung gelesen. Fehlt die Auswahl ganz, ist das keine bestätigte Rückgabe.
  Die Erreichbarkeit solcher Gerätewechsel im echten Modalablauf bleibt offen.

## 5. Offline-Gegenprüfung und Konsequenz für Linux

Das eigene Modell `tests/nexus_calibration_flow_model.py` bildet nur die hier
beschriebenen Übergänge und Anfragen ab. Es enthält keinen Gerätetransport,
keine echten Timer, keinen Herstellerquellcode und keine Speichersimulation.
`tests/test_nexus_calibration_flow_model.py` prüft **13 Fälle**: Normalabschluss,
ein fertiger Stick, wiederholte Meldung, Schließen vor/nach Start, Abschluss
nach Exit, zurückfallende/inaktive Flags, verborgene Vorbereitung, Zurück im
Zeitfenster, fremde Meldung, Gerätewechsel/-verlust und Destroy-Aufräumung.

Alle bestehen. Das bestätigt die Gegenbeispiele im expliziten Modell, nicht
das Laufzeitverhalten von Vue, Windows oder Firmware. Die Quellanker wurden
zusätzlich gegen die Originaldateien geprüft. Dokumentationslinks,
Privatdatenprüfung und der reproduzierbare Quellenarchiv-Test gehören zur
lokalen Abschlussprüfung; keine Hardwareabnahme wird daraus abgeleitet.

Für einen späteren Linux-Nachbau ergeben sich konkrete Anforderungen:

1. Eine Sitzung an genau eine Geräteinstanz binden; fremde/veraltete Meldungen
   zurückweisen, alle verzögerten Aktionen an diese Sitzung koppeln.
2. Abbruch invalidiert alle ausstehenden Start-/Finish-Aktionen. Schließen
   darf keine verborgenen Schreibaktionen hinterlassen.
3. „Angefordert“, „Gerät hat bestätigt“ und „dauerhaft gespeichert“ getrennt
   behandeln. Keine Erfolgsseite allein aufgrund von LS/RS oder Timerablauf.
4. Exit nur gemäß belegter Firmwaresemantik verwenden. Bei Disconnect oder
   fehlender Bestätigung den Ausgang als unbekannt melden; keine blinde
   Wiederholung und kein behauptetes Wiederherstellen alter Werte.
5. Zuerst Speicher-/Abbruchsemantik und Providerframing weiter belegen.
   Bis dahin keine Kalibrierbefehle in Kernel, Manager oder Control Center.

Nächste gezielte Forschungsfrage ist der Firmwareempfänger der drei Operationen:
Welche Änderungen erfolgen bei Start, Finish und Exit; wo werden Mittel- und
Endpunkte abgelegt; kann man den alten Zustand lesen und wiederherstellen?
Der App-Dialog allein beantwortet das nicht. Das bekannte Firmware-Update-
Recovery-Problem bleibt ein eigener, weiterhin offener Meilenstein.
