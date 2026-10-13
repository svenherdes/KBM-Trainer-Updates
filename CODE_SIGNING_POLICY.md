# Code signing policy

**Projekt:** KBM-Trainer  
**Repository:** https://github.com/svenherdes/KBM-Trainer-Updates  
**Status:** Antrag bei SignPath Foundation ist geplant, **noch nicht bewilligt**. Aktuelle Downloads sind unsigniert.

## SignPath Foundation

Geplanter Signierdienst (nach Annahme): **Free code signing provided by SignPath.io, certificate by SignPath Foundation.** Diese Nennung kennzeichnet das beabsichtigte Verfahren, nicht eine bereits bestehende Signatur.

## Verantwortlichkeiten

- Autor, Maintainer, Committer: Projektinhaber des GitHub-Kontos `svenherdes`.
- Code Reviews: Projektinhaber; vorgeschlagene Änderungen Dritter erfordern seine Prüfung.
- Signing-Approver: Projektinhaber `svenherdes`; **jede Signierung wird manuell freigegeben**.

## Veröffentlichungsregeln

- Signierte Builds dürfen nur anhand des öffentlich dokumentierten Quellcodes und eines kontrollierten GitHub-Actions-Workflows erstellt werden.
- Die spätere Signing-Pipeline wird bei erfolgreicher Aufnahme auf verifizierte Herkunft und freigegebene Branches begrenzt.
- Ein GitHub-Release wird erst als signiert bezeichnet, wenn ein validiertes, signiertes Artefakt verfügbar ist.
- `version.json` darf für neue Versionen erst nach Verfügbarkeit und SHA-256-Prüfung des jeweiligen Release-Installers geändert werden.
- Die Aufnahme von SignPath ist nicht garantiert. Smart App Control kann je nach System und Richtlinie weiterhin blockieren.

## Datenschutz

Siehe [DATENSCHUTZ.md](DATENSCHUTZ.md). Das Programm versendet keine Trainingsdaten automatisch. Bei Updateprüfung und Download entstehen Verbindungen zu GitHub.
