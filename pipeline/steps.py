from . import agent, level_matrix, schemas, scoring
from .agent import run_skill
from .skills import load_skill


def assess_idea_feasibility(idea_text: str) -> dict:
    raw = run_skill(
        skill_text=load_skill("idea-feasibility"),
        task=(
            "Score this proposed STEM project idea against each rubric dimension. "
            "The idea is free-form text from a prompter and may be missing "
            "details -- score a dimension low and explain what's missing rather "
            "than assuming a favorable default."
        ),
        context={"idea": idea_text},
        output_schema=schemas.IDEA_FEASIBILITY,
        web_search=True,
    )
    scored = scoring.score_idea_feasibility(raw["checks"])
    return {
        "summary": raw["summary"],
        "verdict": scored["verdict"],
        "overall_score": scored["overall_score"],
        "safety_override": scored["safety_override"],
        "checks": scored["checks"],
        "blocking_issues": raw["blocking_issues"],
        "open_questions": raw["open_questions"],
        "suggested_changes": raw["suggested_changes"],
        "suggested_parts": raw["suggested_parts"],
        "mock": agent.MOCK_MODE,
    }


def draft_curriculum_roadmap(
    idea_text: str, feasibility_notes: dict | None = None, level: str | None = None
) -> dict:
    return run_skill(
        skill_text=load_skill("curriculum-roadmap"),
        task=(
            "Draft a rough day-by-day curriculum roadmap for this idea so the "
            "prompter can see how long it would run and how each session would "
            "unfold, before any detailed course is authored."
        ),
        context={"idea": idea_text, "feasibility_notes": feasibility_notes, "level": level},
        output_schema=schemas.CURRICULUM_ROADMAP,
        web_search=True,
    )


def interview_turn(idea_text: str, transcript: list[dict], level: str | None = None) -> dict:
    """One turn of the pre-roadmap clarifying interview. `transcript` is the
    growing list of {"role": "ai" | "prompter", "message": str} exchanges so
    far -- the caller (CLI or web) owns and resends this each turn."""
    return run_skill(
        skill_text=load_skill("curriculum-interview"),
        task=(
            "Continue this curriculum-planning conversation with the prompter. "
            "Ask exactly one question, or signal you're ready to draft the roadmap."
        ),
        context={"idea": idea_text, "transcript": transcript, "level": level},
        output_schema=schemas.CURRICULUM_INTERVIEW_TURN,
        effort="medium",
    )


def classify_idea_level(idea_text: str) -> dict:
    """Score the prompter's message against the 5 level signals and turn it
    into a Level 1/2/3 routing decision via pipeline.level_matrix."""
    raw = run_skill(
        skill_text=load_skill("idea-level-classification"),
        task=(
            "Score this prompter's message against each of the 5 signals. "
            "Do not decide the level yourself -- score the signals honestly "
            "and let the pipeline route it."
        ),
        context={"idea": idea_text},
        output_schema=schemas.IDEA_LEVEL_SIGNALS,
        effort="medium",
    )
    classification = level_matrix.classify_level(raw["signals"])
    return {
        "summary": raw["summary"],
        **classification,
        "mock": agent.MOCK_MODE,
    }


def review_curriculum(curriculum_text: str, constraints: str | None = None) -> dict:
    """Level-3 flow: feedback on an already-completed curriculum/project.
    Never rewrites the material -- see skills/curriculum-review.md."""
    return run_skill(
        skill_text=load_skill("curriculum-review"),
        task=(
            "Review this already-completed curriculum/project and give pointers "
            "on what to add, cut, or adjust. Do not rewrite any of it."
        ),
        context={"curriculum": curriculum_text, "constraints": constraints},
        output_schema=schemas.CURRICULUM_REVIEW,
    )


def enrich_idea_with_interview(idea_text: str, transcript: list[dict]) -> str:
    """Fold a finished interview transcript into one idea string, so
    draft_curriculum_roadmap can consume it without changing its signature."""
    if not transcript:
        return idea_text
    qa_lines = "\n".join(f"{turn['role']}: {turn['message']}" for turn in transcript)
    return f"{idea_text}\n\nClarifying conversation:\n{qa_lines}"


def analyze_course(course: dict, persona: dict, pedagogy: dict) -> dict:
    return run_skill(
        skill_text=load_skill("curriculum-analysis"),
        task=(
            "Determine what changes are required to make this curriculum "
            "appropriate for this audience without compromising the learning objective."
        ),
        context={"course": course, "persona": persona, "pedagogy": pedagogy},
    )


def adapt_content(course: dict, analysis: dict) -> dict:
    return run_skill(
        skill_text=load_skill("grade-level-adaptation"),
        task="Adapt this course content per the analysis findings.",
        context={"course": course, "analysis": analysis},
    )


def plan_lessons(adapted_course: dict) -> dict:
    return run_skill(
        skill_text=load_skill("lesson-planning"),
        task="Produce a lesson sequence for this adapted course.",
        context={"adapted_course": adapted_course},
    )


def build_slide_outline(lesson_plan: dict) -> dict:
    return run_skill(
        skill_text=load_skill("slide-storytelling"),
        task="Produce a slide-by-slide outline for this lesson plan.",
        context={"lesson_plan": lesson_plan},
    )


def build_worksheet(lesson_plan: dict) -> dict:
    return run_skill(
        skill_text=load_skill("worksheet-generation"),
        task="Produce a worksheet spec that reinforces this lesson plan's objectives.",
        context={"lesson_plan": lesson_plan},
    )


def evaluate_curriculum(lesson_plan: dict, slide_outline: dict, rubric_context: dict) -> dict:
    return run_skill(
        skill_text=load_skill("curriculum-evaluation"),
        task=(
            "Evaluate whether learning objectives and STEM is FUN principles are "
            "preserved. Flag anything that removes productive struggle."
        ),
        context={"lesson_plan": lesson_plan, "slide_outline": slide_outline, **rubric_context},
    )
