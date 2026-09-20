#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pydantic", "python-dotenv", "click", "rich"]
# ///
"""Run an adhoc Claude Code prompt in the current repo.

    adw "Explain how the login flow works"
    uv run adws/adw_prompt.py "Write a hello world script" --model opus
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "adw_modules"))
from workflow import run


def workflow(ctx, prompt):
    """Run one prompt, no template."""
    ctx.prompt(prompt)


if __name__ == "__main__":
    run(workflow)
