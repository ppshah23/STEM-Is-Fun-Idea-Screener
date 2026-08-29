import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import io, steps


def _slug(idea_text: str) -> str:
    words = re.findall(r"[a-z0-9]+", idea_text.lower())[:6]
    return "-".join(words) or "idea"


def screen_idea(idea_text: str) -> tuple[dict, Path]:
    """Assess a raw idea and save the assessment. Shared by the CLI and the web API."""
    assessment = steps.assess_idea_feasibility(idea_text)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    name = f"{timestamp}_{_slug(idea_text)}"
    path = io.save_idea_assessment(name, {"idea": idea_text, "assessment": assessment})
    return assessment, path


def screen(idea_text: str) -> Path:
    assessment, path = screen_idea(idea_text)

    print(f"Verdict: {assessment.get('verdict', assessment)} ({assessment.get('overall_score', '?')}%)")
    print(f"Summary: {assessment.get('summary', '')}")
    print(f"Full assessment saved: {path}")
    # HUMAN REVIEW GATE -- even a "feasible" verdict just clears the idea for
    # authoring. A human still writes data/courses/<id>.json and
    # data/personas/<id>.json before pipeline.orchestrator can run on it.
    return path


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print('Usage: python -m pipeline.intake "<idea text>"')
        sys.exit(1)

    screen(sys.argv[1])
