#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pydantic", "python-dotenv", "click", "rich"]
# ///
"""Run one slash command from <repo>/.claude/commands/ with its arguments.

    adw prime                       (= /prime)
    uv run adws/adw_slash_command.py /implement specs/chore-xxx.md
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "adw_modules"))
from workflow import run


def workflow(ctx, slash_command, *args):
    """Run one slash command with its arguments."""
    ctx.template(slash_command, args)


if __name__ == "__main__":
    run(workflow)
