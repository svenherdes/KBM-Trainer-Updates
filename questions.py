from __future__ import annotations

import random
import re
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Optional

LEVELS = ["Anfänger", "Fortgeschritten", "Experte"]
CATEGORIES = [
    "Rechnungswesen",
    "Geschäftsprozesse",
    "Deutsch & Rechtschreibung",
    "Schriftverkehr",
    "Büroorganisation",
    "Datenschutz & IT-Sicherheit",
]


def money(value: Decimal) -> str:
    value = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{value:.2f}".replace(".", ",") + " €"


def parse_number(text: str) -> Optional[Decimal]:
    cleaned = text.strip().lower().replace("€", "").replace(" ", "")
    if not cleaned:
        return None
    if "," in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    try:
        return Decimal(cleaned)
    except Exception:
        return None


@dataclass(frozen=True)
class Question:
    id: str
    category: str
    topic: str
    level: str
    prompt: str
    kind: str  # choice | number | text
    correct: str
    explanation: str
    options: list[str] | None = None
    hint: str = ""
    tolerance: Decimal = Decimal("0.01")

    def check(self, answer: str) -> bool:
        if self.kind == "number":
            user = parse_number(answer)
            expected = parse_number(self.correct)
            if user is None or expected is None:
                return False
            return abs(user - expected) <= self.tolerance
        if self.kind == "text":
            # Textaufgaben werden bewusst streng geprüft. Lediglich führende/mehrfache
            # Leerzeichen werden vereinheitlicht; Groß-/Kleinschreibung und Satzzeichen
            # bleiben für Rechtschreibaufgaben relevant.
            norm = lambda s: " ".join(s.strip().split())
            return norm(answer) == norm(self.correct)
        return answer.strip() == self.correct.strip()


def choice(qid: str, category: str, topic: str, level: str, prompt: str,
           correct: str, wrong: Iterable[str], explanation: str, hint: str = "") -> Question:
    options = [correct, *wrong]
    # Doppelte Antwortmöglichkeiten vermeiden.
    unique = []
    for item in options:
        if item not in unique:
            unique.append(item)
    return Question(qid, category, topic, level, prompt, "choice", correct,
                    explanation, unique, hint)


def number(qid: str, category: str, topic: str, level: str, prompt: str,
           correct: Decimal, explanation: str, hint: str = "") -> Question:
    return Question(qid, category, topic, level, prompt, "number", money(correct),
                    explanation, None, hint)


# ---------------------------------------------------------------------------
# Bestehende Fragen aus 0.1/0.2 bleiben erhalten, damit alte Fehlerhistorien
# weiterhin sauber rekonstruiert werden können.
# ---------------------------------------------------------------------------
LEGACY = [
    choice("gp_a_01", "Geschäftsprozesse", "Vom Angebot zur Rechnung", "Anfänger",
           "Welche Unterlage kommt typischerweise vor der Bestellung?", "Angebot",
           ["Mahnung", "Rechnung", "Lieferschein"],
           "Ein Angebot informiert über Leistung, Preis und Bedingungen. Darauf kann die Bestellung folgen.",
           "Denke an die Reihenfolge vor dem Kauf."),
    choice("gp_a_02", "Geschäftsprozesse", "Lieferschein", "Anfänger",
           "Welches Dokument begleitet typischerweise die gelieferte Ware?", "Lieferschein",
           ["Angebot", "Mahnung", "Gutschrift"],
           "Der Lieferschein dokumentiert, welche Waren geliefert wurden.",
           "Das Dokument liegt oft direkt bei der Ware."),
    choice("gp_f_01", "Geschäftsprozesse", "Rechnungsprüfung", "Fortgeschritten",
           "Bestellt wurden 12 Stühle. Geliefert wurden 10, die Rechnung enthält 12. Was ist zuerst zu tun?",
           "Lieferung und Rechnung prüfen und die Abweichung klären",
           ["Rechnung ungeprüft bezahlen", "Die zwei fehlenden Stühle selbst nachbestellen", "Rechnung vernichten"],
           "Bestellung, Lieferschein, tatsächliche Lieferung und Rechnung müssen abgeglichen werden.",
           "Vergleiche Bestellung, Lieferung und Rechnung."),
    choice("gp_e_01", "Geschäftsprozesse", "Reklamation", "Experte",
           "Ein Lieferant liefert 40 Ordner. 4 sind beschädigt, 2 fehlen. Die Rechnung enthält 40 Stück. Welche Reaktion ist kaufmännisch am sinnvollsten?",
           "Abweichungen dokumentieren, Lieferanten informieren und Korrektur bzw. Ersatz abstimmen",
           ["Alles bezahlen und später prüfen", "Alle Ordner ohne Rücksprache zurückschicken", "Nur die fehlenden zwei Ordner beachten"],
           "Mengen- und Qualitätsabweichungen sollten dokumentiert und mit dem Lieferanten geklärt werden.",
           "Es liegen Mengen- und Qualitätsabweichungen vor."),
    choice("de_a_01", "Deutsch & Rechtschreibung", "Groß- und Kleinschreibung", "Anfänger",
           "Welche Schreibweise ist richtig?", "Wir senden Ihnen die Rechnung morgen zu.",
           ["Wir senden Ihnen die rechnung morgen zu.", "Wir Senden Ihnen die Rechnung morgen zu.", "wir senden Ihnen die Rechnung Morgen zu."],
           "Nomen wie „Rechnung“ werden großgeschrieben; Verben werden kleingeschrieben.",
           "Achte auf Nomen und Verben."),
    choice("de_a_02", "Deutsch & Rechtschreibung", "Kommasetzung", "Anfänger",
           "Welcher Satz ist richtig gesetzt?", "Wenn die Ware eintrifft, prüfen wir die Lieferung.",
           ["Wenn die Ware eintrifft prüfen wir die Lieferung.", "Wenn, die Ware eintrifft prüfen wir die Lieferung.", "Wenn die Ware, eintrifft prüfen wir die Lieferung."],
           "Der Nebensatz wird mit einem Komma vom Hauptsatz getrennt.",
           "Ein Nebensatz mit „wenn“ wird abgetrennt."),
    choice("de_f_01", "Deutsch & Rechtschreibung", "Getrennt- und Zusammenschreibung", "Fortgeschritten",
           "Welche Form ist im Satz richtig? „Bitte _____ Sie die Unterlagen vollständig.“", "füllen",
           ["ausfüllen", "aus füllen", "Ausfüllen"],
           "Im Hauptsatz wird das trennbare Verb „ausfüllen“ getrennt: „füllen ... aus“.",
           "Der Satz endet gedanklich mit „aus“."),
    choice("de_e_01", "Deutsch & Rechtschreibung", "Geschäftlicher Text", "Experte",
           "Welche Formulierung ist sprachlich und geschäftlich am saubersten?",
           "Bitte senden Sie uns die fehlenden Unterlagen bis zum 30. September zu.",
           ["Schicken Sie mal die Sachen bis Ende des Monats.", "Wir hätten dann gerne irgendwann die Unterlagen.", "Bitte die Unterlagen uns bis 30 September schicken."],
           "Die Formulierung ist klar, korrekt, höflich und enthält eine eindeutige Frist.",
           "Achte auf Klarheit und ein konkretes Datum."),
    choice("sv_a_01", "Schriftverkehr", "Betreff", "Anfänger",
           "Welcher Betreff ist für eine Reklamation am geeignetsten?", "Reklamation zu Lieferung Nr. 4711",
           ["Hallo", "Wichtig!!!", "Unsere Sache"],
           "Ein guter Betreff nennt Anlass und Referenz.",
           "Der Empfänger sollte den Vorgang sofort zuordnen können."),
    choice("sv_f_01", "Schriftverkehr", "Reklamation", "Fortgeschritten",
           "Welche Formulierung passt am besten in eine sachliche Reklamation?",
           "Bei der Prüfung der Lieferung haben wir festgestellt, dass zwei Artikel fehlen.",
           ["Sie haben schon wieder alles falsch gemacht.", "Das ist eine Frechheit.", "Da fehlen Sachen, kümmern Sie sich."],
           "Eine geschäftliche Reklamation beschreibt den festgestellten Mangel sachlich.",
           "Bleibe sachlich und konkret."),
    choice("sv_e_01", "Schriftverkehr", "Fristsetzung", "Experte",
           "Welche Formulierung enthält eine klare und angemessene Frist?",
           "Bitte liefern Sie die fehlenden Artikel bis spätestens 5. Oktober nach.",
           ["Bitte schnellstmöglich nachliefern.", "Bitte irgendwann nächste Woche liefern.", "Wir erwarten sofortige Erledigung!!!"],
           "Eine konkrete Datumsangabe macht die Frist eindeutig und überprüfbar.",
           "Ein Datum ist eindeutiger als „schnellstmöglich“."),
    choice("bo_a_01", "Büroorganisation", "Prioritäten", "Anfänger",
           "Welche Aufgabe sollte in der Regel zuerst bearbeitet werden?", "Eine heute ablaufende Angebotsfrist",
           ["Ein Prospekt ohne Termin", "Die Ablage alter Unterlagen", "Eine freiwillige Gestaltungsidee"],
           "Unmittelbar ablaufende Fristen haben in der Regel hohe Priorität.",
           "Achte auf Dringlichkeit und Fristen."),
    choice("bo_f_01", "Büroorganisation", "Datenschutz", "Fortgeschritten",
           "Was ist beim Verlassen des Arbeitsplatzes sinnvoll, wenn Kundendaten am Bildschirm geöffnet sind?", "Bildschirm sperren",
           ["Fenster minimieren reicht immer", "Monitor ausschalten, PC offen lassen", "Nichts, wenn man nur kurz weg ist"],
           "Durch das Sperren wird verhindert, dass Unbefugte auf die Daten zugreifen.",
           "Unbefugte sollen keinen Zugriff erhalten."),
    choice("bo_e_01", "Büroorganisation", "Terminplanung", "Experte",
           "Zwei wichtige Termine überschneiden sich. Einer betrifft eine gesetzliche Frist, der andere eine interne Besprechung. Was ist am sinnvollsten?",
           "Gesetzliche Frist absichern und die interne Besprechung abstimmen bzw. verlegen",
           ["Beide ignorieren", "Nur zur internen Besprechung gehen", "Zufällig einen Termin auswählen"],
           "Gesetzliche Fristen sind nicht frei verschiebbar; interne Termine häufig schon.",
           "Prüfe, welcher Termin weniger flexibel ist."),
]


def build_accounting() -> list[Question]:
    out: list[Question] = []
    # Anfänger: 50 eigenständige Rechenaufgaben.
    pcts = [5, 10, 12, 15, 20, 25]
    for i in range(20):
        base = Decimal(120 + i * 35)
        pct = Decimal(pcts[i % len(pcts)])
        result = base * pct / Decimal(100)
        out.append(number(f"rw_a_pct_{i+1:02d}", "Rechnungswesen", "Prozentrechnung", "Anfänger",
                          f"Wie viel sind {pct}% von {money(base)}?", result,
                          f"{money(base)} × {pct}/100 = {money(result)}.",
                          "Grundwert × Prozentsatz / 100."))
    for i in range(15):
        price = Decimal(250 + i * 70)
        pct = Decimal([5, 10, 15, 20, 25][i % 5])
        result = price * pct / Decimal(100)
        out.append(number(f"rw_a_rab_{i+1:02d}", "Rechnungswesen", "Rabatt", "Anfänger",
                          f"Eine Ware kostet {money(price)}. Es werden {pct}% Rabatt gewährt. Wie hoch ist der Rabattbetrag?",
                          result, f"Rabatt = {money(price)} × {pct}/100 = {money(result)}.",
                          "Berechne den Prozentsatz vom Ausgangspreis."))
    for i in range(15):
        net = Decimal(300 + i * 90)
        tax = net * Decimal(19) / Decimal(100)
        out.append(number(f"rw_a_ust_{i+1:02d}", "Rechnungswesen", "Umsatzsteuer", "Anfänger",
                          f"Der Nettobetrag beträgt {money(net)}. Wie hoch sind 19% Umsatzsteuer?",
                          tax, f"Umsatzsteuer = {money(net)} × 19/100 = {money(tax)}.",
                          "Nettobetrag × 19 / 100."))

    # Fortgeschritten: 50 Aufgaben mit mindestens zwei Rechenschritten.
    discounts = [5, 8, 10, 12, 15, 20]
    for i in range(20):
        net = Decimal(600 + i * 85)
        disc = Decimal(discounts[i % len(discounts)])
        after = net * (Decimal(100) - disc) / Decimal(100)
        gross = (after * Decimal("1.19")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        out.append(number(f"rw_f_rabust_{i+1:02d}", "Rechnungswesen", "Rabatt und Umsatzsteuer", "Fortgeschritten",
                          f"Der Listenpreis beträgt {money(net)} netto. Es werden {disc}% Rabatt gewährt. Danach kommen 19% Umsatzsteuer hinzu. Wie hoch ist der Bruttorechnungsbetrag?",
                          gross, f"Nach Rabatt: {money(after)}. Brutto: {money(after)} × 1,19 = {money(gross)}.",
                          "Erst Rabatt vom Nettobetrag abziehen, danach Umsatzsteuer berechnen."))
    for i in range(15):
        gross = Decimal(800 + i * 125)
        skonto = Decimal([2, 3][i % 2])
        amount = gross * skonto / Decimal(100)
        out.append(number(f"rw_f_sko_{i+1:02d}", "Rechnungswesen", "Skonto", "Fortgeschritten",
                          f"Eine Bruttorechnung beträgt {money(gross)}. Bei fristgerechter Zahlung dürfen {skonto}% Skonto abgezogen werden. Wie hoch ist der Skontobetrag?",
                          amount, f"Skonto = {money(gross)} × {skonto}/100 = {money(amount)}.",
                          "Berechne den Skontoprozentsatz vom Rechnungsbetrag."))
    for i in range(15):
        qty = 5 + (i % 6)
        unit = Decimal("39.50") + Decimal(i * 7)
        net = unit * qty
        gross = (net * Decimal("1.19")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        out.append(number(f"rw_f_menge_{i+1:02d}", "Rechnungswesen", "Menge und Umsatzsteuer", "Fortgeschritten",
                          f"Es werden {qty} Artikel zu je {money(unit)} netto bestellt. Wie hoch ist der gesamte Bruttobetrag inklusive 19% Umsatzsteuer?",
                          gross, f"Netto: {qty} × {money(unit)} = {money(net)}. Brutto: {money(net)} × 1,19 = {money(gross)}.",
                          "Zuerst Menge × Einzelpreis, danach 19% Umsatzsteuer."))

    # Experte: 50 mehrstufige Fälle.
    for i in range(30):
        qty = 8 + (i % 13)
        unit = Decimal("49.90") + Decimal(i * 4)
        disc = Decimal([5, 8, 10, 12][i % 4])
        skonto = Decimal([2, 3][i % 2])
        list_total = unit * qty
        target = list_total * (Decimal(100) - disc) / Decimal(100)
        gross = target * Decimal("1.19")
        payment = (gross * (Decimal(100) - skonto) / Decimal(100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        out.append(number(f"rw_e_multi_{i+1:02d}", "Rechnungswesen", "Mehrstufige Rechnung", "Experte",
                          f"Ein Unternehmen bestellt {qty} Artikel zu je {money(unit)} netto. Es erhält {disc}% Rabatt. Auf den rabattierten Nettobetrag kommen 19% Umsatzsteuer. Bei Zahlung innerhalb der Frist dürfen {skonto}% Skonto vom Bruttobetrag abgezogen werden. Wie viel wird überwiesen?",
                          payment,
                          f"Listenwert {money(list_total)} → nach Rabatt {money(target)} → brutto {money(gross)} → nach Skonto {money(payment)}.",
                          "Reihenfolge: Menge × Preis → Rabatt → Umsatzsteuer → Skonto."))
    for i in range(20):
        ordered = 12 + (i % 9)
        delivered = ordered - [1, 2, 3][i % 3]
        unit = Decimal("69.00") + Decimal(i * 6)
        disc = Decimal([0, 5, 10][i % 3])
        delivered_net = unit * delivered * (Decimal(100) - disc) / Decimal(100)
        corrected = (delivered_net * Decimal("1.19")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        out.append(number(f"rw_e_lief_{i+1:02d}", "Rechnungswesen", "Rechnungsprüfung", "Experte",
                          f"Bestellt wurden {ordered} Stück zu je {money(unit)} netto, geliefert aber nur {delivered}. Vereinbart sind {disc}% Rabatt. Wie hoch wäre der Bruttobetrag für die tatsächlich gelieferte Menge?",
                          corrected,
                          f"Gelieferte Menge: {delivered} × {money(unit)} = {money(unit * delivered)} netto. Nach Rabatt: {money(delivered_net)}. Brutto: {money(corrected)}.",
                          "Berechne nur die tatsächlich gelieferte Menge und berücksichtige den vereinbarten Rabatt."))
    return out


def build_german() -> list[Question]:
    out: list[Question] = []
    # Anfänger: 20 Groß-/Kleinschreibung
    noun_phrases = [
        "die Rechnung", "den Lieferschein", "das Angebot", "die Bestellung", "die Unterlagen",
        "den Vertrag", "die Mahnung", "die Gutschrift", "den Termin", "die Anfrage",
        "den Auftrag", "die Lieferung", "die Zahlung", "die Ware", "den Kunden",
        "die E-Mail", "das Formular", "die Kopie", "den Beleg", "die Rechnungskopie",
    ]
    for i, phrase in enumerate(noun_phrases, 1):
        article, noun = phrase.split(" ", 1)
        correct = f"Wir senden Ihnen {article} {noun} morgen zu."
        wrong = [
            f"Wir senden Ihnen {article} {noun.lower()} morgen zu.",
            f"Wir Senden Ihnen {article} {noun} morgen zu.",
            f"wir senden Ihnen {article} {noun} Morgen zu.",
        ]
        out.append(choice(f"de_a_gross_{i:02d}", "Deutsch & Rechtschreibung", "Groß- und Kleinschreibung", "Anfänger",
                          f"Welche Schreibweise ist richtig? ({noun})", correct, wrong,
                          "Nomen werden großgeschrieben; Verben und gewöhnliche Adverbien kleingeschrieben.",
                          "Achte besonders auf das Nomen im Satz."))

    # Anfänger: 20 Kommafragen
    clauses = [
        ("Wenn die Ware eintrifft", "prüfen wir die Lieferung"),
        ("Weil die Rechnung fehlerhaft ist", "bitten wir um Korrektur"),
        ("Sobald der Kunde antwortet", "melden wir uns bei Ihnen"),
        ("Obwohl die Frist knapp ist", "bearbeiten wir den Auftrag heute"),
        ("Bevor wir die Rechnung bezahlen", "prüfen wir die Positionen"),
        ("Nachdem die Ware angekommen ist", "kontrollieren wir die Stückzahl"),
        ("Da der Termin ausfällt", "informieren wir alle Teilnehmer"),
        ("Falls Unterlagen fehlen", "fordern wir diese nach"),
        ("Während der Kunde wartet", "prüfen wir den Vorgang"),
        ("Damit die Lieferung pünktlich ankommt", "geben wir den Auftrag heute frei"),
        ("Wenn die Zahlung eingeht", "verbuchen wir den Betrag"),
        ("Weil der Artikel nicht lieferbar ist", "bieten wir eine Alternative an"),
        ("Sobald die Freigabe vorliegt", "versenden wir die Bestellung"),
        ("Obwohl der Kunde bereits angerufen hat", "senden wir zusätzlich eine E-Mail"),
        ("Bevor das Angebot versendet wird", "prüfen wir die Preise"),
        ("Nachdem die Rechnung korrigiert wurde", "geben wir sie zur Zahlung frei"),
        ("Falls sich der Termin ändert", "informieren wir das Team"),
        ("Da die Ware beschädigt ist", "reklamieren wir die Lieferung"),
        ("Wenn die Frist morgen endet", "bearbeiten wir den Vorgang heute"),
        ("Damit keine Daten verloren gehen", "speichern wir die Datei regelmäßig"),
        ("Sobald die Bestellung freigegeben ist", "leiten wir sie an den Lieferanten weiter"),
    ]
    for i, (sub, main) in enumerate(clauses, 1):
        correct = f"{sub}, {main}."
        wrong = [f"{sub} {main}.", f"{sub.split(' ', 1)[0]}, {sub.split(' ', 1)[1]} {main}.", f"{sub}, {main.replace(' wir ', ', wir ', 1)}."]
        out.append(choice(f"de_a_komma_{i:02d}", "Deutsch & Rechtschreibung", "Kommasetzung", "Anfänger",
                          "Welcher Satz ist richtig gesetzt?", correct, wrong,
                          "Ein einleitender Nebensatz wird mit einem Komma vom Hauptsatz getrennt.",
                          "Suche die Grenze zwischen Nebensatz und Hauptsatz."))

    # Anfänger: 20 häufige Schreibweisen
    spelling = [
        ("Adresse", ["Addresse", "Adrese", "Adressse"]), ("Bestellung", ["Bestelung", "Bestellungg", "bestellung"]),
        ("Rechnung", ["Rechnunng", "Rechung", "rechnung"]), ("Lieferung", ["Liferung", "Lieferunng", "lieferung"]),
        ("Geschäftsführer", ["Geschäftsfüher", "Geschäfts Führer", "geschäftsführer"]), ("Kündigung", ["Kündigun", "Kündigunng", "kündigung"]),
        ("Rückmeldung", ["Rück Meldung", "Rückmeldunng", "rückmeldung"]), ("voraussichtlich", ["vorraussichtlich", "voraussichtlig", "Voraussichtlich"]),
        ("selbstständig", ["selbständigg", "selbst ständig", "Selbstständig"]), ("Auftragsbestätigung", ["Auftrags Bestätigung", "Auftragsbestätigun", "auftragsbestätigung"]),
        ("Reklamation", ["Reklamatzion", "Reklamtion", "reklamation"]), ("Korrespondenz", ["Korespondenz", "Korrespodenz", "korrespondenz"]),
        ("Empfänger", ["Empfenger", "Empfängger", "empfänger"]), ("fristgerecht", ["frist gerechtt", "Fristgerecht", "fristgerech"]),
        ("vollständig", ["voll ständig", "vollständich", "Vollständig"]), ("Bestätigung", ["Bestättigung", "Bestetigung", "bestätigung"]),
        ("zuständig", ["zu ständig", "zuständich", "Zuständig"]), ("verfügbar", ["verfühgbar", "verfüg baar", "Verfügbar"]),
        ("Rücksprache", ["Rück Sprache", "Rückspraache", "rücksprache"]), ("Dokumentation", ["Dokumentazion", "Dokumentationn", "dokumentation"]),
    ]
    for i, (word, wrong) in enumerate(spelling, 1):
        out.append(choice(f"de_a_spell_{i:02d}", "Deutsch & Rechtschreibung", "Rechtschreibung", "Anfänger",
                          "Welche Schreibweise ist richtig?", word, wrong,
                          f"Die korrekte Schreibweise lautet „{word}“.", "Lies die Wörter langsam und achte auf Doppelkonsonanten und Endungen."))

    # Fortgeschritten: 20 Getrennt-/Zusammenschreibung in eindeutigen Infinitiven.
    verbs = [
        ("ausfüllen", "Bitte das Formular vollständig ausfüllen."), ("nachreichen", "Bitte die fehlenden Unterlagen nachreichen."),
        ("absagen", "Wir müssen den Termin leider absagen."), ("bestätigen", "Bitte den Eingang schriftlich bestätigen."),
        ("weiterleiten", "Bitte die E-Mail an die Buchhaltung weiterleiten."), ("zurücksenden", "Bitte die unterschriebene Kopie zurücksenden."),
        ("nachfragen", "Wir sollten beim Lieferanten nachfragen."), ("vorbereiten", "Bitte die Besprechung gut vorbereiten."),
        ("festlegen", "Wir müssen einen neuen Termin festlegen."), ("zusammenfassen", "Bitte die Ergebnisse kurz zusammenfassen."),
        ("bereitstellen", "Bitte die Unterlagen digital bereitstellen."), ("nachbestellen", "Wir müssen fünf Ordner nachbestellen."),
        ("freigeben", "Wir müssen die Rechnung vor der Zahlung freigeben."), ("abgleichen", "Bitte Bestellung und Rechnung miteinander abgleichen."),
        ("eintragen", "Bitte den Termin im Kalender eintragen."), ("nachliefern", "Der Lieferant soll die fehlende Ware nachliefern."),
        ("zurückrufen", "Bitte den Kunden heute zurückrufen."), ("mitteilen", "Wir möchten Ihnen die Änderung schriftlich mitteilen."),
        ("vorlegen", "Bitte die Unterlagen der Geschäftsleitung vorlegen."), ("aufbewahren", "Wir müssen Geschäftsunterlagen geordnet aufbewahren."),
    ]
    for i, (verb, sentence) in enumerate(verbs, 1):
        split = verb.replace("zurück", "zurück ").replace("weiter", "weiter ").replace("nach", "nach ").replace("vor", "vor ").replace("fest", "fest ").replace("zusammen", "zusammen ").replace("bereit", "bereit ").replace("frei", "frei ").replace("ab", "ab ").replace("ein", "ein ").replace("mit", "mit ").replace("auf", "auf ")
        split = " ".join(split.split())
        wrong = [sentence.replace(verb, split), sentence.replace(verb, verb.capitalize()), sentence.replace(verb, verb + " ")]
        out.append(choice(f"de_f_getr_{i:02d}", "Deutsch & Rechtschreibung", "Getrennt- und Zusammenschreibung", "Fortgeschritten",
                          "Welcher Satz ist orthografisch richtig?", sentence, wrong,
                          f"In diesem Infinitiv wird „{verb}“ zusammengeschrieben.",
                          "Achte auf die Schreibweise des Verbs im Infinitiv."))

    # Fortgeschritten: 20 Kommas mit Nebensätzen und Relativsätzen.
    complex_sentences = [
        "Die Rechnung, die gestern eingegangen ist, wird heute geprüft.",
        "Der Kunde, dessen Auftrag noch offen ist, hat erneut angerufen.",
        "Wir informieren Sie, sobald die Ware versendet wurde.",
        "Bitte prüfen Sie, ob alle Positionen korrekt sind.",
        "Da die Lieferung verspätet ist, informieren wir den Kunden.",
        "Der Termin, den wir für Montag geplant hatten, muss verschoben werden.",
        "Wir melden uns, wenn uns die Freigabe vorliegt.",
        "Die Unterlagen, die Sie angefordert haben, sind beigefügt.",
        "Obwohl die Rechnung bereits bezahlt wurde, fehlt noch der Beleg.",
        "Bitte teilen Sie uns mit, wann die Ersatzlieferung eintrifft.",
        "Der Lieferant, mit dem wir gesprochen haben, prüft den Vorgang.",
        "Wenn der Betrag eingegangen ist, wird der Auftrag freigegeben.",
        "Wir prüfen, ob der vereinbarte Rabatt berücksichtigt wurde.",
        "Die Mitarbeiterin, die den Vorgang bearbeitet, ist heute nicht im Haus.",
        "Bevor Sie die Datei versenden, prüfen Sie bitte den Anhang.",
        "Der Kunde fragt, ob eine frühere Lieferung möglich ist.",
        "Nachdem wir die Reklamation erhalten haben, prüfen wir den Sachverhalt.",
        "Die Ware, die beschädigt angekommen ist, wird ersetzt.",
        "Wir bestätigen, dass Ihre Bestellung bei uns eingegangen ist.",
        "Falls Sie Rückfragen haben, stehen wir Ihnen gern zur Verfügung.",
    ]
    for i, correct in enumerate(complex_sentences, 1):
        no_commas = correct.replace(",", "")
        wrong_place = correct.replace(", ", " ", 1)
        too_many = correct.replace(" ist", ", ist", 1) if " ist" in correct else correct.replace(" wir", ", wir", 1)
        out.append(choice(f"de_f_komma_{i:02d}", "Deutsch & Rechtschreibung", "Kommasetzung", "Fortgeschritten",
                          "Welche Version ist richtig gesetzt?", correct, [no_commas, wrong_place, too_many],
                          "Nebensätze und Relativsätze werden durch Kommas abgegrenzt.",
                          "Suche Nebensätze und eingeschobene Relativsätze."))

    # Fortgeschritten: 20 Nominalisierungen.
    nominal = [
        ("Beim Prüfen der Rechnung fiel der Fehler auf.", "Prüfen"), ("Zum Bearbeiten des Auftrags fehlen noch Angaben.", "Bearbeiten"),
        ("Das Ausfüllen des Formulars dauert nur wenige Minuten.", "Ausfüllen"), ("Beim Öffnen der Datei erschien eine Meldung.", "Öffnen"),
        ("Zum Versenden benötigen wir die vollständige Adresse.", "Versenden"), ("Das Speichern der Datei ist abgeschlossen.", "Speichern"),
        ("Beim Telefonieren sollten vertrauliche Daten geschützt werden.", "Telefonieren"), ("Das Prüfen der Lieferung gehört zum Wareneingang.", "Prüfen"),
        ("Zum Nachbestellen benötigen wir die Artikelnummer.", "Nachbestellen"), ("Beim Planen des Termins sind alle Beteiligten zu berücksichtigen.", "Planen"),
        ("Das Schreiben der E-Mail übernimmt Frau Becker.", "Schreiben"), ("Beim Sortieren der Post fiel der Brief auf.", "Sortieren"),
        ("Zum Ablegen verwenden wir die festgelegte Struktur.", "Ablegen"), ("Das Weiterleiten der Nachricht ist nicht erforderlich.", "Weiterleiten"),
        ("Beim Vergleichen der Preise wurde ein Unterschied erkannt.", "Vergleichen"), ("Das Nachfragen beim Kunden ist sinnvoll.", "Nachfragen"),
        ("Zum Vorbereiten der Sitzung gehört die Tagesordnung.", "Vorbereiten"), ("Beim Erfassen der Daten ist Sorgfalt wichtig.", "Erfassen"),
        ("Das Kontrollieren der Fristen erfolgt täglich.", "Kontrollieren"), ("Zum Archivieren gelten feste Regeln.", "Archivieren"),
    ]
    for i, (correct, word) in enumerate(nominal, 1):
        wrong = [correct.replace(word, word.lower()), correct.replace(word, word.upper()), correct.replace(word, word.lower(), 1).replace("Das ", "das ", 1)]
        out.append(choice(f"de_f_nom_{i:02d}", "Deutsch & Rechtschreibung", "Nominalisierung", "Fortgeschritten",
                          "Welcher Satz ist richtig geschrieben?", correct, wrong,
                          "Nominalisierte Verben werden großgeschrieben.",
                          "Achte auf Signalwörter wie „beim“, „zum“ und „das“."))

    # Experte: 20 klare geschäftliche Formulierungen.
    expert_pairs = [
        ("Bitte senden Sie uns die fehlenden Unterlagen bis zum 15. Oktober zu.", "konkrete Frist"),
        ("Bei der Prüfung Ihrer Lieferung haben wir festgestellt, dass drei Artikel fehlen.", "sachliche Feststellung"),
        ("Wir bestätigen den Eingang Ihrer Bestellung vom 12. September.", "klare Bestätigung"),
        ("Bitte teilen Sie uns mit, ob der vorgeschlagene Termin für Sie möglich ist.", "präzise Rückfrage"),
        ("Die korrigierte Rechnung finden Sie im Anhang dieser E-Mail.", "eindeutiger Anhanghinweis"),
        ("Aufgrund der Lieferverzögerung verschiebt sich der Termin voraussichtlich um zwei Werktage.", "konkrete Information"),
        ("Wir bitten Sie, den offenen Betrag bis spätestens 30. September zu überweisen.", "klare Zahlungsfrist"),
        ("Für Rückfragen zum Angebot steht Ihnen Frau Meyer gern zur Verfügung.", "Ansprechpartner"),
        ("Bitte bestätigen Sie uns den Erhalt dieser Nachricht kurz per E-Mail.", "klare Bitte"),
        ("Die von Ihnen gemeldete Abweichung wird derzeit geprüft.", "sachliche Statusinformation"),
        ("Wir haben den Termin auf Dienstag, den 6. Oktober, um 10:00 Uhr verschoben.", "eindeutiger Termin"),
        ("Bitte verwenden Sie für Rückfragen die Vorgangsnummer 4817.", "eindeutige Zuordnung"),
        ("Die Ersatzlieferung wird nach aktuellem Stand am Freitag versendet.", "transparenter Status"),
        ("Wir bitten um Entschuldigung für die entstandene Verzögerung.", "professionelle Entschuldigung"),
        ("Bitte prüfen Sie die beigefügte Auftragsbestätigung und melden Sie Abweichungen zeitnah.", "klare Handlungsaufforderung"),
        ("Die vereinbarte Zahlungsfrist beträgt 14 Tage ab Rechnungsdatum.", "eindeutige Bedingung"),
        ("Wir können den gewünschten Artikel derzeit nicht liefern und bieten Ihnen eine Alternative an.", "sachliche Alternative"),
        ("Ihre Reklamation wurde unter der Vorgangsnummer 7264 erfasst.", "Nachverfolgbarkeit"),
        ("Bitte senden Sie personenbezogene Unterlagen ausschließlich über den vorgesehenen sicheren Übertragungsweg.", "Datenschutz"),
        ("Wir melden uns spätestens bis Mittwoch mit einer abschließenden Rückmeldung.", "verbindliche Rückmeldung"),
    ]
    for i, (correct, reason) in enumerate(expert_pairs, 1):
        wrong = [
            correct.replace("Bitte ", "Mach bitte ", 1),
            correct.replace(".", "!!!", 1),
            "Wegen der Sache melden wir uns dann irgendwann.",
        ]
        out.append(choice(f"de_e_stil_{i:02d}", "Deutsch & Rechtschreibung", "Geschäftlicher Ausdruck", "Experte",
                          "Welche Formulierung ist sprachlich und geschäftlich am geeignetsten?", correct, wrong,
                          f"Die Formulierung ist korrekt und erfüllt das Kriterium „{reason}“.",
                          "Achte auf Klarheit, vollständige Sätze und sachlichen Ton."))

    # Experte: 20 komplexe Kommasätze.
    expert_commas = [
        "Die Rechnung, die wir gestern erhalten haben, enthält, obwohl der Rabatt vereinbart war, den Listenpreis.",
        "Wenn die Ware, die für Montag angekündigt wurde, nicht eintrifft, informieren wir den Kunden.",
        "Der Lieferant teilte mit, dass die Ersatzlieferung, sofern keine Verzögerung eintritt, morgen versendet wird.",
        "Bitte prüfen Sie, ob die Daten, die im Formular eingetragen wurden, vollständig sind.",
        "Nachdem der Kunde bestätigt hatte, dass die Menge stimmt, wurde die Rechnung freigegeben.",
        "Die Mitarbeiterin, die den Termin koordiniert, informiert alle Beteiligten, sobald die Uhrzeit feststeht.",
        "Obwohl die Zahlung bereits angewiesen wurde, prüfen wir, ob der Betrag korrekt verbucht wurde.",
        "Der Auftrag, den wir priorisiert haben, wird, sobald die Freigabe vorliegt, an das Lager übergeben.",
        "Falls die Unterlagen, die Sie gestern versendet haben, unvollständig sind, melden wir uns erneut.",
        "Wir bitten Sie, uns mitzuteilen, wann die Ware, die derzeit fehlt, nachgeliefert wird.",
        "Die Besprechung, die ursprünglich für Freitag geplant war, findet, sofern alle zustimmen, am Donnerstag statt.",
        "Da die Rechnung, die uns vorliegt, eine falsche Menge enthält, bitten wir um eine Korrektur.",
        "Bevor wir entscheiden, ob das Angebot angenommen wird, vergleichen wir die Konditionen.",
        "Der Kunde fragte, ob die Lieferung, die für nächste Woche vorgesehen ist, vorgezogen werden kann.",
        "Wir bestätigen, dass die Unterlagen, die Sie angefordert haben, heute versendet wurden.",
        "Sobald feststeht, welche Artikel fehlen, erstellen wir, falls erforderlich, eine Nachbestellung.",
        "Der Vorgang, der gestern eskaliert wurde, bleibt offen, bis die Rückmeldung des Lieferanten vorliegt.",
        "Obwohl der Termin bestätigt war, musste er, weil ein Teilnehmer erkrankt ist, verschoben werden.",
        "Bitte beachten Sie, dass die Frist, die im Schreiben genannt ist, weiterhin gilt.",
        "Wenn Sie feststellen, dass Angaben fehlen, ergänzen Sie diese, bevor Sie das Formular weiterleiten.",
    ]
    for i, correct in enumerate(expert_commas, 1):
        wrong = [correct.replace(",", "", 1), correct.replace(", ", " ", 2), correct.replace(" wird", ", wird", 1)]
        out.append(choice(f"de_e_komma_{i:02d}", "Deutsch & Rechtschreibung", "Kommasetzung", "Experte",
                          "Welche Version ist korrekt gesetzt?", correct, wrong,
                          "Mehrere Neben- und Einschubsätze müssen jeweils korrekt durch Kommas abgegrenzt werden.",
                          "Bestimme zuerst Hauptsatz, Nebensätze und Einschübe."))

    # Experte: 20 präzise Schreibweisen im Büroalltag.
    expert_spelling = [
        ("Eingangsbestätigung", ["Eingangs Bestätigung", "Eingangsbestättigung", "eingangsbestätigung"]),
        ("Zahlungserinnerung", ["Zahlungs Erinnerung", "Zahlungserinerrung", "zahlungserinnerung"]),
        ("Auftragsbearbeitung", ["Auftrags Bearbeitung", "Auftragsbearbeitunng", "auftragsbearbeitung"]),
        ("Rechnungsprüfung", ["Rechnungs Prüfung", "Rechnungsprüfunng", "rechnungsprüfung"]),
        ("Lieferverzögerung", ["Liefer Verzögerung", "Lieferverzögerunng", "lieferverzögerung"]),
        ("Datenschutzerklärung", ["Datenschutz Erklärung", "Datenschutzerklährung", "datenschutzerklärung"]),
        ("Terminverschiebung", ["Termin Verschiebung", "Terminverschibung", "terminverschiebung"]),
        ("Fristverlängerung", ["Frist Verlängerung", "Fristverlängerunng", "fristverlängerung"]),
        ("Bestellbestätigung", ["Bestell Bestätigung", "Bestellbestättigung", "bestellbestätigung"]),
        ("Wareneingangskontrolle", ["Wareneingangs Kontrolle", "Wareneingangskontrole", "wareneingangskontrolle"]),
        ("Rückrufbitte", ["Rückruf Bitte", "Rückrufbiette", "rückrufbitte"]),
        ("Besprechungsprotokoll", ["Besprechungs Protokoll", "Besprechungsprotokol", "besprechungsprotokoll"]),
        ("Ansprechpartner", ["Ansprech Partner", "Ansprechpartnner", "ansprechpartner"]),
        ("Bearbeitungsstand", ["Bearbeitungs Stand", "Bearbeitungsstannd", "bearbeitungsstand"]),
        ("Vertragsunterlagen", ["Vertrags Unterlagen", "Vertragsunterlaggen", "vertragsunterlagen"]),
        ("Zahlungsbedingungen", ["Zahlungs Bedingungen", "Zahlungsbedingunngen", "zahlungsbedingungen"]),
        ("Lieferbedingungen", ["Liefer Bedingungen", "Lieferbedingunngen", "lieferbedingungen"]),
        ("Kostenübersicht", ["Kosten Übersicht", "Kostenübersichht", "kostenübersicht"]),
        ("Vertretungsregelung", ["Vertretungs Regelung", "Vertretungsregelunng", "vertretungsregelung"]),
        ("Dokumentenablage", ["Dokumenten Ablage", "Dokumentenablagge", "dokumentenablage"]),
    ]
    for i, (word, wrong) in enumerate(expert_spelling, 1):
        out.append(choice(f"de_e_spell_{i:02d}", "Deutsch & Rechtschreibung", "Rechtschreibung", "Experte",
                          "Welche Schreibweise ist korrekt?", word, wrong,
                          f"Die korrekte Zusammenschreibung lautet „{word}“.",
                          "Achte auf zusammengesetzte Nomen und korrekte Wortstämme."))
    return out


def build_office() -> list[Question]:
    out: list[Question] = []
    # Anfänger: 40 Grundlagenfälle.
    urgent = [
        ("Eine Angebotsfrist endet heute um 14 Uhr.", "Eine Broschüre soll irgendwann überarbeitet werden."),
        ("Ein Kunde wartet auf eine heute zugesagte Rückmeldung.", "Die Ablage alter Prospekte ist offen."),
        ("Eine Rechnung muss heute geprüft werden, damit Skonto genutzt werden kann.", "Ein interner Ordner soll neu beschriftet werden."),
        ("Eine gesetzte Rückmeldefrist endet heute.", "Der Schreibtisch soll neu sortiert werden."),
        ("Eine Besprechung beginnt in 20 Minuten und die Unterlagen fehlen noch.", "Eine Präsentationsvorlage könnte verschönert werden."),
        ("Ein Lieferant meldet einen Ausfall für eine heute benötigte Lieferung.", "Alte Notizen könnten archiviert werden."),
        ("Die Geschäftsleitung benötigt eine Auswertung bis 12 Uhr.", "Ein nicht dringender Termin für nächsten Monat kann geplant werden."),
        ("Ein Kunde meldet eine fehlerhafte Rechnung mit Zahlungsfrist heute.", "Der E-Mail-Ordner kann aufgeräumt werden."),
        ("Eine Bestellung muss heute freigegeben werden, damit die Lieferfrist eingehalten wird.", "Eine interne Checkliste kann später formatiert werden."),
        ("Ein Termin mit externen Gästen startet gleich und der Raum ist noch nicht vorbereitet.", "Die Materialschublade kann neu sortiert werden."),
    ]
    for i, (high, low) in enumerate(urgent, 1):
        out.append(choice(f"bo_a_prio_{i:02d}", "Büroorganisation", "Prioritäten", "Anfänger",
                          f"Welche Aufgabe hat in dieser Situation die höhere Priorität?\nA: {high}\nB: {low}", high,
                          [low, "Beide grundsätzlich ignorieren", "Zuerst eine neue freiwillige Aufgabe beginnen"],
                          "Fristen, zugesagte Termine und unmittelbare Auswirkungen bestimmen die Priorität.",
                          "Achte auf Zeitdruck und Folgen einer Verzögerung."))
    privacy = [
        ("Du verlässt kurz deinen Arbeitsplatz. Auf dem Bildschirm sind Kundendaten geöffnet.", "Bildschirm sperren"),
        ("Ein Ausdruck mit personenbezogenen Daten wird nicht mehr benötigt.", "Nach den betrieblichen Vorgaben sicher vernichten"),
        ("Eine unbekannte Person bittet telefonisch um Kundendaten.", "Identität und Berechtigung prüfen, bevor Daten genannt werden"),
        ("Du versendest personenbezogene Daten per E-Mail.", "Nur den vorgesehenen sicheren Übertragungsweg verwenden"),
        ("Ein Kollege ohne Bezug zum Vorgang fragt nach vertraulichen Daten.", "Daten nur bei berechtigtem Bedarf weitergeben"),
        ("Du findest einen vertraulichen Ausdruck am Gemeinschaftsdrucker.", "Ausdruck sichern und dem zuständigen Empfänger zuordnen"),
        ("Ein Passwort steht auf einem Zettel am Monitor.", "Zettel entfernen und Passwort sicher verwalten"),
        ("Eine Datei mit Kundendaten soll auf einen privaten USB-Stick kopiert werden.", "Betriebliche Vorgaben beachten und private Datenträger nicht ungeprüft nutzen"),
        ("Ein Besucher wartet allein im Bürobereich mit offenen Akten.", "Vertrauliche Unterlagen sichern und Besucher nicht unbeaufsichtigt bei Daten lassen"),
        ("Du erhältst eine verdächtige E-Mail mit Anhang.", "Anhang nicht öffnen und nach betrieblichem Verfahren melden"),
    ]
    for i, (scenario, correct) in enumerate(privacy, 1):
        out.append(choice(f"bo_a_ds_{i:02d}", "Büroorganisation", "Datenschutz und Sicherheit", "Anfänger", scenario,
                          correct, ["Nichts unternehmen", "Daten möglichst breit weitergeben", "Die Situation ignorieren"],
                          "Vertrauliche Daten und Systeme müssen vor unberechtigtem Zugriff geschützt werden.",
                          "Wähle die sicherste und betrieblich nachvollziehbare Handlung."))
    filing = [
        ("Eine neue Rechnung wird digital abgelegt.", "Nach der festgelegten Ablagestruktur und eindeutig benannt"),
        ("Zwei Versionen einer Datei existieren.", "Versionen eindeutig kennzeichnen und die gültige Fassung erkennbar halten"),
        ("Ein Dokument wird häufig benötigt.", "An einem festgelegten, für Berechtigte schnell auffindbaren Ort ablegen"),
        ("Eine Datei heißt nur „neu2finalwirklich.pdf“.", "Einen eindeutigen Dateinamen nach betrieblichem Schema verwenden"),
        ("Eine Papierakte wird ergänzt.", "Unterlagen nach der festgelegten Ordnung einsortieren"),
        ("Ein Dokument gehört zu einem bestimmten Vorgang.", "Mit der passenden Vorgangs- oder Kundenzuordnung ablegen"),
        ("Eine veraltete Vorlage wird entdeckt.", "Als veraltet kennzeichnen bzw. nach Vorgabe aus dem aktiven Bestand entfernen"),
        ("Ein Beleg kann nicht gefunden werden.", "Zuerst die definierte Ablagestruktur und Suchkriterien systematisch prüfen"),
        ("Eine Datei wird gemeinsam bearbeitet.", "Klare Versionierung und Zuständigkeit verwenden"),
        ("Ein Dokument soll später nachvollziehbar sein.", "Aussagekräftige Bezeichnung und geordnete Ablage nutzen"),
    ]
    for i, (scenario, correct) in enumerate(filing, 1):
        out.append(choice(f"bo_a_abl_{i:02d}", "Büroorganisation", "Ablage", "Anfänger", scenario,
                          correct, ["Beliebig speichern", "Nur auf dem Desktop ablegen", "Ohne Namen in einen zufälligen Ordner verschieben"],
                          "Eine einheitliche Ablage erleichtert Auffinden, Versionierung und Nachvollziehbarkeit.",
                          "Denke an eindeutige Namen und feste Ablagestrukturen."))
    basics = [
        ("Ein Telefonat betrifft einen Kollegen, der nicht erreichbar ist.", "Name, Rückrufnummer, Anliegen und Zeitpunkt notieren"),
        ("Eine Besprechung wird geplant.", "Teilnehmer, Zeitpunkt, Ort und Ziel klären"),
        ("Ein Termin wird verschoben.", "Alle betroffenen Teilnehmer zeitnah informieren"),
        ("Eine Aufgabe hat eine feste Frist.", "Frist im Kalender bzw. Aufgabenplan vermerken und rechtzeitig einplanen"),
        ("Du erhältst mehrere E-Mails zu demselben Vorgang.", "Vorgang strukturiert zusammenhalten und eindeutig zuordnen"),
        ("Eine Aufgabe ist unklar formuliert.", "Rückfragen stellen, bevor falsche Arbeit entsteht"),
        ("Ein Besucher kommt zu einem vereinbarten Termin.", "Begrüßen, Termin prüfen und zuständige Person informieren"),
        ("Eine Besprechung endet mit mehreren Aufgaben.", "Aufgaben, Zuständigkeiten und Termine dokumentieren"),
        ("Ein Kollege übernimmt deine Vertretung.", "Wichtige offene Vorgänge und Fristen geordnet übergeben"),
        ("Ein Arbeitstag beginnt mit mehreren Aufgaben.", "Aufgaben nach Dringlichkeit, Wichtigkeit und Fristen ordnen"),
    ]
    for i, (scenario, correct) in enumerate(basics, 1):
        out.append(choice(f"bo_a_org_{i:02d}", "Büroorganisation", "Arbeitsorganisation", "Anfänger", scenario,
                          correct, ["Ohne Planung beginnen", "Die Aufgabe ignorieren", "Nur das Einfachste auswählen"],
                          "Gute Büroorganisation schafft Klarheit über Termine, Zuständigkeiten und Informationen.",
                          "Welche Handlung sorgt für Nachvollziehbarkeit und Verlässlichkeit?"))

    # Fortgeschritten: 40 praxisnahe Mehrfachsituationen.
    scenarios_f = [
        ("Um 9:00 Uhr beginnt eine Kundenbesprechung. Um 8:45 Uhr meldet ein Lieferant, dass die für die Besprechung benötigten Muster nicht angekommen sind.", "Kundenbesprechung vorbereiten, fehlende Muster sofort klären und Beteiligte über die Situation informieren"),
        ("Eine Rechnung mit Skontofrist heute liegt ungeprüft vor, gleichzeitig bittet ein Kollege um Hilfe bei einer Aufgabe ohne Termin.", "Rechnung fristgerecht prüfen und die Hilfe anschließend einplanen"),
        ("Zwei interne Termine überschneiden sich, einer davon wurde von der Geschäftsleitung als verpflichtend gekennzeichnet.", "Priorität klären und den anderen Termin aktiv abstimmen bzw. verlegen"),
        ("Ein Kunde erwartet bis 12 Uhr ein Angebot, aber eine benötigte Preisangabe fehlt.", "Preisangabe rechtzeitig beschaffen und bei absehbarer Verzögerung den Kunden informieren"),
        ("Eine dringende Aufgabe benötigt eine Freigabe, die zuständige Person ist nicht erreichbar.", "Vertretungs- oder Eskalationsweg gemäß betrieblicher Regelung nutzen"),
        ("Mehrere Aufgaben haben dieselbe Frist, aber unterschiedliche Auswirkungen.", "Nach Folgen, Abhängigkeiten und Aufwand priorisieren"),
        ("Eine Besprechung ist in 30 Minuten, die Tagesordnung wurde noch nicht verteilt.", "Tagesordnung fertigstellen und sofort an die Teilnehmer senden"),
        ("Eine wichtige E-Mail enthält unklare Aufgaben und mehrere Empfänger.", "Zuständigkeit und erwartete Handlung klären, bevor doppelte Arbeit entsteht"),
        ("Ein Kunde ruft erneut wegen eines offenen Vorgangs an, während du an einer internen Aufgabe ohne feste Frist arbeitest.", "Kundenanliegen aufnehmen, Status prüfen und verlässliche Rückmeldung geben"),
        ("Ein Kollege fällt kurzfristig aus und mehrere seiner Fristen laufen diese Woche ab.", "Offene Vorgänge und Fristen sichten, priorisieren und Vertretung organisieren"),
    ]
    for i, (scenario, correct) in enumerate(scenarios_f, 1):
        out.append(choice(f"bo_f_prio_{i:02d}", "Büroorganisation", "Prioritäten und Vertretung", "Fortgeschritten", scenario,
                          correct, ["Alle Aufgaben ungeprüft verschieben", "Nur die einfachste Aufgabe bearbeiten", "Abwarten, bis jemand nachfragt"],
                          "Bei konkurrierenden Aufgaben zählen Fristen, Auswirkungen, Abhängigkeiten und klare Kommunikation.",
                          "Prüfe Dringlichkeit, Auswirkungen und Zuständigkeit."))
    meetings = [
        ("Eine Besprechung mit acht Personen soll stattfinden.", "Ziel, Teilnehmer, Termin, Raum/Technik und Tagesordnung rechtzeitig klären"),
        ("Mehrere Teilnehmer können nur zu unterschiedlichen Zeiten.", "Verfügbarkeiten systematisch abgleichen und einen tragfähigen Termin festlegen"),
        ("Nach einer Besprechung bestehen unterschiedliche Erinnerungen an eine Entscheidung.", "Entscheidungen und Aufgaben in einem Protokoll nachvollziehbar festhalten"),
        ("Ein externer Gast nimmt digital teil.", "Zugangsdaten, Technik und Datenschutz vorab prüfen"),
        ("Ein wichtiger Tagesordnungspunkt braucht Unterlagen.", "Unterlagen rechtzeitig vorbereiten und den Teilnehmern zugänglich machen"),
        ("Eine Besprechung droht regelmäßig zu lange zu dauern.", "Klare Tagesordnung, Zeitrahmen und Moderation festlegen"),
        ("Ein Termin wird kurzfristig abgesagt.", "Alle Teilnehmer sofort informieren und Folgetermin abstimmen"),
        ("Eine Aufgabe aus der Besprechung hat keinen Verantwortlichen.", "Zuständigkeit und Termin eindeutig festlegen"),
        ("Ein Raum ist doppelt gebucht.", "Alternative organisieren und Teilnehmer rechtzeitig informieren"),
        ("Vor einer Sitzung sind vertrauliche Unterlagen zu verteilen.", "Nur berechtigten Teilnehmern über den vorgesehenen sicheren Weg bereitstellen"),
    ]
    for i, (scenario, correct) in enumerate(meetings, 1):
        out.append(choice(f"bo_f_meet_{i:02d}", "Büroorganisation", "Besprechungsorganisation", "Fortgeschritten", scenario,
                          correct, ["Ohne Vorbereitung starten", "Informationen erst nach dem Termin klären", "Nur den Raum reservieren und sonst nichts planen"],
                          "Besprechungen benötigen klare Ziele, Zuständigkeiten, Informationen und organisatorische Vorbereitung.",
                          "Denke an Vorbereitung, Durchführung und Nachbereitung."))
    data_f = [
        ("Eine E-Mail mit vertraulichem Anhang wurde versehentlich an einen falschen Empfänger gesendet.", "Betrieblichen Datenschutz-/Meldeprozess sofort einleiten und zuständige Stelle informieren"),
        ("Ein externer Dienstleister benötigt Zugriff auf eine Datei.", "Nur erforderliche Daten und passende Berechtigungen nach Freigabe bereitstellen"),
        ("Eine Kollegin bittet um dein Passwort, weil ihr Zugang nicht funktioniert.", "Passwort nicht weitergeben und einen regelkonformen Zugangsweg nutzen"),
        ("Ein Ausdruck mit Personaldaten liegt offen im Besprechungsraum.", "Unterlage sichern und der zuständigen Stelle zuführen"),
        ("Eine Datei soll an viele Empfänger geschickt werden, die sich untereinander nicht kennen.", "Geeignete Empfängerführung wählen und unnötige Offenlegung von Adressen vermeiden"),
        ("Ein privates Cloudkonto wäre bequemer für den Dateiaustausch.", "Nur betriebsseitig freigegebene Systeme verwenden"),
        ("Ein unbekannter USB-Stick wird gefunden.", "Nicht ungeprüft anschließen und nach betrieblichem Sicherheitsverfahren behandeln"),
        ("Ein ehemaliger Mitarbeiter hat noch Zugriff auf einen geteilten Ordner.", "Zugriffsberechtigung unverzüglich prüfen und anpassen lassen"),
        ("Ein Kunde bittet um Auskunft zu Daten eines anderen Kunden.", "Keine fremden Daten herausgeben und Berechtigung klar prüfen"),
        ("Ein Dokument enthält mehr personenbezogene Daten als für den Zweck nötig.", "Nur erforderliche Daten verarbeiten und unnötige Angaben vermeiden"),
    ]
    for i, (scenario, correct) in enumerate(data_f, 1):
        out.append(choice(f"bo_f_ds_{i:02d}", "Büroorganisation", "Datenschutz und IT-Sicherheit", "Fortgeschritten", scenario,
                          correct, ["Bequemsten Weg wählen, auch wenn er nicht freigegeben ist", "Daten ungeprüft weitergeben", "Nichts dokumentieren oder melden"],
                          "Datenschutz und IT-Sicherheit verlangen kontrollierte Zugriffe und definierte Meldewege.",
                          "Nutze nur berechtigte, nachvollziehbare und freigegebene Wege."))
    docs_f = [
        ("Drei Personen bearbeiten nacheinander dasselbe Dokument.", "Eine eindeutige Versionierung und Zuständigkeit festlegen"),
        ("Eine Vorlage wurde geändert, aber alte Versionen sind noch im Umlauf.", "Gültige Version kennzeichnen und alte aktive Vorlagen ersetzen"),
        ("Ein Vorgang umfasst E-Mails, Rechnung und Lieferschein.", "Unterlagen einheitlich unter dem Vorgang zusammenführen bzw. verknüpfen"),
        ("Eine Datei muss später revisionssicher nachvollziehbar sein.", "Betriebliche Aufbewahrungs- und Dokumentationsregeln einhalten"),
        ("Mehrere Dateien tragen fast identische Namen.", "Ein konsistentes Benennungsschema mit Datum/Version oder Vorgangsbezug nutzen"),
        ("Eine Freigabe wurde nur mündlich erteilt.", "Erforderliche Freigabe nach betrieblichem Verfahren nachvollziehbar dokumentieren"),
        ("Ein Dokument wird an einen anderen Bereich übergeben.", "Übergabe, Zuständigkeit und Bearbeitungsstand klar dokumentieren"),
        ("Eine Datei wird versehentlich überschrieben.", "Versionierung bzw. vorhandene Sicherungs-/Wiederherstellungsverfahren nutzen"),
        ("Eine Aufgabe wechselt den Bearbeiter.", "Offene Punkte, Fristen und letzte Schritte strukturiert übergeben"),
        ("Ein Vorgang ist abgeschlossen.", "Nach Vorgabe vollständig ablegen und erforderliche Aufbewahrung sicherstellen"),
    ]
    for i, (scenario, correct) in enumerate(docs_f, 1):
        out.append(choice(f"bo_f_doc_{i:02d}", "Büroorganisation", "Dokumentenmanagement", "Fortgeschritten", scenario,
                          correct, ["Dateien ohne Struktur verteilen", "Bearbeitungsstand nicht dokumentieren", "Beliebige Version als gültig verwenden"],
                          "Dokumentenmanagement soll Versionen, Zuständigkeiten und Vorgänge nachvollziehbar halten.",
                          "Achte auf Version, Freigabe und eindeutige Zuordnung."))

    # Experte: 40 komplexe Entscheidungssituationen.
    expert_cases = [
        ("Am Vormittag laufen eine gesetzliche Frist, eine zugesagte Kundenrückmeldung und eine interne Auswertung zusammen. Die Auswertung kann delegiert werden.", "Gesetzliche Frist absichern, Kundenrückmeldung verlässlich einplanen und delegierbare Auswertung übertragen"),
        ("Ein kritischer Lieferausfall gefährdet einen Kundentermin. Gleichzeitig findet eine interne Routinebesprechung statt.", "Lieferausfall und Kundenfolgen priorisieren, Routinebesprechung vertreten oder verschieben"),
        ("Ein Kollege fällt aus, seine Aufgaben sind nicht vollständig dokumentiert und zwei Fristen sind heute.", "Fristen und kritische Vorgänge zuerst identifizieren, Zuständigkeiten klären und fehlende Informationen gezielt beschaffen"),
        ("Zwei Vorgesetzte geben widersprüchliche Prioritäten für denselben Zeitraum.", "Konflikt transparent machen und Priorität bzw. Entscheidung mit den Verantwortlichen klären"),
        ("Eine kurzfristige Zusatzaufgabe würde eine bereits zugesagte Kundenfrist gefährden.", "Auswirkungen offenlegen, Priorität abstimmen und gegebenenfalls Ressourcen oder Termin anpassen"),
        ("Ein Prozess fällt wegen eines IT-Problems aus, mehrere Abteilungen sind betroffen.", "Störung nach Verfahren melden, Notfall-/Ersatzprozess nutzen und Betroffene über Status informieren"),
        ("Eine wichtige Aufgabe hängt von Informationen eines externen Partners ab, der nicht reagiert.", "Frühzeitig nachfassen, Eskalationsweg nutzen und internen Zeitplan an das Risiko anpassen"),
        ("Eine Aufgabe ist dringend, aber du hast dafür keine Freigabeberechtigung.", "Nicht eigenmächtig freigeben, sondern Vertretungs-/Freigabeweg nutzen und Dringlichkeit kommunizieren"),
        ("Mehrere Kunden sind von demselben Fehler betroffen.", "Ursache und betroffene Vorgänge systematisch erfassen, abgestimmte Information und Korrektur organisieren"),
        ("Ein Termin ist nicht verschiebbar, aber die zuständige Fachperson fällt aus.", "Geeignete Vertretung organisieren und Informationsübergabe sicherstellen"),
    ]
    for i, (scenario, correct) in enumerate(expert_cases, 1):
        out.append(choice(f"bo_e_komplex_{i:02d}", "Büroorganisation", "Komplexe Priorisierung", "Experte", scenario,
                          correct, ["Alle Aufgaben gleich behandeln", "Ohne Rücksprache Zusagen brechen", "Nur nach persönlicher Vorliebe entscheiden"],
                          "Komplexe Priorisierung berücksichtigt Fristen, Auswirkungen, Befugnisse, Delegation und Kommunikation.",
                          "Ordne nach Risiko, Verpflichtung, Abhängigkeit und Delegierbarkeit."))
    expert_security = [
        ("Es besteht der Verdacht, dass Zugangsdaten kompromittiert wurden.", "Zugang nach Sicherheitsverfahren absichern, Passwort ändern und zuständige IT/Sicherheitsstelle informieren"),
        ("Ein externer Empfänger meldet, dass er versehentlich vertrauliche Daten erhalten hat.", "Datenschutzvorfall nach internem Prozess melden und weitere Schritte mit zuständiger Stelle abstimmen"),
        ("Ein Team nutzt seit Monaten einen gemeinsamen Benutzerzugang.", "Individuelle, nachvollziehbare Zugänge und passende Berechtigungen einführen lassen"),
        ("Ein Mitarbeiter benötigt nur vorübergehend Zugriff auf sensible Daten.", "Zeitlich und sachlich begrenzte Berechtigung nach Freigabe vergeben"),
        ("Eine Liste mit Kundendaten soll für einen neuen Zweck genutzt werden.", "Vor Nutzung Zweck, Berechtigung und betriebliche Datenschutzvorgaben prüfen"),
        ("Ein mobiles Gerät mit Geschäftsdaten geht verloren.", "Verlust sofort nach Sicherheits-/Datenschutzprozess melden und Schutzmaßnahmen veranlassen"),
        ("Ein Dokument wurde versehentlich öffentlich freigegeben.", "Freigabe sofort einschränken, Reichweite prüfen und Vorfall nach Vorgabe melden"),
        ("Ein Dienstleister fordert mehr Daten als für seine Aufgabe erforderlich.", "Datenumfang auf das Erforderliche begrenzen und Berechtigung prüfen"),
        ("Eine Phishing-Mail wurde von einem Mitarbeiter geöffnet.", "IT-Sicherheitsprozess sofort auslösen und weitere Anweisungen befolgen"),
        ("Ein ausgeschiedener Mitarbeiter besitzt noch Geräte oder Zugänge.", "Rückgabe und Entzug aller Zugänge systematisch sicherstellen"),
    ]
    for i, (scenario, correct) in enumerate(expert_security, 1):
        out.append(choice(f"bo_e_sec_{i:02d}", "Büroorganisation", "Sicherheits- und Datenschutzfälle", "Experte", scenario,
                          correct, ["Vorfall nicht melden", "Daten vorsorglich an weitere Personen senden", "Nur lokal eine Notiz machen und nichts weiter tun"],
                          "Bei Sicherheits- und Datenschutzfällen zählen schnelle Begrenzung, definierte Meldewege und dokumentierte Maßnahmen.",
                          "Denke an Schadenbegrenzung, Meldung und Berechtigungen."))
    expert_process = [
        ("Ein wiederkehrender Vorgang verursacht regelmäßig Rückfragen, weil Zuständigkeiten unklar sind.", "Prozessschritte, Rollen und Übergaben eindeutig definieren und dokumentieren"),
        ("Eine Aufgabe wird häufig doppelt erledigt.", "Ursache in der Aufgabenverteilung analysieren und eine eindeutige Zuständigkeit schaffen"),
        ("Ein Monatsabschluss hängt von mehreren Bereichen ab.", "Abhängigkeiten, Termine und Verantwortliche frühzeitig in einem gemeinsamen Ablaufplan festlegen"),
        ("Ein wichtiger Prozess ist nur einer Person bekannt.", "Wissen dokumentieren und Vertretung bzw. Übergabe organisieren"),
        ("Bei Urlaubsvertretungen gehen regelmäßig Informationen verloren.", "Standardisierte Übergabe mit offenen Vorgängen, Fristen und Ansprechpartnern einführen"),
        ("Ein Formular wird häufig falsch ausgefüllt.", "Ursachen prüfen und Formular, Anleitung oder Prüfschritt gezielt verbessern"),
        ("Ein Bearbeitungsschritt ist unnötig doppelt freigegeben.", "Prozess sachlich prüfen und mit Verantwortlichen auf notwendige Kontrollen reduzieren"),
        ("Viele Vorgänge warten auf dieselbe Person.", "Engpass sichtbar machen und Kapazität, Vertretung oder Freigaberegeln prüfen"),
        ("Ein Prozess hat keine messbare Bearbeitungsfrist.", "Klare Ziel- und Kontrollgrößen definieren, sofern betrieblich sinnvoll"),
        ("Fehler werden korrigiert, aber die Ursache nie untersucht.", "Wiederkehrende Ursachen analysieren und vorbeugende Maßnahmen ableiten"),
    ]
    for i, (scenario, correct) in enumerate(expert_process, 1):
        out.append(choice(f"bo_e_proc_{i:02d}", "Büroorganisation", "Prozessorganisation", "Experte", scenario,
                          correct, ["Fehler weiterhin nur einzeln beheben", "Zuständigkeiten bewusst offenlassen", "Keine Dokumentation verwenden"],
                          "Gute Prozessorganisation beseitigt wiederkehrende Ursachen und schafft klare Rollen und Übergaben.",
                          "Suche nach einer nachhaltigen statt nur kurzfristigen Lösung."))
    expert_comm = [
        ("Ein Kunde verlangt eine sofortige Zusage, die du fachlich nicht geben darfst.", "Grenzen der eigenen Befugnis erklären, Anliegen aufnehmen und verbindlichen Rückmeldeweg nennen"),
        ("Eine interne Entscheidung wurde geändert, externe Partner sind bereits informiert worden.", "Änderung schnell, eindeutig und mit Bezug auf die vorherige Information kommunizieren"),
        ("Mehrere Empfänger benötigen unterschiedliche Teile derselben Information.", "Information zielgruppengerecht aufbereiten und nur notwendige Details weitergeben"),
        ("Ein Konflikt zwischen zwei Bereichen blockiert einen Vorgang.", "Sachverhalt, Auswirkungen und offene Entscheidungspunkte strukturiert zur Klärung bringen"),
        ("Eine Verzögerung ist absehbar, die genaue Dauer aber noch unklar.", "Frühzeitig transparent informieren und einen konkreten Termin für das nächste Statusupdate nennen"),
        ("Ein Fehler wurde intern verursacht und betrifft einen Kunden.", "Sachlich Verantwortung für die Korrektur übernehmen, ohne unbelegte Schuldzuweisungen"),
        ("Eine Übergabe an eine Vertretung erfolgt mitten in einem kritischen Vorgang.", "Status, nächste Schritte, Fristen, Risiken und Ansprechpartner vollständig übergeben"),
        ("Eine Entscheidung hängt von mehreren unklaren Angaben ab.", "Fehlende Informationen gezielt sammeln und Annahmen klar von Fakten trennen"),
        ("Ein Kunde sendet eine emotional formulierte Beschwerde.", "Sachverhalt ruhig aufnehmen, konkrete Punkte prüfen und lösungsorientiert antworten"),
        ("Ein Problem ist noch nicht gelöst, aber es gibt einen Zwischenstand.", "Zwischenstand, nächste Schritte und nächsten Rückmeldetermin klar kommunizieren"),
    ]
    for i, (scenario, correct) in enumerate(expert_comm, 1):
        out.append(choice(f"bo_e_comm_{i:02d}", "Büroorganisation", "Kommunikation und Eskalation", "Experte", scenario,
                          correct, ["Keine Rückmeldung geben, bis alles gelöst ist", "Ungeprüfte Zusagen machen", "Verantwortung ohne Prüfung anderen zuweisen"],
                          "Professionelle Kommunikation ist transparent, verbindlich und innerhalb der eigenen Befugnisse.",
                          "Trenne Fakten, Zusagen, Zuständigkeit und nächsten Schritt."))
    return out


def build_processes() -> list[Question]:
    out: list[Question] = []
    # Anfänger: 40 Grundlagen zu Belegen und Ablauf.
    docs = [
        ("Angebot", "informiert über Leistung, Preis und Bedingungen vor einer Bestellung"),
        ("Bestellung", "drückt aus, welche Ware oder Leistung der Kunde beziehen möchte"),
        ("Auftragsbestätigung", "bestätigt dem Kunden den angenommenen Auftrag und wesentliche Konditionen"),
        ("Lieferschein", "begleitet bzw. dokumentiert die gelieferte Ware"),
        ("Rechnung", "fordert die Zahlung für eine Lieferung oder Leistung"),
        ("Gutschrift", "korrigiert bzw. mindert einen Betrag zugunsten des Empfängers"),
        ("Mahnung", "erinnert an eine fällige offene Zahlung"),
        ("Reklamation", "beanstandet einen Mangel oder eine Abweichung"),
        ("Anfrage", "holt Informationen oder Konditionen ein"),
        ("Zahlungseingang", "zeigt, dass ein offener Betrag beglichen wurde"),
    ]
    for i, (doc, purpose) in enumerate(docs, 1):
        out.append(choice(f"gp_a_doc_{i:02d}", "Geschäftsprozesse", "Dokumente", "Anfänger",
                          f"Welches Dokument bzw. welcher Vorgang {purpose}?", doc,
                          [d for d, _ in docs if d != doc][:3],
                          f"„{doc}“ erfüllt im typischen Geschäftsprozess diese Funktion.",
                          "Ordne den Zweck dem passenden Dokument zu."))

    sequences = [
        ("Anfrage → Angebot → Bestellung → Auftragsbestätigung", "Welcher Ablauf ist bis zur Auftragsbestätigung typisch?"),
        ("Bestellung → Auftragsbestätigung → Lieferung → Rechnung", "Welcher Ablauf ist nach einer Bestellung typisch?"),
        ("Lieferung → Prüfung → Rechnung prüfen → Zahlung", "Welcher Ablauf passt zum Wareneingang und zur Zahlung?"),
        ("Rechnung → Fälligkeit → Zahlung → Zahlungseingang", "Welcher Ablauf beschreibt einen normalen Zahlungsvorgang?"),
        ("Mangel feststellen → dokumentieren → reklamieren → Lösung abstimmen", "Welcher Ablauf passt zu einer Reklamation?"),
        ("Anfrage → Angebote vergleichen → Lieferant auswählen → bestellen", "Welcher Ablauf passt zur Beschaffung?"),
        ("Bestellung prüfen → Auftrag bestätigen → Ware bereitstellen → liefern", "Welcher Ablauf passt zur Auftragsbearbeitung?"),
        ("Offenen Posten prüfen → Fälligkeit feststellen → Erinnerung/Mahnung → Zahlung überwachen", "Welcher Ablauf passt zu einem offenen Rechnungsbetrag?"),
        ("Ware annehmen → Lieferschein prüfen → Menge kontrollieren → Abweichung melden", "Welcher Ablauf passt zum Wareneingang?"),
        ("Angebot erstellen → versenden → Rückmeldung abwarten → Bestellung erfassen", "Welcher Ablauf passt zum Verkaufsprozess vor der Lieferung?"),
    ]
    for i, (correct, prompt) in enumerate(sequences, 1):
        out.append(choice(f"gp_a_seq_{i:02d}", "Geschäftsprozesse", "Ablauf", "Anfänger", prompt, correct,
                          ["Rechnung → Angebot → Mahnung → Bestellung", "Mahnung → Lieferung → Anfrage → Angebot", "Zahlung → Bestellung → Angebot → Rechnung"],
                          "Geschäftsprozesse folgen einer sachlogischen Reihenfolge.", "Ordne die Dokumente bzw. Schritte zeitlich."))

    products = ["10 Ordner", "6 Bürostühle", "25 Kugelschreiber", "4 Monitore", "12 Tastaturen", "8 Lampen", "30 Mappen", "5 Drucker", "16 Headsets", "20 Notizblöcke"]
    for i, product in enumerate(products, 1):
        out.append(choice(f"gp_a_lief_{i:02d}", "Geschäftsprozesse", "Wareneingang", "Anfänger",
                          f"Eine Lieferung umfasst {product}. Was sollte beim Wareneingang zuerst geprüft werden?",
                          "Ob Lieferung, Lieferschein und Bestellung hinsichtlich Artikel und Menge zusammenpassen",
                          ["Ob die Rechnung bereits gemahnt wurde", "Ob ein neues Angebot erstellt werden kann", "Ob die Ware sofort ohne Prüfung eingelagert werden kann"],
                          "Beim Wareneingang werden Artikel, Menge und erkennbare Abweichungen mit den Unterlagen abgeglichen.",
                          "Vergleiche die tatsächliche Lieferung mit Bestellung und Lieferschein."))
    invoice_cases = [
        "Auf der Rechnung fehlt die Rechnungsnummer", "Der Rechnungsbetrag weicht vom Angebot ab", "Die berechnete Menge ist höher als geliefert",
        "Ein vereinbarter Rabatt fehlt", "Die Zahlungsfrist ist unklar", "Der Artikelpreis weicht von der Bestellung ab",
        "Die Rechnung gehört zu einem anderen Auftrag", "Eine bereits gutgeschriebene Position steht erneut auf der Rechnung",
        "Der Name des Unternehmens ist falsch", "Die Rechnung ist doppelt eingegangen",
    ]
    for i, issue in enumerate(invoice_cases, 1):
        out.append(choice(f"gp_a_inv_{i:02d}", "Geschäftsprozesse", "Rechnungsprüfung", "Anfänger",
                          f"{issue}. Wie sollte man reagieren?", "Rechnung bzw. Vorgang prüfen und die Abweichung vor der Zahlung klären",
                          ["Ungeprüft bezahlen", "Rechnung sofort löschen", "Den Betrag eigenmächtig ändern und überweisen"],
                          "Unklare oder fehlerhafte Rechnungen werden vor der Zahlung geprüft und geklärt.",
                          "Nicht ungeprüft zahlen, wenn eine Abweichung erkennbar ist."))

    # Fortgeschritten: 40 praxisnahe Fälle.
    items = ["Stühle", "Ordner", "Monitore", "Tastaturen", "Leuchten", "Headsets", "Druckerpatronen", "Mappen", "Kabel", "Notizbücher"]
    for i, item in enumerate(items, 1):
        ordered = 20 + i
        delivered = ordered - (1 + i % 3)
        out.append(choice(f"gp_f_qty_{i:02d}", "Geschäftsprozesse", "Mengenabweichung", "Fortgeschritten",
                          f"Bestellt wurden {ordered} {item}, geliefert wurden {delivered}, die Rechnung enthält {ordered}. Was ist kaufmännisch sinnvoll?",
                          "Abweichung dokumentieren, Unterlagen abgleichen und mit dem Lieferanten Korrektur bzw. Nachlieferung klären",
                          ["Volle Rechnung ungeprüft zahlen", "Fehlmenge ignorieren", "Rechnung eigenmächtig auf einen beliebigen Betrag kürzen"],
                          "Bestellung, Lieferung und Rechnung müssen übereinstimmen; Abweichungen werden dokumentiert und abgestimmt.",
                          "Prüfe Menge, Beleglage und notwendigen Korrekturweg."))
    defects = ["3 Artikel zerkratzt", "2 Artikel beschädigt", "4 Artikel funktionslos", "1 Artikel im falschen Modell", "5 Artikel in der falschen Farbe", "2 Artikel unvollständig", "3 Artikel stark verschmutzt", "1 Artikel gebrochen", "2 Artikel falsch beschriftet", "4 Artikel mit sichtbaren Transportschäden"]
    for i, defect in enumerate(defects, 1):
        out.append(choice(f"gp_f_qual_{i:02d}", "Geschäftsprozesse", "Qualitätsabweichung", "Fortgeschritten",
                          f"Bei einer Lieferung sind {defect}. Was sollte als Nächstes geschehen?",
                          "Mangel nachvollziehbar dokumentieren und mit dem Lieferanten Ersatz, Nachbesserung oder weitere Vorgehensweise abstimmen",
                          ["Mangel ohne Dokumentation beseitigen", "Alles ungeprüft akzeptieren", "Ohne Rücksprache die gesamte Geschäftsbeziehung beenden"],
                          "Qualitätsmängel sollten dokumentiert und sachlich mit dem Lieferanten geklärt werden.",
                          "Sichere Nachweise und kläre die gewünschte Lösung."))
    payment_cases = [
        ("2% Skonto bei Zahlung innerhalb von 10 Tagen", "Zahlungsfrist und Skontofrist prüfen und rechtzeitig zur Zahlung freigeben"),
        ("Zahlungsziel 30 Tage netto", "Fälligkeit korrekt erfassen und Zahlung zum vereinbarten Termin einplanen"),
        ("Rechnung vor Lieferung eingegangen", "Prüfen, ob Vorauszahlung vereinbart ist, bevor gezahlt wird"),
        ("Gutschrift angekündigt, aber noch nicht verbucht", "Gutschrift bzw. korrigierten Saldo klären, bevor der offene Betrag abschließend bezahlt wird"),
        ("Teilzahlung bereits geleistet", "Offenen Restbetrag anhand der Buchungen und Rechnung ermitteln"),
        ("Doppelte Rechnung mit gleicher Nummer", "Doppelten Eingang prüfen und eine doppelte Zahlung verhindern"),
        ("Mahnung trotz bereits gezahlter Rechnung", "Zahlung belegen und Vorgang mit dem Lieferanten klären"),
        ("Rechnung enthält falsche Bankverbindung im Vergleich zu bekannten Stammdaten", "Änderung über einen verlässlichen Kanal prüfen, bevor gezahlt wird"),
        ("Fälligkeit fällt auf einen Feiertag", "Betriebliche Zahlungsplanung und Banklaufzeiten rechtzeitig berücksichtigen"),
        ("Rechnung ohne Bestellbezug", "Vorgang und Berechtigung zur Leistung bzw. Bestellung klären"),
    ]
    for i, (case, correct) in enumerate(payment_cases, 1):
        out.append(choice(f"gp_f_pay_{i:02d}", "Geschäftsprozesse", "Zahlungsabwicklung", "Fortgeschritten",
                          f"Situation: {case}. Was ist sinnvoll?", correct,
                          ["Immer sofort zahlen", "Vorgang ohne Prüfung schließen", "Zahlungsdaten eigenmächtig ändern"],
                          "Zahlungsabwicklung benötigt eindeutige Belege, Fälligkeiten und Freigaben.",
                          "Prüfe Beleg, Frist, bereits erfolgte Buchungen und Freigabe."))
    procurement_cases = [
        ("Anbieter A ist günstiger, Anbieter B liefert deutlich früher.", "Neben Preis auch Lieferzeit und Bedarfstermin bewerten"),
        ("Ein Angebot enthält niedrigeren Preis, aber hohe Versandkosten.", "Gesamtkosten statt nur Einzelpreis vergleichen"),
        ("Ein Lieferant bietet 3% Skonto, ein anderer längeres Zahlungsziel.", "Konditionen auf die eigene Liquiditäts- und Zahlungsplanung beziehen"),
        ("Ein Anbieter erfüllt eine zwingende technische Anforderung nicht.", "Nicht nur den Preis betrachten; Muss-Anforderungen müssen erfüllt sein"),
        ("Ein Lieferant hat wiederholt verspätet geliefert.", "Zuverlässigkeit als Bewertungskriterium berücksichtigen"),
        ("Ein Angebot ist nur bis morgen gültig, intern fehlt die Freigabe.", "Freigabe rechtzeitig einholen oder Frist mit Anbieter klären"),
        ("Mehrere Angebote verwenden unterschiedliche Mengeneinheiten.", "Angebote auf eine vergleichbare Basis umrechnen"),
        ("Ein Anbieter nennt Nettopreise, ein anderer Bruttopreise.", "Preise auf dieselbe Vergleichsbasis bringen"),
        ("Ein Angebot enthält optionale Zusatzleistungen.", "Nur vergleichbare Leistungsumfänge gegenüberstellen"),
        ("Der billigste Anbieter hat sehr hohe Mindestabnahmemengen.", "Bedarf, Lagerkosten und Mindestmenge gemeinsam bewerten"),
    ]
    for i, (case, correct) in enumerate(procurement_cases, 1):
        out.append(choice(f"gp_f_proc_{i:02d}", "Geschäftsprozesse", "Angebotsvergleich", "Fortgeschritten",
                          case, correct,
                          ["Immer nur den niedrigsten Einzelpreis wählen", "Angebote ohne Vergleich zufällig auswählen", "Nur das Layout des Angebots bewerten"],
                          "Ein Angebotsvergleich berücksichtigt Preis, Leistung, Konditionen, Termine und Anforderungen.",
                          "Vergleiche auf derselben sachlichen Basis."))

    # Experte: 40 kombinierte Geschäftsfälle.
    expert_delivery = [
        (12, 10, 2, "vereinbarter Rabatt fehlt"), (20, 18, 1, "falscher Einzelpreis"), (15, 14, 3, "zwei Artikel beschädigt"),
        (30, 27, 2, "Frachtkosten doppelt berechnet"), (8, 7, 1, "falsches Modell geliefert"), (25, 22, 4, "Skontoangabe fehlt"),
        (16, 15, 2, "eine Position nicht bestellt"), (40, 38, 5, "mehrere Artikel beschädigt"), (10, 9, 1, "Rechnung enthält 10 Stück"),
        (24, 20, 2, "Liefertermin deutlich überschritten"),
    ]
    for i, (ordered, delivered, bad, extra) in enumerate(expert_delivery, 1):
        out.append(choice(f"gp_e_case_{i:02d}", "Geschäftsprozesse", "Komplexe Rechnungs- und Lieferprüfung", "Experte",
                          f"Bestellt: {ordered} Stück. Geliefert: {delivered}. Zusätzlich: {bad} Stück mit Mangel; {extra}. Wie gehst du strukturiert vor?",
                          "Alle Abweichungen getrennt dokumentieren, Bestellung/Lieferschein/Rechnung abgleichen, Auswirkungen auf Zahlung klären und mit dem Lieferanten eine abgestimmte Korrektur vereinbaren",
                          ["Nur einen der Fehler beachten", "Rechnung vollständig zahlen und später nichts mehr tun", "Gesamte Lieferung ohne Prüfung vernichten"],
                          "Komplexe Fälle erfordern die getrennte Erfassung von Mengen-, Qualitäts- und Rechnungsabweichungen.",
                          "Liste zuerst jede Abweichung auf und ordne sie Beleg, Ware oder Kondition zu."))
    supplier_cases = [
        ("wiederholte Lieferverzögerungen", "Ursachen und Auswirkungen dokumentieren, Leistungsgespräch führen und gegebenenfalls Alternativen bzw. Maßnahmen prüfen"),
        ("häufige Mengenfehler", "Fehlerdaten sammeln, Prozess mit Lieferant klären und Verbesserungsmaßnahme vereinbaren"),
        ("stark schwankende Preise", "Preisbedingungen, Marktvergleich und Vertrags-/Alternativangebote prüfen"),
        ("mehrere Qualitätsmängel", "Mängel systematisch erfassen, Ursachen- und Korrekturmaßnahmen mit Lieferant abstimmen"),
        ("unklare Ansprechpartner", "Verbindliche Kommunikations- und Eskalationskontakte festlegen"),
        ("wiederholte Rechnungsfehler", "Belegfehler kategorisieren und mit Lieferant einen sauberen Rechnungsprozess vereinbaren"),
        ("fehlende Auftragsbestätigungen", "Bestätigungsprozess und Fristen mit Lieferant verbindlich abstimmen"),
        ("unzuverlässige Statusmeldungen", "Verbindliche Statuspunkte bzw. Eskalationswege definieren"),
        ("abweichende Zahlungsbedingungen", "Vertragliche Konditionen und Stammdaten abgleichen und verbindlich korrigieren"),
        ("häufige Teillieferungen ohne Abstimmung", "Bedarf, Kosten und Liefervereinbarung prüfen und künftige Teillieferungen regeln"),
    ]
    for i, (problem, correct) in enumerate(supplier_cases, 1):
        out.append(choice(f"gp_e_sup_{i:02d}", "Geschäftsprozesse", "Lieferantenmanagement", "Experte",
                          f"Bei einem Lieferanten treten {problem} auf. Welche Reaktion ist nachhaltig?", correct,
                          ["Jeden Fall isoliert behandeln und keine Ursachen erfassen", "Probleme ignorieren, solange überhaupt geliefert wird", "Sofort ohne Prüfung alle Bestellungen stornieren"],
                          "Nachhaltiges Lieferantenmanagement verbindet Daten, Ursachen, Vereinbarungen und Alternativen.",
                          "Suche eine Maßnahme, die Wiederholungen reduziert."))
    workflow_cases = [
        ("Ein Auftrag ist bestätigt, aber die Ware ist nicht verfügbar.", "Verfügbarkeit und Alternativen klären, Kunden transparent informieren und neue Zusage abstimmen"),
        ("Ein Kunde ändert nach Auftragsbestätigung die Menge.", "Änderung prüfen, Auswirkungen auf Preis/Liefertermin abstimmen und Auftrag dokumentiert anpassen"),
        ("Eine Rechnung wurde freigegeben, danach wird ein Liefermangel entdeckt.", "Zahlungsstatus prüfen, Vorgang sperren bzw. Korrekturweg einleiten und Lieferant kontaktieren"),
        ("Ein Angebot wurde angenommen, aber die Konditionen im Auftrag weichen ab.", "Abweichung vor weiterer Bearbeitung klären und dokumentieren"),
        ("Eine Mahnung trifft ein, intern ist eine Reklamation offen.", "Reklamations- und Zahlungsstatus zusammenführen und mit Lieferant klären"),
        ("Ein Auftrag hängt von einer Kundenfreigabe ab, die aussteht.", "Freigabe aktiv nachverfolgen und keine unzulässigen Folgeschritte auslösen"),
        ("Eine Teillieferung ist erlaubt, aber der Kunde benötigt eine Mindestmenge.", "Liefermengen und Bedarf abstimmen und Kunden über realistischen Plan informieren"),
        ("Ein Preis ändert sich zwischen Angebot und Bestellung.", "Gültigkeit und Konditionen prüfen, bevor der Auftrag bestätigt wird"),
        ("Ein Kunde reklamiert nach Zahlung einen Mangel.", "Mangel unabhängig vom Zahlungsstatus sachlich prüfen und Korrekturprozess starten"),
        ("Eine Ersatzlieferung wird zugesagt, ist aber nicht terminiert.", "Verbindlichen Termin nachfassen und Kunden/Prozessstatus aktualisieren"),
    ]
    for i, (case, correct) in enumerate(workflow_cases, 1):
        out.append(choice(f"gp_e_flow_{i:02d}", "Geschäftsprozesse", "Prozesssteuerung", "Experte", case, correct,
                          ["Vorgang ohne Klärung weiterlaufen lassen", "Nur einen Beleg betrachten und Zusammenhänge ignorieren", "Keine Beteiligten informieren"],
                          "Prozesssteuerung verbindet Belege, Zusagen, Abhängigkeiten und Kommunikation.",
                          "Prüfe, welcher Folgeschritt von welcher Freigabe oder Klärung abhängt."))
    control_cases = [
        ("Ein Rabatt steht im Angebot, fehlt aber in der Auftragsbestätigung.", "Abweichung vor Lieferung klären und vereinbarte Kondition dokumentieren"),
        ("Die Bestellnummer auf der Rechnung ist falsch, alle übrigen Daten passen.", "Zuordnung verlässlich prüfen und formale Korrektur nach betrieblicher Vorgabe veranlassen"),
        ("Ein Lieferant ändert seine Bankverbindung per unerwarteter E-Mail.", "Änderung über bekannten, verlässlichen Kontaktweg verifizieren"),
        ("Eine Rechnung enthält zusätzliche nicht bestellte Leistungen.", "Leistungs-/Bestellgrundlage prüfen und unklare Positionen reklamieren"),
        ("Eine Gutschrift wird angekündigt, aber eine Mahnung läuft weiter.", "Beide Vorgänge zusammenführen und Saldo mit Lieferant klären"),
        ("Eine Zahlung wurde zweimal ausgelöst.", "Doppelzahlung dokumentieren, Rückforderung/Klärung veranlassen und Ursache im Prozess prüfen"),
        ("Ein Auftrag wurde versehentlich doppelt angelegt.", "Doppelten Vorgang stoppen, Auswirkungen prüfen und Daten konsolidieren"),
        ("Die Rechnung passt zur Bestellung, aber nicht zur tatsächlichen Lieferung.", "Tatsächliche Leistung/Lieferung als weiteren Prüfpunkt einbeziehen und Abweichung klären"),
        ("Eine Lieferfrist ist überschritten, der Kunde wurde noch nicht informiert.", "Status beschaffen, Auswirkungen bewerten und Kunden proaktiv informieren"),
        ("Eine Korrekturrechnung enthält erneut einen Fehler.", "Erneut sachlich prüfen, Fehler genau benennen und eine belastbare Korrektur anfordern"),
    ]
    for i, (case, correct) in enumerate(control_cases, 1):
        out.append(choice(f"gp_e_ctrl_{i:02d}", "Geschäftsprozesse", "Kontrolle und Risikovermeidung", "Experte", case, correct,
                          ["Ungeprüft fortfahren", "Nur die schnellste Lösung wählen, unabhängig von Belegen", "Abweichung nicht dokumentieren"],
                          "Kontrollpunkte verhindern Zahlungs-, Liefer- und Zuordnungsfehler.",
                          "Prüfe Belege, tatsächlichen Vorgang und mögliche Folgerisiken."))
    return out


def build_correspondence() -> list[Question]:
    out: list[Question] = []
    # Anfänger: 40 einfache Geschäftsschreibfragen.
    subjects = [
        ("Angebot für 20 Bürostühle", "Angebot"), ("Reklamation zur Lieferung 4711", "Reklamation"),
        ("Terminbestätigung für den 12. Oktober", "Termin"), ("Rückfrage zur Rechnung 8392", "Rechnung"),
        ("Bestellung Nr. 22018", "Bestellung"), ("Fehlende Unterlagen zum Vorgang 715", "Unterlagen"),
        ("Bitte um Liefertermin für Auftrag 641", "Liefertermin"), ("Zahlungserinnerung zu Rechnung 1884", "Zahlung"),
        ("Änderung des Besprechungstermins", "Terminänderung"), ("Bestätigung Ihrer Reklamation vom 4. September", "Reklamationsbestätigung"),
    ]
    for i, (correct, topic) in enumerate(subjects, 1):
        out.append(choice(f"sv_a_bet_{i:02d}", "Schriftverkehr", "Betreff", "Anfänger",
                          f"Welcher Betreff ist für das Thema „{topic}“ am geeignetsten?", correct,
                          ["Hallo", "Wichtig!!!", "Kurze Frage"],
                          "Ein Betreff sollte Anlass und möglichst eine eindeutige Referenz nennen.",
                          "Der Empfänger soll den Vorgang sofort erkennen."))
    salutations = [
        ("Sehr geehrte Frau Meyer,", "Name der Ansprechpartnerin ist bekannt"),
        ("Sehr geehrter Herr Becker,", "Name des Ansprechpartners ist bekannt"),
        ("Guten Tag Frau Schulz,", "moderne geschäftliche E-Mail bei bekanntem Namen"),
        ("Guten Tag Herr Wagner,", "moderne geschäftliche E-Mail bei bekanntem Namen"),
        ("Sehr geehrte Damen und Herren,", "keine konkrete Ansprechperson ist bekannt"),
        ("Mit freundlichen Grüßen", "neutraler formeller Schluss"),
        ("Freundliche Grüße", "knapper geschäftlicher Schluss"),
        ("Viele Grüße", "etwas weniger formeller, aber üblicher Schluss in passender Geschäftsbeziehung"),
        ("Vielen Dank für Ihre Rückmeldung.", "höflicher Abschlusssatz"),
        ("Für Rückfragen stehen wir Ihnen gern zur Verfügung.", "Angebot für Rückfragen"),
    ]
    for i, (correct, case) in enumerate(salutations, 1):
        out.append(choice(f"sv_a_anr_{i:02d}", "Schriftverkehr", "Anrede und Abschluss", "Anfänger",
                          f"Welche Formulierung passt zu: {case}?", correct,
                          ["Hey Leute", "Na dann", "Mfg!!!"],
                          "Anrede und Abschluss sollten zur geschäftlichen Situation und zum Bekanntheitsgrad passen.",
                          "Wähle eine höfliche, vollständige Formulierung."))
    clear_requests = [
        "Bitte senden Sie uns die fehlenden Unterlagen bis Freitag zu.", "Bitte bestätigen Sie den Termin bis morgen um 12 Uhr.",
        "Bitte teilen Sie uns die aktuelle Lieferzeit mit.", "Bitte prüfen Sie die Rechnung und senden Sie uns eine korrigierte Fassung.",
        "Bitte nennen Sie uns Ihre Ansprechpartnerin für diesen Vorgang.", "Bitte senden Sie die Auftragsbestätigung an diese E-Mail-Adresse.",
        "Bitte bestätigen Sie den Eingang unserer Bestellung.", "Bitte teilen Sie uns mit, ob eine Teillieferung möglich ist.",
        "Bitte senden Sie uns ein Angebot für 25 Stück.", "Bitte informieren Sie uns, sobald die Ware versendet wurde.",
    ]
    for i, correct in enumerate(clear_requests, 1):
        out.append(choice(f"sv_a_req_{i:02d}", "Schriftverkehr", "Klare Formulierung", "Anfänger",
                          "Welche Formulierung ist für eine geschäftliche E-Mail am klarsten?", correct,
                          ["Schicken Sie das mal rüber.", "Melden Sie sich irgendwann dazu.", "Kümmern Sie sich bitte irgendwie darum."],
                          "Klare Geschäftskommunikation nennt Handlung, Gegenstand und gegebenenfalls Termin.",
                          "Achte darauf, dass der Empfänger genau weiß, was zu tun ist."))
    email_basics = [
        ("Vor dem Senden einer E-Mail", "Empfänger, Betreff, Inhalt und Anhänge noch einmal prüfen"),
        ("Bei einem Anhang", "im Text kurz auf den Anhang hinweisen und richtige Datei auswählen"),
        ("Bei mehreren unbekannten externen Empfängern", "Datenschutz und geeignete Empfängerfelder beachten"),
        ("Bei einer Terminänderung", "neuen Termin eindeutig nennen und betroffene Personen informieren"),
        ("Bei einer Reklamation", "sachlich beschreiben, was abweicht, und gewünschte Klärung nennen"),
        ("Bei einer Rückfrage", "Vorgangsnummer oder andere Referenz angeben"),
        ("Bei einer Frist", "ein konkretes Datum oder eindeutig bestimmbaren Termin nennen"),
        ("Bei einer längeren E-Mail", "Inhalt sinnvoll gliedern und Kernaussage sichtbar machen"),
        ("Bei einer Antwort", "prüfen, welche Empfänger die Antwort tatsächlich benötigen"),
        ("Bei vertraulichen Daten", "nur freigegebene und sichere Übertragungswege nutzen"),
    ]
    for i, (case, correct) in enumerate(email_basics, 1):
        out.append(choice(f"sv_a_mail_{i:02d}", "Schriftverkehr", "E-Mail-Grundlagen", "Anfänger", case, correct,
                          ["Ohne Betreff senden", "Möglichst viele Personen in Kopie setzen", "Anhänge und Empfänger nicht prüfen"],
                          "Geschäftliche E-Mails sollen korrekt zugeordnet, vollständig und datenschutzgerecht versendet werden.",
                          "Prüfe vor allem Empfänger, Betreff, Inhalt und Anhänge."))

    # Fortgeschritten: 40 konkrete Schreiben.
    complaints = [
        ("2 von 12 Stühlen fehlen", "Bei der Prüfung der Lieferung haben wir festgestellt, dass zwei der zwölf bestellten Stühle fehlen."),
        ("3 Ordner sind beschädigt", "Bei der Wareneingangskontrolle haben wir festgestellt, dass drei Ordner beschädigt sind."),
        ("falsches Modell geliefert", "Die gelieferte Ausführung entspricht nicht dem von uns bestellten Modell."),
        ("Rechnung enthält falsche Menge", "Die in Rechnung gestellte Menge weicht von der tatsächlich gelieferten Menge ab."),
        ("vereinbarter Rabatt fehlt", "Der vereinbarte Rabatt wurde in der vorliegenden Rechnung nicht berücksichtigt."),
        ("Liefertermin überschritten", "Der bestätigte Liefertermin ist verstrichen, die Ware ist bislang nicht eingetroffen."),
        ("Artikelpreis weicht ab", "Der berechnete Einzelpreis weicht von dem in der Bestellung vereinbarten Preis ab."),
        ("Teillieferung nicht angekündigt", "Die Lieferung ist unvollständig eingetroffen; eine Teillieferung war nicht angekündigt."),
        ("Ware weist Transportschaden auf", "Mehrere Artikel weisen bei Anlieferung erkennbare Transportschäden auf."),
        ("doppelte Rechnung", "Die Rechnung scheint für denselben Vorgang doppelt ausgestellt worden zu sein."),
    ]
    for i, (case, correct) in enumerate(complaints, 1):
        out.append(choice(f"sv_f_rek_{i:02d}", "Schriftverkehr", "Reklamation", "Fortgeschritten",
                          f"Welche Formulierung beschreibt den Mangel „{case}“ sachlich?", correct,
                          ["Das ist schon wieder eine Frechheit.", "Sie machen dauernd alles falsch.", "Kümmern Sie sich sofort um Ihren Mist."],
                          "Eine Reklamation beschreibt die konkrete Abweichung neutral und nachvollziehbar.",
                          "Keine Schuldzuweisung, sondern Fakten nennen."))
    deadlines = [
        "Bitte senden Sie uns die korrigierte Rechnung bis spätestens 25. September zu.", "Bitte bestätigen Sie den Liefertermin bis Freitag, 12:00 Uhr.",
        "Bitte reichen Sie die fehlenden Unterlagen bis zum 30. September nach.", "Bitte teilen Sie uns bis morgen mit, ob der vorgeschlagene Termin möglich ist.",
        "Bitte übermitteln Sie uns Ihr aktualisiertes Angebot bis zum 5. Oktober.", "Bitte senden Sie die Auftragsbestätigung innerhalb der nächsten zwei Werktage.",
        "Bitte geben Sie uns bis Mittwoch eine Rückmeldung zum Bearbeitungsstand.", "Bitte bestätigen Sie bis zum 10. Oktober, wann die Ersatzlieferung erfolgt.",
        "Bitte begleichen Sie den offenen Betrag bis spätestens 15. Oktober.", "Bitte teilen Sie uns bis Ende dieser Woche Ihre Entscheidung mit.",
    ]
    for i, correct in enumerate(deadlines, 1):
        out.append(choice(f"sv_f_frist_{i:02d}", "Schriftverkehr", "Fristsetzung", "Fortgeschritten",
                          "Welche Formulierung enthält eine klare Frist?", correct,
                          ["Bitte möglichst bald erledigen.", "Melden Sie sich irgendwann.", "Das brauchen wir sofort!!!"],
                          "Konkrete Daten oder eindeutig bestimmbare Zeiträume machen Fristen nachvollziehbar.",
                          "Vermeide unbestimmte Begriffe wie „bald“."))
    inquiries = [
        ("Lieferzeit", "Bitte teilen Sie uns mit, mit welcher Lieferzeit wir derzeit rechnen können."),
        ("Mindestbestellmenge", "Bitte nennen Sie uns die für diesen Artikel geltende Mindestbestellmenge."),
        ("Rabattstaffel", "Bitte informieren Sie uns über mögliche Mengenrabatte für 50, 100 und 200 Stück."),
        ("Versandkosten", "Bitte teilen Sie uns die Versandkosten für die angefragte Menge mit."),
        ("Zahlungsbedingungen", "Bitte nennen Sie uns Ihre aktuellen Zahlungsbedingungen für Geschäftskunden."),
        ("Produktalternative", "Bitte schlagen Sie uns eine lieferbare Alternative mit vergleichbaren Eigenschaften vor."),
        ("Terminverfügbarkeit", "Bitte teilen Sie uns mit, welcher der vorgeschlagenen Termine für Sie möglich ist."),
        ("Bearbeitungsstand", "Bitte informieren Sie uns kurz über den aktuellen Bearbeitungsstand des Vorgangs."),
        ("Ansprechpartner", "Bitte nennen Sie uns die zuständige Ansprechperson für die weitere Abstimmung."),
        ("Gültigkeit des Angebots", "Bitte bestätigen Sie uns, bis zu welchem Datum Ihr Angebot gültig ist."),
    ]
    for i, (case, correct) in enumerate(inquiries, 1):
        out.append(choice(f"sv_f_anfr_{i:02d}", "Schriftverkehr", "Anfrage", "Fortgeschritten",
                          f"Welche Formulierung eignet sich für eine Anfrage zum Thema „{case}“?", correct,
                          ["Wie sieht's damit aus?", "Sagen Sie mal Bescheid.", "Brauche Info, danke."],
                          "Eine gute Anfrage nennt genau, welche Information benötigt wird.",
                          "Formuliere konkret und höflich."))
    reminders = [
        ("erste freundliche Zahlungserinnerung", "Bei der Durchsicht unserer offenen Posten haben wir festgestellt, dass die Rechnung 4711 noch offen ist."),
        ("Hinweis auf Fälligkeit", "Der Rechnungsbetrag war am 15. September fällig und ist nach unserem Stand noch nicht eingegangen."),
        ("mögliche Überschneidung", "Sollte sich Ihre Zahlung mit dieser Nachricht überschnitten haben, betrachten Sie diese bitte als gegenstandslos."),
        ("Bitte um Prüfung", "Bitte prüfen Sie den offenen Betrag und geben Sie uns kurz Rückmeldung."),
        ("klare Zahlungsfrist", "Wir bitten Sie, den offenen Betrag bis spätestens 30. September zu überweisen."),
        ("Rückfrage bei Unstimmigkeit", "Sollten Sie Einwände gegen die Rechnung haben, teilen Sie uns diese bitte mit."),
        ("freundlicher Ton", "Vielen Dank für Ihre Unterstützung bei der Klärung des offenen Vorgangs."),
        ("Referenz", "Bitte geben Sie bei der Zahlung die Rechnungsnummer 8821 als Verwendungszweck an."),
        ("Kontaktangebot", "Für Rückfragen zur Rechnung steht Ihnen unsere Buchhaltung gern zur Verfügung."),
        ("Statusnachfrage", "Bitte teilen Sie uns mit, wann wir mit dem Zahlungseingang rechnen können."),
    ]
    for i, (case, correct) in enumerate(reminders, 1):
        out.append(choice(f"sv_f_zahl_{i:02d}", "Schriftverkehr", "Zahlungserinnerung", "Fortgeschritten",
                          f"Welche Formulierung passt zu „{case}“?", correct,
                          ["Zahlen Sie endlich!", "Was ist mit unserem Geld?", "Sofort überweisen!!!"],
                          "Auch bei offenen Forderungen bleibt die Kommunikation sachlich und eindeutig.",
                          "Nenne Rechnung, Fälligkeit und gewünschte nächste Handlung."))

    # Experte: 40 anspruchsvolle Formulierungsentscheidungen.
    expert_tone = [
        ("Ein Kunde ist verärgert, der Sachverhalt ist noch nicht vollständig geklärt.", "Wir verstehen, dass die Situation ärgerlich ist. Wir prüfen den Vorgang derzeit und melden uns spätestens morgen mit einem konkreten Zwischenstand."),
        ("Ein Lieferant weist die Reklamation zunächst zurück.", "Vielen Dank für Ihre Rückmeldung. Nach unseren Unterlagen besteht die Abweichung weiterhin; die entsprechenden Nachweise haben wir beigefügt. Bitte prüfen Sie den Vorgang erneut."),
        ("Eine zugesagte Frist kann nicht eingehalten werden.", "Wir können den ursprünglich zugesagten Termin leider nicht einhalten. Nach aktuellem Stand ist die Fertigstellung bis zum 8. Oktober möglich."),
        ("Ein interner Fehler hat zu einer falschen Rechnung geführt.", "Wir haben den Fehler geprüft und senden Ihnen im Anhang die korrigierte Rechnung. Für die entstandenen Umstände bitten wir um Entschuldigung."),
        ("Der Kunde fordert eine Zusage, die noch nicht freigegeben ist.", "Eine verbindliche Zusage können wir Ihnen derzeit noch nicht geben. Wir klären die Freigabe und melden uns bis 15 Uhr bei Ihnen."),
        ("Mehrere Punkte einer Reklamation sind berechtigt, einer nicht.", "Die Punkte 1 und 2 können wir bestätigen und korrigieren. Zu Punkt 3 ergibt unsere Prüfung derzeit keine Abweichung; die Grundlage dafür erläutern wir nachfolgend."),
        ("Eine Preisänderung muss erklärt werden.", "Der neue Preis gilt ab dem 1. November und beruht auf der aktualisierten Konditionsvereinbarung. Bereits bestätigte Aufträge bleiben davon unberührt."),
        ("Eine Rückmeldung verzögert sich wegen fehlender Information eines Dritten.", "Für die abschließende Klärung fehlt uns noch die Rückmeldung unseres Logistikpartners. Wir melden uns spätestens am Freitag erneut, auch wenn bis dahin noch kein Endergebnis vorliegt."),
        ("Ein Kunde hat eine Rechnung bereits gezahlt, erhält aber eine Mahnung.", "Bitte entschuldigen Sie die Überschneidung. Wir prüfen den Zahlungseingang umgehend und setzen die Mahnbearbeitung bis zur Klärung aus."),
        ("Ein Vorgang muss an eine andere Stelle übergeben werden.", "Für die weitere Bearbeitung ist unser Team Einkauf zuständig. Wir haben den Vorgang einschließlich der bisherigen Korrespondenz dorthin übergeben."),
    ]
    for i, (case, correct) in enumerate(expert_tone, 1):
        out.append(choice(f"sv_e_ton_{i:02d}", "Schriftverkehr", "Professioneller Ton", "Experte", case, correct,
                          ["Das ist nicht unser Problem.", "Warten Sie einfach ab.", "Sie liegen damit falsch und müssen das akzeptieren."],
                          "Professioneller Schriftverkehr trennt Emotionen von Fakten und nennt einen belastbaren nächsten Schritt.",
                          "Achte auf Sachlichkeit, Transparenz und Verbindlichkeit."))
    expert_complaint = [
        ("Menge und Preis sind falsch", "Bei der Prüfung der Rechnung haben wir zwei Abweichungen festgestellt: Die berechnete Menge beträgt 20 statt der gelieferten 18 Stück; außerdem weicht der Einzelpreis vom bestätigten Auftrag ab."),
        ("Teillieferung und beschädigte Ware", "Die Lieferung ist unvollständig eingetroffen; zusätzlich weisen zwei der gelieferten Artikel sichtbare Beschädigungen auf."),
        ("Lieferverzug gefährdet Kundentermin", "Der bestätigte Liefertermin ist überschritten. Da die Ware für einen bereits zugesagten Kundentermin benötigt wird, bitten wir um eine verbindliche Terminangabe."),
        ("Rabatt und Skonto fehlen", "In der Rechnung wurden weder der vereinbarte Rabatt noch die bestätigte Skontokondition berücksichtigt."),
        ("Ersatzlieferung erneut fehlerhaft", "Auch die Ersatzlieferung weist eine Abweichung auf: Statt des bestätigten Modells wurde erneut eine andere Ausführung geliefert."),
        ("Doppelte Berechnung von Fracht", "Die Frachtkosten wurden nach unserer Prüfung zweimal berechnet. Bitte prüfen und korrigieren Sie die entsprechende Position."),
        ("Gutschrift fehlt", "Die angekündigte Gutschrift ist in unserem Kontoauszug bzw. der aktuellen Saldenaufstellung noch nicht berücksichtigt."),
        ("falscher Rechnungsempfänger", "Die Rechnung ist an eine unzutreffende Firmierung adressiert. Bitte stellen Sie eine korrigierte Fassung mit den hinterlegten Rechnungsdaten aus."),
        ("nicht bestellte Position", "Die Rechnung enthält eine zusätzliche Position, die weder in unserer Bestellung noch in der Auftragsbestätigung enthalten ist."),
        ("abweichende Zahlungsbedingungen", "Die auf der Rechnung genannten Zahlungsbedingungen weichen von den in der Auftragsbestätigung vereinbarten Konditionen ab."),
    ]
    for i, (case, correct) in enumerate(expert_complaint, 1):
        out.append(choice(f"sv_e_rek_{i:02d}", "Schriftverkehr", "Komplexe Reklamation", "Experte",
                          f"Welche Formulierung beschreibt den Fall „{case}“ präzise?", correct,
                          ["Da stimmt einiges nicht.", "Ihre Rechnung ist komplett falsch.", "Korrigieren Sie das alles sofort!!!"],
                          "Mehrere Abweichungen werden konkret und getrennt benannt.",
                          "Benenne Fakten, Belegbezug und gewünschte Klärung."))
    expert_sensitive = [
        ("Keine verbindliche Lieferzusage möglich", "Nach aktuellem Stand können wir noch keinen verbindlichen Liefertermin nennen. Wir melden uns bis Mittwoch mit einer aktualisierten Einschätzung."),
        ("Kulanzanfrage ohne Zusage", "Wir prüfen derzeit, ob in diesem Fall eine Kulanzlösung möglich ist, und melden uns nach interner Abstimmung bei Ihnen."),
        ("Unklare Verantwortlichkeit", "Wir prüfen derzeit die interne Zuständigkeit und stellen sicher, dass der Vorgang an die richtige Stelle übergeben wird."),
        ("Möglicher Fehler, noch ungeklärt", "Die von Ihnen geschilderte Abweichung ist nachvollziehbar. Wir prüfen derzeit, an welcher Stelle sie entstanden ist."),
        ("Vertrauliche Unterlagen", "Bitte übermitteln Sie die angeforderten personenbezogenen Unterlagen ausschließlich über den vorgesehenen sicheren Übertragungsweg."),
        ("Ablehnung einer unberechtigten Forderung", "Nach Prüfung der vorliegenden Unterlagen können wir die geltend gemachte Forderung derzeit nicht nachvollziehen. Gern prüfen wir ergänzende Nachweise."),
        ("Termin muss neu abgestimmt werden", "Der bisherige Termin kann leider nicht stattfinden. Bitte teilen Sie uns mit, welcher der folgenden Ersatztermine für Sie passt."),
        ("Interne Freigabe fehlt", "Die gewünschte Änderung befindet sich noch in der internen Freigabe. Wir informieren Sie unmittelbar nach Abschluss der Prüfung."),
        ("Fehlerhafte Stammdaten", "Wir haben die Stammdaten korrigiert. Bitte prüfen Sie, ob die beigefügte Fassung nun Ihren Angaben entspricht."),
        ("Beschwerde wird eskaliert", "Wir haben den Vorgang aufgrund der geschilderten Auswirkungen an die zuständige Leitung zur weiteren Prüfung übergeben."),
    ]
    for i, (case, correct) in enumerate(expert_sensitive, 1):
        out.append(choice(f"sv_e_sens_{i:02d}", "Schriftverkehr", "Sensible Formulierungen", "Experte",
                          f"Welche Formulierung passt zu „{case}“?", correct,
                          ["Das geht gerade nicht.", "Dafür bin ich nicht zuständig.", "Das müssen Sie so hinnehmen."],
                          "Bei sensiblen Sachverhalten werden Unsicherheiten transparent benannt, ohne unzulässige Zusagen zu machen.",
                          "Formuliere belastbar und innerhalb der eigenen Zuständigkeit."))
    expert_structure = [
        ("Reklamation mit Frist", "Mangel konkret benennen → Bezug zu Bestellung/Rechnung herstellen → gewünschte Korrektur nennen → klare Frist setzen"),
        ("Angebotsanfrage", "Bedarf beschreiben → Menge/Leistung nennen → gewünschte Konditionen/Termin anfragen → Rückmeldefrist nennen"),
        ("Terminverschiebung", "Bisherigen Termin nennen → Änderung erklären → neuen Termin/Alternativen anbieten → Bestätigung erbitten"),
        ("Zahlungserinnerung", "Rechnung referenzieren → Fälligkeit/offenen Betrag nennen → Zahlung erbitten → Überschneidung/Rückfrage berücksichtigen"),
        ("Statusupdate bei Verzögerung", "Aktuellen Stand nennen → Ursache soweit sinnvoll erläutern → nächsten Schritt beschreiben → nächsten Rückmeldetermin nennen"),
        ("Antwort auf Beschwerde", "Anliegen bestätigen → geprüfte Fakten nennen → Lösung/Nächste Schritte erklären → Termin/Ansprechpartner nennen"),
        ("Korrekturrechnung senden", "Bezug zur fehlerhaften Rechnung → Korrektur kurz benennen → neue Rechnung anhängen → um Prüfung bitten"),
        ("Unterlagen anfordern", "Vorgang nennen → fehlende Unterlagen konkret aufzählen → sicheren Übertragungsweg nennen → Frist setzen"),
        ("Lieferausfall melden", "Betroffenen Auftrag nennen → Ausfall/Verzögerung transparent beschreiben → Alternative/Neutermin nennen → Rückmeldung anbieten"),
        ("Interne Übergabe", "Vorgang und Status → offene Punkte → Fristen/Risiken → nächste Schritte und Ansprechpartner"),
    ]
    for i, (case, correct) in enumerate(expert_structure, 1):
        out.append(choice(f"sv_e_struk_{i:02d}", "Schriftverkehr", "Aufbau geschäftlicher Schreiben", "Experte",
                          f"Welche Reihenfolge ist für „{case}“ am sinnvollsten?", correct,
                          ["Grußformel → Frist → Vorgang → Betreff", "Nur Forderung ohne Kontext", "Beliebige Reihenfolge ohne Referenz oder nächsten Schritt"],
                          "Ein gutes Schreiben führt vom Bezug und Sachverhalt zum gewünschten nächsten Schritt.",
                          "Strukturiere: Bezug → Fakten → Handlung → Termin/Abschluss."))
    return out


# Gesamtbank aufbauen. Durch feste IDs bleiben Fehlertraining und Historie stabil.
FIXED: list[Question] = []
FIXED.extend(LEGACY)
FIXED.extend(build_accounting())
FIXED.extend(build_german())
FIXED.extend(build_office())
FIXED.extend(build_processes())
FIXED.extend(build_correspondence())

# Alte technische Varianten mit identischem Vierer-Antwortsatz bleiben für Historien
# erhalten, werden neuen Trainings aber nicht mehr zugelost. So lernt man nicht bloß
# wiederkehrende Antwortmuster.
BASE_POOL_EXCLUDED_IDS = {"de_a_02"}
_seen_option_sets = {}
for _q in FIXED:
    if _q.id in BASE_POOL_EXCLUDED_IDS or _q.kind != "choice" or not _q.options:
        continue
    _sig = tuple(sorted(x.strip().casefold() for x in _q.options))
    if _sig in _seen_option_sets:
        BASE_POOL_EXCLUDED_IDS.add(_q.id)
    else:
        _seen_option_sets[_sig] = _q.id

# Historien-Kompatibilität: Der frühere 5.000er Testpool bleibt intern erhalten,
# damit alte Fehlerlisten bestehende Aufgaben noch rekonstruieren können. Für neue
# Trainings wird er ab Version 1.3 jedoch NICHT mehr vollständig verwendet.
from expanded_pool import build_expanded_questions
FIXED.extend(build_expanded_questions(FIXED, Question, choice, number, money, BASE_POOL_EXCLUDED_IDS))

# Version 1.3 TEST: exakt 3.000 aktive Aufgaben, gleichmäßig auf 5 Bereiche und
# 3 Schwierigkeitsstufen verteilt. Deutsch und Büroorganisation erhalten dafür
# neue, stufenspezifische Aufgabenbanken; die drei übrigen Bereiche werden aus
# den vielfältigsten bisherigen Aufgaben kuratiert.
from quality_pool_3000 import build_quality_pool
from distractor_quality import improve_distractors
from exam_style_pool import build_exam_style_questions

# Prüfungsnahe, vollständig neu formulierte Praxisaufgaben. Die bereitgestellten
# Musterunterlagen dienen nur als Orientierung für Themenbreite und Aufgabentiefe;
# Originaltexte werden nicht übernommen. Die bisherigen fünf Bereiche bleiben bei
# 3.000 Aufgaben. Ab Version 1.4.2 kommt Datenschutz & IT-Sicherheit als sechster
# eigenständiger Bereich mit 600 quellengestützten Aufgaben hinzu.
_base_3000 = improve_distractors(build_quality_pool(FIXED, Question, choice, number, money), Question)
_exam_style = build_exam_style_questions(Question, choice, number, money)
ACTIVE_3000 = []
for _cat in [c for c in CATEGORIES if c != "Datenschutz & IT-Sicherheit"]:
    for _lvl in LEVELS:
        _base_group = [q for q in _base_3000 if q.category == _cat and q.level == _lvl]
        _exam_group = [q for q in _exam_style if q.category == _cat and q.level == _lvl]
        if len(_exam_group) != 12:
            raise RuntimeError(f"Prüfungsnaher Pool {_cat}/{_lvl}: {len(_exam_group)} statt 12")
        # 188 bewährte Aufgaben + 12 prüfungsnahe Praxisfälle = weiterhin 200 je Bereich/Stufe.
        ACTIVE_3000.extend(_base_group[:188] + _exam_group)

# Neuer Bereich Datenschutz & IT-Sicherheit: 188 reguläre + 12 prüfungsnahe
# Aufgaben je Stufe = 600 zusätzliche Aufgaben. Fachquellen siehe privacy_pool.py
# und DATENSCHUTZ_QUELLEN_2026-09.txt. Das Update-System bleibt unverändert.
from privacy_pool import build_privacy_questions
_PRIVACY_600 = build_privacy_questions(Question, choice)
ACTIVE_3000.extend(_PRIVACY_600)

# Version 1.4.3: separat ergänzte Wissensbereiche, bestehende Fragen unangetastet.
from knowledge_143 import build_knowledge_143
_NEW_KNOWLEDGE_600 = build_knowledge_143(Question, choice, money)
ACTIVE_3000.extend(_NEW_KNOWLEDGE_600)

_existing_ids = {q.id for q in FIXED}
FIXED.extend(q for q in ACTIVE_3000 if q.id not in _existing_ids)


# Benutzerfreundliche Unterthemen. Die bestehenden internen Themen bleiben erhalten,
# damit alte Statistiken und Fehlerhistorien kompatibel bleiben.
SUBTOPIC_MAP = {
    "Rechnungswesen": {
        "Finanzbuchhaltung – Inventur und Bilanz": {"FiBu: Bilanz und Inventur"},
        "Finanzbuchhaltung – Soll und Haben": {"FiBu: Buchungssätze"},
        "Finanzbuchhaltung – Steuerbuchungen": {"FiBu: Steuerbuchungen"},
        "Finanzbuchhaltung – Abschreibung und GuV": {"FiBu: Abschreibung und GuV"},
        "Kaufmännische Steuerung – Kostenrechnung": {"Steuerung: Kostenrechnung"},
        "Kaufmännische Steuerung – BAB": {"Steuerung: Kostenstellen und BAB"},
        "Kaufmännische Steuerung – Deckungsbeitrag": {"Steuerung: Deckungsbeitrag"},
        "Kaufmännische Steuerung – Budget und Kennzahlen": {"Steuerung: Kennzahlen und Budget"},
        "Prozentrechnung": {"Prozentrechnung"},
        "Rabatt & Skonto": {"Rabatt", "Skonto"},
        "Umsatzsteuer / Netto-Brutto": {"Umsatzsteuer", "Menge und Umsatzsteuer", "Rabatt und Umsatzsteuer"},
        "Rechnungsprüfung": {"Rechnungsprüfung"},
        "Kalkulation & Mischaufgaben": {"Mehrstufige Rechnung"},
        "Prüfungsnahe Praxisfälle": {"Prüfungsnah: Bestandsplanung", "Prüfungsnah: Bestellmenge", "Prüfungsnah: Angebotsvergleich", "Prüfungsnah: Umsatzsteuer", "Prüfungsnah: Skonto", "Prüfungsnah: Rabatt", "Prüfungsnah: Rechnungsprüfung", "Prüfungsnah: Kalkulation", "Prüfungsnah: Preisabweichung", "Prüfungsnah: Mehrstufige Kalkulation", "Prüfungsnah: Skontoentscheidung"},
    },
    "Geschäftsprozesse": {
        "Einkauf – Bedarf und Bestellung": {"Einkauf: Bedarf und Bestellung"},
        "Einkauf – Lieferantenbewertung": {"Einkauf: Lieferantenbewertung"},
        "Einkauf – Beschaffungsstrategien": {"Einkauf: Beschaffungsstrategie"},
        "Einkauf – Kennzahlen": {"Einkauf: Kennzahlen und Controlling"},
        "Logistik – Lagerkennzahlen": {"Logistik: Lagerkennzahlen"},
        "Logistik – ABC- und XYZ-Analyse": {"Logistik: ABC- und XYZ-Analyse"},
        "Logistik – Kommissionierung und Versand": {"Logistik: Kommissionierung und Versand"},
        "Logistik – Transport und Kosten": {"Logistik: Transport und Kosten"},
        "Beschaffung & Ablauf": {"Ablauf", "Vom Angebot zur Rechnung", "Angebotsvergleich", "Prozesssteuerung"},
        "Dokumente & Rechnungsprüfung": {"Dokumente", "Lieferschein", "Rechnungsprüfung", "Komplexe Rechnungs- und Lieferprüfung"},
        "Wareneingang & Abweichungen": {"Wareneingang", "Mengenabweichung", "Qualitätsabweichung", "Reklamation"},
        "Lieferanten & Zahlungsabwicklung": {"Lieferantenmanagement", "Zahlungsabwicklung"},
        "Kontrolle & Risikovermeidung": {"Kontrolle und Risikovermeidung"},
        "Prüfungsnahe Praxisfälle": {"Prüfungsnah: Auftragsablauf", "Prüfungsnah: Reklamationsprozess", "Prüfungsnah: Wareneingang", "Prüfungsnah: Prozessverbesserung", "Prüfungsnah: Kundenkommunikation", "Prüfungsnah: Auftragsnachbereitung", "Prüfungsnah: Bestellprozess", "Prüfungsnah: Qualitätsabweichung", "Prüfungsnah: Zahlungsabwicklung", "Prüfungsnah: Prozessdarstellung", "Prüfungsnah: Kundenbeziehung", "Prüfungsnah: Lieferantenmanagement", "Prüfungsnah: Auftragsbearbeitung", "Prüfungsnah: Reklamation", "Prüfungsnah: Auftragssteuerung"},
    },
    "Deutsch & Rechtschreibung": {
        "Groß-/Kleinschreibung": {"Groß- und Kleinschreibung", "Nominalisierung"},
        "Kommasetzung": {"Kommasetzung"},
        "Getrennt-/Zusammenschreibung": {"Getrennt- und Zusammenschreibung"},
        "Allgemeine Rechtschreibung": {"Rechtschreibung"},
        "Geschäftlicher Ausdruck": {"Geschäftlicher Ausdruck", "Geschäftlicher Text"},
        "Prüfungsnahe Praxisfälle": {"Prüfungsnah: Geschäftlicher Ausdruck", "Prüfungsnah: Kommasetzung", "Prüfungsnah: Groß- und Kleinschreibung", "Prüfungsnah: Rechtschreibung", "Prüfungsnah: Getrennt-/Zusammenschreibung"},
    },
    "Schriftverkehr": {
        "Betreff, Anrede & E-Mail": {"Betreff", "Anrede und Abschluss", "E-Mail-Grundlagen"},
        "Anfragen & klare Formulierungen": {"Anfrage", "Klare Formulierung"},
        "Reklamation & Fristen": {"Reklamation", "Komplexe Reklamation", "Fristsetzung"},
        "Zahlungserinnerung": {"Zahlungserinnerung"},
        "Professioneller Geschäftston": {"Professioneller Ton", "Sensible Formulierungen", "Aufbau geschäftlicher Schreiben"},
        "Prüfungsnahe Praxisfälle": {"Prüfungsnah: Hausmitteilung", "Prüfungsnah: Bestellung", "Prüfungsnah: Reklamation", "Prüfungsnah: Kundeninformation", "Prüfungsnah: Anfrage", "Prüfungsnah: Zahlungserinnerung", "Prüfungsnah: Betreff", "Prüfungsnah: Abschluss", "Prüfungsnah: Anlage", "Prüfungsnah: Terminbestätigung", "Prüfungsnah: Rückfrage", "Prüfungsnah: Interne Mitteilung", "Prüfungsnah: Entscheidungsvorlage"},
    },
    "Büroorganisation": {
        "Prioritäten & Arbeitsorganisation": {"Prioritäten", "Arbeitsorganisation", "Prioritäten und Vertretung", "Komplexe Priorisierung"},
        "Datenschutz & IT-Sicherheit": {"Datenschutz und Sicherheit", "Datenschutz", "Datenschutz und IT-Sicherheit", "Sicherheits- und Datenschutzfälle"},
        "Ablage & Dokumentenmanagement": {"Ablage", "Dokumentenmanagement"},
        "Termine & Besprechungen": {"Terminplanung", "Besprechungsorganisation"},
        "Kommunikation & Prozesse": {"Kommunikation und Eskalation", "Prozessorganisation"},
        "Prüfungsnahe Praxisfälle": {"Prüfungsnah: Tabellenkalkulation", "Prüfungsnah: Diagramm", "Prüfungsnah: Dokumentenorganisation", "Prüfungsnah: Hausmitteilung", "Prüfungsnah: Dateiverwaltung", "Prüfungsnah: Terminplanung", "Prüfungsnah: Datenschutz", "Prüfungsnah: Ablage", "Prüfungsnah: Datenprüfung", "Prüfungsnah: Besprechungsorganisation", "Prüfungsnah: Formular", "Prüfungsnah: Prioritäten", "Prüfungsnah: Datenanalyse", "Prüfungsnah: Datenqualität", "Prüfungsnah: Prozesssteuerung"},
    },
    "Datenschutz & IT-Sicherheit": {
        "Personenbezogene Daten & DSGVO-Grundlagen": {"Personenbezogene Daten", "Besondere Kategorien personenbezogener Daten", "Datenminimierung", "Zweckbindung"},
        "Rechtsgrundlagen & Einwilligung": {"Rechtsgrundlagen", "Einwilligung", "Rechtsgrundlagen & Rechenschaftspflicht", "Zweckänderung"},
        "Betroffenenrechte": {"Betroffenenrechte", "Löschung & Aufbewahrung", "Auskunft & Rechte Dritter"},
        "Beschäftigtendaten": {"Beschäftigtendaten", "Besondere Kategorien & Beschäftigung"},
        "E-Mail, Passwörter & IT-Sicherheit": {"Zugriffsschutz", "E-Mail & Kommunikation", "Passwörter & Konten", "Phishing & E-Mail-Sicherheit", "Papier & Clean Desk", "Zugriffsrechte", "Sichere Übermittlung", "IT-Sicherheitsvorfälle", "Technische & organisatorische Maßnahmen"},
        "Datenpannen & Meldepflichten": {"Datenpannen", "Datenpannen & Risikobewertung", "Datenpannen & Betroffeneninformation", "E-Mail & Datenpannen"},
        "Auftragsverarbeitung & Dienstleister": {"Verantwortlicher & Auftragsverarbeiter", "Auftragsverarbeitung", "Dienstleister & Cloud", "Gemeinsame Verantwortlichkeit", "Drittlandübermittlung", "Auftragsverarbeitung & Datenpannen"},
        "Datenschutzorganisation": {"Pseudonymisierung & Anonymisierung", "Datenschutz-Folgenabschätzung", "Datenschutzbeauftragte", "Datenschutz durch Technikgestaltung", "Datenschutzorganisation", "Datenminimierung & Profilbildung"},
        "Prüfungsnahe Praxisfälle": {
            "Prüfungsnah: Personenbezogene Daten", "Prüfungsnah: Datenminimierung", "Prüfungsnah: E-Mail & Kommunikation",
            "Prüfungsnah: Zugriffsschutz", "Prüfungsnah: Phishing & E-Mail-Sicherheit", "Prüfungsnah: Betroffenenrechte",
            "Prüfungsnah: Datenpannen", "Prüfungsnah: Passwörter & Konten", "Prüfungsnah: Löschung & Aufbewahrung",
            "Prüfungsnah: Besondere Kategorien personenbezogener Daten", "Prüfungsnah: Zugriffsrechte", "Prüfungsnah: Sichere Übermittlung",
            "Prüfungsnah: Auftragsverarbeitung", "Prüfungsnah: Beschäftigtendaten", "Prüfungsnah: Datenschutz-Folgenabschätzung",
            "Prüfungsnah: Pseudonymisierung & Anonymisierung", "Prüfungsnah: Datenschutzbeauftragte", "Prüfungsnah: Datenschutz durch Technikgestaltung",
            "Prüfungsnah: Technische & organisatorische Maßnahmen", "Prüfungsnah: Dienstleister & Cloud",
            "Prüfungsnah: Zweckänderung", "Prüfungsnah: Datenpannen & Risikobewertung", "Prüfungsnah: Gemeinsame Verantwortlichkeit",
            "Prüfungsnah: Auskunft & Rechte Dritter", "Prüfungsnah: Drittlandübermittlung", "Prüfungsnah: Datenpannen & Betroffeneninformation",
            "Prüfungsnah: Datenschutzorganisation"
        },
    },
}

MIXED_SUBTOPIC = "Gemischtes Training"

# Eine alte Testfrage entspricht inhaltlich exakt einer später aufgebauten Aufgabe.
# Sie bleibt für bestehende Historien im Datenbestand, wird aber neuen Trainings nicht mehr zugelost.
POOL_EXCLUDED_IDS = set(BASE_POOL_EXCLUDED_IDS)


def _topics_for_subtopic(category: str, subtopic: str | None) -> set[str] | None:
    if not subtopic or subtopic == MIXED_SUBTOPIC:
        return None
    return SUBTOPIC_MAP.get(category, {}).get(subtopic)


def available_fixed(category: str, level: str, subtopic: str | None = None) -> list[Question]:
    candidates = [q for q in ACTIVE_3000 if q.category == category and q.level == level]
    topics = _topics_for_subtopic(category, subtopic)
    if topics is None:
        return candidates
    return [q for q in candidates if q.topic in topics]


def available_subtopics(category: str, level: str) -> list[str]:
    result = [MIXED_SUBTOPIC]
    for name in SUBTOPIC_MAP.get(category, {}):
        if available_fixed(category, level, name):
            result.append(name)
    return result


def pool_count(category: str, level: str, subtopic: str | None = None) -> int:
    return len(available_fixed(category, level, subtopic))


def semantic_key(question: Question) -> str:
    """Gruppiert künstlich erzeugte Varianten nach inhaltlicher Aufgabenfamilie.

    Dadurch kann eine Trainingseinheit zuerst unterschiedliche Denkaufgaben zeigen,
    statt mehrere nahezu gleiche Varianten direkt hintereinander auszuwählen.
    """
    m = re.match(r"^x_(rw|gp|de|sv|bo)_([A-Za-z])_(\d{3})$", question.id)
    if m:
        family = (int(m.group(3)) - 1) % 12
        return f"{question.category}|{question.level}|{question.topic}|F{family}"
    m = re.match(r"^q13_(de|bo)_([afe])_f(\d{2})_v\d{2}$", question.id)
    if m:
        return f"{question.category}|{question.level}|{question.topic}|F{int(m.group(3))}"
    m = re.match(r"^ds_([afe])_f(\d{2})_v\d{2}$", question.id)
    if m:
        return f"{question.category}|{question.level}|{question.topic}|F{int(m.group(2))}"
    return f"{question.category}|{question.level}|{question.topic}|{question.id}"


def semantic_keys_for_ids(question_ids: Iterable[str]) -> set[str]:
    ids = set(question_ids or [])
    if not ids:
        return set()
    return {semantic_key(q) for q in ACTIVE_3000 if q.id in ids}


def generate_question(category: str, level: str, exclude_ids: Iterable[str] | None = None,
                      exclude_prompts: Iterable[str] | None = None,
                      subtopic: str | None = None,
                      exclude_semantic_keys: Iterable[str] | None = None) -> Question:
    candidates = available_fixed(category, level, subtopic)
    if not candidates:
        label = f" / {subtopic}" if subtopic and subtopic != MIXED_SUBTOPIC else ""
        raise ValueError(f"Kein Aufgabenpool für {category} / {level}{label} vorhanden.")
    excluded_ids = set(exclude_ids or [])
    excluded_prompts = set(exclude_prompts or [])
    excluded_semantics = set(exclude_semantic_keys or [])

    fresh = [q for q in candidates
             if q.id not in excluded_ids
             and q.prompt not in excluded_prompts
             and semantic_key(q) not in excluded_semantics]
    if not fresh:
        fresh = [q for q in candidates if q.id not in excluded_ids and q.prompt not in excluded_prompts]
    if not fresh:
        fresh = [q for q in candidates if q.id not in excluded_ids]
    if not fresh:
        fresh = candidates
    q = random.choice(fresh)
    options = list(q.options or [])
    random.shuffle(options)
    return Question(q.id, q.category, q.topic, q.level, q.prompt, q.kind, q.correct,
                    q.explanation, options if options else None, q.hint, q.tolerance)


def points_for(level: str, correct: bool, hints_used: int = 0) -> int:
    if not correct:
        return 0
    base = {"Anfänger": 10, "Fortgeschritten": 20, "Experte": 30}.get(level, 10)
    return max(1, base - hints_used * 3)
