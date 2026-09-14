"""Plain-assert tests for pipeline.level_matrix -- a pure function, so these
run with no Anthropic API key and no test framework dependency.

Run with: python tests/test_level_matrix.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.level_matrix import classify_level  # noqa: E402


def _signals(**overrides) -> dict:
    """All 5 signals default to 50 (dead zone) unless overridden."""
    dims = ["existing_artifact", "relevant_experience", "goal_clarity", "decision_ownership", "guidance_request"]
    return {dim: {"score": overrides.get(dim, 50), "notes": "test"} for dim in dims}


def test_all_dead_zone_falls_back_to_datum():
    result = classify_level(_signals())
    assert result["level"] == "level_1", result


def test_existing_artifact_short_circuits_to_level_3():
    result = classify_level(
        _signals(
            existing_artifact=80,
            relevant_experience=90,
            goal_clarity=90,
            decision_ownership=90,
            guidance_request=90,
        )
    )
    assert result["level"] == "level_3", result
    assert result["existing_artifact_override"] is True


def test_high_driven_signals_without_artifact_gives_level_2():
    result = classify_level(
        _signals(
            existing_artifact=50,
            relevant_experience=80,
            goal_clarity=80,
            decision_ownership=80,
            guidance_request=80,
        )
    )
    assert result["level"] == "level_2", result
    assert result["existing_artifact_override"] is False


def test_thresholds_are_inclusive():
    assert classify_level(_signals(relevant_experience=65, goal_clarity=65, decision_ownership=65, guidance_request=65))[
        "matrix"
    ]["level_2"]["criteria"]["relevant_experience"]["relative"] == 1
    assert classify_level(_signals(relevant_experience=35, goal_clarity=35, decision_ownership=35, guidance_request=35))[
        "matrix"
    ]["level_2"]["criteria"]["relevant_experience"]["relative"] == -1


def test_low_existing_artifact_does_not_suppress_level_2():
    result = classify_level(
        _signals(
            existing_artifact=20,
            relevant_experience=80,
            goal_clarity=80,
            decision_ownership=80,
            guidance_request=80,
        )
    )
    assert result["level"] == "level_2", result
    # existing_artifact has weight 0 in the level_2 row -- its score shouldn't matter at all.
    assert result["matrix"]["level_2"]["criteria"]["existing_artifact"]["weighted"] == 0


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for test in tests:
        test()
        print(f"PASS: {test.__name__}")
    print(f"\n{len(tests)} tests passed.")
