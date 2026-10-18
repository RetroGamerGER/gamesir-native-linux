# Jieli: Sensorinitialisierung und CTRL2_G-Kandidat

Stand: 18. Oktober 2026. Ausschließlich statische Offline-Analyse vorhandener
Dateien. Keine Firmwareausführung oder Emulation, Netzwerkverbindung,
Geräteöffnung, Installation oder Änderung des Treibers. Gyrokalibrierung
und produktive SDL-Sensorfreigabe bleiben pausiert.

## Ergebnis und Beweisgrenze

In drei getrennten App-Versionen ist jetzt eine zusammenhängende
ST-Sensorinitialisierung erkennbar: Ein Transfer mit Registerargument `0x0f`
wird von einem Vergleich mit `0x6a` gefolgt. Im anschließenden Pfad werden
ein Datenbyte `0x6c` für Registerargument `0x11` und ein Datenbyte `0x68`
für Registerargument `0x10` an denselben Schreibhelfer übergeben.

Das ist deutlich stärker als ein passender String oder ein einzelner
Zahlenfund. **Statisch belegt sind die Argumentvorbereitung und die Aufrufe.**
Die Deutung als ST-WHO_AM_I/CTRL2_G/CTRL1_XL-Pfad ist durch Sensorlogs,
Lese-/Schreibhelfer und passende Registerwerte stark gestützt. Der vollständige
Busabschluss, die Auswahl auf einem konkreten Controller und der letzte
wirksame Registerwert im späteren Spielbetrieb sind damit nicht bewiesen.

Unter der LSM6DS3TR-C-Annahme bedeutet `0x6c & 0x0c == 0x0c` den
±2000-Grad/s-Bereich mit **0,07 Grad/s je Sensorzählwert**, entsprechend etwa
14,285714 LSB/(Grad/s) beziehungsweise 0,00122173048 rad/s je Zählwert.
`0x68 & 0x0c == 0x08` passt zu ±4 g. Grundlage ist die bereits lokal
ausgewertete Linux-ST-Referenz und das vorhandene
[experimentelle Profil](EXPERIMENTAL_GYRO_TEST.md#werkzeug-und-quellenstatus).
Die ODR-Bits werden hier nicht als gemessene Abtastrate gewertet.

**Kein bestätigter GameSir-USB-Skalierungsfaktor:** Es fehlen weiterhin der
vollständige Weg von Sensorregistern zum USB-Report, mögliche spätere
Umschaltungen und der Bezug zur tatsächlich installierten Firmware.
Kein Diagnoseprofil wird automatisch ausgewählt; IIO bleibt unverändert.
`0x6a` ist hier der ID-Vergleich, `0x6c` der Konfigurationswert. Letzteres
ist in diesem Kontext ausdrücklich keine WHO_AM_I-Antwort eines LSM6DSO.
Auch `0x6a` allein identifiziert nicht ausschließlich LSM6DS3TR-C; die lokale
Linux-Tabelle enthält weitere ST-Varianten mit derselben Kennung.

## Warum die bisherigen Zeigersuchen den Pfad verfehlten

Zahlreiche Texte werden über eine gemeinsame Basis plus Versatz adressiert.
In DV209 tritt `0x1e24f50` als Basis auf; DV515/DV608 verwenden an den
entsprechenden Stellen `0x1e25030`. Die direkten Additionen für
`lsm6ds3 err!` und `qmi8658 err!` verwenden `r10` und die Versätze
`0x799` beziehungsweise `0x7a7`. Ihre Ergebnisse passen zu den vorhandenen
Textadressen unter der bisherigen Flashadresshypothese `0x1e000c0`.
Ein weiterer Pool liegt jeweils `0x4000` höher.

Zusätzlich gibt es Kombinationen aus kurzem Immediate-Laden und
Registeraddition. Im Bereich DV209 `0xaf7c`–`0xaf86` passen die
Adressausdrücke zu den QMI8658-/LSM6DS3TR-Erkennungsmeldungen. Die dortige
bedingte Auswahl und die Registerlebensdauer über frühere Funktionsaufrufe
sind nicht vollständig verifiziert. Die Textadressrechnung allein wird
deshalb nicht als vollständiger Kontrollflussnachweis behandelt.

Die alten negativen Literal-/Splitpaar-Suchen bleiben für ihre damaligen
Suchformen korrekt. Sie waren keine Aussage über diese weiteren Formen.

## Nachvollziehbare Codeanker

Alle Angaben sind **Dateioffsets innerhalb der jeweiligen `app.bin`**, keine
Linux-Adressen oder direkt verwendbaren Gerätebefehle.

| Beobachtung | DV209 | DV515 / DV608 |
| --- | --- | --- |
| Aufruf mit `r0=0xd6`, `r1=0x0f`, Puffer, `r3=1` | `0xac58` → `0x103da` | `0xac5a` → `0x103e2` |
| Vergleich des geladenen Ergebnisses mit `0x6a` | `0xac6e` | `0xac70` |
| Datenbyte `0x6c` vorbereiten | `0xad30` | `0xad32` |
| Aufruf mit `r0=0xd6`, `r1=0x11`, Datenpuffer, `r3=1` | `0xad3c` → `0x1036a` | `0xad3e` → `0x10372` |
| Datenbyte `0x68` vorbereiten | `0xad56` | `0xad58` |
| Aufruf mit `r0=0xd6`, `r1=0x10`, Datenpuffer, `r3=1` | `0xad62` → `0x1036a` | `0xad64` → `0x10372` |
| LSM-/QMI-Fehlerlogadressbildung | `0xad84` / `0xaf62` | `0xad86` / `0xaf64` |

Das Byte wird vor jedem der beiden entscheidenden Aufrufe in den von `r5`
bezeichneten Puffer geschrieben; `r2` übernimmt dessen Adresse. Die
parallel kodierte Registerkopie und ihr nachfolgendes Byte-Store-Mitglied
sind gemeinsam zu betrachten. Ein linearer P-Code-Ausdruck kann dieses
Mitglied zusätzlich anzeigen; daraus entstehen nicht zwei reale Transfers.

Der Lesehelfer sichert Puffer und Registerargument getrennt, bildet für
eine spätere Busphase `Geräteargument + 1` und hinterlegt Länge und Status.
Der Schreibhelfer hinterlegt Puffer, Registerargument und Länge; das
Geräteargument erreicht den MMIO-Ausdruck `0x1e2404`. Beide nutzen denselben
Kontrollblock bei `0x1e2400`. Das ist konsistent mit einem asynchronen
I²C-Transport einschließlich getrenntem Lese-/Schreibbit. Die komplette
Interruptzustandsmaschine und die genaue MMIO-Zuordnung bleiben zu prüfen;
aus dem Helferaufruf allein folgt kein erfolgreicher Sensorwrite.

Der begrenzte Scan nach der bereits geprüften direkten 22-Bit-CALL-Form
findet je Image 14 Kandidaten zum Schreibhelfer, alle im untersuchten
Initialisierungsbereich. Das schließt indirekte Aufrufe, andere Transferformen
oder andere Konfigurationswege nicht aus und beweist keinen letzten Write.
Die alternative QMI8658-Folge verwendet das Geräteargument `0xd4`; ihre
Registerwerte werden nicht mit dem ST-Datenblatt interpretiert.

## Verbindung zum Messdatenpfad

Ein zusätzlicher DV209-Ausschnitt zeigt bei `0x10a10`–`0x10a16` einen
Aufruf desselben Lesehelfers mit `0xd6`, Startregister `0x22` und Länge
12. Ein anderer Zweig liest über `0xd4` ab Register `0x35` ebenfalls
12 Byte. Im nachfolgenden getrennten Verarbeitungsblock werden Bytepaare
zu sechs 16-Bit-Feldern zusammengesetzt. Das ist ein konkreter Ansatzpunkt
für die weitere Sensor-/Reportanalyse, noch kein Beleg für unveränderte
Weitergabe an den bekannten 64-Byte-USB-Report.

Bei `0x10ad4` folgt ein indirekter Tabellensprung. Die Tabelle und ihre
vier Ziele wurden im [anschließenden Datenflusspass](JIELI_SENSOR_REPORT_DATAFLOW.md)
rekonstruiert; die unmittelbar folgenden Tabellenbytes sind kein Code.
Dieser Folgepass belegt bedingten Offset-Abzug und stützt die ST-Reihenfolge
`Gy,Gz,Gx,Ay,Az,Ax` bis zur vorbereiteten Reportkopie, ohne zusätzlichen
Gyro-Gain in diesem ST-Ausgabeabschnitt. Der
[Transportfolgepass](JIELI_USB_TRANSPORT.md) ordnet die Kopie dem
SDK-ROM-Stub `memcpy`/`memmove` zu und trennt Controller-IN `0x84` von
Dongle-IN `0x82`. Funk-/Sensorverknüpfung und indizierte Halfword-Semantik
bleiben begrenzende offene Stellen. Andere Ausgabezweige verändern Maßstab und Vorzeichen.
Die frühere Annahme, Nexus selbst müsse den Skalierungsfaktor enthalten,
ist für diesen Firmwarepfad nicht erforderlich.

## Decoderkorrekturen und unabhängige Kontrollen

Der zuvor dokumentierte direkte Kalibrierungslog und der ADC-Loganker enden
mit einem unbedingten Sprung zum Logger. Die linear danach dekodierten
Stores sind **keine nachgewiesene Fortsetzung** dieser Logpfade. Die frühere
Formulierung „danach Nullwort-Store“ wird zurückgenommen. Ebenso waren
`register 0x4` und `register 0x8` in P-Code Registerraum-Offsets: Sie
bezeichnen `r1` und `r2`, nicht `r4` und `r8`.

Unvollständig geprüfte Speicheradressausdrücke und Call-Clobbers bleiben
unbestimmt. Die neuen Argumentbelege verwenden die unabhängig kontrollierten
Teilformen; sie behaupten keine vollständige Korrektheit des Decoders.
Die [offizielle, bereits lokal gespeicherte Jieli-ROM-Liste](https://github.com/Jieli-Tech/fw-AC63_BT_SDK/blob/fdc018de81629e21e594d677cf05f87d288be0f0/cpu/br23/tools/rom.lst)
stimmt mit den eigenen Feldprüfungen an 346 kompakten Immediate-Ladungen,
11 unsigned12-Additionen, 54 Byte-Stores und 18 parallelen Registerkopien
überein. Der korrigierte Quarkslab-Pi32v2-Beschreiber ist weiterhin nur eine
lokale Analyseabhängigkeit, kein Bestandteil des Treibers.

Der vergleichende Sandboxlauf erzeugte 436 begrenzte Decode-Datensätze ohne
Decodefehler; zusätzliche DV209-Fenster dienen der Transport-/Datenpfadsuche.
Das ist keine Bestätigung globaler Codegrenzen. Alle Läufe bestätigten die
Isolation und unveränderte Eingabekopien/Originale. 15 lokale Forschungstests
bestanden, darunter Mutationen von Aufrufziel, CALL/GOTO, Bufferregister,
Zugriffsbreite, Länge und abgeschnittenen Eingaben. Keine komplette
Treibersuite oder Hardwareabnahme wird daraus behauptet.

Private Scanner, Testdateien, Sandboxbelege und Rohdekodierungen bleiben
unter `build/jieli-validation-20261018/`; Ergebnisindex:
`anchors/sensor-init-evidence.json`; die Kontrolle aller fünf isolierten
Läufe steht in `anchors/sensor-init-review.json`. Herstellerbinärdateien, SDK-Dumps und
vollständige Disassemblies werden nicht veröffentlicht.

| Geprüfte App | SHA256 |
| --- | --- |
| `JS_3103_DV_V209_No_Key` | `15e48c1c8a6cb9584b059bf54d1f8ad6131a4a3c5b6c082eba394310d03db1d6` |
| `JS_3103_U_DV_V515_No_Key` | `77e77be00ccd03d4c7dc6e469875c977988ffcbecac78a66cfe337c633308673` |
| `JS_3103_U_DV_V608_No_Key` | `6c2155168aae2bfa01b8b391ec2295c4cbf0c27696a49a7d5a063eefdb22147b` |

## Nächster begrenzter Offline-Schritt

Nach dem [Transportfolgepass](JIELI_USB_TRANSPORT.md) den Writer von
DG144 `D+0xa24` und den Funk-/Pakettypbezug auflösen. Indizierte Halfword-
und Vorzeichenoperationen gegen weitere lokale Referenzen prüfen sowie
weitere Offsetschreiber und spätere Registeränderungen
untersuchen. Erst diese Kette kann den Kandidaten
`0,07 Grad/s je Sensorzählwert` mit unseren USB-Rohwerten verbinden.
Ein tatsächlicher Hardware-/Winkeltest und jede Änderung der produktiven
Skalierung benötigen weiterhin eine eigene Freigabe.
