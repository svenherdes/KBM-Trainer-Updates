from __future__ import annotations

import json
import os
import sqlite3
import zipfile
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

APP_NAME = "KBMTrainer"
ERROR_RECOVERY_REQUIRED = 2


def app_data_dir() -> Path:
    """Return an OS-appropriate local application data directory."""
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif os.name == "posix":
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    else:
        base = Path.home()
    path = base / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


DB_PATH = app_data_dir() / "kbm_trainer.db"


@contextmanager
def connection():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        con.execute("PRAGMA foreign_keys = ON")
        yield con
        con.commit()
    finally:
        con.close()


def _ensure_column(con: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    cols = {row["name"] for row in con.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in cols:
        con.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db() -> None:
    """Create and migrate the local database without deleting existing v0.1 data."""
    with connection() as con:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                created_at TEXT NOT NULL,
                last_used_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                mode TEXT NOT NULL DEFAULT 'training',
                category TEXT NOT NULL,
                topic TEXT NOT NULL,
                level TEXT NOT NULL,
                question_id TEXT NOT NULL,
                prompt TEXT NOT NULL,
                user_answer TEXT,
                correct_answer TEXT NOT NULL,
                explanation TEXT,
                is_correct INTEGER NOT NULL,
                elapsed_seconds REAL NOT NULL DEFAULT 0,
                hints_used INTEGER NOT NULL DEFAULT 0,
                points INTEGER NOT NULL DEFAULT 0,
                session_id INTEGER,
                question_kind TEXT,
                options_json TEXT,
                hint TEXT,
                FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS exam_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                level TEXT NOT NULL,
                total_questions INTEGER NOT NULL,
                correct_count INTEGER NOT NULL DEFAULT 0,
                points INTEGER NOT NULL DEFAULT 0,
                elapsed_seconds REAL NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'running',
                FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_attempts_profile_date
                ON attempts(profile_id, created_at);
            CREATE INDEX IF NOT EXISTS idx_attempts_profile_category
                ON attempts(profile_id, category);
            CREATE INDEX IF NOT EXISTS idx_attempts_question
                ON attempts(profile_id, question_id, id);
            CREATE INDEX IF NOT EXISTS idx_exam_sessions_profile_date
                ON exam_sessions(profile_id, started_at);
            """
        )
        # Safe migration from v0.1 databases.
        _ensure_column(con, "attempts", "session_id", "INTEGER")
        _ensure_column(con, "attempts", "question_kind", "TEXT")
        _ensure_column(con, "attempts", "options_json", "TEXT")
        _ensure_column(con, "attempts", "hint", "TEXT")


def create_profile(name: str) -> int:
    name = name.strip()
    if not name:
        raise ValueError("Bitte einen Namen eingeben.")
    now = datetime.now().isoformat(timespec="seconds")
    with connection() as con:
        cur = con.execute(
            "INSERT INTO profiles(name, created_at, last_used_at) VALUES (?, ?, ?)",
            (name, now, now),
        )
        return int(cur.lastrowid)


def list_profiles():
    with connection() as con:
        return con.execute(
            "SELECT id, name, created_at, last_used_at FROM profiles ORDER BY last_used_at DESC, name"
        ).fetchall()


def touch_profile(profile_id: int) -> None:
    with connection() as con:
        con.execute(
            "UPDATE profiles SET last_used_at=? WHERE id=?",
            (datetime.now().isoformat(timespec="seconds"), profile_id),
        )


def delete_profile(profile_id: int) -> None:
    with connection() as con:
        con.execute("DELETE FROM profiles WHERE id=?", (profile_id,))


def start_exam_session(profile_id: int, level: str, total_questions: int) -> int:
    with connection() as con:
        cur = con.execute(
            """
            INSERT INTO exam_sessions(profile_id, started_at, level, total_questions, status)
            VALUES (?, ?, ?, ?, 'running')
            """,
            (profile_id, datetime.now().isoformat(timespec="seconds"), level, total_questions),
        )
        return int(cur.lastrowid)


def finish_exam_session(session_id: int, correct_count: int, points: int, elapsed_seconds: float, status: str = "complete") -> None:
    with connection() as con:
        con.execute(
            """
            UPDATE exam_sessions
            SET finished_at=?, correct_count=?, points=?, elapsed_seconds=?, status=?
            WHERE id=?
            """,
            (
                datetime.now().isoformat(timespec="seconds"),
                int(correct_count),
                int(points),
                float(elapsed_seconds),
                status,
                session_id,
            ),
        )


def abort_exam_session(session_id: int) -> None:
    """Remove answers from an unfinished exam so it does not affect learning statistics."""
    with connection() as con:
        con.execute("DELETE FROM attempts WHERE session_id=?", (session_id,))
        con.execute(
            "UPDATE exam_sessions SET finished_at=?, status='aborted' WHERE id=?",
            (datetime.now().isoformat(timespec="seconds"), session_id),
        )


def save_attempt(
    profile_id: int,
    mode: str,
    category: str,
    topic: str,
    level: str,
    question_id: str,
    prompt: str,
    user_answer: str,
    correct_answer: str,
    explanation: str,
    is_correct: bool,
    elapsed_seconds: float,
    hints_used: int,
    points: int,
    session_id: int | None = None,
    question_kind: str | None = None,
    options: list[str] | None = None,
    hint: str = "",
) -> None:
    with connection() as con:
        con.execute(
            """
            INSERT INTO attempts(
                profile_id, created_at, mode, category, topic, level,
                question_id, prompt, user_answer, correct_answer,
                explanation, is_correct, elapsed_seconds, hints_used, points,
                session_id, question_kind, options_json, hint
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                profile_id,
                datetime.now().isoformat(timespec="seconds"),
                mode,
                category,
                topic,
                level,
                question_id,
                prompt,
                user_answer,
                correct_answer,
                explanation,
                1 if is_correct else 0,
                float(elapsed_seconds),
                int(hints_used),
                int(points),
                session_id,
                question_kind,
                json.dumps(options, ensure_ascii=False) if options else None,
                hint or None,
            ),
        )


def _period_start(period: str, now: Optional[datetime] = None) -> Optional[datetime]:
    now = now or datetime.now()
    if period == "Tag":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "Woche":
        start = now - timedelta(days=now.weekday())
        return start.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "Monat":
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if period == "Jahr":
        return now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    return None


def _previous_period_bounds(period: str, now: Optional[datetime] = None):
    now = now or datetime.now()
    current_start = _period_start(period, now)
    if current_start is None:
        return None, None
    if period == "Tag":
        prev_start = current_start - timedelta(days=1)
    elif period == "Woche":
        prev_start = current_start - timedelta(days=7)
    elif period == "Monat":
        prev_last = current_start - timedelta(days=1)
        prev_start = prev_last.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == "Jahr":
        prev_start = current_start.replace(year=current_start.year - 1)
    else:
        return None, None
    return prev_start, current_start


def _mode_condition(mode_filter: str) -> tuple[str, list[str]]:
    if mode_filter == "Training":
        return " AND mode IN (?, ?)", ["training", "error_training"]
    if mode_filter == "Prüfungen":
        return " AND mode=?", ["exam"]
    return "", []


def _where(profile_id: int, period: str, mode_filter: str = "Alle") -> tuple[str, list]:
    where = "profile_id=?"
    params: list = [profile_id]
    start = _period_start(period)
    if start is not None:
        where += " AND created_at>=?"
        params.append(start.isoformat(timespec="seconds"))
    mode_sql, mode_params = _mode_condition(mode_filter)
    where += mode_sql
    params.extend(mode_params)
    return where, params


def summary(profile_id: int, period: str, mode_filter: str = "Alle"):
    where, params = _where(profile_id, period, mode_filter)
    with connection() as con:
        row = con.execute(
            f"""
            SELECT COUNT(*) AS total,
                   COALESCE(SUM(is_correct),0) AS correct,
                   COALESCE(SUM(elapsed_seconds),0) AS seconds,
                   COALESCE(SUM(points),0) AS points,
                   COALESCE(SUM(CASE WHEN mode='exam' THEN 1 ELSE 0 END),0) AS exam_answers
            FROM attempts WHERE {where}
            """,
            params,
        ).fetchone()
    total = int(row["total"])
    correct = int(row["correct"])
    return {
        "total": total,
        "correct": correct,
        "wrong": total - correct,
        "rate": (correct / total * 100.0) if total else 0.0,
        "seconds": float(row["seconds"]),
        "points": int(row["points"]),
        "exam_answers": int(row["exam_answers"]),
    }


def previous_summary(profile_id: int, period: str, mode_filter: str = "Alle"):
    start, end = _previous_period_bounds(period)
    if start is None:
        return None
    where = "profile_id=? AND created_at>=? AND created_at<?"
    params: list = [profile_id, start.isoformat(timespec="seconds"), end.isoformat(timespec="seconds")]
    mode_sql, mode_params = _mode_condition(mode_filter)
    where += mode_sql
    params.extend(mode_params)
    with connection() as con:
        row = con.execute(
            f"""
            SELECT COUNT(*) AS total,
                   COALESCE(SUM(is_correct),0) AS correct,
                   COALESCE(SUM(elapsed_seconds),0) AS seconds,
                   COALESCE(SUM(points),0) AS points
            FROM attempts WHERE {where}
            """,
            params,
        ).fetchone()
    total = int(row["total"])
    correct = int(row["correct"])
    return {
        "total": total,
        "correct": correct,
        "wrong": total - correct,
        "rate": (correct / total * 100.0) if total else 0.0,
        "seconds": float(row["seconds"]),
        "points": int(row["points"]),
    }


def category_stats(profile_id: int, period: str, mode_filter: str = "Alle"):
    where, params = _where(profile_id, period, mode_filter)
    with connection() as con:
        rows = con.execute(
            f"""
            SELECT category, COUNT(*) AS total, SUM(is_correct) AS correct, SUM(points) AS points
            FROM attempts WHERE {where}
            GROUP BY category ORDER BY category
            """,
            params,
        ).fetchall()
    result = []
    for row in rows:
        total = int(row["total"])
        correct = int(row["correct"] or 0)
        result.append({
            "category": row["category"],
            "total": total,
            "correct": correct,
            "rate": (correct / total * 100.0) if total else 0.0,
            "points": int(row["points"] or 0),
        })
    return result


def level_stats(profile_id: int, period: str, mode_filter: str = "Alle"):
    where, params = _where(profile_id, period, mode_filter)
    with connection() as con:
        rows = con.execute(
            f"""
            SELECT level, COUNT(*) AS total, SUM(is_correct) AS correct
            FROM attempts WHERE {where}
            GROUP BY level
            """,
            params,
        ).fetchall()
    result = {}
    for row in rows:
        total = int(row["total"])
        correct = int(row["correct"] or 0)
        result[row["level"]] = {"total": total, "correct": correct, "rate": (correct / total * 100.0) if total else 0.0}
    return result


def trend(profile_id: int, period: str, mode_filter: str = "Alle"):
    """Return compact trend buckets for the active period and data filter."""
    now = datetime.now()
    if period == "Tag":
        start = _period_start("Tag", now)
        fmt = "%H"
        labeler = lambda key: f"{int(key):02d} Uhr"
    elif period == "Woche":
        start = _period_start("Woche", now)
        fmt = "%Y-%m-%d"
        weekday = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
        labeler = lambda key: weekday[datetime.fromisoformat(key).weekday()]
    elif period == "Monat":
        start = _period_start("Monat", now)
        fmt = "%Y-%m-%d"
        labeler = lambda key: str(datetime.fromisoformat(key).day)
    elif period == "Jahr":
        start = _period_start("Jahr", now)
        fmt = "%Y-%m"
        months = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
        labeler = lambda key: months[int(key[-2:]) - 1]
    else:
        start = None
        fmt = "%Y-%m"
        labeler = lambda key: key

    query = "SELECT created_at, is_correct FROM attempts WHERE profile_id=?"
    params: list = [profile_id]
    if start is not None:
        query += " AND created_at>=?"
        params.append(start.isoformat(timespec="seconds"))
    mode_sql, mode_params = _mode_condition(mode_filter)
    query += mode_sql
    params.extend(mode_params)
    query += " ORDER BY created_at"
    with connection() as con:
        rows = con.execute(query, params).fetchall()

    buckets = {}
    for row in rows:
        dt = datetime.fromisoformat(row["created_at"])
        key = dt.strftime(fmt)
        item = buckets.setdefault(key, [0, 0])
        item[0] += 1
        item[1] += int(row["is_correct"])

    return [
        {"label": labeler(key), "total": vals[0], "rate": vals[1] / vals[0] * 100.0}
        for key, vals in buckets.items()
    ]


def active_errors(profile_id: int, limit: int = 100):
    """Return errors that have not yet been answered correctly twice after the latest wrong attempt."""
    with connection() as con:
        wrongs = con.execute(
            """
            SELECT a.*
            FROM attempts a
            JOIN (
                SELECT question_id, MAX(id) AS last_wrong_id
                FROM attempts
                WHERE profile_id=? AND is_correct=0
                GROUP BY question_id
            ) x ON x.last_wrong_id=a.id
            WHERE a.profile_id=?
            ORDER BY a.id DESC
            LIMIT ?
            """,
            (profile_id, profile_id, limit),
        ).fetchall()
        result = []
        for row in wrongs:
            recovered = con.execute(
                """
                SELECT COUNT(*) AS n
                FROM attempts
                WHERE profile_id=? AND question_id=? AND id>? AND is_correct=1
                """,
                (profile_id, row["question_id"], row["id"]),
            ).fetchone()["n"]
            if int(recovered) < ERROR_RECOVERY_REQUIRED:
                item = dict(row)
                item["recovery_correct"] = int(recovered)
                item["recovery_required"] = ERROR_RECOVERY_REQUIRED
                result.append(item)
        return result


def learning_recommendations(profile_id: int, limit: int = 12, recent_per_topic: int = 20):
    """Return rule-based learning recommendations for one profile.

    The calculation deliberately uses only local learning data. For each
    category/topic/level combination, at most the latest `recent_per_topic`
    attempts are considered so older mistakes do not permanently dominate the
    recommendation. A topic is recommended when at least five recent attempts
    exist and the hit rate is below 85%, or when at least two unresolved errors
    remain.
    """
    with connection() as con:
        rows = con.execute(
            """
            SELECT id, category, topic, level, is_correct
            FROM attempts
            WHERE profile_id=? AND mode IN ('training', 'error_training', 'exam')
            ORDER BY id DESC
            """,
            (profile_id,),
        ).fetchall()

    grouped: dict[tuple[str, str, str], list[int]] = {}
    for row in rows:
        key = (str(row["category"]), str(row["topic"]), str(row["level"]))
        bucket = grouped.setdefault(key, [])
        if len(bucket) < int(recent_per_topic):
            bucket.append(int(row["is_correct"]))

    error_counts: dict[tuple[str, str, str], int] = {}
    for row in active_errors(profile_id, limit=1000):
        key = (str(row["category"]), str(row["topic"]), str(row["level"]))
        error_counts[key] = error_counts.get(key, 0) + 1

    keys = set(grouped) | set(error_counts)
    result = []
    for category, topic, level in keys:
        answers = grouped.get((category, topic, level), [])
        total = len(answers)
        correct = sum(answers)
        rate = (correct / total * 100.0) if total else 0.0
        open_errors = int(error_counts.get((category, topic, level), 0))

        qualifies = (total >= 5 and rate < 85.0) or open_errors >= 2
        if not qualifies:
            continue

        status = "Noch üben" if rate < 70.0 or open_errors >= 4 else "Festigen"
        # Lower hit rates and more unresolved errors rank first.
        priority = (0 if status == "Noch üben" else 1, rate, -open_errors, -total, category, topic, level)
        result.append({
            "category": category,
            "topic": topic,
            "level": level,
            "total": total,
            "correct": correct,
            "rate": rate,
            "active_errors": open_errors,
            "status": status,
            "_priority": priority,
        })

    result.sort(key=lambda item: item["_priority"])
    for item in result:
        item.pop("_priority", None)
    return result[: int(limit)]



def stage_progress(profile_id: int, level: str) -> dict:
    """Return the local evidence used for a difficulty-stage recommendation.

    Only normal training and completed exam answers count toward the general
    hit rate. Error-training repetitions are intentionally excluded so that
    repeatedly correcting one old mistake cannot artificially unlock a higher
    stage.
    """
    with connection() as con:
        row = con.execute(
            """
            SELECT COUNT(*) AS total, COALESCE(SUM(is_correct), 0) AS correct
            FROM attempts
            WHERE profile_id=? AND level=? AND mode IN ('training', 'exam')
            """,
            (profile_id, level),
        ).fetchone()
        exam = con.execute(
            """
            SELECT id, total_questions, correct_count, finished_at
            FROM exam_sessions
            WHERE profile_id=? AND level=? AND status='complete'
            ORDER BY id DESC
            LIMIT 1
            """,
            (profile_id, level),
        ).fetchone()

    total = int(row["total"] or 0)
    correct = int(row["correct"] or 0)
    rate = (correct / total * 100.0) if total else 0.0
    exam_rate = None
    exam_total = 0
    exam_correct = 0
    if exam is not None:
        exam_total = int(exam["total_questions"] or 0)
        exam_correct = int(exam["correct_count"] or 0)
        exam_rate = (exam_correct / exam_total * 100.0) if exam_total else 0.0

    open_errors = sum(1 for item in active_errors(profile_id, limit=2000) if str(item["level"]) == level)
    return {
        "level": level,
        "total": total,
        "correct": correct,
        "rate": rate,
        "latest_exam_rate": exam_rate,
        "latest_exam_total": exam_total,
        "latest_exam_correct": exam_correct,
        "active_errors": open_errors,
    }


STAGE_MIN_ATTEMPTS = 40
STAGE_MIN_RATE = 85.0
STAGE_MIN_EXAM_RATE = 90.0
STAGE_MAX_ACTIVE_ERRORS = 3


def stage_qualification(progress: dict) -> dict:
    """Evaluate the transparent fixed rules for moving to the next stage."""
    exam_rate = progress.get("latest_exam_rate")
    criteria = {
        "attempts": progress.get("total", 0) >= STAGE_MIN_ATTEMPTS,
        "rate": progress.get("rate", 0.0) >= STAGE_MIN_RATE,
        "exam": exam_rate is not None and exam_rate >= STAGE_MIN_EXAM_RATE,
        "errors": progress.get("active_errors", 0) <= STAGE_MAX_ACTIVE_ERRORS,
    }
    return {
        "qualified": all(criteria.values()),
        "criteria": criteria,
        "requirements": {
            "attempts": STAGE_MIN_ATTEMPTS,
            "rate": STAGE_MIN_RATE,
            "exam": STAGE_MIN_EXAM_RATE,
            "errors": STAGE_MAX_ACTIVE_ERRORS,
        },
    }


def stage_recommendation(profile_id: int) -> dict | None:
    """Recommend the next difficulty stage using transparent fixed rules.

    The function never locks or changes a stage automatically; it only returns
    a recommendation for the UI. The highest earned advancement is returned.
    """
    levels = ["Anfänger", "Fortgeschritten", "Experte"]
    best = None
    for idx, level in enumerate(levels[:-1]):
        progress = stage_progress(profile_id, level)
        qualification = stage_qualification(progress)
        if qualification["qualified"]:
            best = {
                "from_level": level,
                "to_level": levels[idx + 1],
                **progress,
            }
    return best

def wrong_history(profile_id: int, limit: int = 100):
    with connection() as con:
        return con.execute(
            """
            SELECT * FROM attempts
            WHERE profile_id=? AND is_correct=0
            ORDER BY id DESC LIMIT ?
            """,
            (profile_id, limit),
        ).fetchall()


def exam_history(profile_id: int, limit: int = 20):
    with connection() as con:
        return con.execute(
            """
            SELECT id, started_at, finished_at, level, total_questions, correct_count,
                   points, elapsed_seconds, status
            FROM exam_sessions
            WHERE profile_id=? AND status='complete'
            ORDER BY id DESC LIMIT ?
            """,
            (profile_id, limit),
        ).fetchall()


def recent_question_ids(profile_id: int, category: str, level: str, limit: int = 20) -> list[str]:
    """Return recently used question IDs for this profile/category/level.

    Used by the trainer to avoid immediately repeating fixed questions across
    training sessions and exams. No additional personal data is stored.
    """
    with connection() as con:
        rows = con.execute(
            """
            SELECT question_id
            FROM attempts
            WHERE profile_id=? AND category=? AND level=?
            ORDER BY id DESC
            LIMIT ?
            """,
            (profile_id, category, level, int(limit)),
        ).fetchall()
    return [str(row["question_id"]) for row in rows]


BACKUP_FORMAT = "KBMTrainerProfileBackup"
BACKUP_FORMAT_VERSION = 1


def get_profile(profile_id: int):
    with connection() as con:
        return con.execute(
            "SELECT id, name, created_at, last_used_at FROM profiles WHERE id=?",
            (profile_id,),
        ).fetchone()


def profile_name_exists(name: str) -> bool:
    with connection() as con:
        row = con.execute(
            "SELECT 1 FROM profiles WHERE name=? COLLATE NOCASE LIMIT 1",
            (name.strip(),),
        ).fetchone()
    return row is not None


def unique_profile_name(base_name: str) -> str:
    base_name = base_name.strip() or "Importiertes Profil"
    if not profile_name_exists(base_name):
        return base_name
    i = 1
    while True:
        candidate = f"{base_name} (Import {i})"
        if not profile_name_exists(candidate):
            return candidate
        i += 1


def export_profile(profile_id: int, target_path: str | Path, app_version: str = "0.5") -> dict:
    """Export one profile and all data into a portable .kbmbackup file.

    The backup is a ZIP container with a single JSON payload. No cloud or
    network access is used.
    """
    target = Path(target_path)
    profile = get_profile(profile_id)
    if profile is None:
        raise ValueError("Das ausgewählte Profil wurde nicht gefunden.")

    with connection() as con:
        exams = [dict(r) for r in con.execute(
            "SELECT * FROM exam_sessions WHERE profile_id=? ORDER BY id",
            (profile_id,),
        ).fetchall()]
        attempts = [dict(r) for r in con.execute(
            "SELECT * FROM attempts WHERE profile_id=? ORDER BY id",
            (profile_id,),
        ).fetchall()]

    payload = {
        "format": BACKUP_FORMAT,
        "format_version": BACKUP_FORMAT_VERSION,
        "app_version": app_version,
        "exported_at": datetime.now().isoformat(timespec="seconds"),
        "profile": {
            "name": profile["name"],
            "created_at": profile["created_at"],
            "last_used_at": profile["last_used_at"],
        },
        "exam_sessions": exams,
        "attempts": attempts,
    }

    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("profile.json", json.dumps(payload, ensure_ascii=False, indent=2))

    return {
        "name": profile["name"],
        "attempts": len(attempts),
        "exams": len(exams),
        "path": str(target),
    }


def inspect_backup(source_path: str | Path) -> dict:
    source = Path(source_path)
    if not source.exists():
        raise ValueError("Die Sicherungsdatei wurde nicht gefunden.")
    if source.stat().st_size > 100 * 1024 * 1024:
        raise ValueError("Die Sicherungsdatei ist ungewöhnlich groß und wird nicht geöffnet.")
    try:
        with zipfile.ZipFile(source, "r") as zf:
            if "profile.json" not in zf.namelist():
                raise ValueError("Ungültige KBM-Trainer-Sicherung: profile.json fehlt.")
            raw = zf.read("profile.json")
    except zipfile.BadZipFile as exc:
        raise ValueError("Die Datei ist keine gültige KBM-Trainer-Sicherung.") from exc

    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise ValueError("Die Sicherungsdatei enthält keine lesbaren Profildaten.") from exc

    if data.get("format") != BACKUP_FORMAT:
        raise ValueError("Diese Datei ist keine KBM-Trainer-Profilsicherung.")
    if int(data.get("format_version", 0)) > BACKUP_FORMAT_VERSION:
        raise ValueError("Die Sicherung stammt aus einer neueren, derzeit nicht unterstützten Version.")
    profile = data.get("profile") or {}
    if not str(profile.get("name", "")).strip():
        raise ValueError("In der Sicherung fehlt der Profilname.")
    if not isinstance(data.get("attempts", []), list) or not isinstance(data.get("exam_sessions", []), list):
        raise ValueError("Die Sicherungsdatei ist beschädigt oder unvollständig.")
    return data


def import_profile(source_path: str | Path, imported_name: str | None = None) -> dict:
    """Import a portable profile backup as a new local profile.

    Existing profiles are never overwritten. The caller can provide a unique
    imported_name, otherwise a collision-safe name is generated automatically.
    """
    data = inspect_backup(source_path)
    profile = data["profile"]
    original_name = str(profile["name"]).strip()
    new_name = (imported_name or unique_profile_name(original_name)).strip()
    if not new_name:
        raise ValueError("Der Profilname darf nicht leer sein.")
    if profile_name_exists(new_name):
        raise ValueError(f"Ein Profil mit dem Namen „{new_name}“ existiert bereits.")

    now = datetime.now().isoformat(timespec="seconds")
    created_at = str(profile.get("created_at") or now)

    with connection() as con:
        cur = con.execute(
            "INSERT INTO profiles(name, created_at, last_used_at) VALUES (?, ?, ?)",
            (new_name, created_at, now),
        )
        new_profile_id = int(cur.lastrowid)

        session_map: dict[int, int] = {}
        for row in data.get("exam_sessions", []):
            old_id = row.get("id")
            c = con.execute(
                """
                INSERT INTO exam_sessions(
                    profile_id, started_at, finished_at, level, total_questions,
                    correct_count, points, elapsed_seconds, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    new_profile_id,
                    row.get("started_at") or now,
                    row.get("finished_at"),
                    row.get("level") or "Anfänger",
                    int(row.get("total_questions") or 0),
                    int(row.get("correct_count") or 0),
                    int(row.get("points") or 0),
                    float(row.get("elapsed_seconds") or 0),
                    row.get("status") or "complete",
                ),
            )
            if old_id is not None:
                session_map[int(old_id)] = int(c.lastrowid)

        for row in data.get("attempts", []):
            old_session = row.get("session_id")
            new_session = session_map.get(int(old_session)) if old_session is not None else None
            con.execute(
                """
                INSERT INTO attempts(
                    profile_id, created_at, mode, category, topic, level,
                    question_id, prompt, user_answer, correct_answer, explanation,
                    is_correct, elapsed_seconds, hints_used, points, session_id,
                    question_kind, options_json, hint
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    new_profile_id,
                    row.get("created_at") or now,
                    row.get("mode") or "training",
                    row.get("category") or "Unbekannt",
                    row.get("topic") or "Allgemein",
                    row.get("level") or "Anfänger",
                    row.get("question_id") or "imported",
                    row.get("prompt") or "",
                    row.get("user_answer"),
                    row.get("correct_answer") or "",
                    row.get("explanation"),
                    1 if int(row.get("is_correct") or 0) else 0,
                    float(row.get("elapsed_seconds") or 0),
                    int(row.get("hints_used") or 0),
                    int(row.get("points") or 0),
                    new_session,
                    row.get("question_kind"),
                    row.get("options_json"),
                    row.get("hint"),
                ),
            )

    return {
        "profile_id": new_profile_id,
        "name": new_name,
        "original_name": original_name,
        "attempts": len(data.get("attempts", [])),
        "exams": len(data.get("exam_sessions", [])),
    }
