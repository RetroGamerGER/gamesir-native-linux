> **Historischer Komponentenstand: Sprint 001.** Aktueller gemeinsamer Stand: [PROJECT_STATE](../../../docs/PROJECT_STATE.md), [PROTOCOL](../../../docs/PROTOCOL.md).

# Projektstand – Offline-PoC 0.1

Stand: 11. Oktober 2026.

## Freigegebener Umfang

Der Nutzer hat den Offline-Proof-of-Concept freigegeben und USB-Befehle,
Treiberwechsel sowie Kernel-Patches weiter ausgeschlossen. In der Präzisierung
sind auch neue USB-Mitschnitte und sonstige Hardwarezugriffe ausgeschlossen.
Die vorhandenen Recherchekopien dienen ausschließlich als Textquellen.

## Historischer Vorbefund des Nutzers

Der frühere Mitschnitt wurde nur temporär gespeichert und anschließend gelöscht.
Die Angaben wurden in diesem Schritt weder neu gemessen noch mit Rohdaten geprüft:

| Angabe | Vom Nutzer berichtet |
|---|---|
| USB-Zuordnung im damaligen Mitschnitt | Bus 8, Device 12 |
| USB-ID | `3537:100a` |
| Treiber | `xpad` |
| USB-Ereignisse insgesamt | 17.353 |
| Dem GameSir zugeordnete Ereignisse | 13.557 |
| Eingabeformat | 20 Byte, Xbox-360-kompatibel, IN `0x82` |
| Kurzer Zeitabschnitt | Mehrere aufeinanderfolgende Reports ungefähr 1 ms auseinander |

Ereigniszahlen sind nicht automatisch Zahlen vollständiger Eingabereports;
Submit/Completion und weitere Transferarten können enthalten sein.
Die Angaben reichen nicht zur Rekonstruktion des Mitschnitts oder für eine
Langzeit-Ratenmessung. Einzelne Paketzeilen aus einem früheren Chat wurden
hier nicht als verfügbare Rohdaten angenommen.

Die in dieser Dateisammlung verwendete Busadresse 8/12 ist eine künstliche
Beispielzuordnung. Ebenso ist 8/13 für `109c` frei gewählt. Kein Paket wurde
aus den historischen Zählwerten rekonstruiert.

## Neu erreicht

- Eigenständiger reiner Datei-Decoder für die dokumentierten Grundformate.
- Strikte Metadaten mit expliziter künstlicher/realer Herkunft.
- 19 gültige künstliche Pakete und 19 absichtlich negative Fälle.
- Regressionstests für 16-Bit-Vorzeichen, Endianness, Paketgrenzen, Zusatzbuttons,
  Konfigurationsantworten und die Unterscheidung von Selektor und Länge.
- Getrennte Auswertung von Identitäten und Pakettypen ohne Hardware-Zusagen.
- Ablehnung von Spezialdateien und Schutz gegen versehentlichen Gerätezugriff.

Die Abdeckung von synthetischen Layouts ist Softwarevalidierung. Es gibt
weiterhin keine neue Hardwarebestätigung für IMU, vier Motoren, Gleichzeitigkeit,
Firmwarezustände oder SDL-/Steam-/Proton-Kompatibilität.

## Wiederherstellung

Der Prototyp verändert keine Controller- oder Systemzustände und hat keinen
Hintergrunddienst. Zum Beenden genügt das Ende des lokalen Prozesses.
Es wurden keine Treiber-, udev-, Firmware-, Profil- oder Kerneländerungen vorgenommen.
Es gibt kein Git-Repository und keinen Remote; andere Projekte bleiben unberührt.

## Nächster zulässiger Schritt

Bereitgestellte echte gespeicherte Paketzeilen können offline eingebunden werden.
Dazu Originaldatei, Herkunft, Zielgerät-Zuordnung, Capture-Längenbegrenzung und
Zeitbasis dokumentieren. Einen Importer erst anhand des tatsächlichen Dateiformats
und mit unveränderten Referenzzeilen prüfen.

Ein neuer Mitschnitt oder irgendein aktiver Hardwaretest ist ein separater,
derzeit nicht freigegebener Arbeitsschritt. Auch ein Kernel-Patch ist nicht freigegeben.
