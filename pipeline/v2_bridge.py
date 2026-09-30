"""Bridge into curriculum_developer_tool_v2's engine (Sp/S0-S3 pipeline).

Runs curriculum_developer_tool_v2 in-process, via the editable install in
requirements.txt (`-e ../../curriculum_developer_tool_v2`), rather than
shelling out to its `ce` CLI. This module does not touch anything in
STEM-Is-Fun-V2's existing pipeline/ -- it's a new, separate entry point that
orchestrator_v2.py calls. v2's own approval-gate design (one human review per
stage, not one review at the end) is preserved as-is: this module exposes
each step, it does not auto-approve anything.

Projects and runs created through this bridge live inside the v2 checkout's
own `content/projects/` and `runs/` folders (both gitignored there per its
README), so nothing here touches v2's tracked files either.
"""

from __future__ import annotations

import contextlib
import os
from pathlib import Path

from curriculum_engine.application.errors import SkillRunError
from curriculum_engine.application.fixture_builder import (
    seed_s2_fixture as _seed_s2_fixture,
    seed_s3_fixture as _seed_s3_fixture,
)
from curriculum_engine.application.project_creator import create_project as _create_project
from curriculum_engine.application.project_loader import (
    ProjectValidationResult,
    validate_project as _validate_project,
)
from curriculum_engine.application.skill_runner import (
    approve_skill_run as _approve_skill_run,
    reject_skill_run as _reject_skill_run,
    run_skill as _run_skill,
)
from curriculum_engine.domain.skill_runs import SkillRunRecord
from curriculum_engine.infrastructure.persistence.skill_runs import (
    find_approved_run as _find_approved_run,
    list_skill_runs as _list_skill_runs,
)

__all__ = [
    "SkillRunError",
    "V2_ROOT",
    "approve_run",
    "create_project",
    "list_runs",
    "reject_run",
    "run_skill",
    "seed_next_fixture",
    "validate_project",
]

# Sibling checkout by default (STEM-Is-Fun-V2/ and curriculum_developer_tool_v2/
# under the same parent folder). Override with CURRICULUM_V2_ROOT if the two
# repos aren't checked out next to each other.
V2_ROOT = Path(
    os.environ.get("CURRICULUM_V2_ROOT")
    or Path(__file__).resolve().parents[3] / "curriculum_developer_tool_v2"
)


def create_project(
    *,
    project_id: str,
    title: str,
    product_line: str,
    domains: list[str] | None = None,
    pedagogy_profile_id: str = "stem_is_fun_default",
    from_intake: Path | None = None,
) -> Path:
    """Create a v2 project pack (S0 + S1 fixture envelopes seeded, per v2's create-project)."""
    return _create_project(
        project_id=project_id,
        title=title,
        product_line=product_line,
        pedagogy_profile_id=pedagogy_profile_id,
        domains=domains or [],
        from_intake=from_intake,
        root=V2_ROOT,
    )


def run_skill(
    *,
    stage_id: str,
    project_slug: str,
    provider: str = "fake",
    lesson_id: str | None = None,
) -> SkillRunRecord:
    """Run one v2 stage (Sp/S0-S3). Returns a pending run -- call approve_run to gate it."""
    return _run_skill(
        stage_id=stage_id,
        project_slug=project_slug,
        provider=provider,
        lesson_id=lesson_id,
        root=V2_ROOT,
    )


def approve_run(*, project_slug: str, run_id: str, approved_by: str = "local-user") -> SkillRunRecord:
    return _approve_skill_run(
        project_slug=project_slug, run_id=run_id, approved_by=approved_by, root=V2_ROOT
    )


def reject_run(*, project_slug: str, run_id: str) -> SkillRunRecord:
    return _reject_skill_run(project_slug=project_slug, run_id=run_id, root=V2_ROOT)


def list_runs(project_slug: str) -> list[SkillRunRecord]:
    return _list_skill_runs(project_slug, V2_ROOT)


def validate_project(project_id: str) -> ProjectValidationResult:
    return _validate_project(project_id, V2_ROOT)


@contextlib.contextmanager
def _chdir(path: Path):
    # v2's fixture_builder calls workspace_root() with no args internally
    # (it only threads `root` through to the write path, not the schema
    # lookup), so it falls back to Path.cwd()-based discovery. Since we're
    # invoked from STEM-Is-Fun-V2's cwd, not v2's, hop over there for the call.
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def seed_next_fixture(*, project_slug: str, stage_id: str, lesson_id: str | None = None) -> Path:
    """Derive an S2/S3 fixture from the latest approved upstream run via v2's
    own fixture_builder -- no LLM call. Lets `run_skill(..., provider="fake")`
    work past S1 without an Anthropic API key."""
    if stage_id == "S2":
        upstream = _find_approved_run(project_slug, "S1", root=V2_ROOT)
        if upstream is None or not upstream.output_json:
            raise SkillRunError("No approved S1 run found for this project; approve S1 first")
        with _chdir(V2_ROOT):
            return _seed_s2_fixture(project_id=project_slug, s1_envelope=upstream.output_json, root=V2_ROOT)

    if stage_id == "S3":
        if not lesson_id:
            raise SkillRunError("S3 fixture seeding requires a lesson id")
        upstream = _find_approved_run(project_slug, "S2", root=V2_ROOT)
        if upstream is None or not upstream.output_json:
            raise SkillRunError("No approved S2 run found for this project; approve S2 first")
        with _chdir(V2_ROOT):
            return _seed_s3_fixture(
                project_id=project_slug, lesson_id=lesson_id, s2_envelope=upstream.output_json, root=V2_ROOT
            )

    raise SkillRunError(f"No fixture seeding available for stage {stage_id!r} (only S2 and S3 need it)")
