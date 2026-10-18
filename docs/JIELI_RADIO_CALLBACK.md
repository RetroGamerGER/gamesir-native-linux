# Jieli: Registrierung des Funktransport-Callbacks

Stand: 18. Oktober 2026. Fortsetzung des
[A2-/Dongle-Datenflusses](JIELI_WIRELESS_DATAFLOW.md). Nur lokale statische
Analyse der bereits gehashten App-Kopien und gespeicherten Referenzen.
Keine Zielausführung oder Emulation, Netzwerk-/Hardwarezugriffe,
Installation oder Treiberänderung. Gyrokalibrierung bleibt pausiert.

**Fortsetzung:** [Sendepfadauswahl und Dongle-Empfang](JIELI_LINK_ROUTING.md)
ordnet inzwischen die beiden Suchverfahren für die Verbindungskennung und die DG-Kette vom
aufbereiteten Deskriptor bis zum A2-Parser zu. Untere Funkzustellung und
bedingte Callback-/Verarbeitungsschritte bleiben offen. Dieser Bericht
dokumentiert den vorherigen Nachweisstand.

## Ergebnis

Die zuvor fehlende **Registrierung des Controller-Transport-Callbacks ist
statisch zugeordnet**. Sie erfolgt über eine Funktionstabelle, nicht durch
einen direkten Aufruf des Setters. Deshalb blieb die vorige Suche nach
direkten CALLs zum Setter leer.

Der untersuchte Initialisierungspfad wählt die Tabelle `H4_Controller`,
startet einen Worker und registriert über Tabellenslot `+0x10` den Callback
bei Dateioffset `0x32090` (DV209). Der bekannte Rahmen-Wrapper ruft genau
diesen gespeicherten Zeiger mit Operationsargument **2**, Rahmenzeiger und
Länge auf. Der Callback reicht den Rahmen abhängig von einer
Verbindungszuordnung an einen von zwei tieferen Pfaden weiter.

**„Aktiv“ bleibt eine Laufzeitfrage:** Belegt ist, welchen Callback dieser
Initialisierungspfad registriert. Nicht beobachtet wurden seine tatsächliche
Ausführung, erfolgreiches Task-Scheduling, der spätere Inhalt des
Callback-Speichers oder die erfolgreiche Funkzustellung beim Capture.
Kein statischer Tabellenfund ersetzt diese Nachweise.

Die beiden offenen Decoderoperationen sind weiter eingegrenzt, aber weiterhin
nicht unabhängig als genaue ISA-Form validiert. Es gibt keinen neuen
bestätigten USB-Gyrofaktor und keine Änderung der Sensorausgabe.

## 1. Adressen und Callback-Kette

Alle Codepositionen sind **Dateioffsets in DV209**, soweit nicht ausdrücklich
als Speicheradresse bezeichnet. Quellen/Hashes und die getrennten Flash-/
RAM-Adressmodelle stehen in den verlinkten Vorgängerberichten.

Für die hier gespeicherten Textzeiger gilt das geprüfte Modell
`Dateioffset = Textzeiger − 0x01e000c0`. Beispiel: `0x01e31f26` bezeichnet
`0x31e66`, **nicht** `0x31f26`. ROM-CALLs und der RAM-Suffix verwenden ihre
eigenen, bereits dokumentierten Modelle; kein globales Adressmaskieren.

| Station | Code-/Datenfundstelle | Nachgewiesene Beziehung |
| --- | --- | --- |
| Startpfad | `0x104c4` → `0x31b84` | Direkter Aufruf der Transportinitialisierung; zwei weitere Aufrufer von `0x104a8` bei `0x1719e`/`0x171a6` mit unterschiedlichen Startargumenten |
| Tabelle auswählen | `0x31b92`–`0x31b9e` | Zeiger `0x01e319e4` auf Tabelle bei `0x31924` in Speicheradresse `0x21e5c` ablegen |
| Worker vorbereiten | `0x31ba0`–`0x31bb0` | Entry-Zeiger `0x01e31f26` → `0x31e66`, Argument null und Name `btctrler` an Task-Helfer `0x4558e` |
| Setter auswählen | `0x31e98`–`0x31e9a` | Geladene Tabelle, Slot `+0x10`, Nullprüfung |
| Callback registrieren | `0x31e9c`–`0x31ea2` | Callback-Zeiger `0x01e32150` → `0x32090` als Argument; indirekter Aufruf des Tabellenslots |
| Setter implementieren | Tabelle `0x31934` → `0x32018`; Store `0x3201e` | Übergebenen Zeiger in Speicheradresse `0x21e64` speichern |
| Rahmen abgeben | `0x1b422` → `0x31b74` | Bereits untersuchter Rahmenkonstruktor ruft Transport-Wrapper |
| Callback aufrufen | `0x31b74`–`0x31b82` | Zeiger aus `0x21e64` laden, Argumente `2, Rahmen, Länge`, indirekter Sprung |

Der Task-Helfer vergleicht bei `0x455a2` den Namen mit einer lokalen Tabelle
und reicht bei passendem Eintrag Entry und Taskparameter an einen unteren
Helfer weiter. Das stützt die Worker-Registrierung; Erfolg und Scheduling
sind nicht gemessen. Der obere Startpfad prüft bei `0x104d0` einen weiteren
Helferrückgabewert. Seine vollständige Ereignis-/Startauswahl bleibt außerhalb
dieses begrenzten Nachweises.

Die Tabelle ist keine beliebige Zeigeransammlung: Ihr Name, ihre Auswahl,
der genaue Slotzugriff, der Setter und dessen Verbraucher passen zusammen.
Auch die weiteren exakt gefundenen Referenzen auf `0x21e5c` bei `0x35298`
und `0x35478` sind **Leser**, keine hier gefundenen alternativen Setter.
Das ist keine globale Ausschlussprüfung aller indirekten Speicherzugriffe.

Die entsprechenden Tabellen-/Setter-/Callback-Beziehungen wurden zusätzlich
in **DV515 und DV608** geprüft; die untersuchten Code-/Tabellenpositionen
liegen dort jeweils `0xe0` höher. Die beiden RAM-Speicheradressen bleiben
gleich. Daraus folgt keine vollständige Gleichheit der drei Firmwares.

## 2. Datenrichtung und untere Sendepfade

Die Tabelle enthält bei `+0x18` einen anderen Handler, in DV209 `0x32026`.
Er verarbeitet u. a. Operationswerte 2 und 4 und übergibt Nachrichten an
`btstack`. Er darf nicht mit dem registrierten Callback `0x32090` verwechselt
werden. Die Richtungen müssen aus den jeweiligen Aufrufern und Argumenten
abgeleitet werden, nicht allein aus der Zahl 2.

Im für unseren Rahmen aufgerufenen Callback unterscheidet `0x32096`
Operationswert 1 von dem Zweig bei `0x320ce`. Letzterer wird vom geprüften
Wrapper mit 2 erreicht. Der Zweig liest den zweibyteigen Rahmenkopf über
`0x1eda2`, grenzt dessen Verbindungsfeld ab und versucht zwei Zuordnungen:

| Zweig | Bedingungen und Verarbeitung | Neue Datenflussgrenze |
| --- | --- | --- |
| Erste Zuordnung | `0x320dc` → `0x34f7e`; bei nichtnull über `0x320e6` → `0x365e0` → `0x36260` | `0x3628c` überspringt vier äußere Kopfbytes; `0x362b6` reicht Nutzdatenabschnitte an `0x346e6`; `0x34734` kopiert mit dem bekannten ROM-Stub nach Paketpuffer `+0x10`, danach Queue-/Scheduling-Helfer |
| Zweite Zuordnung | Nur wenn die erste fehlt: `0x320ec` → `0x3a34a`; bei nichtnull `0x320f6` → `0x3a370` | `0x3a394`/`0x3a398` wählen `Rahmen+4` und `Länge−4`; `0x3a39a` kopiert nach Paketpuffer `+0x18`, danach Weitergabe an `0x3cb40` |
| Keine Zuordnung | Beide Prüfungen liefern null | Rückkehr aus dem Callback; kein belegter erfolgreicher Versand |

Die erste Zuordnung durchsucht eine zustandsabhängige Liste und vergleicht
eine gespeicherte Kennung. Ihre Existenz und der jeweilige Rückgabewert
bleiben Laufzeitvoraussetzungen. Im ersten Sendepfad werden Abschnitte anhand
einer verbindungsabhängigen Länge gebildet. **Nur die ausgewählten Kopierstellen**
sind als byteerhaltend verfolgt; Paketierung, Fehlerbehandlung und die
untere Funkübertragung sind nicht vollständig validiert.

Die ersten vier äußeren Kopfbytes sind keine Sensorbytes. Das Entfernen
dieses Headers widerspricht daher nicht dem bisherigen A2-Nutzdatenpfad.
Es fehlen weiterhin der vollständige untere Funkweg und die Zuordnung zum
tatsächlichen Dongle-Empfangseinstieg. Keine neue Achsenumordnung,
Offsetkorrektur oder Gyroverstärkung in den hier geprüften Kopierstellen.

## 3. Die zwei Decodergrenzen genauer eingegrenzt

### EDD8: skalierte Halfword-Adressierung

Zusätzlich zu den bereits dokumentierten Sensorindizes gibt es einen
unabhängigen **Kontext innerhalb derselben Firmware**: Bei `0xa8`/`0xac`
wird die Adresse einer 32-elementigen Halfword-Tabelle gebildet, Dateioffset
`0x2bffe`. Ein berechneter Index wird bei `0xbe` mit der strittigen EDD8-Form
verwendet. Die konkrete Indexspanne aller Laufzeitzustände ist nicht bewiesen.

Für die betrachteten Indizes 0–31 ergeben sich zwei deutlich verschiedene
statische Tabelleninterpretationen:

- `Basis + 2×Index`: 32 streng ansteigende Werte von 0 bis 16384.
- `Basis + Index`: überlappende Zweibytefenster, 31 von 32 Ergebnissen
  verschieden, nicht monoton; letzter Wert 17156.

Die skalierte Deutung passt zur Tabellenstruktur und zu den getrennt
gefundenen Sensorfeldadressen. Der Zweck der Tabelle ist jedoch nicht
belegt; insbesondere ist 16384 **kein gefundener Gyrofaktor**.

Eine verwandte Schreibform ist ebenfalls fehlerverdächtig: Der Load bei
`0x115ba` und Store bei `0x115c4` verwenden dieselben Basis-/Indexregister.
Der aktuelle Decoder liefert beim Load `Basis+Index`, beim Store dagegen
`(Basis+Index)<<1`. Das plausible gemeinsame Modell wäre
`Basis+(Index<<1)`. Die Mode-9-Schreibform ist damit ausdrücklich in den
Prüfumfang aufgenommen, aber nicht stillschweigend als korrigiert behandelt.

### Signed extract: verschobene Felder und Parallelkontext

Neben der bisherigen 16-Bit-Akkumulation gibt es bei `0x30e80`/`0x30e86`
16-Bit-Felder ab **Bitposition 8**. Der aktuelle P-Code führt auch hier
nur Maskierung und logisches Schieben aus, keine wirksame Vorzeichenerweiterung.
Die folgende Quadrierung ist ein weiterer Konsistenzkontext, keine
unabhängige Bestätigung der Instruktionssemantik.

Bei `0x10e2a` und `0x10e2e` stehen eine kompakte 16→32-Vorzeichenerweiterung
und die strittige Extract-Form im selben Sensor-Nachbarblock. Beide sind
mit Stores parallelisiert: alte Registerwerte und neue Ergebnisse dürfen
nicht durch doppeltes Zählen der Parallelmitglieder vermischt werden.
Dieser Abschnitt wird nicht als zusätzliche Verstärkung des bereits
abgegrenzten ST-Berichtskonstruktors interpretiert.

Ein zweites reines Integer-Modell – links ausrichten, als vorzeichenbehaftete
32-Bit-Zahl interpretieren, arithmetisch zurückschieben – wurde gegen alle
65.536 16-Bit-Werte **an den Positionen 0 und 8** sowie weitere Feldgrenzen
geprüft. Es stimmt mit der mathematischen Signed-Deutung überein. Das prüft
das vorgeschlagene Rechenmodell, **führt keine Firmware aus und validiert
keinen Opcode**.

Das bereits gespeicherte offizielle ROM-Listing wurde diesmal nach den
**Rohkodierungen** statt nur nach Mnemonics durchsucht: Unter seinen 3422
Instruktionszeilen kein exaktes EDD8-Beispiel und keine E1B-Signed-Form.
Die vorhandenen unsigned-extract- und indizierten Word-Beispiele schließen
diese Lücke nicht. Kein neuer Decoderpatch und kein automatischer Ersatz
der unbestätigten Semantik in den Forschungsbefunden.

## 4. Validierung und nächster Schritt

- **61 lokale Forschungstests bestanden**, zwölf neu: Adressraumverwechslung,
  falscher Tabellenslot, falsches Callback-Ziel, falsche RAM-Zelle,
  Tabellen-/Feldgrenzen, Modellgegenproben und drei App-Hashprüfungen.
- Abschließender isolierter statischer Lauf: **29 Fenster, 389 Decode-
  Datensätze, keine Decodeabbrüche**, Quellen unverändert. Explorative
  Fehlstarts und Fortsetzungen hinter Sprungtabellen/Funktionsenden wurden
  separat ausgeschlossen; keine automatische Resynchronisation.
- Der schon geprüfte private Decoder bleibt unverändert. Seine früheren
  127 SDK-Kontrollen werden nicht als neue Bestätigung der offenen Formen
  ausgegeben. Das SDK bleibt eine gespeicherte, hashgeprüfte Referenz.
- Privater Auditindex:
  `build/jieli-validation-20261018/anchors/callback-review.json`.
  Eigene Prüfer/Tests und Rohresultate bleiben dort; der öffentliche Commit
  enthält nur Dokumentation, keine Firmware oder fremden Decoderquellen.

Die offene Frage ist nun gezielter: Welcher der beiden unteren
Verbindungspfade trägt den A2-Rahmen in der betreffenden Betriebsart, und
wie gelangt er in den bereits identifizierten DG-Empfangsparser? Zusätzlich
bleiben genaue ISA-Gegenbelege für die beiden Decoderfamilien und die letzte
wirksame Sensorkonfiguration erforderlich. **0,07 Grad/s je ST-Sensorzählwert
bleibt bedingt, kein bestätigter USB-Gyrofaktor.**
