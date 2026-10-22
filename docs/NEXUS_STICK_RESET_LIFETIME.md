# Stickkalibrierung: Soft Reset, Startinitialisierung und Sequenznummer

Stand: 22. Oktober 2026. Offline-Fortsetzung der
[Rücksetzpfad-Analyse](NEXUS_STICK_RESET_PATHS.md).
[Fundstellen und Prüfbeleg](evidence/NEXUS_STICK_RESET_LIFETIME_20261022.json).

Die [Folgeanalyse der Reconnect-Zweige](NEXUS_STICK_RECONNECT_ROUTES.md)
ordnet inzwischen die beiden offenen Task-Aufträge ihren Empfängern zu und
trennt Reset-, Verbindungsannahme- und Schlafpfade.

## Ergebnis

**Ein vollständiger normaler Firmware-Neustart und ein Funk-Reconnect sind
verschiedene Fälle.** Der normale Startcode des untersuchten Dongles löscht
den RAM mit ausstehendem Auftrag, Nutzlastkopie und Sequenznummer. Beim
Controller löscht die entsprechende Initialisierung den zuletzt empfangenen
Sequenzwert sowie die untersuchten Kalibrierflags und Arbeitsbereiche.
Alte Inhalte dieser RAM-Felder überleben den abgeschlossenen Löschlauf nicht.
Das ist kein Löschen der dauerhaft gespeicherten Kalibrierung.

Das bisher als extern offen geführte Dongle-Resetziel ist jetzt einem
**bereits vorhandenen RAM-Codebereich** zugeordnet. Es setzt über einen
Registerhelfer Bit 4 im P33-Register `0xa0`. Die unabhängige, lokal vorhandene
Jieli-Referenz verwendet dasselbe Register und Bit für ihren Chip-Reset.
Damit ist die Reset-Interpretation durch Befehle und Referenzcode gestützt,
nicht allein durch den Firmwaretext „Soft Reset“. Ein tatsächlich erfolgreicher
Reset und der Weg durch Boot-ROM und Startcode wurden nicht ausgeführt.

**Ein reiner Funkverlust storniert einen alten Befehl weiterhin nicht
nachweislich.** Die zuvor untersuchten Verlustzweige können auch nur
Verbindungsfelder und die Ausgabefreigabe ändern. Dass jeder Reconnect den
vollständigen Startcode durchläuft, ist nicht belegt.

Für die Sequenzprüfung folgt daraus: Bleibt der zuletzt verarbeitete Wert
erhalten, wird ein unmittelbar wiederholter gleicher Wert im untersuchten
Pfad nicht erneut verteilt. Wird nur der Controller neu initialisiert,
beginnt dieser Vergleichswert wieder bei null. Eine möglicherweise im Dongle
verbliebene Kopie mit anderer Sequenz könnte dann den Vergleich passieren.
**Das ist eine bedingte Möglichkeit, kein nachgewiesener verspäteter Befehl
oder wirksames Finish.** Kalibrierzustand und weitere Protokollprüfungen gelten
zusätzlich.

## Quellen und Grenzen

Unveränderte lokale Firmwaredateien **DG144** und **DV209**, vorhandener
isolierter statischer Decoder und bereits gespeicherte offizielle
Jieli-Referenzen. Herstellerdateien und vollständige Disassemblierungen bleiben
außerhalb von Git. Der Prüfbeleg enthält Adressen, Hashes und eigene Aussagen.

- [Offizielles Jieli-ROM-Listing, Commit fdc018de](https://github.com/Jieli-Tech/fw-AC63_BT_SDK/blob/fdc018de81629e21e594d677cf05f87d288be0f0/cpu/br23/tools/rom.lst):
  `chip_reset`, `P33_CON_SET`, Bytezugriff und Wiederholungs-/Speicherbefehle.
- Bereits vorhandener Commit-Datensatz von `Jieli-Tech/fw-AC63_GP_MCU`,
  `53fd6bc15600a4c06aa9932b1f1b7b66a2d54c29`: AC632N-Header mit
  `P3_PR_PWR` bei `0xa0`, `cpu_reset` über `p33_soft_reset` und Startinitialisierung.
  Das ist eine Familienreferenz, keine zusätzliche Bestimmung des GameSir-MCU.

Es erfolgte kein Download, Netzwerk-, SSH-, USB-, Funk- oder Input-Zugriff.
Keine Hersteller-App-/Firmwareausführung oder Emulation. Decoder und laufende
Treiber bleiben unverändert. Beide Installationen und die zurückgestellte
Treiberdiagnose bleiben erhalten; präzise Gyrokalibrierung bleibt pausiert.

`D = 0x62c0` bezeichnet die Dongle-, `B = 0xf140` die Controller-RAM-Basis.
Codeadressen sind Dateioffsets, sofern nicht ausdrücklich als RAM-Laufadresse
bezeichnet. Die Zuordnung zur installierten Firmware wurde nicht abgefragt.

## 1. Das Reset-Ziel liegt im bekannten RAM-Suffix

Die Startliterale bei `0x62`, `0x68` und `0x6e` beschreiben RAM-Ziel null,
Quellzeiger und Länge. Mit der bereits geprüften Datenadressierung ergibt sich:

| Firmware | Suffix in der Datei | Länge | Reset-Einstieg in der Datei | RAM-Laufadresse |
|---|---:|---:|---:|---:|
| DG144 | `0x37028` | `0x52f0` | `0x37174` | `0x14c` |
| DV209 | `0x4f718` | `0xd1ec` | `0x4f822` | `0x10a` |

Der vorher betrachtete DG-Sprung `0x79fa` hat bei Dateibasis null das Ziel
`0x20008c`. Mit der schon verwendeten relativen Code-Alias-Abbildung
`0xffe000c0` und 32-Bit-Adressarithmetik wird daraus `0x14c`; im Suffix liegt
der Code somit bei `0x37174`. Die alte Einordnung als noch unzugängliches
externes Ziel wird hier ausdrücklich präzisiert.

DV209 enthält denselben Reset-Einstieg bei `0x4f822`. Ein begrenzt geprüfter
Sprung bei `0xd052` ergibt entsprechend `0x20004a` → RAM `0x10a`.
Das bestätigt die passende Reset-Routine auf beiden Seiten, aber noch nicht,
welcher reale Funkverlust diesen DV-Zweig erreicht.

Beide Einstiege übergeben dieselben vier Argumente an den Registerhelfer:
Register `0xa0`, Bitposition 4, Breite 1, Wert 1. DG läuft weiter über
`0x3714c`, DV über `0x4f7fa`. Der Helfer liest den Registerwert, ersetzt das
betroffene Bit und schreibt ihn zurück. DG-Lese-/Schreibhelfer bei
`0x370c2`/`0x3710a` entsprechen strukturell den offiziellen P33-Bytehelfern.
Die Referenzroutine `chip_reset` schreibt `0x10` in dasselbe Register.

Ein relevanter Decoderfehler wurde bei der Gegenprüfung erkannt:
DG `0x3715c` beziehungsweise DV `0x4f80a` wird als AND ausgegeben. Das exakte
Befehlswort steht im offiziellen `P33_CON_SET`-Listing bei `0x112428` jedoch
für **bitweises NOT**. Für diese Aussage gilt der unabhängige Byte-/Referenzbeleg;
die falsche P-Code-Ausgabe wird nicht als Maskenberechnung übernommen.
Der Decoder wurde nicht geändert. Ebenso wird aus dieser begrenzten Prüfung
keine Validierung sämtlicher P33- oder bedingter Befehlsformen abgeleitet.

## 2. Welche RAM-Inhalte der normale Start löscht

Bei beiden Images lädt der Startcode bei `0x36` den Bereichsanfang, bei
`0x3c` den Nullwert und bei `0x3e` die Bytezahl. Es folgen Wortzählung und
die Wiederholungs-/Speicherschleife bei `0x46…0x4a`.

| Firmware | Anfang | Bytezahl | Ende, exklusiv |
|---|---:|---:|---:|
| DG144 | `0x5b60` | `0x11ca4` | `0x17804` |
| DV209 | `0xda60` | `0x16688` | `0x240e8` |

Die vorhandene Decoderfassung erkennt die REP-Form nicht. Deshalb wurden
deren ursprüngliche Operanden und die angrenzenden Wortstore-/Rücksprungformen
direkt mit dem offiziellen ROM-Listing gegengeprüft. Diese Stelle gehört
nicht zu den als fehlerfrei dekodiert gezählten Bereichen. Es wurde kein
Firmwareprogramm ausgeführt, um die Schleife zu beobachten.

Der DG-Bereich enthält insbesondere:

- `D+0x48`: Sequenzbyte und `D+0x4a`: gehaltene Länge;
- `D+0x2d0`: Pending-Flag und `D+0xb64`: gehaltene Nutzlast;
- `D+0x2cc`: Durchlauf-Freigabe, `D+0x118`: Wiederholungszähler;
- `D+0x2dc`: Warteschlangenzeiger.

Der DV-Bereich enthält insbesondere:

- `B+0x50`: zuletzt angenommene Sequenz;
- `B+0x1b3a…0x1b3c`: untersuchte Kalibrierflags;
- die gesicherten RAM-Datensätze ab `B+0x1b3e` und `B+0x1b5d`;
- beide Stick-Arbeitsbereiche ab `B+0x1b8e` und `B+0x1bf6`.

Die Bereiche wurden einschließlich ihrer Endgrenzen geprüft, nicht nur auf
einen enthaltenen Anfangszeiger. Der abgegrenzte Pending-Nutzlastnachweis
verwendet konservativ 256 Byte als Hülle der Byte-Längenrepräsentation;
daraus wird keine tatsächliche Pufferallokationsgröße abgeleitet.

**Aussagegrenze:** Nach abgeschlossenem normalem Löschlauf sind diese alten
RAM-Inhalte weg. Spätere Initialisierung, neu eintreffende Host-Befehle und
das [Laden dauerhaft gespeicherter Kalibrierwerte](NEXUS_STICK_READBACK.md)
sind davon getrennt. Weder Flash-Löschen noch Rückgängigmachen eines bereits
verarbeiteten Finish folgt aus dem Nullsetzen von RAM. Der Löschlauf ist
auch kein Nachweis, dass ein bloßer Funk-Reconnect ihn aufruft.

## 3. Sequenznummer: Duplikatfilter mit begrenzter Lebensdauer

DG144 erhöht bei einer neuen Nachricht das Byte `D+0x48`
(`0xa828…0xa832`), verwendet es im Vorspann und hält es für Wiederholungen.
Der Retry-Zweig verwendet denselben Wert. Im geprüften neuen Nachrichtenpfad
ist dies eine Byte-Sequenz; der inkrementierte Wert wird als Byte gespeichert.
Ohne zusätzliche Zustandsänderungen läuft er somit nach 255 wieder auf null.
Das ist keine neue globale Aussage über jeden möglichen Writer.

DV209 liest die empfangene Sequenz bei `0xe244` und den letzten Wert bei
`0xe246`. **Nur ungleiche Werte** lassen die vier Befehle ab `0xe24e` laufen:
neuen Wert merken, Vorspann entfernen und über `0xde2a` verteilen. Bei Gleichheit
wird diese Verteilung übersprungen. Beide Fälle bauen danach Transportstatus
`0x14` auf. Die bedingte Blockgrenze wurde erneut geprüft.

Das Feld speichert einen letzten Wert, keine Historie aller Aufträge und keine
belegte, einen Neustart überdauernde Sitzungskennung. Der bekannte Filter
schützt deshalb vor der unmittelbaren Wiederholung bei erhaltenem Vergleichswert;
allein daraus folgt kein „genau einmal“ über Reset, Überlauf oder dazwischen
verarbeitete andere Sequenzen.

| Bedingter Fall | Bedeutung für einen alten Auftrag |
|---|---|
| Nur Funkverlust; Pending und letzter Sequenzwert bleiben erhalten | Nach erneuter Sendefreigabe kann eine Wiederholung denselben Filterwert treffen und ohne erneute Verteilung beantwortet werden. Erhalt und Sendefreigabe über den gesamten Reconnect sind noch nicht bewiesen. |
| Normaler Dongle-Neustart vollständig durchlaufen | Alte gehaltene Kopie, Pending und Dongle-Sequenz werden gelöscht. Dieser alte RAM-Auftrag kann nicht unverändert aus diesem Pending-Pfad weiterlaufen. |
| Nur Controller durchläuft den normalen Start; Dongle hält tatsächlich noch Pending | Der Vergleich startet bei null. Eine alte Nichtnull-Sequenz kann den Ungleichvergleich passieren; eine Null-Sequenz zunächst nicht. Weitere Empfangs-/Kalibrierbedingungen bleiben maßgeblich. |
| Beide durchlaufen den normalen Start | Die betrachteten Pending-/Sequenzfelder beginnen neu; kein Fortbestand dieser alten RAM-Kopie. Neu gesendete Host-Aufträge sind ein anderer Fall. |
| Funk-Reconnect ohne geklärten Reset-/Taskpfad | Weder vollständiges Löschen noch tatsächliche spätere Ausführung darf zugesichert werden. |

Insbesondere löscht ein Controller-Neustart auch die untersuchten
Kalibrierflags. **Erneute Verteilung eines Pakets ist daher nicht automatisch
eine erneute Kalibrierung oder Speicherung.** Ob ein späteres Start, Finish
oder Exit wirksam wird, hängt weiter vom jeweiligen Dispatcherzustand ab.
Es gibt hier keinen nachgewiesenen Replay-Bug und keine belegte Endlosschleife.

## 4. Konsequenz für den geplanten Linux-Ablauf

Die normale Bedienung bleibt **Start → bewegen → bereit → Finish**, alternativ
Exit. Die Firmware übernimmt das Speichern; keine zusätzliche Persistenz-ACK
wird als neue Voraussetzung eingeführt.

Nach Verbindungsverlust muss die Anwendung ihre eigenen verzögerten Aktionen
stoppen und den Vorgang als unterbrochen behandeln. Ein bereits an den Transport
übergebener Befehl ist allein dadurch nicht nachweislich storniert. Deshalb
kein blindes Wiederholen eines unklar zugestellten Finish und kein automatisches
Start/Exit nach Reconnect. Ein Geräte-Reset wird hier ausdrücklich nicht als
neuer Abbruchbefehl vorgeschlagen oder implementiert.

## Prüfung und verbleibende Arbeit

Der abschließende isolierte Decoderlauf umfasst **22 begrenzte Bereiche und
224 Instruktionsdatensätze**, ohne fehlgeschlagene Zeile in diesen Bereichen.
224 Instruktionsanker und 22 Bereichshashes sind festgehalten. Unabhängige
Prüfungen: 171 Literal- und 179 Kurztransferformen aus dem offiziellen Listing,
elf konkrete relative Transferziele samt veränderten Gegenbeispielen,
vier P33-Referenzblöcke, zwölf veränderte Schleifenbelege, zehn veränderte
Startliterale sowie 13 RAM-Bereiche mit 26 absichtlich falschen Grenzen.
Eine eigene Wahrheitstabelle mit 65.536 Sequenzpaaren illustriert die
Vergleichsfolgen; sie ist keine Firmwareemulation oder Hardwarevalidierung.
Alle **16 bestehenden Dialogtests** bestehen weiterhin.

Suchläufe trafen auch nicht unterstützte REP-Formen. Erfolgreiche begrenzte
Dekodierung bedeutet nicht vollständige semantische Korrektheit: der oben
ausdrücklich korrigierte NOT-Befund und die schon bekannte, hier ausgeschlossene
DV-Form `0xe976` zeigen diese Grenze. Quellen und Decoder bleiben unverändert.

Die nächste offene Frage ist jetzt enger: **Welcher reale Reconnect-Zweig
führt zur normalen Neuinitialisierung, welcher nur zum Verbindungswechsel?**
Dafür fehlen insbesondere die vollständigen Wirkungen der nachgelagerten
Controller-Aufträge `joypadtask 0x400008/0x40000b` und weiterer indirekter
Zustandswechsel. Der Offline-Nachweis ersetzt keine Beobachtung des aktiven
Firmwarepaars. Eine vollständige Alias-/Writeranalyse, ein automatischer Exit
bei RF-Verlust und die tatsächliche späte Zustellung bleiben unbewiesen.

Die ältere Provider-/USB-Modus-Lücke bleibt separat bestehen. Keine neue
Hardwarefreigabe, Treiberänderung oder Garantie für einen Firmware-Updater
folgt aus dieser Untersuchung.
