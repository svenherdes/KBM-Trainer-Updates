from __future__ import annotations

"""Datenschutz & IT-Sicherheit – 600 aktive Aufgaben.

Quellenstand: 21.09.2026
Fachliche Primärquellen:
- DSGVO, konsolidierter deutscher Text, EUR-Lex: Art. 4, 5, 6, 7, 9, 12–21,
  25, 26, 28, 32–35, 37–39, 44 ff.
- BDSG: insbesondere § 26 (Beschäftigtendaten) und § 38 (Datenschutzbeauftragte).
- BfDI: Info 1 (DSGVO/BDSG), Info 6 (DSGVO in der Bundesverwaltung),
  Erläuterungen zu Betroffenenrechten und Auftragsverarbeitung.
- BSI: Basistipps zur IT-Sicherheit, sichere Passwörter, 2FA und Phishing-Schutz.

Die Aufgaben sind eigenständig formuliert. Es werden keine fremden Prüfungsfragen kopiert.
"""

from typing import Callable


SOURCE_STAND = "21.09.2026"
CATEGORY = "Datenschutz & IT-Sicherheit"


def _fmt(text: str, ctx: dict[str, str]) -> str:
    return text.format(**ctx)


def _add_family(out, choice, family: int, level_code: str, level: str, topic: str,
                contexts: list[dict[str, str]], prompt: str, correct: str,
                wrong_sets: list[list[str]], explanation: str, hint: str = ""):
    """Erzeugt 10 kontextuell unterschiedliche Varianten einer Aufgabenfamilie.

    Die Fehlantworten rotieren, damit nicht immer derselbe Antwortsatz erscheint.
    """
    for i, ctx in enumerate(contexts, 1):
        wrong = wrong_sets[(i - 1) % len(wrong_sets)]
        if "dept" in ctx:
            scope = f"Im Bereich {ctx['dept']}: "
        elif "company" in ctx:
            scope = f"Bei {ctx['company']}: "
        elif "org" in ctx:
            scope = f"Bei {ctx['org']}: "
        else:
            scope = ""
        out.append(choice(
            f"ds_{level_code}_f{family:02d}_v{i:02d}", CATEGORY, topic, level,
            scope + _fmt(prompt, ctx), _fmt(correct, ctx), [_fmt(x, ctx) for x in wrong],
            _fmt(explanation, ctx), _fmt(hint, ctx) if hint else ""
        ))


def _contexts_beginner():
    return [
        {"dept":"Einkauf", "doc":"Bestellung", "person":"Kundin", "system":"Warenwirtschaft", "service":"Lieferung"},
        {"dept":"Vertrieb", "doc":"Angebot", "person":"Kunde", "system":"CRM", "service":"Angebotserstellung"},
        {"dept":"Personal", "doc":"Bewerbung", "person":"Bewerberin", "system":"Bewerberportal", "service":"Bewerbungsverfahren"},
        {"dept":"Buchhaltung", "doc":"Rechnung", "person":"Lieferant", "system":"Buchhaltungssystem", "service":"Rechnungsbearbeitung"},
        {"dept":"Service", "doc":"Reklamation", "person":"Kunde", "system":"Ticketsystem", "service":"Reklamationsbearbeitung"},
        {"dept":"Logistik", "doc":"Lieferschein", "person":"Empfängerin", "system":"Versandsystem", "service":"Versand"},
        {"dept":"Sekretariat", "doc":"Terminliste", "person":"Besucher", "system":"Kalender", "service":"Terminorganisation"},
        {"dept":"Kundenservice", "doc":"Kundenakte", "person":"Kundin", "system":"Kundenportal", "service":"Kundenbetreuung"},
        {"dept":"Disposition", "doc":"Tourenplan", "person":"Fahrer", "system":"Dispositionssystem", "service":"Tourenplanung"},
        {"dept":"Empfang", "doc":"Besucherliste", "person":"Gast", "system":"Besuchersystem", "service":"Besucherverwaltung"},
    ]


def build_beginner(choice):
    out=[]
    c=_contexts_beginner()

    _add_family(out, choice, 1, "a", "Anfänger", "Personenbezogene Daten", c,
        "Im {dept} steht in einer Datei der Name einer {person} zusammen mit ihrer E-Mail-Adresse. Was sind diese Angaben?",
        "Personenbezogene Daten, weil sie sich auf eine identifizierbare natürliche Person beziehen.",
        [["Keine personenbezogenen Daten, weil eine E-Mail-Adresse öffentlich sein kann.","Nur technische Daten ohne Datenschutzbezug.","Erst dann personenbezogen, wenn zusätzlich die Steuer-ID gespeichert ist."],
         ["Nur der Name ist personenbezogen; die E-Mail-Adresse nie.","Nur interne Betriebsdaten.","Anonyme Daten, weil mehrere Personen E-Mails nutzen."],
         ["Nur dann personenbezogen, wenn die Person ausdrücklich zustimmt.","Reine Sachinformation ohne Personenbezug.","Erst ab drei gespeicherten Merkmalen personenbezogen."]],
        "Art. 4 Nr. 1 DSGVO erfasst Informationen, die sich auf eine identifizierte oder identifizierbare natürliche Person beziehen.",
        "Frage dich, ob die Angaben einer konkreten Person zugeordnet werden können.")

    _add_family(out, choice, 2, "a", "Anfänger", "Personenbezogene Daten", c,
        "Welche Information wäre im {dept} typischerweise am ehesten anonym, wenn wirklich keine Person mehr identifizierbar ist?",
        "Eine Statistik, dass im letzten Monat insgesamt 420 Vorgänge bearbeitet wurden, ohne Personenbezug.",
        [["Eine Liste mit Kundennummern, wenn die Zuordnungstabelle im Unternehmen vorhanden ist.","Eine Datei mit Initialen und Geburtsdatum.","Eine E-Mail-Adresse ohne ausgeschriebenen Namen."],
         ["Eine pseudonymisierte Personalnummer, deren Zuordnung intern möglich ist.","Eine IP-Adresse eines konkreten Nutzers.","Ein Aktenzeichen, das auf eine Personenakte verweist."],
         ["Ein gekürzter Name zusammen mit der vollständigen Anschrift.","Eine verschlüsselte Kundenliste, für die das Unternehmen den Schlüssel besitzt.","Eine Telefonnummer ohne Namensfeld."]],
        "Echte Anonymisierung bedeutet, dass die betroffene Person nicht mehr identifizierbar ist. Pseudonymisierte oder verschlüsselte Daten bleiben grundsätzlich personenbezogen.",
        "Pseudonymisiert ist nicht dasselbe wie anonym.")

    _add_family(out, choice, 3, "a", "Anfänger", "Besondere Kategorien personenbezogener Daten", c,
        "Welche Angabe gehört nach der DSGVO zu besonders geschützten Datenkategorien?",
        "Gesundheitsdaten einer Person.",
        [["Die normale Geschäftsadresse eines Unternehmens.","Die Artikelnummer eines Produkts.","Die Öffnungszeiten einer Filiale."],
         ["Die interne Nummer eines Besprechungsraums.","Der Preis eines Bürostuhls.","Die Lieferzeit eines Artikels."],
         ["Die Postleitzahl eines Lagerstandorts ohne Personenbezug.","Die Bestellmenge eines Produkts.","Die Bezeichnung einer Abteilung." ]],
        "Art. 9 DSGVO nennt unter anderem Gesundheitsdaten, genetische Daten, bestimmte biometrische Daten, politische Meinungen, Religion und Gewerkschaftszugehörigkeit als besondere Kategorien.",
        "Denke an Angaben, die für Grundrechte besonders sensibel sind.")

    _add_family(out, choice, 4, "a", "Anfänger", "Datenminimierung", c,
        "Für die {service} benötigt das Unternehmen Name und Lieferadresse. Eine private Religionsangabe wird dafür nicht gebraucht. Was entspricht der DSGVO?",
        "Nur die für den Zweck erforderlichen Daten erheben.",
        [["Vorsorglich möglichst viele Daten sammeln, falls sie später nützlich werden.","Alle verfügbaren Daten speichern, solange genug Speicherplatz vorhanden ist.","Zusatzdaten immer erheben und erst nach einigen Jahren prüfen, ob sie gebraucht werden."],
         ["Die Religionsangabe trotzdem verlangen, weil ein Formular vollständig sein muss.","Daten unabhängig vom Zweck sammeln und intern frei verwenden.","Nur freiwillig zusätzliche Daten erheben, ohne einen Zweck zu nennen."],
         ["Jede bekannte Information zur Person dauerhaft in derselben Akte speichern.","Nicht benötigte Daten erheben, wenn sie nicht sofort ausgewertet werden.","Zusatzdaten ohne Bezug zur {service} als Standardfeld verlangen." ]],
        "Art. 5 Abs. 1 lit. c DSGVO verlangt Datenminimierung: verarbeitet werden sollen nur Daten, die für den jeweiligen Zweck erforderlich sind.",
        "Braucht man diese Angabe wirklich für den konkreten Vorgang?")

    _add_family(out, choice, 5, "a", "Anfänger", "Zweckbindung", c,
        "Die Daten einer {person} wurden für die {service} erhoben. Welche Grundregel gilt für eine spätere andere Nutzung?",
        "Die Daten dürfen nicht einfach beliebig für einen völlig anderen Zweck verwendet werden; die neue Nutzung braucht eine passende datenschutzrechtliche Grundlage.",
        [["Einmal erhobene Daten dürfen intern für jeden beliebigen Zweck genutzt werden.","Nur die Dateiendung entscheidet, wofür Daten genutzt werden dürfen.","Nach der ersten Speicherung gibt es keine Zweckbindung mehr."],
         ["Jede andere Nutzung ist automatisch erlaubt, wenn sie günstiger ist.","Daten dürfen immer an andere Abteilungen weitergegeben werden, ohne den Zweck zu prüfen.","Der ursprüngliche Zweck spielt nach 30 Tagen keine Rolle mehr."],
         ["Eine neue Nutzung ist stets verboten, auch wenn eine Rechtsgrundlage besteht.","Der Zweck kann jederzeit mündlich geändert werden, ohne weitere Prüfung.","Nur externe Weitergaben müssen einen Zweck haben; interne Nutzungen nicht." ]],
        "Art. 5 Abs. 1 lit. b DSGVO verlangt Zweckbindung. Eine andere Nutzung muss mit den Datenschutzregeln vereinbar sein und auf einer tragfähigen Grundlage beruhen.",
        "Daten werden für festgelegte Zwecke erhoben.")

    _add_family(out, choice, 6, "a", "Anfänger", "Rechtsgrundlagen", c,
        "Eine {person} bestellt eine Ware. Die Lieferadresse wird benötigt, um den Vertrag zu erfüllen. Welche Aussage ist richtig?",
        "Die Verarbeitung kann zur Vertragserfüllung erforderlich und damit nach Art. 6 Abs. 1 lit. b DSGVO zulässig sein.",
        [["Es ist immer zusätzlich eine freiwillige Einwilligung nötig, selbst wenn die Daten für die Vertragserfüllung erforderlich sind.","Vertragsdaten dürfen nur verarbeitet werden, wenn eine Aufsichtsbehörde vorher zustimmt.","Eine Lieferadresse darf grundsätzlich nicht elektronisch gespeichert werden."],
         ["Die DSGVO erlaubt Vertragsdaten nur bei Barzahlung.","Die Adresse darf nur verwendet werden, wenn sie öffentlich im Internet steht.","Für jede einzelne Bearbeitung muss ein neuer Vertrag unterschrieben werden."],
         ["Eine Rechtsgrundlage ist unnötig, sobald ein Unternehmen Geld für die Leistung erhält.","Nur Einwilligung kann eine Datenverarbeitung rechtmäßig machen.","Vertragserfüllung ist keine Rechtsgrundlage der DSGVO." ]],
        "Art. 6 Abs. 1 DSGVO kennt mehrere Rechtsgrundlagen. Für Daten, die zur Erfüllung eines Vertrags erforderlich sind, kommt insbesondere lit. b in Betracht.",
        "Einwilligung ist nicht die einzige Rechtsgrundlage.")

    _add_family(out, choice, 7, "a", "Anfänger", "Einwilligung", c,
        "Welche Aussage beschreibt eine wirksame Einwilligung am besten?",
        "Sie muss unter anderem freiwillig, für bestimmte Zwecke und informiert erfolgen und kann grundsätzlich widerrufen werden.",
        [["Sie ist automatisch wirksam, sobald ein Kästchen bereits vorausgewählt ist.","Sie darf nur mündlich und ohne Information über den Zweck erfolgen.","Nach einer Einwilligung ist ein Widerruf grundsätzlich ausgeschlossen."],
         ["Sie gilt immer für sämtliche zukünftigen Zwecke des Unternehmens.","Sie darf in einem Pflichtfeld versteckt werden, auch wenn sie für den Vertrag nicht nötig ist.","Sie ist nur gültig, wenn sie mindestens fünf Jahre nicht widerrufen wird."],
         ["Sie ersetzt jede andere Datenschutzpflicht.","Sie muss stets unbegrenzt gelten.","Sie ist auch dann freiwillig, wenn eine unnötige Einwilligung zwingende Voraussetzung für eine Leistung ist." ]],
        "Art. 7 DSGVO stellt Anforderungen an Einwilligungen. Sie müssen nachweisbar sein; ein Widerruf muss möglich sein. Freiwilligkeit und Zweckklarheit sind zentral.",
        "Einwilligung heißt echte Wahl und klare Information.")

    _add_family(out, choice, 8, "a", "Anfänger", "Betroffenenrechte", c,
        "Eine {person} fragt, welche personenbezogenen Daten das Unternehmen über sie verarbeitet. Welches Recht ist betroffen?",
        "Das Auskunftsrecht nach Art. 15 DSGVO.",
        [["Nur das Recht auf Datenübertragbarkeit.","Das Urheberrecht.","Nur das Recht auf Widerruf eines Kaufvertrags."],
         ["Das Recht auf unbegrenzte Datenspeicherung.","Das Hausrecht des Unternehmens.","Nur ein Recht auf telefonische Beratung."],
         ["Ein Recht, das nur Mitarbeitende haben.","Das Recht auf kostenlose Warenlieferung.","Ein Anspruch auf Veröffentlichung aller Unternehmensdaten." ]],
        "Art. 15 DSGVO gibt betroffenen Personen ein Recht auf Auskunft über die Verarbeitung ihrer personenbezogenen Daten und weitere Informationen.",
        "Es geht darum zu erfahren, was über die eigene Person gespeichert und verarbeitet wird.")

    _add_family(out, choice, 9, "a", "Anfänger", "Betroffenenrechte", c,
        "Eine gespeicherte Anschrift einer {person} ist falsch. Welches Recht passt am besten?",
        "Das Recht auf Berichtigung nach Art. 16 DSGVO.",
        [["Das Recht auf eine neue Kundennummer.","Das Recht auf unbegrenzte Speicherung.","Das Recht auf einen Rabatt."],
         ["Nur das Recht auf Datenübertragbarkeit.","Ein Anspruch auf Löschung aller Unternehmensdaten.","Das Recht, interne Passwörter zu erhalten."],
         ["Kein Datenschutzrecht, weil Adressen nie berichtigt werden müssen.","Nur ein Recht auf Widerspruch gegen Werbung.","Das Recht, jede Rechnung zu ändern." ]],
        "Nach Art. 16 DSGVO können betroffene Personen die unverzügliche Berichtigung unrichtiger personenbezogener Daten verlangen.",
        "Falsche personenbezogene Daten sollen korrigiert werden.")

    _add_family(out, choice, 10, "a", "Anfänger", "Löschung & Aufbewahrung", c,
        "Eine {person} verlangt die Löschung aller Daten. Welche Aussage ist richtig?",
        "Ein Löschungsrecht kann bestehen, ist aber nicht absolut; gesetzliche Aufbewahrungspflichten oder andere Ausnahmen können einer sofortigen Löschung entgegenstehen.",
        [["Das Unternehmen muss ausnahmslos jede Information innerhalb von fünf Minuten löschen.","Ein Löschungsrecht gibt es in der DSGVO überhaupt nicht.","Daten dürfen immer dauerhaft gespeichert werden, wenn sie einmal rechtmäßig erhoben wurden."],
         ["Nur Papierunterlagen können gelöscht werden, digitale Daten nie.","Eine Löschung ist erst nach 30 Jahren zulässig.","Jeder Löschwunsch darf ohne Prüfung abgelehnt werden."],
         ["Ein Löschungsverlangen beendet automatisch alle gesetzlichen Pflichten des Unternehmens.","Die DSGVO verlangt immer eine lebenslange Speicherung.","Löschung hängt nur vom verfügbaren Speicherplatz ab." ]],
        "Art. 17 DSGVO enthält das Recht auf Löschung, aber auch Ausnahmen, etwa wenn eine Verarbeitung zur Erfüllung einer rechtlichen Verpflichtung erforderlich ist.",
        "Löschung prüfen – nicht automatisch alles löschen und nicht automatisch ablehnen.")

    _add_family(out, choice, 11, "a", "Anfänger", "Zugriffsschutz", c,
        "Du verlässt deinen Arbeitsplatz im {dept} für einige Minuten. Im {system} sind personenbezogene Daten geöffnet. Was ist richtig?",
        "Den Bildschirm sperren, bevor du den Arbeitsplatz verlässt.",
        [["Nur das Fenster minimieren; der PC darf entsperrt bleiben.","Den Monitor ausschalten, aber den Rechner offen lassen.","Nichts tun, weil kurze Abwesenheiten datenschutzrechtlich nie relevant sind."],
         ["Das Programm offen lassen und nur den Stuhl heranschieben.","Die Daten ausdrucken und auf den Tisch legen.","Den Zugang mit Kolleginnen und Kollegen teilen, damit jemand aufpassen kann."],
         ["Die Daten auf einen privaten USB-Stick kopieren.","Nur den Mauszeiger aus dem Fenster bewegen.","Den Bildschirm lediglich dunkler stellen." ]],
        "Art. 5 Abs. 1 lit. f und Art. 32 DSGVO verlangen einen angemessenen Schutz vor unbefugtem Zugriff. Eine Bildschirmsperre ist eine typische organisatorisch-technische Maßnahme.",
        "Unbefugte dürfen auch bei kurzer Abwesenheit keinen freien Zugriff haben.")

    _add_family(out, choice, 12, "a", "Anfänger", "E-Mail & Kommunikation", c,
        "Du sendest eine allgemeine Information an 35 externe Empfänger, die ihre E-Mail-Adressen gegenseitig nicht sehen sollen. Welche Versandart ist typischerweise geeignet?",
        "Die Empfängeradressen in Bcc setzen, sofern der betriebliche Prozess dies vorsieht.",
        [["Alle Adressen offen in das An-Feld setzen.","Alle Adressen offen in Cc setzen.","Die Adressliste zusätzlich als Anhang mitsenden."],
         ["Die E-Mail zehnmal weiterleiten, jeweils mit allen bisherigen Empfängern sichtbar.","Die Adressen in den Betreff schreiben.","Die Empfängerliste in die Signatur kopieren."],
         ["Die E-Mail an eine öffentliche Mailingliste schicken.","Alle Adressen in den Nachrichtentext schreiben.","Die Adressen öffentlich auf der Website veröffentlichen und darauf verweisen." ]],
        "Das offene Sichtbarmachen fremder E-Mail-Adressen kann personenbezogene Daten unbefugt offenlegen. Bcc kann bei Rundmails helfen, Empfängeradressen voreinander zu schützen.",
        "Sollen die Empfänger die Adressen der anderen wirklich sehen?")

    _add_family(out, choice, 13, "a", "Anfänger", "Passwörter & Konten", c,
        "Welche Vorgehensweise ist für ein Benutzerkonto im {system} am sichersten?",
        "Ein eigenes starkes Passwort verwenden, es nicht für andere Dienste wiederverwenden und nach Möglichkeit einen Passwortmanager nutzen.",
        [["Dasselbe Passwort für alle beruflichen und privaten Konten verwenden.","Das Passwort mit dem Team teilen, damit Vertretungen leichter arbeiten können.","Das Passwort als Klartext auf einen Zettel am Monitor kleben."],
         ["Ein sehr kurzes Passwort verwenden, solange es jeden Monat gleich bleibt.","Das Passwort im Dateinamen einer Textdatei speichern.","Den eigenen Zugang dauerhaft angemeldet für alle Mitarbeitenden offen lassen."],
         ["Ein Standardpasswort des Herstellers unverändert lassen.","Passwörter per unverschlüsselter Rundmail verteilen.","Für alle Abteilungen denselben Sammelzugang nutzen, obwohl persönliche Konten vorgesehen sind." ]],
        "Das BSI empfiehlt für Konten eigene sichere Passwörter und nennt Passwortmanager als sinnvolle Hilfe. Persönliche Zugangsdaten sollen nicht geteilt werden.",
        "Ein Konto – ein eigenes Passwort.")

    _add_family(out, choice, 14, "a", "Anfänger", "Passwörter & Konten", c,
        "Für das {system} wird zusätzlich zum Passwort eine Zwei-Faktor-Authentisierung angeboten. Was bringt sie?",
        "Sie ergänzt das Passwort um einen weiteren Faktor und kann den Kontozugriff besser absichern.",
        [["Sie ersetzt jede andere Sicherheitsmaßnahme im Unternehmen.","Sie macht Passwörter grundsätzlich überflüssig, auch wenn das System sie verlangt.","Sie sorgt dafür, dass alle Mitarbeitenden denselben Zugang verwenden können."],
         ["Sie verschlüsselt automatisch jede Datei im Unternehmen.","Sie verhindert jeden denkbaren Cyberangriff.","Sie ist nur für private Spielekonten sinnvoll."],
         ["Sie erlaubt das Weitergeben des Passworts an Kollegen.","Sie dient nur dazu, Werbung zu blockieren.","Sie macht Sicherheitsupdates unnötig." ]],
        "Das BSI empfiehlt 2FA dort, wo sie angeboten wird, als zusätzliche Absicherung eines Kontos.",
        "Zwei voneinander unabhängige Nachweise sind schwerer zu missbrauchen als nur ein Passwort.")

    _add_family(out, choice, 15, "a", "Anfänger", "Phishing & E-Mail-Sicherheit", c,
        "Du erhältst im {dept} unerwartet eine E-Mail mit Anhang und der Aufforderung, sofort Makros zu aktivieren. Was ist am sinnvollsten?",
        "Anhang nicht ausführen, Absender und Vorgang über einen sicheren Weg prüfen und die interne Sicherheitsregel beachten.",
        [["Makros sofort aktivieren, damit die Datei vollständig angezeigt wird.","Die Datei an die private E-Mail-Adresse schicken und dort öffnen.","Die Sicherheitswarnung ignorieren, wenn der Absendername bekannt klingt."],
         ["Auf jeden Link klicken, um die Echtheit zu testen.","Das eigene Passwort als Antwort senden.","Den Anhang an alle Kolleginnen und Kollegen weiterleiten."],
         ["Virenschutz deaktivieren, falls der Anhang blockiert wird.","Die Warnung fotografieren und anschließend trotzdem öffnen.","Den Absender aus der E-Mail heraus über den enthaltenen Link kontaktieren." ]],
        "Unerwartete Anhänge und Aufforderungen zum Aktivieren von Makros sind typische Warnsignale. Das BSI empfiehlt, verdächtige Nachrichten kritisch zu prüfen und nicht unbedacht Inhalte auszuführen.",
        "Nicht öffnen, erst verifizieren.")

    _add_family(out, choice, 16, "a", "Anfänger", "Papier & Clean Desk", c,
        "Die {doc} enthält personenbezogene Daten und wird nicht mehr benötigt. Wie sollte sie entsorgt werden?",
        "Nach der betrieblichen Datenschutzregel sicher vernichten, zum Beispiel über den vorgesehenen Aktenvernichtungsweg.",
        [["In den normalen offenen Papierkorb werfen.","Als Schmierpapier im öffentlich zugänglichen Bereich weiterverwenden.","Auf dem Drucker liegen lassen, bis jemand anderes sie entsorgt."],
         ["Mit nach Hause nehmen und dort wegwerfen.","In der Teeküche ablegen.","Ein Foto davon für alle Fälle auf dem privaten Handy speichern."],
         ["An die Pinnwand hängen und später entsorgen.","In einem frei zugänglichen Altpapierkorb sammeln.","Die Rückseite für Besucherlisten weiterverwenden." ]],
        "Personenbezogene Daten müssen vor unbefugtem Zugriff geschützt werden. Sichere Vernichtung ist eine organisatorische Maßnahme nach Art. 32 DSGVO.",
        "Auch Papier kann personenbezogene Daten offenlegen.")

    _add_family(out, choice, 17, "a", "Anfänger", "Zugriffsrechte", c,
        "Wer sollte im Unternehmen Zugriff auf die {doc} mit personenbezogenen Daten erhalten?",
        "Nur Personen, die den Zugriff für ihre Aufgabe tatsächlich benötigen.",
        [["Grundsätzlich alle Mitarbeitenden, weil es interne Daten sind.","Jede Person mit einem Firmen-PC.","Alle Praktikanten automatisch ab dem ersten Tag."],
         ["Jeder, der aus Interesse nachfragt.","Alle Beschäftigten, unabhängig von ihrer Zuständigkeit.","Auch externe Besucher, solange sie nichts verändern."],
         ["Nur die Person mit dem längsten Dienstalter, auch wenn sie den Vorgang nicht bearbeitet.","Alle Abteilungen vorsorglich.","Jeder, der den Dateipfad kennt." ]],
        "Art. 5 Abs. 1 lit. f und Art. 32 DSGVO sprechen für rollen- und aufgabenbezogene Zugriffe. Das Prinzip 'Need to know' reduziert unbefugte Einsicht.",
        "Zugriff nach Aufgabe, nicht nach Neugier.")

    _add_family(out, choice, 18, "a", "Anfänger", "Datenpannen", c,
        "Du merkst, dass du eine {doc} mit personenbezogenen Daten versehentlich an den falschen externen Empfänger gesendet hast. Was ist zuerst sinnvoll?",
        "Den Vorfall unverzüglich nach dem internen Meldeweg melden und nicht eigenmächtig vertuschen.",
        [["Nichts tun, solange sich der Empfänger nicht beschwert.","Die gesendete E-Mail aus dem eigenen Postfach löschen und den Vorfall verschweigen.","Erst nach einigen Wochen erwähnen, falls jemand nachfragt."],
         ["Nur die Datei auf dem eigenen PC umbenennen.","Den falschen Empfänger ohne interne Abstimmung bedrohen.","Den Vorgang als normalen Tippfehler behandeln und nicht dokumentieren."],
         ["Alle Kolleginnen und Kollegen per Rundmail mit den betroffenen Daten informieren.","Die Daten erneut an denselben falschen Empfänger schicken.","Den Computer ausschalten und den Vorfall vergessen." ]],
        "Eine Fehlübermittlung kann eine Verletzung des Schutzes personenbezogener Daten sein. Sie muss intern schnell bewertet werden, damit Pflichten nach Art. 33 und ggf. Art. 34 DSGVO eingehalten werden können.",
        "Schnell intern melden, damit Risiko und weitere Schritte geprüft werden können.")

    _add_family(out, choice, 19, "a", "Anfänger", "Sichere Übermittlung", c,
        "Du sollst eine {doc} mit sensiblen personenbezogenen Daten an eine berechtigte externe Stelle übermitteln. Was ist die beste Grundidee?",
        "Den vorgesehenen sicheren Übertragungsweg nutzen und Empfänger sowie Berechtigung vor dem Versand prüfen.",
        [["Die Datei über einen beliebigen privaten Messenger senden.","Die Daten in eine öffentliche Cloud ohne Freigabekontrolle hochladen.","Die Empfängeradresse ungeprüft aus einer alten E-Mail übernehmen."],
         ["Die Datei öffentlich verlinken, damit der Empfänger sie leichter findet.","Die Unterlage an mehrere mögliche Empfänger gleichzeitig schicken.","Sensible Daten in den Betreff schreiben."],
         ["Den betrieblichen Übertragungsweg umgehen, wenn der private Weg schneller ist.","Empfängeradressen nie kontrollieren, solange Autovervollständigung aktiv ist.","Die Datei ohne Zugriffsschutz in einem frei erreichbaren Ordner ablegen." ]],
        "Art. 32 DSGVO verlangt ein dem Risiko angemessenes Schutzniveau. Dazu gehören geeignete Übertragungswege, Zugriffsschutz und eine sorgfältige Empfängerprüfung.",
        "Sicherer Kanal + richtiger Empfänger + Berechtigung.")

    return out[:188]


def _contexts_intermediate():
    return [
        {"company":"Büroservice Nord", "process":"Kundenportal", "data":"Kundendaten", "vendor":"Cloud-Dienstleister"},
        {"company":"Handelskontor West", "process":"Online-Shop", "data":"Bestelldaten", "vendor":"Hostinganbieter"},
        {"company":"Logistikpartner Süd", "process":"Tourenplanung", "data":"Fahrerdaten", "vendor":"Softwareanbieter"},
        {"company":"Servicezentrum Mitte", "process":"Ticketsystem", "data":"Supportdaten", "vendor":"IT-Supportfirma"},
        {"company":"Personalbüro Alpha", "process":"Bewerberportal", "data":"Bewerberdaten", "vendor":"Recruiting-Plattform"},
        {"company":"Vertriebshaus Beta", "process":"CRM", "data":"Kontaktdaten", "vendor":"CRM-Anbieter"},
        {"company":"Abrechnung Gamma", "process":"Lohnabrechnung", "data":"Beschäftigtendaten", "vendor":"Abrechnungsdienstleister"},
        {"company":"Einkauf Delta", "process":"Bestellsystem", "data":"Lieferantendaten", "vendor":"ERP-Dienstleister"},
        {"company":"Kundenservice Epsilon", "process":"Kontaktcenter", "data":"Gesprächsnotizen", "vendor":"Callcenter-Dienstleister"},
        {"company":"Projektbüro Zeta", "process":"Projektplattform", "data":"Projektkontaktdaten", "vendor":"Collaboration-Anbieter"},
    ]


def build_intermediate(choice):
    out=[]
    c=_contexts_intermediate()

    _add_family(out, choice, 1, "f", "Fortgeschritten", "Verantwortlicher & Auftragsverarbeiter", c,
        "{company} entscheidet, warum und wie {data} im {process} verarbeitet werden. Welche Rolle beschreibt das am ehesten?",
        "Verantwortlicher, weil das Unternehmen über Zwecke und wesentliche Mittel der Verarbeitung entscheidet.",
        [["Auftragsverarbeiter, nur weil Software eingesetzt wird.","Betroffene Person, weil das Unternehmen Daten besitzt.","Aufsichtsbehörde, weil es interne Regeln festlegt."],
         ["Datenschutzbeauftragter als Organisationseinheit.","Empfänger ohne eigene Verantwortung.","Automatisch gemeinsamer Verantwortlicher mit jedem Softwarehersteller."],
         ["Nur technischer Nutzer ohne datenschutzrechtliche Rolle.","Immer Auftragsverarbeiter, sobald Daten elektronisch vorliegen.","Betroffener, weil das Unternehmen Rechnungen erhält." ]],
        "Art. 4 Nr. 7 DSGVO definiert den Verantwortlichen als Stelle, die über Zwecke und Mittel der Verarbeitung entscheidet.",
        "Wer bestimmt das Warum und die wesentlichen Rahmenbedingungen?")

    _add_family(out, choice, 2, "f", "Fortgeschritten", "Auftragsverarbeitung", c,
        "{vendor} verarbeitet {data} ausschließlich nach Weisung von {company} für das {process}. Was ist typischerweise erforderlich?",
        "Eine Auftragsverarbeitungsregelung nach Art. 28 DSGVO mit einem geeigneten Auftragsverarbeiter.",
        [["Nur eine mündliche Absprache ohne Datenschutzinhalte.","Keine Regelung, solange der Dienstleister bezahlt wird.","Eine Einwilligung sämtlicher Beschäftigter für jede einzelne Verarbeitung unabhängig von der Rechtsgrundlage."],
         ["Ein Kaufvertrag über Hardware genügt immer automatisch.","Nur ein Hinweis im Impressum des Dienstleisters.","Ein Vertrag ist nur nötig, wenn der Dienstleister außerhalb Deutschlands sitzt."],
         ["Auftragsverarbeitung braucht nie dokumentierte Weisungen.","Der Dienstleister darf die Daten frei für eigene Zwecke nutzen.","Es genügt, dass der Dienstleister verspricht, vorsichtig zu sein." ]],
        "Art. 28 DSGVO verlangt bei Auftragsverarbeitung eine verbindliche Regelung und hinreichende Garantien für geeignete technische und organisatorische Maßnahmen.",
        "Wer Daten weisungsgebunden für einen anderen verarbeitet, braucht klare Regeln.")

    _add_family(out, choice, 3, "f", "Fortgeschritten", "Auftragsverarbeitung", c,
        "{vendor} möchte für das {process} einen weiteren Unterauftragnehmer einsetzen. Welche Aussage passt zu Art. 28 DSGVO?",
        "Der Einsatz weiterer Auftragsverarbeiter braucht die vorherige spezifische oder allgemeine schriftliche bzw. elektronische Genehmigung des Verantwortlichen; bei allgemeiner Genehmigung ist über Änderungen zu informieren.",
        [["Unterauftragnehmer dürfen immer ohne Information eingesetzt werden.","Nur der Unterauftragnehmer muss zustimmen; der Verantwortliche hat keine Rolle.","Eine Genehmigung ist nur bei Papierakten nötig."],
         ["Der Verantwortliche erfährt erst nach Vertragsende davon.","Unterauftragnehmer sind datenschutzrechtlich grundsätzlich verboten.","Eine Genehmigung ist nur nötig, wenn mehr als 1.000 Datensätze betroffen sind."],
         ["Der Dienstleister entscheidet allein und darf dem Verantwortlichen den Namen nicht nennen.","Allgemeine Genehmigungen sind in der DSGVO ausgeschlossen.","Nur die betroffenen Personen können Unterauftragnehmer genehmigen." ]],
        "Art. 28 Abs. 2 DSGVO regelt den Einsatz weiterer Auftragsverarbeiter. Die Kontrolle verbleibt beim Verantwortlichen.",
        "Subunternehmer in der Datenverarbeitung dürfen nicht völlig überraschend hinzukommen.")

    _add_family(out, choice, 4, "f", "Fortgeschritten", "Betroffenenrechte", c,
        "Eine betroffene Person stellt bei {company} einen normalen Auskunftsantrag. Welche Grundfrist nennt Art. 12 Abs. 3 DSGVO für die Reaktion?",
        "Unverzüglich, in jedem Fall grundsätzlich innerhalb eines Monats nach Eingang des Antrags.",
        [["Immer innerhalb von 72 Stunden.","Grundsätzlich erst nach sechs Monaten.","Es gibt keinerlei Frist."],
         ["Immer innerhalb von 14 Kalendertagen.","Erst zum Ende des Geschäftsjahres.","Nur wenn die Aufsichtsbehörde erinnert."],
         ["Genau drei Monate ohne Verlängerungsmöglichkeit.","Nur an Werktagen innerhalb von 30 Arbeitstagen.","Erst nach Zahlung einer Bearbeitungsgebühr." ]],
        "Art. 12 Abs. 3 DSGVO sieht grundsätzlich eine Information über Maßnahmen innerhalb eines Monats vor. Bei komplexen oder zahlreichen Anträgen kann unter den gesetzlichen Voraussetzungen verlängert werden.",
        "Nicht mit der 72-Stunden-Frist für bestimmte Datenpannen verwechseln.")

    _add_family(out, choice, 5, "f", "Fortgeschritten", "Betroffenenrechte", c,
        "Bei einem Auskunftsantrag bestehen begründete Zweifel an der Identität der anfragenden Person. Was darf {company} tun?",
        "Zusätzliche Informationen anfordern, die zur Bestätigung der Identität erforderlich sind, ohne unnötig mehr Daten zu verlangen.",
        [["Den Antrag automatisch endgültig ablehnen.","Ohne Prüfung eine vollständige Datenkopie an die angegebene E-Mail-Adresse senden.","Immer eine Kopie des Personalausweises mit allen Angaben verlangen, unabhängig vom Risiko."],
         ["Die Identität nie prüfen, weil Auskunft stets anonym möglich sein muss.","Den Antrag öffentlich im Teamchat veröffentlichen.","Die Person zwingen, sämtliche Unternehmensdaten offenzulegen."],
         ["Nur die Telefonnummer aus einem beliebigen Internetverzeichnis vergleichen und danach sensible Daten versenden.","Eine Identitätsprüfung ist nach der DSGVO grundsätzlich verboten.","Den Antrag erst nach einem Jahr bearbeiten." ]],
        "Art. 12 Abs. 6 DSGVO erlaubt bei begründeten Zweifeln zusätzliche Informationen zur Identitätsbestätigung. Auch dabei gilt Datenminimierung.",
        "Identität angemessen prüfen – nicht blind herausgeben und nicht unnötig Daten sammeln.")

    _add_family(out, choice, 6, "f", "Fortgeschritten", "Löschung & Aufbewahrung", c,
        "Eine Person verlangt Löschung von {data}. Ein Teil muss aufgrund einer gesetzlichen Aufbewahrungspflicht weiter gespeichert werden. Was ist richtig?",
        "Die Löschanfrage ist differenziert zu prüfen; Daten mit fortbestehender rechtlicher Aufbewahrungspflicht können von der sofortigen Löschung ausgenommen sein.",
        [["Die gesetzliche Aufbewahrungspflicht entfällt automatisch durch den Löschantrag.","Der Löschantrag darf vollständig ignoriert werden, sobald irgendeine Aufbewahrungspflicht besteht.","Alle Daten müssen unabhängig von Rechtsgrundlagen für immer gespeichert werden."],
         ["Nur digitale Daten unterliegen dem Löschungsrecht.","Man darf die Daten weiter für beliebige neue Zwecke nutzen, solange sie aufbewahrt werden müssen.","Aufbewahrungspflichten spielen im Datenschutz nie eine Rolle."],
         ["Es muss ausnahmslos alles sofort gelöscht werden und anschließend neu erfasst werden.","Die Daten dürfen zur Werbung weiterverwendet werden, weil sie ohnehin gespeichert bleiben.","Löschung ist nur auf Papier möglich." ]],
        "Art. 17 DSGVO enthält Löschgründe und Ausnahmen. Eine rechtliche Verpflichtung kann die weitere Speicherung bestimmter Daten rechtfertigen; die Nutzung bleibt zweckgebunden.",
        "Speichern müssen heißt nicht automatisch für jeden Zweck nutzen dürfen.")

    _add_family(out, choice, 7, "f", "Fortgeschritten", "Betroffenenrechte", c,
        "Eine Person bestreitet die Richtigkeit bestimmter {data}; die Prüfung dauert an. Welches Recht kann in dieser Situation besonders relevant sein?",
        "Das Recht auf Einschränkung der Verarbeitung nach Art. 18 DSGVO.",
        [["Ein Recht auf Veröffentlichung der Daten.","Das Recht, sämtliche Unternehmenssoftware zu sperren.","Ein automatischer Anspruch auf Schadensersatz in jeder Höhe."],
         ["Nur das Recht auf Datenübertragbarkeit.","Das Recht auf dauerhafte Geheimhaltung gegenüber der betroffenen Person.","Ein Recht auf Löschung aller anderen Kundendaten."],
         ["Das Recht, die Daten ohne Prüfung selbst im System zu verändern.","Kein Betroffenenrecht, solange Daten elektronisch vorliegen.","Nur ein Recht auf Widerruf des Arbeitsvertrags." ]],
        "Art. 18 DSGVO nennt unter anderem die bestrittene Richtigkeit als Fall, in dem eine Einschränkung der Verarbeitung verlangt werden kann.",
        "Einschränkung kann eine Zwischenlösung sein, während etwas geklärt wird.")

    _add_family(out, choice, 8, "f", "Fortgeschritten", "Betroffenenrechte", c,
        "{company} verarbeitet Daten für Direktwerbung. Die betroffene Person widerspricht dieser Verarbeitung. Was gilt grundsätzlich?",
        "Bei Widerspruch gegen Verarbeitung für Direktwerbung dürfen die personenbezogenen Daten nicht mehr für diese Zwecke verarbeitet werden.",
        [["Der Widerspruch gilt erst nach fünf weiteren Werbesendungen.","Direktwerbung ist vom Widerspruchsrecht immer ausgenommen.","Das Unternehmen darf den Widerspruch ohne Prüfung unbegrenzt ignorieren."],
         ["Der Widerspruch betrifft nur Papierwerbung, nicht E-Mail-Werbung.","Die Person muss ihren Widerspruch jedes Quartal wiederholen.","Ein Widerspruch ist nur über einen Notar wirksam."],
         ["Nach einem Widerspruch darf Werbung unverändert weiterlaufen, wenn das CRM technisch bequem ist.","Nur die Aufsichtsbehörde kann Direktwerbung beenden.","Der Widerspruch wird erst nach Vertragsende wirksam." ]],
        "Art. 21 Abs. 2 und 3 DSGVO regelt den Widerspruch gegen Direktwerbung besonders klar: Danach ist eine weitere Verarbeitung für Direktwerbezwecke zu unterlassen.",
        "Direktwerbung hat beim Widerspruch eine besondere Regel.")

    _add_family(out, choice, 9, "f", "Fortgeschritten", "Betroffenenrechte", c,
        "Eine Person möchte bestimmte selbst bereitgestellte Daten aus dem {process} in einem strukturierten, gängigen und maschinenlesbaren Format erhalten. Welches Recht kann gemeint sein?",
        "Das Recht auf Datenübertragbarkeit nach Art. 20 DSGVO, sofern dessen Voraussetzungen erfüllt sind.",
        [["Nur das Recht auf Berichtigung.","Das Recht auf Einsicht in den Quellcode des Systems.","Ein Anspruch auf sämtliche internen Geschäftsgeheimnisse."],
         ["Das Recht auf Löschung aller Daten anderer Personen.","Ein Recht auf kostenlose Hardware.","Das Hausrecht des Unternehmens."],
         ["Ein Recht, das ausschließlich Behörden haben.","Ein Anspruch auf Übergabe sämtlicher Backups.","Nur das Recht auf eine Papierkopie ohne weitere Voraussetzungen." ]],
        "Art. 20 DSGVO regelt die Datenübertragbarkeit unter bestimmten Voraussetzungen, insbesondere bei automatisierter Verarbeitung auf Basis von Einwilligung oder Vertrag.",
        "Maschinenlesbares Format ist ein typischer Hinweis auf Art. 20.")

    _add_family(out, choice, 10, "f", "Fortgeschritten", "Beschäftigtendaten", c,
        "Welche Grundidee enthält § 26 BDSG für die Verarbeitung von Beschäftigtendaten?",
        "Beschäftigtendaten dürfen insbesondere verarbeitet werden, wenn dies für die Entscheidung über, Durchführung oder Beendigung des Beschäftigungsverhältnisses erforderlich ist.",
        [["Arbeitgeber dürfen sämtliche privaten Daten ohne Zweck speichern.","Beschäftigtendaten fallen generell nicht unter Datenschutzrecht.","Nur handschriftliche Personalakten sind geschützt."],
         ["Jede Verarbeitung von Beschäftigtendaten braucht zwingend eine Einwilligung.","Nach der Einstellung dürfen keine Beschäftigtendaten mehr verarbeitet werden.","§ 26 BDSG erlaubt unbegrenzte Überwachung ohne Erforderlichkeitsprüfung."],
         ["Beschäftigtendaten dürfen nur im Ausland verarbeitet werden.","Der Arbeitgeber darf Gesundheitsdaten immer offen im Team teilen.","Bewerber gelten nie als Beschäftigte im Sinne des § 26 BDSG." ]],
        "§ 26 Abs. 1 BDSG knüpft die Verarbeitung im Beschäftigungskontext wesentlich an die Erforderlichkeit für Begründung, Durchführung oder Beendigung des Beschäftigungsverhältnisses.",
        "Auch im Arbeitsverhältnis gilt: Zweck und Erforderlichkeit prüfen.")

    _add_family(out, choice, 11, "f", "Fortgeschritten", "Beschäftigtendaten", c,
        "{company} möchte eine Einwilligung von Beschäftigten nutzen. Was muss bei der Freiwilligkeit besonders berücksichtigt werden?",
        "Die Abhängigkeit im Beschäftigungsverhältnis und die konkreten Umstände, unter denen die Einwilligung erteilt wird.",
        [["Freiwilligkeit ist im Arbeitsverhältnis automatisch immer gegeben.","Eine Einwilligung ist nur dann freiwillig, wenn sie nie widerrufen werden kann.","Die Stellung des Arbeitgebers spielt bei der Freiwilligkeit keine Rolle."],
         ["Nur das Alter des Unternehmens ist entscheidend.","Eine Einwilligung gilt als freiwillig, sobald sie im Arbeitsvertrag steht, unabhängig vom Inhalt.","Beschäftigte können datenschutzrechtlich nie einwilligen."],
         ["Freiwilligkeit hängt allein von der Schriftgröße des Formulars ab.","Ein wirtschaftlicher oder rechtlicher Nachteil bei Ablehnung ist immer irrelevant.","Nur der Betriebsrat kann für alle Beschäftigten individuell einwilligen." ]],
        "§ 26 Abs. 2 BDSG verlangt bei Beschäftigteneinwilligungen eine besondere Betrachtung der Abhängigkeit und Umstände. Freiwilligkeit ist nicht einfach zu unterstellen.",
        "Im Arbeitsverhältnis besteht ein strukturelles Abhängigkeitsverhältnis.")

    _add_family(out, choice, 12, "f", "Fortgeschritten", "Datenpannen", c,
        "{company} stellt eine Verletzung des Schutzes personenbezogener Daten fest. Wann muss die zuständige Aufsichtsbehörde nach Art. 33 DSGVO grundsätzlich informiert werden?",
        "Unverzüglich und möglichst binnen 72 Stunden nach Bekanntwerden, sofern die Verletzung voraussichtlich zu einem Risiko für Rechte und Freiheiten natürlicher Personen führt.",
        [["Immer erst nach 30 Tagen.","Nur wenn mindestens 10.000 Datensätze betroffen sind.","Nie, solange die Daten digital gespeichert waren."],
         ["Grundsätzlich binnen eines Jahres.","Nur wenn die betroffene Person vorher zustimmt.","Erst nach Abschluss aller internen Untersuchungen, unabhängig von der Dauer."],
         ["Innerhalb von 24 Monaten.","Nur Datenpannen bei Papierakten können meldepflichtig sein.","Eine Meldung ist nur nötig, wenn bereits ein Schaden eingetreten ist." ]],
        "Art. 33 Abs. 1 DSGVO nennt die 72-Stunden-Regel und die Ausnahme, wenn voraussichtlich kein Risiko für die Rechte und Freiheiten natürlicher Personen besteht.",
        "72 Stunden beziehen sich auf die Aufsichtsbehörde, nicht auf jeden Betroffenenantrag.")

    _add_family(out, choice, 13, "f", "Fortgeschritten", "Datenpannen", c,
        "Wann kann zusätzlich zur Behördenmeldung eine Benachrichtigung der betroffenen Personen nach Art. 34 DSGVO erforderlich sein?",
        "Wenn die Verletzung voraussichtlich ein hohes Risiko für die persönlichen Rechte und Freiheiten der betroffenen Personen zur Folge hat.",
        [["Bei jeder kleinen technischen Störung ohne Personenbezug.","Nur wenn die Betroffenen bereits aus der Presse davon erfahren haben.","Nie; Betroffene dürfen bei Datenpannen grundsätzlich nicht informiert werden."],
         ["Nur wenn mehr als 100.000 Personen betroffen sind.","Ausschließlich auf richterliche Anordnung.","Nur bei Verlust von Papier, nie bei digitalen Daten."],
         ["Sobald ein Server neu gestartet wird.","Immer bei jeder vergessenen Bildschirmsperre, unabhängig von Risiko und Zugriff.","Nur wenn das Unternehmen keine Datenschutzbeauftragte hat." ]],
        "Art. 34 DSGVO knüpft die Benachrichtigung der betroffenen Person an ein voraussichtlich hohes Risiko. Die Risikobewertung ist daher entscheidend.",
        "Behördenmeldung und Betroffeneninformation haben unterschiedliche Risikoschwellen.")

    _add_family(out, choice, 14, "f", "Fortgeschritten", "Pseudonymisierung & Anonymisierung", c,
        "Im {process} werden Namen durch Codes ersetzt. {company} besitzt separat eine Zuordnungstabelle. Wie sind die Daten typischerweise einzuordnen?",
        "Pseudonymisiert, aber weiterhin personenbezogen, weil die Zuordnung mit Zusatzinformationen möglich ist.",
        [["Vollständig anonym und damit sicher außerhalb der DSGVO.","Keine Datenverarbeitung mehr, weil Namen fehlen.","Automatisch öffentliche Daten."],
         ["Nur verschlüsselte Betriebsgeheimnisse ohne Personenbezug.","Immer anonym, sobald ein Code verwendet wird.","Nicht personenbezogen, solange die Zuordnungstabelle in einem anderen Ordner liegt."],
         ["Anonym, wenn der Code mehr als acht Zeichen hat.","Anonym, sobald nur Mitarbeitende die Zuordnung kennen.","Keine personenbezogenen Daten, weil die Person nicht direkt im Dateinamen steht." ]],
        "Art. 4 Nr. 5 DSGVO beschreibt Pseudonymisierung. Solange eine Zuordnung mit zusätzlichen Informationen möglich ist, bleibt der Personenbezug grundsätzlich bestehen.",
        "Code statt Name ist nicht automatisch anonym.")

    _add_family(out, choice, 15, "f", "Fortgeschritten", "Technische & organisatorische Maßnahmen", c,
        "Wie bestimmt {company} nach Art. 32 DSGVO angemessene Sicherheitsmaßnahmen für {data}?",
        "Risikoorientiert unter Berücksichtigung unter anderem von Stand der Technik, Art, Umfang, Umständen und Zwecken der Verarbeitung sowie Eintrittswahrscheinlichkeit und Schwere möglicher Risiken.",
        [["Ausschließlich nach dem günstigsten Preis.","Immer mit exakt denselben Maßnahmen, unabhängig von Daten und Risiko.","Nur danach, welche Software gerade im Unternehmen vorhanden ist."],
         ["Nur nach der Anzahl der Mitarbeitenden.","Ausschließlich nach Wunsch der IT-Abteilung ohne Risikobetrachtung.","Sicherheitsmaßnahmen sind bei personenbezogenen Daten freiwillig."],
         ["Nur nach der Dateigröße.","Je älter ein System ist, desto weniger Schutz ist nötig.","Art. 32 verlangt nur Verschlüsselung und sonst keine organisatorischen Maßnahmen." ]],
        "Art. 32 DSGVO verlangt ein dem Risiko angemessenes Schutzniveau. Genannt werden technische und organisatorische Maßnahmen, nicht eine starre Einheitslösung.",
        "Das Risiko der konkreten Verarbeitung bestimmt das Schutzniveau mit.")

    _add_family(out, choice, 16, "f", "Fortgeschritten", "Datenschutz-Folgenabschätzung", c,
        "Wann ist eine Datenschutz-Folgenabschätzung nach Art. 35 DSGVO besonders zu prüfen?",
        "Wenn eine Form der Verarbeitung voraussichtlich ein hohes Risiko für die Rechte und Freiheiten natürlicher Personen zur Folge hat.",
        [["Bei jeder einzelnen E-Mail im Unternehmen.","Nur wenn kein Internetanschluss vorhanden ist.","Ausschließlich nach einer bereits eingetretenen Datenpanne."],
         ["Nur bei Unternehmen mit mehr als 10.000 Beschäftigten.","Nie bei automatisierter Verarbeitung.","Nur wenn die Aufsichtsbehörde jede einzelne Verarbeitung vorher genehmigt."],
         ["Nur wenn die Daten auf Papier stehen.","Immer bei jeder normalen Kundenbestellung.","Ausschließlich bei Daten aus dem Ausland." ]],
        "Art. 35 DSGVO knüpft die DSFA an voraussichtlich hohe Risiken, insbesondere bei bestimmten neuen Technologien oder besonders eingriffsintensiven Verarbeitungen.",
        "DSFA = vorherige strukturierte Risikobewertung bei hohem Risiko.")

    _add_family(out, choice, 17, "f", "Fortgeschritten", "Datenschutzbeauftragte", c,
        "Welche ergänzende deutsche Regel nennt § 38 BDSG für nichtöffentliche Stellen?",
        "Ein Datenschutzbeauftragter ist unter anderem zu benennen, wenn in der Regel mindestens 20 Personen ständig mit der automatisierten Verarbeitung personenbezogener Daten beschäftigt sind; daneben gibt es weitere Fälle unabhängig von dieser Zahl.",
        [["Ein Datenschutzbeauftragter ist erst ab 500 Beschäftigten möglich.","Jedes Unternehmen braucht ausnahmslos ab der ersten Person einen internen Datenschutzbeauftragten nach § 38 BDSG.","Die Zahl der mit automatisierter Verarbeitung beschäftigten Personen spielt in Deutschland nie eine Rolle."],
         ["Die Grenze liegt nach § 38 BDSG grundsätzlich bei genau fünf Personen.","Nur Behörden dürfen einen Datenschutzbeauftragten benennen.","Ein Datenschutzbeauftragter ist verboten, wenn weniger als 20 Personen beschäftigt sind."],
         ["Die Benennungspflicht richtet sich ausschließlich nach dem Jahresumsatz.","Ein Datenschutzbeauftragter wird nur nach einer Datenpanne nötig.","§ 38 BDSG gilt nur für Papierakten." ]],
        "§ 38 Abs. 1 BDSG ergänzt Art. 37 DSGVO. Die 20-Personen-Regel ist nicht die einzige Benennungspflicht; etwa bestimmte DSFA-pflichtige oder geschäftsmäßige Verarbeitungen können unabhängig davon relevant sein.",
        "Merke: 20 Personen ist eine deutsche Zusatzregel, aber nicht die einzige.")

    _add_family(out, choice, 18, "f", "Fortgeschritten", "Datenschutz durch Technikgestaltung", c,
        "Ein neues {process} soll standardmäßig nur die für den jeweiligen Vorgang notwendigen {data} anzeigen. Welches DSGVO-Prinzip wird damit besonders umgesetzt?",
        "Datenschutz durch Technikgestaltung und datenschutzfreundliche Voreinstellungen nach Art. 25 DSGVO.",
        [["Nur das Recht auf Datenübertragbarkeit.","Ausschließlich die Pflicht zur Bestellung eines Datenschutzbeauftragten.","Das Recht auf Vergessenwerden ohne weiteren Bezug."],
         ["Nur die Meldepflicht nach Art. 33 DSGVO.","Ausschließlich die Informationspflicht bei Datenpannen.","Das Verbot jeder Automatisierung."],
         ["Nur die Archivierungspflicht.","Ausschließlich die Pflicht zur Veröffentlichung von Quellcode.","Die Regel, dass alle Daten standardmäßig für alle sichtbar sein sollen." ]],
        "Art. 25 DSGVO verlangt Datenschutz durch Technikgestaltung und datenschutzfreundliche Voreinstellungen. Standardmäßig sollen insbesondere nur erforderliche Daten verarbeitet werden.",
        "Privacy by Design und Privacy by Default beginnen schon bei der Systemgestaltung.")

    _add_family(out, choice, 19, "f", "Fortgeschritten", "Dienstleister & Cloud", c,
        "{company} möchte {vendor} für das {process} einsetzen. Welche Prüfung ist vor der Freigabe datenschutzrechtlich sinnvoll?",
        "Rolle des Dienstleisters, Rechtsgrundlage, Vertrag nach Art. 28 soweit einschlägig, Sicherheitsmaßnahmen, Datenstandorte und erforderliche Garantien prüfen.",
        [["Nur prüfen, ob die Benutzeroberfläche schön aussieht.","Datenschutz nicht prüfen, wenn der Anbieter bekannt ist.","Den Dienst freigeben, sobald ein kostenloser Testzugang verfügbar ist."],
         ["Nur die monatlichen Kosten betrachten.","Davon ausgehen, dass jeder Cloud-Dienst automatisch DSGVO-konform ist.","Alle Daten hochladen und erst danach den Vertrag lesen."],
         ["Die Verantwortung vollständig auf den Dienstleister übertragen und selbst nichts dokumentieren.","Nur prüfen, ob der Anbieter ein deutsches Logo verwendet.","Datenschutzprüfung ist bei externen IT-Diensten grundsätzlich unnötig." ]],
        "Verantwortliche bleiben für eine rechtmäßige und sichere Verarbeitung verantwortlich. Art. 28 und Art. 32 DSGVO verlangen bei passenden Konstellationen vertragliche und sicherheitsbezogene Prüfungen; bei Drittlandbezug kommen zusätzlich Art. 44 ff. in Betracht.",
        "Cloud-Auswahl ist nicht nur eine Preis- und Funktionsfrage.")

    return out[:188]


def _contexts_expert():
    return [
        {"org":"Musterhandel GmbH", "process":"CRM-Analyse", "data":"Kundenhistorien", "incident":"fehlgeleitete Kundenliste"},
        {"org":"Nordservice AG", "process":"Bewerberanalyse", "data":"Bewerbungsdaten", "incident":"offener Bewerberordner"},
        {"org":"Logistik Plus", "process":"Fahrer-App", "data":"Standort- und Fahrerdaten", "incident":"verlorenes Diensthandy"},
        {"org":"Bürozentrum West", "process":"Cloud-DMS", "data":"Vertrags- und Kontaktdaten", "incident":"falsch gesetzte Freigabe"},
        {"org":"Vertrieb Direkt", "process":"Marketingsegmentierung", "data":"Kundenprofile", "incident":"Export an falschen Empfänger"},
        {"org":"Personal Kontor", "process":"HR-System", "data":"Beschäftigtendaten", "incident":"unberechtigter Personalzugriff"},
        {"org":"Service Partner", "process":"Supportplattform", "data":"Ticket- und Kontaktdaten", "incident":"kompromittiertes Supportkonto"},
        {"org":"Einkauf Pro", "process":"Lieferantenportal", "data":"Ansprechpartnerdaten", "incident":"öffentliches Freigabelink"},
        {"org":"Finance Office", "process":"Abrechnungssystem", "data":"Rechnungs- und Bankdaten", "incident":"unverschlüsselter Laptopverlust"},
        {"org":"Projektwerk", "process":"Collaboration-Plattform", "data":"Projekt- und Personaldaten", "incident":"Phishing mit Zugangsdaten"},
    ]


def build_expert(choice):
    out=[]
    c=_contexts_expert()

    _add_family(out, choice, 1, "e", "Experte", "Rechtsgrundlagen & Rechenschaftspflicht", c,
        "{org} möchte im {process} zusätzliche {data} auswerten. Welche Vorgehensweise ist datenschutzrechtlich am belastbarsten?",
        "Vor Beginn Zweck, passende Rechtsgrundlage, Erforderlichkeit, Informationspflichten und Schutzmaßnahmen prüfen und die Entscheidung nachvollziehbar dokumentieren.",
        [["Erst alle verfügbaren Daten auswerten und die Rechtsgrundlage später suchen.","Eine pauschale Einwilligung für alle aktuellen und zukünftigen Zwecke als einzige Prüfung verwenden.","Die Auswertung allein deshalb für zulässig halten, weil sie technisch möglich ist."],
         ["Nur den wirtschaftlichen Nutzen dokumentieren; Datenschutzfragen können nach Projektende folgen.","Die Daten intern frei verwenden, weil keine externe Weitergabe erfolgt.","Eine alte Datenschutzerklärung unverändert auf jeden neuen Zweck übertragen."],
         ["Nur prüfen, ob genügend Speicherplatz vorhanden ist.","Den Zweck absichtlich sehr allgemein formulieren, damit jede spätere Nutzung umfasst ist.","Auf Dokumentation verzichten, weil die Rechenschaftspflicht nur Behörden betrifft." ]],
        "Art. 5 Abs. 2 DSGVO enthält die Rechenschaftspflicht. Zusammen mit Art. 5 und 6 müssen Zweck, Rechtsgrundlage, Erforderlichkeit und Schutzmaßnahmen vor der Verarbeitung tragfähig sein.",
        "Nicht erst verarbeiten und später begründen.")

    _add_family(out, choice, 2, "e", "Experte", "Zweckänderung", c,
        "{data} wurden für einen klaren ursprünglichen Zweck erhoben. {org} plant eine neue, nicht auf Einwilligung oder Unions-/Mitgliedstaatenrecht gestützte Weiterverarbeitung. Was ist nach Art. 6 Abs. 4 DSGVO zu prüfen?",
        "Ob der neue Zweck mit dem ursprünglichen Zweck vereinbar ist, unter anderem anhand von Zweckzusammenhang, Erhebungskontext, Datenart, möglichen Folgen und vorhandenen Garantien.",
        [["Nur ob die neue Nutzung günstiger ist als die alte.","Nur ob die Daten älter als ein Jahr sind.","Nichts; interne Zweckänderungen sind immer frei möglich."],
         ["Ausschließlich die Dateigröße.","Nur ob die betroffene Person noch Kundin ist.","Nur ob die Daten verschlüsselt gespeichert werden, unabhängig vom neuen Zweck."],
         ["Ob die Marketingabteilung den neuen Zweck interessant findet.","Ob der ursprüngliche Zweck schriftlich statt elektronisch dokumentiert war.","Nur die Zahl der Datensätze; Kontext und Folgen sind irrelevant." ]],
        "Art. 6 Abs. 4 DSGVO nennt Kriterien für die Vereinbarkeitsprüfung einer Zweckänderung, darunter Zusammenhang der Zwecke, Kontext, Datenart, Folgen und Garantien.",
        "Zweckänderung = strukturierte Vereinbarkeitsprüfung, nicht Bauchgefühl.")

    _add_family(out, choice, 3, "e", "Experte", "Datenpannen & Risikobewertung", c,
        "Bei {org} tritt der Vorfall '{incident}' auf. Welche erste fachliche Bewertung ist für Art. 33/34 DSGVO entscheidend?",
        "Welche personenbezogenen Daten betroffen sind, wie viele Personen betroffen sein können, ob Unbefugte Zugriff hatten, welche Schutzmaßnahmen wirkten und welches Risiko bzw. hohe Risiko für Betroffene entsteht.",
        [["Nur die Höhe des wirtschaftlichen Schadens für das Unternehmen.","Nur ob die Geschäftsführung den Vorfall peinlich findet.","Nur die Dateigröße der betroffenen Daten."],
         ["Nur ob bereits eine Beschwerde eingegangen ist.","Nur ob der Vorfall an einem Wochenende passiert ist.","Nur ob der Computer noch eingeschaltet ist."],
         ["Nur ob die IT-Abteilung den Fehler schnell beheben kann.","Nur ob das Unternehmen versichert ist.","Nur die Zahl der internen E-Mails zum Vorfall." ]],
        "Art. 33 und 34 DSGVO knüpfen Melde- und Benachrichtigungspflichten an das Risiko für Rechte und Freiheiten. Art, Sensibilität, Umfang, Schutzmaßnahmen und Folgen sind deshalb zentral.",
        "Das Risiko für Menschen ist maßgeblich, nicht nur der Aufwand für das Unternehmen.")

    _add_family(out, choice, 4, "e", "Experte", "Datenpannen & Betroffeneninformation", c,
        "Eine Datenpanne bei {org} führt voraussichtlich zu einem hohen Risiko. Welche Aussage zu Art. 34 DSGVO ist am präzisesten?",
        "Betroffene sind grundsätzlich unverzüglich in klarer und einfacher Sprache zu benachrichtigen; die DSGVO kennt aber Ausnahmen, etwa wenn wirksame Schutzmaßnahmen die Daten für Unbefugte unverständlich machen oder das hohe Risiko nachträglich beseitigt wurde.",
        [["Betroffene müssen bei hohem Risiko nie informiert werden, wenn die Aufsichtsbehörde informiert wurde.","Eine öffentliche Mitteilung ist in jedem Fall verboten.","Nur die IT-Abteilung darf von der Panne erfahren."],
         ["Die Benachrichtigung ist immer genau 72 Stunden nach der Behördenmeldung fällig.","Eine Information ist nur nötig, wenn ein Gericht sie anordnet.","Verschlüsselung ist für die Bewertung grundsätzlich irrelevant."],
         ["Betroffene werden nur informiert, wenn mehr als 10.000 Personen betroffen sind.","Eine Benachrichtigung kann beliebig lange aufgeschoben werden.","Art. 34 betrifft nur Papierakten." ]],
        "Art. 34 DSGVO knüpft die Betroffeneninformation an ein hohes Risiko und enthält Ausnahmen, etwa bei wirksamen Schutzmaßnahmen oder wenn das hohe Risiko nicht mehr besteht.",
        "Art. 34 ist risikobasiert und kennt Ausnahmen.")

    _add_family(out, choice, 5, "e", "Experte", "Auftragsverarbeitung", c,
        "Ein Auftragsverarbeiter von {org} beginnt, {data} entgegen der Weisung für eigene Zwecke zu nutzen. Welche Aussage trifft Art. 28 Abs. 10 DSGVO am besten?",
        "Soweit der Auftragsverarbeiter Zwecke und Mittel dieser unzulässigen Verarbeitung selbst bestimmt, gilt er insoweit als Verantwortlicher für diese Verarbeitung.",
        [["Die Verarbeitung bleibt immer reine Auftragsverarbeitung, unabhängig von eigenen Zwecken.","Nur {org} kann datenschutzrechtlich verantwortlich sein; der Dienstleister nie.","Eigenzwecke des Auftragsverarbeiters sind zulässig, solange sie intern bleiben."],
         ["Der Dienstleister wird automatisch zur Aufsichtsbehörde.","Eigene Zwecke sind nur bei mehr als 1.000 Datensätzen relevant.","Die Rollen ändern sich ausschließlich durch eine neue Rechnung."],
         ["Art. 28 erlaubt dem Auftragsverarbeiter freie Zweitnutzung.","Eine Rollenänderung ist bei Cloud-Diensten ausgeschlossen.","Nur die betroffene Person entscheidet, wer Verantwortlicher ist." ]],
        "Art. 28 Abs. 10 DSGVO ordnet an, dass ein Auftragsverarbeiter insoweit als Verantwortlicher gilt, wie er unter Verstoß gegen die Verordnung Zwecke und Mittel selbst bestimmt.",
        "Wer aus der Weisungsrolle ausbricht und eigene Zwecke bestimmt, verändert seine Rolle.")

    _add_family(out, choice, 6, "e", "Experte", "Gemeinsame Verantwortlichkeit", c,
        "{org} und ein Partner bestimmen gemeinsam Zwecke und wesentliche Mittel einer Verarbeitung von {data}. Welche Regel ist besonders relevant?",
        "Art. 26 DSGVO: Die gemeinsam Verantwortlichen müssen in transparenter Form festlegen, wer welche Verpflichtungen erfüllt, insbesondere hinsichtlich Betroffenenrechten und Informationspflichten.",
        [["Art. 28 DSGVO macht automatisch einen der beiden zum weisungsgebundenen Auftragsverarbeiter, auch wenn beide Zwecke bestimmen.","Gemeinsame Verantwortlichkeit ist nach der DSGVO verboten.","Eine Rollenklärung ist unnötig, solange beide Firmen dieselbe Software verwenden."],
         ["Nur der größere Partner trägt Pflichten; eine Vereinbarung ist überflüssig.","Die Betroffenenrechte entfallen bei gemeinsamer Verantwortlichkeit.","Gemeinsame Verantwortlichkeit bedeutet, dass keine Stelle mehr verantwortlich ist."],
         ["Art. 26 gilt nur für Behörden.","Die Partner dürfen die Zuständigkeiten geheim halten.","Nur technische Administratoren müssen sich abstimmen, nicht die Verantwortlichen." ]],
        "Art. 26 DSGVO regelt die gemeinsame Verantwortlichkeit und verlangt eine transparente Festlegung der jeweiligen Zuständigkeiten.",
        "Gemeinsam Zwecke/Mittel bestimmen ≠ automatisch Auftragsverarbeitung.")

    _add_family(out, choice, 7, "e", "Experte", "Datenschutz-Folgenabschätzung", c,
        "{org} plant im {process} eine neue Verarbeitung, die voraussichtlich ein hohes Risiko erzeugt. Welche Reihenfolge ist fachlich richtig?",
        "Vor Beginn der Verarbeitung eine DSFA nach Art. 35 durchführen; verbleibt trotz Maßnahmen ein hohes Risiko, ist vor der Verarbeitung die Aufsichtsbehörde nach Art. 36 zu konsultieren.",
        [["Verarbeitung vollständig starten und erst nach einem Jahr eine DSFA nachholen.","Nur eine Datenschutzinformation veröffentlichen; eine Risikoprüfung ist dann nicht nötig.","Die Aufsichtsbehörde erst nach einer Datenpanne konsultieren, unabhängig vom vorhersehbaren Risiko."],
         ["Zuerst alle Daten sammeln und anschließend entscheiden, ob eine DSFA sinnvoll wäre.","Eine DSFA darf erst nach Abschluss des Projekts erfolgen.","Bei technischen Schutzmaßnahmen ist eine DSFA grundsätzlich ausgeschlossen."],
         ["Eine DSFA ersetzt jede Rechtsgrundlage.","Vorherige Konsultation ist immer Pflicht, auch wenn nach Maßnahmen kein hohes Restrisiko besteht.","Art. 35 gilt nur bei Papierverarbeitung." ]],
        "Art. 35 DSGVO verlangt die DSFA vor der risikoreichen Verarbeitung. Art. 36 sieht eine vorherige Konsultation vor, wenn trotz geplanter Maßnahmen ein hohes Risiko verbleibt.",
        "Risikofolgen abschätzen, bevor das System produktiv läuft.")

    _add_family(out, choice, 8, "e", "Experte", "Datenschutzbeauftragte", c,
        "Die Datenschutzbeauftragte von {org} soll zusätzlich eine Funktion übernehmen, in der sie selbst Zwecke und Mittel zentraler Verarbeitungen bestimmt. Was ist kritisch?",
        "Ein möglicher Interessenkonflikt: Andere Aufgaben sind zulässig, dürfen aber nach Art. 38 Abs. 6 DSGVO nicht zu einem Interessenkonflikt führen.",
        [["Datenschutzbeauftragte dürfen grundsätzlich niemals andere Aufgaben haben.","Interessenkonflikte sind unerheblich, solange die Funktion gut bezahlt ist.","Art. 38 verlangt ausdrücklich, dass Datenschutzbeauftragte alle Verarbeitungszwecke selbst bestimmen."],
         ["Ein Interessenkonflikt ist nur bei externen Datenschutzbeauftragten möglich.","Die DSGVO verlangt, dass der Datenschutzbeauftragte zugleich Geschäftsführer sein muss.","Zusätzliche Aufgaben sind immer automatisch mit Art. 38 vereinbar."],
         ["Nur die Zahl der Mitarbeitenden ist für den Interessenkonflikt relevant.","Der Datenschutzbeauftragte darf Weisungen zur Bewertung einzelner Datenschutzfragen erhalten.","Ein Interessenkonflikt kann durch einen neuen Jobtitel ausgeschlossen werden." ]],
        "Art. 38 Abs. 3 und 6 DSGVO schützt die Unabhängigkeit der Datenschutzbeauftragten und verlangt, dass andere Aufgaben nicht zu Interessenkonflikten führen.",
        "Kontrollieren und zugleich selbst über dieselbe Verarbeitung entscheiden kann kollidieren.")

    _add_family(out, choice, 9, "e", "Experte", "Beschäftigtendaten", c,
        "{org} vermutet eine Straftat eines Beschäftigten und möchte Beschäftigtendaten zur Aufklärung auswerten. Welche Anforderung nennt § 26 Abs. 1 BDSG besonders?",
        "Es müssen zu dokumentierende tatsächliche Anhaltspunkte für den Verdacht bestehen; die Verarbeitung muss erforderlich sein und darf nicht unverhältnismäßig in schutzwürdige Interessen eingreifen.",
        [["Ein bloßes Gerücht reicht immer für eine unbegrenzte Überwachung.","Bei Straftatverdacht gelten Datenschutzregeln nicht mehr.","Der Arbeitgeber darf ohne Anlass sämtliche private Kommunikation aller Beschäftigten auswerten."],
         ["Nur die Höhe des möglichen Schadens ist relevant; tatsächliche Anhaltspunkte sind nicht nötig.","Eine Dokumentation des Verdachts ist ausdrücklich verboten.","Verhältnismäßigkeit spielt bei internen Ermittlungen keine Rolle."],
         ["Jede anonyme Behauptung verpflichtet automatisch zur Vollüberwachung.","Es darf nur auf Einwilligung des Verdächtigen verarbeitet werden.","§ 26 BDSG erlaubt zur Aufklärung jede technisch mögliche Maßnahme." ]],
        "§ 26 Abs. 1 BDSG nennt für die Aufdeckung von Straftaten dokumentierte tatsächliche Anhaltspunkte, Erforderlichkeit und eine Verhältnismäßigkeitsabwägung.",
        "Verdacht muss konkret und dokumentierbar sein; Maßnahmen müssen verhältnismäßig bleiben.")

    _add_family(out, choice, 10, "e", "Experte", "Besondere Kategorien & Beschäftigung", c,
        "{org} verarbeitet im HR-System Gesundheitsdaten von Beschäftigten. Welche Aussage ist am präzisesten?",
        "Gesundheitsdaten gehören zu Art. 9 DSGVO; im Beschäftigungskontext kann eine Verarbeitung unter den besonderen Voraussetzungen von Art. 9 Abs. 2 und § 26 Abs. 3 BDSG zulässig sein, wenn sie erforderlich und rechtlich gedeckt ist.",
        [["Gesundheitsdaten sind normale Kontaktdaten und brauchen keine besondere Prüfung.","§ 26 BDSG erlaubt Gesundheitsdaten jederzeit für beliebige Personalzwecke.","Eine Speicherung ist immer verboten, selbst wenn eine arbeitsrechtliche Pflicht sie erfordert."],
         ["Nur Einwilligung kann Gesundheitsdaten im Arbeitsverhältnis rechtfertigen.","Art. 9 gilt nur für Krankenhäuser, nicht für Arbeitgeber.","Gesundheitsdaten dürfen offen im Teamordner gespeichert werden, wenn alle Beschäftigten Zugriff haben."],
         ["Besondere Kategorien verlieren ihren Schutz, sobald sie in einer Personalakte stehen.","Eine gesetzliche Pflicht ist für Art. 9 grundsätzlich irrelevant.","Gesundheitsdaten dürfen immer für Leistungsbewertungen wiederverwendet werden." ]],
        "Art. 9 DSGVO schützt Gesundheitsdaten besonders. § 26 Abs. 3 BDSG enthält eine beschäftigungsbezogene Öffnung unter strengen Voraussetzungen, insbesondere Erforderlichkeit und Interessenabwägung.",
        "Bei besonderen Kategorien braucht es zusätzlich zur allgemeinen Verarbeitung eine spezifische Erlaubnislage.")

    _add_family(out, choice, 11, "e", "Experte", "Auskunft & Rechte Dritter", c,
        "Eine Person verlangt nach Art. 15 DSGVO eine Kopie ihrer Daten. In denselben Dokumenten stehen vertrauliche personenbezogene Daten Dritter. Was ist zu beachten?",
        "Das Auskunfts- und Kopierecht ist zu erfüllen, darf aber nach Art. 15 Abs. 4 DSGVO die Rechte und Freiheiten anderer Personen nicht beeinträchtigen; Inhalte müssen gegebenenfalls sachgerecht getrennt oder geschwärzt werden.",
        [["Der Antrag ist automatisch vollständig abzulehnen, sobald irgendwo Daten Dritter vorkommen.","Daten Dritter müssen immer ungeschwärzt mit herausgegeben werden.","Art. 15 Abs. 4 erlaubt es, jeden Auskunftsantrag ohne Begründung abzulehnen."],
         ["Rechte Dritter spielen bei Auskunft nie eine Rolle.","Die betroffene Person erhält stattdessen den vollständigen Datenbestand des Unternehmens.","Nur Papierdokumente dürfen geschwärzt werden."],
         ["Die Rechte Dritter führen automatisch zur Löschung der angefragten Daten.","Eine Kopie ist bei digitalen Daten grundsätzlich ausgeschlossen.","Der Antragsteller muss auf alle Rechte verzichten, sobald Dritte erwähnt werden." ]],
        "Art. 15 Abs. 4 DSGVO schützt Rechte und Freiheiten anderer Personen. Das erfordert eine konkrete Abwägung und gegebenenfalls Trennung oder Schwärzung, nicht pauschale Verweigerung.",
        "Auskunft ermöglichen, ohne Dritte unnötig offenzulegen.")

    _add_family(out, choice, 12, "e", "Experte", "Löschung & Aufbewahrung", c,
        "{org} muss bestimmte {data} noch aufgrund einer gesetzlichen Pflicht aufbewahren, obwohl der ursprüngliche operative Zweck beendet ist. Welche Vorgehensweise ist datenschutzrechtlich am saubersten?",
        "Nur die erforderlichen Daten für die gesetzlich gebotene Dauer und den gebotenen Zweck weiter vorhalten, Zugriffe beschränken und nach Wegfall der Pflicht löschen, sofern keine andere Rechtsgrundlage greift.",
        [["Die Daten wegen der Aufbewahrungspflicht nun für beliebige Marketing- und Analysezwecke nutzen.","Alle Daten des Vorgangs auf unbestimmte Zeit speichern, weil ein Teil aufbewahrungspflichtig ist.","Die gesetzliche Pflicht ignorieren und alles sofort löschen."],
         ["Aufbewahrungspflicht bedeutet automatisch öffentliche Zugänglichkeit.","Nur die Dateinamen aufbewahren, unabhängig von der gesetzlichen Anforderung.","Nach Ablauf der Pflicht ist eine weitere Speicherung stets erlaubt, ohne neuen Zweck."],
         ["Die Daten in einen frei zugänglichen Archivordner verschieben.","Aufbewahrung und Zweckbindung haben nichts miteinander zu tun.","Die Löschung darf nie automatisiert vorgesehen werden." ]],
        "Art. 5 DSGVO verlangt Zweckbindung, Datenminimierung und Speicherbegrenzung. Art. 17 Abs. 3 berücksichtigt rechtliche Aufbewahrungspflichten, erlaubt aber keine beliebige Weiterverwendung.",
        "Aufbewahren müssen ≠ frei weiterverwenden dürfen.")

    _add_family(out, choice, 13, "e", "Experte", "E-Mail & Datenpannen", c,
        "Bei {org} wurde eine E-Mail mit {data} an einen falschen externen Empfänger gesendet. Der Empfänger bestätigt sofort glaubhaft die ungelesene Löschung. Wie ist das einzuordnen?",
        "Der Vorfall bleibt eine Datenschutzverletzung und ist zu dokumentieren; die bestätigte Löschung ist ein risikomindernder Faktor für die Bewertung, ob eine Meldung nach Art. 33 oder Information nach Art. 34 erforderlich ist.",
        [["Durch die Löschbestätigung hat es rechtlich nie eine Datenschutzverletzung gegeben.","Eine Meldung an die Aufsichtsbehörde ist automatisch immer Pflicht, unabhängig von Risiko und Datenart.","Der Vorfall muss nicht dokumentiert werden, wenn der Empfänger höflich reagiert."],
         ["Die Risikobewertung darf die Reaktion des Empfängers niemals berücksichtigen.","Die E-Mail muss zur Beweissicherung noch einmal gesendet werden.","Nur absichtliche Fehlversendungen sind Datenschutzverletzungen."],
         ["Eine Datenschutzverletzung liegt nur vor, wenn die Daten veröffentlicht wurden.","Die Art der betroffenen Daten ist für die Risikobewertung irrelevant.","Interne Dokumentation ist nur bei meldepflichtigen Vorfällen erlaubt." ]],
        "Art. 4 Nr. 12 DSGVO erfasst auch unbeabsichtigte unbefugte Offenlegung. Art. 33 Abs. 5 verlangt Dokumentation von Verletzungen; Risikominderungen beeinflussen die Meldebewertung.",
        "Vorfall ja – Meldepflicht hängt vom Risiko ab.")

    _add_family(out, choice, 14, "e", "Experte", "Technische & organisatorische Maßnahmen", c,
        "{org} verarbeitet besonders sensible {data}. Welche Kombination entspricht dem risikobasierten Ansatz von Art. 32 DSGVO am ehesten?",
        "Rollenbasierte Zugriffe, starke Authentisierung, geeignete Verschlüsselung/Pseudonymisierung, Protokollierung, Wiederherstellbarkeit und regelmäßige Wirksamkeitsprüfungen nach Risiko.",
        [["Ein einziges gemeinsames Passwort und keine Protokollierung.","Nur ein Virenscanner, unabhängig von Zugriffen und Wiederherstellung.","Ausschließlich eine Papier-Richtlinie ohne technische Umsetzung."],
         ["Alle Daten für alle Mitarbeitenden sichtbar machen, damit Vertretungen einfacher sind.","Backups ohne Wiederherstellungstest und ohne Zugriffsschutz.","Sicherheitsmaßnahmen nur nach einer Panne einführen."],
         ["Nur Verschlüsselung verwenden und alle organisatorischen Maßnahmen weglassen.","Zugriffe nie protokollieren, weil Kontrolle grundsätzlich unzulässig ist.","Sicherheitsupdates dauerhaft verschieben, um Systemänderungen zu vermeiden." ]],
        "Art. 32 DSGVO nennt unter anderem Pseudonymisierung/Verschlüsselung, Vertraulichkeit, Integrität, Verfügbarkeit, Wiederherstellbarkeit und regelmäßige Überprüfung der Wirksamkeit.",
        "Sicherheit ist ein System aus mehreren risikoadäquaten Maßnahmen.")

    _add_family(out, choice, 15, "e", "Experte", "IT-Sicherheitsvorfälle", c,
        "Nach einem Phishing-Angriff auf {org} wurden Zugangsdaten zum {process} eingegeben. Was ist fachlich zuerst zu koordinieren?",
        "Konto absichern bzw. Zugang sperren, kompromittierte Zugangsdaten ändern, Sitzungen/Tokens prüfen, Vorfall intern melden, Logs und mögliche Datenzugriffe bewerten und daraus Datenschutz- und Sicherheitsmaßnahmen ableiten.",
        [["Nur die Phishing-Mail löschen und ansonsten nichts tun.","Den kompromittierten Zugang weiterverwenden, bis tatsächlich ein Schaden sichtbar ist.","Alle Logs sofort löschen, damit keine sensiblen Informationen mehr vorhanden sind."],
         ["Nur das Passwort des privaten E-Mail-Kontos ändern.","Den Vorfall ausschließlich dem Absender der Phishing-Mail melden.","Die interne Meldung vermeiden, um den Vorfall klein zu halten."],
         ["Erst nach mehreren Tagen prüfen, ob noch aktive Sitzungen bestehen.","Den betroffenen Account mit Kolleginnen und Kollegen teilen, damit Arbeit weitergeht.","Nur einen Screenshot speichern; technische Sperrmaßnahmen sind nicht nötig." ]],
        "Kompromittierte Zugangsdaten erfordern schnelle Eindämmung und Untersuchung. Art. 32 DSGVO verlangt angemessene Sicherheit; mögliche Datenzugriffe müssen zudem auf eine Datenschutzverletzung bewertet werden.",
        "Zuerst eindämmen, dann Reichweite und Datenschutzfolgen bewerten.")

    _add_family(out, choice, 16, "e", "Experte", "Drittlandübermittlung", c,
        "{org} möchte einen Dienst nutzen, bei dem {data} in einem Staat außerhalb EU/EWR verarbeitet werden. Welche Aussage ist richtig?",
        "Neben einer Rechtsgrundlage und den übrigen DSGVO-Pflichten sind für die Drittlandübermittlung die besonderen Voraussetzungen der Art. 44 ff. DSGVO zu prüfen.",
        [["Drittlandübermittlungen sind immer automatisch erlaubt, wenn der Dienst günstiger ist.","Art. 44 ff. gelten nur für Papierakten.","Eine Auftragsverarbeitungsvereinbarung allein macht jede Drittlandübermittlung automatisch zulässig."],
         ["Außerhalb der EU gilt die DSGVO nie, daher ist keine Prüfung erforderlich.","Nur die Sprache des Vertrags entscheidet über die Zulässigkeit.","Eine Einwilligung der IT-Abteilung ersetzt alle Anforderungen der Art. 44 ff."],
         ["Drittländer sind grundsätzlich vollständig verboten.","Ein Serverstandort außerhalb des EWR ist rechtlich dasselbe wie ein Standort im Nachbarbüro.","Nur die Dateigröße bestimmt, ob Art. 44 ff. anzuwenden sind." ]],
        "Kapitel V der DSGVO (Art. 44 ff.) enthält zusätzliche Anforderungen für Übermittlungen personenbezogener Daten an Drittländer oder internationale Organisationen.",
        "Bei Drittlandbezug kommt eine zusätzliche Prüfschicht hinzu.")

    _add_family(out, choice, 17, "e", "Experte", "Datenminimierung & Profilbildung", c,
        "Für {process} möchte {org} vorsorglich sämtliche vorhandenen {data} und zusätzliche private Merkmale zusammenführen, obwohl nur ein kleiner Teil für den definierten Zweck benötigt wird. Was ist der zentrale Einwand?",
        "Das widerspricht insbesondere Datenminimierung und Zweckbindung; Umfang und Merkmale müssen auf den legitimen, rechtlich getragenen Zweck begrenzt werden.",
        [["Die DSGVO bevorzugt grundsätzlich möglichst große Datenmengen.","Datenminimierung gilt nur für Papierunterlagen.","Einmal vorhandene Daten dürfen ohne neue Prüfung immer kombiniert werden."],
         ["Nur Speicherplatzkosten sind relevant.","Zusätzliche private Merkmale sind immer erlaubt, solange sie nicht angezeigt werden.","Zweckbindung gilt nur bei Weitergabe an Behörden."],
         ["Je mehr Daten verarbeitet werden, desto leichter ist die Rechtmäßigkeit nachzuweisen.","Interne Datenzusammenführung fällt generell nicht unter die DSGVO.","Datenminimierung bedeutet nur, Dateien zu komprimieren." ]],
        "Art. 5 Abs. 1 lit. b und c DSGVO verlangen Zweckbindung und Datenminimierung. Eine technisch mögliche umfassende Profilbildung braucht eine tragfähige Notwendigkeit und Rechtsgrundlage.",
        "Mehr Daten sind nicht automatisch besser oder zulässiger.")

    _add_family(out, choice, 18, "e", "Experte", "Auftragsverarbeitung & Datenpannen", c,
        "Ein Auftragsverarbeiter von {org} entdeckt einen Sicherheitsvorfall mit {data}. Welche Pflicht nennt Art. 33 Abs. 2 DSGVO?",
        "Der Auftragsverarbeiter muss den Verantwortlichen nach Bekanntwerden der Verletzung unverzüglich informieren.",
        [["Er darf den Vorfall bis zum Monatsende intern behalten.","Er informiert ausschließlich die betroffenen Personen und nicht den Verantwortlichen.","Eine Information ist erst nötig, wenn ein Gericht sie anordnet."],
         ["Er entscheidet allein, ob der Verantwortliche von der Panne erfahren soll.","Er meldet nur, wenn mindestens 1.000 Datensätze betroffen sind.","Art. 33 Abs. 2 gilt nur für Papierakten."],
         ["Er muss zuerst 72 Stunden warten.","Nur der Unterauftragnehmer darf informieren.","Eine Meldung an den Verantwortlichen ist bei verschlüsselten Daten immer verboten." ]],
        "Art. 33 Abs. 2 DSGVO verpflichtet den Auftragsverarbeiter zur unverzüglichen Unterrichtung des Verantwortlichen. Dieser muss dann seine eigenen Meldepflichten bewerten.",
        "Der Verantwortliche braucht die Information schnell, um seine 72-Stunden-Prüfung durchführen zu können.")

    _add_family(out, choice, 19, "e", "Experte", "Datenschutzorganisation", c,
        "{org} möchte nachweisen, dass Datenschutz im {process} dauerhaft funktioniert. Welche Kombination ist am überzeugendsten?",
        "Klare Verantwortlichkeiten, dokumentierte Rechtsgrundlagen/Zwecke, Verzeichnis relevanter Verarbeitungstätigkeiten, geregelte Betroffenenprozesse, Schulungen, technische und organisatorische Maßnahmen, Incident-Prozess und regelmäßige Kontrollen.",
        [["Nur eine einmal unterschriebene Datenschutzerklärung ohne weitere Prozesse.","Nur ein Passwortwechsel pro Jahr, unabhängig von Risiken.","Datenschutz ausschließlich an eine einzelne Person delegieren und sonst nicht dokumentieren."],
         ["Nur eine Firewall und keine organisatorischen Regeln.","Nur eine jährliche Rundmail ohne technische Kontrollen.","Ausschließlich Verträge mit Dienstleistern, aber keine eigenen Prozesse."],
         ["Nur ein Hinweis im Impressum.","Nur eine Versicherung gegen Cyberrisiken.","Datenschutz erst bearbeiten, wenn eine Aufsichtsbehörde anfragt." ]],
        "Die DSGVO verbindet Rechenschaftspflicht, Transparenz, Betroffenenrechte, Sicherheit, Verantwortlichkeiten und dokumentierte Prozesse. Nachhaltige Compliance besteht aus mehreren abgestimmten Elementen.",
        "Datenschutz ist ein Managementprozess, kein einzelnes Dokument.")

    return out[:188]


def _exam_cases(level: str):
    if level == "Anfänger":
        return [
            ("Personenbezogene Daten", "Eine Kollegin sagt: 'Eine geschäftliche E-Mail-Adresse ist nie personenbezogen.' Wie bewertest du das?", "Die Aussage ist falsch; eine E-Mail-Adresse kann personenbezogen sein, wenn sie einer natürlichen Person zugeordnet werden kann.", ["Die Aussage ist immer richtig.","E-Mail-Adressen sind nur bei Privatpersonen personenbezogen.","Erst zusammen mit einer Bankverbindung entsteht Personenbezug."], "Art. 4 Nr. 1 DSGVO stellt auf Identifizierbarkeit ab."),
            ("Datenminimierung", "Für einen Newsletter soll zusätzlich ohne erkennbaren Zweck das Geburtsdatum verpflichtend abgefragt werden. Welche Grundregel ist betroffen?", "Datenminimierung: Es sollen nur für den Zweck erforderliche Daten verarbeitet werden.", ["Speicherbegrenzung bedeutet, möglichst viele Daten zu erfassen.","Es gibt keine datenschutzrechtliche Grundregel dazu.","Nur die Dateigröße ist relevant."], "Art. 5 Abs. 1 lit. c DSGVO verlangt Datenminimierung."),
            ("E-Mail & Kommunikation", "Du möchtest 50 externe Empfänger über eine Terminänderung informieren; ihre Adressen sollen voreinander verborgen bleiben. Was ist typischerweise passend?", "Bcc verwenden oder einen dafür vorgesehenen Verteildienst nutzen.", ["Alle offen in Cc setzen.","Alle Adressen in den Betreff schreiben.","Die Empfängerliste als Anhang mitsenden."], "Vertraulichkeit und Datenminimierung sprechen gegen unnötige Offenlegung fremder Adressen."),
            ("Zugriffsschutz", "Auf einem gemeinsam zugänglichen Drucker liegt eine Personalliste. Was tust du?", "Die Unterlage sichern und nach dem vorgesehenen internen Datenschutzprozess weitergeben bzw. melden.", ["Liegen lassen.","Fotografieren und in die Teamgruppe schicken.","In den offenen Papierkorb werfen."], "Personenbezogene Daten müssen vor unbefugter Einsicht geschützt werden."),
            ("Phishing & E-Mail-Sicherheit", "Eine E-Mail fordert dich überraschend auf, dein Firmenpasswort über einen Link zu bestätigen. Was ist richtig?", "Nicht über den Link anmelden; Nachricht und Absender über einen sicheren Kanal prüfen und internen Sicherheitsweg nutzen.", ["Passwort sofort eingeben, damit das Konto nicht gesperrt wird.","Den Link an alle Kollegen schicken.","Virenschutz ausschalten, falls die Seite blockiert wird."], "Phishing versucht häufig, Zugangsdaten über täuschende Links abzugreifen."),
            ("Betroffenenrechte", "Ein Kunde teilt mit, seine gespeicherte Adresse sei falsch. Welche Reaktion passt?", "Die Berichtigung nach Art. 16 DSGVO prüfen und unrichtige Daten korrigieren.", ["Nichts ändern, weil gespeicherte Daten nie geändert werden dürfen.","Alle Kundendaten löschen, ohne den Vorgang zu prüfen.","Den Kunden auf ein neues Kundenkonto verweisen."], "Art. 16 DSGVO regelt die Berichtigung unrichtiger personenbezogener Daten."),
            ("Datenpannen", "Du sendest eine Kundenliste versehentlich an einen falschen Empfänger. Was ist zuerst wichtig?", "Den Vorfall unverzüglich intern melden, damit Risiko und weitere Pflichten bewertet werden können.", ["Nur die gesendete Nachricht im eigenen Postfach löschen.","Nichts tun, solange niemand anruft.","Die Liste erneut an denselben Empfänger senden."], "Fehlversand kann eine Datenschutzverletzung sein; schnelle interne Bewertung ist nötig."),
            ("Passwörter & Konten", "Ein Kollege bittet um dein Passwort, weil sein Konto gesperrt ist. Was ist richtig?", "Passwort nicht weitergeben und den vorgesehenen Supportweg nutzen.", ["Passwort kurz nennen und später ändern.","Passwort auf einen Zettel schreiben.","Gemeinsam dauerhaft dasselbe Konto nutzen."], "Persönliche Zugangsdaten sollten nicht geteilt werden; das BSI empfiehlt eigene sichere Passwörter."),
            ("Löschung & Aufbewahrung", "Eine Kundin verlangt Löschung ihrer Daten. Muss immer sofort ausnahmslos alles gelöscht werden?", "Nein. Das Löschungsrecht ist zu prüfen; gesetzliche Aufbewahrungspflichten oder andere Ausnahmen können entgegenstehen.", ["Ja, immer ohne jede Prüfung.","Nein, weil es überhaupt kein Löschungsrecht gibt.","Nur Papierdaten können gelöscht werden."], "Art. 17 DSGVO enthält sowohl Löschgründe als auch Ausnahmen."),
            ("Besondere Kategorien personenbezogener Daten", "Welche Angabe ist besonders sensibel im Sinne des Art. 9 DSGVO?", "Eine ärztliche Diagnose.", ["Eine allgemeine Produktnummer.","Die Öffnungszeit des Büros.","Die Nummer eines Besprechungsraums."], "Gesundheitsdaten gehören zu den besonderen Kategorien des Art. 9 DSGVO."),
            ("Zugriffsrechte", "Eine Praktikantin möchte aus Interesse eine Personalakte ansehen, braucht sie aber nicht für ihre Aufgabe. Was ist richtig?", "Keinen Zugriff gewähren; personenbezogene Daten sollen nur für berechtigte Aufgaben zugänglich sein.", ["Zugriff gewähren, weil sie im Unternehmen arbeitet.","Akte öffentlich im Teamordner ablegen.","Nur den Dateinamen ändern und Zugriff geben."], "Art. 5 Abs. 1 lit. f und Art. 32 sprechen für aufgabenbezogene Zugriffsrechte."),
            ("Sichere Übermittlung", "Du sollst sensible Daten an eine berechtigte Stelle senden. Welche Vorbereitung ist sinnvoll?", "Empfänger/Berechtigung prüfen und den vorgesehenen sicheren Übertragungsweg verwenden.", ["Private Cloud ohne Zugriffsschutz nutzen.","An mehrere mögliche Empfänger gleichzeitig senden.","Sensible Angaben in den Betreff schreiben."], "Art. 32 verlangt angemessene Sicherheit auch bei der Übermittlung."),
        ]
    if level == "Fortgeschritten":
        return [
            ("Auftragsverarbeitung", "Ein externer Anbieter hostet ein CRM und verarbeitet Kundendaten nur nach Weisung. Was ist vor Einsatz zentral?", "Rolle und Eignung prüfen und eine Regelung nach Art. 28 DSGVO abschließen, soweit Auftragsverarbeitung vorliegt.", ["Nur den Preis prüfen.","Keine Vereinbarung, solange Server in Deutschland stehen.","Den Anbieter die Daten für eigene Werbung verwenden lassen."], "Art. 28 regelt Auftragsverarbeitung und verlangt hinreichende Garantien."),
            ("Betroffenenrechte", "Ein Auskunftsantrag geht am 3. Mai ein. Welche Grundregel gilt zur Antwortfrist?", "Unverzüglich, grundsätzlich innerhalb eines Monats nach Eingang; Verlängerungen sind nur unter den gesetzlichen Voraussetzungen möglich.", ["Immer binnen 72 Stunden.","Erst nach drei Monaten.","Keine Frist."], "Art. 12 Abs. 3 DSGVO enthält die Monatsfrist."),
            ("Beschäftigtendaten", "Für die Lohnabrechnung werden erforderliche Beschäftigtendaten verarbeitet. Welche Grundlage ist im deutschen Beschäftigungskontext besonders zu prüfen?", "§ 26 BDSG in Verbindung mit den einschlägigen DSGVO-Regeln und weiteren gesetzlichen Pflichten.", ["Nur eine freiwillige Werbeeinwilligung.","Keine Datenschutzregel, weil es interne Daten sind.","Ausschließlich das Handelsgesetzbuch."], "§ 26 BDSG regelt Datenverarbeitung für Zwecke des Beschäftigungsverhältnisses."),
            ("Datenpannen", "Ein unverschlüsselter Laptop mit Kundendaten wird gestohlen. Welche Frist ist bei einer meldepflichtigen Verletzung besonders relevant?", "Meldung an die zuständige Aufsichtsbehörde unverzüglich und möglichst binnen 72 Stunden nach Bekanntwerden.", ["Ein Jahr.","Genau sieben Werktage.","Keine Frist."], "Art. 33 Abs. 1 DSGVO enthält die 72-Stunden-Regel."),
            ("Datenschutz-Folgenabschätzung", "Ein neues System soll großflächig besonders sensible Daten auswerten und erzeugt voraussichtlich hohe Risiken. Was ist vor Start zu prüfen?", "Eine Datenschutz-Folgenabschätzung nach Art. 35 DSGVO.", ["Nur eine neue Firmenfarbe.","Ausschließlich ein längeres Passwort.","Erst nach einer Panne über Risiken nachdenken."], "Art. 35 knüpft die DSFA an voraussichtlich hohe Risiken."),
            ("Pseudonymisierung & Anonymisierung", "Namen werden durch Codes ersetzt; eine Zuordnungstabelle bleibt vorhanden. Was ist das?", "Pseudonymisierung; die Daten bleiben grundsätzlich personenbezogen.", ["Vollständige Anonymisierung.","Keine Verarbeitung mehr.","Automatisch öffentliche Daten."], "Art. 4 Nr. 5 definiert Pseudonymisierung."),
            ("Datenschutzbeauftragte", "Ein privates Unternehmen beschäftigt regelmäßig 24 Personen ständig mit automatisierter Verarbeitung personenbezogener Daten. Welche deutsche Zusatzregel ist relevant?", "§ 38 BDSG sieht in dieser Konstellation grundsätzlich eine Benennungspflicht für einen Datenschutzbeauftragten vor.", ["Die Grenze liegt bei 500 Personen.","§ 38 gilt nur für Behörden.","Die Zahl ist grundsätzlich irrelevant und es gibt nie eine Benennungspflicht."], "§ 38 Abs. 1 BDSG nennt mindestens 20 Personen als eine relevante Schwelle."),
            ("Datenschutz durch Technikgestaltung", "Ein neues System zeigt standardmäßig nur die Daten, die die jeweilige Rolle benötigt. Welches Prinzip passt?", "Datenschutzfreundliche Voreinstellungen und Datenschutz durch Technikgestaltung nach Art. 25 DSGVO.", ["Nur Datenübertragbarkeit.","Nur die 72-Stunden-Regel.","Die Pflicht, alle Daten für alle sichtbar zu machen."], "Art. 25 DSGVO fordert Privacy by Design und Privacy by Default."),
            ("Betroffenenrechte", "Eine Person widerspricht der Verarbeitung ihrer Daten für Direktwerbung. Was ist zu tun?", "Die Daten dürfen nicht mehr für Direktwerbung verarbeitet werden.", ["Werbung noch fünfmal fortsetzen.","Widerspruch nur bei Papierwerbung beachten.","Widerspruch ohne Prüfung ignorieren."], "Art. 21 Abs. 2 und 3 DSGVO schützt den Widerspruch gegen Direktwerbung besonders."),
            ("Technische & organisatorische Maßnahmen", "Wie wird nach Art. 32 das angemessene Schutzniveau bestimmt?", "Risikoorientiert unter Berücksichtigung von Stand der Technik, Verarbeitung und möglichen Folgen für Betroffene.", ["Nur nach dem niedrigsten Preis.","Mit einer festen identischen Maßnahme für jedes System.","Nur nach Anzahl der Dateien."], "Art. 32 verlangt risikoadäquate technische und organisatorische Maßnahmen."),
            ("Dienstleister & Cloud", "Ein Cloud-Dienst verarbeitet Kundendaten und nutzt Server außerhalb EU/EWR. Was kommt zusätzlich in den Blick?", "Neben den allgemeinen DSGVO-Pflichten insbesondere Art. 44 ff. zu Drittlandübermittlungen.", ["Keine zusätzlichen Regeln.","Nur die Farbe des Serverraums.","Art. 44 ff. gelten ausschließlich für Papierakten."], "Drittlandübermittlungen unterliegen Kapitel V der DSGVO."),
            ("Datenpannen", "Eine Verletzung erzeugt voraussichtlich ein hohes Risiko für Betroffene. Welche zusätzliche Pflicht kann entstehen?", "Benachrichtigung der betroffenen Personen nach Art. 34 DSGVO, sofern keine gesetzliche Ausnahme greift.", ["Nur eine interne Notiz.","Nie eine Information an Betroffene.","Nur die Buchhaltung informieren."], "Art. 34 knüpft die Betroffeneninformation an ein hohes Risiko."),
        ]
    return [
        ("Zweckänderung", "Ein Unternehmen will Kundendaten für einen neuen Zweck nutzen, der nicht auf Einwilligung oder einer speziellen gesetzlichen Grundlage beruht. Was ist vorab zu prüfen?", "Die Vereinbarkeit des neuen Zwecks anhand der Kriterien des Art. 6 Abs. 4 DSGVO.", ["Nur der mögliche Umsatz.","Nur die Dateigröße.","Nichts, weil interne Zweitnutzung immer frei ist."], "Art. 6 Abs. 4 nennt Kriterien der Zweckkompatibilität."),
        ("Datenpannen & Risikobewertung", "Ein verschlüsseltes Notebook mit personenbezogenen Daten wird verloren; Schlüssel und Zugangsdaten sind nicht betroffen. Welche Bewertung ist richtig?", "Es liegt ein Vorfall vor, der dokumentiert und risikobewertet werden muss; wirksame Verschlüsselung kann das Risiko deutlich senken und die Meldepflicht beeinflussen.", ["Es kann niemals eine Datenschutzverletzung vorliegen.","Es ist automatisch immer ein hohes Risiko.","Verschlüsselung darf bei der Bewertung nicht berücksichtigt werden."], "Art. 33/34 arbeiten risikobasiert; Schutzmaßnahmen sind relevant."),
        ("Auftragsverarbeitung", "Ein Auftragsverarbeiter verwendet Kundendaten entgegen Weisung für eigene Werbezwecke. Welche Rollenfolge kann eintreten?", "Für diese eigenmächtige Verarbeitung kann er nach Art. 28 Abs. 10 DSGVO insoweit selbst Verantwortlicher sein.", ["Er bleibt zwingend immer Auftragsverarbeiter.","Er wird zur Aufsichtsbehörde.","Die Verarbeitung wird automatisch anonym."], "Art. 28 Abs. 10 regelt die Folge eigener Zweck-/Mittelbestimmung."),
        ("Gemeinsame Verantwortlichkeit", "Zwei Unternehmen bestimmen gemeinsam Zweck und wesentliche Mittel eines Kundenportals. Was ist erforderlich?", "Eine transparente Regelung der jeweiligen Pflichten nach Art. 26 DSGVO, insbesondere zu Betroffenenrechten und Informationspflichten.", ["Automatisch ein Art.-28-Vertrag, weil immer einer Auftragsverarbeiter sein muss.","Keine Rollenklärung.","Betroffenenrechte entfallen."], "Art. 26 regelt gemeinsame Verantwortlichkeit."),
        ("Datenschutz-Folgenabschätzung", "Eine DSFA zeigt trotz geplanter Maßnahmen ein verbleibendes hohes Risiko. Was sieht die DSGVO vor?", "Vor der Verarbeitung ist die Aufsichtsbehörde nach Art. 36 DSGVO zu konsultieren.", ["System trotzdem sofort starten.","DSFA löschen.","Nur die Betroffenen informieren und ohne weitere Prüfung starten."], "Art. 36 regelt die vorherige Konsultation bei verbleibendem hohem Risiko."),
        ("Beschäftigtendaten", "Bei Verdacht einer Straftat eines Beschäftigten soll eine interne Auswertung erfolgen. Welche drei Kernelemente nennt § 26 BDSG?", "Dokumentierte tatsächliche Anhaltspunkte, Erforderlichkeit und Verhältnismäßigkeit gegenüber schutzwürdigen Interessen.", ["Gerücht, technische Möglichkeit, niedrige Kosten.","Nur Einwilligung, sonst nichts.","Beliebige Vollüberwachung ohne Anlass."], "§ 26 Abs. 1 BDSG stellt für Straftataufklärung besondere Anforderungen."),
        ("Auskunft & Rechte Dritter", "Eine Auskunftskopie enthält zugleich personenbezogene Daten unbeteiligter Dritter. Was verlangt Art. 15 Abs. 4?", "Die Rechte und Freiheiten anderer Personen dürfen nicht beeinträchtigt werden; gegebenenfalls ist zu trennen oder zu schwärzen.", ["Immer vollständige ungeschwärzte Herausgabe.","Immer vollständige Ablehnung.","Automatische Löschung des gesamten Dokuments."], "Art. 15 Abs. 4 schützt Rechte Dritter, ohne den Auskunftsanspruch pauschal zu beseitigen."),
        ("Drittlandübermittlung", "Ein Auftragsverarbeiter verarbeitet Daten außerhalb EU/EWR. Reicht ein Art.-28-Vertrag allein?", "Nein. Zusätzlich sind die Voraussetzungen für Drittlandübermittlungen nach Art. 44 ff. DSGVO zu prüfen.", ["Ja, Art. 28 ersetzt Kapitel V vollständig.","Ja, wenn die Daten verschlüsselt sind, ohne weitere Prüfung.","Drittlandübermittlungen sind grundsätzlich immer verboten."], "Auftragsverarbeitung und Drittlandtransfer sind getrennte Prüfschritte."),
        ("Datenschutzbeauftragte", "Eine Datenschutzbeauftragte soll gleichzeitig als Leiterin die Zwecke und Mittel der von ihr zu kontrollierenden HR-Verarbeitung bestimmen. Was ist das Kernproblem?", "Ein möglicher Interessenkonflikt nach Art. 38 Abs. 6 DSGVO.", ["Datenschutzbeauftragte dürfen grundsätzlich keine anderen Aufgaben übernehmen.","Es gibt kein Problem, solange die Stelle intern ist.","Nur die Vergütung ist relevant."], "Andere Aufgaben sind möglich, dürfen aber keinen Interessenkonflikt verursachen."),
        ("Datenpannen & Betroffeneninformation", "Nach einer Panne besteht zunächst hohes Risiko. Durch sofortige Maßnahmen wird dieses hohe Risiko nachweislich beseitigt. Welche Auswirkung kann Art. 34 haben?", "Eine Benachrichtigung der Betroffenen kann unter den gesetzlichen Voraussetzungen entbehrlich sein, wenn nachträgliche Maßnahmen sicherstellen, dass das hohe Risiko aller Wahrscheinlichkeit nach nicht mehr besteht.", ["Betroffene müssen immer informiert werden, ohne Ausnahme.","Der Vorfall muss nicht dokumentiert werden.","Auch die interne Bewertung ist dann verboten."], "Art. 34 Abs. 3 nennt Ausnahmen von der individuellen Benachrichtigung."),
        ("Technische & organisatorische Maßnahmen", "Ein System verarbeitet sensible Daten. Welche Maßnahme entspricht Art. 32 am wenigsten?", "Ein gemeinsames dauerhaftes Team-Passwort ohne individuelle Konten oder Protokollierung.", ["Rollenbasierte Zugriffe.","Wiederherstellungstests für Backups.","Regelmäßige Wirksamkeitsprüfung von Schutzmaßnahmen."], "Art. 32 verlangt ein risikoadäquates Schutzniveau; gemeinsame unkontrollierte Zugänge widersprechen diesem Ziel."),
        ("Datenschutzorganisation", "Welche Aussage beschreibt Rechenschaftspflicht am besten?", "Der Verantwortliche muss Datenschutzgrundsätze nicht nur einhalten, sondern deren Einhaltung auch nachweisen können.", ["Es genügt, Datenschutzregeln mündlich zu kennen.","Nachweise sind nur bei Behörden nötig.","Eine Datenschutzerklärung ersetzt alle organisatorischen Nachweise."], "Art. 5 Abs. 2 DSGVO enthält die Rechenschaftspflicht."),
    ]


def build_exam_privacy(choice):
    out=[]
    code={"Anfänger":"a","Fortgeschritten":"f","Experte":"e"}
    for level in ("Anfänger","Fortgeschritten","Experte"):
        for i,(topic,prompt,correct,wrong,explanation) in enumerate(_exam_cases(level),1):
            out.append(choice(
                f"exam_ds_{code[level]}_{i:02d}", CATEGORY, f"Prüfungsnah: {topic}", level,
                prompt, correct, wrong, explanation,
                "Prüfe zuerst Zweck, Datenart, Rechtsgrundlage, Rechte und Risiko."
            ))
    return out


def build_privacy_questions(Question, choice):
    regular=[]
    regular.extend(build_beginner(choice))
    regular.extend(build_intermediate(choice))
    regular.extend(build_expert(choice))
    exam=build_exam_privacy(choice)

    active=[]
    for level in ("Anfänger","Fortgeschritten","Experte"):
        base=[q for q in regular if q.level==level]
        ex=[q for q in exam if q.level==level]
        if len(base)!=188:
            raise RuntimeError(f"Datenschutz-Basispool {level}: {len(base)} statt 188")
        if len(ex)!=12:
            raise RuntimeError(f"Datenschutz-Prüfungspool {level}: {len(ex)} statt 12")
        active.extend(base+ex)

    if len(active)!=600:
        raise RuntimeError(f"Datenschutz-Aktivpool: {len(active)} statt 600")
    if len({q.id for q in active})!=600:
        raise RuntimeError("Doppelte Datenschutz-IDs gefunden")
    if len({q.prompt for q in active})!=600:
        raise RuntimeError("Doppelte Datenschutz-Fragetexte gefunden")
    for q in active:
        if q.kind=="choice":
            if len(q.options or [])!=4:
                raise RuntimeError(f"{q.id}: nicht genau vier Antwortoptionen")
            if q.correct not in q.options:
                raise RuntimeError(f"{q.id}: richtige Antwort fehlt")
    return active
