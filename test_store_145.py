"""Tests der isolierten Store-1.4.5-Funktionen ohne grafische Oberflaeche."""
import ast
from pathlib import Path

import db
from store_features_145 import FEEDBACK_URL, stage_display_rows, prioritized_error_rows


def run():
    p = {"total": 64, "rate": 91.0, "active_errors": 2, "latest_exam_rate": 93.0}
    q = db.stage_qualification(p)
    assert q["qualified"]
    rows = stage_display_rows(p, q)
    assert len(rows) == 4
    assert "64 bearbeitet" in rows[0][1]
    assert "mindestens 40" in rows[0][1]
    assert rows[0][2]
    assert rows[3][2]

    active = [
        {"question_id": "A", "recovery_correct": 1, "id": 100},
        {"question_id": "B", "recovery_correct": 0, "id": 200},
        {"question_id": "C", "recovery_correct": 0, "id": 300},
    ]
    wrong = [
        {"question_id": "A"},
        {"question_id": "A"},
        {"question_id": "A"},
        {"question_id": "B"},
        {"question_id": "B"},
        {"question_id": "C"},
    ]
    ranked = prioritized_error_rows(active, wrong)
    assert [row["question_id"] for row in ranked] == ["A", "B", "C"]
    assert [row["question_id"] for row in active] == ["A", "B", "C"]
    assert FEEDBACK_URL.startswith("https://docs.google.com/forms/")

    source = Path("store_update_145_entry.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert "KBMStoreApp" in source
    assert "original.APP_VERSION = \"1.4.5\"" in source
    assert "self._open_store()" in source
    assert "FEEDBACK_URL" in source
    assert "return super().start_error_training(ranked)" in source
    assert "super().download_and_install_update" not in source

    # Wesentlich: Produktivversion und GitHub-Updater werden NICHT veraendert.
    original_source = Path("app.py").read_text(encoding="utf-8")
    assert 'APP_VERSION = "1.4.3"' in original_source
    assert 'UPDATE_MANIFEST_URL = "https://raw.githubusercontent.com/' in original_source

    print("STORE 145 FEATURE TEST OK")


if __name__ == "__main__":
    run()
