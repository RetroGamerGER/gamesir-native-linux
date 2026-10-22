# Stickkalibrierung: Übertragung, Abbruch und Verbindungsverlust

Stand: 21. Oktober 2026. Offline-Fortsetzung von
[Dialogablauf](NEXUS_STICK_CALIBRATION_FLOW.md),
[Firmware und Exit](NEXUS_STICK_FIRMWARE.md) sowie
[Status und Laden](NEXUS_STICK_READBACK.md).
[Fundstellen und Quellenhashes](evidence/NEXUS_STICK_TRANSPORT_20261021.json).
Keine Hersteller-App oder Firmware ausgeführt oder emuliert, keine Geräte- oder
Netzwerkzugriffe, keine Änderungen an installiertem Treiber oder System.

**Fortsetzung:** Der [USB-/Funkbericht](NEXUS_STICK_WIRE_PATH.md) verfolgt nun
die zweite Dongle-Queue mit A0-Vorspann bis zum gemeinsamen Controller-
Kalibrierverteiler. Eine ausstehende Kopie im Dongle ist nachgewiesen;
deren Lebensdauer bei Funkverlust und ein automatischer RAM-Rückweg bleiben
offen. Der folgende Bericht bewahrt den vorherigen Untersuchungsumfang.

## Ergebnis

**Nexus schickt Start, Finish und Exit über denselben direkten GIP-Sendeweg.**
Die Firmware erledigt die Kalibrierung und nach Finish das Speichern. Die
Anwendung muss die Kalibrierwerte weder selbst berechnen noch zurückschreiben.
Exit ist die Alternative beim Abbruch, kein obligatorischer Schritt nach Finish.

Der zuvor unbenannte Provider lässt sich jetzt anhand der Objektkonstruktion,
Typinformationen und Zeigerübergabe dem Windows-Interface
`IGipGameControllerProvider` zuordnen. Das schließt eine wichtige Lücke zwischen
Nexus und Windows, aber noch nicht das vollständige USB-/Funk-Framing.

**Ohne Finish wird im untersuchten Stick-Abschlussweg keine neue Speicherung
ausgelöst.** Die vorher gespeicherten Werte bleiben in diesem Pfad erhalten.
Start verändert jedoch bereits Arbeitswerte im RAM. Exit holt bei noch aktiver
Kalibrierung die RAM-Sicherung zurück. Dass Funkverlust automatisch dieselbe
Rückkehr auslöst, ist weiterhin nicht belegt. „Nicht neu gespeichert“ und
„sofort wieder normal benutzbar“ sind verschiedene Aussagen.

Eine zusätzliche Speicherquittung wird nicht zur Pflicht gemacht. Die App kann
den normalen Ablauf abschließen, ohne eine hier nicht vorhandene Quittung zu
erfinden; sie darf nur keinen tatsächlich ungeprüften Rücklesevergleich behaupten.

## 1. Weg der drei Anfragen

Alle PC-Codeadressen sind RVAs zur jeweiligen DLL-Basis `0x180000000`.
Firmwareadressen sind Dateioffsets in DV209. Die unveränderten Originaldateien,
vollständigen Disassemblierungen und privaten Arbeitsverzeichnisse bleiben
außerhalb von Git.

| Grenze | Belegter Inhalt / Entscheidung |
|---|---|
| Kalibrierdialog | Start: `calType=0, calPart=sticks`; Finish: `calType=1`; Exit: `calType=2` |
| JavaScript `deviceReq` | Liest für jeden Aufruf erneut die aktuelle Gerätekennung |
| `commonReq` / WebView | Sendet `requestType`, `deviceId`, `payload` über `postMessage`; kein anfragespezifisches Promise oder Rückgabeergebnis in diesen Helfern |
| G7Pro.Proxy `0x198b490` | Baut drei interne Nutzbytes, Typ `0x0f` und Direktflag `+0x0c=1` |
| Sendeservice `0x187354f…0x1873599` | Nimmt den Direktzweig, holt das Geräteinterface und ruft `0x148ff20` auf |
| Native Projektion | Übergibt Arraylänge, Nutzdatenzeiger und Typ an Slot 13 von ID4XDevice |
| D4X `0x1be0…0x1c0f` | Reicht die Argumente an Slot 6 des gespeicherten GIP-Providers weiter |

Die drei Nutzinhalte an dieser **internen Providergrenze** sind:

| Operation | Nutzinhalt | Länge | Typ |
|---|---|---:|---|
| Start, beide Sticks | `fe 00 03` | 3 | `0x0f` |
| Finish | `fe 01 00` | 3 | `0x0f` |
| Exit | `fe 02 00` | 3 | `0x0f` |

Dies sind keine vollständigen USB-Pakete und kein freigegebener Sendebefehl.
Der Firmwareempfänger erwartet zusätzlich einen Kopf und liest die Nutzbytes
an Position 4–6. Dessen Erzeugung, Sequenz-/Bestätigungsregeln, Endpunktwahl und
die Weiterleitung durch den Funkempfänger sind mit diesem Befund nicht vollständig
geschlossen. Auch die Auswahl der konkreten Laufzeitinstanz für Standard, ZZZ,
Kabel und Funk muss jeweils gelten; die gemeinsame Methode allein reicht nicht.

Der andere Zweig ab `0x187359a` behandelt die interne Warteschlange und
Duplikatprüfung. Kalibrierpakete nehmen ihn wegen ihres Direktflags nicht.
Das bedeutet weder „keine Warteschlange irgendwo im System“ noch garantierte
Reihenfolge unabhängig eingehender WebView-Aufträge. Im begrenzten Direktzweig
und D4X-Wrapper ist keine Wiederholung des Kalibrierbefehls enthalten.

## 2. Der Provider ist genauer zugeordnet

Die endgültige D4X-Objekttabelle liegt bei `0x8940`. Das ID4XDevice-Interface
liegt **16 Bytes innerhalb** des vollständigen Objekts und verwendet `0x8868`.
Die RTTI-Objektbeschreibung bestätigt diesen Versatz. Dadurch bedeutet der
SendMessage-Zugriff `[Interface+0x70]` tatsächlich `[Objekt+0x80]`.
`Objekt+0x70` ist dagegen ein Lock; die Bezugspunkte dürfen nicht vermischt werden.

Die Konstruktion `0x4822…0x483a` fordert per QueryInterface die IID
`dbcf1e19-1af5-45a8-bf02-a0ee50c823fc` an und übergibt das Ergebnis an Slot 9
der vollständigen Objekttabelle. Dieser zeigt auf `0x17c0`; bei `0x1801` wird
genau dieses Interface in `Objekt+0x80` gespeichert. Der RTTI-Basisklasseneintrag
bezeichnet den zugehörigen `CustomTypedGameControllerBase` ausdrücklich mit
`IGipGameControllerProvider` und `IGipGameControllerInputSink`.

Der Aufruf bei `0x1c06` hat im x64-ABI die Argumentfolge:

`Provider, 0, Nachrichtentyp 0x0f, Länge 3, Nutzdatenzeiger`

Der zweite Nullparameter erhält hier keinen ungeprüften Enum-Namen. Die
Interfacezuordnung ist durch Typ- und Datenfluss gestützt; die Implementierung
des Windows-Providers selbst wurde nicht lokal gefunden oder ausgeführt.

Die lokale Wine-Referenz für `IGameControllerInputSink` bestätigt die Reihenfolge
`OnInputResumed`/`OnInputSuspended`. Beide entsprechenden D4X-Slots zeigen auf
`0x1860`, einen Erfolg liefernden Stub ohne weiteren Aufruf. **Diese beiden
Callbacks senden kein Exit.** Das ist kein Beweis, dass Geräteentfernung nur
diese Callbacks auslöst oder dass höhere Nexus-Schichten niemals auf Verlust
reagieren. Die lokale Wine-Datei definiert den GIP-Provider nicht; dafür dient
sie ausdrücklich nicht als unabhängiger vollständiger SDK-Nachweis.

## 3. Übertragungsfehler und Abschlussmeldung

D4X gibt das Providerergebnis im Rückgaberegister unverändert zurück. Die
native Nexus-Projektion prüft bei `0x1490087…0x1490092` dessen Vorzeichen und
ruft bei negativem HRESULT einen Fehlerhelfer auf. Die Behauptung „Nexus prüft
überhaupt keinen Sendefehler“ wäre daher falsch.

Das ist die unmittelbare Rückmeldung des Windows-Aufrufs. Sie ist keine
zusätzliche Meldung „Kalibrierwerte dauerhaft gespeichert“. Ebenso ist noch
keine vollständige Kette von diesem Fehlerhelfer zu einer passenden Fehlermeldung
im Kalibrierdialog belegt. Dessen JavaScript-Aufrufe warten nicht auf ein solches
Ergebnis; Schritt 4 fordert Finish an und zeigt die Erfolgsseite.

Bei Verbindungsverlust muss außerdem unterschieden werden:

- **Finish noch nicht angefordert:** Der untersuchte Abschlussweg schreibt
  keine neuen Stickwerte. Die RAM-Kalibrierung kann trotzdem noch aktiv sein.
- **Finish angefordert, Zustellung unklar:** Ein verlorener Rückkanal beweist
  nicht, dass der Controller den Befehl nicht bekommen hat. Nicht blind wiederholen.
- **Finish verarbeitet und Daten übernommen:** Exit ist kein belegter Rückbau
  dieses neuen Zustands oder eines schon eingereihten Speicherauftrags.

## 4. Abbruch und Verlust am Dialogrand

| Situation | Statisch belegt | Noch offen / Konsequenz |
|---|---|---|
| Schließen während der Messung, Gerät erreichbar | Dialog fordert Exit an; Firmware hat einen RAM-Rückweg für aktive Sticks | Vollständige PC→Gerät-Zustellung muss gelten |
| Beide Sticks fertig, dann Schließen innerhalb der 510 ms | Exit wird angefordert, geplanter Finish-Callback bleibt bestehen | Bei vollständig verarbeitetem Exit verhindert das gelöschte Fertigbit ein späteres Speichern in diesem seriellen Pfad; kein nachgewiesener Geräteschaden |
| Geräteauswahl verschwindet vor Start/Finish/Exit | `getCurrentDevice` kann nichts finden; `.deviceId` kann dann nicht gelesen werden | Der geplante Schritt ist damit nicht automatisch sauber abgebrochen oder zurückgenommen |
| Gerät weg, UI hält noch eine Auswahl | Request kann bis zum nativen Provider gelangen | Dessen tatsächliches Verlust-/Fehlerverhalten ist nicht mit Hardware geprüft |
| Auswahl wird durch anderes Gerät ersetzt | Jeder Request liest erneut die aktuelle Kennung | Keine instanzgebundene Kalibriersitzung an diesem UI-Rand nachgewiesen |
| Nur Funk weg, Dongle bleibt | Keine vollständige automatische Exit-/Restore-Kette belegt | USB-Geräteabwesenheit und Funkverlust nicht gleichsetzen |
| Controller verliert Strom | RAM-Sicherung ist kein dauerhafter Wiederherstellungsspeicher | Späteres Laden alter Records ist bekannt; vollständiger Neustartablauf in diesem Fehlerfall bleibt unbelegt |

Schließen löscht weder den noch ausstehenden Abschluss-Timer noch zwingend die
Vorbereitungsaktion. Der Komponenten-Abbau löscht das Vorbereitungsintervall,
sendet aber selbst kein Exit. Diese bereits belegten UI-Befunde bleiben bedingte
Ablaufgegenbeispiele, keine ausgeführten Nexus- oder Hardwarefehler.

### Weitere Aufrufe der RAM-Wiederherstellung

Die Suche nach der bereits geprüften relativen Call-Form findet in DV209 für
den linken Rückweg `0x19b6` die Stellen `0x2208` und `0x54fe8`; für den rechten
Rückweg `0x1a80` die Stellen `0x2226` und `0x551f2`. Die ersten gehören zu Exit.
Die beiden zusätzlichen Aufrufe liegen hinter Schleifen über acht Tabellenwerte
und einer Prüfung der nach rechts um 13 Bit verschobenen Werte. Das ist ein
weiterer bedingter Rückweg, **kein belegter Funkverlust-Handler**.

Zwei begrenzte statische Dekodierungen ergeben 128 Instruktionsdatensätze ohne
Dekodierabbruch. Das beweist weder vollständige Funktionsgrenzen noch die Herkunft
sämtlicher Registerwerte. Die Call-Suche berücksichtigt das bekannte RAM-Suffix-
Adressmodell, aber keine beliebigen indirekten Aufrufe oder unbekannten Formen.
Aus dem fehlenden weiteren Treffer wird keine Garantie „es gibt keinen anderen
Rückweg“ abgeleitet. Der Decoder wurde nicht verändert.

## 5. Folgerung für die spätere Linux-Oberfläche

Das gewünschte einfache Bedienmodell bleibt erhalten: **Start, Sticks bewegen,
Fertigmeldung der Firmware, Finish — oder Abbrechen mit Exit.** Zwei sichtbare
Stickpositionen und die vereinbarte blaue Spur/grüne Fertiganzeige genügen.

Intern braucht die Sitzung eine feste Geräteinstanz. Abbruch und Verlust müssen
ausstehende Start-/Finish-Aktionen ungültig machen. Exit darf bei Abbruch nur an
dieselbe noch erreichbare Instanz gehen; keine nachträgliche Zustellung an ein
neu verbundenes Gerät und keine automatische neue Kalibrierung. Bei Verlust
wird die Bedienung angehalten und der ungeklärte Ausgang verständlich angezeigt.
Das ist eine Anforderung, keine bereits eingebaute Linux-Schreibfunktion.

**Nächster gezielter Schritt:** Den Provider-Nutzinhalt mit vorhandenen
Kalibriermitschnitten bzw. dem Firmware-/Dongle-Empfänger verbinden; den
Funkverlustpfad zu aktivem Kalibrierzustand/RAM-Restore eingrenzen und prüfen,
ob normale Stickpositionsmeldungen während der Kalibrierung verfügbar bleiben.
Keine neue Geräteaufnahme ist mit diesem Forschungsstand freigegeben.
Der separate Firmware-Updater behält seine eigenen Integritäts-/Recovery-Ziele.

## 6. Offline-Prüfung

Vier Nexus-Quellenhashes, 28 native Instruktionsanker, elf JavaScript-Fundstellen,
RTTI-/VTable-/IID-Verknüpfungen und acht Firmwareanker wurden geprüft.
20 Mutationskontrollen erkennen veränderte Providerkennung oder Aufrufziele.
Die Firmwarequelle, Analysekopien und der Decoder blieben unverändert.

Das bestehende, selbst geschriebene Dialogmodell bekommt drei Gegenbeispiele:
Geräteverlust vor verzögertem Start, vor verzögertem Finish und vor Abbruch mit
noch ausstehendem Finish. Alle **16 Modelltests** bestehen. Sie führen keine
Herstellerlogik aus, bilden keine Firmware nach und beweisen keine tatsächliche
Vue-/Windows-Zustellung. 337 lokale Dokumentationslinks, Privatdaten und
Projektprüfsummen wurden geprüft; der reproduzierbare Quellenarchiv-Test besteht.
