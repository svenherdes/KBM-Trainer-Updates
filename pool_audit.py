from collections import Counter, defaultdict
from pathlib import Path
import re
import questions

errors=[]
active=[]
for c in questions.CATEGORIES:
    for l in questions.LEVELS:
        active.extend(questions.available_fixed(c,l))

expected_total = 4200
if len(active)!=expected_total:
    errors.append(f"Aktiver Pool: {len(active)} statt {expected_total}")

by_pair=Counter((q.category,q.level) for q in active)
for c in questions.CATEGORIES:
    for l in questions.LEVELS:
        target = 320 if c == "Rechnungswesen" else 280 if c == "Geschäftsprozesse" else 200
        if by_pair[(c,l)]!=target:
            errors.append(f"{c}/{l}: {by_pair[(c,l)]} statt {target}")

ids=Counter(q.id for q in active)
for k,v in ids.items():
    if v!=1: errors.append(f"Doppelte aktive ID: {k} ({v}x)")

prompt_correct=defaultdict(list)
answer_sets=defaultdict(list)
for q in active:
    key=(" ".join(q.prompt.split()).casefold(), " ".join(q.correct.split()).casefold())
    prompt_correct[key].append(q.id)
    if not q.check(q.correct):
        errors.append(f"Eigene Lösung wird abgelehnt: {q.id}")
    if q.kind=="choice":
        opts=q.options or []
        if q.correct not in opts:
            errors.append(f"Richtige Auswahl fehlt: {q.id}")
        if len(opts)!=4:
            errors.append(f"Nicht genau 4 Antwortmöglichkeiten: {q.id} ({len(opts)})")
        if len(opts)!=len(set(opts)):
            errors.append(f"Doppelte Auswahl innerhalb Aufgabe: {q.id}")
        sig=tuple(sorted(" ".join(x.split()).casefold() for x in opts))
        answer_sets[sig].append(q.id)

for same in prompt_correct.values():
    if len(same)>1:
        errors.append("Exakt gleiche Frage+Lösung: "+", ".join(same[:10]))
def audit_family(q):
    # Nur fuer die Quellenpruefung: gleiche fachliche Aufgabenfamilie in neuen
    # Zahlen-/Fallvarianten; die Laufzeitlogik des Trainers bleibt unberuehrt.
    m = re.match(r"^kb143_([a-z_]+)_([AFE])_(\d{3})$", q.id)
    if m:
        size = ({"fibu_buchung": 12, "einkauf_strategie": 4}
                .get(m.group(1), 4 if m.group(1).startswith(("fibu_", "einkauf_")) else 5))
        return f"{q.category}|{q.topic}|K{(int(m.group(3))-1) % size}"
    return questions.semantic_key(q)

for same in answer_sets.values():
    if len(same)>1:
        qs = [next(q for q in active if q.id == qid) for qid in same]
        families = {audit_family(q) for q in qs}
        if len(families) > 1:
            errors.append("Gleicher Multiple-Choice-Antwortsatz in unterschiedlichen Aufgabenfamilien: "+", ".join(same[:10]))

# Stufen-Trennung: Für die Vergleichssignatur werden Zahlen/Namen abstrahiert,
# aber bei Multiple Choice auch die Antwortmöglichkeiten einbezogen. So ist eine
# generische Arbeitsanweisung wie "Welche Schreibweise ist korrekt?" erlaubt,
# solange der eigentliche Satz/Antwortinhalt in den Stufen verschieden ist.
def skeleton(text):
    s=" ".join(text.split()).casefold()
    s=re.sub(r"\b\d+[\d.,]*\b", "<n>", s)
    s=re.sub(r"\b(?:frau|herr)\s+[a-zäöüß-]+\b", "<name>", s)
    return s

cross=defaultdict(lambda: defaultdict(list))
for q in active:
    content = q.prompt
    if q.kind == "choice":
        content += " || " + " || ".join(sorted(q.options or []))
    else:
        content += " || " + q.correct
    cross[(q.category,skeleton(content))][q.level].append(q.id)
for (cat,sk), levels in cross.items():
    if len(levels)>1:
        detail="; ".join(f"{lvl}: {ids[:3]}" for lvl,ids in levels.items())
        errors.append(f"Gleicher normalisierter Aufgabeninhalt in mehreren Stufen ({cat}): {detail}")

# Keine künstlichen sichtbaren Fall-Präfixe in Antworten.
for q in active:
    if q.kind == "choice":
        for opt in (q.options or []):
            if "zum fall" in opt.casefold():
                errors.append(f"Künstlicher 'Zum Fall'-Präfix in {q.id}: {opt}")

# Radio-Button-Regressionsprüfung: Keine Vorauswahl.
app=Path(__file__).with_name('app.py').read_text(encoding='utf-8')
for needle in ['StringVar(value="__NO_SELECTION__")', 'tristatevalue="__TRISTATE__"', 'answer == "__NO_SELECTION__"']:
    if needle not in app:
        errors.append(f"Radiobutton-Fix fehlt: {needle}")

print("KBM TRAINER 1.4.3 - POOL AUDIT")
print("="*40)
print(f"Aktiver Aufgabenpool: {len(active)}")
print("Verteilung je Bereich/Stufe:")
for c in questions.CATEGORIES:
    print(f"  {c}:")
    for l in questions.LEVELS:
        print(f"    {l}: {by_pair[(c,l)]}")
print(f"Multiple Choice: {sum(q.kind=='choice' for q in active)}")
print(f"Numerisch/frei: {sum(q.kind!='choice' for q in active)}")
print(f"Wiederholte Antwortsets innerhalb derselben Familie: {sum(1 for v in answer_sets.values() if len(v)>1)}")
print(f"Exakt doppelte Frage+Lösung: {sum(1 for v in prompt_correct.values() if len(v)>1)}")
print(f"Gleicher normalisierter Aufgabeninhalt in mehreren Stufen: {sum(1 for v in cross.values() if len(v)>1)}")
print()
if errors:
    print("FEHLER:")
    for e in errors[:100]: print("-",e)
    raise SystemExit(1)
print("AUDIT OK")
