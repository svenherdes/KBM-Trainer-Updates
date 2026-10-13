"""Regressionscheck der rein inhaltlichen Version-1.4.3-Erweiterung."""
from collections import Counter
import questions


def run():
    new = [q for q in questions.ACTIVE_3000 if q.id.startswith('kb143_')]
    old = [q for q in questions.ACTIVE_3000 if not q.id.startswith('kb143_')]
    assert len(old) == 3600, len(old)
    assert len(new) == 600, len(new)
    assert len(questions.ACTIVE_3000) == 4200
    assert len({q.id for q in questions.ACTIVE_3000}) == 4200
    targets = {'Rechnungswesen': 120, 'Geschäftsprozesse': 80}
    for category, n in targets.items():
        for level in questions.LEVELS:
            group = [q for q in new if q.category == category and q.level == level]
            assert len(group) == n, (category,level,len(group))
    expected = {
        'fibu_bilanz':12,'fibu_buchung':24,'fibu_steuer':12,'fibu_guv':12,
        'steuer_kosten':15,'steuer_bab':15,'steuer_db':15,'steuer_budget':15,
        'einkauf_bedarf':12,'einkauf_nutzwert':12,'einkauf_strategie':8,'einkauf_controlling':8,
        'logistik_lager':12,'logistik_abc':10,'logistik_kommission':10,'logistik_transport':8,
    }
    names = set()
    for code,n in expected.items():
        for lvl in questions.LEVELS:
            group=[q for q in new if q.id.startswith('kb143_'+code+'_'+lvl[0]+'_')]
            assert len(group)==n, (code,lvl,len(group))
            names.add(group[0].topic)
            visible=[s for s in questions.available_subtopics(group[0].category,lvl)
                     if s!=questions.MIXED_SUBTOPIC and any(q.topic in questions.SUBTOPIC_MAP[group[0].category][s] for q in group)]
            assert visible, (code,lvl)
    assert len(names)==16
    signatures=set()
    for q in new:
        assert q.check(q.correct), q.id
        assert q.explanation and q.hint, q.id
        sig=(q.prompt.strip().casefold(),q.correct.strip().casefold())
        assert sig not in signatures, q.id
        signatures.add(sig)
        if q.kind=='choice':
            assert q.correct in q.options and len(q.options)==4 and len(set(q.options))==4, q.id
        else:
            assert q.kind=='number',q.id
    c=Counter(q.kind for q in new)
    assert c['choice']+c['number']==600
    print(f'NEUE WISSENSBEREICHE OK - {len(new)} neue Fragen, {len(names)} Unterthemen, '+
          f'{c["choice"]} Auswahlfragen, {c["number"]} Rechenfragen; bestehender Bestand: {len(old)}')

if __name__ == '__main__':
    run()
