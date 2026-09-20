#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pydantic", "python-dotenv", "click", "rich"]
# ///
"""Review the diff against a spec with /review. Blockers are fixed with /patch + /implement, then reviewed again.

    adw review specs/feature-3f9a2c1d-csv-export.md
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "adw_modules"))
from workflow import StepFailed, json_block, run, spec_path

MAX_ATTEMPTS = 2
DRY = {"success": True, "review_summary": "[dry-run]", "review_issues": [], "screenshots": []}


def workflow(ctx, spec):
    """Compare what was built to what the spec asked. Returns the review JSON."""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        result = ctx.template("/review", [ctx.adw_id, spec, "reviewer"], agent="reviewer", parse=json_block, dry=DRY)
        ctx.save("review.json", result)
        ctx.console.print(result.get("review_summary", ""))
        blockers = [i for i in result.get("review_issues", []) if i.get("issue_severity") == "blocker"]
        if not blockers:
            ctx.console.print(f"[bold green]review passed[/bold green] ({len(result.get('review_issues', []))} non-blocking issue(s))")
            return result
        if attempt == MAX_ATTEMPTS:
            raise StepFailed(f"{len(blockers)} blocker(s) remain after {MAX_ATTEMPTS} review passes")
        for n, issue in enumerate(blockers, 1):
            request = f"{issue.get('issue_description', '')} Resolution: {issue.get('issue_resolution', '')}"
            patch = ctx.template("/patch", [ctx.adw_id, request, spec], agent=f"patch_planner_{attempt}_{n}",
                                 parse=spec_path, dry="specs/patch/dry-run.md")
            ctx.template("/implement", [patch], agent=f"patch_builder_{attempt}_{n}")


if __name__ == "__main__":
    run(workflow)
