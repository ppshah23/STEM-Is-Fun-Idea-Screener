import sys
from datetime import datetime, timezone
from pathlib import Path

from . import io, steps


def screen_idea(idea_text: str) -> tuple[dict, Path]:
    """Assess a raw idea and save the assessment. Shared by the CLI and the web API."""
    assessment = steps.assess_idea_feasibility(idea_text)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    name = f"{timestamp}_{io.slugify(idea_text)}"
    path = io.save_idea_assessment(name, {"idea": idea_text, "assessment": assessment})
    return assessment, path


def classify_level(idea_text: str) -> tuple[dict, Path]:
    """Classify which of the 3 levels this prompter message falls into.
    Shared by the CLI and the web API. Kept separate from screen_idea --
    feasibility scoring doesn't apply to Level 3 (review) input."""
    classification = steps.classify_idea_level(idea_text)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    name = f"{timestamp}_{io.slugify(idea_text)}"
    path = io.save_level_classification(name, {"idea": idea_text, "classification": classification})
    return classification, path


def review_curriculum(curriculum_text: str, constraints: str | None = None) -> tuple[dict, Path]:
    """Level-3 flow: feedback on an already-completed curriculum/project.
    Shared by the CLI and the web API."""
    review = steps.review_curriculum(curriculum_text, constraints)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    name = f"{timestamp}_{io.slugify(curriculum_text)}"
    path = io.save_curriculum_review(
        name, {"curriculum": curriculum_text, "constraints": constraints, "review": review}
    )
    return review, path


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
