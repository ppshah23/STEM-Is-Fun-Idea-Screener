import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"


def slugify(text: str) -> str:
    words = re.findall(r"[a-z0-9]+", text.lower())[:6]
    return "-".join(words) or "idea"


def timestamped_name(text: str) -> str:
    """Output filename stem: UTC timestamp + slug, e.g. 20260101T000000Z_build-a-robot."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{timestamp}_{slugify(text)}"


def load_course(course_id: str) -> dict:
    return json.loads((DATA_DIR / "courses" / f"{course_id}.json").read_text(encoding="utf-8"))


def load_persona(persona_id: str) -> dict:
    return json.loads((DATA_DIR / "personas" / f"{persona_id}.json").read_text(encoding="utf-8"))


def _save_json(subdir: str, name: str, payload: dict) -> Path:
    path = OUTPUT_DIR / subdir / f"{name}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def save_draft(name: str, payload: dict) -> Path:
    return _save_json("drafts", name, payload)


def save_idea_assessment(name: str, payload: dict) -> Path:
    return _save_json("ideas", name, payload)


def save_level_classification(name: str, payload: dict) -> Path:
    return _save_json("levels", name, payload)


def save_curriculum_review(name: str, payload: dict) -> Path:
    return _save_json("reviews", name, payload)


def render_roadmap_markdown(idea_text: str, roadmap: dict) -> str:
    """Render a curriculum roadmap to a human-readable Markdown document. Pure mechanical work -- no LLM call."""
    lines = [
        f"# {roadmap['title']}",
        "",
        f"> **Source idea:** {idea_text}",
        "",
        f"**{roadmap['total_sessions']} sessions x {roadmap['session_length_minutes']} minutes** "
        f"-- {roadmap['duration_summary']}",
        "",
    ]

    if roadmap["shopping_list"]:
        lines.append("## Shopping list")
        lines.append("")
        for item in roadmap["shopping_list"]:
            lines.append(f"- **{item['name']}** -- {item['note']} ([link]({item['url']}))")
        lines.append("")

    for day in roadmap["days"]:
        lines.append(f"## Day {day['day']}: {day['title']}")
        lines.append("")
        lines.append(day["summary"])
        lines.append("")
        if day["key_activities"]:
            lines.append("**Activities:**")
            lines.extend(f"- {a}" for a in day["key_activities"])
            lines.append("")
        if day["materials"]:
            lines.append("**Materials:**")
            lines.extend(f"- {m}" for m in day["materials"])
            lines.append("")

    if roadmap["open_questions"]:
        lines.append("## Open questions")
        lines.append("")
        lines.extend(f"- {q}" for q in roadmap["open_questions"])
        lines.append("")

    return "\n".join(lines)


def save_roadmap(name: str, idea_text: str, roadmap: dict) -> Path:
    """Save both the structured roadmap (for any later pipeline step) and its
    rendered Markdown (the actual prompter-facing deliverable)."""
    json_path = OUTPUT_DIR / "roadmaps" / f"{name}.json"
    md_path = OUTPUT_DIR / "roadmaps" / f"{name}.md"
    json_path.write_text(
        json.dumps({"idea": idea_text, "roadmap": roadmap}, indent=2), encoding="utf-8"
    )
    md_path.write_text(render_roadmap_markdown(idea_text, roadmap), encoding="utf-8")
    return md_path


def approve_draft(name: str) -> Path:
    """Move a reviewed draft into output/approved/, unblocking the render step."""
    src = OUTPUT_DIR / "drafts" / f"{name}.json"
    dst = OUTPUT_DIR / "approved" / f"{name}.json"
    shutil.move(str(src), str(dst))
    return dst


def export_pptx(slide_outline: dict, out_path: Path) -> None:
    """Render an approved slide outline to a .pptx file. Pure mechanical work -- no LLM call."""
    # from pptx import Presentation
    # ... build the deck from slide_outline here ...
    raise NotImplementedError("Wire up python-pptx rendering here")


def export_worksheet(worksheet_spec: dict, out_path: Path) -> None:
    """Render an approved worksheet spec to a file (docx/pdf). Pure mechanical work -- no LLM call."""
    raise NotImplementedError("Wire up worksheet rendering here")
