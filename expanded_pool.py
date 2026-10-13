from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from itertools import cycle
from typing import Callable


def build_expanded_questions(existing_questions, Question, choice, number, money, excluded_ids=None):
    """Expand the active pool to exactly 1,000 questions per category.

    The generated items deliberately vary scenario details and answer sets. IDs and
    content are deterministic so histories stay stable between runs of this test build.
    """
    categories = [
        "Rechnungswesen",
        "Geschäftsprozesse",
        "Deutsch & Rechtschreibung",
        "Schriftverkehr",
        "Büroorganisation",
    ]
    levels = ["Anfänger", "Fortgeschritten", "Experte"]
    target = {"Anfänger": 334, "Fortgeschritten": 333, "Experte": 333}

    excluded_ids = set(excluded_ids or [])
    active_existing = [q for q in existing_questions if q.id not in excluded_ids]
    by_key = {(cat, lvl): 0 for cat in categories for lvl in levels}
    for q in active_existing:
        if (q.category, q.level) in by_key:
            by_key[(q.category, q.level)] += 1

    out = []
    for cat in categories:
        for lvl in levels:
            need = target[lvl] - by_key[(cat, lvl)]
            if need < 0:
                raise ValueError(f"Existing pool already exceeds target for {cat}/{lvl}")
            builder = {
                "Rechnungswesen": _accounting_question,
                "Geschäftsprozesse": _process_question,
                "Deutsch & Rechtschreibung": _german_question,
                "Schriftverkehr": _correspondence_question,
                "Büroorganisation": _office_question,
            }[cat]
            for i in range(1, need + 1):
                out.append(builder(lvl, i, Question, choice, number, money))
    return out


def _money_dec(v):
    return Decimal(str(v)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _accounting_question(level, i, Question, choice, number, money):
    # 12 distinct calculation families, with scenario-specific values.
    family = (i - 1) % 12
    ref = f"R{i:03d}"
    if level == "Anfänger":
        if family == 0:
            base = Decimal(145 + i * 7); pct = Decimal([5, 8, 10, 12, 15, 20, 25][i % 7]); res = base*pct/100
            return number(f"x_rw_a_{i:03d}", "Rechnungswesen", "Prozentrechnung", level,
                          f"Vorgang {ref}: Wie viel sind {pct}% von {money(base)}?", res,
                          f"{money(base)} × {pct}/100 = {money(res)}.", "Grundwert × Prozentsatz ÷ 100.")
        if family == 1:
            price = Decimal(220 + i*9); pct = Decimal([5,10,15,20][i%4]); res=price*pct/100
            return number(f"x_rw_a_{i:03d}", "Rechnungswesen", "Rabatt", level,
                          f"Artikelgruppe {ref} kostet {money(price)}. Der Lieferant gewährt {pct}% Rabatt. Wie hoch ist der Rabattbetrag?", res,
                          f"Rabatt: {money(price)} × {pct}/100 = {money(res)}.", "Berechne den Rabatt vom Ausgangspreis.")
        if family == 2:
            net=Decimal(310+i*11); res=net*Decimal('0.19')
            return number(f"x_rw_a_{i:03d}", "Rechnungswesen", "Umsatzsteuer", level,
                          f"Rechnung {ref} weist {money(net)} netto aus. Wie hoch ist die Umsatzsteuer bei 19%?", res,
                          f"{money(net)} × 19/100 = {money(res)}.", "19% vom Nettobetrag berechnen.")
        if family == 3:
            net=Decimal(265+i*13); gross=net*Decimal('1.19')
            return number(f"x_rw_a_{i:03d}", "Rechnungswesen", "Umsatzsteuer", level,
                          f"Für Auftrag {ref} beträgt der Nettowert {money(net)}. Wie hoch ist der Bruttobetrag bei 19% Umsatzsteuer?", gross,
                          f"Brutto = {money(net)} × 1,19 = {money(gross)}.", "Netto × 1,19.")
        if family == 4:
            gross=Decimal(476+i*17); net=gross/Decimal('1.19')
            return number(f"x_rw_a_{i:03d}", "Rechnungswesen", "Umsatzsteuer", level,
                          f"Der Bruttobetrag von Beleg {ref} beträgt {money(gross)}. Wie hoch ist der Nettobetrag bei 19% Umsatzsteuer?", net,
                          f"Netto = {money(gross)} ÷ 1,19 = {money(net)}.", "Brutto durch 1,19 teilen.")
        if family == 5:
            qty=3+(i%12); unit=Decimal('24.50')+Decimal(i%20)*Decimal('3.25'); res=qty*unit
            return number(f"x_rw_a_{i:03d}", "Rechnungswesen", "Menge und Umsatzsteuer", level,
                          f"Position {ref}: {qty} Stück kosten je {money(unit)} netto. Wie hoch ist der Nettogesamtbetrag?", res,
                          f"{qty} × {money(unit)} = {money(res)}.", "Menge × Einzelpreis.")
        if family == 6:
            old=Decimal(180+i*5); pct=Decimal([5,10,15][i%3]); new=old*(100+pct)/100
            return number(f"x_rw_a_{i:03d}", "Rechnungswesen", "Prozentrechnung", level,
                          f"Der Preis von Artikel {ref} steigt von {money(old)} um {pct}%. Wie hoch ist der neue Preis?", new,
                          f"Erhöhung {money(old*pct/100)}, neuer Preis {money(new)}.", "Erst die Erhöhung berechnen, dann addieren.")
        if family == 7:
            old=Decimal(260+i*6); pct=Decimal([5,8,12,20][i%4]); new=old*(100-pct)/100
            return number(f"x_rw_a_{i:03d}", "Rechnungswesen", "Prozentrechnung", level,
                          f"Für Sonderaktion {ref} wird {money(old)} um {pct}% reduziert. Wie hoch ist der neue Preis?", new,
                          f"Neuer Preis = {money(old)} × {(100-pct)}/100 = {money(new)}.", "Vom Ausgangswert den Prozentanteil abziehen.")
        if family == 8:
            gross=Decimal(500+i*8); sk=Decimal([2,3][i%2]); res=gross*sk/100
            return number(f"x_rw_a_{i:03d}", "Rechnungswesen", "Skonto", level,
                          f"Rechnung {ref} über {money(gross)} erlaubt {sk}% Skonto. Wie hoch ist der Skontobetrag?", res,
                          f"{money(gross)} × {sk}/100 = {money(res)}.", "Skonto als Prozentsatz berechnen.")
        if family == 9:
            gross=Decimal(530+i*10); sk=Decimal([2,3][i%2]); pay=gross*(100-sk)/100
            return number(f"x_rw_a_{i:03d}", "Rechnungswesen", "Skonto", level,
                          f"Bei Beleg {ref} beträgt die Rechnung {money(gross)}. Nach {sk}% Skonto: Welcher Betrag wird überwiesen?", pay,
                          f"Zahlbetrag = {money(gross)} × {(100-sk)}/100 = {money(pay)}.", "Skonto vom Rechnungsbetrag abziehen.")
        if family == 10:
            listp=Decimal(420+i*12); rab=Decimal([5,10,15,20][i%4]); res=listp*(100-rab)/100
            return number(f"x_rw_a_{i:03d}", "Rechnungswesen", "Rabatt", level,
                          f"Listenpreis {ref}: {money(listp)}, Rabatt {rab}%. Wie hoch ist der Preis nach Rabatt?", res,
                          f"{money(listp)} × {(100-rab)}/100 = {money(res)}.", "Rabatt vom Listenpreis abziehen.")
        qty=2+(i%9); unit=Decimal('59.90')+Decimal(i%14)*Decimal('2.50'); net=qty*unit; tax=net*Decimal('0.19')
        return number(f"x_rw_a_{i:03d}", "Rechnungswesen", "Menge und Umsatzsteuer", level,
                      f"Auftrag {ref}: {qty} Stück zu je {money(unit)} netto. Wie hoch ist nur die Umsatzsteuer für die Gesamtmenge?", tax,
                      f"Netto gesamt {money(net)}; davon 19% = {money(tax)}.", "Menge × Einzelpreis, davon 19%.")

    if level == "Fortgeschritten":
        qty=5+(i%18); unit=Decimal('38.50')+Decimal(i%25)*Decimal('4.10'); rab=Decimal([5,8,10,12,15][i%5]); sk=Decimal([2,3][i%2])
        if family in (0,1):
            net=qty*unit; after=net*(100-rab)/100; gross=after*Decimal('1.19')
            return number(f"x_rw_f_{i:03d}", "Rechnungswesen", "Rabatt und Umsatzsteuer", level,
                          f"Bestellung {ref}: {qty} Stück à {money(unit)} netto, {rab}% Rabatt, anschließend 19% Umsatzsteuer. Wie hoch ist der Bruttobetrag?", gross,
                          f"Netto {money(net)} → nach Rabatt {money(after)} → brutto {money(gross)}.", "Menge × Preis → Rabatt → Umsatzsteuer.")
        if family in (2,3):
            gross=Decimal(780+i*15); pay=gross*(100-sk)/100
            return number(f"x_rw_f_{i:03d}", "Rechnungswesen", "Skonto", level,
                          f"Rechnung {ref}: {money(gross)} brutto. Bei fristgerechter Zahlung gelten {sk}% Skonto. Wie hoch ist der Zahlbetrag?", pay,
                          f"{money(gross)} × {(100-sk)}/100 = {money(pay)}.", "Skonto vom Bruttobetrag abziehen.")
        if family in (4,5):
            gross=Decimal(950+i*19); net=gross/Decimal('1.19'); tax=gross-net
            return number(f"x_rw_f_{i:03d}", "Rechnungswesen", "Umsatzsteuer", level,
                          f"Bruttorechnung {ref} beträgt {money(gross)} bei 19% Umsatzsteuer. Wie hoch ist der enthaltene Umsatzsteuerbetrag?", tax,
                          f"Netto {money(net)}, Umsatzsteuer {money(tax)}.", "Brutto ÷ 1,19, Differenz zum Brutto bilden.")
        if family in (6,7):
            ordered=10+(i%15); delivered=ordered-(1+i%3); net=delivered*unit; gross=net*Decimal('1.19')
            return number(f"x_rw_f_{i:03d}", "Rechnungswesen", "Rechnungsprüfung", level,
                          f"Zu Auftrag {ref} wurden {ordered} Stück bestellt, aber nur {delivered} zu je {money(unit)} netto geliefert. Wie hoch ist der korrekte Bruttobetrag für die Lieferung?", gross,
                          f"{delivered} × {money(unit)} = {money(net)} netto; brutto {money(gross)}.", "Nur tatsächlich gelieferte Menge berechnen.")
        if family in (8,9):
            listp=qty*unit; after=listp*(100-rab)/100; saving=listp-after
            return number(f"x_rw_f_{i:03d}", "Rechnungswesen", "Rabatt", level,
                          f"Vorgang {ref}: {qty} Stück à {money(unit)} netto, {rab}% Rabatt. Wie hoch ist die gesamte Ersparnis durch den Rabatt?", saving,
                          f"Listenwert {money(listp)}, Rabattbetrag {money(saving)}.", "Rabatt auf den gesamten Warenwert berechnen.")
        net=qty*unit; after=net*(100-rab)/100; gross=after*Decimal('1.19'); pay=gross*(100-sk)/100
        return number(f"x_rw_f_{i:03d}", "Rechnungswesen", "Mehrstufige Rechnung", level,
                      f"Fall {ref}: {qty} Stück à {money(unit)}, {rab}% Rabatt, 19% Umsatzsteuer und danach {sk}% Skonto. Wie hoch ist der Zahlbetrag?", pay,
                      f"Netto {money(net)} → Rabatt {money(after)} → brutto {money(gross)} → Zahlbetrag {money(pay)}.", "Reihenfolge beachten: Rabatt vor Umsatzsteuer, Skonto danach.")

    # Expert: multi-step, reconciliation, reverse calculations.
    qty=12+(i%20); unit=Decimal('52.40')+Decimal(i%30)*Decimal('3.70'); rab=Decimal([5,8,10,12,15][i%5]); sk=Decimal([2,3][i%2])
    if family in (0,1,2):
        net=qty*unit; after=net*(100-rab)/100; gross=after*Decimal('1.19'); pay=gross*(100-sk)/100
        return number(f"x_rw_e_{i:03d}", "Rechnungswesen", "Mehrstufige Rechnung", level,
                      f"Beschaffung {ref}: {qty} Stück zu {money(unit)} netto, {rab}% Lieferantenrabatt, 19% Umsatzsteuer, anschließend {sk}% Skonto. Welcher Betrag wird überwiesen?", pay,
                      f"{money(net)} → {money(after)} → {money(gross)} → {money(pay)}.", "Komplette Bezugskette in der richtigen Reihenfolge rechnen.")
    if family in (3,4):
        ordered=qty; delivered=qty-(2+i%5); damaged=1+(i%2); billable=delivered-damaged; net=billable*unit*(100-rab)/100; gross=net*Decimal('1.19')
        return number(f"x_rw_e_{i:03d}", "Rechnungswesen", "Rechnungsprüfung", level,
                      f"Prüffall {ref}: {ordered} bestellt, {delivered} geliefert, davon {damaged} nachweislich nicht berechenbar. Preis {money(unit)} netto, {rab}% Rabatt. Wie hoch ist der Bruttowert der berechenbaren Ware?", gross,
                      f"Berechenbar {billable} Stück; nach Rabatt netto {money(net)}, brutto {money(gross)}.", "Nur berechenbare Menge, Rabatt und Umsatzsteuer berücksichtigen.")
    if family in (5,6):
        gross=Decimal(1800+i*23); net=gross/Decimal('1.19'); target=net*(100-rab)/100
        return number(f"x_rw_e_{i:03d}", "Rechnungswesen", "Mehrstufige Rechnung", level,
                      f"Analyse {ref}: Ein Bruttolistenwert von {money(gross)} enthält 19% Umsatzsteuer. Auf den daraus ermittelten Nettowert sollen {rab}% Nachlass gerechnet werden. Welcher Nettowert verbleibt?", target,
                      f"Netto vor Nachlass {money(net)}, nach {rab}% Nachlass {money(target)}.", "Zuerst Umsatzsteuer herausrechnen, dann Nachlass.")
    if family in (7,8):
        correct_net=qty*unit; invoiced_net=(qty+2)*unit; diff=(invoiced_net-correct_net)*Decimal('1.19')
        return number(f"x_rw_e_{i:03d}", "Rechnungswesen", "Rechnungsprüfung", level,
                      f"Kontrolle {ref}: Geliefert wurden {qty} Stück zu {money(unit)} netto, berechnet wurden jedoch {qty+2}. Wie hoch ist die Bruttodifferenz der zwei zu viel berechneten Stück?", diff,
                      f"Differenz netto {money(2*unit)}, brutto {money(diff)}.", "Nur die überberechnete Menge bewerten.")
    if family in (9,10):
        gross=Decimal(2200+i*29); pay=gross*(100-sk)/100; saved=gross-pay
        return number(f"x_rw_e_{i:03d}", "Rechnungswesen", "Skonto", level,
                      f"Liquiditätsfall {ref}: Bruttorechnung {money(gross)}, Skonto {sk}%. Wie groß ist der absolute Vorteil einer fristgerechten Zahlung?", saved,
                      f"Skontovorteil = {money(saved)}.", "Absolute Ersparnis durch Skonto berechnen.")
    net=qty*unit; after=net*(100-rab)/100; tax=after*Decimal('0.19');
    return number(f"x_rw_e_{i:03d}", "Rechnungswesen", "Rabatt und Umsatzsteuer", level,
                  f"Kalkulationsfall {ref}: {qty} Stück à {money(unit)} netto, {rab}% Rabatt. Wie hoch ist anschließend allein die Umsatzsteuer?", tax,
                  f"Nach Rabatt netto {money(after)}; davon 19% = {money(tax)}.", "Umsatzsteuer erst auf den rabattierten Nettowert berechnen.")


def _german_question(level, i, Question, choice, number, money):
    ref=f"D{i:03d}"
    family=(i-1)%12
    j=(i-1)//12
    nouns=["Rechnung","Bestellung","Lieferung","Mahnung","Gutschrift","Anfrage","Auftragsbestätigung","Preisliste","Terminbestätigung","Reklamation","Zahlung","Wareneingang","Inventarliste","Kundenakte","Versandbestätigung","Kostenübersicht"]
    verbs=["prüfen","versenden","bearbeiten","freigeben","archivieren","weiterleiten","bestätigen","zuordnen","korrigieren","erfassen","abgleichen","ergänzen"]
    docs=nouns[(j*3 + family)%len(nouns)]
    verb=verbs[(j*5 + family)%len(verbs)]
    date=["Montag","Dienstag","Mittwoch","Donnerstag","Freitag"][(j+family)%5]
    order_no=4700 + i + (0 if level=="Anfänger" else 1000 if level=="Fortgeschritten" else 2000)
    context=f"Auftrag {order_no}"

    if family==0:
        correct=f"Für {context} werden wir die {docs} am {date} {verb}."
        wrong=[f"Für {context} werden wir die {docs.lower()} am {date} {verb}.", f"Für {context} werden wir die {docs} am {date.lower()} {verb}.", f"Für {context} Werden wir die {docs} am {date} {verb}."]
        return choice(f"x_de_{level[0]}_{i:03d}","Deutsch & Rechtschreibung","Groß- und Kleinschreibung",level,
                      f"Welche Schreibweise ist bei {context} korrekt?",correct,wrong,"Nomen und Wochentage werden großgeschrieben; Verben im Satz klein.","Achte auf Nomen, Wochentage und Verben.")
    if family==1:
        starts=["Wenn die Ware eintrifft","Sobald die Freigabe vorliegt","Obwohl die Rechnung bereits bezahlt ist","Bevor der Termin bestätigt wird","Nachdem die Bestellung eingegangen ist","Weil eine Position fehlt","Während die Unterlagen geprüft werden","Falls der Kunde zustimmt"]
        ends=[f"prüfen wir die {docs} zu {context}",f"versenden wir die Unterlagen zu {context}",f"klären wir den Vorgang {context}",f"erfassen wir die Änderung zu {context}",f"informieren wir den zuständigen Bereich zu {context}"]
        a=starts[j%len(starts)]; b=ends[(j*2+family)%len(ends)]; correct=f"{a}, {b}."
        wrong=[f"{a} {b}.",f"{a},, {b}.",f"{a.split(' ',1)[0]}, {a.split(' ',1)[1]} {b}."]
        return choice(f"x_de_{level[0]}_{i:03d}","Deutsch & Rechtschreibung","Kommasetzung",level,
                      f"Welche Kommasetzung ist für den Satz zu {context} richtig?",correct,wrong,"Ein vorangestellter Nebensatz wird mit Komma vom Hauptsatz getrennt.","Suche Nebensatz und Hauptsatz.")
    if family==2:
        compounds=[("kennenlernen","kennen lernen"),("stattfinden","statt finden"),("teilnehmen","teil nehmen"),("weiterleiten","weiter leiten"),("zurückrufen","zurück rufen"),("feststellen","fest stellen"),("bereitstellen","bereit stellen"),("nachfragen","nach fragen")]
        corr,wrongform=compounds[j%len(compounds)]
        correct=f"Bei {context} ist die Grundform „{corr}“ richtig geschrieben."
        wrong=[f"Bei {context} ist die Grundform „{wrongform}“ richtig geschrieben.",f"Bei {context} ist die Grundform „{corr.title()}“ richtig geschrieben.",f"Bei {context} ist die Grundform „{corr[:-1]} {corr[-1]}“ richtig geschrieben."]
        return choice(f"x_de_{level[0]}_{i:03d}","Deutsch & Rechtschreibung","Getrennt- und Zusammenschreibung",level,
                      f"Welche Aussage zur Schreibweise in {context} ist korrekt?",correct,wrong,"Die angegebene Verbform wird in dieser Grundform zusammengeschrieben.","Achte auf die Grundform des Verbs.")
    if family==3:
        words=[("voraussichtlich",["vorraussichtlich","voraussichtlig","vorausstichtlich"]),("Standard",["Standart","Standartt","standart"]),("Rhythmus",["Rythmus","Rhytmus","Rhythmuss"]),("separat",["seperat","seperrat","separrat"]),("Adresse",["Addresse","Adrese","Adressse"]),("Reparatur",["Reperatur","Reparaturr","Reperratur"]),("Quittung",["Quitung","Quittunng","Quittunng"]),("Lizenz",["Lizens","Liezens","Lizenß"]),("Akquise",["Aquise","Akqise","Akwi­se"]),("Kapazität",["Kapazitaet","Kapazietät","Kapazittät"]),("parallel",["paralel","parrallel","paralell"]),("effizient",["efizient","effizent","effitient"])]
        corr,wr=words[j%len(words)]
        correct=f"Im Text zu {context} lautet die richtige Schreibweise „{corr}“."
        wrong=[f"Im Text zu {context} lautet die richtige Schreibweise „{x}“." for x in wr]
        return choice(f"x_de_{level[0]}_{i:03d}","Deutsch & Rechtschreibung","Rechtschreibung",level,
                      f"Welche Schreibweise ist im Geschäftstext zu {context} korrekt?",correct,wrong,"Die richtige Standardschreibweise ist angegeben.","Achte auf typische Fehlerstellen im Wort.")
    if family==4:
        time=["10:00 Uhr","12:00 Uhr","14:30 Uhr","16:00 Uhr"][j%4]
        correct=f"Bitte senden Sie uns die {docs} zu {context} bis {date}, {time}, zu."
        wrong=[f"Schicken Sie uns die {docs} zu {context} irgendwann bis {date}.",f"Wir brauchen die {docs} für {context} schnellstens!!!",f"Die {docs} zu {context} muss bis {date} her."]
        return choice(f"x_de_{level[0]}_{i:03d}","Deutsch & Rechtschreibung","Geschäftlicher Ausdruck",level,
                      f"Welche Formulierung zu {context} ist klar und geschäftlich angemessen?",correct,wrong,"Die Formulierung ist höflich, konkret und enthält eine eindeutige Frist.","Bevorzuge sachliche, konkrete Formulierungen.")
    if family==5:
        correct=f"Vielen Dank für Ihre {docs} zu {context}. Wir prüfen den Vorgang und melden uns bis {date}."
        wrong=[f"Danke für die {docs} zu {context}. Wir gucken mal.",f"Ihre {docs} zu {context} ist angekommen, irgendwann melden wir uns.",f"Wir prüfen {context} vielleicht und sagen dann Bescheid."]
        return choice(f"x_de_{level[0]}_{i:03d}","Deutsch & Rechtschreibung","Geschäftlicher Text",level,
                      f"Welche Antwort zu {context} ist professionell?",correct,wrong,"Der Text bestätigt den Eingang und nennt einen konkreten nächsten Schritt.","Klare Zusage zum nächsten Schritt statt vager Aussage.")
    if family==6:
        correct=f"Die Prüfung der {docs} zu {context} ist abgeschlossen."
        wrong=[f"Die prüfung der {docs} zu {context} ist abgeschlossen.",f"Die Prüfung der {docs} zu {context} ist Abgeschlossen.",f"die Prüfung der {docs} zu {context} ist abgeschlossen."]
        return choice(f"x_de_{level[0]}_{i:03d}","Deutsch & Rechtschreibung","Nominalisierung",level,
                      f"Welcher Satz zu {context} ist korrekt?",correct,wrong,"Das Nomen „Prüfung“ wird großgeschrieben; das Verb/Adjektiv hier klein.","Nomen erkennen.")
    if family==7:
        correct=f"Wir prüfen, ob die {docs} zu {context} vollständig vorliegt."
        wrong=[f"Wir prüfen ob die {docs} zu {context} vollständig vorliegt.",f"Wir, prüfen ob die {docs} zu {context} vollständig vorliegt.",f"Wir prüfen, ob, die {docs} zu {context} vollständig vorliegt."]
        return choice(f"x_de_{level[0]}_{i:03d}","Deutsch & Rechtschreibung","Kommasetzung",level,
                      f"Welche Kommasetzung zu {context} ist richtig?",correct,wrong,"Ein mit „ob“ eingeleiteter Nebensatz wird durch Komma abgetrennt.","Nebensatz mit „ob“ erkennen.")
    if family==8:
        correct=f"Bitte prüfen Sie die beigefügte {docs} zu {context} und geben Sie uns bis {date} Rückmeldung."
        wrong=[f"Bitte mal {docs} zu {context} checken und melden.",f"{docs} zu {context} angucken, Rückmeldung wäre gut.",f"Prüfen Sie sofort die {docs} zu {context}!!!"]
        return choice(f"x_de_{level[0]}_{i:03d}","Deutsch & Rechtschreibung","Geschäftlicher Ausdruck",level,
                      f"Welche Geschäftssprache passt bei {context} am besten?",correct,wrong,"Die Formulierung ist sachlich, höflich und eindeutig.","Vermeide Umgangssprache und unnötige Schärfe.")
    if family==9:
        correct=f"Nach Rücksprache können wir den Termin zu {context} am {date} bestätigen."
        wrong=[f"Nach Rücksprache Können wir den Termin zu {context} am {date} bestätigen.",f"Nach rücksprache können wir den Termin zu {context} am {date} bestätigen.",f"Nach Rücksprache können wir den Termin zu {context} am {date} Bestätigen."]
        return choice(f"x_de_{level[0]}_{i:03d}","Deutsch & Rechtschreibung","Groß- und Kleinschreibung",level,
                      f"Welche Schreibweise zum Termin von {context} ist korrekt?",correct,wrong,"Nomen werden groß-, Verben klein geschrieben.","Prüfe besonders „Rücksprache“, „können“ und „bestätigen“.")
    if family==10:
        correct=f"Die Unterlagen zu {context}, die gestern eingegangen sind, werden heute {verb}."
        wrong=[f"Die Unterlagen zu {context} die gestern eingegangen sind werden heute {verb}.",f"Die Unterlagen zu {context}, die gestern eingegangen sind werden heute {verb}.",f"Die Unterlagen zu {context} die gestern eingegangen sind, werden heute {verb}."]
        return choice(f"x_de_{level[0]}_{i:03d}","Deutsch & Rechtschreibung","Kommasetzung",level,
                      f"Welche Kommasetzung beim Relativsatz zu {context} ist richtig?",correct,wrong,"Ein eingeschobener Relativsatz wird mit zwei Kommas abgetrennt.","Der Relativsatz ist ein Einschub.")
    correct=f"Für {context} ist das sorgfältige {verb.capitalize()} der {docs} erforderlich."
    wrong=[f"Für {context} ist das sorgfältige {verb} der {docs} erforderlich.",f"Für {context} ist das Sorgfältige {verb.capitalize()} der {docs} erforderlich.",f"Für {context} ist das sorgfältige {verb.capitalize()} der {docs.lower()} erforderlich."]
    return choice(f"x_de_{level[0]}_{i:03d}","Deutsch & Rechtschreibung","Nominalisierung",level,
                  f"Welche Groß-/Kleinschreibung bei {context} ist korrekt?",correct,wrong,"Nach dem substantivierenden Artikel/Adjektiv wird das Verb als Nomen großgeschrieben.","Achte auf die Nominalisierung.")


def _office_question(level, i, Question, choice, number, money):
    ref=f"B-{level[0]}{i:03d}"; family=(i-1)%12
    names=["Frau Neumann","Herr Keller","Frau Brandt","Herr Peters","Frau Vogel","Herr Stein"]
    departments=["Einkauf","Vertrieb","Buchhaltung","Personal","Logistik","Service"]
    n=names[i%len(names)]; dep=departments[i%len(departments)]
    day=["heute","morgen","am Freitag","bis 14 Uhr","bis Tagesende"][i%5]
    if family==0:
        c=f"Die fristgebundene Aufgabe {ref} zuerst sichern und weniger dringende Tätigkeiten anschließend bearbeiten."
        w=[f"Zuerst die Ablage aus Vorgang {ref} sortieren und die Frist später prüfen.",f"Alle Aufgaben zu {ref} gleichzeitig beginnen.",f"Die Frist zu {ref} ignorieren, wenn andere Aufgaben angenehmer sind."]
        topic="Prioritäten"
        p=f"Im {dep} läuft {day} eine verbindliche Frist ab; zugleich stehen Routineablage und eine interne Rückfrage an. Was ist sinnvoll?"
    elif family==1:
        c=f"Den Bildschirm sperren und Unterlagen zu Vorgang {ref} gegen Einsicht sichern."
        w=[f"Nur den Monitor ausschalten und Vorgang {ref} offen lassen.",f"Die Daten aus {ref} sichtbar lassen, weil die Pause kurz ist.",f"Ein Fenster über den Kundendaten von {ref} öffnen; Sperren ist nicht nötig."]
        topic="Datenschutz und Sicherheit"; p=f"{n} verlässt den Arbeitsplatz kurz. Auf dem Bildschirm sind Kundendaten aus {ref} geöffnet. Was ist richtig?"
    elif family==2:
        c=f"Vorgang {ref} nach dem festgelegten Ablageplan eindeutig verschlagworten und am vorgesehenen Ort speichern."
        w=[f"Vorgang {ref} irgendwo auf dem Desktop ablegen.",f"Für {ref} einen privaten Ordner ohne Struktur anlegen.",f"{ref} mehrfach in verschiedenen Ordnern speichern, ohne Versionen zu kennzeichnen."]
        topic="Ablage"; p=f"Ein abgeschlossener Vorgang aus dem {dep} soll archiviert werden. Welche Vorgehensweise ist am besten?"
    elif family==3:
        c=f"Für Besprechung {ref} Ziel, Teilnehmer, Unterlagen und Zeitrahmen vorab festlegen."
        w=[f"Besprechung {ref} ohne Agenda starten und Themen spontan sammeln.",f"Zu {ref} möglichst viele Personen ohne Aufgabenbezug einladen.",f"Unterlagen für {ref} erst nach der Besprechung verteilen."]
        topic="Besprechungsorganisation"; p=f"Du bereitest eine Besprechung im Bereich {dep} vor. Welche Maßnahme verbessert die Organisation am stärksten?"
    elif family==4:
        c=f"Den Konflikt bei Termin {ref} früh klären, Priorität prüfen und eine abgestimmte Alternative festhalten."
        w=[f"Beide Termine zu {ref} unverändert stehen lassen und hoffen, dass es klappt.",f"Einen Termin zu {ref} ohne Information löschen.",f"Erst nach Beginn von {ref} auf die Überschneidung hinweisen."]
        topic="Terminplanung"; p=f"Für {n} überschneiden sich zwei wichtige Termine. Einer ist extern gebunden, der andere intern verschiebbar. Was ist sinnvoll?"
    elif family==5:
        c=f"Die zuständige Person im Bereich {dep} mit den relevanten Fakten zu {ref} informieren und den nächsten Schritt dokumentieren."
        w=[f"Den Vorgang {ref} ohne Kontext weiterleiten.",f"{ref} an möglichst viele Empfänger senden, unabhängig von Zuständigkeit.",f"Bei {ref} nur mündlich etwas erwähnen und nichts festhalten."]
        topic="Kommunikation und Eskalation"; p=f"Ein Problem in Vorgang {ref} kann die vereinbarte Frist gefährden. Wie eskalierst du sinnvoll?"
    elif family==6:
        c=f"Für Datei {ref} eine eindeutige Version und einen nachvollziehbaren Dateinamen verwenden."
        w=[f"Datei {ref} als 'neu_neu_final2' speichern.",f"Mehrere unterschiedliche Fassungen von {ref} gleich benennen.",f"Bei {ref} Datum und Version grundsätzlich vermeiden."]
        topic="Dokumentenmanagement"; p=f"Mehrere Mitarbeitende bearbeiten dasselbe Dokument. Wie verhinderst du Versionschaos?"
    elif family==7:
        c=f"Aufgabe {ref} mit Termin, Zuständigkeit und Status im vorgesehenen System erfassen."
        w=[f"Aufgabe {ref} nur im Gedächtnis behalten.",f"{ref} auf einen losen Zettel ohne Termin schreiben.",f"Bei {ref} nur den Titel speichern, aber keine Zuständigkeit."]
        topic="Arbeitsorganisation"; p=f"Eine neue Aufgabe aus dem {dep} muss bis {day} erledigt sein. Wie organisierst du sie zuverlässig?"
    elif family==8:
        c=f"Verdächtige Nachricht zu {ref} nicht öffnen, Absender und Inhalt prüfen und nach interner Regel melden."
        w=[f"Anhang zu {ref} sofort öffnen, um zu sehen, was enthalten ist.",f"Passwort auf Anfrage in Nachricht {ref} zurücksenden.",f"Verdächtige Mail {ref} an private Adresse weiterleiten."]
        topic="Datenschutz und IT-Sicherheit"; p=f"Im Postfach erscheint eine unerwartete Nachricht mit Anhang und Aufforderung zur Passworteingabe. Wie reagierst du?"
    elif family==9:
        c=f"Bei Vertretung {ref} offene Aufgaben, Fristen, Ansprechpartner und Bearbeitungsstand strukturiert übergeben."
        w=[f"Für Vertretung {ref} nur sagen, dass 'alles im Ordner' liegt.",f"Fristen aus {ref} nicht erwähnen, um die Übergabe kurz zu halten.",f"Vertretung {ref} ohne Zugriff auf nötige Unterlagen starten lassen."]
        topic="Prioritäten und Vertretung"; p=f"{n} fällt kurzfristig aus. Was gehört in eine gute Übergabe an die Vertretung?"
    elif family==10:
        c=f"Bei Prozess {ref} den tatsächlichen Ablauf dokumentieren, Engpass benennen und eine überprüfbare Verbesserung vereinbaren."
        w=[f"Prozess {ref} vollständig ändern, ohne Ursache zu prüfen.",f"Nur die langsamste Person für {ref} verantwortlich machen.",f"Bei {ref} keine Kennzahlen oder Rückmeldungen berücksichtigen."]
        topic="Prozessorganisation"; p=f"Ein wiederkehrender Büroprozess dauert deutlich länger als geplant. Was ist ein sinnvoller Verbesserungsansatz?"
    else:
        c=f"Bei Fall {ref} zuerst Auswirkungen und Frist prüfen, dann Zuständigkeit und nächste Schritte verbindlich koordinieren."
        w=[f"Fall {ref} sofort an irgendeine Stelle abgeben.",f"Nur die zuletzt eingegangene Aufgabe bearbeiten, unabhängig von Folgen für {ref}.",f"Bei {ref} Entscheidungen vermeiden, bis jemand nachfragt."]
        topic="Komplexe Priorisierung"; p=f"Mehrere Aufgaben treffen gleichzeitig ein: Kundenreklamation, interne Rückfrage und fristgebundene Freigabe. Wie gehst du vor?"
    return choice(f"x_bo_{level[0]}_{i:03d}","Büroorganisation",topic,level,p,c,w,
                  "Die sinnvolle Lösung berücksichtigt Frist, Zuständigkeit, Datenschutz und nachvollziehbare Organisation.","Bewerte Dringlichkeit, Wichtigkeit und Zuständigkeit.")


def _process_question(level, i, Question, choice, number, money):
    ref=f"G-{level[0]}{i:03d}"; family=(i-1)%12
    product=["Bürostühle","Ordner","Druckerpapier","Monitore","Schreibtischlampen","Toner","Versandkartons","Headsets"][i%8]
    supplier=["Nordhandel","BüroPlus","OfficePro","Hansebedarf","WeserLogistik"][i%5]
    qty=10+(i%30)
    if family==0:
        p=f"Für Beschaffung {ref} werden {qty} {product} benötigt. Welcher Schritt gehört typischerweise vor die verbindliche Bestellung?"
        c=f"Geeignete Angebote für {ref} prüfen und die Bestellung anschließend freigeben."
        w=[f"Rechnung für {ref} vorab als bezahlt buchen.",f"Wareneingang für {ref} bestätigen, obwohl noch nichts geliefert wurde.",f"Mahnung zu {ref} erstellen, bevor ein Auftrag besteht."]
        topic="Ablauf"
    elif family==1:
        p=f"Lieferung {ref} von {supplier}: bestellt {qty}, angekommen {qty-2} {product}. Was ist zuerst zu dokumentieren?"
        c=f"Die Mengenabweichung von zwei Stück bei {ref} festhalten und mit Bestellung/Lieferschein abgleichen."
        w=[f"Für {ref} automatisch die volle Menge als erhalten buchen.",f"Die zwei fehlenden Stück bei {ref} privat nachkaufen.",f"Den Lieferschein zu {ref} ungeprüft ablegen."]
        topic="Mengenabweichung"
    elif family==2:
        p=f"Bei Wareneingang {ref} sind mehrere {product} sichtbar beschädigt. Welche Reaktion ist kaufmännisch sinnvoll?"
        c=f"Schaden zu {ref} dokumentieren, betroffene Menge sichern und Lieferantenkontakt nach Vorgabe veranlassen."
        w=[f"Beschädigte Ware aus {ref} ohne Dokumentation entsorgen.",f"Lieferung {ref} vollständig als mangelfrei bestätigen.",f"Schäden aus {ref} erst bei der nächsten Inventur erwähnen."]
        topic="Qualitätsabweichung"
    elif family==3:
        p=f"Rechnung {ref} enthält eine Position, die weder in Bestellung noch Auftragsbestätigung steht. Was ist sinnvoll?"
        c=f"Die nicht zuordenbare Position bei {ref} klären und die Rechnung bis zur Prüfung nicht ungeprüft freigeben."
        w=[f"Rechnung {ref} vollständig zahlen und die Position ignorieren.",f"Die Bestellung zu {ref} nachträglich passend ändern.",f"Position aus {ref} intern auf irgendeine Kostenstelle buchen."]
        topic="Rechnungsprüfung"
    elif family==4:
        p=f"Für Vorgang {ref} weicht der Rechnungsrabatt vom bestätigten Angebot von {supplier} ab. Welche Unterlagen sind besonders relevant?"
        c=f"Angebot, Bestellung/Auftragsbestätigung und Rechnung zu {ref} miteinander vergleichen."
        w=[f"Nur den Lieferschein von {ref} prüfen; Preisvereinbarungen sind dort immer vollständig.",f"Nur die aktuelle Preisliste von {supplier} ansehen und Vereinbarung {ref} ignorieren.",f"Die Rechnung {ref} ohne Belegvergleich korrigieren."]
        topic="Dokumente"
    elif family==5:
        p=f"Lieferant {supplier} kündigt zu {ref} eine Verzögerung an, die einen Kundentermin gefährdet. Was ist sinnvoll?"
        c=f"Auswirkung von {ref} bewerten, Alternativen/Neutermin klären und betroffene Stellen rechtzeitig informieren."
        w=[f"Verzögerung {ref} nicht weitergeben, bis der Termin verstrichen ist.",f"Ohne Prüfung sofort alle Aufträge bei {supplier} stornieren.",f"Zu {ref} einen beliebigen neuen Termin versprechen."]
        topic="Lieferantenmanagement"
    elif family==6:
        p=f"Zu Rechnung {ref} ist die Ware vollständig und korrekt, aber die Fälligkeit wurde falsch erfasst. Was ist zu tun?"
        c=f"Zahlungsbedingung anhand des Belegs zu {ref} prüfen und den korrekten Fälligkeitstermin erfassen."
        w=[f"Rechnung {ref} sofort doppelt bezahlen.",f"Fälligkeit bei {ref} grundsätzlich ignorieren.",f"Liefermenge zu {ref} ändern, obwohl sie korrekt ist."]
        topic="Zahlungsabwicklung"
    elif family==7:
        p=f"Für Anfrage {ref} liegen drei Angebote für {product} vor. Was gehört zu einem sachlichen Vergleich?"
        c=f"Bei {ref} Preis, Leistung, Liefertermin, Zahlungsbedingungen und relevante Folgekosten vergleichbar bewerten."
        w=[f"Bei {ref} ausschließlich das schönste Angebotslayout auswählen.",f"Nur den niedrigsten Einzelpreis betrachten und alle Bedingungen ignorieren.",f"Angebot wählen, das zuletzt eingegangen ist."]
        topic="Angebotsvergleich"
    elif family==8:
        p=f"Bei Vorgang {ref} ist die Rechnung bereits bezahlt, danach wird eine berechtigte Gutschrift angekündigt. Was ist sinnvoll?"
        c=f"Gutschrift zu {ref} dem ursprünglichen Vorgang zuordnen und die finanzielle Korrektur nachvollziehbar überwachen."
        w=[f"Gutschrift {ref} löschen, weil bereits bezahlt wurde.",f"Ursprüngliche Rechnung zu {ref} nachträglich auf null setzen.",f"Gutschrift {ref} einem beliebigen anderen Lieferanten zuordnen."]
        topic="Zahlungsabwicklung"
    elif family==9:
        p=f"Wareneingang {ref}: Lieferschein nennt {qty} {product}, tatsächlich sind {qty} angekommen. Was ist der nächste Kontrollschritt?"
        c=f"Bei {ref} zusätzlich Zustand/Qualität prüfen und den Wareneingang entsprechend dokumentieren."
        w=[f"Nur die Anzahl reicht; Qualität von {ref} darf nie geprüft werden.",f"Lieferschein {ref} vernichten, sobald die Menge stimmt.",f"Rechnung {ref} unabhängig vom weiteren Belegfluss sofort zahlen."]
        topic="Wareneingang"
    elif family==10:
        p=f"Prozess {ref}: Bestellung wurde geändert, aber die Änderung ist nicht in allen Folgebelegen sichtbar. Was reduziert das Risiko?"
        c=f"Änderung zu {ref} eindeutig dokumentieren und sicherstellen, dass betroffene Folgebelege/Personen denselben Stand verwenden."
        w=[f"Bei {ref} mehrere widersprüchliche Versionen parallel weiterverwenden.",f"Änderung {ref} nur mündlich einer Person mitteilen.",f"Den ursprünglichen Vorgang {ref} löschen und ohne Referenz neu beginnen."]
        topic="Kontrolle und Risikovermeidung"
    else:
        p=f"Bei Reklamation {ref} fehlen {2+i%4} {product} und ein Teil ist beschädigt. Wie sollte der Vorgang behandelt werden?"
        c=f"Mengen- und Qualitätsabweichung zu {ref} getrennt dokumentieren und mit {supplier} eine nachvollziehbare Korrektur abstimmen."
        w=[f"Bei {ref} nur die fehlende Menge beachten und Schäden ignorieren.",f"Alles aus {ref} ungeprüft bezahlen.",f"Ohne Rücksprache die gesamte Geschäftsbeziehung mit {supplier} beenden."]
        topic="Reklamation"
    return choice(f"x_gp_{level[0]}_{i:03d}","Geschäftsprozesse",topic,level,p,c,w,
                  "Geschäftsprozesse werden anhand von Belegen, tatsächlichem Sachverhalt und vereinbarten Bedingungen nachvollziehbar geprüft.","Vergleiche Soll, Ist und Belege.")


def _correspondence_question(level, i, Question, choice, number, money):
    ref=f"S-{level[0]}{i:03d}"; family=(i-1)%12
    product=["Lieferung","Rechnung","Angebot","Gutschrift","Termin","Bestellung","Reklamation","Unterlagen"][i%8]
    date=["22. September","30. September","5. Oktober","12. Oktober","18. Oktober"][i%5]
    if family==0:
        p=f"E-Mail {ref} betrifft eine fehlerhafte Rechnung. Welcher Betreff ist am aussagekräftigsten?"
        c=f"Reklamation zu Rechnung {ref} – Bitte um Prüfung"
        w=[f"Wichtig {ref}",f"Hallo wegen {ref}",f"Problem!!! {ref}"]
        topic="Betreff"
    elif family==1:
        p=f"Für Vorgang {ref} fehlen Unterlagen. Welche Formulierung ist sachlich und eindeutig?"
        c=f"Bitte senden Sie uns die zu {ref} noch fehlenden Unterlagen bis zum {date} zu."
        w=[f"Schicken Sie den Rest zu {ref} mal schnell.",f"Da fehlt bei {ref} noch was.",f"Unterlagen {ref} sofort!!!"]
        topic="Klare Formulierung"
    elif family==2:
        p=f"Bei {ref} wurden zwei Positionen nicht geliefert. Welche Reklamationsformulierung passt?"
        c=f"Bei der Prüfung der Lieferung {ref} haben wir festgestellt, dass zwei bestätigte Positionen fehlen. Bitte prüfen Sie die Nachlieferung."
        w=[f"Bei {ref} haben Sie schon wieder Mist gebaut.",f"Da fehlt was bei {ref}, kümmern.",f"Wir sind wegen {ref} total sauer!!!"]
        topic="Reklamation"
    elif family==3:
        p=f"Zu {ref} soll eine klare Frist gesetzt werden. Welche Formulierung ist am besten?"
        c=f"Bitte senden Sie uns Ihre Rückmeldung zu {ref} bis spätestens {date}."
        w=[f"Bitte möglichst bald zu {ref} melden.",f"Antwort zu {ref} irgendwann diese Woche.",f"Sofort antworten!!! {ref}"]
        topic="Fristsetzung"
    elif family==4:
        p=f"Für {ref} soll ein Angebot angefragt werden. Welche Formulierung ist vollständig?"
        c=f"Bitte senden Sie uns zu {ref} ein Angebot mit Preis, Lieferzeit und Zahlungsbedingungen bis zum {date}."
        w=[f"Was kostet {ref}?",f"Schicken Sie mal was zu {ref}.",f"Wir brauchen zu {ref} einen Preis, schnell."]
        topic="Anfrage"
    elif family==5:
        p=f"Rechnung {ref} ist überfällig. Welche erste Zahlungserinnerung ist angemessen?"
        c=f"Zu Rechnung {ref} konnten wir bislang keinen Zahlungseingang feststellen. Bitte prüfen Sie den Vorgang; sollte sich die Zahlung überschnitten haben, betrachten Sie diese Nachricht als gegenstandslos."
        w=[f"Zahlen Sie {ref} sofort!!!",f"Warum haben Sie {ref} noch nicht bezahlt?",f"Letzte Warnung zu {ref}, obwohl noch keine Erinnerung gesendet wurde."]
        topic="Zahlungserinnerung"
    elif family==6:
        p=f"Eine Verzögerung bei {ref} ist noch nicht abschließend geklärt. Welche Formulierung vermeidet eine ungesicherte Zusage?"
        c=f"Wir prüfen derzeit den aktuellen Stand zu {ref} und melden uns bis zum {date} mit einer belastbaren Rückmeldung."
        w=[f"{ref} ist garantiert morgen erledigt.",f"Bei {ref} wird schon alles klappen.",f"Wir wissen zu {ref} nichts und melden uns irgendwann."]
        topic="Sensible Formulierungen"
    elif family==7:
        p=f"Welche Reihenfolge eignet sich für eine geschäftliche Reklamation zu {ref}?"
        c=f"Bezug zu {ref} → Abweichung konkret nennen → gewünschte Korrektur → Frist/Rückmeldung"
        w=[f"Drohung → Gruß → Bezug zu {ref} → unklare Forderung",f"Nur Forderung zu {ref} ohne Sachverhalt",f"Grußformel → beliebige Details → keine Handlung zu {ref}"]
        topic="Aufbau geschäftlicher Schreiben"
    elif family==8:
        p=f"Wie sollte eine sachliche E-Mail zu {ref} abgeschlossen werden, wenn eine Rückmeldung benötigt wird?"
        c=f"Vielen Dank für Ihre Prüfung. Wir bitten um Rückmeldung zu {ref} bis zum {date}."
        w=[f"Na dann bis irgendwann wegen {ref}.",f"Melden!!! {ref}",f"Ich hoffe, Sie kriegen {ref} endlich hin."]
        topic="Anrede und Abschluss"
    elif family==9:
        p=f"Zu {ref} muss intern eine Entscheidung angefragt werden. Welche Formulierung ist professionell?"
        c=f"Bitte prüfen Sie den Vorgang {ref} und teilen Sie mir mit, ob die vorgeschlagene Vorgehensweise freigegeben werden kann."
        w=[f"Kann ich {ref} einfach machen?",f"Bitte {ref} irgendwie freigeben.",f"Ich mache {ref} jetzt, falls niemand widerspricht."]
        topic="Professioneller Ton"
    elif family==10:
        p=f"Für {ref} soll ein Statusupdate an einen Kunden gesendet werden. Welche Variante ist geeignet?"
        c=f"Der Vorgang {ref} befindet sich derzeit in Prüfung. Der nächste Bearbeitungsschritt ist eingeleitet; wir melden uns bis zum {date} erneut."
        w=[f"Bei {ref} passiert gerade nichts.",f"Keine Ahnung, wie lange {ref} dauert.",f"{ref} kommt bestimmt bald."]
        topic="E-Mail-Grundlagen"
    else:
        p=f"Welche Formulierung bleibt bei einer abgelehnten Forderung zu {ref} sachlich?"
        c=f"Nach Prüfung der vorliegenden Unterlagen können wir die Forderung zu {ref} derzeit nicht nachvollziehen. Gern prüfen wir ergänzende Nachweise."
        w=[f"Die Forderung {ref} ist Unsinn.",f"Keine Chance bei {ref}.",f"Wir lehnen {ref} ab, weil wir das so entschieden haben."]
        topic="Professioneller Ton"
    return choice(f"x_sv_{level[0]}_{i:03d}","Schriftverkehr",topic,level,p,c,w,
                  "Geschäftlicher Schriftverkehr sollte eindeutig, sachlich, höflich und nachvollziehbar sein.","Benenne Bezug, Sachverhalt und gewünschten nächsten Schritt.")

# ---------------------------------------------------------------------------
# TEST 1.2.1: Natürlichere Büroorganisationsfälle ohne sichtbare interne Codes.
# Die frühere Variante verwendete Kennungen wie B-A240 in den Antworttexten.
# Diese Funktion überschreibt die frühere _office_question zur Laufzeit.
# ---------------------------------------------------------------------------
def _office_question(level, i, Question, choice, number, money):
    family = (i - 1) % 12
    v = (i - 1) // 12
    names = ["Frau Neumann", "Herr Keller", "Frau Brandt", "Herr Peters", "Frau Vogel", "Herr Stein", "Frau Meyer", "Herr Wagner"]
    departments = ["Einkauf", "Vertrieb", "Buchhaltung", "Personal", "Logistik", "Service", "Disposition", "Verwaltung"]
    deadlines = ["heute um 12 Uhr", "heute um 14 Uhr", "bis Tagesende", "morgen früh", "innerhalb der nächsten Stunde", "bis Freitagmittag"]
    n = names[(i + v) % len(names)]
    dep = departments[(i * 2 + v) % len(departments)]
    dl = deadlines[(i + 2 * v) % len(deadlines)]

    # Formulierungsvarianten verhindern, dass innerhalb einer Familie immer
    # derselbe Antwortsatz erscheint.
    prio_correct = [
        "Zuerst die Folgen und die verbindliche Frist prüfen, danach die Aufgaben nach Dringlichkeit und Wichtigkeit ordnen.",
        "Die fristkritische Aufgabe absichern und anschließend die weniger dringenden Vorgänge strukturiert bearbeiten.",
        "Erst klären, welche Aufgabe bei Verzögerung den größten Schaden verursacht, dann die Reihenfolge festlegen.",
        "Frist, Auswirkung und Zuständigkeit vergleichen und daraus eine nachvollziehbare Priorität ableiten.",
    ]
    prio_wrong1 = [
        "Immer die zuletzt eingegangene Aufgabe zuerst erledigen, unabhängig von Fristen.",
        "Mit der angenehmsten Aufgabe beginnen und die dringenden Vorgänge später ansehen.",
        "Alle Aufgaben gleichzeitig anfangen, damit nichts liegen bleibt.",
        "Die Reihenfolge zufällig festlegen, wenn mehrere Aufgaben gleichzeitig eintreffen.",
    ]
    prio_wrong2 = [
        "Die interne Rückfrage grundsätzlich vor jeder Kunden- oder Fristsache bearbeiten.",
        "Nur den Umfang der Aufgabe beachten; mögliche Folgen spielen keine Rolle.",
        "Fristen erst prüfen, wenn eine Erinnerung eintrifft.",
        "Zunächst Routineablage erledigen, weil sie schnell abgeschlossen ist.",
    ]
    prio_wrong3 = [
        "Entscheidungen vermeiden und warten, bis jemand eine konkrete Reihenfolge vorgibt.",
        "Alle Vorgänge weiterleiten, auch wenn die Zuständigkeit bekannt ist.",
        "Nur nach Eingangszeit sortieren, ohne Bedeutung oder Termin zu berücksichtigen.",
        "Die Aufgabe mit der längsten Bearbeitungszeit automatisch an erste Stelle setzen.",
    ]
    pv = v % 4

    if family == 0:
        scenarios = [
            "Gleichzeitig gehen eine Kundenreklamation, eine interne Rückfrage und eine fristgebundene Freigabe ein.",
            "Im Postfach liegen eine Mahnung mit heutiger Frist, eine Terminbitte für nächste Woche und eine interne Statistik-Anfrage.",
            "Kurz vor Feierabend kommen ein dringender Lieferausfall, eine Routineablage und eine Rückfrage ohne feste Frist herein.",
            "Während einer laufenden Aufgabe meldet sich ein Kunde mit Terminbezug; zugleich wartet eine interne Freigabe bis heute.",
            "Drei Aufgaben stehen an: Rückruf mit zugesagter Uhrzeit, Bestellung ohne Eile und eine heute endende Angebotsfrist.",
            "Im Team treffen mehrere Aufgaben gleichzeitig ein, von denen nur eine eine verbindliche Außenfrist hat.",
        ]
        p = scenarios[v % len(scenarios)] + " Wie gehst du vor?"
        c = prio_correct[pv]
        w = [prio_wrong1[pv], prio_wrong2[(pv+1)%4], prio_wrong3[(pv+2)%4]]
        topic = "Komplexe Priorisierung" if level == "Experte" else "Prioritäten"

    elif family == 1:
        scenarios = [
            f"{n} verlässt den Arbeitsplatz für einige Minuten. Auf dem Bildschirm sind Kundendaten geöffnet.",
            "Du gehst in eine Besprechung und auf deinem Monitor ist eine Personaldatei sichtbar.",
            "Ein Besucher wartet im Büro, während auf dem Arbeitsplatz vertrauliche Daten offen angezeigt werden.",
            "Du musst den Arbeitsplatz kurzfristig verlassen; eine Anwendung mit personenbezogenen Daten ist geöffnet.",
        ]
        p = scenarios[v % len(scenarios)] + " Was ist richtig?"
        corrects = [
            "Den Bildschirm sperren und vertrauliche Unterlagen so sichern, dass Unbefugte keinen Zugriff haben.",
            "Arbeitsplatz und Anwendung sperren, bevor du den Raum verlässt.",
            "Sichtbare Unterlagen sichern und den Rechner gegen unbefugte Nutzung sperren.",
            "Vor dem Weggehen den Zugriff auf die geöffneten Daten technisch und organisatorisch absichern.",
        ]
        wrong = [
            "Nur den Monitor ausschalten; eine Bildschirmsperre ist nicht nötig.",
            "Die Daten geöffnet lassen, wenn die Abwesenheit voraussichtlich kurz ist.",
            "Das Fenster minimieren und den Rechner ansonsten frei zugänglich lassen.",
            "Vertrauliche Unterlagen offen liegen lassen, solange nur Kollegen im Raum sind.",
            "Den Browser schließen, aber den angemeldeten Rechner ungesperrt lassen.",
        ]
        c = corrects[pv]
        w = [wrong[(pv+j)%len(wrong)] for j in (0,1,2)]
        topic = "Datenschutz und Sicherheit"

    elif family == 2:
        docs = ["eine Eingangsrechnung", "einen abgeschlossenen Bestellvorgang", "ein Besprechungsprotokoll", "eine Kundenkorrespondenz", "eine Lieferantenvereinbarung", "eine interne Freigabe"]
        doc = docs[v % len(docs)]
        p = f"Im {dep} soll {doc} digital abgelegt werden. Welche Vorgehensweise ist am sinnvollsten?"
        corrects = [
            "Die Datei nach der festgelegten Ablagestruktur eindeutig benennen und am vorgesehenen Ort speichern.",
            "Den Vorgang nachvollziehbar zuordnen, eine klare Dateibezeichnung verwenden und die gültige Ablage nutzen.",
            "Nach dem betrieblichen Ablageplan speichern, sodass berechtigte Personen die Datei eindeutig wiederfinden.",
            "Eine eindeutige Zuordnung und Version sicherstellen und die Datei nur im vorgesehenen Bereich ablegen.",
        ]
        c = corrects[pv]
        wrong = [
            "Die Datei auf dem Desktop speichern, weil sie dort am schnellsten erreichbar ist.",
            "Mehrere Kopien in verschiedenen Ordnern ablegen, ohne die Version zu kennzeichnen.",
            "Einen privaten Ordner ohne einheitliche Struktur verwenden.",
            "Einen Dateinamen wie 'neu_final_final2' verwenden und auf eine Zuordnung verzichten.",
            "Die Datei ausschließlich per E-Mail an sich selbst schicken und nicht ablegen.",
        ]
        w = [wrong[(pv+j)%len(wrong)] for j in (0,1,2)]
        topic = "Ablage" if level == "Anfänger" else "Dokumentenmanagement"

    elif family == 3:
        meetings = ["eine Lieferantenbesprechung", "eine interne Projektbesprechung", "ein Kundengespräch", "eine Monatsauswertung", "eine Übergabebesprechung"]
        mt = meetings[v % len(meetings)]
        p = f"Du bereitest {mt} im Bereich {dep} vor. Welche Maßnahme verbessert die Organisation am stärksten?"
        corrects = [
            "Ziel, Teilnehmer, benötigte Unterlagen und Zeitrahmen vorab festlegen.",
            "Eine klare Agenda erstellen und notwendige Informationen rechtzeitig an die Beteiligten geben.",
            "Vorab klären, was entschieden werden soll und welche Unterlagen dafür gebraucht werden.",
            "Teilnehmerkreis, Themen, Verantwortlichkeiten und verfügbare Zeit vor der Besprechung abstimmen.",
        ]
        c = corrects[pv]
        wrong = [
            "Ohne Agenda starten und die Themen erst während der Besprechung sammeln.",
            "Möglichst viele Personen einladen, auch wenn sie keinen Bezug zum Thema haben.",
            "Unterlagen erst nach dem Termin verteilen, damit niemand vorab Fragen stellt.",
            "Die Dauer offenlassen und auf eine Zielsetzung verzichten.",
            "Nur den Raum buchen und alle weiteren Vorbereitungen spontan erledigen.",
        ]
        w = [wrong[(pv+j)%len(wrong)] for j in (0,2,3)]
        topic = "Besprechungsorganisation"

    elif family == 4:
        p = f"Für {n} überschneiden sich zwei wichtige Termine. Ein externer Termin ist verbindlich, der interne Termin kann verschoben werden. Was ist sinnvoll?"
        corrects = [
            "Die Bindung beider Termine prüfen, den flexibleren Termin abstimmen und die Änderung allen Beteiligten mitteilen.",
            "Den extern gebundenen Termin absichern und für den internen Termin rechtzeitig eine abgestimmte Alternative suchen.",
            "Priorität und Verschiebbarkeit klären und anschließend einen Termin transparent neu koordinieren.",
            "Die weniger flexible Verpflichtung beibehalten und die interne Überschneidung frühzeitig lösen.",
        ]
        c = corrects[pv]
        w = [
            "Beide Termine unverändert stehen lassen und erst kurz vorher entscheiden.",
            "Einen Termin ohne Information an die Beteiligten löschen.",
            "Erst nach Beginn des ersten Termins auf die Überschneidung hinweisen.",
            "Den externen Termin automatisch absagen, weil interne Termine Vorrang haben.",
            "Beide Termine bestätigen und davon ausgehen, dass sich die Überschneidung von selbst löst.",
        ][pv:pv+3] if pv <= 2 else [
            "Den externen Termin automatisch absagen, weil interne Termine Vorrang haben.",
            "Beide Termine bestätigen und davon ausgehen, dass sich die Überschneidung von selbst löst.",
            "Einen Termin ohne Information an die Beteiligten löschen.",
        ]
        topic = "Terminplanung"

    elif family == 5:
        issues = ["eine Lieferverzögerung", "eine fehlende Freigabe", "eine fehlerhafte Rechnung", "eine nicht erreichbare Ansprechperson", "eine drohende Terminüberschreitung"]
        issue = issues[v % len(issues)]
        p = f"Im {dep} gefährdet {issue} eine zugesagte Frist {dl}. Wie eskalierst du sinnvoll?"
        corrects = [
            "Die zuständige Person mit den relevanten Fakten informieren, Auswirkungen benennen und den nächsten Schritt dokumentieren.",
            "Sachverhalt, Frist und Risiko knapp zusammenfassen und an die tatsächlich zuständige Stelle eskalieren.",
            "Frühzeitig die richtige Verantwortungsebene einbinden und klar festhalten, welche Entscheidung benötigt wird.",
            "Die Eskalation mit Fakten, Terminbezug und einer konkreten Handlungsfrage nachvollziehbar weitergeben.",
        ]
        c = corrects[pv]
        wrong = [
            "Den Vorgang ohne Kontext an mehrere Personen gleichzeitig weiterleiten.",
            "Nur mündlich erwähnen, dass es ein Problem gibt, und nichts dokumentieren.",
            "Bis zum Ablauf der Frist warten, damit keine unnötige Unruhe entsteht.",
            "Die Nachricht an möglichst viele Empfänger senden, unabhängig von deren Zuständigkeit.",
            "Den Sachverhalt beschönigen und den Terminbezug weglassen.",
        ]
        w = [wrong[(pv+j)%len(wrong)] for j in (0,1,2)]
        topic = "Kommunikation und Eskalation"

    elif family == 6:
        p = "Mehrere Mitarbeitende bearbeiten dasselbe Dokument. Wie lässt sich Versionschaos am besten vermeiden?"
        corrects = [
            "Eindeutige Versionsstände und nachvollziehbare Dateinamen verwenden und die gültige Fassung klar kennzeichnen.",
            "Eine gemeinsame Ablage mit klarer Versionsregel nutzen und Änderungen nachvollziehbar dokumentieren.",
            "Festlegen, wo die aktuelle Fassung liegt, und ältere Versionen eindeutig von ihr unterscheiden.",
            "Mit verbindlicher Benennung und geregelter Ablage sicherstellen, dass alle an derselben gültigen Version arbeiten.",
        ]
        c = corrects[pv]
        wrong = [
            "Alle Fassungen gleich benennen und anhand des Änderungsdatums raten, welche aktuell ist.",
            "Jede Person speichert ihre eigene Kopie an einem beliebigen Ort.",
            "Dateien mit Namen wie 'final_neu2_wirklich_final' kennzeichnen.",
            "Änderungen nur mündlich ankündigen und auf eine gemeinsame Ablage verzichten.",
            "Die jeweils aktuelle Datei ausschließlich als E-Mail-Anhang verteilen.",
        ]
        w = [wrong[(pv+j)%len(wrong)] for j in (0,2,3)]
        topic = "Dokumentenmanagement"

    elif family == 7:
        tasks = ["eine Rückmeldung an einen Kunden", "eine Bestellfreigabe", "eine interne Auswertung", "eine Lieferantenanfrage", "eine Terminvorbereitung"]
        task = tasks[v % len(tasks)]
        p = f"Im {dep} muss {task} {dl} erledigt sein. Wie organisierst du die Aufgabe zuverlässig?"
        corrects = [
            "Termin, Zuständigkeit und Bearbeitungsstatus im vorgesehenen System erfassen.",
            "Die Aufgabe mit Fälligkeit und Verantwortlichkeit dokumentieren und den Fortschritt nachvollziehbar halten.",
            "Einen verbindlichen Termin setzen, die Zuständigkeit klären und die Aufgabe in der Arbeitsorganisation erfassen.",
            "Aufgabe, Frist und nächsten Schritt so festhalten, dass sie nicht nur vom Gedächtnis abhängen.",
        ]
        c = corrects[pv]
        wrong = [
            "Die Aufgabe nur im Gedächtnis behalten.",
            "Einen losen Zettel ohne Termin oder Verantwortlichkeit verwenden.",
            "Nur den Titel notieren und auf eine Fälligkeit verzichten.",
            "Die Aufgabe erst erfassen, wenn die Frist bereits überschritten ist.",
            "Die Zuständigkeit offenlassen, damit sich später jemand darum kümmert.",
        ]
        w = [wrong[(pv+j)%len(wrong)] for j in (0,1,3)]
        topic = "Arbeitsorganisation"

    elif family == 8:
        phishing = [
            "Eine unerwartete E-Mail fordert dich auf, dein Passwort über einen Link zu bestätigen.",
            "Ein unbekannter Absender schickt einen Anhang mit dem Hinweis 'dringende Rechnung'.",
            "Eine Nachricht wirkt wie vom Vorgesetzten, verlangt aber ungewöhnlich eine sofortige Anmeldung über einen fremden Link.",
            "Du erhältst eine Datei von einem Lieferanten, mit dem aktuell kein Vorgang besteht, und wirst zur Makro-Aktivierung aufgefordert.",
        ]
        p = phishing[v % len(phishing)] + " Wie reagierst du?"
        corrects = [
            "Nicht öffnen bzw. keine Zugangsdaten eingeben, Absender und Inhalt prüfen und nach interner Regel melden.",
            "Die Nachricht zunächst als verdächtig behandeln und den vorgesehenen Sicherheitsweg zur Prüfung nutzen.",
            "Keine Links oder Anhänge ausführen und die Echtheit über einen unabhängigen bekannten Kontaktweg prüfen.",
            "Die verdächtige Nachricht sichern bzw. melden, ohne die geforderte Aktion auszuführen.",
        ]
        c = corrects[pv]
        wrong = [
            "Den Anhang sofort öffnen, um zu sehen, ob er wirklich gefährlich ist.",
            "Das Passwort eingeben, wenn die Nachricht dringend formuliert ist.",
            "Die Nachricht an die private E-Mail-Adresse weiterleiten und dort testen.",
            "Den Link öffnen, solange auf der Seite ein Firmenlogo zu sehen ist.",
            "Die Sicherheitswarnung ignorieren, wenn der Absendername bekannt klingt.",
        ]
        w = [wrong[(pv+j)%len(wrong)] for j in (0,1,2)]
        topic = "Datenschutz und IT-Sicherheit"

    elif family == 9:
        p = f"{n} fällt kurzfristig aus. Was gehört in eine gute Übergabe an die Vertretung im Bereich {dep}?"
        corrects = [
            "Offene Aufgaben, Fristen, Ansprechpartner und Bearbeitungsstand strukturiert übergeben.",
            "Die laufenden Vorgänge mit Prioritäten, nächsten Schritten und wichtigen Terminen nachvollziehbar zusammenfassen.",
            "Kritische Fristen, Zuständigkeiten, offene Rückmeldungen und benötigte Unterlagen geordnet übergeben.",
            "So dokumentieren, was offen ist, dass die Vertretung ohne Rätselraten weiterarbeiten kann.",
        ]
        c = corrects[pv]
        wrong = [
            "Nur sagen, dass alle Informationen irgendwo im Ordner liegen.",
            "Fristen bewusst weglassen, damit die Übergabe kürzer ist.",
            "Die Vertretung ohne Zugriff auf die benötigten Unterlagen beginnen lassen.",
            "Nur bereits erledigte Aufgaben aufzählen und offene Punkte nicht erwähnen.",
            "Die Übergabe ausschließlich mündlich machen, obwohl mehrere Fristen laufen.",
        ]
        w = [wrong[(pv+j)%len(wrong)] for j in (0,1,2)]
        topic = "Prioritäten und Vertretung"

    elif family == 10:
        processes = ["die Rechnungsfreigabe", "die Postverteilung", "die Bestellprüfung", "die Terminabstimmung", "die Ablage von Lieferdokumenten", "die Bearbeitung von Kundenrückfragen"]
        proc = processes[v % len(processes)]
        p = f"Der wiederkehrende Prozess „{proc}“ dauert deutlich länger als geplant. Was ist ein sinnvoller Verbesserungsansatz?"
        corrects = [
            "Den tatsächlichen Ablauf aufnehmen, den Engpass bestimmen und eine überprüfbare Verbesserung vereinbaren.",
            "Zuerst feststellen, an welcher Stelle Zeit verloren geht, und anschließend gezielt dort ansetzen.",
            "Ablauf und Zuständigkeiten analysieren, Ursache benennen und die Wirkung einer Änderung später kontrollieren.",
            "Messbare Problemstellen identifizieren und eine konkrete Verbesserung mit Verantwortlichkeit testen.",
        ]
        c = corrects[pv]
        wrong = [
            "Den gesamten Prozess sofort ändern, ohne die Ursache zu prüfen.",
            "Die langsamste Person verantwortlich machen, ohne den Ablauf zu untersuchen.",
            "Kennzahlen und Rückmeldungen ignorieren und nur nach Gefühl umorganisieren.",
            "Zusätzliche Arbeitsschritte einführen, ohne zu prüfen, ob sie einen Nutzen haben.",
            "Den Prozess unverändert lassen und nur mehr Zeit dafür einplanen.",
        ]
        w = [wrong[(pv+j)%len(wrong)] for j in (0,1,2)]
        topic = "Prozessorganisation"

    else:
        scenarios = [
            "Eine wichtige Kundenreklamation muss geprüft werden, gleichzeitig wartet eine interne Rückfrage und eine Freigabe läuft heute ab.",
            "Ein Lieferant kündigt eine Verzögerung an, ein Kollege benötigt eine Entscheidung und eine zugesagte Kundenrückmeldung ist noch offen.",
            "Kurz vor einer Besprechung kommt eine dringende externe Anfrage herein, während eine interne Frist ebenfalls endet.",
            "Mehrere Vorgänge konkurrieren um Aufmerksamkeit: einer ist fristkritisch, einer hat hohe Kundenwirkung, einer ist reine Routine.",
            "Im Büro treffen gleichzeitig eine Eskalation, eine normale Anfrage und eine Aufgabe mit gesetzter Außenfrist ein.",
            "Du übernimmst mehrere offene Vorgänge einer erkrankten Kollegin; einige haben feste Termine, andere nicht.",
        ]
        p = scenarios[v % len(scenarios)] + " Wie gehst du vor?"
        c = prio_correct[(pv + 1) % 4]
        w = [prio_wrong1[(pv+2)%4], prio_wrong2[(pv+3)%4], prio_wrong3[pv]]
        topic = "Komplexe Priorisierung"

    # Expertenfragen sind sprachlich etwas anspruchsvoller, ohne bloß dieselbe
    # Antwort mit einer künstlichen Fallnummer zu versehen.
    if level == "Experte" and family in {0, 5, 10, 11}:
        p = p.replace("Wie gehst du vor?", "Welche Vorgehensweise ist unter Abwägung von Frist, Auswirkung und Zuständigkeit am sinnvollsten?")

    return choice(
        f"x_bo_{level[0]}_{i:03d}",
        "Büroorganisation",
        topic,
        level,
        p,
        c,
        w,
        "Die sinnvolle Lösung berücksichtigt Fristen, Auswirkungen, Zuständigkeit, Datenschutz und nachvollziehbare Organisation.",
        "Bewerte nicht nur die Reihenfolge, sondern auch Folgen, Fristen und Zuständigkeiten.",
    )


# ---------------------------------------------------------------------------
# TEST 1.3.2: Sichtbare interne Fall-/Vorgangsnummern entfernt.
# Interne IDs bleiben für Statistik und Historie stabil, werden aber niemals
# in Fragen, Antworten oder Erklärungen eingeblendet.
# ---------------------------------------------------------------------------
def _accounting_question(level, i, Question, choice, number, money):
    family = (i - 1) % 12
    products = ["Bürostühle", "Aktenordner", "Druckerpapier", "Monitore", "Schreibtischlampen", "Toner", "Versandkartons", "Headsets"]
    product = products[(i + family) % len(products)]

    if level == "Anfänger":
        if family == 0:
            base = Decimal(145 + i * 7); pct = Decimal([5, 8, 10, 12, 15, 20, 25][i % 7]); res = base*pct/100
            return number(f"x_rw_a_{i:03d}", "Rechnungswesen", "Prozentrechnung", level,
                          f"Wie viel sind {pct}% von {money(base)}?", res,
                          f"{money(base)} × {pct}/100 = {money(res)}.", "Grundwert × Prozentsatz ÷ 100.")
        if family == 1:
            price = Decimal(220 + i*9); pct = Decimal([5,10,15,20][i%4]); res=price*pct/100
            return number(f"x_rw_a_{i:03d}", "Rechnungswesen", "Rabatt", level,
                          f"{product} kosten insgesamt {money(price)}. Der Lieferant gewährt {pct}% Rabatt. Wie hoch ist der Rabattbetrag?", res,
                          f"Rabatt: {money(price)} × {pct}/100 = {money(res)}.", "Berechne den Rabatt vom Ausgangspreis.")
        if family == 2:
            net=Decimal(310+i*11); res=net*Decimal('0.19')
            return number(f"x_rw_a_{i:03d}", "Rechnungswesen", "Umsatzsteuer", level,
                          f"Eine Rechnung weist {money(net)} netto aus. Wie hoch ist die Umsatzsteuer bei 19%?", res,
                          f"{money(net)} × 19/100 = {money(res)}.", "19% vom Nettobetrag berechnen.")
        if family == 3:
            net=Decimal(265+i*13); gross=net*Decimal('1.19')
            return number(f"x_rw_a_{i:03d}", "Rechnungswesen", "Umsatzsteuer", level,
                          f"Eine Bestellung hat einen Nettowert von {money(net)}. Wie hoch ist der Bruttobetrag bei 19% Umsatzsteuer?", gross,
                          f"Brutto = {money(net)} × 1,19 = {money(gross)}.", "Netto × 1,19.")
        if family == 4:
            gross=Decimal(476+i*17); net=gross/Decimal('1.19')
            return number(f"x_rw_a_{i:03d}", "Rechnungswesen", "Umsatzsteuer", level,
                          f"Eine Rechnung beträgt {money(gross)} brutto. Wie hoch ist der Nettobetrag bei 19% Umsatzsteuer?", net,
                          f"Netto = {money(gross)} ÷ 1,19 = {money(net)}.", "Brutto durch 1,19 teilen.")
        if family == 5:
            qty=3+(i%12); unit=Decimal('24.50')+Decimal(i%20)*Decimal('3.25'); res=qty*unit
            return number(f"x_rw_a_{i:03d}", "Rechnungswesen", "Menge und Umsatzsteuer", level,
                          f"{qty} {product} kosten je {money(unit)} netto. Wie hoch ist der Nettogesamtbetrag?", res,
                          f"{qty} × {money(unit)} = {money(res)}.", "Menge × Einzelpreis.")
        if family == 6:
            old=Decimal(180+i*5); pct=Decimal([5,10,15][i%3]); new=old*(100+pct)/100
            return number(f"x_rw_a_{i:03d}", "Rechnungswesen", "Prozentrechnung", level,
                          f"Der Preis eines Artikels steigt von {money(old)} um {pct}%. Wie hoch ist der neue Preis?", new,
                          f"Erhöhung {money(old*pct/100)}, neuer Preis {money(new)}.", "Erst die Erhöhung berechnen, dann addieren.")
        if family == 7:
            old=Decimal(260+i*6); pct=Decimal([5,8,12,20][i%4]); new=old*(100-pct)/100
            return number(f"x_rw_a_{i:03d}", "Rechnungswesen", "Prozentrechnung", level,
                          f"Ein Artikel kostet regulär {money(old)} und wird um {pct}% reduziert. Wie hoch ist der neue Preis?", new,
                          f"Neuer Preis = {money(old)} × {(100-pct)}/100 = {money(new)}.", "Vom Ausgangswert den Prozentanteil abziehen.")
        if family == 8:
            gross=Decimal(500+i*8); sk=Decimal([2,3][i%2]); res=gross*sk/100
            return number(f"x_rw_a_{i:03d}", "Rechnungswesen", "Skonto", level,
                          f"Eine Rechnung über {money(gross)} erlaubt {sk}% Skonto. Wie hoch ist der Skontobetrag?", res,
                          f"{money(gross)} × {sk}/100 = {money(res)}.", "Skonto als Prozentsatz berechnen.")
        if family == 9:
            gross=Decimal(530+i*10); sk=Decimal([2,3][i%2]); pay=gross*(100-sk)/100
            return number(f"x_rw_a_{i:03d}", "Rechnungswesen", "Skonto", level,
                          f"Der Rechnungsbetrag beträgt {money(gross)}. Bei fristgerechter Zahlung dürfen {sk}% Skonto abgezogen werden. Wie viel wird überwiesen?", pay,
                          f"Zahlbetrag = {money(gross)} × {(100-sk)}/100 = {money(pay)}.", "Skonto vom Rechnungsbetrag abziehen.")
        if family == 10:
            listp=Decimal(420+i*12); rab=Decimal([5,10,15,20][i%4]); res=listp*(100-rab)/100
            return number(f"x_rw_a_{i:03d}", "Rechnungswesen", "Rabatt", level,
                          f"Der Listenpreis beträgt {money(listp)}. Es werden {rab}% Rabatt gewährt. Wie hoch ist der Preis nach Rabatt?", res,
                          f"{money(listp)} × {(100-rab)}/100 = {money(res)}.", "Rabatt vom Listenpreis abziehen.")
        qty=2+(i%9); unit=Decimal('59.90')+Decimal(i%14)*Decimal('2.50'); net=qty*unit; tax=net*Decimal('0.19')
        return number(f"x_rw_a_{i:03d}", "Rechnungswesen", "Menge und Umsatzsteuer", level,
                      f"Ein Unternehmen kauft {qty} {product} zu je {money(unit)} netto. Wie hoch ist nur die Umsatzsteuer für die Gesamtmenge?", tax,
                      f"Netto gesamt {money(net)}; davon 19% = {money(tax)}.", "Menge × Einzelpreis, davon 19%.")

    if level == "Fortgeschritten":
        qty=5+(i%18); unit=Decimal('38.50')+Decimal(i%25)*Decimal('4.10'); rab=Decimal([5,8,10,12,15][i%5]); sk=Decimal([2,3][i%2])
        if family in (0,1):
            net=qty*unit; after=net*(100-rab)/100; gross=after*Decimal('1.19')
            return number(f"x_rw_f_{i:03d}", "Rechnungswesen", "Rabatt und Umsatzsteuer", level,
                          f"Ein Unternehmen bestellt {qty} {product} zu je {money(unit)} netto. Es erhält {rab}% Rabatt. Anschließend kommen 19% Umsatzsteuer hinzu. Wie hoch ist der Bruttobetrag?", gross,
                          f"Netto {money(net)} → nach Rabatt {money(after)} → brutto {money(gross)}.", "Menge × Preis → Rabatt → Umsatzsteuer.")
        if family in (2,3):
            gross=Decimal(780+i*15); pay=gross*(100-sk)/100
            return number(f"x_rw_f_{i:03d}", "Rechnungswesen", "Skonto", level,
                          f"Eine Bruttorechnung beträgt {money(gross)}. Bei fristgerechter Zahlung gelten {sk}% Skonto. Wie hoch ist der Zahlbetrag?", pay,
                          f"{money(gross)} × {(100-sk)}/100 = {money(pay)}.", "Skonto vom Bruttobetrag abziehen.")
        if family in (4,5):
            gross=Decimal(950+i*19); net=gross/Decimal('1.19'); tax=gross-net
            return number(f"x_rw_f_{i:03d}", "Rechnungswesen", "Umsatzsteuer", level,
                          f"Eine Rechnung beträgt {money(gross)} brutto und enthält 19% Umsatzsteuer. Wie hoch ist der enthaltene Umsatzsteuerbetrag?", tax,
                          f"Netto {money(net)}, Umsatzsteuer {money(tax)}.", "Brutto ÷ 1,19, Differenz zum Brutto bilden.")
        if family in (6,7):
            ordered=10+(i%15); delivered=ordered-(1+i%3); net=delivered*unit; gross=net*Decimal('1.19')
            return number(f"x_rw_f_{i:03d}", "Rechnungswesen", "Rechnungsprüfung", level,
                          f"Bestellt wurden {ordered} {product}, geliefert aber nur {delivered}. Der Stückpreis beträgt {money(unit)} netto. Wie hoch ist der korrekte Bruttobetrag für die tatsächlich gelieferte Menge?", gross,
                          f"{delivered} × {money(unit)} = {money(net)} netto; brutto {money(gross)}.", "Nur die tatsächlich gelieferte Menge berechnen.")
        if family in (8,9):
            listp=qty*unit; after=listp*(100-rab)/100; saving=listp-after
            return number(f"x_rw_f_{i:03d}", "Rechnungswesen", "Rabatt", level,
                          f"{qty} {product} kosten je {money(unit)} netto. Der Lieferant gewährt {rab}% Rabatt auf den Gesamtwert. Wie hoch ist die gesamte Ersparnis?", saving,
                          f"Listenwert {money(listp)}, Rabattbetrag {money(saving)}.", "Rabatt auf den gesamten Warenwert berechnen.")
        net=qty*unit; after=net*(100-rab)/100; gross=after*Decimal('1.19'); pay=gross*(100-sk)/100
        return number(f"x_rw_f_{i:03d}", "Rechnungswesen", "Mehrstufige Rechnung", level,
                      f"Für {qty} {product} zu je {money(unit)} netto werden {rab}% Rabatt gewährt. Danach kommen 19% Umsatzsteuer hinzu; bei schneller Zahlung gelten {sk}% Skonto. Wie hoch ist der Zahlbetrag?", pay,
                      f"Netto {money(net)} → Rabatt {money(after)} → brutto {money(gross)} → Zahlbetrag {money(pay)}.", "Reihenfolge beachten: Rabatt vor Umsatzsteuer, Skonto danach.")

    qty=12+(i%20); unit=Decimal('52.40')+Decimal(i%30)*Decimal('3.70'); rab=Decimal([5,8,10,12,15][i%5]); sk=Decimal([2,3][i%2])
    if family in (0,1,2):
        net=qty*unit; after=net*(100-rab)/100; gross=after*Decimal('1.19'); pay=gross*(100-sk)/100
        return number(f"x_rw_e_{i:03d}", "Rechnungswesen", "Mehrstufige Rechnung", level,
                      f"Ein Unternehmen beschafft {qty} {product} zu je {money(unit)} netto. Der Lieferant gewährt {rab}% Rabatt. Nach 19% Umsatzsteuer können bei fristgerechter Zahlung noch {sk}% Skonto abgezogen werden. Welcher Betrag wird überwiesen?", pay,
                      f"{money(net)} → {money(after)} → {money(gross)} → {money(pay)}.", "Rabatt, Umsatzsteuer und Skonto in der richtigen Reihenfolge berücksichtigen.")
    if family in (3,4):
        ordered=qty; delivered=qty-(2+i%5); damaged=1+(i%2); billable=delivered-damaged; net=billable*unit*(100-rab)/100; gross=net*Decimal('1.19')
        return number(f"x_rw_e_{i:03d}", "Rechnungswesen", "Rechnungsprüfung", level,
                      f"Von {ordered} bestellten {product} werden nur {delivered} geliefert. Davon sind {damaged} nachweislich beschädigt und nicht berechenbar. Der Stückpreis beträgt {money(unit)} netto, vereinbart sind {rab}% Rabatt. Wie hoch ist der Bruttowert der berechenbaren Ware?", gross,
                      f"Berechenbar {billable} Stück; nach Rabatt netto {money(net)}, brutto {money(gross)}.", "Nur berechenbare Menge, Rabatt und Umsatzsteuer berücksichtigen.")
    if family in (5,6):
        gross=Decimal(1800+i*23); net=gross/Decimal('1.19'); target=net*(100-rab)/100
        return number(f"x_rw_e_{i:03d}", "Rechnungswesen", "Mehrstufige Rechnung", level,
                      f"Ein Bruttolistenwert von {money(gross)} enthält 19% Umsatzsteuer. Auf den daraus ermittelten Nettowert werden anschließend {rab}% Nachlass gewährt. Welcher Nettowert verbleibt?", target,
                      f"Netto vor Nachlass {money(net)}, nach {rab}% Nachlass {money(target)}.", "Zuerst Umsatzsteuer herausrechnen, dann Nachlass.")
    if family in (7,8):
        correct_net=qty*unit; invoiced_net=(qty+2)*unit; diff=(invoiced_net-correct_net)*Decimal('1.19')
        return number(f"x_rw_e_{i:03d}", "Rechnungswesen", "Rechnungsprüfung", level,
                      f"Geliefert wurden {qty} {product} zu je {money(unit)} netto, auf der Rechnung stehen jedoch {qty+2}. Wie hoch ist die Bruttodifferenz der zwei zu viel berechneten Stück?", diff,
                      f"Differenz netto {money(2*unit)}, brutto {money(diff)}.", "Nur die überberechnete Menge bewerten.")
    if family in (9,10):
        gross=Decimal(2200+i*29); pay=gross*(100-sk)/100; saved=gross-pay
        return number(f"x_rw_e_{i:03d}", "Rechnungswesen", "Skonto", level,
                      f"Eine Bruttorechnung über {money(gross)} kann bei fristgerechter Zahlung mit {sk}% Skonto beglichen werden. Wie groß ist der absolute finanzielle Vorteil?", saved,
                      f"Skontovorteil = {money(saved)}.", "Absolute Ersparnis durch Skonto berechnen.")
    net=qty*unit; after=net*(100-rab)/100; tax=after*Decimal('0.19')
    return number(f"x_rw_e_{i:03d}", "Rechnungswesen", "Rabatt und Umsatzsteuer", level,
                  f"{qty} {product} kosten je {money(unit)} netto. Nach {rab}% Rabatt wird 19% Umsatzsteuer berechnet. Wie hoch ist allein die Umsatzsteuer?", tax,
                  f"Nach Rabatt netto {money(after)}; davon 19% = {money(tax)}.", "Umsatzsteuer erst auf den rabattierten Nettowert berechnen.")


def _process_question(level, i, Question, choice, number, money):
    family=(i-1)%12
    product=["Bürostühle","Ordner","Druckerpapier","Monitore","Schreibtischlampen","Toner","Versandkartons","Headsets"][i%8]
    supplier=["Nordhandel GmbH","BüroPlus GmbH","OfficePro GmbH","Hansebedarf GmbH","WeserLogistik GmbH"][i%5]
    qty=10+(i%30)
    if family==0:
        p=f"Für das Büro werden {qty} {product} benötigt. Welcher Schritt gehört typischerweise vor die verbindliche Bestellung?"
        c="Geeignete Angebote prüfen und die Bestellung nach der vorgesehenen Freigabe auslösen."
        w=["Die Rechnung vorab als bezahlt buchen.","Den Wareneingang bestätigen, obwohl noch nichts geliefert wurde.","Eine Mahnung erstellen, obwohl noch keine Bestellung vorliegt."]
        topic="Ablauf"
    elif family==1:
        p=f"Von {supplier} wurden {qty} {product} bestellt, angekommen sind nur {qty-2}. Was ist zuerst zu tun?"
        c="Die Mengenabweichung dokumentieren und Bestellung, Lieferschein und tatsächliche Lieferung abgleichen."
        w=["Die volle Menge als erhalten buchen.","Die zwei fehlenden Stück privat nachkaufen.","Den Lieferschein ungeprüft ablegen."]
        topic="Mengenabweichung"
    elif family==2:
        p=f"Bei einer Lieferung von {supplier} sind mehrere {product} sichtbar beschädigt. Welche Reaktion ist kaufmännisch sinnvoll?"
        c="Den Schaden dokumentieren, die betroffene Menge festhalten und die Reklamation nach betrieblicher Vorgabe veranlassen."
        w=["Die beschädigte Ware ohne Dokumentation entsorgen.","Die Lieferung vollständig als mangelfrei bestätigen.","Die Schäden erst bei der nächsten Inventur erwähnen."]
        topic="Qualitätsabweichung"
    elif family==3:
        p="Eine Eingangsrechnung enthält eine Position, die weder in der Bestellung noch in der Auftragsbestätigung steht. Was ist sinnvoll?"
        c="Die nicht zuordenbare Position klären und die Rechnung bis zur Prüfung nicht ungeprüft freigeben."
        w=["Die Rechnung vollständig bezahlen und die Position ignorieren.","Die Bestellung nachträglich passend ändern.","Die Position auf irgendeine Kostenstelle buchen."]
        topic="Rechnungsprüfung"
    elif family==4:
        p=f"Der auf einer Rechnung ausgewiesene Rabatt weicht vom bestätigten Angebot von {supplier} ab. Welche Unterlagen sind für die Prüfung besonders wichtig?"
        c="Angebot, Bestellung beziehungsweise Auftragsbestätigung und Rechnung miteinander vergleichen."
        w=["Nur den Lieferschein prüfen, weil dort Preisvereinbarungen immer vollständig stehen.","Nur die aktuelle Preisliste ansehen und die konkrete Vereinbarung ignorieren.","Die Rechnung ohne Belegvergleich selbst ändern."]
        topic="Dokumente"
    elif family==5:
        p=f"{supplier} kündigt eine Lieferverzögerung an, durch die ein zugesagter Kundentermin gefährdet ist. Was ist sinnvoll?"
        c="Die Auswirkungen bewerten, Alternativen oder einen neuen Termin klären und betroffene Stellen rechtzeitig informieren."
        w=["Die Verzögerung verschweigen, bis der Kundentermin verstrichen ist.","Ohne Prüfung sofort alle Bestellungen beim Lieferanten stornieren.","Dem Kunden einen beliebigen neuen Termin versprechen."]
        topic="Lieferantenmanagement"
    elif family==6:
        p="Ware und Rechnungsbetrag sind korrekt, aber im System wurde die Fälligkeit falsch erfasst. Was ist zu tun?"
        c="Die Zahlungsbedingung anhand des Belegs prüfen und den korrekten Fälligkeitstermin erfassen."
        w=["Die Rechnung sicherheitshalber doppelt bezahlen.","Die Fälligkeit ignorieren, weil die Ware stimmt.","Die Liefermenge ändern, obwohl sie korrekt ist."]
        topic="Zahlungsabwicklung"
    elif family==7:
        p=f"Für {product} liegen drei Angebote verschiedener Lieferanten vor. Was gehört zu einem sachlichen Angebotsvergleich?"
        c="Preis, Leistung, Liefertermin, Zahlungsbedingungen und relevante Folgekosten vergleichbar bewerten."
        w=["Ausschließlich das schönste Angebotslayout auswählen.","Nur den niedrigsten Einzelpreis betrachten und alle Bedingungen ignorieren.","Das zuletzt eingegangene Angebot wählen."]
        topic="Angebotsvergleich"
    elif family==8:
        p="Eine Rechnung ist bereits bezahlt. Danach kündigt der Lieferant wegen einer berechtigten Korrektur eine Gutschrift an. Was ist sinnvoll?"
        c="Die Gutschrift dem ursprünglichen Geschäftsvorgang zuordnen und die finanzielle Korrektur nachvollziehbar überwachen."
        w=["Die Gutschrift löschen, weil die Rechnung schon bezahlt wurde.","Die ursprüngliche Rechnung nachträglich auf null setzen.","Die Gutschrift einem beliebigen anderen Lieferanten zuordnen."]
        topic="Zahlungsabwicklung"
    elif family==9:
        p=f"Der Lieferschein nennt {qty} {product}; bei der Zählung sind ebenfalls {qty} vorhanden. Was ist der nächste sinnvolle Kontrollschritt?"
        c="Zusätzlich Zustand und Qualität prüfen und den Wareneingang entsprechend dokumentieren."
        w=["Die Anzahl reicht aus; die Qualität muss nicht geprüft werden.","Den Lieferschein vernichten, sobald die Menge stimmt.","Die Rechnung unabhängig vom weiteren Belegfluss sofort bezahlen."]
        topic="Wareneingang"
    elif family==10:
        p="Eine Bestellung wurde nachträglich geändert, aber die Änderung ist nicht in allen Folgebelegen sichtbar. Was reduziert das Risiko weiterer Fehler?"
        c="Die Änderung eindeutig dokumentieren und sicherstellen, dass betroffene Personen und Folgebelege denselben Stand verwenden."
        w=["Mehrere widersprüchliche Versionen parallel weiterverwenden.","Die Änderung nur mündlich einer Person mitteilen.","Den ursprünglichen Vorgang ohne Referenz löschen und komplett neu beginnen."]
        topic="Kontrolle und Risikovermeidung"
    else:
        missing=2+i%4
        p=f"Bei einer Lieferung fehlen {missing} {product}; zusätzlich ist ein Teil der gelieferten Ware beschädigt. Wie sollte die Reklamation bearbeitet werden?"
        c=f"Mengen- und Qualitätsabweichung getrennt dokumentieren und mit {supplier} eine nachvollziehbare Korrektur abstimmen."
        w=["Nur die fehlende Menge beachten und die beschädigte Ware ignorieren.","Die gesamte Rechnung ungeprüft bezahlen.","Ohne Rücksprache die gesamte Geschäftsbeziehung beenden."]
        topic="Reklamation"
    return choice(f"x_gp_{level[0]}_{i:03d}","Geschäftsprozesse",topic,level,p,c,w,
                  "Geschäftsprozesse werden anhand von Belegen, tatsächlichem Sachverhalt und vereinbarten Bedingungen nachvollziehbar geprüft.","Vergleiche Soll, Ist und Belege.")


def _correspondence_question(level, i, Question, choice, number, money):
    family=(i-1)%12
    item=["Rechnung","Lieferung","Angebot","Gutschrift","Termin","Bestellung","Reklamation","Unterlagen"][i%8]
    date=["22. September","30. September","5. Oktober","12. Oktober","18. Oktober"][i%5]
    company=["Nordhandel GmbH","BüroPlus GmbH","OfficePro GmbH","Hansebedarf GmbH","WeserLogistik GmbH"][i%5]
    if family==0:
        p="Du möchtest eine fehlerhafte Rechnung per E-Mail reklamieren. Welcher Betreff ist am aussagekräftigsten?"
        c="Reklamation zur Rechnung – Bitte um Prüfung"
        w=["Wichtig!!!","Hallo","Problem mit Ihrer Firma"]
        topic="Betreff"
    elif family==1:
        p=f"Für die Bearbeitung einer {item.lower()} fehlen noch Unterlagen. Welche Formulierung ist sachlich und eindeutig?"
        c=f"Bitte senden Sie uns die noch fehlenden Unterlagen bis zum {date} zu."
        w=["Schicken Sie den Rest mal schnell.","Da fehlt noch was.","Unterlagen sofort!!!"]
        topic="Klare Formulierung"
    elif family==2:
        p=f"Bei einer Lieferung von {company} wurden zwei bestätigte Positionen nicht geliefert. Welche Reklamationsformulierung passt?"
        c="Bei der Prüfung der Lieferung haben wir festgestellt, dass zwei bestätigte Positionen fehlen. Bitte prüfen Sie die Nachlieferung."
        w=["Sie haben schon wieder alles falsch gemacht.","Da fehlt was, kümmern Sie sich.","Wir sind total sauer!!!"]
        topic="Reklamation"
    elif family==3:
        p="In einer geschäftlichen Nachricht soll eine klare Antwortfrist gesetzt werden. Welche Formulierung ist am besten?"
        c=f"Bitte senden Sie uns Ihre Rückmeldung bis spätestens {date}."
        w=["Bitte möglichst bald melden.","Antwort irgendwann diese Woche.","Sofort antworten!!!"]
        topic="Fristsetzung"
    elif family==4:
        p=f"Du möchtest bei {company} ein Angebot anfragen. Welche Formulierung ist vollständig?"
        c=f"Bitte senden Sie uns ein Angebot mit Preis, Lieferzeit und Zahlungsbedingungen bis zum {date}."
        w=["Was kostet das?","Schicken Sie mal ein Angebot.","Wir brauchen einen Preis, schnell."]
        topic="Anfrage"
    elif family==5:
        p="Eine Rechnung ist überfällig. Welche Formulierung eignet sich für eine erste freundliche Zahlungserinnerung?"
        c="Zu unserer Rechnung konnten wir bislang keinen Zahlungseingang feststellen. Bitte prüfen Sie den Vorgang; sollte sich die Zahlung überschnitten haben, betrachten Sie diese Nachricht als gegenstandslos."
        w=["Zahlen Sie sofort!!!","Warum haben Sie noch nicht bezahlt?","Letzte Warnung, obwohl noch keine Erinnerung gesendet wurde."]
        topic="Zahlungserinnerung"
    elif family==6:
        p="Eine Lieferverzögerung ist noch nicht abschließend geklärt. Welche Formulierung vermeidet eine ungesicherte Zusage?"
        c=f"Wir prüfen derzeit den aktuellen Stand und melden uns bis zum {date} mit einer belastbaren Rückmeldung."
        w=["Die Lieferung ist garantiert morgen da.","Das wird schon klappen.","Wir wissen nichts und melden uns irgendwann."]
        topic="Sensible Formulierungen"
    elif family==7:
        p="Welche Reihenfolge eignet sich für den Aufbau einer sachlichen geschäftlichen Reklamation?"
        c="Bezug nennen → Abweichung konkret beschreiben → gewünschte Korrektur formulieren → Frist oder Rückmeldung vereinbaren"
        w=["Drohung → Gruß → unklare Forderung → Bezug","Nur Forderung ohne Sachverhalt","Grußformel → beliebige Details → keine gewünschte Handlung"]
        topic="Aufbau geschäftlicher Schreiben"
    elif family==8:
        p="Wie sollte eine sachliche E-Mail abgeschlossen werden, wenn eine Rückmeldung bis zu einem bestimmten Termin benötigt wird?"
        c=f"Vielen Dank für Ihre Prüfung. Wir bitten um Rückmeldung bis zum {date}."
        w=["Na dann bis irgendwann.","Melden!!!","Ich hoffe, Sie kriegen das endlich hin."]
        topic="Anrede und Abschluss"
    elif family==9:
        p="Intern muss eine Entscheidung beziehungsweise Freigabe angefragt werden. Welche Formulierung ist professionell?"
        c="Bitte prüfen Sie den Vorgang und teilen Sie mir mit, ob die vorgeschlagene Vorgehensweise freigegeben werden kann."
        w=["Kann ich das einfach machen?","Bitte irgendwie freigeben.","Ich mache es jetzt, falls niemand widerspricht."]
        topic="Professioneller Ton"
    elif family==10:
        p="Ein Kunde wartet auf ein Statusupdate, die Bearbeitung ist aber noch nicht abgeschlossen. Welche Formulierung ist geeignet?"
        c=f"Der Vorgang befindet sich derzeit in Prüfung. Der nächste Bearbeitungsschritt ist eingeleitet; wir melden uns bis zum {date} erneut."
        w=["Es passiert gerade nichts.","Keine Ahnung, wie lange es dauert.","Das kommt bestimmt bald."]
        topic="E-Mail-Grundlagen"
    else:
        p="Eine Kundenforderung kann nach Prüfung der vorliegenden Unterlagen derzeit nicht anerkannt werden. Welche Formulierung bleibt sachlich?"
        c="Nach Prüfung der vorliegenden Unterlagen können wir die Forderung derzeit nicht nachvollziehen. Gern prüfen wir ergänzende Nachweise."
        w=["Die Forderung ist Unsinn.","Keine Chance.","Wir lehnen das ab, weil wir das so entschieden haben."]
        topic="Professioneller Ton"
    return choice(f"x_sv_{level[0]}_{i:03d}","Schriftverkehr",topic,level,p,c,w,
                  "Geschäftlicher Schriftverkehr sollte eindeutig, sachlich, höflich und nachvollziehbar sein.","Benenne Bezug, Sachverhalt und gewünschten nächsten Schritt.")


# 1.3.2 Nachschärfung: Antwortsets bleiben kontextbezogen verschieden,
# ohne künstliche Fallcodes einzublenden.
def _process_question(level, i, Question, choice, number, money):
    family=(i-1)%12
    product=["Bürostühle","Ordner","Druckerpapier","Monitore","Schreibtischlampen","Toner","Versandkartons","Headsets"][i%8]
    supplier=["Nordhandel GmbH","BüroPlus GmbH","OfficePro GmbH","Hansebedarf GmbH","WeserLogistik GmbH"][i%5]
    qty=10+i  # bewusst eindeutig, aber weiterhin realistische Beschaffungsmengen
    batch=f"{qty} {product}"
    if family==0:
        p=f"Für das Büro werden {batch} benötigt. Welcher Schritt gehört typischerweise vor die verbindliche Bestellung?"
        c=f"Geeignete Angebote für {batch} prüfen und die Bestellung nach der vorgesehenen Freigabe auslösen."
        w=[f"Eine Rechnung über {batch} vorab als bezahlt buchen.",f"Den Wareneingang für {batch} bestätigen, obwohl noch nichts geliefert wurde.",f"Eine Mahnung wegen {batch} erstellen, obwohl noch keine Bestellung vorliegt."]
        topic="Ablauf"
    elif family==1:
        p=f"Von {supplier} wurden {batch} bestellt, angekommen sind nur {qty-2} Stück. Was ist zuerst zu tun?"
        c=f"Die Mengenabweichung bei den {batch} dokumentieren und Bestellung, Lieferschein und tatsächliche Lieferung abgleichen."
        w=[f"Alle {batch} als erhalten buchen.",f"Die zwei fehlenden {product} privat nachkaufen.",f"Den Lieferschein über {batch} ungeprüft ablegen."]
        topic="Mengenabweichung"
    elif family==2:
        p=f"Bei einer Lieferung von {batch} durch {supplier} sind mehrere Stück sichtbar beschädigt. Welche Reaktion ist kaufmännisch sinnvoll?"
        c=f"Den Schaden an den {batch} dokumentieren, die betroffene Menge festhalten und die Reklamation nach betrieblicher Vorgabe veranlassen."
        w=[f"Beschädigte Stück aus den {batch} ohne Dokumentation entsorgen.",f"Die Lieferung der {batch} vollständig als mangelfrei bestätigen.",f"Die Schäden an den {batch} erst bei der nächsten Inventur erwähnen."]
        topic="Qualitätsabweichung"
    elif family==3:
        p=f"Eine Eingangsrechnung über {batch} enthält eine zusätzliche Position, die weder in Bestellung noch Auftragsbestätigung steht. Was ist sinnvoll?"
        c=f"Die nicht zuordenbare Position zur Rechnung über {batch} klären und die Rechnung bis dahin nicht ungeprüft freigeben."
        w=[f"Die Rechnung über {batch} vollständig bezahlen und die zusätzliche Position ignorieren.",f"Die Bestellung über {batch} nachträglich passend ändern.",f"Die zusätzliche Position einfach auf irgendeine Kostenstelle buchen."]
        topic="Rechnungsprüfung"
    elif family==4:
        p=f"Der Rechnungsrabatt für {batch} weicht vom bestätigten Angebot von {supplier} ab. Welche Unterlagen sind besonders wichtig?"
        c=f"Angebot, Bestellung beziehungsweise Auftragsbestätigung und Rechnung für {batch} miteinander vergleichen."
        w=[f"Nur den Lieferschein über {batch} prüfen, weil dort Preisvereinbarungen immer vollständig stehen.",f"Nur die aktuelle Preisliste von {supplier} ansehen und die konkrete Vereinbarung über {batch} ignorieren.",f"Die Rechnung über {batch} ohne Belegvergleich selbst ändern."]
        topic="Dokumente"
    elif family==5:
        p=f"{supplier} kündigt für {batch} eine Lieferverzögerung an, durch die ein Kundentermin gefährdet ist. Was ist sinnvoll?"
        c=f"Die Auswirkungen der Verzögerung bei {batch} bewerten, Alternativen oder einen neuen Termin klären und betroffene Stellen rechtzeitig informieren."
        w=[f"Die Verzögerung bei {batch} verschweigen, bis der Kundentermin verstrichen ist.",f"Wegen der {batch} sofort alle Bestellungen bei {supplier} stornieren.",f"Für die {batch} ohne Prüfung einen beliebigen neuen Termin versprechen."]
        topic="Lieferantenmanagement"
    elif family==6:
        p=f"Ware und Rechnungsbetrag für {batch} sind korrekt, aber im System wurde die Fälligkeit falsch erfasst. Was ist zu tun?"
        c=f"Die Zahlungsbedingung der Rechnung über {batch} prüfen und den korrekten Fälligkeitstermin erfassen."
        w=[f"Die Rechnung über {batch} sicherheitshalber doppelt bezahlen.",f"Die Fälligkeit für {batch} ignorieren, weil die Ware stimmt.",f"Die Liefermenge der {batch} ändern, obwohl sie korrekt ist."]
        topic="Zahlungsabwicklung"
    elif family==7:
        p=f"Für {batch} liegen drei Angebote verschiedener Lieferanten vor. Was gehört zu einem sachlichen Angebotsvergleich?"
        c=f"Für die {batch} Preis, Leistung, Liefertermin, Zahlungsbedingungen und relevante Folgekosten vergleichbar bewerten."
        w=[f"Für die {batch} ausschließlich das schönste Angebotslayout auswählen.",f"Bei den {batch} nur den niedrigsten Einzelpreis betrachten und alle Bedingungen ignorieren.",f"Für die {batch} das zuletzt eingegangene Angebot wählen."]
        topic="Angebotsvergleich"
    elif family==8:
        p=f"Eine Rechnung über {batch} ist bereits bezahlt. Danach kündigt {supplier} wegen einer berechtigten Korrektur eine Gutschrift an. Was ist sinnvoll?"
        c=f"Die Gutschrift für {batch} dem ursprünglichen Geschäftsvorgang zuordnen und die finanzielle Korrektur nachvollziehbar überwachen."
        w=[f"Die Gutschrift für {batch} löschen, weil die Rechnung schon bezahlt wurde.",f"Die ursprüngliche Rechnung über {batch} nachträglich auf null setzen.",f"Die Gutschrift für {batch} einem beliebigen anderen Lieferanten zuordnen."]
        topic="Zahlungsabwicklung"
    elif family==9:
        p=f"Der Lieferschein nennt {batch}; bei der Zählung ist die Menge vollständig. Was ist der nächste sinnvolle Kontrollschritt?"
        c=f"Bei den {batch} zusätzlich Zustand und Qualität prüfen und den Wareneingang entsprechend dokumentieren."
        w=[f"Bei den {batch} reicht die Anzahl aus; die Qualität muss nicht geprüft werden.",f"Den Lieferschein über {batch} vernichten, sobald die Menge stimmt.",f"Die Rechnung über {batch} unabhängig vom weiteren Belegfluss sofort bezahlen."]
        topic="Wareneingang"
    elif family==10:
        p=f"Eine Bestellung über {batch} wurde nachträglich geändert, aber die Änderung ist nicht in allen Folgebelegen sichtbar. Was reduziert das Risiko weiterer Fehler?"
        c=f"Die Änderung der Bestellung über {batch} eindeutig dokumentieren und sicherstellen, dass alle betroffenen Personen und Folgebelege denselben Stand verwenden."
        w=[f"Für die {batch} mehrere widersprüchliche Versionen parallel weiterverwenden.",f"Die Änderung bei den {batch} nur mündlich einer Person mitteilen.",f"Die ursprüngliche Bestellung über {batch} ohne nachvollziehbare Verbindung löschen und komplett neu beginnen."]
        topic="Kontrolle und Risikovermeidung"
    else:
        missing=2+i%4
        p=f"Bei einer Lieferung von {batch} fehlen {missing} Stück; zusätzlich ist ein Teil der gelieferten Ware beschädigt. Wie sollte die Reklamation bearbeitet werden?"
        c=f"Mengen- und Qualitätsabweichung bei den {batch} getrennt dokumentieren und mit {supplier} eine nachvollziehbare Korrektur abstimmen."
        w=[f"Bei den {batch} nur die fehlende Menge beachten und die beschädigte Ware ignorieren.",f"Die Rechnung für die {batch} ungeprüft vollständig bezahlen.",f"Wegen der {batch} ohne Rücksprache die gesamte Geschäftsbeziehung mit {supplier} beenden."]
        topic="Reklamation"
    return choice(f"x_gp_{level[0]}_{i:03d}","Geschäftsprozesse",topic,level,p,c,w,
                  "Geschäftsprozesse werden anhand von Belegen, tatsächlichem Sachverhalt und vereinbarten Bedingungen nachvollziehbar geprüft.","Vergleiche Soll, Ist und Belege.")


def _correspondence_question(level, i, Question, choice, number, money):
    family=(i-1)%12
    item=["Rechnung","Lieferung","Angebot","Gutschrift","Termin","Bestellung","Reklamation","Unterlagen"][i%8]
    months=["Januar","Februar","März","April","Mai","Juni","Juli","August","September","Oktober","November","Dezember"]
    day=1+((i-1)%28); month=months[((i-1)//28)%12]; date=f"{day}. {month}"
    company=["Nordhandel GmbH","BüroPlus GmbH","OfficePro GmbH","Hansebedarf GmbH","WeserLogistik GmbH","Elbe Büroservice GmbH","Mittelweser Handel GmbH"][i%7]
    if family==0:
        p=f"Du möchtest eine fehlerhafte Rechnung von {company} reklamieren. Welcher Betreff ist am aussagekräftigsten?"
        c=f"Reklamation zur Rechnung vom {date} – Bitte um Prüfung"
        w=[f"Wichtig – Rechnung vom {date}",f"Hallo wegen der Rechnung vom {date}",f"Problem!!! Rechnung {date}"]
        topic="Betreff"
    elif family==1:
        p=f"Für die Bearbeitung einer {item.lower()} fehlen noch Unterlagen. Welche Formulierung ist sachlich und eindeutig?"
        c=f"Bitte senden Sie uns die noch fehlenden Unterlagen bis zum {date} zu."
        w=[f"Schicken Sie den Rest bis {date} mal schnell.",f"Da fehlt noch was; am besten bis {date}.",f"Unterlagen bis {date} sofort!!!"]
        topic="Klare Formulierung"
    elif family==2:
        p=f"Bei einer Lieferung von {company} wurden zwei bestätigte Positionen nicht geliefert. Welche Reklamationsformulierung passt?"
        c=f"Bei der Prüfung der Lieferung haben wir festgestellt, dass zwei bestätigte Positionen fehlen. Bitte teilen Sie uns bis zum {date} mit, wann die Nachlieferung erfolgt."
        w=[f"Sie haben schon wieder alles falsch gemacht. Antworten Sie bis {date}.",f"Da fehlt was, kümmern Sie sich bis {date}.",f"Wir sind total sauer!!! Rückmeldung bis {date}."]
        topic="Reklamation"
    elif family==3:
        p="In einer geschäftlichen Nachricht soll eine klare Antwortfrist gesetzt werden. Welche Formulierung ist am besten?"
        c=f"Bitte senden Sie uns Ihre Rückmeldung bis spätestens {date}."
        w=[f"Bitte möglichst bald, vielleicht bis {date}, melden.",f"Antwort irgendwann um den {date} herum.",f"Sofort antworten!!! Spätestens {date}."]
        topic="Fristsetzung"
    elif family==4:
        p=f"Du möchtest bei {company} ein Angebot anfragen. Welche Formulierung ist vollständig?"
        c=f"Bitte senden Sie uns ein Angebot mit Preis, Lieferzeit und Zahlungsbedingungen bis zum {date}."
        w=[f"Was kostet das? Bitte bis {date} antworten.",f"Schicken Sie bis {date} mal ein Angebot.",f"Wir brauchen bis {date} einen Preis, schnell."]
        topic="Anfrage"
    elif family==5:
        p=f"Eine Rechnung von {company} mit Rechnungsdatum {date} ist überfällig. Welche Formulierung eignet sich für eine erste freundliche Zahlungserinnerung?"
        c=f"Zu unserer Rechnung vom {date} konnten wir bislang keinen Zahlungseingang feststellen. Bitte prüfen Sie den Vorgang; sollte sich die Zahlung überschnitten haben, betrachten Sie diese Nachricht als gegenstandslos."
        w=[f"Zahlen Sie die Rechnung vom {date} sofort!!!",f"Warum haben Sie die Rechnung vom {date} noch nicht bezahlt?",f"Letzte Warnung zur Rechnung vom {date}, obwohl noch keine Erinnerung gesendet wurde."]
        topic="Zahlungserinnerung"
    elif family==6:
        p=f"Eine Lieferverzögerung bei {company} ist noch nicht abschließend geklärt. Welche Formulierung vermeidet eine ungesicherte Zusage?"
        c=f"Wir prüfen derzeit den aktuellen Stand und melden uns bis zum {date} mit einer belastbaren Rückmeldung."
        w=[f"Die Lieferung ist garantiert noch vor dem {date} da.",f"Bis {date} wird das schon klappen.",f"Wir wissen nichts und melden uns vielleicht nach dem {date}."]
        topic="Sensible Formulierungen"
    elif family==7:
        p="Welche Reihenfolge eignet sich für den Aufbau einer sachlichen geschäftlichen Reklamation?"
        c=f"Bezug nennen → Abweichung konkret beschreiben → gewünschte Korrektur formulieren → Rückmeldung bis {date} erbitten"
        w=[f"Drohung → Gruß → unklare Forderung → irgendwann vor {date} Bezug nennen",f"Nur Forderung ohne Sachverhalt → Frist {date}",f"Grußformel → beliebige Details → bis {date} keine gewünschte Handlung nennen"]
        topic="Aufbau geschäftlicher Schreiben"
    elif family==8:
        p="Wie sollte eine sachliche E-Mail abgeschlossen werden, wenn eine Rückmeldung bis zu einem bestimmten Termin benötigt wird?"
        c=f"Vielen Dank für Ihre Prüfung. Wir bitten um Rückmeldung bis zum {date}."
        w=[f"Na dann bis irgendwann, spätestens {date}.",f"Melden!!! Bis {date}.",f"Ich hoffe, Sie kriegen das bis {date} endlich hin."]
        topic="Anrede und Abschluss"
    elif family==9:
        p="Intern muss eine Entscheidung beziehungsweise Freigabe angefragt werden. Welche Formulierung ist professionell?"
        c=f"Bitte prüfen Sie den Vorgang und teilen Sie mir bis zum {date} mit, ob die vorgeschlagene Vorgehensweise freigegeben werden kann."
        w=[f"Kann ich das bis {date} einfach machen?",f"Bitte bis {date} irgendwie freigeben.",f"Ich mache es am {date}, falls niemand widerspricht."]
        topic="Professioneller Ton"
    elif family==10:
        p="Ein Kunde wartet auf ein Statusupdate, die Bearbeitung ist aber noch nicht abgeschlossen. Welche Formulierung ist geeignet?"
        c=f"Der Vorgang befindet sich derzeit in Prüfung. Der nächste Bearbeitungsschritt ist eingeleitet; wir melden uns bis zum {date} erneut."
        w=[f"Bis {date} passiert wahrscheinlich nichts.",f"Keine Ahnung, ob es bis {date} fertig ist.",f"Das kommt bestimmt irgendwann vor dem {date}."]
        topic="E-Mail-Grundlagen"
    else:
        p="Eine Kundenforderung kann nach Prüfung der vorliegenden Unterlagen derzeit nicht anerkannt werden. Welche Formulierung bleibt sachlich?"
        c=f"Nach Prüfung der vorliegenden Unterlagen können wir die Forderung derzeit nicht nachvollziehen. Gern prüfen wir ergänzende Nachweise, wenn Sie diese bis zum {date} einreichen."
        w=[f"Die Forderung ist Unsinn; weitere Unterlagen bis {date} ändern daran nichts.",f"Keine Chance, auch nicht bis {date}.",f"Wir lehnen das ab. Wenn Sie möchten, können Sie bis {date} trotzdem etwas schicken."]
        topic="Professioneller Ton"
    return choice(f"x_sv_{level[0]}_{i:03d}","Schriftverkehr",topic,level,p,c,w,
                  "Geschäftlicher Schriftverkehr sollte eindeutig, sachlich, höflich und nachvollziehbar sein.","Benenne Bezug, Sachverhalt und gewünschten nächsten Schritt.")
