# Nexus: sechs Sensorfelder und nativer Kalibrierungspfad

Stand: 15. Oktober 2026. Fortsetzung der
[Nexus-Paketanalyse](GAMESIR_NEXUS_RESEARCH.md), ausschließlich offline.
**Ein physikalischer Gyro-Skalierungsfaktor wurde nicht bestimmt.** Die
Fortsetzung mit alternativen Pfaden hat aber die zuvor offenen nativen
Sensorzugriffe aufgelöst und zusätzliche Empfangs-, Legacy- und
Profilkonverter geprüft. Die Feldnamen allein waren dafür kein Nachweis.

## Vorgehen, Quelle und Grenzen

Vor Beginn erläutert: Feldproduzenten rückwärts zum Paketparser verfolgen,
Typen und Umrechnungen prüfen, Kalibrierungsanforderung und Rückantwort
getrennt untersuchen. Eine Konstante zählt nur mit belegtem Datenfluss zu
°/s oder rad/s als Gyrofaktor. Empfindlichkeitsregler, Triggernormalisierung,
Anzeigeskalen und bloße Zahlenähnlichkeiten reichen nicht.

Quelle ist unverändert `HJC.GameSir.Nexus2_0.dll`, 33306624 Bytes, aus Nexus
2.1.23.0, SHA256
`36cb48433ca270994ada6625348af7f1c51a1a50f7dc6d63b7d0fff372c0a040`.
Vorhandene Linux-Werkzeuge und eigene begrenzte Python-Leser verarbeiten nur
Dateibytes/Metadaten/Disassemblierung. Kein Import oder Ausführen von
Hersteller-Code, kein Netzwerk/SSH, keine Geräteöffnung, USB-Anforderung,
Kalibrierung oder Änderung an Kernel, Manager, Installation oder Spielbetrieb.

Zusätzliche unveränderte lokale Quelle ist die mit Nexus ausgelieferte
x64-Abhängigkeit `Microsoft.NET.Native.Runtime.2.2.appx`, 244530 Bytes,
SHA256 `27fae660d8c609e020703bb463b6601e62811dc75db19975bcb7d68d959b527d`.
Der Eintrag im ursprünglichen Installations-ZIP ist bytegleich. Daraus wurde
`mrt100_app.dll`, 445936 Bytes, SHA256
`c3f74a65a2dfa3679b06d3c205e79144aa95e5c47b1908badf6a737dea73d717`,
privat ohne Ausführungsrechte als Daten extrahiert. Ihre exportierte Funktion
`RhFindBlob` wurde disassembliert, nicht aufgerufen. Sie erklärt das interne
Verweistabellenformat der Hauptanwendung. Keine neue Software installiert.

**Dateioffsets** unten sind nullbasiert; **RVA** sind virtuelle PE-Adressen
relativ zur bevorzugten Basis `0x180000000`. In dieser DLL liegt der untersuchte
`.text`-Dateioffset jeweils `0x2c00` unter der RVA. Das gilt nicht pauschal
für andere Sektionen oder DLLs. Disassemblerbeschriftungen relativ zum
nächsten Export werden nicht als echte Funktionsnamen übernommen.

Öffentlich geeignete eigene Metadaten:
[nexus-sensor-dataflow.json](nexus-sensor-dataflow.json).
Vollständige private Belege bleiben unter
`.local/research/20261015-gamesir-nexus/followup-{metadata,sensors,calibration,units}/`.
Die zusätzlichen Belege und eigenen Leser liegen daneben in
`alternative-{map,receive,config,consumers}/`.
Keine Binärdateien, vollständigen Disassemblierungen oder Herstellercode in Git.

## 1. Die sechs Felder: tatsächliche Typzuordnung

Ein begrenzter eigener Leser dekodiert die beobachteten NativeFormat-
Metadaten ab Dateioffset `0x752630`. Namen, Verweise, Methodensignaturen und
Feldsignaturen werden gegengeprüft; kein allgemeiner AOT-Decompiler behauptet.

Die Felder gehören zu
**`HJC.GameSir.Nexus2_0.Core.Models.KeyState`**, einer gemeinsamen
`System.ValueType`-Struktur, nicht zu einem eigenständigen kalibrierten
Sensorobjekt. Typdefinition: Datei `0x8872ed`, Attribute `0x100109`,
104 Methoden, 48 Felder, 56 Eigenschaften. Die Metadaten deklarieren unter
anderem sequenzielles Layout. Der Typ enthält auch normale Tasten, Trigger,
Sticks und Zusatztasten.

| Eigenschaft | Getter-Record | Setter-Record | privates Feld-Record |
|---|---|---|---|
| GyroX | `0x9351c8` | `0x9351da` | `0x9355a9` |
| GyroY | `0x9351ec` | `0x9351fe` | `0x9355b6` |
| GyroZ | `0x935210` | `0x935222` | `0x9355c3` |
| AccelX | `0x935234` | `0x935246` | `0x9355d0` |
| AccelY | `0x935258` | `0x93526a` | `0x9355dd` |
| AccelZ | `0x93527c` | `0x93528e` | `0x9355ea` |

Alle sechs Getter geben **`System.Int32`** zurück, alle Setter nehmen
`System.Int32`, und alle sechs privaten Backing-Felder haben diesen Typ.
Der gemeinsame Getter-Signaturrecord liegt bei `0x7649b9`, die Feldsignatur
bei `0x766b22`; beide führen über einen TypeReference-Record bei `0x757695`
zu `System.Int32`. Damit ist die Typaussage stärker als eine Zeichensuche.
Sie belegt weder Einheiten noch 32-Bit-Wireauflösung oder eine Verwendung
der Eigenschaften im G7-Pro-Pfad.

### Native Zugriffe inzwischen aufgelöst

Die anfangs ungelöste Zuordnung ist durch die mitgelieferte Runtime erklärt:
`RhFindBlob` (Runtime-RVA `0x46b60`) und der interne Zugriff bei `0x50e28`
lesen Datensätze aus zwölf Headerbytes plus direkt anschließenden Nutzdaten,
**ohne Ausrichtungspadding**. Das Modulverzeichnis enthält 27 Blobs. Die
ExternalReferences-Tabelle, Blob-ID 8, beginnt deshalb **nicht ausgerichtet
bei Dateioffset `0x5f3209`** und enthält 96310 DWORD-Einträge. Frühere
ausgerichtete Zeigersuchen konnten sie nicht finden.

Beispiel: Index `0x11efc` ergibt die unabhängig bekannte Versionsparser-RVA
`0x141b650`. Die Typmap in Blob-ID 1 verbindet den KeyState-Index `0x7af`
mit der bekannten Typdefinition `0x8872ed`; derselbe Index führt in
ExternalReferences zur EEType-RVA `0x24be0`.
Die Methodenmap in Blob-ID 6 und Feldmap in Blob-ID 9 lassen sich damit
gezielt für den richtigen deklarierenden Typ auswerten.

| Feld | Versatz im unboxed KeyState | Getter-RVA | Setter-RVA |
|---|---|---|---|
| GyroX | `0x50` | `0x13c9070` | `0x141b320` |
| GyroY | `0x54` | `0x1a2c0c0` | `0x141b310` |
| GyroZ | `0x58` | `0x1936de0` | `0x141b300` |
| AccelX | `0x5c` | `0x19faaa0` | `0x1407080` |
| AccelY | `0x60` | `0x13ebf40` | `0x1407070` |
| AccelZ | `0x64` | `0x13ebf30` | `0x1a6ae40` |

Alle Feldmap-Ergebnisse wurden zusätzlich gegen den tatsächlichen Getter-
und Settercode geprüft. Dieser lädt beziehungsweise speichert ausschließlich
Int32; **keine Skalierung, Bias-Korrektur oder Einheitenumrechnung**.
Boxing-Adapter addieren acht Byte zum Objektzeiger und springen zum
unboxed Zugriff; auch diese Ketten sind aufgelöst. Die Feldoffsets sind damit
belegt und keine Vermutung aus der Metadatenreihenfolge mehr.

Die trivialen Zugriffskörper werden allerdings vom Compiler zwischen Typen
geteilt. Ein direkter Aufruf desselben Setters beweist allein keinen
Sensorzugriff: Ein geprüfter Aufrufcluster ab RVA `0x118a7d1` setzt damit
Geräte-VID/PIDs auf einem anderen Typ. Der deklarierende Typ beziehungsweise
der Empfänger muss bei jeder Writer-/Consumer-Zuordnung mitbelegt werden.
Die Auflösung ist ein begrenzter eigener Datenleser, kein vollständiger
NativeFormat-Decompiler oder vollständiger Anwendungscallgraph.

## 2. Zwei native E0-Telemetrieparser gefunden

| Pfad | Eingangsgate RVA | Parser RVA | Dateibereich des Parsers, Ende exklusiv |
|---|---|---|---|
| primär | `0x1894720` | `0x1895400` | `0x1892800…0x18934be` |
| alternativ | `0x19837c0` | `0x1984a60` | `0x1981e60…0x1982af8` |

Beide Gates verlangen ein Bytearray mit **Länge 60** und
**`payload[0] == 0xe0`**. Das primäre Gate prüft die Länge bei RVA
`0x189475c`, die Kennung bei `0x1894770` und ruft bei `0x189479b` den
Parser auf. Dieser Befund stammt aus nativem Maschinencode.

Die beiden vollständigen Decoder lesen Nutzdatenindizes **1–9 und 25–56**;
das Gate liest zusätzlich Index 0. **Indizes 10–24 und 57–59 werden in
diesen Pfaden nicht gelesen.** Dpad- und Stickhelfer erhalten bereits
geladene Einzelbytes, keinen Rohpayload. Indirekte Schleifenziele und die
Zustandsbenachrichtigung wurden zusätzlich geprüft; Letztere erhält nur
Zustandskopien. Die Readset-Aussage ist auf diese beiden Funktionspfade samt
den untersuchten Helfern begrenzt.

Abgleich mit unserem 64-Byte-Bericht:

| Gespeicherter Capture | Bei rechnerischem Abzug von vier Headerbytes | Verhalten der beiden Nexus-Parser |
|---|---|---|
| Gyro signed-LE16 ab 17/19/21 | signed-LE16 ab 13/15/17 | Bytes 13–18 ungelesen |
| Accel signed-LE16 ab 23/25/27 | signed-LE16 ab 19/21/23 | Bytes 19–24 ungelesen |
| Zusatztasten bei 57/58 | 53/54 | werden ausgewertet |

Länge, `e0` und die zusätzlichen Tastenpositionen passen zu einem um vier
Byte gekürzten Bericht. **Die konkrete Headerentfernung und vollständige
Modell-/Transportzuordnung sind aber nicht nachgewiesen.** Der untersuchte
vorgeschaltete Wrapper RVA `0x18945f0` reicht den übergebenen Payload weiter;
er selbst entfernt keinen Header. Die Tabelle ist ein gezielter Vergleich,
keine Behauptung bereits identischer Windows-/Linux-Pakete.

Beide Parser initialisieren zwei `0x78`-Byte-Zustandsblöcke mit null über
das statisch aufgelöste Importziel `mrt100_app.dll!RhpInitMultibyte`.
Anschließend werden normale Eingaben, Status und weitere Felder geschrieben;
der Bereich `0x4e…0x67` bleibt in den geprüften Pfaden unbeschrieben.
Mit den inzwischen unabhängig belegten Feldoffsets lässt sich nun stärker
festhalten: **Alle sechs Sensorfelder `0x50…0x67` bleiben in diesen beiden
Parserpfaden null.** Das ist eine statische Datenflussaussage, kein neu
beobachteter Hardwarezustand. Die Nichtauswertung des passenden
IMU-Bytefensters bleibt zusätzlich belegt.

**Folgerung:** Diese beiden Pfade liefern keine Herleitung eines
Gyrofaktors. Die sechs vorhandenen Eigenschaften beweisen keine dort
implementierte Sensorausgabe. Andere Empfangs-/Anwendungspfade bleiben
ausdrücklich offen.

## 3. Alternative Empfangs- und Verbraucherpfade

Die native Methodenmap ordnet denselben Metadatenrecord `0x937f46`
mehreren deklarierenden Typen zu. Die Zuordnung erfolgt deshalb immer
zusammen mit dem Typ, nicht allein anhand eines Methodennamens oder einer
geteilten Codeadresse. Insgesamt wurden diese sieben `Update`-Körper geprüft:

| Typ unter `HJC.GameSir.Nexus2_0.Core` | Update-RVA | Einordnung |
|---|---|---|
| `Services.GamepadStateParseService` | `0x1984a60` | byteweise Telemetrie, oben bereits untersucht |
| `Devices.T7.GamepadStateParseService` | `0x1a650d0` | byteweise Telemetrie |
| `Devices.T7ProW.GamepadStateParseService` | `0x1895400` | byteweise Telemetrie, oben bereits untersucht |
| `Devices.T3Pro.GamepadStateParseService` | `0x1989a50` | byteweise Telemetrie |
| `Devices.G7.GamepadStateParseService` | `0x1a65d90` | byteweise Telemetrie |
| `Devices.T7.XBoxXControllerKeyParser` | `0x198e960` | vier vorzeichenbehaftete 16-Bit-Stickwerte |
| `Devices.G7.XBoxXControllerKeyParser` | `0x1980180` | vier vorzeichenbehaftete 16-Bit-Stickwerte |

Alle sieben initialisieren einen frischen KeyState mit null und beschreiben
seinen jetzt belegten Sensorbereich `0x50…0x67` nicht vor der Weitergabe.
Sie liefern daher in diesen Pfaden keine sechs Sensormesswerte oder
physikalische Umrechnung. Die Typnamen beweisen nicht automatisch, welcher
Parser für jede reale G7-Pro-Verbindung gewählt wird.

Die beiden Legacy-Parser rufen einen indirekten 16-Bit-Lesehelfer mit den
Indizes 6/8/10/12 auf, erweitern dessen Ergebnis vorzeichenbehaftet und
normieren auf Double mit 32766 auf der positiven und 32767 auf der negativen
Seite. Y wird invertiert; die Ausgabe geht in **Stickfelder `0x20…0x3f`**.
Die exakte Implementierung/Byteordnung des indirekten Lesehelfers wurde
nicht aufgelöst. Das reicht zur Zuordnung dieser Zahlen zu Sticks, aber
nicht für einen neuen Wiredecoder oder einen Gyrofaktor. Auch der untersuchte
`OldFwStateParseService`-Callback bei RVA `0x198f790` kopiert zwei bereits
gebildete `0x118`-Byte-Gesamtzustände, ohne Sensorumrechnung.

### Transport, Firmwarebrücke und offene Einstellungsantworten

Die WinMD-Metadaten und die nativen Methoden der vorhandenen
`D4XGaming.Devices.dll` wurden zusammen geprüft. `ID4XDevice.GetMessageB`
(RVA `0x1c10` in dieser DLL) kopiert einen vollständigen gepufferten
Bytevektor. Der Empfangscallback `0x1870` übernimmt gelieferte Länge und
Zeiger unverändert und veröffentlicht über `0x19d0`. Hier findet weder
eine Sensorumrechnung noch die bisher fehlende Entfernung von vier
Headerbytes statt. Das Framing des vorgeschalteten Windows-Providers
bleibt offen.

Ein anderer Pfad verlangt 60 Byte mit `0xf1` statt `0xe0`:
`Instance_OnReceiveMessage` bei Haupt-DLL-RVA `0x191f880` führt über
`0x191f8f0` und `0x14bb3c0` zum PE-Import **`JL_handleGipData`** aus
`JL_Upgrade_Gip.dll`. Dabei werden 60 Byte in einen neuen 64-Byte-Puffer
**ab Zieloffset 4 eingefügt**, nicht vier Headerbytes entfernt. Dies ist
konkret eine Firmware-Empfangsbrücke und kein belegter IMU-Produzent.
Keiner dieser Herstellerpfade wurde aufgerufen.

Der Nicht-E0-Antwortparser `0x18951a0` bildet aus einer 60-Byte-Hülle ein
Antwortobjekt und kopiert Nutzbytes ab Index 5 beziehungsweise 6;
Länge aus Byte 4 beziehungsweise für internen Typ 15 aus Big-Endian 4/5.
Der Dispatcher `0x18949a0` behandelt interne Enumwerte 6/5/12/15/17/10.
Diese Werte werden nicht ungeprüft zu USB-Befehlsnummern erklärt.
Ein generischer Antwortkörper könnte auch numerische Kalibrierungsdaten
transportieren; ein solcher konkret zugeordneter Körper wurde nicht gefunden.

**Weiterer gezielter Ansatz, ausdrücklich unbestätigt:**
`ID4XDevice.SendReceiveMessageC` nimmt einen `SettingTag:uint32` und liefert
`Result`, `SettingTag`, `SettingType` als uint32 sowie `SettingValue:uint64`.
Die native D4X-Methode `0x1cd0` verarbeitet dafür 4 Request- und 20 Antwortbytes.
Die Haupt-DLL-Projektion ist bei `0x1e55460` aufgelöst. Es ist ein generischer
getaggter Einstellungskanal. Ein Gain-/Offsetwert wäre darin darstellbar,
aber **kein zugehöriger Sensor-Tag, Einheitenbezug oder Verbraucher ist belegt**.
Keine direkten E8/E9-Aufrufer gefunden bedeutet hier keine Abwesenheit
virtueller oder dynamischer Aufrufe. Der Kanal bleibt offen, statt ihn
fälschlich als ausgeschlossene Kalibrierungsquelle zu behandeln.

### Begrenzte Prüfung der Zustandsverbraucher

Vier direkt auf den belegten KeyState-Typ verweisende Körper bei RVA
`0x17d0870`, `0x17d0920`, `0x184c1f0` und `0x1863990` bereiten Argumente
oder Boxing/Zustandskopien vor. Der native `GamepadStateChanged`-Ereignispfad
`0x1d75190` → `0x1d75270` reicht Nutzdaten an asynchrone Verarbeitung weiter.
In diesen Körpern wurde keine Umrechnung auf °/s oder rad/s gefunden;
die dahinter liegenden indirekten Verbraucher sind damit nicht vollständig
aufgelöst.

Im bereits extrahierten Web-JavaScript leitet `sendFromBackend` bei UTF8-
Dateioffset 595061 `GamepadStateChanged` an Testbeobachter weiter, je nach
Testmodus mit `Original` oder `Mapped`. Eine Textsuche nach Gyro/Accel
findet in dieser Datei keine Treffer. Auch das beweist keine globale
Abwesenheit einer versteckten oder anders benannten Sensorauswertung.

## 4. Kalibrierung vom UI bis zur nativen Transportgrenze

Der zuvor belegte UI-Aufruf `deviceReq("calibrate", …)` ist jetzt auch
auf der nativen Seite verfolgt:

```text
Registrierung "calibrate"
  → Delegate
  → asynchroner Handler
  → virtuelle Gerätemethode, Slot +0x68
  → konkreter Kalibrierungs-Builder
  → interne Sendeanforderung
  → WinRT-Transportgrenze
```

| Schritt | Statische Fundstelle |
|---|---|
| Registrierung / Handler | UTF16 `calibrate` bei Datei `0xe29804`; Registrierungsreferenz VA `0x181a6469b`, Delegate `0x181a62960`, Async-Körper `0x181a62a80` |
| konkrete Methode | RVA `0x198b490`, Datei `0x1988890`; Funktionszeiger liegt tatsächlich im Slot `+0x68` der EEType-Tabelle `0x1800ad4b0` |
| Transportfortsetzung | RVA `0x18733b0` → Wrapper `0x148ff20`, gepinnter Puffer und Länge, indirekter WinRT-Aufruf |

Die konkret untersuchte virtuelle Implementierung ist damit statisch
verbunden. Vollständiges `deviceId`-/Modellrouting im realen Betrieb bleibt
offen; dieser VTable-Nachweis ist kein Laufzeit- oder Hardwarebeleg.

Der Builder deserialisiert eine Anforderung und bildet **drei Nutzbytes**:
`[0xfe, low_byte(calType), partMask]`. Die Part-Zuordnung lautet:

| `calPart` | Maske |
|---|---|
| `sticks` | `0x03` |
| `triggers` | `0x0c` |
| `motion` | `0x10` |
| `triggers_sticks` | `0x0f` |

Die native Enum heißt tatsächlich **`CalibrationOpration`**; die Schreibweise
stammt aus Nexus. Metadaten belegen `Start=0`, `Finish=1`, `Exit=2` mit
**System.Int32** als zugrunde liegendem Typ. Der Builder kopiert davon nur
das untere Byte. Die zugehörige `CalibrationRequest`-Typdefinition liegt
bei Datei `0x8879a3`, die Enumdefinition bei `0x8879d7`, beide im oben
genannten `Core.Models`-Namensraum. Dies bestätigt die schon im UI
beobachteten Werte, aber keine physikalische Kalibrierungsformel.

Die interne Transportanforderung führt zusätzlich das Byte `0x0f`;
Puffer/Länge und dieses Byte werden an einen WinRT-Aufruf weitergereicht.
Der Methodenname ist inzwischen als **D4X `SendMessage`** aufgelöst:
Metadatenrecord `0x7a09a3` mit deklarierendem Typindex `0x18d4` führt zu
RVA `0x1e554e0`; deren Aufruf bei `0x1e554e4` erreicht den bekannten Wrapper
`0x148ff20`. WinMD-Reihenfolge und nativer Slot 13 passen dazu. Dies ist
mehr als eine Slotvermutung; Framing und konkrete USB-Übertragung bleiben
aber unaufgelöst. **Die drei Nutzbytes sind kein vollständiger, validierter
USB-Befehl und keine lesende Kalibrierungsabfrage.** Sie dürfen weder im
Bootstrap noch in einem passiven Test automatisch gesendet werden.

Drei native `CalibrationStateChanged`-Pfade, RVA `0x19858a0`,
`0x198a8d0` und `0x198e230`, prüfen einen Statuswert und die Bits
`0x01/0x02/0x04/0x08/0x10`. Über den DTO-Konstruktor RVA `0x127da30`
werden daraus Gerätebezug und Booleans. In diesen vollständigen Handlern
findet sich **kein numerischer Bias-/Gain-/Referenzblock und keine
Gyro-Umrechnung**. Das stützt eine an das Gerät delegierte
Kalibrierungssteuerung mit Statusmeldung. Tatsächliche Firmwarewirkung,
Persistenz, Erfolg auf Hardware und mögliche weitere Antwortpfade bleiben offen.

## 5. Konfiguration und verworfene Zahlenkandidaten

Die Auflösung der Methoden erlaubt inzwischen die Prüfung der tatsächlichen
Profilkonverter. Der vollständige Typname lautet
`HJC.GameSir.Nexus2_0.Core.Profile.Templates.C2.Models.SensorModule`.
`Parse` (RVA `0x18703f0`), `Serialize` (`0x186f360`) und
`GetPacketLength` (`0x1597fb0`) verarbeiten einen **34-Byte-Profilblock**:

| Lokaler Blockoffset | Länge | Inhalt |
|---|---:|---|
| 0 | 3 | Aktivierungsverhalten, Aktivierungstaste, Achsenmodus |
| 3 | 5 | Deadzone-Modul |
| 8 | 13 | Kurvenmodul |
| 21 | 13 | `StickMapModule`, Typ `MotionMapModule` |

Diese lokalen Profiloffsets sind keine USB- oder IMU-Berichtsoffsets.
Die Eingabe ist eine Folge von Konfigurationsbytes über `RawData/ReadOffset`,
kein Sechsachsen-Messwert. Das Template-Präfix C2 wird nicht ungeprüft mit
einer vollständigen Gerätemodellzuordnung gleichgesetzt.

| Konverter | GetAppModel-RVA | GetDeviceModel-RVA |
|---|---|---|
| MotionParser | `0x18906b0` | `0x188a870` |
| AdvanceMotionMapParser | `0x1890790` | `0x188a970` |

Die geprüften Methodenkörper kopieren Aktivierung, Orientierungsmodus,
Tastenzuordnungen, Umkehrungen, `axisRatio`, `mouseDpi`, Deadzones und Kurven
zwischen Profilmodellen. Die Achsenoptionen sind Modusbits und kein belegter
Rohachsen-/Vorzeichenbezug. Es gibt in diesen Körpern keinen IMU-Rohsample-
Eingang oder numerischen Sensor-Bias-/Gainblock. Submodule sowie 129
Methodenbindungen wurden mit deklarierendem Typ gegengeprüft;
18 Codebereiche sind mit Grenzen und Hashes belegt. Andere Templates und
weitere Anwendungspfade werden damit nicht pauschal ausgeschlossen.

Eine gefundene Normierung mit **255** ist nun konkret Kurvenpunkten
zugeordnet. Die Helfer RVA `0x1890b90` und `0x188ab90` rechnen vor der
abschließenden Rundung zwischen Bytekoordinaten und einem konfigurierten
Deadzone-Bereich um:

```text
app_point = minimum + (curve_byte / 255) * (maximum - minimum)
curve_byte = 255 * (app_point - minimum) / (maximum - minimum)
```

Die Eingänge stammen aus `LinearModule.OriginalData/TargetData` und
Deadzone-Grenzen, nicht aus Gyrokanälen. **255 ist hier kein Gyrofaktor.**

Eine begrenzte Suche nach direkt RIP-bezogenen skalaren SSE-Operanden fand
1756 Kandidaten, darunter 56 Multiplikationen und 30 Divisionen. Dort wurde
keine direkte Verwendung der untersuchten üblichen Sensitivitätskandidaten
131/65,5/32,8/16,4 oder 8192 und ausgewählter Einheitenfaktoren nachgewiesen.
Das schließt Integer-, SIMD-, indirekte oder dynamische Faktoren nicht aus.

Zwei konkrete Verwechslungen wurden über den Datenfluss ausgeschlossen:

- `/254` in den E0-Decodern normalisiert vier **Triggerwerte** aus
  Payloadindizes 8/9/55/56. Das ist kein Gyrofaktor.
- Der Helfer RVA `0x1896210` zentriert einen **einzelnen 8-Bit-Stickwert**
  um 128 und behandelt die positive Seite mit 127; auch das ist keine IMU-Skala.

Sonstige Zahlen-/Kryptotreffer erhalten ohne Feldbezug keine
Kalibrierungsbedeutung. Die erste Nexus-Analyse hatte bereits alle lesbaren
`8192`-Treffer als kryptografische Namen eingeordnet.

## 6. Konsequenz für GameSir Native Linux

**Bestätigt:** sechs Int32-Sensorfelder einschließlich nativer Speicherlage
und zwölf getrennter Getter-/Setterzuordnungen; deren Körper kopieren nur
Int32. Sieben benannte Zustandsdecoder lassen diese Felder null. Weitere
untersuchte Empfangs-/Kopierpfade liefern keine Sensoreinheiten. Der native
Kalibrierungs-Steuerpfad erreicht D4X.SendMessage und meldet Statusbooleans;
die untersuchten Profilkonverter verarbeiten Konfiguration statt Rohmessung.

**Plausibel, nicht vollständig bewiesen:** Die E0-Parser bekommen einen um
vier Byte gekürzten bekannten Telemetriebericht; die Kalibrierung wird intern
im Gerät durchgeführt. Der generische MessageC-Einstellungskanal könnte
Koeffizienten tragen. Keines davon belegt einen Gyrofaktor.

**Weiter offen:** vollständiges Modell-/Providerframing, weitere indirekte
Sensorproduzenten und Verbraucher, belegte MessageC-Tags/Antwortinhalte,
Sensoreinheiten, physische Achsen, Bias und Gyro-Sensitivität. Die frühere
NativeFormat-/ExternalReferences- und Feldoffsetlücke ist geschlossen;
der vollständige Sensordatenfluss der Anwendung bleibt offen. Die
Untersuchung beweist keine globale Abwesenheit einer Nexus-Umrechnung.

**Für die Alpha gibt es weiterhin keinen neuen einsetzbaren Gyrofaktor.**
Die 12204 gespeicherten IMU-Pakete bleiben Rohdaten; ohne belegte
Drehgeschwindigkeit oder Winkel-/Zeitreferenz lässt sich deren Skala nicht
eindeutig bestimmen. 8192 LSB/g bleibt experimentell und bestimmt den
Gyrofaktor niemals. IIO und normale Gamepad-/Viermotor-/Paddle-Funktionen
bleiben unabhängig; finale SDL-Sensorausgabe bleibt eingeschränkt.

Die anschließend ausdrücklich beauftragte [Firmware-Dateianalyse](GAMESIR_NEXUS_RESEARCH.md)
öffnet die zwölf äußeren Container und bestätigt 126 Eintrags-CRCs. Ihre
MCU-/Packtoolkonfiguration liefert ebenfalls keinen Gyrofaktor. Die
anschließende innere Analyse belegt Packed-Split, 48 Appcontainer und die
vollständige Key-/No-Key-Beziehung. Globale Bankzuordnung, eigentliche
Körperdekodierung und Sensorcode bleiben gezielte offene Fragen. Sie ersetzt
keinen Nachweis der Umrechnung zwischen Sensorregistern und unseren Reports.

Die verbleibende Offline-Suche sollte sich auf konkrete Sensor-Tags und
indirekte Empfänger des MessageC-/Antwortpfads begrenzen. Noch mehr beliebige
Zahlenkonstanten liefern keinen verlässlichen Fortschritt. Kalibrierungs-
Steuerbytes sind kein Ersatz für einen Koeffizientenabruf. Ein eigener
Gyrofaktor kann alternativ über spätere kontrollierte Referenzdrehungen
gewonnen werden, ohne vorher den Sensorchip bestimmen zu müssen.
Eine solche Messung braucht gesonderte Freigabe und gehört nicht zu diesem
Offline-Auftrag. [Prioritäten und Abnahmegrenzen](ROADMAP.md).

## Verifikation

Originalquellen und private Extraktion wurden gegen SHA256 und Archiveinträge
geprüft. Der eigene begrenzte Map-Leser prüft Typ-/Methoden-/Feldzuordnungen,
ExternalReferences und Boxing-Sprungketten; alle sechs Felder wurden unabhängig
gegen Getter und Setter gegengeprüft. Die 129 Profilmethodenbindungen wurden
zusätzlich mit explizitem deklarierendem Typ abgeglichen. PE-Adressabbildung,
Funktionsgrenzen und Bytebereichshashes sind in den eigenen JSON-Belegen
festgehalten. Ungeklärte gemeinsame Codeadressen werden nicht als Sensor-
Produzenten ausgegeben. Keine vollständige AOT-Dekompilierung behauptet.

Die Text-/Metadatenprüfungen ersetzen keinen Runtime- oder Hardwaretest.
Dokumentationsänderung ohne Treiber-/Paketbau, Installation, Ausführung von
Hersteller-Code, Netzwerk oder neue Kalibrierung. Private Herstellerartefakte
bleiben ignoriert; die laufende Treiberversion ist unverändert.
