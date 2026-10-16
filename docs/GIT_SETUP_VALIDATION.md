# Prüfung der Git-Einrichtung

11. Oktober 2026; ausschließlich lokale Offline-Arbeit.

| Prüfung | Ergebnis |
|---|---|
| Bestandssicherung | Alle 70 ursprünglichen Dateien mit SHA256 geprüft |
| Ursprünglicher Offline-PoC | Alle 24 Originaldateien unverändert |
| C-Kern bei Einrichtung | Alle vier vorhandenen C-/Headerdateien unverändert |
| Parser | 44 Tests erfolgreich |
| Sensorvertrag | C-Tests unter ASan/UBSan erfolgreich |
| Zielgeräte-Fixture | Sieben echte Pakete und neun Übergangspakete erfolgreich verglichen |
| Vollcapture | 12.204 IMU, 3.786 GIP, 1.458 XInput; zehn Motor- und 521 Wartungspakete erfolgreich verglichen |
| IMU-Analyse | Alle 12.204 gespeicherten Samples und Quellen geprüft |
| SDL | 12/12 gerätefreie Fälle erfolgreich |
| Diagrammerzeugung | Erfolgreich; neue Ausgabe ausschließlich in build/results |
| Portabilität | Grundtests und SDL aus unabhängiger Dateikopie erfolgreich; ohne lokale Konfiguration, private Capture-Dateien oder Nachbarparser |
| Git-Inhalt | Einzelne Dateiliste geprüft; keine Rohaufnahmen, fremden Installer/Firmware, privaten Home-Pfade oder erkannten Credentials |
| Ignore-Regeln | Build-/Kerneldateien, Rohcaptures, Installer, Firmware, Geheimnisse und lokale Dateien ausgeschlossen; notwendige Fixtures eingeschlossen |
| Prüfsummen | Projektmanifest und kopiertes Parsermanifest vollständig gültig |

Beim Umstellen des SDL-Runners wurde ein falscher Fixture-Feldname (`packets`
statt `cases`) erkannt und korrigiert. Danach bestanden alle zwölf Fälle auch
im unabhängigen Arbeitsordner. Es wurde kein Hardware-Fallback verwendet.

Die Portabilitätskopie und ihre Logs bleiben unter dem lokalen Arbeitsbereich
beziehungsweise `.local/`; sie gehören nicht zu den versionierten Dateien.
Originalmitschnitte und aus Git ausgeschlossene historische Belege bleiben
erhalten. Es wurde kein Remote eingerichtet und nichts veröffentlicht.

Die Prüfung bestätigt Offline-Verhalten und Bestandserhalt. Sie bestätigt
keine fertige native USB-Laufzeit oder physikalische Gyrokalibrierung.
