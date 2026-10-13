import questions


def run():
    ids=[]
    for cat in questions.CATEGORIES:
        for lvl in questions.LEVELS:
            qs=questions.available_fixed(cat,lvl,"Prüfungsnahe Praxisfälle")
            assert len(qs)==12, (cat,lvl,len(qs))
            assert all(q.id.startswith("exam_") for q in qs)
            ids.extend(q.id for q in qs)
            for q in qs:
                assert q.check(q.correct), q.id
                if q.kind == "choice":
                    assert len(q.options or []) == 4, q.id
                    assert q.correct in q.options, q.id
    expected = len(questions.CATEGORIES) * len(questions.LEVELS) * 12
    assert len(ids)==expected
    assert len(set(ids))==expected
    print(f"EXAM STYLE TEST OK - {expected} prüfungsnahe Aufgaben")

if __name__ == "__main__":
    run()
