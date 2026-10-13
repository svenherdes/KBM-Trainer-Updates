"""KBM 1.4.3: additive Lernfragen, ohne Eingriff in bestehende Fragen/Profil-Daten.

600 Aufgaben: Finanzbuchhaltung 180, kaufmännische Steuerung 180,
Einkauf 120, Logistik 120. Zu jeder Stufe separate Aufgabenvarianten.
"""
from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP

LEVELS = ('Anfänger', 'Fortgeschritten', 'Experte')
RW = 'Rechnungswesen'
GP = 'Geschäftsprozesse'
D = lambda x: Decimal(str(x))


def build_knowledge_143(Question, choice, money):
    out = []
    counters = {}
    def amt(value):
        return D(value).quantize(D('0.01'), rounding=ROUND_HALF_UP)
    def addn(cat, topic, lvl, key, prompt, value, unit, explanation, hint):
        idx = counters.get((key, lvl), 0) + 1
        counters[(key, lvl)] = idx
        val = amt(value)
        if unit != '€':
            prompt += ' Bitte nur die Zahl ohne Einheit eingeben.'
        if unit == '€':
            correct = money(val)
        elif unit == '%':
            correct = str(val.normalize()).replace('.', ',')
        elif unit == 'Stück':
            correct = str(val.normalize()).replace('.', ',')
        else:
            correct = str(val.normalize()).replace('.', ',')
        out.append(Question(f'kb143_{key}_{lvl[0]}_{idx:03d}', cat, topic, lvl, prompt, 'number', correct,
                            explanation, None, hint))
    def addc(cat, topic, lvl, key, prompt, correct, wrong, explanation, hint):
        idx = counters.get((key, lvl), 0) + 1
        counters[(key, lvl)] = idx
        assert len(wrong) == 3 and len({correct, *wrong}) == 4, (key, prompt)
        out.append(choice(f'kb143_{key}_{lvl[0]}_{idx:03d}', cat, topic, lvl, prompt, correct, wrong, explanation, hint))
    def calc(cat, topic, lvl, key, prompt, val, unit, equation, hint):
        addn(cat, topic, lvl, key, prompt, val, unit, equation, hint)

    finance_topics = [
        ('fibu_bilanz', 'FiBu: Bilanz und Inventur', 12),
        ('fibu_buchung', 'FiBu: Buchungssätze', 24),
        ('fibu_steuer', 'FiBu: Steuerbuchungen', 12),
        ('fibu_guv', 'FiBu: Abschreibung und GuV', 12),
    ]
    steering_topics = [
        ('steuer_kosten', 'Steuerung: Kostenrechnung', 15),
        ('steuer_bab', 'Steuerung: Kostenstellen und BAB', 15),
        ('steuer_db', 'Steuerung: Deckungsbeitrag', 15),
        ('steuer_budget', 'Steuerung: Kennzahlen und Budget', 15),
    ]
    buying_topics = [
        ('einkauf_bedarf', 'Einkauf: Bedarf und Bestellung', 12),
        ('einkauf_nutzwert', 'Einkauf: Lieferantenbewertung', 12),
        ('einkauf_strategie', 'Einkauf: Beschaffungsstrategie', 8),
        ('einkauf_controlling', 'Einkauf: Kennzahlen und Controlling', 8),
    ]
    logistics_topics = [
        ('logistik_lager', 'Logistik: Lagerkennzahlen', 12),
        ('logistik_abc', 'Logistik: ABC- und XYZ-Analyse', 10),
        ('logistik_kommission', 'Logistik: Kommissionierung und Versand', 10),
        ('logistik_transport', 'Logistik: Transport und Kosten', 8),
    ]

    # Geschäftsvorgänge mit buchhalterisch korrekter Soll-Haben-Logik.
    booking_cases = [
        ('Ein Bürostuhl wird auf Ziel eingekauft (netto).', 'Büroausstattung', 'Verbindlichkeiten aus Lieferungen und Leistungen'),
        ('Eine offene Kundenrechnung wird per Banküberweisung bezahlt.', 'Bank', 'Forderungen aus Lieferungen und Leistungen'),
        ('Eine offene Lieferantenrechnung wird per Bank beglichen.', 'Verbindlichkeiten aus Lieferungen und Leistungen', 'Bank'),
        ('Bargeld wird vom Bankkonto für die Kasse abgehoben.', 'Kasse', 'Bank'),
        ('Bargeld wird von der Kasse auf das Bankkonto eingezahlt.', 'Bank', 'Kasse'),
        ('Ein Unternehmer legt Geld aus dem Privatvermögen auf das betriebliche Bankkonto ein.', 'Bank', 'Privateinlagen'),
        ('Eine Beratungsleistung wird auf Ziel verkauft (netto).', 'Forderungen aus Lieferungen und Leistungen', 'Umsatzerlöse'),
        ('Eine bereits bestehende Bankverbindlichkeit wird per Überweisung getilgt.', 'Darlehensverbindlichkeiten', 'Bank'),
        ('Ein Darlehen wird auf das Geschäftskonto ausgezahlt.', 'Bank', 'Darlehensverbindlichkeiten'),
        ('Büromaterial wird gegen Barzahlung eingekauft (netto).', 'Büromaterialaufwand', 'Kasse'),
        ('Ein Kunde bezahlt eine Barverkaufsleistung (netto).', 'Kasse', 'Umsatzerlöse'),
        ('Die Miete für das Büro wird überwiesen.', 'Mietaufwand', 'Bank'),
    ]
    accounts = ['Bank','Kasse','Forderungen aus Lieferungen und Leistungen','Verbindlichkeiten aus Lieferungen und Leistungen',
                'Büroausstattung','Umsatzerlöse','Büromaterialaufwand','Mietaufwand','Darlehensverbindlichkeiten','Privateinlagen']
    for li, lvl in enumerate(LEVELS):
        for key, topic, count in finance_topics:
            for k in range(count):
                n = k + 1
                a = D(150 + 37*n + 190*li)
                b = D(75 + 19*n + 95*li)
                if key == 'fibu_bilanz':
                    mode = k % 4
                    if mode == 0:
                        if li == 0:
                            calc(RW,topic,lvl,key,f'Betrieb Fall B{li+1}-{n}: Vermögen {money(a*10)}, Schulden {money(b*3)}. Wie hoch ist das Eigenkapital?',a*10-b*3,'€',f'Eigenkapital = Vermögen {money(a*10)} minus Schulden {money(b*3)}.','Bilanzgleichung anwenden.')
                        elif li == 1:
                            calc(RW,topic,lvl,key,f'Inventar B{li+1}-{n}: Kasse {money(a)}, Bank {money(a*2)}, Fuhrpark {money(a*3)} und Schulden {money(b*2)}. Welches Eigenkapital ergibt sich?',a*6-b*2,'€',f'Eigenkapital = alle Vermögenswerte {money(a*6)} minus Fremdkapital {money(b*2)}.','Inventarwerte addieren und Schulden abziehen.')
                        else:
                            calc(RW,topic,lvl,key,f'Bilanzvergleich B{li+1}-{n}: Eigenkapital zu Jahresbeginn {money(a*5)}, am Jahresende {money(a*6)}. Privatentnahme {money(b)}, Privateinlage {money(b*2)}. Wie hoch ist der Gewinn durch Betriebsvermögensvergleich?',a+b-b*2,'€',f'Gewinn = End-EK {money(a*6)} minus Anfangs-EK {money(a*5)} plus Entnahme {money(b)} minus Einlage {money(b*2)}.','Privatvorgänge beim Eigenkapitalvergleich bereinigen.')
                    elif mode == 1:
                        v = [
                            ('Inventur', 'Die mengen- und wertmäßige Bestandsaufnahme zu einem Stichtag', 'Das Verzeichnis der Einnahmen','Eine Kundenrechnung','Die Buchung einer Miete'),
                            ('Inventar', 'Das ausführliche Verzeichnis von Vermögen und Schulden', 'Eine verkürzte Bilanzsumme','Der Wareneingangsstempel','Der Jahresumsatz'),
                            ('Bilanz', 'Die Gegenüberstellung von Aktiva und Passiva', 'Eine Liste offener Termine','Die Summe der Versandkosten','Die Warenbestellung'),
                        ][li]
                        addc(RW,topic,lvl,key,f'Fall B{li+1}-{n}: Welche Beschreibung trifft auf „{v[0]}“ zu?',v[1],list(v[2:]),f'{v[0]}: {v[1]}.','Inventur, Inventar und Bilanz auseinanderhalten.')
                    elif mode == 2:
                        if li == 0:
                            calc(RW,topic,lvl,key,f'Bei der Inventur B{n} werden {12+n} Ordner zu je {money(b)} gezählt. Welcher Bestandswert ergibt sich?',D(12+n)*b,'€',f'Bestandswert = {12+n} × {money(b)}.','Menge mal Wert pro Stück.')
                        elif li == 1:
                            calc(RW,topic,lvl,key,f'Die Bilanz B{n} enthält Anlagevermögen {money(a*4)} und Umlaufvermögen {money(a*2)}. Das Eigenkapital beträgt {money(b*3)}. Wie hoch ist das Fremdkapital?',a*6-b*3,'€',f'Bilanzsumme {money(a*6)} minus Eigenkapital {money(b*3)}.','Aktiva entsprechen dem Gesamtkapital.')
                        else:
                            calc(RW,topic,lvl,key,f'Bilanz B{n}: Aktiva vor Zahlung {money(a*8)}. Eine Verbindlichkeit von {money(b)} wird vom Bankkonto getilgt. Wie hoch ist die neue Bilanzsumme?',a*8-b,'€',f'Aktiv- und Passivseite sinken um {money(b)} (Aktiv-Passiv-Minderung).','Zahlung einer bestehenden Verbindlichkeit mindert die Bilanzsumme.')
                    else:
                        items = [
                            ('Bankbestand steigt, weil ein Kunde eine offene Rechnung begleicht.', 'Aktivtausch: Bank steigt und Forderungen sinken', 'Bilanzverlängerung','Passivtausch','Ertragsbuchung'),
                            ('Eine Lieferantenverbindlichkeit wird aus der Kasse bezahlt.', 'Aktiv-Passiv-Minderung: Kasse und Verbindlichkeit sinken', 'Aktivtausch','Passivtausch','Aktiv-Passiv-Mehrung'),
                            ('Ein bisher offener Kredit wird in Eigenkapital umgewandelt, ohne Geldfluss.', 'Passivtausch: Fremdkapital sinkt, Eigenkapital steigt', 'Aktivtausch','Aktiv-Passiv-Mehrung','Aktiv-Passiv-Minderung'),
                        ][li]
                        addc(RW,topic,lvl,key,f'Bilanzfall B{li+1}-{n}: {items[0]} Welche Bilanzveränderung liegt vor?',items[1],list(items[2:]),f'Richtig ist {items[1]}.','Unterscheide Aktiva und Passiva.')
                elif key == 'fibu_buchung':
                    item=booking_cases[k % len(booking_cases)]
                    amount=amt(a + D(k//12)*D(45))
                    sol,hab=item[1],item[2]
                    good=f'{sol} {money(amount)} an {hab} {money(amount)}'
                    other1=next(x for x in accounts[(k+4)%len(accounts):]+accounts[:(k+4)%len(accounts)] if x not in (sol,hab))
                    other2=next(x for x in accounts[(k+7)%len(accounts):]+accounts[:(k+7)%len(accounts)] if x not in (sol,hab,other1))
                    wrong=[f'{hab} {money(amount)} an {sol} {money(amount)}',
                           f'{sol} {money(amount)} an {other1} {money(amount)}',
                           f'{other2} {money(amount)} an {hab} {money(amount)}']
                    # Beträge werden netto oder ohne Umsatzsteuereffekt betrachtet, soweit angegeben.
                    addc(RW,topic,lvl,key,f'Geschäftsvorfall F{li+1}-{n}: {item[0]} Betrag {money(amount)}. Welche vereinfachte Buchung (ohne Umsatzsteuerbuchung) ist richtig?',good,wrong,
                         f'Im Soll steht {sol}, im Haben {hab}. Soll- und Habenbetrag: jeweils {money(amount)}.', 'Zuerst Kontenart und Zu- bzw. Abgang bestimmen.')
                elif key == 'fibu_steuer':
                    mode = k % 4
                    if mode == 0:
                        calc(RW,topic,lvl,key,f'Beleg S{li+1}-{n}: Der Betrieb kauft Büromaterial für {money(a)} netto zuzüglich 19 % USt. Wie viel Vorsteuer entsteht?',a*D('0.19'),'€',f'Vorsteuer = {money(a)} × 19 %. Voraussetzung: ordnungsgemäße Rechnung und Vorsteuerabzugsberechtigung.','Vorsteuer entsteht bei abzugsberechtigten Einkäufen.')
                    elif mode == 1:
                        calc(RW,topic,lvl,key,f'Umsatz S{li+1}-{n}: Dienstleistungen werden für {money(a*2)} netto zuzüglich 19 % USt verkauft. Wie hoch ist die Umsatzsteuer-Verbindlichkeit vor Vorsteuerverrechnung?',a*2*D('.19'),'€',f'Ausgangsumsatzsteuer = {money(a*2)} × 19 %.','Nicht mit dem Bruttorechnungsbetrag verwechseln.')
                    elif mode == 2:
                        calc(RW,topic,lvl,key,f'Voranmeldung S{li+1}-{n}: Ausgangsumsatzsteuer {money(a)} und abzugsfähige Vorsteuer {money(b)}. Wie hoch ist die Zahllast?',a-b,'€',f'Zahllast = Umsatzsteuer {money(a)} minus Vorsteuer {money(b)}.','Umsatzsteuer und Vorsteuer saldieren.')
                    else:
                        items = [
                            ('Ein abzugsberechtigter Einkauf auf Ziel mit 19 % USt', 'Aufwand und Vorsteuer im Soll; Verbindlichkeit brutto im Haben', 'Umsatzerlöse und Umsatzsteuer im Soll; Bank im Haben','Nur Vorsteuer im Haben; Bank im Soll','Verbindlichkeit im Soll; Aufwand im Haben'),
                            ('Eine Ausgangsrechnung an den Kunden mit 19 % USt', 'Forderung brutto im Soll; Erlös und Umsatzsteuer im Haben', 'Vorsteuer im Soll und Erlös im Haben','Bank im Haben und Forderung im Haben','Umsatzsteuer im Soll und Verbindlichkeit im Haben'),
                            ('Vorsteuerüberhang nach einer Voranmeldung', 'Übersteigt die abziehbare Vorsteuer die Ausgangsumsatzsteuer, ergibt sich ein Erstattungsanspruch', 'Vorsteuer ist stets identisch mit dem Gewinn','Ein Vorsteuerüberhang ist immer ein Buchungsfehler','Die Zahllast wird unabhängig von Vorsteuer berechnet'),
                        ][li]
                        addc(RW,topic,lvl,key,f'Steuerfall S{li+1}-{n}: {items[0]}. Welche Aussage passt?',items[1],list(items[2:]),items[1]+'.','Trenne Vorsteuer von Ausgangsumsatzsteuer.')
                elif key == 'fibu_guv':
                    mode = k % 4
                    if mode in (0,1):
                        ansch = a*5
                        dauer = D(3 + n % 5)
                        if li == 0:
                            calc(RW,topic,lvl,key,f'Anlagegut A{n} kostet {money(ansch)} netto und wird linear über {int(dauer)} Jahre abgeschrieben. Wie hoch ist die jährliche Abschreibung (ohne Restwert)?',ansch/dauer,'€',f'Jährliche lineare Abschreibung = {money(ansch)} ÷ {int(dauer)} Jahre.','Anschaffungskosten durch Nutzungsdauer teilen.')
                        elif li == 1:
                            rest = a
                            calc(RW,topic,lvl,key,f'Anlagegut A{n}: Anschaffungswert {money(ansch)}, geplanter Restwert {money(rest)}, Nutzungsdauer {int(dauer)} Jahre. Wie hoch ist die jährliche lineare Abschreibung?',(ansch-rest)/dauer,'€',f'Abschreibungsbasis = {money(ansch-rest)}; diese durch {int(dauer)} Jahre teilen.','Anschaffungswert minus Restwert.')
                        else:
                            wert=amt((ansch-b)/dauer)
                            calc(RW,topic,lvl,key,f'Anlagegut A{n}: Anschaffungswert {money(ansch)}, Restwert {money(b)}, Nutzungsdauer {int(dauer)} Jahre. Wie hoch ist der Buchwert am Ende des 2. vollen Nutzungsjahres bei linearer Abschreibung?',ansch-((ansch-b)/dauer)*2,'€',f'Buchwert = {money(ansch)} minus 2 × ({money(ansch-b)} ÷ {int(dauer)}).','Abschreibungen für zwei volle Jahre abziehen.')
                    elif mode == 2:
                        erloese=a*5
                        aufwand=b*3
                        calc(RW,topic,lvl,key,f'GuV G{li+1}-{n}: Erträge {money(erloese)} und Aufwendungen {money(aufwand)}. Wie hoch ist das Jahresergebnis (positiv = Gewinn)?',erloese-aufwand,'€',f'Erträge {money(erloese)} minus Aufwendungen {money(aufwand)}.','Gewinn = Erträge − Aufwendungen.')
                    else:
                        items=[
                            ('Lineare Abschreibung', 'Gleichmäßige Verteilung des abschreibbaren Werts über die Nutzungsdauer', 'Jedes Jahr ein zufälliger Abschreibungsbetrag','Immer vollständige Abschreibung im Anschaffungsjahr','Verteilung nur nach Verkaufszahlen'),
                            ('Abschreibungen in der GuV', 'Planmäßige Abschreibungen sind grundsätzlich Aufwand und mindern das Ergebnis', 'Abschreibungen sind immer zusätzlicher Umsatz','Abschreibungen erhöhen automatisch den Bankbestand','Abschreibungen ersetzen jede Inventur'),
                            ('Aufwands- und Ertragskonten', 'Sie werden über die Gewinn-und-Verlust-Rechnung abgeschlossen', 'Sie werden nur über die Kasse abgeschlossen','Sie werden direkt als Lieferantenkonten geführt','Sie gehören grundsätzlich nicht zur Buchführung'),
                        ][li]
                        addc(RW,topic,lvl,key,f'GuV-Fall G{li+1}-{n}: Welche Aussage zu {items[0]} ist fachlich richtig?',items[1],list(items[2:]),items[1]+'.','Unterscheide Bestandskonten von Erfolgskonten.')

        for key, topic, count in steering_topics:
            for k in range(count):
                n=k+1
                a=D(100+23*n+40*li)
                b=D(12+3*n+4*li)
                mode=k%5
                if key=='steuer_kosten':
                    if mode==0:
                        calc(RW,topic,lvl,key,f'Kostenfall K{li+1}-{n}: Fixkosten {money(a*10)} und variable Kosten {money(b)} je Einheit. Wie hoch sind die Gesamtkosten bei {n+30} Einheiten?',a*10+b*(n+30),'€',f'Gesamtkosten = Fixkosten {money(a*10)} + {n+30} × {money(b)}.','Fixe und variable Kosten addieren.')
                    elif mode==1:
                        q=D(n+24)
                        calc(RW,topic,lvl,key,f'Kostenfall K{li+1}-{n}: Gesamtkosten {money(a*12)}, davon Fixkosten {money(a*4)} bei {int(q)} Stück. Wie hoch sind die variablen Stückkosten?', (a*8)/q,'€',f'(Gesamtkosten {money(a*12)} minus Fixkosten {money(a*4)}) ÷ {int(q)} Stück.','Variable Kosten durch Menge teilen.')
                    elif mode==2:
                        fix=a*6
                        calc(RW,topic,lvl,key,f'Kostenfall K{li+1}-{n}: Fixkosten {money(fix)}. Die Ausbringung steigt von {int(n+20)} auf {int(n+40)} Stück. Um wie viel Euro ändern sich die gesamten Fixkosten, wenn die Kapazitätsgrenze nicht überschritten wird?',D(0),'€','Innerhalb derselben Kapazitätsstufe bleiben gesamte Fixkosten konstant.','Fixkosten sind nicht proportional zur Menge.')
                    elif mode==3:
                        items=[
                            ('Strom für den laufenden Produktionsprozess abhängig von Maschinenlaufzeit','Variable Kosten bei entsprechendem Verbrauch','Immer fixe Kosten','Immer neutrale Erträge','Grundsätzlich keine Kosten'),
                            ('Monatliche Büromiete in fester Höhe','Fixkosten innerhalb der betrachteten Kapazität','Immer variable Kosten','Nur außerordentlicher Ertrag','Kein Bestandteil der Kostenrechnung'),
                            ('Materialeinsatz je hergestelltem Stück','Variable Einzelkosten bei direkter Zurechenbarkeit','Stets fixe Gemeinkosten','Ausschließlich Finanzierungskosten','Immer periodenfremde Kosten'),
                        ][li]
                        addc(RW,topic,lvl,key,f'Kostenklassifizierung K{li+1}-{n}: {items[0]}. Welche Einordnung passt?',items[1],list(items[2:]),items[1]+'.','Prüfe Mengenabhängigkeit und Zuordenbarkeit.')
                    else:
                        if li==0:
                            calc(RW,topic,lvl,key,f'Kalkulation K{n}: Materialeinzelkosten {money(a)}, Fertigungseinzelkosten {money(b)}. Wie hoch ist die Summe der Einzelkosten?',a+b,'€',f'{money(a)} + {money(b)}.','Einzelkosten können direkt zugerechnet werden.')
                        else:
                            calc(RW,topic,lvl,key,f'Kalkulation K{li+1}-{n}: Materialeinzelkosten {money(a)} und Materialgemeinkostenzuschlag {3+n%12} %. Wie hoch sind die Materialkosten?',a*(1+D(3+n%12)/100),'€',f'{money(a)} × (1 + {3+n%12}/100).','Gemeinkosten als Zuschlag auf Materialeinzelkosten.')
                elif key=='steuer_bab':
                    if mode==0:
                        calc(RW,topic,lvl,key,f'BAB KSt{li+1}-{n}: Materialgemeinkosten {money(a*3)} und Materialeinzelkosten {money(a*10)}. Wie hoch ist der Materialgemeinkostenzuschlag in Prozent?',D(30),'%',f'{money(a*3)} ÷ {money(a*10)} × 100 = 30 %.','Zuschlag = Gemeinkosten / Bezugsgröße × 100.')
                    elif mode==1:
                        calc(RW,topic,lvl,key,f'BAB KSt{li+1}-{n}: Fertigungsgemeinkosten {money(a*2)} bei Fertigungslöhnen von {money(a*8)}. Wie hoch ist der Zuschlagssatz?',D(25),'%',f'{money(a*2)} ÷ {money(a*8)} × 100 = 25 %.','Bezugsgröße der Fertigung = hier die Fertigungslöhne.')
                    elif mode==2:
                        calc(RW,topic,lvl,key,f'Kostenstellen KSt{li+1}-{n}: Gemeinkosten {money(a*9)} werden im Verhältnis 2:1:1 auf Material, Fertigung und Verwaltung verteilt. Welcher Betrag entfällt auf Material?',a*9/D(2),'€',f'2 von 4 Anteilen: {money(a*9)} × 2/4.','Verteilungsschlüssel auswerten.')
                    elif mode==3:
                        items=[
                            ('Betriebsabrechnungsbogen (BAB)','Er verteilt Gemeinkosten auf betriebliche Kostenstellen','Er ersetzt Kontoauszüge','Er ermittelt die private Einkommensteuer','Er ist ein Lieferschein'),
                            ('Kostenstelle','Sie bezeichnet den betrieblichen Ort der Kostenentstehung','Sie ist immer ein einzelner Artikel','Sie bezeichnet ausschließlich einen Kunden','Sie entspricht dem Steuersatz'),
                            ('Kostenträger','Er bezeichnet die Leistung oder das Produkt, für das Kosten entstehen','Er ist die zuständige Bank','Er bezeichnet ausschließlich ein Lagerregal','Er ist immer die Personalabteilung'),
                        ][li]
                        addc(RW,topic,lvl,key,f'BAB-Begriff KSt{li+1}-{n}: Was beschreibt {items[0]}?',items[1],list(items[2:]),items[1]+'.','Kostenart, Kostenstelle und Kostenträger unterscheiden.')
                    else:
                        calc(RW,topic,lvl,key,f'BAB KSt{li+1}-{n}: Vertriebsgemeinkosten {money(a*2)} und Herstellkosten des Umsatzes {money(a*10)}. Wie hoch ist der Vertriebsgemeinkostenzuschlag?',D(20),'%',f'{money(a*2)} ÷ {money(a*10)} × 100 = 20 %.','Zuschlagssatz mit passender Bezugsgröße bilden.')
                elif key=='steuer_db':
                    p=a+b*3
                    v=a
                    per=p-v
                    qty=n+25
                    if mode==0:
                        calc(RW,topic,lvl,key,f'Deckungsbeitrag DB{li+1}-{n}: Nettoerlös {money(p)} je Stück, variable Kosten {money(v)} je Stück. Wie hoch ist der Stückdeckungsbeitrag?',per,'€',f'{money(p)} − {money(v)} = {money(per)}.','Verkaufspreis minus variable Stückkosten.')
                    elif mode==1:
                        calc(RW,topic,lvl,key,f'Deckungsbeitrag DB{li+1}-{n}: {qty} Stück werden zu {money(p)} netto verkauft; variable Stückkosten {money(v)}. Wie hoch ist der gesamte Deckungsbeitrag?',per*qty,'€',f'{qty} × ({money(p)} − {money(v)}) = {money(per*qty)}.','Stückdeckungsbeitrag mal Absatzmenge.')
                    elif mode==2:
                        fix=per*D(20+n)
                        calc(RW,topic,lvl,key,f'Gewinnschwelle DB{li+1}-{n}: Fixkosten {money(fix)} und Stückdeckungsbeitrag {money(per)}. Bei wie vielen Stück liegt die Break-even-Menge?',D(20+n),'Stück',f'{money(fix)} ÷ {money(per)} = {20+n} Stück.','Fixkosten durch Stückdeckungsbeitrag.')
                    elif mode==3:
                        fix=per*D(n+12)
                        calc(RW,topic,lvl,key,f'Ergebnis DB{li+1}-{n}: {qty} Stück zu Stückdeckungsbeitrag {money(per)}, Fixkosten {money(fix)}. Wie hoch ist das Betriebsergebnis?',per*qty-fix,'€',f'{qty} × {money(per)} − {money(fix)}.','Gesamtdeckungsbeitrag minus Fixkosten.')
                    else:
                        items=[
                            ('Zusatzauftrag bei freien Kapazitäten', 'Ein positiver zusätzlicher Deckungsbeitrag kann zur Fixkostendeckung beitragen', 'Jeder Zusatzauftrag muss unabhängig vom Deckungsbeitrag abgelehnt werden','Nur der Listenpreis entscheidet ohne Kosten','Fixkosten steigen zwingend proportional je Stück'),
                            ('Negativer Stückdeckungsbeitrag', 'Der Verkaufserlös deckt nicht einmal die variablen Stückkosten', 'Der gesamte Jahresgewinn ist sicher positiv','Die Fixkosten sind bereits vollständig bezahlt','Die Menge ist automatisch zu gering'),
                            ('Break-even-Punkt', 'Der Gesamterlös deckt bei der betrachteten Menge genau die Gesamtkosten', 'Dort ist der Absatz immer null','Dort sind sämtliche Kosten variabel','Dort fällt keine Buchführung an'),
                        ][li]
                        addc(RW,topic,lvl,key,f'Entscheidungsfall DB{li+1}-{n}: {items[0]}. Welche Aussage trifft zu?',items[1],list(items[2:]),items[1]+'.','Deckungsbeitrag und Fixkostendeckung beachten.')
                elif key=='steuer_budget':
                    ist=a*7
                    plan=a*8
                    if mode==0:
                        calc(RW,topic,lvl,key,f'Budget C{li+1}-{n}: Kostenbudget {money(plan)}, Istkosten {money(ist)}. Wie hoch ist die Unterschreitung des Kostenbudgets?',plan-ist,'€',f'{money(plan)} − {money(ist)}.','Plan minus Ist bei Kosten.')
                    elif mode==1:
                        calc(RW,topic,lvl,key,f'Budget C{li+1}-{n}: Geplante Ausgaben {money(plan)}, tatsächliche Ausgaben {money(ist)}. Um wie viel Prozent liegen die Ist-Ausgaben unter dem Plan?',D('12.5'),'%',f'({money(plan)} − {money(ist)}) / {money(plan)} × 100 = 12,5 %.','Für Prozentabweichung Plan als Bezugswert nehmen.')
                    elif mode==2:
                        umsatz=a*9
                        gewinn=a
                        calc(RW,topic,lvl,key,f'Kennzahl C{li+1}-{n}: Umsatz {money(umsatz)} und Gewinn {money(gewinn)}. Wie hoch ist die Umsatzrentabilität?',D(100)/D(9),'%',f'{money(gewinn)} ÷ {money(umsatz)} × 100 ≈ 11,11 %.','Gewinn ins Verhältnis zum Umsatz setzen.')
                    elif mode==3:
                        items=[
                            ('Soll-Ist-Vergleich', 'Er macht Abweichungen zwischen Planung und tatsächlichem Ergebnis sichtbar', 'Er ersetzt alle Zahlungsbelege','Er legt automatisch das Kontierungskonto fest','Er zeigt nur den Lagerort'),
                            ('Liquiditätsplanung', 'Sie betrachtet erwartete Ein- und Auszahlungen und die Zahlungsfähigkeit', 'Sie ermittelt ausschließlich die Nutzungsdauer','Sie zählt nur Inventargegenstände','Sie ersetzt das Mahnwesen'),
                            ('Wirtschaftlichkeit', 'Sie setzt den bewerteten Ertrag ins Verhältnis zum Aufwand', 'Sie ist immer identisch mit dem Kassenbestand','Sie setzt nur Liefertermine ins Verhältnis','Sie zählt nur Buchungssätze'),
                        ][li]
                        addc(RW,topic,lvl,key,f'Controlling C{li+1}-{n}: {items[0]}. Welche Aussage stimmt?',items[1],list(items[2:]),items[1]+'.','Kennzahl und Steuerungszweck zusammenbringen.')
                    else:
                        calc(RW,topic,lvl,key,f'Liquiditätsplan C{li+1}-{n}: Anfangsbestand {money(a*2)}, Einzahlungen {money(a*5)}, Auszahlungen {money(a*4)}. Wie hoch ist der Endbestand?',a*3,'€',f'{money(a*2)} + {money(a*5)} − {money(a*4)} = {money(a*3)}.','Anfang + Einzahlungen − Auszahlungen.')

        for key, topic, count in buying_topics:
            for k in range(count):
                n=k+1
                a=D(30+7*n+10*li)
                b=D(12+2*n+3*li)
                mode=k%4
                if key=='einkauf_bedarf':
                    if mode==0:
                        calc(GP,topic,lvl,key,f'Bedarfsrechnung E{li+1}-{n}: Bruttobedarf {100+n*12} Stück, vorhandener Bestand {n+18}, offene Bestellungen {n+9}, Sicherheitsbestand {12+li*6}. Wie hoch ist der Nettobedarf?',D(100+n*12-(n+18)-(n+9)+(12+li*6)),'Stück',f'Bruttobedarf {100+n*12} + Sicherheitsbestand {12+li*6} − Lagerbestand {n+18} − bereits bestellte Menge {n+9}.','Verfügbare und bereits bestellte Menge abziehen.')
                    elif mode==1:
                        required=D(67+n*11+li*8)
                        pack=D(6+li*2)
                        packages=(required+pack-1)//pack
                        ordered=packages*pack
                        calc(GP,topic,lvl,key,f'Verpackungseinheiten E{li+1}-{n}: Nettobedarf {int(required)} Stück. Der Lieferant liefert nur volle Verpackungseinheiten zu {int(pack)} Stück. Welche kleinste bestellbare Stückzahl deckt den Bedarf?', ordered, 'Stück',
                             f'{int(required)} / {int(pack)} = {str(required/pack).replace(".",",")} Verpackungseinheiten, auf {int(packages)} volle Einheiten aufrunden: {int(ordered)} Stück.',
                             'Auf eine volle Verpackungseinheit aufrunden.')
                    elif mode==2:
                        items=[
                            ('Bestellpunktverfahren', 'Nachbestellung bei Erreichen eines festgelegten Meldebestands','Automatische Bestellung nur am Jahresende','Nachbestellung unabhängig vom Bestand','Beschaffung nur auf Zuruf ohne Bestandsdaten'),
                            ('Bestellrhythmusverfahren', 'Prüfung und Bestellung zu festgelegten Zeitpunkten','Bestellung bei jedem Kassenvorgang','Bestellung ohne Plantermin','Bestellung nur bei leeren Regalen'),
                            ('Sicherheitsbestand', 'Puffer gegen unerwarteten Verbrauch oder Lieferverzug','Immer die gesamte Jahresbedarfsmenge','Gleiche Größe wie alle offenen Rechnungen','Nur beschädigte Ware'),
                        ][li]
                        addc(GP,topic,lvl,key,f'Bedarf E{li+1}-{n}: Was kennzeichnet das {items[0]}?',items[1],list(items[2:]),items[1]+'.','Auslöser und Zweck der Bestellung bestimmen.')
                    else:
                        calc(GP,topic,lvl,key,f'Bestellmengenplanung E{li+1}-{n}: Jahresbedarf {3600+120*n} Stück bei {12-li*2} gleichmäßigen Lieferungen. Wie viele Stück entfallen rechnerisch auf jede Lieferung?',D(3600+120*n)/D(12-li*2),'Stück',f'Jahresbedarf ÷ {12-li*2} Lieferungen.','Gleichmäßige Teilmengen berechnen.')
                elif key=='einkauf_nutzwert':
                    # In der Nutzwertanalyse gelten vorgegebene, vollständige Kriterien.
                    price=D(45+n%12)
                    punctual=D(75-n%10)
                    quality=D(70+n%14)
                    weights=[(50,30,20),(35,35,30),(25,45,30)][li]
                    if mode==0:
                        w=weights
                        result=(price*D(w[0])+punctual*D(w[1])+quality*D(w[2]))/D(100)
                        calc(GP,topic,lvl,key,f'Nutzwert N{li+1}-{n}: Anbieter A erhält {int(price)} Punkte für Preis, {int(punctual)} für Termintreue und {int(quality)} für Qualität (je 0–100). Gewichtung {w[0]}/{w[1]}/{w[2]} %. Wie viele gewichtete Gesamtpunkte erreicht A?',result,'Punkte',f'{int(price)} × {w[0]} % + {int(punctual)} × {w[1]} % + {int(quality)} × {w[2]} % = {str(amt(result)).replace(".",",")} Punkte.','Gewichtete Summe bilden.')
                    elif mode==1:
                        w=weights
                        pa=(price*D(w[0])+punctual*D(w[1])+quality*D(w[2]))/D(100)
                        pb=pa+D(3+li)
                        addc(GP,topic,lvl,key,f'Nutzwert N{li+1}-{n}: Anbieter A erreicht {str(amt(pa)).replace(".",",")} Punkte und B {str(amt(pb)).replace(".",",")} Punkte. Beide sind geeignet, Kapazität ist vorhanden. Welcher ist nach reinem Nutzwert vorzuziehen?',f'Anbieter B mit {str(amt(pb)).replace(".",",")} Punkten',
                             [f'Anbieter A mit {str(amt(pa)).replace(".",",")} Punkten','Beide sind automatisch gleichwertig','Ein Lieferant darf nie anhand mehrerer Kriterien bewertet werden'],f'B hat den höheren Nutzwert ({str(amt(pb)).replace(".",",")} > {str(amt(pa)).replace(".",",")}).','Höhere gewichtete Punktzahl gewinnt.')
                    elif mode==2:
                        w=weights
                        calc(GP,topic,lvl,key,f'Nutzwert N{li+1}-{n}: Ein Kriterium wurde mit {int(price)} von 100 Punkten bewertet und erhält {w[0]} % Gewicht. Wie groß ist sein Beitrag zur Nutzwertsumme in Punkten?',price*D(w[0])/100,'Punkte',f'{int(price)} × {w[0]} / 100.','Kriterienpunkte mit Gewicht multiplizieren.')
                    else:
                        items=[
                            ('Nutzwertanalyse', 'Preis und qualitative Kriterien nach vorab festgelegter Gewichtung vergleichen','Ohne Kriterien zufällig einen Lieferanten wählen','Nur die Rechnungsnummer auswerten','Immer nur den Bruttolistenpreis betrachten'),
                            ('Lieferantenbewertung', 'Liefertermintreue nachvollziehbar durch zugesagte und tatsächliche Termine bewerten','Nur auf Selbstauskünfte ohne Belege vertrauen','Liefertermine grundsätzlich nicht dokumentieren','Alle Anbieter unabhängig von Leistung gleich bewerten'),
                            ('Gewichtung von Kriterien', 'Gewichtungen vor der Bewertung transparent festlegen und zusammen auf 100 % bringen','Jedes Kriterium nach dem Ergebnis frei verändern','Qualität darf nie eine Rolle spielen','Die Gewichte müssen stets gleich groß sein'),
                        ][li]
                        addc(GP,topic,lvl,key,f'Bewertungsverfahren N{li+1}-{n}: Welche Aussage zu {items[0]} ist richtig?',items[1],list(items[2:]),items[1]+'.','Objektive, dokumentierte Kriterien verwenden.')
                elif key=='einkauf_strategie':
                    items=[
                        [
                            ('Single Sourcing','Bewusster Bezug eines Artikels von nur einer Bezugsquelle','Verteilung auf alle verfügbaren Lieferanten','Bestellung ohne Bedarf','Beschaffung nur in Barzahlung'),
                            ('Multiple Sourcing','Beschaffung eines Artikels über mehrere Lieferanten','Ausschließlich ein Monopollieferant','Nur eine interne Kostenstelle','Bezug nur am Monatsende'),
                            ('Rahmenvertrag','Vereinbarung grundlegender Konditionen für spätere Einzelabrufe','Eine sofortige Abrechnung sämtlicher künftiger Waren','Eine reine Inventurliste','Nur ein Versandetikett'),
                            ('Just-in-Time-Beschaffung','Bedarfssynchrone Lieferung mit geringerem Lagerbestand und erhöhtem Abstimmungsbedarf','Beliebige Bevorratung unabhängig vom Bedarf','Beschaffung ohne Liefertermin','Eine Bilanzierungsart'),
                        ],[
                            ('Risiko bei Single Sourcing','Abhängigkeit vom Ausfall eines einzelnen Lieferanten','Garantiert keine Transportkosten','Unbegrenzte Alternativlieferanten','Automatisch keine Preisänderungen'),
                            ('Strategie bei schwankenden Lieferzeiten','Mehrere geeignete Bezugsquellen können Versorgungsrisiken reduzieren','Nur noch am Jahresende beschaffen','Jede Wareneingangskontrolle aufgeben','Bedarf aus den Daten entfernen'),
                            ('Konsignationslager','Lieferantenbestand wird beim Abnehmer bereitgehalten; Eigentumsübergang nach Vereinbarung','Bestand wird immer sofort Eigentum des Fahrers','Ein allgemeines Ersatzteillager ohne Vereinbarung','Nur ein digitales Mahnverfahren'),
                            ('Make-or-Buy-Entscheidung','Eigenfertigung und Fremdbezug unter Kosten-, Kapazitäts- und Risikokriterien vergleichen','Immer das billigste Einzelteil wählen','Nur das Design des Angebots bewerten','Alle Lieferanten ungeprüft abweisen'),
                        ],[
                            ('Zweiquellenstrategie für kritische Bauteile','Versorgung absichern, zugleich Qualifizierung und Aufteilungskosten berücksichtigen','Beide Lieferanten ohne Prüfung willkürlich mischen','Immer 100 % ohne Vertrag von beiden abrufen','Versorgungsrisiken grundsätzlich ignorieren'),
                            ('Total Cost of Ownership','Neben Kaufpreis auch Folgekosten während Beschaffung und Nutzung berücksichtigen','Nur den Rabatt auf der ersten Rechnung betrachten','Nur die Verpackungsfarbe bewerten','Alle Transport- und Ausfallkosten ausblenden'),
                            ('Rahmenvertrag mit Mengenstaffel','Abnahmekonditionen, Abrufregeln und Mengenbindungen vertraglich prüfen','Sämtliche Mengen sofort ohne Bedarf abrufen','Lieferfristen nicht verhandeln','Bestellungen ohne Freigabe erzeugen'),
                            ('Internationaler Beschaffungsmarkt','Liefer-, Wechselkurs-, Zoll- und Compliance-Risiken mitbewerten','Währungsrisiko stets auf null setzen','Liefervorgaben ignorieren','Nur Inlandstransporte betrachten'),
                        ]
                    ][li]
                    item=items[k % 4]
                    addc(GP,topic,lvl,key,f'Beschaffungsstrategie S{li+1}-{n}: Was bedeutet bzw. erfordert „{item[0]}“?',item[1],list(item[2:]),item[1]+'.','Strategie, Vorteile und Risiken abwägen.')
                elif key=='einkauf_controlling':
                    if mode==0:
                        planned=D(40+n*5)
                        true=D(34+n*5)
                        calc(GP,topic,lvl,key,f'Liefertermintreue EK{li+1}-{n}: {int(planned)} Lieferungen, davon {int(true)} termingerecht. Wie hoch ist die Termintreue in Prozent?',true/planned*100,'%',f'{int(true)} ÷ {int(planned)} × 100.','Pünktliche durch gesamte Lieferungen teilen.')
                    elif mode==1:
                        total=D(100+n*7)
                        defects=D(n+3)
                        calc(GP,topic,lvl,key,f'Qualitätskennzahl EK{li+1}-{n}: {int(total)} geprüfte Lieferpositionen, davon {int(defects)} mangelhaft. Wie hoch ist die Mängelquote in Prozent?',defects/total*100,'%',f'{int(defects)} ÷ {int(total)} × 100.','Mangelhafte Positionen durch Gesamtzahl teilen.')
                    elif mode==2:
                        old=D(1200+n*45)
                        new=old-D(45+n)
                        calc(GP,topic,lvl,key,f'Einkaufserfolg EK{li+1}-{n}: Alter Bezugspreis für die Vergleichsmenge {money(old)}, neuer {money(new)}. Wie hoch ist die absolute Einsparung?',old-new,'€',f'{money(old)} − {money(new)}.','Vergleiche identische Mengen und Konditionen.')
                    else:
                        items=[
                            ('Termintreue','Anteil der zum zugesagten Termin eingetroffenen Lieferungen','Anteil der Auszubildenden','Höhe der Umsatzsteuerzahllast','Nur die Anzahl von E-Mails'),
                            ('Reklamationsquote','Anteil beanstandeter Lieferungen an den betrachteten Lieferungen','Nur den Wareneingangswert','Nur die Büromiete','Immer die Höhe des Gewinns'),
                            ('Beschaffungscontrolling','Kennzahlen, Ursachen und Zielabweichungen zur Einkaufssteuerung verwenden','Nur die Rechnungsanschrift formatieren','Zieltermine bewusst ignorieren','Lieferanten ausschließlich nach Firmenlogo ordnen'),
                        ][li]
                        addc(GP,topic,lvl,key,f'Einkaufscontrolling EK{li+1}-{n}: Welche Aussage zu {items[0]} ist passend?',items[1],list(items[2:]),items[1]+'.','Kennzahl und Datenbasis unterscheiden.')

        for key, topic, count in logistics_topics:
            for k in range(count):
                n=k+1
                a=D(25+11*n+6*li)
                b=D(8+2*n+3*li)
                mode=k%5
                if key=='logistik_lager':
                    if mode==0:
                        calc(GP,topic,lvl,key,f'Lager L{li+1}-{n}: Anfangsbestand {int(a*3)} Stück, Endbestand {int(a)} Stück. Wie hoch ist der einfache durchschnittliche Lagerbestand?',a*2,'Stück',f'({int(a*3)} + {int(a)}) ÷ 2 = {int(a*2)} Stück.','Mittelwert von Anfang und Ende.')
                    elif mode==1:
                        qty=D(50+n*10)
                        avg=D(10+n)
                        calc(GP,topic,lvl,key,f'Lager L{li+1}-{n}: Jahresverbrauch {int(qty*4)} Stück, durchschnittlicher Bestand {int(avg)} Stück. Wie oft schlägt der Lagerbestand pro Jahr um?',qty*4/avg,'Umschläge',f'{int(qty*4)} ÷ {int(avg)}.','Lagerumschlag = Jahresverbrauch / durchschnittlicher Bestand.')
                    elif mode==2:
                        days=D(360)
                        turnover=D(4+n%10)
                        calc(GP,topic,lvl,key,f'Lager L{li+1}-{n}: Es wird mit 360 Tagen gerechnet. Lagerumschlag {int(turnover)}. Wie hoch ist die durchschnittliche Lagerdauer in Tagen?',days/turnover,'Tage',f'360 ÷ {int(turnover)}.','Lagerdauer aus 360 Tagen ableiten.')
                    elif mode==3:
                        items=[
                            ('FIFO (First In, First Out)','Zuerst eingelagerte Ware wird bei der Entnahme zuerst verwendet','Die neueste Ware wird zuerst entnommen','Ware wird ohne Nachweis vernichtet','Entnahme ausschließlich nach Kartonfarbe'),
                            ('FEFO (First Expired, First Out)','Ware mit dem frühesten Verfallsdatum wird zuerst entnommen','Immer die schwerste Ware zuerst','Nur Ware vom letzten Liefertag','Ware mit der höchsten Artikelnummer'),
                            ('Chaotische Lagerhaltung','Freie Lagerplätze mit systematischer digitaler Platzzuordnung nutzen','Ware ungeordnet ohne Erfassung abstellen','Jeden Platz dauerhaft einem Kunden zuordnen','Alle Wareneingänge ohne Buchung einlagern'),
                        ][li]
                        addc(GP,topic,lvl,key,f'Lagerorganisation L{li+1}-{n}: Welche Aussage zu {items[0]} stimmt?',items[1],list(items[2:]),items[1]+'.','Entnahmeprinzip bzw. Platzverwaltung erkennen.')
                    else:
                        avg=a*D(7)
                        zins=D(6+li*2)
                        calc(GP,topic,lvl,key,f'Lager L{li+1}-{n}: Durchschnittlicher Lagerwert {money(avg)}, Kalkulationszins {int(zins)} % pro Jahr. Wie hoch sind die jährlichen kalkulatorischen Lagerzinsen?',avg*zins/100,'€',f'{money(avg)} × {int(zins)} / 100.','Durchschnittlichen Wert mit Zinssatz multiplizieren.')
                elif key=='logistik_abc':
                    if mode==0:
                        qty=D(12+n)
                        unit=D(20+2*n)
                        calc(GP,topic,lvl,key,f'ABC-Analyse LA{li+1}-{n}: Artikel X: Jahresverbrauch {int(qty)} Stück und Preis {money(unit)} je Stück. Wie hoch ist sein jährlicher Verbrauchswert?',qty*unit,'€',f'{int(qty)} × {money(unit)}.','Menge mal Einstandspreis.')
                    elif mode==1:
                        v=a*12
                        sumv=v*D(5)
                        calc(GP,topic,lvl,key,f'ABC LA{li+1}-{n}: Artikel X hat Jahresverbrauchswert {money(v)}, das Sortiment insgesamt {money(sumv)}. Wie hoch ist sein Wertanteil?',D(20),'%',f'{money(v)} ÷ {money(sumv)} × 100 = 20 %.','Wertanteil der Artikelklasse bestimmen.')
                    elif mode==2:
                        items=[
                            ('A-Artikel','Hoher Anteil am gesamten Verbrauchswert bei häufig geringerer Artikelzahl','Immer die Artikel mit niedrigstem Verbrauchswert','Immer die ältesten Lagerplätze','Artikel nur mit A im Namen'),
                            ('X-Artikel','Relativ regelmäßiger, gut prognostizierbarer Verbrauch','Stark sporadischer und unvorhersehbarer Verbrauch','Immer der teuerste Artikel','Artikel mit unbekanntem Besitzer'),
                            ('Z-Artikel','Unregelmäßiger, schwer prognostizierbarer Verbrauch','Garantiert jeden Tag gleiche Menge','Artikel mit stets kürzester Lieferzeit','Artikel mit immer null Lagerkosten'),
                        ][li]
                        addc(GP,topic,lvl,key,f'Bestandsanalyse LA{li+1}-{n}: Was kennzeichnet {items[0]}?',items[1],list(items[2:]),items[1]+'.','ABC beschreibt Wert, XYZ beschreibt Planbarkeit des Verbrauchs.')
                    elif mode==3:
                        # Klassengrenzen sind explizit fallbezogen statt als Allgemeinregel gesetzt.
                        shares = [D(45+n), D(83+n%9), D(96+n%4)]
                        share = shares[li]
                        classification = ['A-Artikel', 'B-Artikel', 'C-Artikel'][li]
                        wrong = [x for x in ['A-Artikel','B-Artikel','C-Artikel','XYZ-Z-Artikel'] if x!=classification][:3]
                        addc(GP,topic,lvl,key,f'ABC LA{li+1}-{n}: Eine betriebliche Einteilung legt A bis 80 %, B bis 95 %, C darüber fest (kumulierte Wertanteile). Nach Sortierung liegt Artikel X bei kumuliert {int(share)} %. Welche Klasse hat er?', classification, wrong,
                             f'{int(share)} % liegt in der vorgegebenen Klasse {classification[0]} (A bis 80 %, B über 80 % bis 95 %, C über 95 %).','Vorgegebene Klassengrenzen nutzen.')
                    else:
                        data=[
                            ('konstant 40 Stück pro Woche, geringe Abweichungen', 'X: gut planbarer Verbrauch', ['Y: stark trend- oder saisonabhängig','Z: stark unregelmäßig','A: immer der teuerste Artikel']),
                            ('deutliche, regelmäßig wiederkehrende saisonale Spitzen', 'Y: schwankender, aber teilweise prognostizierbarer Verbrauch', ['X: stets gleichmäßig','Z: ohne erkennbare Struktur','C: sicherer Mindestpreis']),
                            ('seltene unregelmäßige Bedarfe ohne erkennbares Muster', 'Z: schwer prognostizierbarer Verbrauch', ['X: stets gleichmäßiger Verbrauch','Y: feste monatliche Planmenge','A: garantierter Spitzenartikel']),
                        ][li]
                        addc(GP,topic,lvl,key,f'XYZ LA{li+1}-{n}: Ein Artikel zeigt {data[0]}. Welche Einordnung passt am besten?',data[1],data[2],data[1]+'.','Regelmäßigkeit und Prognosegüte betrachten.')
                elif key=='logistik_kommission':
                    if mode==0:
                        orders=D(6+n)
                        picks=D(4+li+n%5)
                        calc(GP,topic,lvl,key,f'Kommissionierung LK{li+1}-{n}: {int(orders)} Kundenaufträge mit je {int(picks)} Positionen. Wie viele Positionen sind insgesamt zu kommissionieren?',orders*picks,'Positionen',f'{int(orders)} × {int(picks)}.','Aufträge mal Positionen.')
                    elif mode==1:
                        lines=D(70+n*6)
                        wrong=D(3+n%4)
                        calc(GP,topic,lvl,key,f'Kommissionierung LK{li+1}-{n}: {int(lines)} Positionen geprüft, {int(wrong)} fehlerhaft. Wie hoch ist die Fehlerquote?',wrong/lines*100,'%',f'{int(wrong)} / {int(lines)} × 100.','Fehlerhafte Positionen / geprüfte Positionen.')
                    elif mode==2:
                        items=[
                            ('Pick-by-Scan','Barcodegestützte Entnahme mit elektronischer Bestätigung','Ausschließlich mündliche Zurufe','Ungeprüfter Versand aller Positionen','Ein Verfahren zur GuV-Erstellung'),
                            ('Seriennummernverfolgung','Zuordnung ausgelieferter Einzelgeräte zu konkreten Seriennummern','Löschen sämtlicher Artikelnummern','Nur die Farbe des Kartons erfassen','Alle Geräte als identisch ohne Nachweis behandeln'),
                            ('Chargenrückverfolgung','Zuordnung der Ware zu einer Herstellungs- oder Liefercharge','Bestellung ohne Mengendaten','Verzicht auf Warenkennzeichnung','Nur die Kundennummer auf dem Lieferschein'),
                        ][li]
                        addc(GP,topic,lvl,key,f'Kommissionierung LK{li+1}-{n}: Welcher Zweck gehört zu {items[0]}?',items[1],list(items[2:]),items[1]+'.','Rückverfolgbarkeit und Kommissionierprüfung unterscheiden.')
                    elif mode==3:
                        carts=D(9+n)
                        items=D(4+li)
                        calc(GP,topic,lvl,key,f'Versand LK{li+1}-{n}: {int(carts)} Pakete, je {int(items)} Etiketten (Artikel-, Chargen- und Transportkennzeichnung nach Vorgabe). Wie viele Etiketten werden benötigt?',carts*items,'Etiketten',f'{int(carts)} × {int(items)}.','Paketzahl mit Etiketten je Paket multiplizieren.')
                    else:
                        item=[
                            ('Wegeoptimierung beim Kommissionieren','Laufwege und Entnahmezeiten anhand sinnvoller Lagerplatzfolge verringern','Jeden Artikel mehrfach auslagern','Schwerste Waren grundsätzlich ungesichert transportieren','Reihenfolge ohne Sicherheitsregeln ändern'),
                            ('Vier-Augen-Prinzip bei kritischen Sendungen','Eine zweite Person prüft festgelegte risikoreiche Versandmerkmale','Zweiten Auftrag ohne Prüfung verschicken','Die Rechnung durch den Lieferschein ersetzen','Kundeninformationen öffentlich aushängen'),
                            ('Verpackung und Ladeeinheiten','Verpackung passend zu Schutz, Gewicht und Transportbeanspruchung wählen','Verpackung immer nur nach Farbe wählen','Alle Artikel ungepolstert versenden','Zulässige Gewichte ignorieren'),
                        ][li]
                        addc(GP,topic,lvl,key,f'Versandprüfung LK{li+1}-{n}: Welche Maßnahme passt zu {item[0]}?',item[1],list(item[2:]),item[1]+'.','Qualität und Sicherheit des Versands beachten.')
                elif key=='logistik_transport':
                    if mode==0:
                        fixed=a*3
                        km=D(90+n*10)
                        rate=D('0.65')+D('0.05')*li
                        calc(GP,topic,lvl,key,f'Transport LT{li+1}-{n}: Grundgebühr {money(fixed)}, Strecke {int(km)} km zu {str(rate).replace(".",",")} € je km. Wie hoch sind die Gesamtkosten?',fixed+km*rate,'€',f'{money(fixed)} + {int(km)} × {money(rate)}.','Grundgebühr plus streckenabhängige Kosten.')
                    elif mode==1:
                        gross=D(120+n*15)
                        load=D(60+n*9)
                        calc(GP,topic,lvl,key,f'Auslastung LT{li+1}-{n}: Ein Fahrzeug darf maximal {int(gross)} kg Nutzlast befördern, geladen sind {int(load)} kg. Wie hoch ist die Auslastung in Prozent?',load/gross*100,'%',f'{int(load)} / {int(gross)} × 100.','Geladene Nutzlast im Verhältnis zur zulässigen Nutzlast.')
                    elif mode==2:
                        total=D(225+n*32)
                        units=D(9+n)
                        calc(GP,topic,lvl,key,f'Frachtkosten LT{li+1}-{n}: Gesamte Frachtkosten {money(total)} für {int(units)} Pakete. Wie hoch sind die durchschnittlichen Kosten pro Paket?',total/units,'€',f'{money(total)} / {int(units)}.','Gesamtkosten durch Anzahl Pakete.')
                    elif mode==3:
                        item=[
                            ('Tourenplanung','Liefertermine, Fahrstrecken, Kapazitäten und Ladezeiten gemeinsam berücksichtigen','Lieferorte zufällig anfahren','Fahrzeugkapazitäten außer Acht lassen','Terminzusagen ignorieren'),
                            ('Sendungsverfolgung','Transportstatus und Übergaben anhand von Ereignisdaten nachvollziehen','Frachtbriefe ohne Prüfung vernichten','Nur den Büromietvertrag betrachten','Pakete ohne Identifikation versenden'),
                            ('Transportvergleich','Nicht nur Preis, sondern auch Laufzeit, Zuverlässigkeit und Schadensrisiko abwägen','Immer automatisch die längste Route nehmen','Versandkosten nie berücksichtigen','Risiken bei empfindlicher Ware grundsätzlich ausblenden'),
                        ][li]
                        addc(GP,topic,lvl,key,f'Transportentscheidung LT{li+1}-{n}: Was gehört fachlich zu {item[0]}?',item[1],list(item[2:]),item[1]+'.','Kosten, Termine und Risiken gemeinsam betrachten.')
                    else:
                        trips=D(4+n)
                        km=D(35+n*5)
                        rate=D('0.75')
                        calc(GP,topic,lvl,key,f'Tourenbudget LT{li+1}-{n}: {int(trips)} Touren mit je {int(km)} km, variable Kosten {money(rate)} pro km. Wie hoch sind die gesamten variablen Kosten?',trips*km*rate,'€',f'{int(trips)} × {int(km)} × {money(rate)}.','Tourenanzahl mal Strecke mal km-Kosten.')
    expected = {key: size for key, _, size in finance_topics+steering_topics+buying_topics+logistics_topics}
    for key,size in expected.items():
        for lvl in LEVELS:
            actual=counters.get((key,lvl),0)
            if actual!=size: raise AssertionError((key,lvl,actual,size))
    if len(out)!=600: raise AssertionError(len(out))
    return out
