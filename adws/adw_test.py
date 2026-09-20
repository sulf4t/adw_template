#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pydantic", "python-dotenv", "click", "rich"]
# ///
"""Run the repo test suite through /test, fix failures with /resolve_failed_test, re-run.

    adw test                                  (max 4 attempts)
    adw test --e2e e2e/test_csv_export.md     (one browser test through /test_e2e)
"""
import json
import os
import sys

import click

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "adw_modules"))
from workflow import StepFailed, json_block, run

MAX_ATTEMPTS = 4


def parse_tests(text):
    data = json_block(text)
    if not isinstance(data, list):
        raise ValueError("/test must return a JSON array")
    return data


def workflow(ctx, e2e=None):
    """Run every test listed in .claude/commands/test.md. Failures are handed to /resolve_failed_test, then the suite runs again."""
    if e2e:
        return run_e2e(ctx, e2e)
    for attempt in range(1, MAX_ATTEMPTS + 1):
        results = ctx.template("/test", [], agent="test_runner", parse=parse_tests, dry=[])
        ctx.save("test_results.json", results)
        failed = [t for t in results if not t.get("passed")]
        if not failed:
            ctx.console.print(f"[bold green]{len(results)} test(s) passed[/bold green]")
            return results
        names = ", ".join(t.get("test_name", "?") for t in failed)
        ctx.console.print(f"[yellow]{len(failed)} failed (attempt {attempt}/{MAX_ATTEMPTS}): {names}[/yellow]")
        if attempt == MAX_ATTEMPTS:
            raise StepFailed(f"still failing after {MAX_ATTEMPTS} attempts: {names}")
        for test in failed:
            ctx.template("/resolve_failed_test", [json.dumps(test)], agent=f"test_resolver_{attempt}")


def run_e2e(ctx, e2e_file):
    result = ctx.template(
        "/test_e2e", [ctx.adw_id, "e2e_runner", e2e_file], agent="e2e_runner",
        parse=json_block, dry={"test_name": e2e_file, "status": "passed", "screenshots": [], "error": None},
    )
    ctx.save("e2e_results.json", result)
    if result.get("status") != "passed":
        raise StepFailed(f"E2E {e2e_file} failed: {result.get('error')}")
    ctx.console.print(f"[bold green]E2E passed:[/bold green] {result.get('test_name')}")
    return result


if __name__ == "__main__":
    run(workflow, click.option("--e2e", default=None, help="Run one E2E test file (.claude/commands/e2e/...) instead of the suite."))
