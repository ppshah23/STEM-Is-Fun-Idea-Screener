import sys
from pathlib import Path

from . import io, steps


def draft_roadmap(idea_text: str, feasibility_notes: dict | None = None) -> tuple[dict, Path]:
    """Draft a day-by-day curriculum roadmap and save it (JSON + rendered .md).
    Shared by the CLI and any future caller (e.g. chained after pipeline.intake)."""
    roadmap = steps.draft_curriculum_roadmap(idea_text, feasibility_notes)

    path = io.save_roadmap(io.timestamped_name(idea_text), idea_text, roadmap)
    return roadmap, path


def draft(idea_text: str):
    roadmap, path = draft_roadmap(idea_text)

    print(f"{roadmap['title']} -- {roadmap['total_sessions']} sessions x {roadmap['session_length_minutes']} min")
    print(f"Roadmap saved: {path}")
    # HUMAN REVIEW GATE -- this is a rough preview, not an authored course.
    # A human still decides whether to proceed to full authoring from here.
    return path


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print('Usage: python -m pipeline.roadmap "<idea text>"')
        sys.exit(1)

    draft(sys.argv[1])
