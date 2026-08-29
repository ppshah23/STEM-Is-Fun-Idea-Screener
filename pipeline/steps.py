from . import agent, schemas, scoring
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
        "mock": agent.MOCK_MODE,
    }


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
