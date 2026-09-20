#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pydantic", "python-dotenv", "click", "rich"]
# ///
"""Implement a spec with /implement.

    adw build specs/chore-3f9a2c1d-add-contributing.md
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "adw_modules"))
from workflow import StepFailed, run


def workflow(ctx, spec):
    """Read the spec, do what it says, report the diff."""
    if not ctx.dry_run and not Path(ctx.working_dir, spec).exists():
        raise StepFailed(f"spec not found: {spec}")
    return ctx.template("/implement", [spec], agent="builder")


if __name__ == "__main__":
    run(workflow)
