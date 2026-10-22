> Public export: personal tester, host and path references were anonymized. Historical evidence hashes refer to the private originals.

# GameSir Nexus: statische Firmware- und Sensoranalyse

**Fortsetzung vom 21. Oktober 2026:** Die
[Wartungsanalyse zu Stickkalibrierung und Firmwareupdates](NEXUS_MAINTENANCE_RESEARCH.md)
verfolgt den UI-Ablauf und sechs Updatefunktionen mit lokalem REA weiter.
Sie präzisiert die Grenzen der Geräteprüfung, Bestätigungsschleifen und
Abschlussmeldungen. Kein schreibender Linux-Updater und kein Recovery-Nachweis.
Die folgenden Sensoranalysen behalten ihren historischen Stand.

Stand: 18. Oktober 2026. Untersucht wurde das lokal vorhandene Windows-Paket
**GameSir Nexus 2.1.23.0**. Dieser Bericht dokumentiert eigene Beobachtungen,
Dateimetadaten und begrenzte statische Codeanalyse; Herstellerdateien werden
nicht Bestandteil des Projekts.

**Ergebnis:** Das Paket enthält einen nativen GIP-Firmware-Updater, getrennte
Controller-/Dongle-Paketkandidaten und eine Bewegungskalibrierungsoberfläche.
Es liefert wichtige Ansatzpunkte für eine spätere Linux-Implementierung,
aber noch kein vollständiges, sicher verwendbares Updateprotokoll und keinen
bestätigten Gyrofaktor. Laufzeit, Kalibrierungswerte und installierte Alpha
bleiben unverändert. Die Release-Abnahme hat Vorrang vor Firmwareentwicklung.

**Neuer Sensorbefund vom 18. Oktober:** Zusammengesetzte Textadressen führen
in drei App-Versionen zu einer WHO_AM_I-/Initialisierungskette mit
Vergleich `0x6a` sowie vorbereiteten Transfers `0x11 ← 0x6c` und
`0x10 ← 0x68`. Unter der ST-Arbeitshypothese ist das ein konkreter Kandidat
für ±2000 Grad/s und 0,07 Grad/s je Sensorzählwert. Aktive Hardware,
Busabschluss und unveränderte Übernahme in USB sind noch nicht bewiesen.
[Fundstellen, Decoderkorrekturen, Tests und Grenzen](JIELI_SENSOR_INITIALIZATION.md).
Die [Zwölf-Byte-Fortsetzung](JIELI_SENSOR_REPORT_DATAFLOW.md) stützt nun
eine Kette aus ST-Empfang, Achsenumordnung, bedingtem Offset-Abzug und
`10/3c/e0`-Berichtskonstruktor. Seine Kopiergeometrie trifft die bekannten
Sensorpositionen 17–27. Keine zusätzliche Gyro-Verstärkung im untersuchten
ST-Ausgabeabschnitt; andere Zweige skalieren oder negieren.
Der [Transportfolgepass](JIELI_USB_TRANSPORT.md) ordnet die externe Kopie
dem SDK-ROM-Stub `memcpy`/`memmove` zu und erreicht Controller-USB-IN `0x84`.
Der [Funkrahmen-Folgepass](JIELI_WIRELESS_DATAFLOW.md) ergänzt einen
beidseitig passenden `A2`-/Queue-Kandidaten bis zum DG144-Sendepuffer für
IN `0x82`, ohne zusätzliche Sensorarithmetik in den geprüften Kopien.
Der [Callback-Folgepass](JIELI_RADIO_CALLBACK.md) ordnet inzwischen
Transporttabelle, Setter und registrierten Callback in drei Apps statisch zu;
zwei bedingte untere Sendepfade sind eingegrenzt. Tatsächliches Scheduling,
Verbindungswahl und Funkzustellung bleiben unbeobachtet. 61 Forschungstests
bestanden. Die [Routingfortsetzung](JIELI_LINK_ROUTING.md) klärt nun die
Listen-/Slot-Auswahl anhand der Verbindungskennung und verfolgt den
aufbereiteten DG-Empfangsdeskriptor über Transporttabelle und `btstack`-
Nachricht bis zum A2-Parser; damals 70 Forschungstests bestanden. Der
[Empfangs-/Kontextfolgepass](JIELI_RX_CONTEXT.md) behebt die verlorene
Kontextübernahme unseres Exporters und klärt die einfache Callback-Auswahl.
Eine fünfte private Decoderkorrektur ergänzt fehlende Stack-Offsetbits;
81 Forschungstests, 140 SDK-Einzelbefehls-Kontrollen und fünf einfache
Bedingungsblöcke bestehen. Bedingte Parallelblöcke sowie bestimmte negative
Konstanten bleiben begrenzt. `0xfe42` verarbeitet Paketpuffer über einen
Hardwareblock; CCM-artige Verarbeitung bleibt eine Hypothese.
Halfword-/Vorzeichenformen bleiben weiterhin unbestätigt.
Aktive Konfiguration und physische Achsen bleiben begrenzt. Kein bestätigter
USB-Gyrofaktor.
Die folgenden älteren Suchpässe dokumentieren ihre damalige Erkenntnisgrenze.

**Innerer Strukturfolgepass vom 16. Oktober:** `app.bin` und `cfg_tool.bin`
sind inzwischen für alle 48 Flashdateien vollständig und mit gültigen
Dateiprüfsummen extrahiert. Sensor-/Kalibrierungsmeldungen sind erstmals
lesbar. Der zuvor offene Körper-/CRC-Bezug ist für diese Dateien geklärt.
Der weitere statische MCU-Folgepass erhärtet drei begrenzte Befehlsmuster
und verfolgt die Kalibriermeldung zu einem gemeinsamen Textausgabe-
Zielkandidaten. Ein vollständiger ISA-Decoder, der Sensor-Schreibpfad und
aktives CTRL2_G fehlen weiterhin. Die älteren Fehlversuche unten behalten
ihren historischen Umfang.

**MCU-Folgepass vom 18. Oktober:** Zwei weitere begrenzte Feldmodelle
(kurze positive Zielfelder und signed6-Maskenoperanden) sind empirisch
korroboriert. Außerdem ist für einen App-Suffix eine getrennte
Load-/Run-Adressabbildung durch Startgeometrie und 75 Textverweise gestützt.
Die Sensoranker liegen außerhalb dieses Suffix. Speicher-/Vergleichssemantik,
Sensorinitialisierung und aktiver CTRL2_G-Wert bleiben offen; kein Faktor
wird aus den neu lesbaren Zahlen allein abgeleitet.

**Sensorfolgepass:** Der [Sensor-/Kalibrierungsdatenfluss](NEXUS_SENSOR_DATAFLOW.md)
belegt inzwischen alle sechs Int32-Feldzugriffe im gemeinsamen KeyState samt
nativen Getter-/Setter-RVAs und Offsets. Sieben geprüfte Eingabe-Zustandspfade
lassen die Sensorfelder null. C2-Profilblock und /255-Kurvennormierung sind
Konfiguration; D4X-Sendemethode und F1-JL-Firmwarebridge sind zugeordnet.
Kein physikalischer Gyrofaktor oder numerischer Kalibrierungsabruf gewonnen.
Der Folgepass vom 18. Oktober verfolgt den Zustandsereignispfad bis zur
JSON-/WebView-Weitergabe und benennt die Profilantworten typgebunden.
MessageC setzt in der gebündelten D4X-DLL auf normalen Rückkehrpfaden E_FAIL;
ein realer Anwendungscaller oder Sensor-Tag ist weiterhin nicht belegt.
Das ist kein reproduzierter Nexus-Bug. Globale JSON-Settings verhindern
zudem die pauschale Aussage, alle Sensorwerte würden unverändert ausgegeben.
Weitere Provider, vollständige Header-/Modellzuordnung und physisches
Kalibrierungsframing bleiben offen. Die folgenden Grenzen der
ersten Namens-/UI-Prüfung werden dadurch präzisiert, keine globale
Abwesenheit anderer Sensorpfade behauptet.

**Entscheidung vom 18. Oktober: weitere Funkanalyse zurückgestellt.**
Registerblock und Parameter des Pakethelfers `0xfe42`, Ursprung der
Empfangsdeskriptoren und Zustands-/Freigabe-/Kennungsschreiber bleiben offene
Forschungsfragen. Der reale IMU-Paketempfang ist bereits belegt; die Zuordnung
zu jedem einzelnen Firmwarezweig ist keine Voraussetzung für eine spätere
Referenzmessung. **0,07 °/s pro USB-Rohwert ist nur ein unbestätigter
Testkandidat**; [Herkunft und Grenzen](PROTOCOL.md#unbestätigter-gyro-testkandidat).
Gyrokalibrierung bleibt pausiert, keine Änderung an Treiber oder SDL-Ausgabe.
Statische Registrierung und der obere Empfangseinstieg zum `A2`-Pfad sind
zugeordnet; tatsächlich aktive interne Zweige bleiben unbestätigt. Der Writer
des Formatcaches `D+0xa24` ist gefunden, bleibt aber
vom passend zugeordneten Queue-Pfad getrennt. Indizierte Halfword-/
Vorzeichenformen sowie weitere Schreiber der Offsets und Sensorregister
bleiben ebenfalls offene Forschungsfragen.
Sensorwahl und letzte wirksame Initialisierung bleiben
unbestätigt. Ein aktiver Messbereich allein ist noch kein Faktor für
unsere USB-Rohwerte. Bestehende Werkzeuge werden
weiterverwendet. Nach gesonderter Freigabe ist REA jetzt als getrenntes,
wiederverwendbares lokales Analysewerkzeug eingerichtet; der unten
beschriebene Jieli-Backend-Abgleich bleibt davon getrennt.

## 1. Quellen, Verfahren und Grenzen

Lokale Originale unter `~/Downloads`:

| Quelle | Bytes | SHA256 |
|---|---:|---|
| `GameSir.Nexus-Manual Install.zip` | 121402887 | `66368251480ac7082fc07da8f133ca5723194839e6b21a3c2d323679c33e1219` |
| `HJC.GameSir.Nexus2_0_2.1.23.0_Test/HJC.GameSir.Nexus2_0_2.1.23.0_x64.msixbundle` | 58553643 | `7a537cbcd8641147833140edebba984aebf59e72561b850e2786436b5e59c7b4` |
| darin `HJC.GameSir.Nexus2_0_2.1.23.0_x64.msix` | 57565503 | `51212b76ec90f91d23eca1c7d33fd11f2be9f3187c962fb63d5d46c9fd31ce9f` |

Das Bundle im ZIP ist bytegleich mit dem bereits ausgepackten Download.
Manifest, PE-Importe/-Exporte und Versionsressourcen, ASCII-/UTF16-Zeichenketten,
WinMD-Namen, lesbares Web-JavaScript und begrenzte x64-Disassemblierung wurden
mit vorhandenen Linux-Werkzeugen geprüft. Hersteller-Code, PowerShell,
JavaScript, EXE, DLL und Firmware wurden weder ausgeführt noch importiert.
Keine Netzwerk-/SSH-/USB-Abfrage, Paketinstallation oder Systemänderung.

Privates Arbeitsverzeichnis: `.local/research/20261015-gamesir-nexus/`.
Extraktion in ein separates Verzeichnis mit privaten, nicht ausführbaren
Dateien; Downloads bleiben erhalten. Dort liegen vollständiges Inventar,
Hashes, Zeichenketten, Disassemblierung und eigene Analyseprotokolle.
Öffentlich geeignet sind dieser Bericht und das eigene
[Quellmanifest](nexus-source-manifest.json), keine Binärdateien, Firmware,
Ressourcenkopien oder vollständigen Zeichenkettenauszüge. Rechte zur
Weiterverteilung des Herstellerinhalts sind nicht geklärt.

Fundstellen sind **nullbasierte Dateibyte-Offsets**, bei JavaScript UTF8 und
bei entsprechend bezeichneten DLL-Literalen UTF16LE. Native **RVA** sind
relative virtuelle Adressen im PE, keine Dateioffsets. Für die JL-DLL ist
die bevorzugte Imagebasis `0x180000000`; VA = Imagebasis + RVA. Das Manifest
fixiert die jeweils untersuchte Datei per SHA256. Bezeichnungen und statisch
erreichbare Zweige beweisen nicht ihre tatsächliche Benutzung auf unserem Gerät.

## 2. Paket und zuständige Komponenten

Das Bundle enthält ein x64-Hauptpaket, neun Sprachpakete und vier zusätzliche
Skalierungsressourcen. Das Hauptpaket umfasst **223 Dateien**, darunter
**24 UFW-Dateien**, davon zwölf unter `FirmwarePackages/G7Pro/`.

`AppxManifest.xml` nennt die Identität
`GuangzhouChickenRunNetwor.16460D2A87234`, Version `2.1.23.0`,
Windows.Universal ab `10.0.17763.0`, URI-Schema `gamesirnexus` und
`internetClient`. Abhängigkeiten: .NET Native Framework/Runtime 2.2,
Microsoft.UI.Xaml 2.8 sowie VCLibs 140 einschließlich UWPDesktop.
Der Installations-ZIP enthält passende Frameworkpakete für mehrere
Architekturen, Installations-/Telemetrieskripte und ein Zertifikat.
Keines davon wurde gestartet oder installiert.

| Komponente | Bytes | Nachweis / Aufgabe |
|---|---:|---|
| `HJC.GameSir.Nexus2_0.exe` | 20480 | x64-PE-Startstub; importiert `RHBinder__ShimExeMain` aus der Haupt-DLL |
| `HJC.GameSir.Nexus2_0.dll` | 33306624 | Native .NET-Native/AOT-Anwendung; WebView-Bridge, Gerätemodelle, Konfigurations-/Updateklassen; direkte Importe der JL-Updatefunktionen |
| `D4XGaming.Devices.dll` | 101376 | Native WinRT/COM-Komponente; Manifest registriert `D4XGaming.Devices.D4XDevice` |
| `D4XGaming.Devices.winmd` | 5632 | Metadaten der Geräte-/Nachrichtenschnittstelle und Firmware-/Hardwareversionseigenschaften |
| `FirmwarePackages/JL_Upgrade_Gip.dll` | 119808 | Nativer GIP-Updater mit Firmware-Lader, Versions-/Kompatibilitätsprüfung, Transportcallbacks, Flash- und CRC-Pfaden |
| `Web/js/app.4b7a6fef.js` | 1975162 | Vue-/Webpack-Oberfläche, Konfiguration, Kalibrierung und Firmwaredialog |
| `Web/js/chunk-2d0e1bd0.a6548804.js` | 50305 | Markdown-Renderer für Änderungsnotizen; kein eigener Firmwaretransport |
| WebView2Loader / Microsoft.Web.WebView2.Core | 165968 / 773712 | Windows-WebView-Infrastruktur, kein belegter eigenständiger Controllerdecoder |

EXE und Haupt-DLL haben keinen CLR-IL-Verzeichniseintrag; das Manifest nennt
`ilc.exe` als OptimizingToolset. Eine gewöhnliche C#-Decompilation reicht
deshalb nicht. Die Haupt-DLL trägt die Dateiversion `1.0.0.0`, die JL-DLL
`1.0.0.1`; das sind **keine** Nexus-Paket- oder Controllerfirmwareversionen.
Eingebettete PDB-Pfade sind vorhanden, passende PDB-Dateien fehlen im Hauptpaket.

Im Hauptpaket und den Eintragsnamen des äußeren ZIP wurden **keine `.sys`
oder `.inf`** gefunden. Das ist keine Aussage über die zusätzlich von Windows
bereitgestellten Treiber. D4X und JL haben keine direkten HID-/WinUSB-Importe;
der Transport wird über Windows-Schnittstellen beziehungsweise Callbacks
abstrahiert. Eine bestimmte Windows-Kerneltreiberkette ist damit nicht bewiesen.

## 3. Firmwareversionen und Auswahl eines Updates

### Geräteversionen

D4X-WinMD enthält `get_FirmwareVersionInfo` (Offset `0xd8e`),
`get_HardwareProductId` (`0xda6`), `get_HardwareVendorId` (`0xdbc`) und
`get_HardwareVersionInfo` (`0xdd1`). Nachrichtenmethoden heißen
`SendMessage`, `SendMessageA`, `GetMessageB` und `SendReceiveMessageC`
(`0xe7f`, `0xe9b`, `0xea8`, `0xebd`). Das belegt eine Windows-API,
noch keine Linux-tauglichen Abfragebytes.

Die Haupt-DLL enthält außerdem `ReadFirmwareVersion` und
`ReadFirmwareVersionAck` bei `0x9d0e56`/`0x9d0e6a`,
`LoadFirmwareVersions` bei `0x9c1492`, sowie getrennte
`DeviceDfuPackage`-/`DongleDfuPackage`-Namen und WFF-/ZZZ-Varianten.
Der Web-Firmwaredialog verwendet vom Backend gelieferte
`controllerFirmwareVersion`/`dongleVersion`; seine Auswahl hängt von
`connectionType == "Wired"` ab. Diese Oberfläche belegt die Trennung beider
Versionen, nicht den kompletten nativen Empfangs-/Dekodierpfad.

### Updateauswahl und Aufrufkette

Der moderne Firmwaredialog, Webpack-Modul `f9c0`, erhält
`device.config.dfuPackageInfo` sowie `state.firmwareVersion` und Felder wie
`Version`, `Identifier` und `hasUpdate`. Der nachweisbare Aufrufweg ist:

```text
UpdateDialog.update
  → commonReq("requestToUpdate", deviceId)
  → send("commonReq", {requestType, deviceId, payload})
  → chrome.webview.postMessage({action, payload})
  → native Windows-Anwendung
```

Fundstellen in `app.4b7a6fef.js`: `update()` bei Byte `1945945`,
`commonReq` bei `599361`, `send` bei `595850`. Manuelle Dateiauswahl führt
zu `requestSelectFileToUpdate` ab `1943602`. Die Haupt-DLL importiert
`JL_loadFirmwareData`, `JL_getFirmwarePidVid`, `JL_getFirmwareDataCRC`,
`JL_registerGipOperations`, `JL_handleGipData`, `JL_upgradeDeviceByHandle`
und weitere Updatefunktionen direkt. Der konkrete Bridge-Handler und die
Modell-/Versionsvergleichslogik wurden nicht vollständig rückverfolgt.
Der statisch zugeordnete Katalogkonstruktor ruft allerdings eine
Dateinamen-Auswertung auf: VA `0x18141b650`, Regex `V(\d+)_Key\.ufw`
bei Dateioffset `0xdb978c` und Formate bei `0xdb97c4`/`0xdb769c`.
Drei Ziffern werden als `x.y.z`, zwei als `x.y` formatiert. Beispielsweise
ergibt `V209` die **Katalogversion 2.0.9**, `V144` die Version 1.4.4.
Das ist eine native Zuordnung des gebündelten Angebots, keine Live-Abfrage
und noch kein vollständiger Vergleich mit der Gerätefirmware.

Eine zusätzliche Store-Aktion `updatePackage` (Byte `588246`, Modul `56d7`)
sucht nach `Model` und `PackedFirmware.Version/Path`. Sie verwendet ein anderes
Schema und ein lokal nicht definiertes `HasUpdate`. Sie wird deshalb nur als
älterer beziehungsweise extern ergänzter Kandidat dokumentiert, **nicht** als
nachgewiesener aktiver Online-Katalog.

### Enthaltene G7-Pro-Pakete und Varianten

Alle Pfade unten liegen unter `FirmwarePackages/G7Pro/`; zu jedem Eintrag
existieren **`_Key.ufw` und `_No_Key.ufw`**, jeweils mit der angegebenen Größe.
Versionen sind zunächst Dateinamentokens, keine am Controller gelesenen Werte.

| Paketgruppe | DG-Dateistamm / Bytes je Datei | DV-Dateistamm / Bytes je Datei |
|---|---|---|
| `PCWireless` | `JS_3103_DG_V144` / 1270784 | `JS_3103_DV_V209` / 1903616 |
| `WFF` | `JS_3103_U_DG_V510` / 1271296 | `JS_3103_U_DV_V515` / 1904160 |
| `ZZZ` | `JS_3103_U_DG_V604` / 1271296 | `JS_3103_U_DV_V608` / 1904160 |

Native UTF16-Pfadliterale beginnen bei `0xd9128c`/`0xd91334` (PCWireless),
`0xd913ec`/`0xd91494` (WFF) und `0xd91514`/`0xd91594` (ZZZ).
Der Initialisierer VA `0x18118ba70`, Dateioffset `0x1188e70`, erzeugt
tatsächlich sechs Paketobjekte mit diesen Pfaden. **Dasselbe Standard-DV-
Objekt erhält `G7Pro`, das Standard-DG-Objekt `G7ProDongle`.** Das geht
über Textnachbarschaft hinaus. DV-Konstruktoren erhalten Argument 1,
DG-Konstruktoren 0; die Enum-/Verbrauchersemantik ist nicht vollständig geklärt.

WFF-DG und beide ZZZ-Objekte erhalten ebenfalls die Zeichenkette `G7ProWFF`.
Solche Namen sind damit keine belegte eindeutige Gerätekennung und dürfen
keine Firmwareauswahl allein bestimmen. **DV = Controller, DG = Dongle**
ist durch Standardzuordnung und getrennte Klassen stark gestützt; genaue
Geräteauswahl, Varianteneigenschaften und Paketkompatibilität bleiben offen.

**Bestätigt:** Nexus unterscheidet Editionen mindestens bei Ressourcen,
Paketpfaden und Updateklassen. **Nicht bewiesen:** konkrete Zuordnung dieser
Pakete zu `100a`, `109c`, `105d` oder `105e`, Hardwareunterschiede,
Austauschbarkeit, aktuellste Version oder zulässiges Cross-Flashing.
Die gemeinsame Linux-Treiberarchitektur für Standard und ZZZ bleibt erhalten.

### Netzwerkadressen: nur Literale, keine Abfrage

In der Haupt-DLL liegen `https://gs.7years-dc.com/` bei UTF16-Offset `0xe6180c`
und `https://orsbjnbwlcsomwpjwexq.supabase.co/functions/v1/rapid-processor`
bei `0xe08914`. Erstere wird bei VA `0x181d76753` tatsächlich referenziert;
derselbe umschaltbare Codepfad wählt alternativ
`http://app.local/index.html` (`0xe61854`). Das stützt eine externe/lokale
UI-Seitenquelle; die konkreten indirekten WebView-Methoden sind nicht aufgelöst.
Die Rolle des Supabase-Literals ist unbekannt. Ein Firmwareendpunkt ist bei
keiner dieser Adressen belegt. `app.local` ist eine lokale WebView-Adresse;
die enthaltene Microsoft-CAB-Adresse gehört zur WebView2-Laufzeit.
Diese Adressen wurden nicht aufgerufen. Es wurde **keine belastbare
Firmware-Download-URL oder Online-Katalogantwort** nachgewiesen. Die gebündelten
Dateien beweisen, dass Firmwareinhalt bereits im untersuchten Paket vorliegt;
ob weitere Downloads benutzt werden, bleibt offen.

## 4. Updateprotokoll, Bootloader und Integrität

Alle folgenden Protokollbefunde stammen aus **statischem Code der JL-DLL**,
nicht aus einem Updatecapture auf unserem Controller:

- `JL_registerGipOperations` (RVA `0x1ef0`) speichert drei Callbacks.
  Aufrufstellen sprechen für Öffnen, Schließen und Senden. Der genaue
  Callbackvertrag zur Hauptanwendung ist noch nicht vollständig zugeordnet.
- Der Sendepfad RVA `0x1fc0…0x20e7` fragmentiert in **56-Byte-Einheiten**
  mit vier Headerbytes und höchstens **52 Nutzbytes**, verarbeitet in
  **512-Byte-Blöcken**. Dies sind SDK-Transportgrößen, kein Beweis einer
  gleich großen physischen USB-Übertragung.
- `JL_handleGipData` (RVA `0x2120`) prüft mindestens 56 Byte und betrachtet
  den letzten solchen Abschnitt. `0x4a` und `0x4c` führen in Daten- bzw.
  Bestätigungspfade; zwei Korrelationsbytes und Blockzusammenbau sind erkennbar.
- Ein erreichbarer Versionsabfragefehler und ein gesonderter Firmware-/
  Gerätevergleich liegen im Aufrufpfad von `JL_upgradeDeviceByHandle`
  (RVA `0x15330`, interne Routine `0x14a20`). Die Abfrageroutine `0x130a0`
  benutzt einen Konstruktor `0x31f0`, der unter anderem `0x00c1` an
  Pufferposition `+0x10` schreibt. **Das ist kein freigegebener oder fertig
  verstandener USB-Lesebefehl.** Framing, Parameter und Nebenwirkungen fehlen.
- Erase-/Write-/Verify-Fehlerzweige, KEY-Mismatch, Reset-/Reopen-Pfade und
  Schalter `JL_setDualUbootEnabled`/`JL_setDualBackupBurning` sind vorhanden.
  Daraus folgen weder konkrete Bootloader-VID/PIDs noch sichere Eintritts-/
  Austrittsbefehle, Rollbackgarantien oder Wiederherstellbarkeit nach Stromausfall.
  Die UI-Ereignisse `UDiskUpgradeStarted/Finished` belegen ebenso keinen
  tatsächlich getesteten Massenspeicher-Bootloader des G7 Pro.

Integrität hat mehrere getrennte Ebenen:

| Ebene | Tatsächlicher Befund | Grenze |
|---|---|---|
| Paketkonsistenz | Alle 1446 SHA256-Blöcke für 219 Einträge des Hauptpaket-`AppxBlockMap.xml` stimmen überein | Keine Zertifikatsketten-/Herausgebervertrauensprüfung; keine Firmwareauthentizität |
| Paketunterzeichnung | `AppxSignature.p7x` und Zertifikat vorhanden | Vorhandensein ist keine erfolgreiche Signaturprüfung |
| Update-CRC16 | RVA `0x16b0`, Dateioffset `0xab0`: Polynom `0x1021`, Startwert 0, nicht reflektiert | In der Folge Header, rohe Tabelle und logische äußere Abschnitte aller zwölf UFW-Dateien geprüft; keine Signaturprüfung |
| Update-CRC32 | RVA `0x1750`, Dateioffset `0xb50`: reflektiertes Polynom `0xedb88320`, Startwert **`0x26536734`**, kein Final-XOR | Nicht ungeprüft Standard-CRC32 verwenden; keine kryptografische Echtheitsprüfung |
| CRC-Datenfluss | Berechnung an RVA `0xb34b`, Cache `0x1da18`, Ausgabe über `JL_getFirmwareDataCRC` (`0x11c20`); separate Originalfelder über `JL_getFirmwareOrigCRC` (`0x11c80`) | Separater SDK-CRC32-Cache nicht vollständig zu jedem UFW nachgerechnet; Original-CRC-Export nicht direkt von der Haupt-DLL importiert |

Die erste Prüfung der 128 Anfangsbytes zeigte Unterschiede nur an
`0x00…0x03` und `0x44…0x45`. Die ausdrücklich beauftragte Fortsetzung unten
löst nun Header und Dateitabelle auf. Das gilt nicht als Signaturprüfung:
`KEY`, kryptografische Frameworkklassen und CRC-Prüfungen belegen weder
Firmwareauthentizität noch die sichere Eignung für ein reales Gerät.

Der Debugpfad der Update-DLL enthält bei `0x18f24`
`hjc_ac695x_xbox_firmware_update_gip`. Das ist ein SDK-/Buildhinweis,
**keine Identifikation des IMU-Chips oder des tatsächlich verbauten MCU**.

### Firmware als Daten geöffnet: Containerstruktur belegt

Auf [tester]’ ausdrücklichen Folgeauftrag wurden die zwölf bereits vorhandenen
G7-Pro-UFW-Dateien selbst geöffnet. Ausschließlich Byteanalyse und ein eigener,
aus statisch geprüftem Ladercode abgeleiteter Datenleser; keine Ausführung
von Hersteller-DLL oder Firmware und keine Geräte-/Netzwerkzugriffe.
Originale bleiben unverändert, eigene Belege und etwaige dekodierte Daten
privat unter `.local/research/20261015-gamesir-nexus/firmware-sensor/`.

Die Header-/Tabellentransformation ist ein rücksetzbarer 16-Bit-XOR-Strom
mit Startwert `0xffff`. Der Lader setzt ihn für den 64-Byte-Header und jeden
80-Byte-Dateieintrag neu an. Damit sind bei **allen zwölf Dateien**
die folgenden Prüfungen reproduzierbar bestanden:

- CRC16 des dekodierten Headers über Byte 2…63 gegen sein Feld bei 0.
- CRC16 der noch kodierten Dateitabelle ab Datei `0x40` über
  `80 × Eintragszahl` gegen das Headerfeld bei 2.
- Dateigröße und Abschnittsgrenzen gemäß dekodierter Tabelle.

Der Header enthält das Textlabel **`AC695X`** ab dekodiertem Offset `0x10`.
Das belegt die Container-/SDK-Familienkennung. Es identifiziert weder den
IMU-Chip noch ungeprüft den tatsächlich bestückten Mikrocontroller.
DG-Pakete enthalten elf, DV-Pakete zehn Tabelleneinträge. Die Tabelle benennt
`flash.bin`, `flash2.bin`, `flash3.bin`, `flash4.bin`, `ota.bin`,
`isd_config.ini`, `script.ver`, `blimit.bin`, `tail.bin` und einen leeren
`info.log`-Eintrag; DG zusätzlich `br23loader.bin`.

Die Key-/No-Key-Paare unterscheiden sich in großen Nutzdatenbereichen,
nicht nur im zuvor betrachteten Header. Gemeinsame Dateinamen, gleiche
Abschnittslängen oder große übereinstimmende WFF-/ZZZ-Bereiche beweisen
keine Firmwareaustauschbarkeit. Es wurde kein Paket für Hardware ausgewählt.

Auch die äußeren Nutzdaten wurden mit dem eigenen, nur auf Dateibytes
arbeitenden Leser abgeleitet. Die Abschnittstransformation setzt den
XOR-Zustand in 32-Byte-Blöcken anhand eines abgeleiteten Seeds und des
Abschnittsversatzes neu an (statische Laderfunktionen RVA `0x18f0` und
`0x19c0` in `JL_Upgrade_Gip.dll`). **Alle 126 Einträge**, einschließlich
zwölf leerer `info.log`-Einträge, stimmen nach erforderlicher Transformation
über ihre logische Länge mit der tabellierten CRC16 überein. Padding zählt
nicht zur logischen Nutzdaten-CRC; Endmarker und dessen CRC sind ebenfalls
bei allen zwölf Paketen konsistent. Das ist Dateikonsistenz, keine
Signatur-/Herausgeberprüfung und keine Updatefreigabe.

Der gespeicherte `ota.bin`-Abschnitt ist über alle zwölf Dateien bytegleich.
Darin sichtbare allgemeine Update-/AC695x-Texte dürfen daher nicht als
konkreter Sensortreiber für Standard oder ZZZ ausgegeben werden.

Die `flash*.bin`-Nutzdaten enthalten eine weitere, 32-Byte-basierte
Verzeichnisstruktur. Header und Eintragsprüfsummen lassen sich prüfen;
die benannten Bereiche umfassen `uboot.boot`, `isd_config.ini`,
`app_dir_head`, `app_dir_head2` und `key_mac`. Die geprüfte Folge enthält
vier normale CRC-valide Header und einen CRC-validen Abschlussheader.
Die Fortsetzung unten klärt das Feld `app_dir_head +8` als Splitgrenze:
Die frühere pauschale Deutung als Länge war falsch. Globale Bankadressen
und gepackte Dateioffsets bleiben getrennt. Verzeichnisdekodierung ist keine
vollständige Entschlüsselung, Dekomprimierung oder Disassemblierung des
Firmwarecodes.

Die 24 dekodierten `isd_config.ini`-/`script.ver`-Dateien wurden zusätzlich
unabhängig gegen Hashes und CRC16 geprüft. `CHIP_NAME=AC695X` steht am
INI-Keyoffset `0x118` bei DG beziehungsweise `0x116` bei DV;
`FLASH_SIZE` nennt 512K beziehungsweise 1M. Das sind konfigurierte MCU-/
Packtoolwerte, kein nachgewiesener IMU-Chip. Die INI-Felder `VID` und `PID`
enthalten Versions- beziehungsweise Modelltexte und sind **keine USB-VID/PID**.
`EOFFSET` ist laut Konfigurationskommentar ein Flashversatz in 4-KiB-Einheiten,
kein Gyrobias. In diesen Konfigurationsdateien wurde kein Sensormessbereich,
Gyrofaktor oder zugeordneter Sensorregisterblock gefunden. Die Aussage gilt
für diese Dateien, nicht den gesamten Firmwarecode.

Die Untersuchung liefert **noch keinen Gyrofaktor**. Dafür muss
die Sensorinitialisierung beziehungsweise Kalibrierung mit eventuellen
Zwischenskalierungen und genau den ausgegebenen IMU-Rohkanälen verbunden
werden. Ein Chipname, Messbereichsregister oder eine passende Zahl allein
reicht nicht. Die bekannten 12204 Pakete und experimentellen 8192 LSB/g
bleiben von dieser Dateiformatanalyse unverändert.

### Innere Flashadressierung und Anwendungsteil weiter aufgeklärt

Die nächste ausschließlich statische Fortsetzung verbindet jetzt den nativen
Ladercode mit den zuvor CRC-geprüften 48 `flash*.bin`-Dateien. Alte private
Belege bleiben unverändert; die frühere Deutung von Feld `+8` als Länge bei
`app_dir_head` ist ausdrücklich korrigiert. Die damals berechneten 96
scheinbaren Bereichsüberschreitungen waren dadurch kein Dateidefekt.

| Feld / Bereich | Jetzt belegte Bedeutung |
|---|---|
| äußerer UFW-Tabelleneintrag `+8` | tatsächlicher Quelldateiversatz des Flash-Abschnitts |
| inneres `app_dir_head`, DWORD `+8` | lokale Trennstelle zwischen Prefix und Appcontainer |
| derselbe Record, DWORD `+4` | Trennstelle plus 32 Byte |
| `app_dir_head2`, DWORD `+8` | andere logische Bankgrenze; kein Byteumfang ab `+4` |
| Appcontainer an der Trennstelle | 32-Byte-Header; sein DWORD `+8` ist die gespeicherte Inhaltslänge ab Headerende |

Der Defaultlader RVA `0x56d0` lädt die Trennstelle bei `0x7ece` und kopiert
Prefix `[0:split]` sowie Appteil `[split:Dateigröße]` getrennt
(`0x7ede`, `0x7f73…0x802b`). Modebytes 1/16 wählen eigene Cachezweige,
bezeichnen aber keine hier identifizierte CPU oder Sensorauflösung.
**Alle 48** Trennstellen liegen innerhalb der jeweiligen Datei. An ihnen
stimmen der Appcontainer-Header-CRC sowie der CRC16-Wert bei Header `+4`
über genau die nachfolgenden, durch DWORD `+8` begrenzten gespeicherten
Inhaltsbytes. Die Inhaltsprüfsumme gilt für gespeicherte Bytes und beweist
noch keinen dekodierten Anwendungscode.

Die Markerfamilien haben jetzt konkrete statische Pfade: Im Defaultpfad
werden `ffff`, `ff00`, `00ff` getrennt behandelt. Der Export
`JL_setDualUbootEnabled` bei `0x11ae0` verändert einen internen Selektor;
der alternative Pfad `0x11b00 → 0x15910 → 0xf220 → 0xc7f0` akzeptiert
`0fff` bei `0xd2ac`/`0xd2fa`. Seine Prefix-/App-Kopien verwenden ebenfalls
die belegte Trennstelle. Damit sind 36 Default- und zwölf alternative
Markerfälle erklärt. **Welcher Nexus-Modellaufruf den alternativen Pfad
im realen Betrieb auswählt, ist weiterhin nicht vollständig verfolgt.**
Es wurde kein solcher Herstelleraufruf ausgeführt.

Relocation verändert in den geprüften Zweigen zwischengespeicherte
32-Byte-Verzeichnisrecords, nicht den kopierten Appkörper. Beobachtet sind
exakt `-0x10000`, `+0x10000` und Addition `0xffff1000` modulo 2³²,
Letztere also `-0xf000`. Ein Zweig hängt zusätzlich `0x1000` Bytes `ff`
an den Prefix. Der Helfer `0xc000` ersetzt einen 32-Byte-Record; die
Headerprüfsumme wird neu berechnet. Daraus folgt keine universelle Formel
für sämtliche physischen Flashadressen, keine vollständige virtuelle
Flashrekonstruktion und keine zulässige Schreiboperation auf Hardware.

### Key-/No-Key-Schicht und verbleibender Sensorcode-Blocker

Die ersten 32 Inhaltsbytes bilden `app_area_head`. Je Dateiklasse wurde
ein eindeutiger 16-Bit-XOR-Startwert mit bekanntem Metadatanamen und CRC
ermittelt und unabhängig geprüft. Alle **48** Metadatensätze sind gültig;
ihr Key-/No-Key-Klartext stimmt paarweise überein. Abgeleitete Startwerte,
volle Masken und Binärdaten bleiben privat.

Die Beziehung reicht über die Metadaten hinaus: **24 vollständige
Key-/No-Key-Inhaltspaare mit insgesamt 7960580 Bytes** stimmen nach der
jeweiligen 32-Byte-Streamnormalisierung vollständig überein, einschließlich
letzter Teilblöcke. Das ist ein vollständiger Datenvergleich dieser
CRC-begrenzten Bereiche, keine bloße Ähnlichkeit einzelner Zahlen.

Ein zuvor betrachteter DG-Körperkandidat verwendete nach Entfernen seines
32-Byte-Metadatenkopfs unverändert dessen ungeklärtes Längenfeld. Er bezog
dadurch 32 Bytes `ff`-Padding hinter dem bestätigten Inhalt ein. Die dortige
letzte Blockabweichung ist damit erklärt und kein Firmwareunterschied.
Die Bedeutung von `app_area_head +4/+8` bleibt von der belegten
Appcontainerlänge getrennt; `0x1e000c0` ist kein lokaler Dateiversatz.

**Stand vor dem nachfolgenden Strukturfolgepass: Der Anwendungskörper war
noch nicht belastbar dekodiert.**
Einfache feste 32-Byte-XOR-Kandidaten erfüllen die angenommene innere
Feld-2-Prüfsumme in keinem der 48 Fälle. Auch 14 gezielte Varianten des
bekannten adressabhängigen äußeren XOR-Algorithmus ergaben bei zwei
Referenzdateien keinen passenden Wert. Der innere Prüfsummenbezug selbst
ist dabei noch offen; diese Tests schließen andere Schichten nicht aus.
Der untersuchte Windows-Lader kopiert diesen Appkörper in den benannten
Zweigen unverändert, statt dort Sensorregister oder Einheiten auszuwerten.

Der begrenzte Erkennbarkeitspass fand keine konkreten Sensor-/Einheiten-
bezeichnungen in ASCII/UTF16, keinen vollständigen prüfsummengültigen
Zlib-Stream unter 6993 Kandidaten und keine gültigen PE-/Bzip2-Dateien.
Das sind Ergebnisse für die untersuchten Daten/Transformkandidaten,
**kein Nachweis der Abwesenheit von Sensorcode oder Kompression**.
Weder ISA noch IMU-Chip, Messbereichsregister, Achsensignale oder
Sensorregister → Verarbeitung → bekannter 64-Byte-IMU-Report sind belegt.

Der damalige nächste fachliche Schritt war ein validierter Bezug zwischen
innerer Appstruktur, Körperdekodierung und Prüfsumme. Erst dann lassen sich
Sensorinitialisierung und eventuelle Zwischenskalierungen seriös verfolgen.
**Kein neuer Gyrofaktor; 8192 LSB/g, IIO und SDL-Freigabe unverändert.**
Quellenhashes, 20 abgegrenzte Ladercodeintervalle und repräsentative
Dateizuordnungen stehen im [Quellmanifest](nexus-source-manifest.json).
Neue private Belege: `.local/research/20261015-gamesir-nexus/inner-flash-20261015/`.

### LSM6DSO-/CTRL2_G-Folgepass vom 16. Oktober

[tester] bestätigt die DigiKey-Fotoidentifikation LSM6DSO/LSM6DSOTR; diese
externe Zuordnung kommt nicht aus der Firmwaredekodierung. Die vorhandene
Linux-Treiberdatei `st_lsm6dsx` wurde statisch als zusätzliche Registerreferenz
geprüft: WHO_AM_I `0x0f`/`0x6c`, Gyroregister `0x11`, Maske `0x0c`, vier
maskierte Werte `00/04/08/0c` und Gewinne passend zu 8,75/17,5/35/70 mdps/LSB.
Kein Modul geladen; die Vierertabelle belegt nicht den gesonderten ±125-Modus.

Die gezielte erneute Prüfung aller zwölf UFW-Quellen/48 Flashdateien erhält
die vorhandenen CRC-/Hashbelege. Alle fünf geprüften Sensor-/Registernamen
bleiben ohne ASCII-/UTF16-Treffer. Kurze Registerfolgen einschließlich
dreier aufeinanderfolgender Adressen haben Kandidaten, aber keinen belegten
Codeverweis oder Schreibpfad. Key-/No-Key-/Bankduplikate sind keine
unabhängigen Nachweise. 36 gezielte strukturähnliche Folgerecords erfüllen
die geprüften Header-/Inhalts-CRC-Hypothesen nicht; innere Code-/Formatdeutung
weiter offen, keine Defektbehauptung.

**Stand dieses ersten Registerfolgepasses: kein aktiver CTRL2_G-Wert oder
GameSir-Gyrofaktor.** Die damalige Blockade war die innere Körperdekodierung;
sie wird durch den folgenden Strukturpass für die enthaltenen Dateien gelöst. Danach
müssen Initialisierung, spätere Messbereichsänderungen und Rohwertweitergabe
bis zum bekannten USB-Bericht nachgewiesen werden. Die Linux-Referenz ist
kein Nachweis eines GameSir-Schreibwerts. [Detailbefunde und Referenzfundstellen](IMU-STATISTIK-UND-SENSORIDENTIFIKATION.rst),
eigene Metadaten im [Quellmanifest](nexus-source-manifest.json) und
[Sensorstatus](imu-sensor-identification.json).
Neue private Belege: `.local/research/20261016-lsm6dso-ctrl2g/`.
Keine App-/Firmwareausführung, Netzwerk-, Geräte- oder Laufzeitaktion.

### Innere Appstruktur und Prüfsummen am 16. Oktober aufgelöst

Der eigene Byte-Leser berücksichtigt jetzt die Position jedes Blocks relativ
zum **Beginn des gespeicherten Appinhalts**, statt den gleichen Stream in
jedem Block zu wiederholen. Das entspricht dem bereits statisch gelesenen
positionsabhängigen Transformtyp der JL-Laderfunktion bei RVA `0x18f0`.
Die frühere feste Klassennormalisierung belegte Key-/No-Key-Gleichheit,
war aber noch keine vollständige Dekodierung. Konkrete Startwerte, Masken
und Herstellerbytes bleiben privat. DLL und Firmware wurden nicht ausgeführt.

Ein neuer Ansatzpunkt war die CRC-Differenz zwischen den vier Flashvarianten:
Die veränderlichen Records zeigten konsistente CRC16-Beziehungen über 30
Headerbytes. Allein die CRC-Anpassung lässt zwei mögliche Streamzustände
pro Header zu. Deshalb wurden zusätzlich Namen, Offsets, Grenzen,
benachbarte Dateibereiche und deren **Inhaltsprüfsummen** geprüft. Ein einzelner
angepasster Header wäre kein Dekodierungsnachweis.

Für alle zwölf UFW-Quellen und 48 Flashdateien bestätigt:

| Position relativ zum Appinhalt | Eintrag | Bestätigte Bedeutung |
|---|---|---|
| `0x00` | `app_area_head` | WORD `+0`: Header-CRC über `[+2,+32)`; DWORD `+8`: Ende des inneren Appbereichs relativ zu dessen Beginn; WORD `+2`: CRC über `[32, Bereichsende)` |
| `0x20` | `app.bin` | DWORD `+4/+8`: lokaler Offset/Länge der Datei; WORD `+2`: CRC ihres dekodierten Inhalts |
| `0x40` | `cfg_tool.bin` | Gleiche Offset-/Längen-/Inhalts-CRC-Struktur |
| `0x60` | `VM` | Gültiger Record mit Speicher-/Konfigurationsfeldern; keine lokale Dateischeibe daraus abgeleitet |
| `0x80` | `PRCT` | Gültiger Record, zusätzlicher Text `CODE`; Laufzeitsemantik offen |
| `0xa0` | `BTIF` | Gültiger Record, zusätzlicher Text `AUTO`; Laufzeitsemantik offen |

Die sechs 32-Byte-Records bilden genau `0xc0` Bytes. `app.bin` beginnt bei
`0xc0`, `cfg_tool.bin` folgt unmittelbar und endet genau am Bereichsende aus
`app_area_head +8`. Die frühere Deutung dieses Feldes als Länge **nach**
dem Metadatenheader war damit um 32 Bytes falsch. Das ist keine beschädigte
Firmware. DWORD `+4` des Metadatenheaders ist weiterhin keine lokale
Dateiposition; seine `0x1e000c0` passt zu zahlreichen String-Adressliteralen,
belegt allein aber weder CPU-ISA noch einen ausgeführten Einstiegspunkt.

| Paketfamilie | `app.bin` Bytes | `cfg_tool.bin` Bytes | Appbereichsende | Weitere gespeicherte Bytes dahinter |
|---|---:|---:|---:|---:|
| PCWireless DG144 | 246552 | 904 | 247648 | 0 |
| PCWireless DV209 | 379140 | 880 | 380212 | 35151 |
| WFF DG510 | 246884 | 904 | 247980 | 0 |
| WFF DV515 | 379364 | 880 | 380436 | 35151 |
| ZZZ DG604 | 246884 | 904 | 247980 | 0 |
| ZZZ DV608 | 379364 | 880 | 380436 | 35151 |

Die zusätzlichen DV-Bytes sind im äußeren gespeicherten Inhalts-CRC enthalten,
gehören aber nicht zum gerade bestätigten inneren Appbereich. Im folgenden
MCU-Folgepass werden davon DV209-Tonressourcen und ein zlib-Objekt erklärt;
andere Teile bleiben offen. Sie werden nicht als Teil von `app.bin`, Kalibrierung oder
Padding umetikettiert. VM-/PRCT-/BTIF-Adressen werden nicht als lokale
Offsets gelesen.

**Nachweise:** 288 innere Header-CRC, 48 Bereichs-CRC und 96 Datei-CRC gültig.
Eine zweite eigene Implementierung mit anderer Stream-/CRC-Berechnung
reproduziert alle 48 vollständigen dekodierten Inhalte bytegenau. CRC-
Referenztest `123456789` ergibt `0x31c3`; 24 gezielte Prüfungen mit falschem
Ursprung oder im Speicher beschädigten Header-/Dateibytes werden abgewiesen.
Alle 24 Key-/No-Key-Inhaltspaare bleiben identisch. Innerhalb jedes Quellpakets
sind `app.bin` und `cfg_tool.bin` über die vier Flashvarianten bytegleich;
die wenigen Unterschiede im dekodierten Appcontainer liegen in Records.
Verschiedene Versionen/Editionen haben weiterhin verschiedene Appdateien.

**Sensorpfade erstmals lesbar:** Im DV209-`app.bin` mit SHA256
`15e48c1c8a6cb9584b059bf54d1f8ad6131a4a3c5b6c082eba394310d03db1d6`:

| Dateioffset in der extrahierten `app.bin` | Fund |
|---|---|
| `0x230f0` | `Enter Sensor Cal Mode!` |
| `0x25629` / `0x25637` | `lsm6ds3 err!` / `qmi8658 err!` |
| `0x25eaf` | `Sensor cal start` |
| `0x27370` | `gyro factory = %d %d %d` |
| `0x288c1` | `rx usb sensor calibrate command` |
| `0x289c9` / `0x28f85` | Meldungen `Sensor IS QMI8658` / `Sensor IS LSM6DS3TR` |

Entsprechende Meldungen sind in DV515/DV608 mit eigenen, dokumentierten
Offsets vorhanden. `gyro factory` beweist keine physikalische Sensitivität
oder eine ausgelesene Kalibrierung. Die kompilierten Sensornamen bestimmen
keinen real ausgewählten Chip, keine bestückte PCB-Variante und keinen
aktiven Messbereich. [tester]' externe LSM6DSO-Fotoidentifikation bleibt als
separater Nutzerbeleg erhalten; die Beziehung zu diesen Firmwareversionen
und benannten Treiberpfaden ist offen. Auch die Zuordnung dieser Paketversionen
zur tatsächlich auf [tester]' Controller installierten Firmware ist hier
nicht hergestellt. Keine neue breite Chipsuche.

Ein vollständiges Little-Endian-Adressliteral für die Kalibriermodusmeldung
liegt in DV209 bei `app.bin +0x1071a`, in DV515/DV608 bei `+0x10722`.
Das ist eine konkrete Verweisfundstelle, noch kein dekodierter Aufruf.
Die einfachen Tabellenhypothesen für Register `0x10/0x11/0x12` liefern in
jedem DV-Appinhalt nur eine unzugeordnete Folge fortlaufender Zahlen,
keinen bestätigten Sensorinitialisierungsblock. Aus einer Bytefolge wird
weiterhin kein CTRL2_G-Schreibbefehl abgeleitet.

**Neue konkrete Grenze:** Für den nun prüfsummengültig lesbaren Appinhalt
fehlen eine belegte MCU-Befehlszuordnung und ein passender statischer
Instruktionsdecoder. Buildtexte nennen BR22/BR23/AC695X, bestimmen aber
allein noch keine nachgewiesene ISA. Die vorhandenen GNU-/LLVM-Werkzeuge
und lokal geprüften Dateien liefern dafür derzeit keinen bestätigten Decoder.
Keine ARM-/RISC-V-Disassemblierung auf Verdacht und keine Firmwareemulation.
Als Nächstes Sensorwahl-/Initialisierungsroutine an den jetzt lesbaren
Ankern verfolgen, den letzten wirksamen CTRL2_G-Wert einschließlich
Rekonfiguration bestimmen und anschließend die Register→USB-Skalierung
prüfen. **Aktiver Messbereich und Gyrofaktor bleiben unbekannt.**

Neue private Belege: `.local/research/20261016-inner-structure-followup/`.
Alle 727 vorangegangenen Belegdateien sind unverändert; Rohdateien und
Dekodierungen bleiben privat. Experimentelle 8192 LSB/g, SDL-Profil und
laufender Treiber unverändert. Keine App-/Netz-/Hardware-/Treiberaktion.
Hash- und Prüfdaten im [Quellmanifest](nexus-source-manifest.json).

### MCU-Teilformate und Kalibrierungsverweise, weiterer Offline-Pass

**Ergebnis:** Drei begrenzte Muster sind über gespeicherte Firmwarebytes
empirisch erhärtet. Das ist weiterhin keine vollständige oder normativ
belegte Jieli-ISA. Kein Firmwarecode wurde ausgeführt oder emuliert.
Die lokale Referenzsuche fand weder eine passende Befehlsbeschreibung noch
einen bestätigten Jieli-/PI32-/BA2-Decoder in den geprüften Werkzeugen,
Dokumentationen und Downloads. BR22/BR23/AC695X bleiben Buildhinweise.

| Teilmuster | Belegter Zusammenhang | Grenze |
|---|---|---|
| 6-Byte-Literalform | Ein Prefix und ein zusammenhängender LE32-Wert verweisen unter Basis `0x1e000c0` auf echte Texte | Slotnummern sind noch keine normativ bestätigten Registernamen/ABI |
| Relatives 4-Byte-Muster | Zwei LE16-Halbwörter liefern 6+16 Displacementbits; mit Vorzeichenerweiterung auf 22 Bit gilt `Ziel = Position + 2 × Displacement` | Ein Prefixflag bleibt unbenannt; CALL-/JUMP-/Bedingungssemantik nicht vollständig belegt |
| 4-Byte-Konstantenform | Fortlaufende 32-Bit-Bitlöschmasken passen exakt zur Vorzeichenerweiterung eines 16-Bit-Werts; ab Bit 15 folgt die volle 32-Bit-Literalform | Kein allgemeiner Register-/Speicherdecoder und keine vollständige Instruktionssegmentierung |

Die ersten beiden Muster hängen konkret zusammen:

| Controller-App | Kalibriermeldung | Literalfolge | Anschließendes relatives Muster | Gemeinsamer Zielkandidat |
|---|---|---|---|---|
| DV209 | `0x230f0` | `0x10718` | `0x1071e` | `0x44d34` |
| DV515 | `0x231c8` | `0x10720` | `0x10726` | `0x44e14` |
| DV608 | `0x231c6` | `0x10720` | `0x10726` | `0x44e14` |

Alle Offsets beziehen sich auf die extrahierte `app.bin`. Die jeweils
benachbarten EEPROM-Lese-/Schreibmeldungen führen zum selben Ziel.
Zwei getrennte eigene Leser bestätigen je Version 50 unmittelbar benachbarte
Textliteral-/Transferstellen; die ersten 92 Zielbytes stimmen über alle
drei Versionen überein, SHA256
`1e38e03337a68e18d88bef237273a4b855fdb62f33b05dc38cdf8a979f2db7f2`.
Ein gemeinsamer Textausgabepfad ist damit stark gestützt; eine konkrete
`printf`-Implementierung oder tatsächlich ausgeführte Sensorinitialisierung
ist daraus nicht bewiesen.

Die zunächst plausible Verkürzung auf signed16 würde für DV209 fälschlich
`0x4d34` statt `0x44d34` ergeben. Deshalb ist sie verworfen. Der gesamte
Halbwortscan findet je Version 424 Kandidatenverweise auf den richtigen
Zielkandidaten. Diese Zahl ist keine Anzahl belegter Aufrufe: Ein vollständiger
Code-/Daten- und Instruktionsgrenzenparser fehlt, Fehlpositive bleiben möglich.

Die Konstantenfolge in DV209 `[0x12af8,0x12b64)` belegt 16 aufeinanderfolgende
Bitlöschmasken für Bits 5 bis 20. Dasselbe 108-Byte-Stück liegt in DV515/DV608
bei `0x12b00`, SHA256
`fd50be1afcd8e5becb333e289e88653575f706aab629f2595bdb228b2cb61dea`.
Sie bestätigt insbesondere die vorzeichenbehaftete Deutung der kurzen Form;
sie ist kein Sensorregisterblock. Kompakte Blattfragmente und mögliche
Rückkehrwörter bleiben bewusst ohne erfundene Mnemonik. Ein eigener
begrenzter Feldleser prüft ausschließlich ausgewählte Stellen, behandelt
unbekannte Formen als undurchsichtig und führt keine Kontrollflussemulation
aus. 175 Fundstellenkontrollen und acht Grenz-/Ablehnungstests bestehen.

**Sensor-Schreibpfad weiterhin offen:** Die Meldungen zu LSM6DS3TR/QMI8658,
Sensorfehlern und `gyro factory` besitzen unter der bestätigten Kandidatenbasis
keine direkt gefundenen vollständigen Adressliterale. Alternative gemeinsame
Adressbasen liefern nur schwache Kollisionen. Das belegt weder toten Code
noch ein RAM-Overlay oder die Abwesenheit einer Initialisierung. Ein
unterstütztes Register-`0x11`-/Schreibwertpaar und ein zugeordneter I2C-
Schreibhelfer wurden nicht gewonnen. Kompakte Argumentformen, Speicher-
operationen und ABI-/Registerzuordnung fehlen hierfür. **Kein aktiver
CTRL2_G-Wert, kein gewählter Gyromessbereich und kein Gyrofaktor.** Die
ursprüngliche Fotoauskunft bleibt als Quelle erhalten; die exakte Variante
ist wieder offen. Das SDL-Kalibrierungsprofil bleibt unverändert.

**Zusätzlich DV209-Nachlauf zugeordnet:** Ab `full-content +0x5cd34` liegt
ein `tone`-Verzeichnis mit Index und WTG-Dateien für Verbindungs-, Start-,
Stopp- und andere Töne. 28 Header-CRC, 27 Datei-CRC und die Bereichs-CRC
sind gültig. Ein vollständiger zlib-Stream bei `+0x65600` umfasst 131 Bytes
und liefert 327 Bytes; EOF und Adler32 `0x6eeb2a61` sind bestätigt.
Zehn Float-Tripel sehen wie Frequenz-/Verstärkungs-/Q-Werte aus; Audio-EQ
ist eine Hypothese. Darin enthaltene Zahlen wie 1000 oder 2000 sind **keine
Gyromessbereiche**. Kein ELF-/PE-Symbolsatz oder ISA-Beleg gewonnen;
weitere Restbytes und andere DV-Versionen sind dadurch nicht abschließend
erklärt. Die Ton- und zlib-Prüfungen sind unabhängig nachgerechnet.

Nächster gezielter Schritt: fehlende Kompakt-/Speicheroperationen anhand
einer belastbaren ISA-Referenz oder weiterer unabhängiger Codebelege
auflösen; erst dann Sensorwahl, letzte wirksame Initialisierung und
CTRL2_G bis zum Register→USB-Datenfluss verfolgen. Keine blinde Wahl eines
Standarddecoders und keine Übernahme eines plausiblen Zahlenwerts.
881 frühere Belegdateien unverändert, neue private Daten unter
`.local/research/20261016-mcu-instructions/`. Nur eigene Befunde und Hashes
versioniert; keine Herstellerbytes, Dekodierungsmasken oder Schlüssel in Git.
Keine App-, Netzwerk-, Hardware-, Treiber- oder Kalibrierungsänderung.

### Sensorverweise: begrenzter Folgepass vom 18. Oktober

Die bestehenden `app.bin`-Dateien DV209/DV515/DV608 wurden erneut gegen ihre
Hashes geprüft. Die bekannte Kalibriermeldung und ihre relative
Textsenkenzuordnung sind unabhängig reproduzierbar. Für sieben weitere
Sensorlogs wurden vollständige und verkürzte Adress-/Offsetkandidaten,
relative 32-/22-Bit-Kandidaten und String-Innenpositionen geprüft.
Ein neuer belastbarer Initialisierungs- oder Register-Schreibpfad wurde
dadurch nicht gewonnen. Das schließt andere Adressierungsformen nicht aus.

Ein konkreter Gegenbeleg verhindert eine Fehlzuordnung: Ein über alle drei
Versionen stabiler scheinbarer Relativverweis auf `Sensor IS QMI8658`
bei DV209-Dateioffset `0x285c0`, DV515/DV608 `0x286a0` gehört zu einem
gespeicherten USB-HID-Deskriptorblock mit Längen 9+9+7+7
(Interface/HID/zwei Endpunkte). Dessen erstes DWORD ergibt nur zufällig
mit der Position die Sensorlogadresse. Der identische 32-Byte-Bereich hat
SHA256 `eb8ebafb4b26a0dfaa13535882e39c28e767a7d5e88dfaa70f86e689ed8bd584`.
Auch ein versionsstabiler rechnerischer Treffer beweist also keinen
MCU-Codeverweis oder Sensorzugriff.

Die konkrete Analysegrenze bleibt: kompakte Adress-/Speicher-/Argumentformen
und verlässliche Code-/Datengrenzen. WHO_AM_I-Pfad, letzter CTRL2_G-Wert und
Nachskalierung zum USB-Bericht sind weiterhin unbelegt. Bestehende
Werkzeuge wurden genutzt; REA bleibt Reserve. Neue private Belege unter
`build/nexus-followup-20261018/firmware/`, nur eigene Befunde/Hashes in Git.

### MCU-Folgepass: getrennte Speicherabbildung und kompakte Formen

Ein weiterer ausschließlich lokaler Folgepass verwendet die bisherigen
Dateien und Werkzeuge, ohne REA oder Herstellercode auszuführen. Er trennt
neu korroborierte Operand-/Adressfelder weiterhin von ungeklärter
Instruktionswirkung, Registerbezeichnung, ABI und tatsächlich ausgeführtem
Sensorcode. Die drei quellgeprüften Apps bleiben DV209, DV515 und DV608;
sie sind nicht mit der installierten Controllerfirmware gleichgesetzt.

**Kurze Zielfelder:** In vier getrennten, über alle drei Versionen
byteidentischen Bereichen passt ein weiteres 2-Byte-Feldmodell. Für die
geprüfte Klasse mit `h & 0xe0cf == 0x8004` ergibt sich:

```text
d = ((h >> 8) & 31) | ((h & 0x30) << 1)
Ziel = Dateiposition + 2 + 2 × d
```

| DV209-Dateibereich, Ende exklusiv | Gemeinsamer Zielkandidat | Verschiebung in DV515/DV608 |
|---|---|---|
| `0x12adc…0x12b80` | `0x12b6a` | `+0x8` |
| `0x36954…0x369aa` | `0x369a6` | `+0xe0` |
| `0x31c8e…0x31ccc` | `0x31cc8` | `+0xe0` |
| `0x31ce2…0x31d1c` | `0x31d18` | `+0xe0` |

Insgesamt passen 132 ausgewählte Stellen zu den jeweiligen gemeinsamen
Fortsetzungen. Ein weiterer Fall bei DV209 `0xd8fe`, DV515/DV608 `0xd900`
hat Displacement 123 und erreicht `0xd9f6` beziehungsweise `0xd9f8`.
Er widerlegt sowohl eine Verkürzung auf sechs Bits als auch eine signed7-
Deutung. Das ist ein empirisch korroboriertes **positives** Zielfeld;
andere Typbits, unter anderem Bit 6 im unteren Byte, werden nicht
interpretiert. Keine universelle Sprung-/CALL-Semantik oder vollständige
Instruktionssegmentierung behauptet.

**Kompakte Maskenoperanden:** Fünf Wörter im bekannten Maskenkontext
passen zu `field = ((h >> 8) & 31) | ((h & 0x10) << 1)` mit signed6-
Vorzeichenerweiterung. Sie ergeben `−2/−3/−5/−9/−17`, also die
Komplementmasken der Bits 0–4. Zusammen mit den bekannten langen Formen
passen jetzt alle 22 lokalen Maskenwerte für Bits 0–21 über drei Versionen.
Dies belegt Operandbits, keine MOV-/AND-Wirkung oder Registerrolle.
Ein numerisch passendes `0x0f` oder `0x11` wäre weiterhin kein Sensorzugriff.
Die WHO_AM_I-ID-Kandidaten `0x69/0x6a/0x6c` passen nicht in signed6.

Die anders aufgebaute, bisher als blattartig bezeichnete 88-Byte-Folge
bleibt mehrdeutig. Weder die Rolle des Nachfolgeworts noch ein Übergang
zu belegten Langkonstanten ist dort nachgewiesen. Eine lineare Zahlenfolge
und eine One-Hot-Deutung lassen sich ohne Datenflussanker nicht trennen.
Das neue signed6-Modell wird ausdrücklich nicht auf diese andere Klasse
übertragen; eine synthetische Datentabelle kann dieselbe Blattform liefern.

**Load-/Run-Abbildung:** Drei zusammenpassende Startbereichsliterale
benennen einen Suffix der Appdatei. Quelle plus Länge erreicht exakt das
Dateiende; der benachbarte Zieladresskandidat ist null.

| Appversion | Suffix-Dateianfang | Länge | Korroborierte Laufadressbasis |
|---|---|---|---|
| DV209 | `0x4f718` | `0xd1ec` | `0` |
| DV515 / DV608 | `0x4f7f8` | `0xd1ec` | `0` |

Die Geometrie ist nicht bloß aus dem Startbereich geraten: Je Version
verweisen 25 vollständige Literalformen auf dort enthaltene RTOS-Namen
unter genau dieser Abbildung. Beispiel DV209: `vTaskDelete` bei
Dateioffset `0x5a28d` hat Laufadresskandidat `0xab75`, referenziert bei
`0x59d2a`. In DV515/DV608 verschieben sich die Dateistellen um `0xe0`,
die Laufadresse bleibt gleich. Von je 15 unmittelbar folgenden bekannten
22-Bit-Transferformen erreichen zehn dieselbe Laufadresse `0x99e6`.
Andere Nachfolger bleiben bewusst undekodiert. Das stützt einen eigenen
Adressbereich, beweist aber noch keine ausgeführte Kopierschleife, keinen
physischen RAM-Typ und keine Aufrufkonvention.

Alle acht gewählten Sensoranker liegen **vor** diesem Suffix. Eine
Umrechnung dieser Sensoradressen mit der Suffixbasis ist deshalb
unzulässig und wird vom eigenen Bereichsleser zurückgewiesen. Die neue
Abbildung allein löst die fehlenden Sensorverweise nicht auf.

Neue private eigene Leser, Tests, Quell-/Bereichshashes und Kontrollen:
`build/mcu-init-followup-20261018/`. Keine Herstellerbytes im öffentlichen
Baum. Sechs synthetische Layouttests sowie 75 Namens-/Literalpaare,
45 bekannte folgende Transferformen und 24 Bereichsausschlüsse wurden
unabhängig geprüft. Die kompakten Feldmodelle bestehen 201 statische
Fundstellenkontrollen, elf Ablehnungsfälle und 192 synthetische
Packingkontrollen. Vier zusätzliche Eigenlesertests prüfen die Grenzen der
blattartigen Kandidaten. Synthetische Tests validieren die eigenen Leser,
keine ISA oder reale Ausführung. Die zentralen Feld-/Adresskontrollen
wurden mit anderer Arithmetik zusätzlich unabhängig wiederholt.

Die gezielte neue lokale Referenzprüfung der bereits vorhandenen Archive
und Werkzeugreferenzen liefert weiterhin keinen passenden MCU-Backend,
keine Opcodebeschreibung und keine SDK-/ELF-/Linkermap-Quelle. Das ist
eine begrenzte Inventur, keine globale Aussage über sämtliche Dateien.
Eine Bytekodierungsreferenz oder bekannter Compileroutput mit passenden
Symbolen würde besonders bei Speicher-/Vergleichsbefehlen helfen.
Weiter offen bleiben Sensorregister-Lese-/Schreibhelfer,
Argument-/Vergleichssemantik und die letzte wirksame Initialisierung.
**Kein aktiver CTRL2_G-Wert und kein physikalischer Gyrofaktor gewonnen.**

### Lokales REA und neuer Jieli-Referenzkandidat, 18. Oktober

Die spätere Freigabe erlaubt eine lokale Werkzeugumgebung auch für andere
Programme. Sie ändert weder den installierten Treiber noch die pausierte
Gyrokalibrierung. REA `6.5.0` ist auf den veröffentlichten Quellcommit
`3b79af28e80785afce9f5998d8f03289402a1847` festgelegt; npm-SRI und lokale
SHA256 wurden geprüft. Die Installation im Benutzerverzeichnis ignoriert
sämtliche npm-Lifecycle-Skripte und aktiviert keine MCP-Anbindung. Ghidra
`12.1.4` und ein separates Temurin-JDK `21.0.12.1+1` stammen aus geprüften
offiziellen Releasearchiven. Keine Systempakete oder Agentenkonfigurationen
werden dafür geändert. Die Werkzeuge behalten ihre eigenen Lizenzen;
Herstellerdateien und Werkzeugbinärdateien gehören nicht ins Repository.

**Wiederverwendbarer Starthelfer fertig:** `~/.local/bin/rea-local` bietet
`check`, `native DATEI`, `javascript DATEI_ODER_ORDNER`, `managed DATEI`,
`artifact DATEI` und `function DATEI 0xADRESSE`. Keine freien REA-Optionen,
Debugger oder Zielprogrammstarts. Jeder Lauf erhält ein neues privates
Verzeichnis unter `~/Documents/REA-Analysen`; nur eine nicht ausführbare
Kopie wird lesend eingebunden. Original- und Kopiehash werden vor/nach
dem Lauf verglichen. Vollständige Ergebnisse bleiben in `work/rea.stdout.json`
und `work/rea.stderr.log`, der äußere Status enthält keine Targetauszüge.
`completed=true` allein bestätigt Prozessabschluss und Dateiintegrität,
nicht die fachliche Richtigkeit eines Analyseergebnisses.

Fünf echte statische Prüfungen mit **eigenen synthetischen Dateien** bestehen:
Windows-PE-Übersicht mit Ghidra, ELF-Funktion samt korrekt rekonstruierter
Arithmetik `b + a * 3`, JavaScript-Exportanalyse, Artefaktklassifikation und
PE/CLI-Metadaten einschließlich eigener Assemblykennung. Kein Testprogramm
wurde ausgeführt. Der Managed-Pfad ist eine Metadatenprüfung, keine Zusage
vollständiger C#-Dekompilierung. Alle fünf Läufe bestätigten Isolation sowie
unveränderte Originale/Kopien. Die [eigenen Helfer und Tests](../tools/research/rea_local/launcher/rea_local.py)
sind getrennt vom Treiber; `make test-rea-local` startet nur synthetische
Metadaten-/Mocktests, niemals REA oder ein Analyseziel. Alle 39 Helfertests bestehen.

Bewusste Grenzen: maximal 4096 Dateien, 256 MiB pro Datei, 1 GiB pro Eingabe,
15 Minuten pro Lauf und 128 MiB je erzeugter Datei. Symlinks, Spezialdateien,
wechselnde Eingaben und `/proc`, `/sys`, `/dev`, `/run` als Analysequelle
werden abgewiesen. Host-Shellprofile, Steam und Dienste bleiben unverändert.
Dies ist ein lokal geprüftes Isolationsmodell auf dem vorhandenen Linux-
System, keine Garantie gegen sämtliche Parser- oder Kernel-Schwachstellen.

Die gerätefreie Bubblewrap-Prüfung besteht mit sieben getrennten Namespaces,
fünf leeren Capability-Sätzen, `NoNewPrivs=1`, privatem Home/Temp, lesenden
Werkzeugmounts und verweigertem Netzwerk. Eine anfänglich zu strenge
UID-Mapping-Erwartung stoppte vor REA: Bubblewrap `0.13.1` verwendet für
`--dev` zwei Benutzernamensräume. Die zweite Mapping-Spalte bezieht sich auf
den unmittelbaren Elternnamensraum, nicht Host-root. Der korrigierte Test
prüft die genaue belegte Zuordnung; Rechte werden nicht angehoben.
[Bubblewrap-Quellbeleg](https://github.com/containers/bubblewrap/blob/v0.13.1/bubblewrap.c#L3030-L3048).

**Die MCU-Lücke löst REA nicht automatisch:** Die festgelegte Version bietet
für rohe Dateien nur x86, x86_64, ARM, ARM64 und 6502 an. Die Datei darf
deshalb nicht mit einem geratenen ARM-Profil geöffnet werden. Ghidra kann
PE/ELF statisch bearbeiten; das ist kein Nachweis eines geeigneten Jieli-
Loaders. Zusätzliche Firmware-Containerwerkzeuge sind bislang nicht
installiert. Siehe [REA-Rohdateigrenzen](https://github.com/morluto/rea/blob/3b79af28e80785afce9f5998d8f03289402a1847/docs/raw-binary.md).

Eine neue Recherche in öffentlichen Primärquellen findet tatsächlich einen
passenden **Prüfkandidaten**, [Quarkslabs ghidra-jieli](https://github.com/quarkslab/ghidra-jieli).
Das offizielle [BR23-SDK-Makefile von Jieli](https://github.com/Jieli-Tech/fw-AC63_BT_SDK/blob/master/apps/hid/board/br23/Makefile)
verwendet `pi32v2`, `-mcpu=r3` und entsprechende Toolchainnamen. Das verbindet
BR23 mit einer echten Compilerarchitektur; es identifiziert noch nicht den
MCU oder ausgeführten Code unseres G7 Pro. Die Erweiterung wurde für die
private lokale Ghidra-Installation aus dem festgehaltenen Quellcommit
`e1bd0707874b77b759401555d24839ad43af1267` gebaut. Sie ist nicht Teil des
öffentlichen Projekts. Herstellerdateien wurden nicht ausgeführt oder
emuliert.

Zum Zeitpunkt der ersten Sichtung war die SLEIGH-Referenz unvollständig und
noch nicht an den Firmwareankern geprüft. Ihre [Immediate-Regeln im fixierten
Quellcommit](https://github.com/quarkslab/ghidra-jieli/blob/e1bd0707874b77b759401555d24839ad43af1267/data/languages/pi32v2_ins_loadimm.sinc)
beschreiben unter anderem die lange Literalform und `E040` als Nullerweiterung.
Dieser `E040`-Teil wird durch den unten beschriebenen unabhängigen
Jieli-SDK-Disassembly-Gegenbeleg widerlegt und darf nicht als bestätigte
Instruktionssemantik verwendet werden.
Die [relativen Transferregeln desselben Commits](https://github.com/quarkslab/ghidra-jieli/blob/e1bd0707874b77b759401555d24839ad43af1267/data/languages/pi32v2_ins_progflow.sinc)
verwenden `inst_next`; die nachfolgende Offline-Validierung prüft genau diese
Teilformen. Sie bestätigt weder eine vollständige ISA noch die getrennte
kurze signed6-Hypothese.

### Offline-Validierung des Pi32v2-Decoders, 18. Oktober

Der Apache-2.0-lizenzierte Quarkslab-SLEIGH-Beschreiber wurde aus dem
festgehaltenen [Quellcommit](https://github.com/quarkslab/ghidra-jieli/tree/e1bd0707874b77b759401555d24839ad43af1267)
mit Ghidra 12.1.4 kompiliert und
statisch auf drei lokal vorhandene Controller-App-Versionen angewandt. Die
Kompilierung war erfolgreich, meldete aber zwei Delay-Slot-Warnungen,
50 als NOP markierte Konstruktoren und eine vereinfachte Erweiterungs-/
Trunkierungsoperation. Der Beschreiber ist damit brauchbar für die geprüften
Konstrukte, jedoch kein vollständiger oder unabhängig bestätigter Decoder.

Die bekannten Literal-/Stringanker bestanden die gezielten Kontrollen:
je 50 verschiedene Stellen pro App wurden als 6-Byte-`mov` mit 32-Bit-
Immediate dekodiert; jedes Immediate stimmt mit der separat gefundenen
Stringadresse überein. Das validiert diese konkrete Literalform, nicht die
Vollständigkeit aller Adressierungsarten.

Die 50 relativen Transferstellen pro App wurden als 4-Byte-`call` oder
`goto` dekodiert. Für diese Formen ergibt die im SLEIGH definierte Basis
`inst_next + 2 * displacement` in allen drei Apps dieselbe gemeinsame
Logging-Funktion. Das frühere empirische Modell ohne `inst_next` zielte
jeweils vier Bytes vor deren Prolog auf deren vorhergehendes Rückkehrende.
Die PC-Basis ist für diese konkreten 22-Bit-Transfers damit durch die
gemeinsamen Literal-/Kontrollflussanker gestützt; sie ist keine allgemeine
Bestätigung aller Pi32v2-Sprungformen.

#### Korrektur: `E040`-Vorzeichenerweiterung und gemeinsamer Maskenhelfer

Die damalige Schlussfolgerung, `E040` sei ein Null-erweiterndes `movz`, war
falsch. Die SLEIGH-Quellregel ist zwar so formuliert, wird aber von der
unabhängigen offiziellen [Jieli-Tech-`fw-AC63_BT_SDK`-Referenz](https://github.com/Jieli-Tech/fw-AC63_BT_SDK/blob/fdc018de81629e21e594d677cf05f87d288be0f0/cpu/br23/tools/rom.lst)
für `ELF32-pi32v2` nicht gestützt. Eine begrenzte Prüfung der fixierten
`cpu/br23/tools/rom.lst`-Datei (SHA256
`650bd301951a311207aad7000fa27bdfa8fce0ae8101576eaaf302072982f1d2`)
erfasste 3.422 Listingzeilen: 44/44 `E040`-Immediatewerte und Register
stimmen mit Vorzeichenerweiterung überein; nur 30/44 stimmen mit
Nullerweiterung überein, weil 14 Werte negativ sind. Unabhängige
Kontrollgruppen passten ebenfalls: 289/289 geprüfte 22-Bit-Transfers zur
`PC+4`-Basis, 346/346 U8-Immediates und 11/11 negative 5-Bit-Immediates.
Das belegt die gelisteten SDK-Encodings, nicht automatisch die genaue
MCU-Variante oder jede Instruktion im Controller.

Ein privater, isoliert gebauter SLEIGH-Folgevariant änderte ausschließlich
`E040` auf Vorzeichenerweiterung und ließ eine nicht implementierte
`rep nwords`-Familie bewusst unaufgelöst. Die drei App-Binärdateien blieben
hashgleich und wurden nicht ausgeführt. In jeder App führen 16 geprüfte
Maskeneinträge (zehn `E040`-Formen plus sechs 32-Bit-Literalformen) per
relativem Kurzsprung in denselben versionsinternen Codeblock. Ein gezielter
P-Code-Durchlauf dekodierte 48 Eintragsfenster und 72 Instruktionen des
gemeinsamen Blocks ohne Fehler. Der Block lädt einen Wert an einer aus
`0x2010 + r0` berechneten Adresse, AND-verknüpft ihn mit dem Maskenregister
`r4` und speichert das Ergebnis zurück. Zusammen mit den abgestuften
Komplementmasken stützt das einen allgemeinen maskierten Feld-Update-Helfer;
eine globale Funktionsgrenze oder die Bedeutung des bearbeiteten Objekts ist
damit nicht bewiesen. Insbesondere ist kein Bezug zu IMU, Sensorbus oder
`CTRL2_G` hergestellt.

Damit ist die frühere Interpretation der `E040`-Maske durch die
Decoder- und Quelllistenprüfung ersetzt. Der Beschreiber bleibt partiell;
fehlende Instruktionsfamilien und globale Code-/Datengrenzen dürfen nicht
übergangen werden.

Der kurze kompakte Block dekodiert an den geprüften Stellen als wechselnde
kurze `add`-/`mov`- und `rts`-Instruktionen. Ein Scan fand in den drei
Versionen keine von den geprüften relativen Transfers direkt angesprungenen
Ziele in diesem Block und keine Treffer für die angenommene Laufzeitadresse;
einige Treffer auf nackte Dateioffsets bleiben mehrdeutig. Daher ist weder
eine Funktionsgrenze noch eine ausführbare Rückgabewerttabelle bewiesen.
Indirekte Referenzen und Code-/Datengrenzen bleiben offen.

### Sensorpfad nach Decoderabgleich

Die Zeichenkette `Enter Sensor Cal Mode!` besitzt einen bekannten direkten
Literalverweis in allen drei Apps: `0x10718` in DV209 und `0x10720` in
DV515/DV608. Der korrigierte Decoder zeigt jeweils das Laden der Zeichenkette,
gefolgt vom relativen Transfer zum zuvor bekannten Textlogger (`0x44d38` bzw.
`0x44e18`). Das belegt den Formatstring-/Logpfad, aber weder einen
Sensorregisterzugriff noch eine Initialisierung. Für die übrigen sieben
priorisierten Sensor- und Kalibrierungszeichenketten fanden die gezielten
Scans keine exakten Flash-/Dateioffset-Zeiger, keine geprüften E000/E010-
Splitpaare und keine begrenzten Innenstring-Zeiger. Das schließt indirekte
Tabellen, weitere Adressierungsformen oder nicht erkannte Referenzen nicht
aus.

Die Sensoranker bleiben außerhalb des bestätigten Load-/Run-Suffixbereichs;
die dortige Adressumrechnung wird nicht auf sie übertragen. In diesem
damaligen Suchpass war trotz validierter Teilregeln noch keine belastbare
WHO_AM_I-Lesekette oder Schreibvorbereitung für Register `0x11` nachgewiesen.
Ein numerischer Treffer für `0x11` wäre weiterhin kein `CTRL2_G`-Schreibbeleg.
Dieser frühere Suchpass fand noch keinen Initialisierungskandidaten; der
[anschließende Basis-plus-Versatz-Pass](JIELI_SENSOR_INITIALIZATION.md) löst
diese Suchlücke teilweise. Aktive Gerätekonfiguration und USB-Gyrofaktor
bleiben offen. Keine Firmwareausführung, Emulation oder Hardwareaktion.

**Kontrollflusskorrektur:** Der Kalibrierungslog endet mit einem unbedingten
Sprung zum Logger. Der linear dahinter dekodierte Ausschnitt mit einem
16-Bit-Nullwort-Store ist keine nachgewiesene Fortsetzung dieses Pfads.
Seine P-Code-Registerraum-Offsets `0x4` und `0x8` bezeichnen `r1` und `r2`,
nicht die zuvor genannten `r4` und `r8`. Objektbedeutung und genauer
Adressausdruck bleiben ungeprüft; daraus folgt kein Sensorwrite.

**Korrektur der ADC-/EEPROM-Zuordnung:** Der frühere Bericht identifizierte
den Code bei `0x10730` (DV209) beziehungsweise `0x10738` (DV515/DV608)
fälschlich als `adc scan not over`. Der dort dekodierte Literalzeiger zeigt
tatsächlich auf `eeprom read over:`. Der gleichartige zweite Block bei
`0x10760`/`0x10768` zeigt auf `eeprom write over`. In beiden EEPROM-Blöcken
prüft der begrenzte P-Code ein Statusbyte mit Ausdruck `0xf140 + 0x534` und
lädt anschließend einen möglichen indirekten Aufruf über
`((0xf140 + 0x298) << 2)`; wenn der geladene Wert ungleich null ist, folgt
`CALLIND`. Pro App tritt die geprüfte unmittelbare `0x298`-Form nur an diesen
beiden Stellen auf. Tabelleninhalt, Speicherabbildung, ABI und Zielcode sind
nicht aufgelöst. Die Call-Sites liegen bei `0x1075a`/`0x1078a` (DV209) und
`0x10762`/`0x10792` (DV515/DV608). Diese EEPROM-Blöcke werden nicht als
Sensor- oder ADC-Pfad gewertet.

Der tatsächliche Text `adc scan not over!!` liegt separat in den Appdaten
(DV209 `0x23108`, DV515 `0x231e0`, DV608 `0x231de`). Ein eigener direkter
Literalzeiger steht in allen drei Varianten bei Codeoffset `0x7426`; der
folgende relative Transfer führt zum gemeinsamen Textlogger (`0x44d38` in
DV209, `0x44e18` in DV515/DV608). Auch hier endet der Logpfad mit einem
unbedingten Sprung. Linear folgende Stores und Schleifen gehören ohne
weiteren Kontrollflussbeleg nicht zu seiner Fortsetzung. Rückgabewerte,
Call-Clobbers, Registerprovenienz und ABI bleiben unbestimmt. Im dekodierten
Fenster steht kein `CALLIND`; kein IMU-Bezug dieses ADC-Logs ist nachgewiesen.
Der isolierte statische Decode lief über 40 Datensätze je
Appversion ohne Decodefehler; alle drei Eingabedateien blieben hashgleich.

Eine byte-ausgerichtete Suche über alle drei vollständigen Appdateien fand
keine Kandidaten für eingehende Sprünge in den geprüften relativen 22-Bit-
und kompakten GOTO-Formen auf den Kalibrierungs- oder EEPROM-Lese-Logblock.
Für den echten ADC-Text wurde stattdessen der direkte Literalzeiger bei
`0x7426` gefunden und separat dekodiert. Die geprüften exakten Zeigerformen
auf die genannten Codeanker ergaben keinen Treffer. Das schließt andere
Instruktionsformen, indirekte Tabellen und unbekannte Code-/Datenabbildungen
nicht aus. Ergebnisse für die drei gehashten Binärbilder, Scanner und
Regressionstest bleiben ausschließlich unter `build/` und sind kein Teil des
öffentlichen Quellstands.

### Querverweiskarte: Sensorlogs, Maskenblock und IMU-Bericht

Die Befunde aus `app.bin`, dem G7-Pro-Capture und dem separat analysierten
Nexus-Prozess bilden noch keine durchgehende Datenflusskette:

| Ausgangspunkt | Nachgewiesene Kante | Offene Verbindung |
|---|---|---|
| `Enter Sensor Cal Mode!` | Literal laden → unbedingter Sprung zum Textlogger | Lineare Nachbar-Stores sind keine belegte Fortsetzung; kein Sensorbus-Schreibzugriff |
| `adc scan not over!!` | Literalzeiger bei `0x7426` → unbedingter Sprung zum Textlogger | Kein belegter IMU-Bezug; Nachbarcode separat betrachten |
| `eeprom read/write over` | Zwei EEPROM-Logblöcke → Statusbyte und bedingter `CALLIND` über Ausdruck `((0xf140 + 0x298) << 2)` | Callback-Tabelleninhalt/-ursprung und Zielcode ungelöst; kein belegter Sensorbezug |
| Weitere Sensor-/Kalibrierungstexte | Keine direkten Zeiger in den damaligen Literal-/Splitformen; neuer Basis-plus-Versatz-Pass findet Sensoranker | [Initialisierungskandidat und offene USB-Verbindung](JIELI_SENSOR_INITIALIZATION.md) |
| 16 Maskeneinträge pro App | Je Eintrag kurzer Sprung zum lokalen AND-/Write-Block | Kein eingehender Treffer in der Datei für die geprüften kurzen und 22-Bit-Sprungformen; indirekte Erreichbarkeit ungeklärt |
| Sprint-002 IMU-Capture | 64 Byte IN `0x82`; Gyro bei 17/19/21, Beschleunigung bei 23/25/27 | Kein Firmwarecodeort des Berichtsproduzenten identifiziert |
| Nexus-E0-Sensorpfade | Zwei E0-Parser lesen 60 Byte; die sechs `KeyState`-Sensorfelder bleiben ungesetzt | Bei hypothetischem Abzug von vier Headerbytes werden die Capture-Sensorfenster nicht gelesen |
| Nexus-F1-Firmwarebrücke | 60 Byte werden ab Offset 4 in einen 64-Byte-Puffer kopiert und an `JL_handleGipData` übergeben | Kein Beleg, dass dies der Produzent des aufgenommenen IMU-Berichts ist |

Die Capture-Offsets stammen aus [PROTOCOL.md](PROTOCOL.md). Die E0-/F1-
Parserbefunde und Sensorfeld-Datenflüsse sind detailliert in
[NEXUS_SENSOR_DATAFLOW.md](NEXUS_SENSOR_DATAFLOW.md) belegt. Der Abzug von
vier Headerbytes ist eine Vergleichshypothese, keine nachgewiesene
Transportnormalisierung.

Ein zusätzliches byte-ausgerichtetes Suchfenster prüfte die eingehenden Ziele
der validierten kompakten GOTO- und relativen 22-Bit-Transferformen sowohl für
alle 48 Maskeneinträge als auch für den Kalibrierungs- und EEPROM-Lese-
Logblock. Es fand dort in den geprüften Formen keine direkten
Sprungkandidaten. Der ADC-Textanker wurde danach korrekt auf `0x7426`
zurückverfolgt; der dortige begrenzte Ausschnitt enthält einen Textlogger,
Speicher-/Schleifenausdrücke und einen direkten Hilfsaufruf, aber keinen
nachgewiesenen Sensorbezug. Der `CALLIND` gehört zu den separat liegenden
EEPROM-Lese-/Schreibblöcken, nicht zum ADC-Textanker. Unvollständige
ISA-/Code-Datensegmentierung bedeutet, dass fehlende Treffer keine
Unerreichbarkeit beweisen. Der neue Sensorpfad hat jetzt Vorrang vor dem
ungeklärten EEPROM-Callback: Transportabschluss, letzte Registerkonfiguration
und Sensorpuffer → Verarbeitung → USB-Report verfolgen. Der dokumentierte
Initialisierungswert ist noch keine bestätigte Skala der USB-Rohwerte.

Der private lokale REA-/Ghidra-Aufbau enthält den Pi32v2-Beschreiber nun
wiederverwendbar für weitere statische Analysen. Die Herstellersoftware und
ihre Firmware bleiben lokale Eingaben; Rohdaten, Projektdumps und komplette
Disassembly-Ausgaben werden nicht ins öffentliche Repository übernommen.
Die Gyrokalibrierung bleibt pausiert.

### Exakte Sensorvariante erneut offen: gezielter WHO_AM_I-Abgleich

[tester] hält eine Verwechslung der exakten Variante bei DigiKey für möglich
und berichtet von gleichem Gehäuseaussehen. Die ursprüngliche Fotoauskunft
LSM6DSO/LSM6DSOTR bleibt dokumentiert; sie wird weder als widerlegt noch als
endgültiger Modellnachweis behandelt. Das Foto selbst und die Vendorantwort
wurden hier weiterhin nicht unabhängig geprüft. Ebenso wenig identifiziert
der Firmwaretext `LSM6DS3TR` automatisch einen LSM6DS3TR-C auf diesem Exemplar.

Der vorhandene Linux-ST-Treiber bestätigt den vorgeschlagenen Unterschied
bereits lokal, ohne Netz oder Gerät:

| Linux-Modelleintrag | WHO_AM_I-Register | Erwarteter Wert |
|---|---|---|
| LSM6DS3TR-C | `0x0f` | `0x6a` |
| LSM6DSO | `0x0f` | `0x6c` |
| LSM6DS3, zur Namensabgrenzung | `0x0f` | `0x69` |

ELF-Quelle und Hash sind im Sensorstatus dokumentiert. Der TR-C-Eintrag
liegt bei Dateioffset `0x76e0`, DSO bei `0x7b90`. Die Gyro- und Accel-
Gewinntabellen beider Einträge stimmen überein. Ungefähr 8192 Zähler/g
trennt diese beiden Kandidaten daher nicht. `0x6c` ist zudem kein weltweit
eindeutiger Typwert: Der lokale DSOX-Eintrag verwendet ihn ebenfalls.

Die Nachsuche in den drei Controller-Apps prüfte die bisher verstandenen
langen Literalformen gezielt für `0x0f`, `0x69`, `0x6a` und `0x6c`.
Die wenigen `0x0f`-Kandidaten besitzen keinen belegten Sensorzugriffskontext;
die ID-Werte kommen in diesen geprüften Formen nicht vor. Unverstandene
kompakte Konstanten und Vergleichs-/Speicherbefehle verhindern derzeit die
vollständige Zuordnung. Das ist **kein Nachweis fehlender WHO_AM_I-Prüfung**.

Zu belegen bleibt die konkrete Kette: Register lesen → ID vergleichen →
Sensorpfad auswählen → letzte wirksame CTRL2_G-Konfiguration schreiben →
Registerwerte zum USB-Bericht weiterreichen. Weder Unterstützung beider
ST-Varianten noch der aktive Pfad oder ein realer Chip-ID-Wert wurden
nachgewiesen. Kein Register ausgelesen und kein Kalibrierungswert geändert.

## 5. Bewegungssensoren, Kalibrierung und Profile

Die Haupt-DLL besitzt native Metadatennamen für `GyroX/Y/Z` und `AccelX/Y/Z`
(Getter ab `0x994163`, sechs einzelne Fundstellen im Quellmanifest),
`SensorModule`, `MotionMapModule`, `AdvanceMotionMapParser` und `MotionParser`.
Die [native Fortsetzung](NEXUS_SENSOR_DATAFLOW.md) belegt inzwischen Int32-Typen,
Feldoffsets und Zugriffscode; die Namen allein belegen weder Rohdatenproduzent,
USB-Offsets noch physikalische Einheiten.

Das G7-Pro-Motion-Modul `f8d2` der Weboberfläche (UTF8-Bytes
`1913238…1935646`) enthält Aim/Tilt, Yaw/Roll/Combine, Umkehrungen sowie
`axisRatio`, `cross`, `mouseDpi` und Stickempfindlichkeit. Es reicht Änderungen
über `setProfileByProperty("Motion", …)` in das Profil weiter; die Bridge
plant danach ein Speichern. Diese Optionen konfigurieren die Bewegungsabbildung
auf Spiel-/Mauseingaben. Sie belegen weder die Orientierung der Rohachsen noch
eine Sensitivität in LSB/(°/s). Profileigenschaften sind auch keine sichere
Methode zum ausschließlich lesenden Abruf von Kalibrierungsdaten.

Der Kalibrierungsdialog `c5ee` (Bytes `1562905…1575574`) besitzt `motionCal`.
Er verlangt flaches Ablegen und übergibt `calPart="motion"`; Start, Abschluss
und Abbruch benutzen `calType` 0, 1 und 2 über `deviceReq("calibrate", …)`.
**Das sind WebView-/Anwendungsparameter, keine USB-Opcodes.** Der Backendpfad
ist inzwischen bis `D4X.SendMessage` verfolgt; physisches USB-Framing und
tatsächliche Firmwarewirkungen sind weiterhin nicht vollständig dekodiert.
Ein UTF16-Formatliteral für Kalibrierstatus nennt LS/RS/LT/RT/Sensor, aber
keine numerischen Bias-/Gainwerte; es wurde keine reale Antwort erfasst.
Native Namen wie `WriteProfileToEEPRom` bestätigen zusätzlich, dass
Konfigurationspfade schreibend sein können; sie gehören nicht in passive Tests.

**In Nexus nicht nachgewiesen:** Gyro-LSB/(°/s), bestätigtes Accel-LSB/g, Sensorauflösung
oder Messbereich, Achsenvorzeichen, Bias, Gerätezeitbasis, auslesbarer
Kalibrierungsblock, IMU-Chip und ein vollständiger IMU-Aktivierungsbefehl.
Alle 18 lesbaren `8192`-Treffer der Haupt-DLL gehören zu Kryptografienamen;
keiner bestätigt unseren Kalibrierungskandidaten. Negative Zeichenkettensuchen
schließen unbenannte Konstanten oder Umrechnungen im AOT-Maschinencode nicht aus.

## 6. Abgleich mit Deadband, Capture und gs_native

Maßgeblich bleiben die [capturebelegten Formate](PROTOCOL.md), die fixierten
Deadband-Quellen und [IMU-Statistik](IMU-STATISTIK-UND-SENSORIDENTIFIKATION.rst).
Der Sprint-002-Originalcapture hat SHA256
`4045577a7a9e7a1a0f84307a45e96fd524cd7dea1d4af276ebd7db20a0994a89`.
Die Auswertung seiner **12204** gespeicherten IMU-Pakete wurde übernommen;
dieser Auftrag erzeugt keine neue Messung und keinen neuen Hardwarebeleg.

| Gegenstand | Vorhandener Nachweis | Beitrag von Nexus / verbleibende Lücke |
|---|---|---|
| Normale Eingaben | XInput 20 Byte, GIP 36 Byte; reale native Tests | Keine neue Dekodierung nötig; kein Updatepfad in den normalen Start übernehmen |
| IMU | 64 Byte IN `0x82`, Gyro signed-LE16 ab 17/19/21, Accel ab 23/25/27 | Sechs native Namen passen thematisch; die Zuordnung zu genau diesem Bericht ist in Nexus noch nicht rückverfolgt |
| Zusatztasten | Bytes 57/58, vier eigene Codes 704–707 | Profil-/Motion-Forschung darf die unabhängigen Tasten nicht ersetzen |
| Viermotorbetrieb | 13-Byte-OUT `0x09`, unabhängige Griffe/Trigger, reale Wirkung | SDK-Updatefragmente `0x4a/0x4c` sind ein anderer Pfad, nicht Motor- oder IMU-Laufzeit |
| Beschleunigung | Experimentelle, austauschbare 8192 LSB/g | Betragsmedian heuristisch ausgewählter Ruhefenster 8215,8385, rund +0,291 %; Nexus bestätigt den Faktor nicht |
| Gyroskop | Eigener Faktor, Bias und physische Achsen offen | Keine verwendbare neue Konstante oder ausgelesene Kalibrierung |
| Zeitbasis | IMU-Hostrate rund 62,527 Hz, Median 16 ms | Kein Nachweis einer Sensoruhr oder von 1000-Hz-IMU durch Nexus |

Deadbands `/32768`-Anzeige ist eine Balkennormierung, kein Gyrofaktor.
Auch Nexus-Empfindlichkeitsregler sind keine physikalische Kalibrierung.
Ruhende Daten in einer Lage bestimmen weder sechs Achsen noch eine bekannte
Drehgeschwindigkeit. Bestehende experimentelle Accel-Ausgabe bleibt deshalb
markiert; kalibrierte SDL-Sensorausgabe bleibt bis zu eigenen Faktoren gesperrt.

Für eine spätere Kalibrierung fehlen weiterhin kontrollierte ±g-Lagen aller
drei Achsen, Ruhefenster für Bias und Drift, markierte positive/negative
Drehungen um alle Achsen mit bekanntem Winkel und Zeit oder bekannter Rate,
Wiederholungen und gegebenenfalls Temperatur-/Filterabhängigkeit. Zuerst
Bewegungsrichtungen und Einheiten belegen, dann den vorhandenen
Kalibrierungskern nutzen. Ein identifizierter Chip wäre hilfreich, ist aber
keine Voraussetzung für eine belastbare Referenzmessung.
Die [DualSense-/SDL-Empfehlung](DUALSENSE_SENSOR_COMPARISON.md) bleibt:
IIO-Rohdaten erhalten und später kalibriertes evdev-Sensorgerät ergänzen.

## 7. Bewertung für Linux und nächster Forschungsumfang

| Funktion | Einschätzung | Vor einer Umsetzung erforderlich |
|---|---|---|
| Laufzeit ohne Windows | Bereits im begrenzten Testumfang real vorhanden | Stabilen nativen Betrieb und Release-Abnahme erhalten |
| Firmware-/Hardwareversion anzeigen | Plausibel implementierbar | Nativen Abfrage-/Antwortpfad bytegenau zuordnen; Seiteneffekte ausschließen; zunächst gespeicherte Daten testen |
| Profile/Motion/Kalibrierung | Hersteller-API vorhanden, Linux-Protokoll nur teilweise bekannt | Bridge zu Serializer und Antwortparser verfolgen; flüchtige Einstellungen, EEPROM-Schreiben und Kalibrierung unterscheiden |
| Kalibrierte SDL-IMU | Weiterhin erreichbar, durch Nexus nicht freigabereif | Unabhängiger Gyrofaktor, Accel-/Achsen-/Biasnachweis und Zuordnung zum Gamepad |
| Offline-Firmwareprüfung | Äußere Container, innere Appstruktur und app.bin/cfg_tool.bin samt CRC belegt | MCU-Instruktionen, aktiver Sensorpfad, übriger DV-Inhalt, globale Bank-/Modellzuordnung und Authentizität offen |
| Firmware flashen | **Kein Go** | Vollständiger Bootloader-/Update-/Rückweg, Antwortkorrelation, Integrität/Authentizität, Versions-/Paketpaarung und gezielte neue Freigabe |

Eine spätere Windows-unabhängige Updateanwendung soll getrennt vom normalen
Kernelbetrieb bleiben, ihre exklusive Geräteübergabe mit dem Manager abstimmen
und keine proprietäre Firmware mitliefern. Kein Updater im Autostart, keine
automatischen Downloads oder Firmwareupdates. Ein Hersteller-Downloadlink
oder erkannter CRC ist keine ausreichende Sicherheitsprüfung.

Vertiefung zunächst rein statisch: Verbraucher der nativen Gerätemodell-/
DFU-Objekte und vollständiger Live-Versionsvergleich, danach Produzenten der sechs Sensorfelder und der
Kalibrierungsantworten gezielt rückverfolgen. Umfang und Methode vor weiterer
tieferer AOT-/Firmwareformatanalyse erläutern. App-Ausführung, Netzwerk oder
Hardware benötigen jeweils eine separate Freigabe. Diese Analyse liefert
keinen Anlass für einen neuen Bootstrap-, Treiber- oder Firmwareeingriff.
Prioritäten und Abnahmekriterien stehen in der [Roadmap](ROADMAP.md).

## 8. Prüfung und Abschluss dieses Arbeitsgangs

Quellhashes, Bundle-/ZIP-Übereinstimmung, PE-Metadaten und wesentliche
Bytefundstellen wurden gegengeprüft. Die 1446 MSIX-Inhaltsblöcke stimmen;
Dateinamen mit Leerzeichen wurden anhand ihrer beobachteten `%20`-ZIP-Namen
zugeordnet. Die Vertrauenskette wurde nicht geprüft. Private Originale und
Auswertungen bleiben außerhalb von Git, eigene Dokumentation wird lokal
versioniert. Keine Änderung an Kernel, Manager, Kalibrierung, Paketierung oder
laufender Alpha; kein Build-/Installationstest und kein Push aus diesem Auftrag.
