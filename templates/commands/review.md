# Review

Review the work done against a spec file. The question is not "does it work" (tests answer that) but "is this what was asked". Return the result as JSON.

## Variables
adw_id: $1
spec_file: $2
agent_name: $3 (default `reviewer`)
review_image_dir: `<absolute repo path>/agents/{adw_id}/{agent_name}/review_img/`

## Instructions
- Run `git branch --show-current` and `git diff origin/main` (or `origin/master`) to see the changes. Read `spec_file`.
- Compare the diff with every requirement and acceptance criterion in the spec.
- If the change has a user interface and a Playwright MCP server is available: start the application as `README.md` describes, navigate to the critical path, and take 1 to 5 screenshots into `review_image_dir` named `01_<description>.png`, `02_...`. Screenshot every issue you find. Otherwise, review the diff only and leave `screenshots` empty.
- Severity:
  - `blocker`: the work does not do what the spec asked, or would harm the user. Must be fixed before release.
  - `tech_debt`: releasable, but will cost later.
  - `skippable`: minor.
- Report only issues that matter. Think hard about impact before calling something a blocker.
- IMPORTANT: Return ONLY the JSON object below. No prose, no markdown fences.

## Report

```json
{
  "success": true,
  "review_summary": "2 to 4 sentences: what was built and whether it matches the spec, as said in a standup",
  "review_issues": [
    {
      "review_issue_number": 1,
      "screenshot_path": "absolute path or empty string",
      "issue_description": "string",
      "issue_resolution": "string",
      "issue_severity": "blocker | tech_debt | skippable"
    }
  ],
  "screenshots": ["absolute path", "..."]
}
```

`success` is `false` only when at least one issue is a `blocker`.
