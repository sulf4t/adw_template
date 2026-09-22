#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pydantic", "python-dotenv", "click", "rich"]
# ///
"""Write a plan (a spec) with /chore, /feature or /bug. Prints the spec path.

    adw chore "Add a CONTRIBUTING.md"
    adw feature "Export encounters to CSV"
    adw bug "Login form accepts an empty password"
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "adw_modules"))
from workflow import StepFailed, run, spec_path

KINDS = ("chore", "feature", "bug")


def workflow(ctx, kind, prompt):
    """Plan with /<kind>. The template writes specs/<kind>-<adw_id>-<slug>.md and returns its path."""
    kind = kind.lstrip("/")
    if kind not in KINDS:
        raise StepFailed(f"kind must be one of {KINDS}, got {kind!r}")
    spec = ctx.template(f"/{kind}", [ctx.adw_id, prompt], agent="planner", parse=spec_path, dry="specs/dry-run.md", model="fable")
    ctx.console.print(f"[bold]spec:[/bold] {spec}")
    return spec


if __name__ == "__main__":
    run(workflow)
