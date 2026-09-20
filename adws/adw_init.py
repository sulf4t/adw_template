#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pydantic", "python-dotenv", "click", "rich"]
# ///
"""Prepare the current repo for ADW: copy the prompt templates, create specs/, ignore agents/, then /install and /prime.

    adw init               (= adwi)
    adw init --no-agent    (files only, no Claude Code call)
"""
import os
import shutil
import sys
from pathlib import Path

import click

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "adw_modules"))
from workflow import run

KIT_ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = KIT_ROOT / "templates" / "commands"
GITIGNORE_SNIPPET = KIT_ROOT / "templates" / "gitignore.snippet"


def install_templates(working_dir: str):
    """Copy templates into <repo>/.claude/commands/ without overwriting. Returns (copied, skipped)."""
    repo = Path(working_dir)
    commands = repo / ".claude" / "commands"
    copied, skipped = [], []
    for src in sorted(TEMPLATES.rglob("*.md")):
        rel = src.relative_to(TEMPLATES)
        dst = commands / rel
        if dst.exists():
            skipped.append(str(rel))
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied.append(str(rel))
    (repo / "specs").mkdir(exist_ok=True)
    gitignore = repo / ".gitignore"
    existing = gitignore.read_text() if gitignore.exists() else ""
    lines = [l for l in GITIGNORE_SNIPPET.read_text().splitlines() if l.strip() and l not in existing.splitlines()]
    if lines:
        with gitignore.open("a") as f:
            if existing and not existing.endswith("\n"):
                f.write("\n")
            f.write("\n".join(lines) + "\n")
    return copied, skipped


def workflow(ctx, no_agent=False):
    """Install the agentic layer in this repo, then let the agent install dependencies and read the code."""
    copied, skipped = install_templates(ctx.working_dir)
    ctx.console.print(f"[green]{len(copied)} template(s) copied[/green] to .claude/commands/, {len(skipped)} already there (kept as is)")
    for name in copied:
        ctx.console.print(f"  + .claude/commands/{name}")
    ctx.console.print("specs/ ready, agents/ ignored in .gitignore")
    if no_agent:
        return
    ctx.template("/install", [], agent="installer")
    ctx.template("/prime", [], agent="primer")


if __name__ == "__main__":
    run(workflow, click.option("--no-agent", is_flag=True, help="Copy files only, do not call Claude Code."))
