import tempfile
from pathlib import Path

import db
import questions


def run():
    tmp = Path(tempfile.mkdtemp()) / "test.db"
    db.DB_PATH = tmp
    db.init_db()
    pid = db.create_profile("Test")
    db.save_attempt(pid, "training", "Rechnungswesen", "Rabatt", "Anfänger", "q1", "Test?", "1", "1", "ok", True, 10, 0, 10, question_kind="number")
    db.save_attempt(pid, "exam", "Büroorganisation", "Prioritäten", "Fortgeschritten", "q2", "Test?", "x", "y", "no", False, 15, 0, 0, question_kind="text")
    assert db.summary(pid, "Gesamt")["total"] == 2
    assert db.summary(pid, "Gesamt", "Training")["total"] == 1
    assert db.summary(pid, "Gesamt", "Prüfungen")["total"] == 1
    errors = db.active_errors(pid)
    assert len(errors) == 1
    # Two later correct answers resolve the active error.
    for _ in range(2):
        db.save_attempt(pid, "error_training", "Büroorganisation", "Prioritäten", "Fortgeschritten", "q2", "Test?", "y", "y", "ok", True, 2, 0, 20, question_kind="text")
    assert len(db.active_errors(pid)) == 0
    sid = db.start_exam_session(pid, "Fortgeschritten", 20)
    db.finish_exam_session(sid, 12, 240, 600)
    assert len(db.exam_history(pid)) == 1

    # Profile backup/import must preserve all learning data.
    backup = tmp.parent / "profile.kbmbackup"
    exported = db.export_profile(pid, backup, "1.0-test")
    assert backup.exists() and exported["attempts"] == 4 and exported["exams"] == 1
    meta = db.inspect_backup(backup)
    assert meta["profile"]["name"] == "Test"
    imported = db.import_profile(backup, "Test Import")
    imported_pid = imported["profile_id"]
    assert db.summary(imported_pid, "Gesamt")["total"] == 4
    assert len(db.exam_history(imported_pid)) == 1
    assert len(db.active_errors(imported_pid)) == 0

    # Subtopic selection must expose only non-empty pools.
    for category in questions.CATEGORIES:
        for level in questions.LEVELS:
            subs = questions.available_subtopics(category, level)
            assert subs[0] == questions.MIXED_SUBTOPIC
            assert questions.pool_count(category, level, questions.MIXED_SUBTOPIC) > 0
            for subtopic in subs[1:]:
                assert questions.pool_count(category, level, subtopic) > 0
                q = questions.generate_question(category, level, subtopic=subtopic)
                allowed = {x.id for x in questions.available_fixed(category, level, subtopic)}
                assert q.id in allowed

    # Rule-based learning recommendation: 5 attempts with a weak hit rate.
    rec_pid = db.create_profile("Recommendation Test")
    for i, ok in enumerate([True, False, False, True, False], start=1):
        db.save_attempt(
            rec_pid, "training", "Büroorganisation", "Prioritäten", "Anfänger",
            f"rec{i}", f"Frage {i}", "x", "y", "", ok, 1, 0, 10 if ok else 0,
            question_kind="choice"
        )
    recs = db.learning_recommendations(rec_pid)
    assert recs and recs[0]["category"] == "Büroorganisation"
    assert recs[0]["topic"] == "Prioritäten"
    assert recs[0]["status"] == "Noch üben"

    # Stage progress stays visible even when the recommendation is not yet earned.
    progress = db.stage_progress(rec_pid, "Anfänger")
    qualification = db.stage_qualification(progress)
    assert qualification["qualified"] is False
    assert qualification["criteria"]["attempts"] is False
    assert qualification["requirements"]["attempts"] == 40
    assert qualification["requirements"]["rate"] == 85.0
    assert qualification["requirements"]["exam"] == 90.0
    assert qualification["requirements"]["errors"] == 3

    print("CORE TEST OK")


if __name__ == "__main__":
    run()
