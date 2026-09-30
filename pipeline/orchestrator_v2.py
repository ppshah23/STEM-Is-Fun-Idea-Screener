"""CLI for curriculum_developer_tool_v2's pipeline, run from inside STEM-Is-Fun-V2.

A new, parallel path alongside the existing orchestrator.py -- that module,
steps.py, and the analyze/adapt/plan/outline/evaluate chain it drives are
untouched. Use this once an idea has cleared pipeline.intake and/or
pipeline.roadmap and a human wants to hand it to v2's Sp/S0-S3 pipeline
instead of (or as well as) the original course/persona-JSON flow.

v2 keeps a human-approval gate on every stage (not one review at the end), so
this CLI mirrors that: each command does one step and stops. Nothing here
auto-approves anything.

Usage:
    python -m pipeline.orchestrator_v2 create-project my_fan --title "Smart Personal Fan" \\
        --product-line explorer --domains arduino,electronics
    python -m pipeline.orchestrator_v2 create-project my_fan --from-roadmap 20260101T000000Z_smart-fan \\
        --product-line explorer --domains arduino,electronics
    python -m pipeline.orchestrator_v2 run-skill S1 --project my_fan --provider anthropic
    python -m pipeline.orchestrator_v2 approve-run --project my_fan S1-abcd1234
    python -m pipeline.orchestrator_v2 run-skill S2 --project my_fan --provider anthropic
    python -m pipeline.orchestrator_v2 approve-run --project my_fan S2-abcd1234
    python -m pipeline.orchestrator_v2 run-skill S3 --project my_fan --lesson lesson1 --provider anthropic
    python -m pipeline.orchestrator_v2 approve-run --project my_fan S3-abcd1234
    python -m pipeline.orchestrator_v2 list-runs --project my_fan

No Anthropic API key? Use --provider fake throughout, and before each of the
S2/S3 run-skill calls, derive that stage's fixture from the prior approved
run with `seed-fixture` (no LLM call, uses v2's own fixture_builder):
    python -m pipeline.orchestrator_v2 run-skill S1 --project my_fan --provider fake
    python -m pipeline.orchestrator_v2 approve-run --project my_fan <S1_run_id>
    python -m pipeline.orchestrator_v2 seed-fixture S2 --project my_fan
    python -m pipeline.orchestrator_v2 run-skill S2 --project my_fan --provider fake
    python -m pipeline.orchestrator_v2 approve-run --project my_fan <S2_run_id>
    python -m pipeline.orchestrator_v2 seed-fixture S3 --project my_fan --lesson lesson1
    python -m pipeline.orchestrator_v2 run-skill S3 --project my_fan --lesson lesson1 --provider fake
    python -m pipeline.orchestrator_v2 approve-run --project my_fan <S3_run_id>
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from dotenv import load_dotenv

from . import io, v2_bridge

# v2's own .env is optional and may not exist; its AnthropicMessagesClient
# just reads os.environ["ANTHROPIC_API_KEY"] directly (no dotenv loading of
# its own), so reuse this project's key for --provider anthropic runs here.
load_dotenv(Path(__file__).parent.parent / ".env")


def _render_saved_roadmap(name: str) -> str:
    """Load a saved pipeline.roadmap output and render it as Markdown for v2's intake.md."""
    path = io.OUTPUT_DIR / "roadmaps" / f"{name}.json"
    if not path.is_file():
        raise FileNotFoundError(f"roadmap not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    return io.render_roadmap_markdown(data["idea"], data["roadmap"])


def cmd_create_project(args: argparse.Namespace) -> int:
    domains = [d.strip() for d in args.domains.split(",") if d.strip()] if args.domains else []

    from_intake: Path | None = None
    title = args.title
    if args.from_roadmap:
        try:
            rendered = _render_saved_roadmap(args.from_roadmap)
        except FileNotFoundError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        if not title:
            # First line of the rendered roadmap markdown is "# <title>".
            title = rendered.splitlines()[0].lstrip("# ").strip()
        tmp = Path(tempfile.gettempdir()) / f"{args.project_id}_roadmap_intake.md"
        tmp.write_text(rendered, encoding="utf-8")
        from_intake = tmp

    if not title:
        print("Error: --title is required unless --from-roadmap supplies one", file=sys.stderr)
        return 1

    try:
        project_dir = v2_bridge.create_project(
            project_id=args.project_id,
            title=title,
            product_line=args.product_line,
            domains=domains,
            pedagogy_profile_id=args.pedagogy,
            from_intake=from_intake,
        )
    except v2_bridge.SkillRunError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Created v2 project at {project_dir}")
    return 0


def cmd_validate_project(args: argparse.Namespace) -> int:
    result = v2_bridge.validate_project(args.project)
    if not result.exists:
        print(f"Project not found: {args.project}")
        return 1
    print(f"Project: {result.slug}")
    if result.missing_files:
        print("Missing:")
        for item in result.missing_files:
            print(f"  - {item}")
    if result.errors:
        print("Errors:")
        for item in result.errors:
            print(f"  - {item}")
    if result.missing_files or result.errors:
        return 1
    print("OK")
    return 0


def cmd_run_skill(args: argparse.Namespace) -> int:
    try:
        record = v2_bridge.run_skill(
            stage_id=args.stage,
            project_slug=args.project,
            provider=args.provider,
            lesson_id=args.lesson,
        )
    except (v2_bridge.SkillRunError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Run {record.id} status={record.status}")
    return 0


def cmd_seed_fixture(args: argparse.Namespace) -> int:
    try:
        path = v2_bridge.seed_next_fixture(
            project_slug=args.project, stage_id=args.stage, lesson_id=args.lesson
        )
    except (v2_bridge.SkillRunError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Seeded fixture: {path}")
    return 0


def cmd_approve_run(args: argparse.Namespace) -> int:
    try:
        record = v2_bridge.approve_run(project_slug=args.project, run_id=args.run_id, approved_by=args.by)
    except (v2_bridge.SkillRunError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Approved {record.id} at {record.approved_at}")
    return 0


def cmd_reject_run(args: argparse.Namespace) -> int:
    try:
        record = v2_bridge.reject_run(project_slug=args.project, run_id=args.run_id)
    except (v2_bridge.SkillRunError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Rejected {record.id}")
    return 0


def cmd_list_runs(args: argparse.Namespace) -> int:
    runs = v2_bridge.list_runs(args.project)
    if not runs:
        print("No runs found.")
        return 0
    for run in runs:
        lesson = f" lesson={run.lesson_id}" if run.lesson_id else ""
        print(f"  {run.id}  stage={run.stage_id}  status={run.status}{lesson}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="orchestrator_v2", description="STEM-Is-Fun-V2 bridge into curriculum_developer_tool_v2"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_create = sub.add_parser("create-project")
    p_create.add_argument("project_id")
    p_create.add_argument("--title")
    p_create.add_argument(
        "--from-roadmap", metavar="NAME", help="Seed from output/roadmaps/<NAME>.json (pipeline.roadmap output)"
    )
    p_create.add_argument("--product-line", required=True, choices=["explorer", "maker", "innovator"])
    p_create.add_argument("--pedagogy", default="stem_is_fun_default")
    p_create.add_argument("--domains", help="Comma-separated domain hints, e.g. arduino,electronics")
    p_create.set_defaults(func=cmd_create_project)

    p_val = sub.add_parser("validate-project")
    p_val.add_argument("project")
    p_val.set_defaults(func=cmd_validate_project)

    p_run = sub.add_parser("run-skill")
    p_run.add_argument("stage")
    p_run.add_argument("--project", required=True)
    p_run.add_argument(
        "--provider",
        default="fake",
        choices=["fake", "anthropic"],
        help="LLM provider (anthropic requires ANTHROPIC_API_KEY in the v2 checkout's .env; supports S1, S2, S3)",
    )
    p_run.add_argument("--lesson")
    p_run.set_defaults(func=cmd_run_skill)

    p_seed = sub.add_parser(
        "seed-fixture",
        help="Derive an S2/S3 fixture from the latest approved upstream run (no LLM call), "
        "so run-skill --provider fake can proceed past S1 without an API key.",
    )
    p_seed.add_argument("stage", choices=["S2", "S3"])
    p_seed.add_argument("--project", required=True)
    p_seed.add_argument("--lesson", help="Required for S3")
    p_seed.set_defaults(func=cmd_seed_fixture)

    p_app = sub.add_parser("approve-run")
    p_app.add_argument("--project", required=True)
    p_app.add_argument("run_id")
    p_app.add_argument("--by", default="local-user")
    p_app.set_defaults(func=cmd_approve_run)

    p_rej = sub.add_parser("reject-run")
    p_rej.add_argument("--project", required=True)
    p_rej.add_argument("run_id")
    p_rej.set_defaults(func=cmd_reject_run)

    p_runs = sub.add_parser("list-runs")
    p_runs.add_argument("--project", required=True)
    p_runs.set_defaults(func=cmd_list_runs)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
