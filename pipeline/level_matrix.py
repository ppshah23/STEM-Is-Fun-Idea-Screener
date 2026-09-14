# Pugh matrix for idea-level classification. Claude scores 5 independent
# signals 0-100 (see skills/idea-level-classification.md); this module turns
# those scores into one of three levels deterministically. Kept separate from
# the model call so the weighting can be tuned without re-prompting -- same
# rationale as pipeline/scoring.py.
#
# Level 1 (Guided) is the datum: the implicit baseline, never computed
# directly. Level 2 (Driven) and Level 3 (Review) are each a candidate scored
# relative to that datum, one weighted row per signal. A candidate only wins
# if its net weighted score beats the datum (> 0); ties and negatives fall
# back to Level 1 by construction.

PUGH_ROWS = {
    "level_2": {  # Driven -- loads onto experience/clarity/ownership/skip-basics
        "existing_artifact": 0,
        "relevant_experience": 25,
        "goal_clarity": 30,
        "decision_ownership": 20,
        "guidance_request": 25,
    },
    "level_3": {  # Review -- only existing_artifact matters, near-binary
        "existing_artifact": 100,
        "relevant_experience": 0,
        "goal_clarity": 0,
        "decision_ownership": 0,
        "guidance_request": 0,
    },
}

HIGH_THRESHOLD = 65  # signal >= this -> +1 relative to the Level-1 datum
LOW_THRESHOLD = 35  # signal <= this -> -1 relative to the Level-1 datum
# 36-64 is a dead zone -> 0 (an ambiguous signal can't swing a candidate)

LEVEL_LABELS = {
    "level_1": "Guided",
    "level_2": "Driven",
    "level_3": "Review",
}


def _relative(score: int) -> int:
    if score >= HIGH_THRESHOLD:
        return 1
    if score <= LOW_THRESHOLD:
        return -1
    return 0


def classify_level(raw_signals: dict) -> dict:
    """
    raw_signals: {dimension: {"score": 0-100, "notes": str}}, one entry per
    LEVEL_SIGNAL_DIMENSIONS in schemas.py (Claude's raw output).

    Returns {"level", "existing_artifact_override", "matrix", "signals"}
    where matrix shows each candidate's per-criterion score/relative/weight
    so the decision is auditable, not just the final answer.
    """
    matrix = {}
    for candidate, weights in PUGH_ROWS.items():
        criteria = {}
        net_score = 0
        for dim, weight in weights.items():
            score = raw_signals[dim]["score"]
            relative = _relative(score)
            weighted = relative * weight
            criteria[dim] = {
                "score": score,
                "relative": relative,
                "weight": weight,
                "weighted": weighted,
            }
            net_score += weighted
        matrix[candidate] = {"criteria": criteria, "net_score": net_score}

    existing_artifact_override = matrix["level_3"]["net_score"] > 0
    if existing_artifact_override:
        level = "level_3"
    elif matrix["level_2"]["net_score"] > 0:
        level = "level_2"
    else:
        level = "level_1"

    return {
        "level": level,
        "level_label": LEVEL_LABELS[level],
        "existing_artifact_override": existing_artifact_override,
        "matrix": matrix,
        "signals": raw_signals,
    }
