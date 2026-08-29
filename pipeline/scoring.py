# Weighted-dimension decision matrix for idea feasibility. Claude scores each
# dimension 0-100 (see skills/idea-feasibility.md); this module turns those
# scores into one overall percentage and a verdict. Kept deterministic and
# separate from the model call so the weighting can be tuned without
# re-prompting, per this scaffold's design: judgment goes to Claude, the
# pipeline (not the model) decides what the number means.

# Weights sum to 100 across every dimension except "safety", which is a hard
# gate rather than a weighted input -- a safety failure overrides the score
# instead of being averaged away by everything else passing.
WEIGHTS = {
    "pedagogical_alignment": 26,
    "materials_feasibility": 20,
    "instructor_capability": 18,
    "time_scope_fit": 18,
    "ai_assistance_value": 13,
    "grade_level_fit": 5,
}
SAFETY_DIMENSION = "safety"

PASS_THRESHOLD = 60  # score >= this displays as a per-dimension pass
SAFETY_OVERRIDE_CAP = 15  # overall_score ceiling when safety fails

# (score floor, verdict) -- first match wins, evaluated high to low.
VERDICT_BANDS = [
    (85, "feasible"),
    (65, "feasible_with_changes"),
    (40, "needs_more_info"),
    (0, "not_feasible"),
]


def _verdict_for_score(score: float) -> str:
    for floor, verdict in VERDICT_BANDS:
        if score >= floor:
            return verdict
    return "not_feasible"


def score_idea_feasibility(raw_checks: dict) -> dict:
    """
    raw_checks: {dimension: {"score": 0-100, "notes": str}}, one entry per
    CHECK_DIMENSIONS in schemas.py (Claude's raw output).

    Returns {"overall_score", "verdict", "safety_override", "checks"} where
    checks adds "pass" (derived) and "weight" (None for safety) to each entry.
    """
    checks = {}
    weighted_total = 0.0
    for dim, weight in WEIGHTS.items():
        score = raw_checks[dim]["score"]
        checks[dim] = {
            "score": score,
            "pass": score >= PASS_THRESHOLD,
            "notes": raw_checks[dim]["notes"],
            "weight": weight,
        }
        weighted_total += score * weight / 100

    safety_score = raw_checks[SAFETY_DIMENSION]["score"]
    safety_pass = safety_score >= PASS_THRESHOLD
    checks[SAFETY_DIMENSION] = {
        "score": safety_score,
        "pass": safety_pass,
        "notes": raw_checks[SAFETY_DIMENSION]["notes"],
        "weight": None,
    }

    overall_score = round(weighted_total)
    safety_override = not safety_pass
    if safety_override:
        overall_score = min(overall_score, SAFETY_OVERRIDE_CAP)
        verdict = "not_feasible"
    else:
        verdict = _verdict_for_score(overall_score)

    return {
        "overall_score": overall_score,
        "verdict": verdict,
        "safety_override": safety_override,
        "checks": checks,
    }
