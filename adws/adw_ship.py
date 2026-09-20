#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pydantic", "python-dotenv", "click", "rich"]
# ///
"""Commit on an adw/<id>-<slug> branch, push, open the pull request. Prints the PR URL.

    adw ship                                   (branch from the current changes)
    adw ship specs/chore-3f9a2c1d-add-docs.md  (spec gives the branch slug and the PR context)
"""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "adw_modules"))
from workflow import run

DEFAULT_BRANCHES = ("main", "master", "")


def slug(spec: str) -> str:
    """specs/chore-3f9a2c1d-add-logging.md -> add-logging"""
    stem = Path(spec).stem if spec else ""
    stem = re.sub(r"^(chore|feature|bug|patch)-[0-9a-f]{8}-", "", stem)
    return re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-") or "changes"


def ensure_branch(ctx, spec: str = "") -> str:
    """Stay on the current feature branch, or create adw/<id>-<slug> when on main."""
    current = ctx.sh(["git", "rev-parse", "--abbrev-ref", "HEAD"]).strip()
    if current not in DEFAULT_BRANCHES:
        return current
    branch = f"adw/{ctx.adw_id}-{slug(spec)}"
    ctx.sh(["git", "checkout", "-b", branch])
    return branch


def workflow(ctx, spec=""):
    """Branch if needed, /commit, push, /pull_request."""
    branch = ensure_branch(ctx, spec)
    ctx.template("/commit", [ctx.adw_id, spec or "none"], agent="committer")
    ctx.sh(["git", "push", "-u", "origin", branch])
    url = ctx.template("/pull_request", [branch, spec or "none", ctx.adw_id], agent="pr_creator",
                       parse=str.strip, dry="https://github.com/example/repo/pull/0")
    ctx.console.print(f"[bold green]PR:[/bold green] {url}")
    return url


if __name__ == "__main__":
    run(workflow)
