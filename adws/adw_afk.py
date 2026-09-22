#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["click"]
# ///
"""AFK mode: poll this repo's open GitHub issues and run `adw full` on each new one.

    adw afk            (every 20 s, Ctrl+C to stop)
    adw afk --once     (one pass, then exit; used by the tests)

Issues already labeled `adw-done`, or whose title contains `[adw skip]`, are ignored.
Requires: gh CLI authenticated, git remote `origin` on GitHub.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import click

HERE = Path(__file__).resolve().parent
DONE_LABEL = "adw-done"
SKIP_MARK = "[adw skip]"


def gh(repo, *args, check=True):
    return subprocess.run(["gh", *args], cwd=repo, capture_output=True, text=True, check=check)


def new_issues(repo):
    out = gh(repo, "issue", "list", "--state", "open", "--json", "number,title,body,labels").stdout
    issues = json.loads(out or "[]")
    return [
        i for i in issues
        if DONE_LABEL not in [l["name"] for l in i["labels"]] and SKIP_MARK not in i["title"].lower()
    ]


def process(repo, issue):
    number = str(issue["number"])
    prompt = f"{issue['title']}\n\n{issue.get('body') or ''}".strip()
    print(f"[adw afk] issue #{number}: {issue['title']}")
    run = subprocess.run(
        ["uv", "run", "--quiet", str(HERE / "adw_full.py"), prompt, "--working-dir", repo, "--issue", number]
    )
    status = "completed" if run.returncode == 0 else f"failed (exit {run.returncode})"
    gh(repo, "issue", "comment", number, "--body", f"ADW workflow {status}.", check=False)
    gh(repo, "issue", "edit", number, "--add-label", DONE_LABEL, check=False)
    print(f"[adw afk] issue #{number} {status}")


@click.command()
@click.option("--working-dir", default=None, help="Repo to watch (default: current directory).")
@click.option("--interval", default=20, show_default=True, help="Seconds between polls.")
@click.option("--once", is_flag=True, help="One pass, then exit.")
def main(working_dir, interval, once):
    repo = working_dir or os.getcwd()
    gh(repo, "label", "create", DONE_LABEL, "--description", "Processed by adw afk", check=False)
    print(f"[adw afk] watching {repo} every {interval}s (Ctrl+C to stop)")
    while True:
        try:
            for issue in new_issues(repo):
                process(repo, issue)
        except subprocess.CalledProcessError as e:
            print(f"[adw afk] gh error: {e.stderr}", file=sys.stderr)
        if once:
            return
        time.sleep(interval)


if __name__ == "__main__":
    main()
