CHECK_DIMENSIONS = [
    "grade_level_fit",
    "materials_feasibility",
    "instructor_capability",
    "ai_assistance_value",
    "time_scope_fit",
    "safety",
    "pedagogical_alignment",
]

# Claude scores each dimension 0-100 and explains why. The verdict itself is
# NOT requested here -- pipeline.scoring turns these scores into a weighted
# overall score and verdict deterministically, so the weighting is auditable
# and tunable without re-prompting. See pipeline/scoring.py for the weights.
IDEA_FEASIBILITY = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "checks": {
            "type": "object",
            "properties": {
                dim: {
                    "type": "object",
                    "properties": {
                        "score": {"type": "integer", "minimum": 0, "maximum": 100},
                        "notes": {"type": "string"},
                    },
                    "required": ["score", "notes"],
                    "additionalProperties": False,
                }
                for dim in CHECK_DIMENSIONS
            },
            "required": CHECK_DIMENSIONS,
            "additionalProperties": False,
        },
        "blocking_issues": {"type": "array", "items": {"type": "string"}},
        "open_questions": {"type": "array", "items": {"type": "string"}},
        "suggested_changes": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["summary", "checks", "blocking_issues", "open_questions", "suggested_changes"],
    "additionalProperties": False,
}
