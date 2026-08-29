import json
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"


def load_course(course_id: str) -> dict:
    return json.loads((DATA_DIR / "courses" / f"{course_id}.json").read_text())


def load_persona(persona_id: str) -> dict:
    return json.loads((DATA_DIR / "personas" / f"{persona_id}.json").read_text())


def save_draft(name: str, payload: dict) -> Path:
    path = OUTPUT_DIR / "drafts" / f"{name}.json"
    path.write_text(json.dumps(payload, indent=2))
    return path


def save_idea_assessment(name: str, payload: dict) -> Path:
    path = OUTPUT_DIR / "ideas" / f"{name}.json"
    path.write_text(json.dumps(payload, indent=2))
    return path


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
