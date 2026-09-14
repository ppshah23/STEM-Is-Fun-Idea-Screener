# Shared shape for a real, currently-purchasable part found via web search.
# Used by both IDEA_FEASIBILITY.suggested_parts and CURRICULUM_ROADMAP.shopping_list.
SHOPPING_ITEM = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "url": {"type": "string"},
        "note": {"type": "string"},
    },
    "required": ["name", "url", "note"],
    "additionalProperties": False,
}

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
        "suggested_parts": {
            "type": "array",
            "description": (
                "Real, currently-purchasable hardware parts for this idea, found via "
                "web search. Empty if the idea has no physical build component."
            ),
            "items": SHOPPING_ITEM,
        },
    },
    "required": [
        "summary",
        "checks",
        "blocking_issues",
        "open_questions",
        "suggested_changes",
        "suggested_parts",
    ],
    "additionalProperties": False,
}

# A rough day-by-day preview generated straight from a prompter's idea (and,
# if available, its feasibility screening notes) -- before anyone commits to
# authoring a full course.json. Rendered to Markdown by pipeline.io, not
# consumed by the later detailed pipeline steps.
CURRICULUM_ROADMAP = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "total_sessions": {"type": "integer", "minimum": 1},
        "session_length_minutes": {"type": "integer", "minimum": 1},
        "duration_summary": {"type": "string"},
        "days": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "day": {"type": "integer", "minimum": 1},
                    "title": {"type": "string"},
                    "summary": {"type": "string"},
                    "key_activities": {"type": "array", "items": {"type": "string"}},
                    "materials": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["day", "title", "summary", "key_activities", "materials"],
                "additionalProperties": False,
            },
        },
        "open_questions": {"type": "array", "items": {"type": "string"}},
        "shopping_list": {
            "type": "array",
            "description": (
                "Every part needed for the full build, each with a real purchase "
                "link found via web search. Assume the prompter owns none of it "
                "unless the idea or conversation explicitly says otherwise."
            ),
            "items": SHOPPING_ITEM,
        },
    },
    "required": [
        "title",
        "total_sessions",
        "session_length_minutes",
        "duration_summary",
        "days",
        "open_questions",
        "shopping_list",
    ],
    "additionalProperties": False,
}

LEVEL_SIGNAL_DIMENSIONS = [
    "existing_artifact",
    "relevant_experience",
    "goal_clarity",
    "decision_ownership",
    "guidance_request",
]

# Claude scores each signal 0-100 and explains why. The level itself is NOT
# requested here -- pipeline.level_matrix turns these signals into a level
# deterministically via a Pugh matrix, same rationale as IDEA_FEASIBILITY /
# pipeline.scoring: the weighting stays auditable and tunable without
# re-prompting. See pipeline/level_matrix.py for the matrix.
IDEA_LEVEL_SIGNALS = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "signals": {
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
                for dim in LEVEL_SIGNAL_DIMENSIONS
            },
            "required": LEVEL_SIGNAL_DIMENSIONS,
            "additionalProperties": False,
        },
    },
    "required": ["summary", "signals"],
    "additionalProperties": False,
}

# Shared shape for one review pointer: an observation plus why it matters --
# never rewritten content. Used by CURRICULUM_REVIEW's cut/add/adjust lists.
REVIEW_ITEM = {
    "type": "object",
    "properties": {
        "item": {"type": "string"},
        "reason": {"type": "string"},
    },
    "required": ["item", "reason"],
    "additionalProperties": False,
}

# Kitara-James Google-Slides layout taxonomy -- kept in sync by hand with
# Framework/CURRICULUM_STYLE_GUIDE.md §2, the single source of truth for
# actually building .pptx decks (Framework/Template.pptx). This is "how we
# make our PowerPoints" -- restructured_outline below maps a reviewed
# curriculum directly onto these layout names.
RESTRUCTURED_SLIDE_LAYOUTS = [
    "TITLE_AND_BODY",
    "Statement",
    "Section",
    "Frame Only",
    "Title Only",
    "Agenda Numbered",
    "Title & Bullets",
]

# Generic slide categories from skills/slide-storytelling.md, extended with
# the review-specific ones (review_question, challenge, section_break) so a
# restructured outline speaks the same vocabulary the rest of the pipeline
# already uses for slide content.
RESTRUCTURED_SLIDE_TYPES = [
    "title",
    "hook",
    "review_question",
    "concept",
    "challenge",
    "activity_bridge",
    "section_break",
    "recap",
]

RESTRUCTURED_SLIDE = {
    "type": "object",
    "properties": {
        "order": {"type": "integer", "minimum": 1},
        "layout": {"type": "string", "enum": RESTRUCTURED_SLIDE_LAYOUTS},
        "type": {"type": "string", "enum": RESTRUCTURED_SLIDE_TYPES},
        "title": {"type": "string"},
        "content": {"type": "string"},
        "speaker_notes": {"type": "string"},
        "source_reference": {
            "type": "string",
            "description": (
                "The specific part of the prompter's own submission this slide "
                "reorganizes -- never blank, never a newly invented activity."
            ),
        },
    },
    "required": [
        "order",
        "layout",
        "type",
        "title",
        "content",
        "speaker_notes",
        "source_reference",
    ],
    "additionalProperties": False,
}

RESTRUCTURED_DAY = {
    "type": "object",
    "properties": {
        "day": {"type": "integer", "minimum": 1},
        "title": {"type": "string"},
        "slides": {"type": "array", "items": RESTRUCTURED_SLIDE},
    },
    "required": ["day", "title", "slides"],
    "additionalProperties": False,
}

# Level-3 flow: feedback on an already-completed curriculum/project. See
# skills/curriculum-review.md -- Claude never rewrites the substance of the
# material (that's what strengths/cut/add/adjust are for), but DOES
# reorganize it, unchanged in substance, onto the STEM is FUN house day-arc
# and slide-layout skeleton via restructured_outline.
CURRICULUM_REVIEW = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "strengths": {"type": "array", "items": {"type": "string"}},
        "cut_candidates": {"type": "array", "items": REVIEW_ITEM},
        "add_candidates": {"type": "array", "items": REVIEW_ITEM},
        "adjust_candidates": {"type": "array", "items": REVIEW_ITEM},
        "open_questions": {"type": "array", "items": {"type": "string"}},
        "restructured_outline": {
            "type": "array",
            "description": (
                "The prompter's own content reorganized (not rewritten) onto "
                "the STEM is FUN house day-arc and slide-layout skeleton."
            ),
            "items": RESTRUCTURED_DAY,
        },
    },
    "required": [
        "summary",
        "strengths",
        "cut_candidates",
        "add_candidates",
        "adjust_candidates",
        "open_questions",
        "restructured_outline",
    ],
    "additionalProperties": False,
}

# One turn of the pre-roadmap clarifying interview (see skills/curriculum-interview.md).
# Stateless like every other schema here -- the caller resends the growing
# transcript each turn.
CURRICULUM_INTERVIEW_TURN = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["asking", "ready"]},
        "message": {"type": "string"},
    },
    "required": ["status", "message"],
    "additionalProperties": False,
}
