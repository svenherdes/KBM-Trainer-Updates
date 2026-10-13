# Datenschutz und lokale Datenhaltung

Der KBM-Trainer speichert Profile, Antworten, Prüfungsversuche, Einstellungen und Lernstände in einer lokalen SQLite-Datenbank im Benutzerverzeichnis (`%LOCALAPPDATA%\KBMTrainer` unter Windows). Diese Dateien werden nicht zusammen mit dem Quellcode veröffentlicht.

Wenn die Updateprüfung aktiv ist, ruft die Anwendung GitHubs öffentlich verfügbare `version.json` ab. Erst nach Bestätigung werden angebotene Installationsdateien von GitHub heruntergeladen; der bestehende Updateprozess überprüft deren SHA-256-Prüfsumme. Dabei erhält GitHub zwangsläufig technische Verbindungsdaten wie die IP-Adresse. GitHubs Datenschutzbestimmungen: https://docs.github.com/de/site-policy/privacy-policies/github-general-privacy-statement

Nach Prüfung des Quellcodes der Version 1.4.3 ist keine Funktion vorhanden, die automatisch Lernstände oder Profildaten an GitHub versendet. Manuelle Exporte, lokale Sicherungen und vom Nutzer selbst versandte Dateien liegen außerhalb dieser automatischen Updatefunktion.

Bei Fragen, Fehlermeldungen oder weiterentwickelten Versionen sollte die konkrete Version geprüft werden. Dieser Text ist eine technische Projektbeschreibung und keine Rechtsberatung.
