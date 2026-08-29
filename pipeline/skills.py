from pathlib import Path

SKILLS_DIR = Path(__file__).parent.parent / "skills"


def load_skill(name: str) -> str:
    """Load a skill's Markdown content by filename stem, e.g. load_skill('curriculum-analysis')."""
    return (SKILLS_DIR / f"{name}.md").read_text(encoding="utf-8")
