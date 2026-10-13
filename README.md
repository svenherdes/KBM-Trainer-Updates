# KBM-Trainer

Kostenloses Windows-Lernprogramm für die Vorbereitung auf eine kaufmännische Umschulung und die Ausbildung im Büromanagement.

**Aktuelle Version:** 1.4.3 · **4.200 Trainingsfragen** · **Lizenz:** [GNU GPL-3.0-only](LICENSE)

## Funktionen

- Sechs Hauptbereiche: Rechnungswesen, Geschäftsprozesse, Deutsch & Rechtschreibung, Schriftverkehr, Büroorganisation sowie Datenschutz & IT-Sicherheit.
- Inhalte zu Finanzbuchhaltung, kaufmännischer Steuerung, Einkauf und Logistik.
- Drei Schwierigkeitsstufen, Trainings- und Prüfungsmodus, persönliche Lernstände und lokale Profile.
- Lokale SQLite-Datenbank; Updateprüfung über GitHub mit SHA-256-Verifikation.

## Installation

Den Windows-Installer gibt es unter [Releases](https://github.com/svenherdes/KBM-Trainer-Updates/releases/latest). Aktuelle Installationsdateien sind **noch nicht digital signiert**. Auf einigen PCs kann Windows Smart App Control die Ausführung blockieren. Bitte Sicherheitsfunktionen deswegen **nicht deaktivieren**.

## Quellcode und Entwicklung

Dieses Repository enthält den Quellcode zur Version 1.4.3. Der Einstieg ist `app.py`, die Fragenbanken befinden sich in den entsprechenden Python-Modulen. Das Programm verwendet Python 3.11, Tkinter und SQLite.

Unter Windows mit Python 3.11:

```powershell
python test_core.py
python test_exam_style.py
python test_privacy.py
python test_knowledge_143.py
python pool_audit.py
python app.py
```

Der vorhandene Windows-Build erfolgt mit PyInstaller und Inno Setup (`ERSTELLE_UPDATE_1.4.3.bat`). Die GitHub-Actions-Datei `.github/workflows/windows-testbuild.yml` bietet einen **manuell gestarteten, nicht veröffentlichenden Testbuild**. Sie wurde für SignPath vorbereitet; eine Freigabe durch SignPath liegt derzeit nicht vor. Das bestehende Updateverfahren wird dadurch nicht geändert.

## Datenschutz

Profile, Übungsergebnisse und Lernstände liegen auf dem eigenen Computer. Einzelheiten und externe Netzwerkzugriffe: [Datenschutz](DATENSCHUTZ.md).

## Code signing policy

Das Projekt bemüht sich um eine kostenlose Codesignierung durch SignPath Foundation. **Bisher ist weder eine Aufnahme bestätigt noch ein signierter Installer verfügbar.** Voraussetzungen, Rollen und Ablauf: [Code signing policy](CODE_SIGNING_POLICY.md).

## Lizenz

Copyright © 2026 Sven Herdes. Quellcode unter [GNU General Public License Version 3.0 (nur Version 3)](LICENSE), SPDX: `GPL-3.0-only`. Eine Weitergabe und Bearbeitung auch für kommerzielle Zwecke ist gemäß der Lizenz erlaubt; bei Weitergabe gelten ihre Copyleft-Pflichten. Ein Anspruch auf Gewährleistung besteht nicht.

Angaben und Lernfragen ersetzen keine individuelle Rechts-, Steuer- oder Ausbildungsberatung.
