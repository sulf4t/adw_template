#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pydantic", "python-dotenv", "click", "rich"]
# ///
"""The whole chain: classify, plan, branch, build, test, review, ship. Prints the PR URL.

    adw full "Add CSV export to the encounters page"
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "adw_modules"))
sys.path.insert(0, HERE)
from workflow import StepFailed, run, spec_path

import adw_build
import adw_review
import adw_ship
import adw_test

KINDS = ("/chore", "/feature", "/bug")


def parse_kind(text: str) -> str:
    kind = text.strip().splitlines()[-1].strip() if text.strip() else ""
    kind = kind.strip("`").strip()
    if kind not in KINDS:
        raise ValueError(f"/classify returned {kind!r}, expected one of {KINDS}")
    return kind


def workflow(ctx, prompt):
    """One prompt in, one pull request out."""
    kind = ctx.template("/classify", [prompt], agent="classifier", parse=parse_kind, dry="/chore")
    spec = ctx.template(kind, [ctx.adw_id, prompt], agent="planner", parse=spec_path, dry="specs/dry-run.md")
    ctx.console.rule(f"[bold]{kind} -> {spec}[/bold]")
    adw_ship.ensure_branch(ctx, spec)
    adw_build.workflow(ctx, spec)
    adw_test.workflow(ctx)
    adw_review.workflow(ctx, spec)
    return adw_ship.workflow(ctx, spec)


if __name__ == "__main__":
    run(workflow)
