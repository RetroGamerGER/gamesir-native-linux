# Vier Motoren: Kernelvertrag der Alpha

Stand: 13. Oktober 2026. Die Erweiterung ist offline implementiert und geprüft;
sie wurde nicht geladen, installiert oder durch einen neuen Hardwaretest bestätigt.
Der USB-Viermotorencoder und frühere Viermotor-Hardwaretests bleiben die
Protokollgrundlage. Die folgende Anwendungsschnittstelle ist neu.

## Tatsächliche Linux-Unterstützung auf dem Build-System

Die installierten UAPI-Header von `7.2.9-2-garuda` und `/usr/include/linux/input.h`
enthalten `FF_RUMBLE=0x50` mit zwei Größen für die Griffmotoren.
`FF_TRIGGER_RUMBLE` und `struct ff_trigger_rumble_effect` fehlen;
`FF_EFFECT_MIN` ist `FF_HAPTIC=0x4f`. `CONFIG_INPUT_FF_MEMLESS=m` ist gesetzt.

Zusätzlich wurden die **Dateien** des installierten Kernels und des Moduls
statisch untersucht, ohne sie auszuführen oder zu laden:

- `llvm-objdump --disassemble-symbols=input_ff_upload` auf dem vorbereiteten
  `build/vmlinux` zeigt bei `ffffffff821865a0` die Subtraktion `type - 0x58`,
  bei `ffffffff821865a3` den vorzeichenlosen 16-Bit-Vergleich gegen `0xfff7`
  und anschließend den Fehlerzweig nach `ffffffff821866e9` (`-EINVAL`).
  Damit passieren ausschließlich Effektkennungen `0x4f` bis `0x57` diese
  Prüfung. Die Grenzrechnung wurde für sämtliche 65.536 möglichen
  16-Bit-Werte nachgerechnet.
- Das vorhandene `ff-memless.ko.zst` wurde nur in den ignorierten lokalen
  Analyseordner entpackt. Der optimierte Kombinationspfad `ml_play_effects`
  enthält die Fälle `0x50`, `0x51` und `0x52`. Die separaten
  Quellfunktionen wurden durch den Compiler integriert; fehlende Symbolnamen
  allein werden deshalb nicht als fehlende Unterstützung gewertet.

Der [Originalvorschlag v3, Teil 1](https://lists.openwall.net/linux-kernel/2026/07/31/470)
definiert einen eigenen Trigger-Effekttyp `0x4e`, statt die vorhandene
Rumble-Struktur umzudeuten.
[Teil 2](https://lists.openwall.net/linux-kernel/2026/07/31/471) ergänzt dafür
die getrennte Effektkombination im Memless-Code.
Dieser vorgeschlagene Typ scheitert im **hier geprüften installierten Kernel**
bereits an dessen Bereichsprüfung, bevor ein Gamepad-Treiber ihn erhält.
Ein bloßes lokales `#define` im GameSir-Treiber würde das nicht beheben.
Es wurde kein Kernelpatch angewendet und keine Linux-FF-UAPI erfunden.

Dateiprüfsummen, die Disassembly und das lokale Ergebnis liegen unter
`build/results/host-ff-audit/`. Die Aussage gilt für die geprüften Dateien;
sie behauptet weder den Merge-Status des Vorschlags noch identische Fähigkeiten
aller Distributionen. Vollständige installierte `ff-core.c`-/`ff-memless.c`-
Quellen standen nicht zur Verfügung.

## Zwei ausdrücklich unterschiedliche Anwendungspfade

Normale Linux-Spiele verwenden `FF_RUMBLE` über das Input-Gerät:
`strong_magnitude` steuert den linken Griff, `weak_magnitude` den rechten.
Der Memless-Core bestimmt Effektlaufzeit, Wiederholungen und Ende. Der Treiber
merkt sich die aktuellen Zielstärken und erneuert alle 500 ms USB-Leases von
höchstens 1.000 ms. Es gibt kein zusätzliches Gesamtzeitlimit für Spieleffekte.
Ein Stop-, Erase- oder Close-Ereignis des FF-Cores liefert eine Nullaktualisierung.

Vier unabhängige Anwendungskanäle verwendet die Nutzer-Bridge über die
**private GameSir-ABI**, nicht über einen behaupteten Linux-Trigger-FF-Typ.
Die privilegierte Bridge vermittelt App-Aufträge; Apps benötigen keinen
direkten Zugriff auf den Kernel-Kontrollknoten. Clientrechte, Verbindungsabbruch,
Effektlaufzeiten und Konkurrenz mehrerer App-Verbindungen werden von der
Bridge geprüft. Der Kernel erhält nur kurze, erneuerbare Kanalaufträge.

## Exakter privater ABI-Vertrag

`GSN_PULSE` bleibt `_IOW('G', 0x73, struct gsn_pulse)` mit unveränderter
32-Byte-Struktur und ABI-Version 1. Auf x86_64 ist die IOCTL-Nummer `0x40204773`.
Die Reihenfolge der acht `u32`-Felder ist:

```text
abi_version, motor, percent, duration_ms, flags, reserved[0..2]
```

Die Kanalnummern sind `0=LT`, `1=RT`, `2=linker Griff`, `3=rechter Griff`.

| Auftrag | Prozent | Dauer | Flags | Wirkung |
|---|---:|---:|---:|---|
| Setzen/Erneuern | 1–100 | 1–1000 ms | 0 | Nur diesen Kanal setzen; andere Kanäle bleiben erhalten |
| Bedingter Kanalstopp | 0 | 0 | `GSN_PULSE_CANCEL=1` | Nur diesen Kanal stoppen, falls sein letzter Schreiber weiterhin die private Schnittstelle ist |

Alle reservierten Felder müssen null sein. Die neue Cancel-Variante gilt nur
im ausdrücklich aktivierten Dauerbetrieb. Die frühere begrenzte Test-ABI
behält ihre bisherigen Prüfungen; dort bleibt diese neue Variante ungültig.
Ein Prozentwert null mit Flags null ist weiterhin kein gültiger Impuls.

Nach einem erfolgreichen persistenten Bootstrap ist die Sitzung bereits aktiv.
Öffnen des exklusiven Root-Kontrollknotens setzt den Kontrollbesitz;
ein zusätzlicher `GSN_START_SESSION` ist für Pulse nicht erforderlich.
`GET_INFO`, Pulse und Ende können über denselben geöffneten FD erfolgen.
Sein Schließen beendet weder die Runtime noch fremdes Standard-FF. Nicht
erneuerte private Kanal-Leases laufen spätestens nach 1.000 ms ab.

`GSN_STOP` und `GSN_END_SESSION` bleiben absichtliche globale Befehle;
sie sind **kein** Ersatz für den Stop eines einzelnen App-Kanals.
Beim App-Abbruch sendet die Bridge Cancel nur für ihre betroffenen Kanäle,
bevor sie den Kontroll-FD schließt. Bei einem Prozessabsturz bleiben die
kurzen Geräte-Leases als zeitlich begrenzter Rückfall.

## Zuständigkeit und Konkurrenz

Ein privater Griffauftrag ersetzt den aktuellen FF-Zielwert nur dieses Griffs;
der Kernel darf dessen kurze private Lease anschließend nicht selbst als FF
verlängern. Ein neuer Standard-FF-Auftrag übernimmt beide Griffwerte und löscht
ihre Kennzeichnung als private Kanäle. Ein verspätetes Bridge-Cancel lässt
solche inzwischen von FF übernommenen Griffe unverändert.

Bei gleichzeitig fortlaufenden FF- und Bridge-Aufträgen auf demselben Griff
gilt damit der jeweils letzte tatsächlich verarbeitete Auftrag. Wiederholte
Bridge-Erneuerungen können einen zwischenzeitlichen FF-Auftrag erneut
übernehmen. Eine additive Mischung beider Quellen wird nicht behauptet.
Trigger-Kanäle bleiben von Standard-FF unberührt.

Die Kernelkennzeichnung unterscheidet private Kontrolle von Standard-FF,
keine App-Verbindungskennungen. Die exklusive Bridge muss deshalb ihre
eigenen Verbindungen und Generationen koordinieren, damit der Abbruch einer
alten Verbindung keinen neueren privaten App-Auftrag löscht.

## Fehler, Funkpause und Energiezustände

Mehr als zwei Sekunden ohne akzeptierte GIP- **und** IMU-Berichte lösen einmal
neutrale Eingaben und Motorstopp aus. Fehlende GIP-Berichte allein sind bei
ruhigem Controller normal. USB-Identität und Heartbeats bleiben erhalten.
Neue Stärken und Pulse werden mit `EAGAIN` abgewiesen, bis wieder passende
Daten eintreffen. Cancel bleibt als eingeschränkter Aufräumauftrag zulässig.
Alte FF-Ziele und private Besitzmarkierungen werden verworfen; Datenrückkehr
allein startet keinen alten Effekt neu.

END, Fehler, Disconnect, Suspend und Shutdown stoppen Ausgaben und verwerfen
Motorziele. Ein nach Disconnect noch offener Kontroll-FD darf keine neue
Ausgabe oder Eingabeneutralisierung auslösen. PM-Resume bleibt ein expliziter,
einmaliger kontrollierter Dienstauftrag für dieselbe zuvor gestartete
109c-Instanz; vor Abschluss dieser Prüfung werden keine Motoraufträge angenommen.

## Offline-Nachweise

`tests/test_runtime.c` führt den tatsächlichen gemeinsamen C-Kern aus:
alle vier Kanäle gleichzeitig über zehn Sekunden, kanalweise Cancel,
unveränderte Nachbarkanäle und Fristen, Schutz neuerer FF-Griffaufträge,
ungültige Cancel-Varianten, Zuständigkeitswechsel, Legacy-Ablehnung,
Idle-/PM-/Fehlergrenzen sowie bestehende 5-s-/60-s-/1-h-FF-Leases.

`tests/kernel_startup_fake.c` führt extrahierte echte Adapterfunktionen mit
künstlichen USB- und Input-Aufrufen aus: vier Motorwerte im tatsächlichen
13-Byte-Encoderpfad, paralleles Standard-FF, einzelner Triggerstopp,
FD-Schließen ohne globalen Stop und Ablauf der übrigen privaten Lease.
Die bestehenden Tests für END nach Disconnect, PM und Neutralisierung bleiben
enthalten. Diese Prüfungen ersetzen keinen realen Anwendungs- oder Hardwaretest.
