from __future__ import annotations

import hashlib
import re
from dataclasses import replace


def _pick(seq, qid, offset=0):
    h = hashlib.sha256((qid + f'|{offset}').encode('utf-8')).digest()
    return seq[int.from_bytes(h[:4], 'big') % len(seq)]


def _uniq(items, correct):
    out=[]
    seen={correct.strip().casefold()}
    for x in items:
        k=x.strip().casefold()
        if k and k not in seen:
            seen.add(k); out.append(x)
    return out[:3]


def _gp_group(topic: str):
    t=topic.casefold()
    if any(x in t for x in ['rechnung', 'dokument', 'beleg']): return 'beleg'
    if any(x in t for x in ['liefer', 'wareneingang', 'menge', 'qualität', 'reklamation']): return 'lieferung'
    if 'angebot' in t: return 'angebot'
    if any(x in t for x in ['zahlung', 'gutschrift']): return 'zahlung'
    if any(x in t for x in ['kontrolle', 'risiko', 'prozess']): return 'prozess'
    return 'ablauf'


def _gp_wrong(q):
    group=_gp_group(q.topic)
    level=q.level
    banks={
      'Anfänger': {
        'beleg': [
          'Zunächst nur einen der vorhandenen Belege prüfen und die übrigen Angaben vorerst übernehmen.',
          'Den Vorgang weiterbearbeiten und die vollständige Belegprüfung erst vor der Zahlung nachholen.',
          'Die Abweichung notieren, aber den nächsten Prozessschritt trotzdem schon auslösen.',
          'Nur die rechnerische Summe prüfen; Mengen, Preise und Vereinbarungen zunächst unverändert übernehmen.',
          'Die Unterlagen ablegen und erst bei einer späteren Rückfrage erneut prüfen.'
        ],
        'lieferung': [
          'Die Lieferung zunächst im System als vollständig erfassen und die Abweichung anschließend klären.',
          'Nur die Stückzahl prüfen; Zustand und vereinbarte Ausführung erst bei einer Reklamation betrachten.',
          'Die sichtbare Abweichung dokumentieren, aber Bestellung und Lieferschein zunächst nicht abgleichen.',
          'Die Ware zunächst weitergeben und die Klärung mit dem Lieferanten später nachholen.',
          'Nur die offensichtlich betroffene Position prüfen und den restlichen Wareneingang ungeprüft übernehmen.'
        ],
        'angebot': [
          'Das günstigste Angebot auswählen und Lieferzeit sowie Zahlungsbedingungen erst danach prüfen.',
          'Das bekannte Lieferunternehmen bevorzugen und auf einen vollständigen Angebotsvergleich verzichten.',
          'Nur Preis und Liefertermin vergleichen; weitere Bedingungen zunächst nicht berücksichtigen.',
          'Die Bestellung auslösen und die Freigabe anschließend dokumentieren.',
          'Das zuerst eingegangene passende Angebot verwenden, sofern der Preis im Budget liegt.'
        ],
        'zahlung': [
          'Den Zahlungsvorgang zunächst auslösen und offene Abweichungen anschließend klären.',
          'Nur den Endbetrag prüfen und die zugrunde liegenden Zahlungsbedingungen vorerst übernehmen.',
          'Die Buchung vornehmen und eine mögliche Korrektur bei der nächsten Abstimmung berücksichtigen.',
          'Die Fälligkeit aus dem System übernehmen, ohne sie mit dem Beleg abzugleichen.',
          'Die finanzielle Korrektur getrennt vom ursprünglichen Vorgang behandeln.'
        ],
        'prozess': [
          'Den nächsten Arbeitsschritt beginnen und die offene Klärung parallel weiterführen.',
          'Die Abweichung nur mündlich weitergeben und auf eine zusätzliche Dokumentation verzichten.',
          'Die schnellste Lösung wählen und die Ursache erst bei erneutem Auftreten untersuchen.',
          'Den Ablauf unverändert fortsetzen und nur den aktuellen Einzelfall korrigieren.',
          'Die Zuständigkeit später klären, solange der Vorgang zunächst weiterbearbeitet werden kann.'
        ],
        'ablauf': [
          'Den nächsten Prozessschritt bereits auslösen und die vorherige Prüfung anschließend nachholen.',
          'Nur die zeitlich schnellste Möglichkeit wählen und die vorgesehenen Freigaben später ergänzen.',
          'Den Vorgang zunächst weitergeben und erst bei Rückfragen prüfen, ob noch Unterlagen fehlen.',
          'Die Bearbeitung nach Eingangsreihenfolge fortsetzen, auch wenn noch eine Prüfung offen ist.',
          'Die Aufgabe abschließen und die Dokumentation gesammelt am Tagesende ergänzen.'
        ]
      },
      'Fortgeschritten': {
        'beleg': [
          'Die Belege weitgehend abgleichen, die offene Abweichung aber erst nach der Freigabe klären.',
          'Die sachliche Prüfung durchführen und bei plausibler Gesamtsumme auf den Abgleich einzelner Positionen verzichten.',
          'Die Abweichung dokumentieren und den Vorgang freigeben, solange der finanzielle Unterschied gering erscheint.',
          'Zuerst die zuständige Stelle informieren und die vollständige Belegprüfung erst nach deren Rückmeldung durchführen.',
          'Nur die zuletzt geänderte Unterlage als maßgeblich ansehen, ohne den Änderungsverlauf zu prüfen.'
        ],
        'lieferung': [
          'Mengenabweichungen sofort reklamieren und die Qualitätsprüfung der tatsächlich gelieferten Ware anschließend durchführen.',
          'Den Wareneingang mit Vorbehalt buchen und die zugrunde liegenden Bestellangaben später vollständig abgleichen.',
          'Die wirtschaftlich größte Abweichung zuerst klären und kleinere Abweichungen zunächst unberücksichtigt lassen.',
          'Den Lieferanten direkt um Korrektur bitten, bevor intern eindeutig geklärt ist, welche Abweichung vorliegt.',
          'Die Lieferung dokumentieren und weiterverwenden, solange die Funktionsfähigkeit überwiegend gegeben ist.'
        ],
        'angebot': [
          'Preis, Lieferzeit und Zahlungsziel vergleichen, qualitative Unterschiede aber erst nach Auftragserteilung bewerten.',
          'Das wirtschaftlich günstigste Angebot wählen, auch wenn eine erforderliche interne Freigabe noch aussteht.',
          'Den bisherigen Lieferanten bevorzugen, sofern sein Angebot nur geringfügig teurer ist, ohne weitere Kriterien zu gewichten.',
          'Die Angebote vollständig vergleichen, aber Nebenkosten erst bei Rechnungseingang berücksichtigen.',
          'Zunächst bestellen und die Dokumentation des Angebotsvergleichs anschließend vervollständigen.'
        ],
        'zahlung': [
          'Die Zahlung fristgerecht auslösen und kleinere Unstimmigkeiten parallel mit dem Lieferanten klären.',
          'Die im System gespeicherten Zahlungsbedingungen verwenden, sofern der Rechnungsbetrag plausibel erscheint.',
          'Eine erwartete Gutschrift bereits vor ihrem Eingang mit der nächsten Zahlung verrechnen.',
          'Den ursprünglichen Vorgang abschließen und die finanzielle Korrektur als separaten neuen Vorgang behandeln.',
          'Bei einer unklaren Fälligkeit zunächst den üblichen Zahlungsrhythmus des Lieferanten zugrunde legen.'
        ],
        'prozess': [
          'Die wahrscheinlichste Ursache korrigieren und erst danach prüfen, ob weitere Schnittstellen betroffen sind.',
          'Die Bearbeitung beschleunigen, indem eine Kontrollstufe vorübergehend ausgelassen und später dokumentiert wird.',
          'Die Zuständigkeit beibehalten und zusätzliche Beteiligte erst bei erneutem Auftreten der Abweichung einbinden.',
          'Den Einzelfall vollständig korrigieren, ohne den zugrunde liegenden Ablauf auf Wiederholungsrisiken zu prüfen.',
          'Eine praktikable Zwischenlösung dauerhaft übernehmen, sobald sie im ersten Fall funktioniert.'
        ],
        'ablauf': [
          'Den zeitkritischsten Schritt sofort auslösen und die erforderliche Freigabe parallel nachholen.',
          'Den Vorgang vollständig vorbereiten und offene Zuständigkeiten erst unmittelbar vor Abschluss klären.',
          'Die Bearbeitung nach wirtschaftlicher Bedeutung priorisieren, auch wenn eine frühere verbindliche Frist besteht.',
          'Eine sinnvolle Standardlösung anwenden und nur bei einer späteren Abweichung erneut prüfen.',
          'Den nächsten Schritt veranlassen, sobald die wesentlichen Informationen vorliegen, auch wenn einzelne Prüfungen noch offen sind.'
        ]
      },
      'Experte': {
        'beleg': [
          'Die Abweichung vollständig dokumentieren und den Vorgang unter Vorbehalt freigeben, solange keine unmittelbare finanzielle Mehrbelastung erkennbar ist.',
          'Die aktuellste Belegfassung als führend behandeln und widersprechende Vorversionen nur bei einer späteren Beanstandung rekonstruieren.',
          'Die sachliche und rechnerische Prüfung abschließen, die Klärung der Zuständigkeit für die Abweichung aber nachgelagert behandeln.',
          'Die Freigabe zurückstellen, jedoch bereits nachgelagerte interne Schritte vorbereiten, damit keine Zeit verloren geht.',
          'Die dokumentierte Abweichung akzeptieren, wenn sie innerhalb einer üblichen Toleranz liegt, ohne die konkrete Vereinbarung erneut zu prüfen.'
        ],
        'lieferung': [
          'Die zeitkritische Ersatzbeschaffung unmittelbar einleiten und die formale Reklamation parallel nachziehen.',
          'Die Lieferung mit dokumentiertem Vorbehalt übernehmen und die kaufmännische Klärung erst nach interner Verwendung abschließen.',
          'Zuerst die Auswirkungen auf nachgelagerte Termine absichern und die genaue Mengen- und Qualitätsabgrenzung anschließend vervollständigen.',
          'Den Lieferanten mit der wahrscheinlichsten Abweichung konfrontieren und die interne Beleglage erst bei Widerspruch vertiefen.',
          'Die wirtschaftlich bedeutendste Abweichung vollständig bearbeiten und geringere Abweichungen in einem späteren Sammelvorgang klären.'
        ],
        'angebot': [
          'Das Angebot mit dem niedrigsten Gesamtkostenwert auswählen und qualitative Risiken als nachgelagerten Steuerungspunkt behandeln.',
          'Den bestehenden Lieferanten trotz leicht ungünstigerer Konditionen bevorzugen, um Prozesskosten eines Wechsels grundsätzlich zu vermeiden.',
          'Die fachlich beste Variante vorläufig auswählen und die formale Freigabe erst nach Abschluss der Detailverhandlung einholen.',
          'Preis, Termin und Folgekosten gewichten, aber vertragliche Nebenbedingungen nur bei annähernd gleichen Angeboten berücksichtigen.',
          'Die wirtschaftliche Entscheidung treffen und die Dokumentation des Auswahlprozesses erst unmittelbar vor Bestellung vervollständigen.'
        ],
        'zahlung': [
          'Die Zahlung zum sicheren Fristerhalt auslösen und die noch offene Korrektur anschließend über eine Gutschrift bereinigen.',
          'Eine angekündigte Gutschrift bereits in die Zahlung einrechnen, sofern der Lieferant sie schriftlich bestätigt hat.',
          'Die im System hinterlegte Fälligkeit verwenden und nur bei deutlicher Abweichung vom Vertrag eine manuelle Prüfung vornehmen.',
          'Den finanziellen Vorgang abschließen und strittige Nebenpositionen separat nachverfolgen, damit der Hauptbetrag nicht offen bleibt.',
          'Bei geringfügiger Differenz die wirtschaftlich günstigere Variante buchen und eine spätere Abstimmung dokumentieren.'
        ],
        'prozess': [
          'Die messbar schnellste Prozessvariante übernehmen und Qualitätsabweichungen zunächst über zusätzliche Nachkontrollen auffangen.',
          'Die erkannte Hauptursache beheben und angrenzende Schnittstellen erst nach einer erneuten Auffälligkeit in die Analyse einbeziehen.',
          'Eine wirksame Zwischenlösung standardisieren, bevor die vollständige Ursachenanalyse abgeschlossen ist, um kurzfristig Stabilität zu gewinnen.',
          'Die Verantwortung zentral bündeln und dezentrale Prüfschritte reduzieren, auch wenn dadurch eine zusätzliche Abhängigkeit entsteht.',
          'Den Prozess anhand der wichtigsten Kennzahl optimieren und gegenläufige Nebenkennzahlen erst in einer zweiten Phase bewerten.'
        ],
        'ablauf': [
          'Die Außenwirkung zuerst absichern und interne Kontroll- oder Freigabeschritte anschließend vollständig nachziehen.',
          'Die wirtschaftlich bedeutendste Option umsetzen, sofern keine unmittelbar erkennbare Pflichtverletzung entsteht.',
          'Die wahrscheinlich beste Lösung vorbereiten und die zuständige Entscheidung erst kurz vor der verbindlichen Umsetzung einholen.',
          'Die Bearbeitung entlang der knappsten Ressource priorisieren, auch wenn dadurch eine frühere, aber weniger folgenreiche Frist zurücksteht.',
          'Den Vorgang zur Zeitersparnis in Teilentscheidungen zerlegen und offene Abhängigkeiten erst bei der Schlussfreigabe zusammenführen.'
        ]
      }
    }
    bank=banks[level][group]
    # drei verschiedene, deterministisch rotierte Antwortalternativen
    start=int(hashlib.sha256(q.id.encode()).hexdigest()[:8],16)%len(bank)
    return [bank[(start+k)%len(bank)] for k in range(3)]


def _bo_group(topic: str):
    t=topic.casefold()
    if any(x in t for x in ['datenschutz','sicherheit']): return 'security'
    if any(x in t for x in ['dokument','ablage']): return 'document'
    if any(x in t for x in ['termin','besprechung']): return 'meeting'
    if any(x in t for x in ['kommunikation','eskalation']): return 'communication'
    if any(x in t for x in ['prozess']): return 'process'
    return 'priority'


def _bo_wrong(q):
    group=_bo_group(q.topic); level=q.level
    banks={
      'Anfänger': {
        'security':['Die Information zunächst weiterverwenden und den Schutz erst bei längerer Abwesenheit erhöhen.','Eine teilweise Schutzmaßnahme wählen, zum Beispiel nur das sichtbare Fenster schließen.','Den Vorgang nur mündlich ansprechen und auf den vorgesehenen Sicherheitsweg verzichten.','Die Daten im normalen Arbeitsablauf belassen, solange kein konkreter Missbrauch erkennbar ist.'],
        'document':['Die Unterlage schnell auffindbar lokal speichern und die zentrale Ablage später nachholen.','Die aktuelle Fassung zusätzlich unter einem zweiten Namen speichern, ohne die alte Version zu kennzeichnen.','Nur den Dateinamen ändern und auf eine eindeutige Ablagestruktur verzichten.','Die Unterlage zunächst per E-Mail an sich selbst senden und später einsortieren.'],
        'meeting':['Den Termin zuerst einstellen und fehlende Angaben anschließend ergänzen.','Nur Zeit und Teilnehmer festhalten; Anlass und benötigte Unterlagen später klären.','Den Termin nach Wunsch der meisten Beteiligten setzen, ohne Raum oder Abhängigkeiten vorher zu prüfen.','Die Einladung versenden und die Agenda erst kurz vor Beginn festlegen.'],
        'communication':['Die wichtigsten Stichpunkte notieren und fehlende Kontaktdaten bei Bedarf später erfragen.','Die Nachricht direkt weiterleiten, ohne Zuständigkeit oder nächsten Schritt festzuhalten.','Nur den Namen und das Anliegen notieren und auf eine Rückrufmöglichkeit verzichten.','Den Vorgang mündlich weitergeben und keine zusätzliche Notiz anlegen.'],
        'process':['Die schnellste Lösung übernehmen und den Ablauf erst bei erneutem Problem genauer betrachten.','Eine zusätzliche Kontrollliste anlegen, ohne zuerst die Ursache des Problems zu prüfen.','Den bisherigen Ablauf beibehalten und nur den aktuellen Einzelfall korrigieren.','Die Aufgabe an eine andere Stelle weitergeben, ohne den Prozess selbst zu betrachten.'],
        'priority':['Zuerst die Aufgabe erledigen, die am schnellsten abgeschlossen werden kann.','Beide Aufgaben gleichzeitig beginnen, damit keine sichtbar liegen bleibt.','Nach Eingangsreihenfolge arbeiten, auch wenn eine Aufgabe eine nähere Frist hat.','Zuerst die angenehmere Routineaufgabe abschließen und die Fristsache anschließend bearbeiten.']
      },
      'Fortgeschritten': {
        'security':['Den Zugriff kurzfristig zulassen und die Berechtigung anschließend dokumentieren.','Die Daten schützen, aber die vorgesehene Meldung erst bei einem tatsächlichen Schaden auslösen.','Den Vorfall intern dokumentieren und zunächst abwarten, ob eine externe Reaktion erfolgt.','Eine technische Sofortmaßnahme umsetzen, ohne Zuständigkeit und weitere Meldewege zu klären.'],
        'document':['Die neueste Datei als gültig behandeln und den Versionskonflikt erst bei einer späteren Rückfrage aufarbeiten.','Die Unterlagen vollständig ablegen, aber uneinheitliche Dateinamen zunächst bestehen lassen.','Die aktuelle Fassung kennzeichnen, ohne zu prüfen, ob ältere Kopien weiterhin im Umlauf sind.','Den gemeinsamen Ordner bereinigen und die Nachvollziehbarkeit älterer Versionen dabei nicht weiter berücksichtigen.'],
        'meeting':['Den Termin nach der wichtigsten Person ausrichten und übrige Abhängigkeiten anschließend anpassen.','Die Agenda vollständig vorbereiten, aber Entscheidungskompetenzen erst in der Besprechung klären.','Den Raum und die Teilnehmer sichern, benötigte Unterlagen jedoch erst unmittelbar vor dem Termin verteilen.','Bei einer Überschneidung den internen Termin verschieben, ohne Auswirkungen auf abhängige Aufgaben zu prüfen.'],
        'communication':['Zunächst alle Beteiligten informieren und Zuständigkeit sowie Entscheidungsbedarf danach eingrenzen.','Die wichtigsten Auswirkungen nennen, aber auf eine konkrete Frist oder gewünschte Entscheidung verzichten.','Den Vorgang direkt eskalieren, obwohl die operative Klärung noch nicht vollständig versucht wurde.','Die Zuständigkeit klären, aber die bisherige Dokumentation erst nach der Entscheidung ergänzen.'],
        'process':['Eine naheliegende Ursache korrigieren und die Wirkung erst nach vollständiger Einführung messen.','Den Ablauf beschleunigen, indem eine Kontrollstufe vorübergehend reduziert und später bewertet wird.','Die Mitarbeitenden zusätzlich schulen, ohne Prozess und Schnittstellen auf strukturelle Ursachen zu prüfen.','Eine funktionierende Zwischenlösung als Standard übernehmen, bevor klare Erfolgskriterien definiert sind.'],
        'priority':['Die knappste Frist zuerst bearbeiten, ohne Abhängigkeiten und mögliche Folgewirkungen zu vergleichen.','Die Aufgabe mit der größten Außenwirkung zuerst wählen, auch wenn eine verbindliche interne Frist früher endet.','Beide zeitkritischen Aufgaben parallel beginnen, ohne Verantwortlichkeiten eindeutig aufzuteilen.','Die wirtschaftlich wichtigste Aufgabe priorisieren und die übrigen Fristen anschließend neu abstimmen.']
      },
      'Experte': {
        'security':['Den unmittelbaren Schaden begrenzen und die formale Meldung erst nach vollständiger Sachverhaltsaufklärung auslösen.','Die betroffene Berechtigung sofort entziehen, ohne vorher zu klären, ob dadurch ein kritischer Prozess unterbrochen wird.','Den Vorfall vollständig dokumentieren und erst danach technische Eindämmungsmaßnahmen einleiten.','Die wahrscheinlich betroffenen Daten sperren und weitere Beteiligte nur bei bestätigtem Missbrauch informieren.'],
        'document':['Die aktuellste Fassung als Arbeitsgrundlage verwenden und die formale Freigabe parallel rekonstruieren.','Widersprüchliche Versionen zusammenführen und offene Unterschiede anschließend dokumentieren.','Die Bearbeitung fortsetzen, sofern die abweichenden Stellen nach eigener Einschätzung nicht entscheidungsrelevant sind.','Eine der formal freigegebenen Fassungen wählen und die Entstehung des Konflikts erst nach Abschluss des Vorgangs analysieren.'],
        'meeting':['Die entscheidungsbefugten Personen priorisieren und Informationsbedarfe anderer Beteiligter nachgelagert bedienen.','Die Sitzung durchführen und unklare Rollen als ersten Tagesordnungspunkt spontan festlegen.','Alle relevanten Unterlagen breit verteilen, um Informationsasymmetrien vollständig zu vermeiden.','Den Termin trotz offener Entscheidungsgrundlage halten und fehlende Informationen als Nachtrag beschließen.'],
        'communication':['Die Entscheidungsvorlage möglichst vollständig eskalieren, auch wenn einzelne Auswirkungen noch nicht belastbar quantifiziert sind.','Zunächst eine bevorzugte Lösung empfehlen und alternative Optionen nur auf Nachfrage erläutern.','Die operative Bearbeitung fortsetzen und die Eskalation erst auslösen, wenn eine Frist tatsächlich gefährdet ist.','Alle Beteiligten gleichzeitig informieren, um maximale Transparenz zu schaffen, auch wenn noch keine abgestimmte Botschaft vorliegt.'],
        'process':['Die wichtigste Kennzahl optimieren und negative Nebeneffekte über zusätzliche Kontrollen kompensieren.','Eine wirksame Sofortmaßnahme dauerhaft standardisieren, bevor die vollständige Ursachenanalyse beendet ist.','Den Prozess vereinfachen, indem Entscheidungskompetenzen zentralisiert und lokale Prüfungen reduziert werden.','Die erkannte Engstelle beseitigen und angrenzende Schnittstellen erst nach erneuter Messung einbeziehen.'],
        'priority':['Die rechtlich bindende Frist immer zuerst bearbeiten, auch wenn eine andere Aufgabe unmittelbar höheren Gesamtschaden verursacht.','Die Aufgabe mit der höchsten Außenwirkung priorisieren und interne Kontrollanforderungen anschließend vollständig nachziehen.','Die wirtschaftlich größte Auswirkung priorisieren und eine frühere, aber beherrschbare Frist aktiv neu verhandeln.','Die verfügbaren Ressourcen gleichmäßig auf alle kritischen Aufgaben verteilen, um keine Aufgabe vollständig zurückzustellen.']
      }
    }
    bank=banks[level][group]
    start=int(hashlib.sha256((q.id+'bo').encode()).hexdigest()[:8],16)%len(bank)
    return [bank[(start+k)%len(bank)] for k in range(3)]


def _date_from(text: str) -> str:
    m=re.search(r'\b(\d{1,2}\.\s+[A-ZÄÖÜ][a-zäöü]+)\b', text)
    return m.group(1) if m else 'dem genannten Termin'


def _sv_wrong(q):
    date=_date_from(q.correct+' '+q.prompt)
    lvl=q.level
    topic=q.topic.casefold()

    # Fachlich passende Alternativen je Schreibanlass. Die Stufe steuert,
    # wie nah die Distraktoren an einer guten Geschäftskorrespondenz liegen.
    if 'betreff' in topic:
        if lvl=='Anfänger':
            return [f'Rechnung vom {date}', f'Bitte um Rückmeldung zur Rechnung vom {date}', f'Frage zur Rechnung vom {date}']
        if lvl=='Fortgeschritten':
            return [f'Rechnung vom {date} – Klärungsbedarf', f'Bitte um Prüfung der Rechnung vom {date}', f'Abweichung bei der Rechnung vom {date}']
        return [f'Prüfung der Rechnung vom {date} – Rückmeldung erbeten', f'Abweichung zur Rechnung vom {date} – weitere Klärung', f'Rechnung vom {date} – Bitte um fachliche Rückmeldung']

    if 'anfrage' in topic:
        if lvl=='Anfänger':
            return [f'Bitte senden Sie uns bis {date} Ihre aktuellen Preise und Lieferzeiten.', f'Bitte senden Sie uns ein Angebot mit Preis bis {date}.', f'Bitte teilen Sie uns bis {date} mit, wann die Ware lieferbar ist.']
        if lvl=='Fortgeschritten':
            return [f'Bitte senden Sie uns bis {date} ein Angebot mit Preis und Lieferzeit; die Zahlungsbedingungen können wir anschließend abstimmen.', f'Bitte senden Sie uns ein Angebot mit Preis und Zahlungsbedingungen bis {date}; den Liefertermin klären wir bei Auftragserteilung.', f'Bitte übermitteln Sie uns Ihre Konditionen und Lieferzeit bis {date}; ein formelles Angebot ist zunächst nicht erforderlich.']
        return [f'Bitte senden Sie uns bis {date} ein verbindliches Preisangebot; Lieferzeit und Zahlungsbedingungen würden wir bei positiver Prüfung gesondert abstimmen.', f'Bitte übermitteln Sie uns bis {date} Ihre aktuellen Konditionen einschließlich Lieferzeit; eine formelle Angebotsfrist ist nicht erforderlich.', f'Bitte senden Sie uns ein Angebot mit Preis und Lieferzeit. Die Zahlungsbedingungen können nach Auswahl des Lieferanten verhandelt werden.']

    if 'reklamation' in topic:
        if lvl=='Anfänger':
            return [f'Bei der Lieferung fehlen zwei Positionen. Bitte prüfen Sie das bis {date}.', f'Wir haben eine Abweichung festgestellt und bitten um Rückmeldung bis {date}.', f'Bitte teilen Sie uns bis {date} mit, wie Sie mit der fehlenden Ware verfahren möchten.']
        if lvl=='Fortgeschritten':
            return [f'Bei der Prüfung der Lieferung fehlen zwei Positionen. Bitte teilen Sie uns bis {date} mit, ob eine Nachlieferung möglich ist.', f'Wir haben zwei fehlende Positionen festgestellt und bitten bis {date} um Klärung; einen konkreten Liefertermin können wir anschließend abstimmen.', f'Bitte prüfen Sie die Abweichung und bestätigen Sie uns bis {date}, wie der Vorgang weiterbearbeitet wird.']
        return [f'Bei der Prüfung der Lieferung fehlen zwei bestätigte Positionen. Bitte bestätigen Sie uns bis {date}, dass eine Nachlieferung veranlasst wird; den Termin können wir anschließend abstimmen.', f'Wir haben zwei fehlende Positionen festgestellt und bitten bis {date} um Ihre Stellungnahme. Bis dahin setzen wir die weitere Bearbeitung aus.', f'Bitte prüfen Sie die fehlenden Positionen bis {date}. Wir gehen davon aus, dass die Nachlieferung kurzfristig erfolgen kann.']

    if 'frist' in topic:
        if lvl=='Anfänger':
            return [f'Bitte melden Sie sich möglichst bald, am besten bis {date}.', f'Wir würden uns über eine zeitnahe Rückmeldung freuen.', f'Bitte antworten Sie in den nächsten Tagen.']
        if lvl=='Fortgeschritten':
            return [f'Bitte senden Sie uns Ihre Rückmeldung möglichst bis {date}.', f'Wir bitten um zeitnahe Rückmeldung; {date} wäre für uns hilfreich.', f'Bitte teilen Sie uns Ihren Stand bis etwa {date} mit.']
        return [f'Bitte senden Sie uns Ihre Rückmeldung nach Möglichkeit bis {date}; bei Verzögerungen informieren Sie uns kurz.', f'Wir bitten um Ihre Rückmeldung bis {date}, sofern die interne Prüfung bis dahin abgeschlossen werden kann.', f'Bitte teilen Sie uns bis {date} den aktuellen Stand mit; die endgültige Rückmeldung kann gegebenenfalls später folgen.']

    if 'zahlungserinnerung' in topic:
        if lvl=='Anfänger':
            return [f'Zu unserer Rechnung vom {date} ist noch kein Zahlungseingang erkennbar. Bitte überweisen Sie den Betrag kurzfristig.', f'Bitte prüfen Sie die offene Rechnung vom {date} und veranlassen Sie die Zahlung.', f'Unsere Rechnung vom {date} ist noch offen. Wir bitten um Rückmeldung.']
        if lvl=='Fortgeschritten':
            return [f'Zu unserer Rechnung vom {date} konnten wir noch keinen Zahlungseingang feststellen. Bitte veranlassen Sie die Zahlung kurzfristig.', f'Unsere Rechnung vom {date} ist nach unserem Stand noch offen. Bitte prüfen Sie, ob die Zahlung bereits angewiesen wurde.', f'Bitte prüfen Sie den offenen Betrag aus unserer Rechnung vom {date} und teilen Sie uns den Zahlungsstatus mit.']
        return [f'Zu unserer Rechnung vom {date} ist nach aktuellem Stand noch kein Zahlungseingang verbucht. Wir bitten um kurzfristige Zahlung und Rückmeldung.', f'Unsere Rechnung vom {date} erscheint in unserem System noch offen. Bitte bestätigen Sie uns, wann die Zahlung veranlasst wurde.', f'Bitte prüfen Sie die Rechnung vom {date}. Sollte die Zahlung noch nicht erfolgt sein, bitten wir um zeitnahe Überweisung.']

    if 'sensible' in topic:
        if lvl=='Anfänger':
            return [f'Wir gehen davon aus, dass die Lieferung bis {date} eintrifft.', f'Nach aktuellem Stand sollte die Lieferung bis {date} eintreffen.', f'Die Lieferung wird voraussichtlich bis {date} eintreffen.']
        if lvl=='Fortgeschritten':
            return [f'Nach aktuellem Stand rechnen wir mit einer Lieferung bis {date}; eine abschließende Bestätigung steht noch aus.', f'Wir erwarten die Lieferung bis {date} und melden uns, falls sich daran etwas ändert.', f'Der aktuelle Stand spricht für eine Lieferung bis {date}; wir betrachten den Termin zunächst als wahrscheinlich.']
        return [f'Nach heutigem Kenntnisstand ist eine Lieferung bis {date} wahrscheinlich; wir planen vorläufig mit diesem Termin.', f'Wir rechnen derzeit mit der Lieferung bis {date}. Sofern keine gegenteilige Nachricht eingeht, gehen wir von diesem Termin aus.', f'Die Lieferung soll nach aktueller Planung bis {date} erfolgen; wir bestätigen den Termin hiermit vorbehaltlich weiterer Änderungen.']

    if 'anrede' in topic or 'abschluss' in topic:
        if lvl=='Anfänger':
            return [f'Vielen Dank für Ihre Prüfung. Wir freuen uns über eine Rückmeldung.', f'Bitte melden Sie sich bis {date}. Vielen Dank.', f'Vielen Dank. Für Rückfragen stehen wir gern zur Verfügung.']
        if lvl=='Fortgeschritten':
            return [f'Vielen Dank für Ihre Prüfung. Eine Rückmeldung bis {date} wäre hilfreich.', f'Wir danken Ihnen für die Bearbeitung und bitten um eine zeitnahe Rückmeldung.', f'Vielen Dank für Ihre Unterstützung. Bitte informieren Sie uns bis {date} über den aktuellen Stand.']
        return [f'Vielen Dank für Ihre Prüfung. Bitte informieren Sie uns bis {date} über den aktuellen Stand; die abschließende Entscheidung kann anschließend erfolgen.', f'Wir danken Ihnen für die Bearbeitung und bitten um Rückmeldung bis {date}, sofern Ihre interne Prüfung bis dahin abgeschlossen ist.', f'Vielen Dank für Ihre Unterstützung. Wir bitten um eine kurze Zwischenmeldung bis {date}.']

    if 'aufbau' in topic:
        if lvl=='Anfänger':
            return [f'Bezug nennen → gewünschte Korrektur formulieren → Abweichung beschreiben → Rückmeldung bis {date} erbitten', f'Abweichung beschreiben → Bezug nennen → Rückmeldung bis {date} erbitten → gewünschte Korrektur offenlassen', f'Bezug nennen → Abweichung beschreiben → Rückmeldung bis {date} erbitten → gewünschte Korrektur erst später klären']
        if lvl=='Fortgeschritten':
            return [f'Bezug nennen → Abweichung beschreiben → mögliche Ursache vermuten → Rückmeldung bis {date} erbitten → Korrektur danach festlegen', f'Abweichung beschreiben → gewünschte Korrektur nennen → Bezug ergänzen → Rückmeldung bis {date} erbitten', f'Bezug nennen → gewünschte Korrektur nennen → Abweichung knapp begründen → Rückmeldung bis {date} erbitten']
        return [f'Bezug nennen → Abweichung bewerten → bevorzugte Lösung vorgeben → Rückmeldung bis {date} erbitten → Nachweise bei Bedarf ergänzen', f'Bezug nennen → Abweichung beschreiben → mögliche Rechtsfolge nennen → gewünschte Korrektur offenlassen → Rückmeldung bis {date} erbitten', f'Abweichung beschreiben → Belege nennen → gewünschte Korrektur formulieren → Bezug am Ende ergänzen → Rückmeldung bis {date} erbitten']

    if 'professioneller ton' in topic:
        if lvl=='Anfänger':
            return [f'Nach unserer Prüfung können wir die Forderung derzeit nicht bestätigen. Bitte senden Sie uns bis {date} weitere Unterlagen.', f'Wir können Ihrer Forderung aktuell nicht entsprechen und bitten bis {date} um ergänzende Nachweise.', f'Nach aktuellem Stand sehen wir keinen ausreichenden Grund für die Forderung. Sie können bis {date} weitere Informationen senden.']
        if lvl=='Fortgeschritten':
            return [f'Nach Prüfung der Unterlagen können wir die Forderung derzeit nicht bestätigen. Ergänzende Nachweise prüfen wir gern bis {date}.', f'Die vorliegenden Unterlagen reichen für eine Anerkennung derzeit nicht aus. Bitte reichen Sie bis {date} weitere Nachweise ein.', f'Wir sehen die Forderung nach aktueller Prüfung als nicht ausreichend belegt an. Eine erneute Prüfung ist nach Eingang weiterer Unterlagen möglich.']
        return [f'Nach Prüfung der vorliegenden Unterlagen sehen wir derzeit keine ausreichende Grundlage für eine Anerkennung. Ergänzende Nachweise können bis {date} eingereicht werden.', f'Die Forderung ist nach aktuellem Sachstand nicht hinreichend belegt. Wir prüfen den Vorgang erneut, sofern bis {date} weitere Unterlagen vorliegen.', f'Nach derzeitiger Prüfung ist eine Anerkennung nicht vorgesehen. Ergänzende Unterlagen bis {date} können in die abschließende Bewertung einbezogen werden.']

    if 'e-mail' in topic:
        if lvl=='Anfänger':
            return [f'Der Vorgang wird noch geprüft. Wir melden uns wieder.', f'Wir bearbeiten den Vorgang und geben Ihnen bis {date} Bescheid.', f'Der Vorgang ist noch offen; bitte haben Sie noch etwas Geduld.']
        if lvl=='Fortgeschritten':
            return [f'Der Vorgang befindet sich noch in Prüfung. Wir melden uns bis {date} mit einem aktuellen Stand.', f'Die Bearbeitung läuft. Eine abschließende Rückmeldung ist für {date} vorgesehen.', f'Wir prüfen den Vorgang weiter und informieren Sie bis {date} über das weitere Vorgehen.']
        return [f'Der Vorgang befindet sich in Prüfung. Wir rechnen damit, die Bearbeitung bis {date} abschließen zu können.', f'Die Bearbeitung ist eingeleitet. Sofern keine neuen Punkte auftreten, erhalten Sie bis {date} eine abschließende Rückmeldung.', f'Der Vorgang wird derzeit geprüft. Wir informieren Sie bis {date}; bis dahin gehen wir von keiner weiteren Aktion Ihrerseits aus.']

    # Klare Formulierung und sonstige Themen
    if lvl=='Anfänger':
        return [f'Bitte senden Sie uns die noch fehlenden Unterlagen möglichst bis {date}.', f'Bitte reichen Sie die fehlenden Unterlagen nach und geben Sie uns bis {date} kurz Bescheid.', f'Wir benötigen noch Unterlagen. Bitte senden Sie diese bis {date}.']
    if lvl=='Fortgeschritten':
        return [f'Bitte senden Sie uns die noch offenen Unterlagen bis {date}; fehlende Einzelheiten können anschließend geklärt werden.', f'Bitte reichen Sie die benötigten Unterlagen bis {date} ein. Welche Dokumente im Einzelnen fehlen, teilen wir Ihnen auf Wunsch mit.', f'Wir bitten um Übersendung der ausstehenden Unterlagen bis {date}; den weiteren Bearbeitungsschritt stimmen wir danach ab.']
    return [f'Bitte reichen Sie die noch offenen Unterlagen bis {date} ein. Sofern einzelne Nachweise nicht verfügbar sind, teilen Sie uns dies bitte gesondert mit.', f'Wir bitten um die ausstehenden Unterlagen bis {date}. Nach Eingang prüfen wir, ob weitere Nachweise erforderlich sind.', f'Bitte senden Sie uns die noch fehlenden Unterlagen bis {date}; bis zur Vollständigkeit bleibt die weitere Bearbeitung zunächst zurückgestellt.']


def improve_distractors(pool, Question):
    out=[]
    for q in pool:
        if q.kind!='choice' or q.category=='Deutsch & Rechtschreibung':
            out.append(q); continue
        if q.category=='Geschäftsprozesse': wrong=_gp_wrong(q)
        elif q.category=='Büroorganisation': wrong=_bo_wrong(q)
        elif q.category=='Schriftverkehr': wrong=_sv_wrong(q)
        else:
            out.append(q); continue
        wrong=_uniq(wrong,q.correct)
        if len(wrong)<3:
            # Fallback auf vorhandene Alternativen, falls eine generierte Formulierung kollidiert.
            wrong=_uniq(wrong+[x for x in (q.options or []) if x!=q.correct],q.correct)

        prompt = q.prompt
        # Die Stufen sollen nicht nur durch andere Antwortalternativen schwerer werden.
        # Fortgeschritten und Experte erhalten zusätzliche Entscheidungskriterien.
        if q.category == "Geschäftsprozesse":
            if q.level == "Fortgeschritten":
                prompt += " Berücksichtige bei deiner Entscheidung auch die erforderliche Freigabe und mögliche Auswirkungen auf den nächsten Prozessschritt."
            elif q.level == "Experte":
                prompt += " Entscheidend sind dabei neben dem unmittelbaren Schritt auch Zuständigkeit, Freigabe und mögliche Folgen für nachgelagerte Vorgänge."
        elif q.category == "Schriftverkehr":
            if q.level == "Fortgeschritten":
                prompt += " Die Formulierung soll zugleich konkret, höflich und handlungsorientiert sein."
            elif q.level == "Experte":
                prompt += " Gesucht ist die professionellste Formulierung, die klar bleibt und keine ungesicherte Zusage enthält."

        out.append(Question(q.id,q.category,q.topic,q.level,prompt,q.kind,q.correct,q.explanation,[q.correct,*wrong[:3]],q.hint,q.tolerance))
    return out
