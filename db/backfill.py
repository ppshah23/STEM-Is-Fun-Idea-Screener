"""Backfill the Postgres mirror from output/ (the actual source of truth).

Safe to re-run: every table is keyed on the output filename stem and upserted
via ON CONFLICT, so this never duplicates rows -- it just resyncs the mirror
to whatever is currently on disk.

Usage:
    python -m db.backfill            # backfill everything
    python -m db.backfill ideas      # backfill just one output/ subfolder
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import psycopg2.extras

from . import get_connection

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"

# UTC timestamp prefix written by pipeline.io.timestamped_name(), e.g.
# "20260101T000000Z_build-a-robot.json" -> "20260101T000000Z".
_TIMESTAMP_RE = re.compile(r"^(\d{8}T\d{6}Z)_")


def _parse_timestamp(stem: str, fallback_mtime: float) -> datetime:
    match = _TIMESTAMP_RE.match(stem)
    if not match:
        return datetime.fromtimestamp(fallback_mtime, tz=timezone.utc)
    return datetime.strptime(match.group(1), "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)


def _upsert(cur, table: str, row: dict) -> None:
    columns = list(row.keys())
    placeholders = ", ".join(["%s"] * len(columns))
    updates = ", ".join(f"{c} = EXCLUDED.{c}" for c in columns if c != "id")
    sql = (
        f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders}) "
        f"ON CONFLICT (id) DO UPDATE SET {updates}"
    )
    cur.execute(sql, [psycopg2.extras.Json(v) if isinstance(v, (list, dict)) else v for v in row.values()])


def backfill_ideas(cur) -> int:
    count = 0
    for path in sorted((OUTPUT_DIR / "ideas").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        a = data["assessment"]
        try:
            _upsert(cur, "ideas", {
                "id": path.stem,
                "idea_text": data["idea"],
                "summary": a["summary"],
                "verdict": a["verdict"],
                "overall_score": a["overall_score"],
                "safety_override": a["safety_override"],
                "checks": a["checks"],
                "blocking_issues": a["blocking_issues"],
                "open_questions": a["open_questions"],
                "suggested_changes": a["suggested_changes"],
                "suggested_parts": a.get("suggested_parts", []),
                "mock": a.get("mock", False),
                "created_at": _parse_timestamp(path.stem, path.stat().st_mtime),
            })
        except KeyError as e:
            print(f"  skipping {path.name}: missing {e} (older output shape)")
            continue
        count += 1
    return count


def backfill_levels(cur) -> int:
    count = 0
    levels_dir = OUTPUT_DIR / "levels"
    if not levels_dir.is_dir():
        return 0
    for path in sorted(levels_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        c = data["classification"]
        try:
            _upsert(cur, "levels", {
                "id": path.stem,
                "idea_text": data["idea"],
                "summary": c["summary"],
                "level": c["level"],
                "level_label": c["level_label"],
                "existing_artifact_override": c["existing_artifact_override"],
                "matrix": c["matrix"],
                "signals": c["signals"],
                "mock": c.get("mock", False),
                "created_at": _parse_timestamp(path.stem, path.stat().st_mtime),
            })
        except KeyError as e:
            print(f"  skipping {path.name}: missing {e} (older output shape)")
            continue
        count += 1
    return count


def backfill_reviews(cur) -> int:
    count = 0
    reviews_dir = OUTPUT_DIR / "reviews"
    if not reviews_dir.is_dir():
        return 0
    for path in sorted(reviews_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        r = data["review"]
        try:
            _upsert(cur, "reviews", {
                "id": path.stem,
                "curriculum_text": data["curriculum"],
                "constraints": data.get("constraints"),
                "summary": r["summary"],
                "strengths": r["strengths"],
                "cut_candidates": r["cut_candidates"],
                "add_candidates": r["add_candidates"],
                "adjust_candidates": r["adjust_candidates"],
                "open_questions": r["open_questions"],
                "restructured_outline": r["restructured_outline"],
                "created_at": _parse_timestamp(path.stem, path.stat().st_mtime),
            })
        except KeyError as e:
            print(f"  skipping {path.name}: missing {e} (older output shape)")
            continue
        count += 1
    return count


def backfill_roadmaps(cur) -> int:
    count = 0
    for path in sorted((OUTPUT_DIR / "roadmaps").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        r = data["roadmap"]
        try:
            _upsert(cur, "roadmaps", {
                "id": path.stem,
                "idea_text": data["idea"],
                "title": r["title"],
                "total_sessions": r["total_sessions"],
                "session_length_minutes": r["session_length_minutes"],
                "duration_summary": r["duration_summary"],
                "days": r["days"],
                "open_questions": r["open_questions"],
                "shopping_list": r.get("shopping_list", []),
                "created_at": _parse_timestamp(path.stem, path.stat().st_mtime),
            })
        except KeyError as e:
            print(f"  skipping {path.name}: missing {e} (older output shape)")
            continue
        count += 1
    return count


def _backfill_draft_dir(cur, subdir: str, status: str) -> int:
    count = 0
    draft_dir = OUTPUT_DIR / subdir
    if not draft_dir.is_dir():
        return 0
    for path in sorted(draft_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        course_id, _, persona_id = path.stem.partition("_")
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        row = {
            "id": path.stem,
            "course_id": course_id or None,
            "persona_id": persona_id or None,
            "status": status,
            "analysis": data.get("analysis"),
            "lesson_plan": data.get("lesson_plan"),
            "slide_outline": data.get("slide_outline"),
            "evaluation": data.get("evaluation"),
            "created_at": mtime,
            "approved_at": mtime if status == "approved" else None,
        }
        _upsert(cur, "drafts", row)
        count += 1
    return count


def backfill_drafts(cur) -> int:
    return _backfill_draft_dir(cur, "drafts", "draft") + _backfill_draft_dir(cur, "approved", "approved")


BACKFILLERS = {
    "ideas": backfill_ideas,
    "levels": backfill_levels,
    "reviews": backfill_reviews,
    "roadmaps": backfill_roadmaps,
    "drafts": backfill_drafts,
}


def run(only: str | None = None) -> None:
    targets = [only] if only else list(BACKFILLERS)
    with get_connection() as conn:
        with conn.cursor() as cur:
            for name in targets:
                fn = BACKFILLERS.get(name)
                if fn is None:
                    print(f"Unknown backfill target: {name!r} (choose from {list(BACKFILLERS)})")
                    sys.exit(1)
                count = fn(cur)
                print(f"{name}: upserted {count} row(s)")


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else None)
