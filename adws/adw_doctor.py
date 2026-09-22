#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["python-dotenv", "rich"]
# ///
"""Check that everything ADW needs is installed. Exit 1 if a required tool is missing.

    adw doctor
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

KIT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(KIT_ROOT / ".env")

CHECKS = [
    ("git", ["git", "--version"], True),
    ("uv", ["uv", "--version"], True),
    ("claude", [os.getenv("CLAUDE_CODE_PATH", "claude"), "--version"], True),
    ("gh", ["gh", "--version"], True),
    ("gh auth", ["gh", "auth", "status"], False),
]


def probe(cmd):
    if not shutil.which(cmd[0]):
        return False, "not found on PATH"
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    except Exception as e:
        return False, str(e)
    text = (out.stdout or out.stderr).strip().splitlines()
    return out.returncode == 0, (text[0] if text else "")


def main():
    console = Console()
    table = Table(show_header=True)
    table.add_column("Check", style="bold")
    table.add_column("Status")
    table.add_column("Detail", style="dim")
    missing = []
    for name, cmd, required in CHECKS:
        ok, detail = probe(cmd)
        status = "[green]ok[/green]" if ok else ("[red]missing[/red]" if required else "[yellow]warn[/yellow]")
        table.add_row(name, status, detail[:80])
        if required and not ok:
            missing.append(name)
    key = os.getenv("ANTHROPIC_API_KEY")
    table.add_row("ANTHROPIC_API_KEY", "[green]set[/green]" if key else "[yellow]not set[/yellow]",
                  f"from {KIT_ROOT / '.env'}" if key else "Claude Code will use its own login (claude login)")
    runner = os.getenv("ADW_RUNNER", "claude")
    table.add_row("ADW_RUNNER", "[green]claude[/green]" if runner == "claude" else f"[red]{runner}[/red]",
                  "" if runner == "claude" else "only 'claude' is implemented")
    table.add_row("ADW_MODEL", os.getenv("ADW_MODEL", "sonnet"), "default model (planning always uses fable)")
    console.print(table)
    if missing:
        console.print(f"[bold red]Missing:[/bold red] {', '.join(missing)}. See README section 3.")
        sys.exit(1)
    console.print("[bold green]All good.[/bold green]")


if __name__ == "__main__":
    main()
