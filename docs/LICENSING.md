> Public export: personal tester, host and path references were anonymized. Historical evidence hashes refer to the private originals.

# Lizenz und Herkunft von GameSir Native Linux

Stand: 16. Oktober 2026. [tester] hat für den eigenen Projektbestand ausdrücklich
**GNU General Public License Version 2 only (`GPL-2.0-only`)** gewählt.
Es gilt keine Wahl einer späteren GPL-Version. Der vollständige Lizenztext
steht in [COPYING](../COPYING). Diese Erklärung umfasst eigenen Kernel- und
Userspace-Code, Parser, Tests, Build-/Pakethelfer und eigene Dokumentation.
Externe Referenzen, fremde Inhalte und die unten bezeichnete UAPI-Ausnahme
behalten ihre jeweiligen Bedingungen.

## Lizenztext, SPDX und UAPI

`COPYING` enthält unverändert den vollständigen GPL-v2-Text aus dem
`License-Text`-Abschnitt der [offiziellen Linux-Referenz v6.12](https://github.com/torvalds/linux/blob/v6.12/LICENSES/preferred/GPL-2.0).
SHA256: `e6d6a009505e345fe949e1310334fcb0747f28dae2856759de102ab66b722cb4`.
Die Beispielanwendung im Anhang nennt auch spätere Versionen; diese
Musterformulierung ist keine entsprechende Lizenzwahl für dieses Projekt.
Die ausdrückliche Projektwahl und SPDX-Angaben lauten `GPL-2.0-only`.
Diese Unterscheidung beschreibt auch die [SPDX-Lizenzreferenz](https://spdx.org/licenses/GPL-2.0-only.html).

Eigene Quellcodedateien tragen den SPDX-Hinweis an der ersten möglichen
Kommentarzeile: C-Quellen mit `//`, Header mit `/* ... */`, Python/Shell/Make
mit `#`; bei Skripten bleibt der Shebang zuerst. Bereits vorhandene Autoren-
und Quellenangaben bleiben erhalten. Die vier eigenen synthetischen SDL-
Testquellen `tests/sdl_buttons_fixture.c`, `sdl_buttons_probe.c`,
`sdl_evdev_fixture.c` und `sdl_sensor_probe.c` trugen zuvor MIT. Der aktuelle
Stand wird gemäß [tester]' neuer Lizenzentscheidung auf GPL-2.0-only gestellt;
historische MIT-Stände werden dadurch nicht rückwirkend geändert. Es wurde
kein SDL-Fremdcode umetikettiert.

`include/uapi/gs_native.h` behält bewusst
`GPL-2.0-only WITH Linux-syscall-note`. Die Ausnahme ist auf diesen Header
begrenzt und stellt keine zweite Lizenzwahl für den Treiber dar. Ihr
[vollständiger Text](../LICENSES/exceptions/Linux-syscall-note) stammt
bytegleich aus [Linux v6.12](https://github.com/torvalds/linux/blob/v6.12/LICENSES/exceptions/Linux-syscall-note),
SHA256 `8e378ab93586eb55135d3bc119cce787f7324f48394777d00c34fa3d0be3303f`.
Die [Kernel-Lizenzregeln](https://docs.kernel.org/process/license-rules.html)
sehen diese Kennzeichnung für die Verwendung von UAPI-Headern durch
Userspace vor. `MODULE_LICENSE("GPL")` bleibt der gültige Kernel-Metadatentag;
die genaue Version wird über SPDX und `COPYING` erklärt.

Die bestehenden GPL-v2-Volltexte der optionalen Steam-Pakete bleiben
unverändert. Ihr Wortlaut unterscheidet sich in Adressformat und
Library-/Lesser-Verweisen von der Linux-Kopie; ihre SPDX-/Paketentscheidung
bleibt ebenfalls GPL-2.0-only. Lizenztexte selbst werden nicht umgeschrieben.

## Vorher geprüfte Codeherkunft

Die Prüfung erfolgte vor der SPDX-Vereinheitlichung am Quellenstand
`3a3ac91`. Eigene Quellen wurden mit gespeicherten Referenzen verglichen:
109 Projektdateien gegen 170 Referenzdateien, keine identischen Blöcke aus
vier aussagekräftigen normalisierten Quellzeilen gefunden. Zusätzlich wurden
C-/Pythondecoder, Datentypen, Validierung und Sitzungsabläufe gelesen. Die
sechs Parserdateien stimmten zuvor bytegleich mit dem erhaltenen eigenen
Offline-PoC überein. Das stützt die dokumentierte eigene Implementierung;
es ist keine vollständige urheberrechtliche Freigabeprüfung. Der bloße
Verzicht auf einen Import wäre kein ausreichender Unabhängigkeitsnachweis.

| Referenz | Geprüfte Herkunft/Lizenz | Rolle und Grenze |
| --- | --- | --- |
| [Deadband `771b28a`](https://github.com/broroeror/gamesir-linux-tools/tree/771b28ae75b0a614a6a7fec9aa606606a27b3b8d) | MIT, Copyright 2026 broroeror; lokale `LICENSE`, SHA256 `5af9a74598efe54d8f5653ed4f712786301d61394af7b21eb5654158d5ced897` | Protokollreferenz; keine erkannte Codeübernahme. Bei künftiger Übernahme MIT-Hinweise erhalten. |
| [g7ctl `0ea4b52`](https://github.com/questionablesyntax/g7ctl/tree/0ea4b5223ba2191c88a3c4d1ff8d34f594bfeb1b) | Projekt/GUI GPL-3.0-or-later; `pyg7/` separat Apache-2.0 laut Unterpaket-Lizenz, README und Metadaten. `pyg7/LICENSE` SHA256 `cb5e8e7e5f4a3988e1063c142c60dc2df75605f4c46515e776e3aca6df976e14` | Referenz für Protokollfakten, keine erkannte Quellcodeübernahme. Kein pauschales GPL-v2-kompatibles Codefundament. |
| [Linux `xpad.c`, `5fce1616`](https://github.com/gregkh/linux/blob/5fce161649b4d779d1b76d9fcd52dc77779774b8/drivers/input/joystick/xpad.c) | GPL-2.0-or-later; gespeicherter Quellhash in der Quellenkarte | Referenz für Eingabesemantik und GIP; keine erkannte kopierte Implementierung. |
| [Linux `hid-playstation.c`, `a5ebb762`](https://github.com/torvalds/linux/blob/a5ebb76233b79db01e82e061173cb73c6d2b5c6b/drivers/hid/hid-playstation.c) | GPL-2.0-or-later, Copyright 2020–2022 Sony Interactive Entertainment | Architektur-/Kalibrierungsreferenz; keine Übernahme von Sony-Kalibrierungswerten oder Quellblöcken. |
| [SDL3 `829a65d7`](https://github.com/libsdl-org/SDL/tree/829a65d769d935c4852f8159e964312c0957260a) | zlib-Hinweise in den untersuchten Referenzdateien, unter anderem Sam Lantinga und Collabora | API-/evdev-Referenz und extern benötigte Testbibliothek, kein mitgelieferter SDL-Quellcode. Einzelne Unterkomponenten können eigene Lizenzen haben. |

Dateihashes und genaue Symbole bleiben in der vorhandenen
[Protokoll-Quellenkarte](../tools/offline/docs/source-map.json), im
[SDL-Quellmanifest](sdl-source-manifest.json) und im
[DualSense-Vergleich](DUALSENSE_SENSOR_COMPARISON.md) erhalten. Die SPDX-Zeilen
ändern keine externen Quellhashes. Die übernommenen eigenen USB-Guard-Helfer
erhalten getrennte aktuelle Hashes; ihre historischen Validierungshashes und
ursprünglichen Quelldateien bleiben erhalten.

GPLv3-only-Code und Apache-2.0-Code dürfen nicht allein durch Entfernen der
Lizenzhinweise als GPL-2.0-only integriert werden. Insbesondere erläutert
die [Apache Software Foundation](https://www.apache.org/licenses/GPL-compatibility.html)
die fehlende GPL-v2-Kompatibilität der Apache-2.0-Bedingungen. Eine künftig
gewünschte Übernahme benötigt eine passende Lizenz-/Rechtegrundlage und eine
gesonderte Prüfung; die heutige Protokollreferenz erteilt diese Erlaubnis nicht.
Hersteller-App, DLLs, Firmware, Ressourcen und vollständige USB-Rohmitschnitte
sind nicht Teil des veröffentlichten eigenen Quellbestands und werden durch
diese Lizenzentscheidung nicht freigegeben.

## DKMS und veröffentlichbare Pakete

Der Paketgenerator führt `COPYING`, die UAPI-Ausnahme und diesen Bericht
ausdrücklich in seiner Dateiliste. Die Lizenztexte liegen im Quellarchiv,
im DKMS-Quellbaum unter `/usr/src/gamesir-native-<Version>/`, in der
installierten Dokumentation und unter:

```text
/usr/share/licenses/gamesir-native-dkms/COPYING
/usr/share/licenses/gamesir-native-dkms/Linux-syscall-note
```

Dateirechte sind 0644. Die Paketmetadaten bleiben `GPL-2.0-only`. Vor einer
Veröffentlichung von Binärpaketen müssen zum exakten Release passende,
vollständige Quellen samt Build-/Installationsskripten zugänglich sein.
Dieser Auftrag ändert keine installierten Dateien, Paketversion, Dienste,
Module, Treiberbindungen oder Controllerzustände und veröffentlicht nichts.

## Prüfung dieses Vorbereitungsstands

`make test` ist vollständig bestanden. Der neue gerätefreie Lizenztest
prüft 125 Quell-/Konfigurationsdateien: 124 mit GPL-2.0-only, genau ein
UAPI-Header mit Linux-syscall-note. Er prüft zudem die Volltext-Hashes und
den gültigen `MODULE_LICENSE`-Tag. Die 25 Pakettests bestätigen Textbytes,
Rechte und Zielpfade im Archiv/Offline-Staging; fehlt GPL oder Ausnahme,
bricht der Generator vor Erzeugung eines Ausgabeverzeichnisses ab.

Das frühere Lizenzprotokoll `build/gpl2-prealpha-tests.log` gehört zum Stand
`6abb83e` mit damals 124 Quellen. Die anschließende öffentliche README-Prüfung
erhöht den Bestand auf 125. Die vollständige Suite besteht erneut im aktuellen
Arbeitsbaum und in einer isolierten Quellkopie ohne Git/private Daten;
Protokolle `build/prealpha-readme-tests.log` und
`build/prealpha-public-readme-audit/tests.log`, Details `docs/RELEASE_AUDIT.md`.
Diese Buildausgaben bleiben außerhalb von Git.
Das eigene Parsermanifest und aktuelle Guard-Hashes sind
aktualisiert, historische Validierungshashes und externe Quellenkarten
unverändert. Nur Lizenzkommentare ändern die bisherigen ausführenden Quellen;
funktionale Änderungen betreffen Paketbeigaben und deren Offline-Regressionen.
Kein neues Installationspaket wurde zur Installation freigegeben oder im
System installiert. Eine spätere Veröffentlichung muss ihren exakten
Quellcommit und neu erzeugte Artefakte mit diesen Lizenzbeigaben verwenden.

## Perspektive Linux-Mainline

Die Lizenzwahl passt zur GPL-v2-Lizenzbasis des Kernels; sie ist keine
Zusage einer Aufnahme. Für einen späteren Patchsatz sind zusätzlich die
zuständigen USB-/Input-/IIO-Maintainer, aktuelle Entwicklungsbasis, normale
Kernel-Schnittstellen, nachvollziehbare Hardwarebelege und bestehende
Treiberzuständigkeiten zu prüfen. Der externe Sitzungsmanager und die private
experimentelle ABI sind dadurch nicht automatisch upstreamgeeignet.

Die offizielle [Anleitung zur Patch-Einreichung](https://docs.kernel.org/process/submitting-patches.html)
verlangt nachvollziehbare einzelne Änderungen und die Herkunftsbestätigung
nach [DCO 1.1](https://developercertificate.org/). Zukünftige Beiträge müssen
ihre Herkunft und kompatiblen Lizenzen mitführen; Sign-offs dürfen nur mit
wahrer, autorisierter Bestätigung erfolgen. Für diesen Auftrag werden keine
nachträglichen Sign-offs erfunden, alten Commits umgeschrieben oder Patches
an Maintainer gesendet. Die Gyrokalibrierung bleibt auf Eis.
