import questions

CATEGORY = "Datenschutz & IT-Sicherheit"


def run():
    all_q=[]
    for level in questions.LEVELS:
        qs=questions.available_fixed(CATEGORY, level)
        assert len(qs)==200, (level, len(qs))
        assert len({q.id for q in qs})==200
        assert len({q.prompt for q in qs})==200
        exam=questions.available_fixed(CATEGORY, level, "Prüfungsnahe Praxisfälle")
        assert len(exam)==12, (level, len(exam))
        for q in qs:
            assert q.explanation.strip(), q.id
            assert q.check(q.correct), q.id
            if q.kind=="choice":
                assert len(q.options or [])==4, q.id
                assert len(set(q.options or []))==4, q.id
                assert q.correct in q.options, q.id
        all_q.extend(qs)
    assert len(all_q)==600
    assert len({q.id for q in all_q})==600
    assert len({q.prompt for q in all_q})==600
    # Rechtsstands-Sicherheitschecks fuer zentrale Zahlen/Fakten.
    text="\n".join(q.prompt+"\n"+q.correct+"\n"+q.explanation for q in all_q)
    assert "72 Stunden" in text
    assert "innerhalb eines Monats" in text
    assert "mindestens 20 Personen" in text
    print("DATENSCHUTZ TEST OK - 600 Aufgaben / 200 je Stufe / 12 Praxisfaelle je Stufe")


if __name__ == "__main__":
    run()
