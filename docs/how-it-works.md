# How it works

The README (sections 2 and 5) has the short version. This page is the long one for people who want to change the kit itself.

## One call, end to end

```
adw chore "Add a CONTRIBUTING.md"
  |
  | adw.zsh: uv run ~/adw/adws/adw_plan.py chore --working-dir $PWD "Add a CONTRIBUTING.md"
  v
adw_plan.py: workflow(ctx, "chore", "Add a CONTRIBUTING.md")
  |
  | ctx.template("/chore", [adw_id, prompt], agent="planner", parse=spec_path)
  v
workflow.py Ctx.template
  |  builds AgentTemplateRequest, calls agent.execute_template
  v
agent.py execute_template
  |  runs: claude -p "/chore <adw_id> Add a CONTRIBUTING.md" --model sonnet --output-format stream-json --verbose --dangerously-skip-permissions
  |  cwd = the repo, so Claude Code loads <repo>/.claude/commands/chore.md
  |  stdout -> <repo>/agents/<adw_id>/planner/cc_raw_output.jsonl
  v
result message (last JSONL line) -> AgentPromptResponse(output=<the Report text>, success, session_id)
  |
  | Ctx.template: writes custom_summary_output.json, applies parse -> "specs/chore-<id>-add-contributing.md"
  v
adw_plan.py prints the path; run() writes agents/<adw_id>/workflow_summary.json and exits 0
```

## What each layer owns

| Layer | File | Owns | Never does |
|---|---|---|---|
| Shell | `adw.zsh` | command names, aliases, `--working-dir $PWD` | logic |
| Workflow script | `adws/adw_<phase>.py` | the sequence of template calls, retries, what to parse | shell, subprocess, console formatting |
| Runtime | `adws/adw_modules/workflow.py` | CLI flags, adw_id, console, summaries, `ctx.sh`, parsers | anything phase-specific |
| Runner | `adws/adw_modules/agent.py` | invoking the Claude Code CLI, retry codes, JSONL parsing | knowing which phase is running |
| Template | `<repo>/.claude/commands/<name>.md` | what the agent does at one step, and the exact shape of its Report | calling other workflows |

## The contract between a script and a template

A script sends `/<name> arg1 arg2 ...`. Claude Code replaces `$1`, `$2` (or `$ARGUMENTS`) in the template. The template ends with `## Report`, which says exactly what to return: a path, a JSON object, a JSON array, one word. The script parses that with `spec_path`, `json_block` or its own function. If the Report format changes, the parser changes with it. That is the only coupling.

## Dry run

`--dry-run` replaces every agent call with a placeholder and every `ctx.sh` call with a printed command. Use it to check a new script's sequence before spending tokens.

## Retries

- `agent.py` retries the CLI call up to 3 times on transient errors (timeout, CLI error).
- `adw_test.py` re-runs the suite up to 4 times, calling `/resolve_failed_test` for each failure in between.
- `adw_review.py` re-runs the review up to 2 times, calling `/patch` then `/implement` for each blocker in between.
- `adw_full.py` stops at the first phase that raises `StepFailed`. The branch and the files stay; nothing is pushed.
