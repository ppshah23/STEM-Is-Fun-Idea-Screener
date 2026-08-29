from . import io, steps


def run(course_id: str, persona_id: str, pedagogy: dict, rubric_context: dict) -> None:
    course = io.load_course(course_id)
    persona = io.load_persona(persona_id)

    analysis = steps.analyze_course(course, persona, pedagogy)
    adapted = steps.adapt_content(course, analysis)
    lesson_plan = steps.plan_lessons(adapted)
    slide_outline = steps.build_slide_outline(lesson_plan)
    evaluation = steps.evaluate_curriculum(lesson_plan, slide_outline, rubric_context)

    draft_name = f"{course_id}_{persona_id}"
    draft_path = io.save_draft(
        draft_name,
        {
            "analysis": analysis,
            "lesson_plan": lesson_plan,
            "slide_outline": slide_outline,
            "evaluation": evaluation,
        },
    )

    print(f"Draft ready for review: {draft_path}")
    print(f"Evaluation summary: {evaluation.get('summary', evaluation)}")
    # HUMAN REVIEW GATE -- pipeline stops here until a person approves the draft.
    # io.approve_draft(draft_name) moves it to output/approved/, which a separate
    # render step then picks up for export_pptx / export_worksheet.


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python -m pipeline.orchestrator <course_id> <persona_id>")
        sys.exit(1)

    run(
        course_id=sys.argv[1],
        persona_id=sys.argv[2],
        pedagogy={},
        rubric_context={},
    )
