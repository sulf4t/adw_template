# ADW: AI Developer Workflows

Write a GitHub issue. Get a pull request with a plan, the code, the test results and a review, without anyone sitting in front of a prompt.

ADW is a small kit (Python scripts + markdown prompt templates + a zsh helper) that runs an AI coding agent through a fixed, repeatable development workflow on **whatever repo you are standing in**. Install it once, use it on Osler, on your side projects, on anything with a git remote.

```
you                     ADW                                   your repo
 |                       |                                       |
 |  adw full "Add CSV export to the encounters page"             |
 |---------------------->|                                       |
 |                       |  plan   -> specs/feature-3f9a2c1d-csv-export.md
 |                       |  build  -> code changes on branch adw/3f9a2c1d-csv-export
 |                       |  test   -> runs the repo test suite, fixes failures (max 4 tries)
 |                       |  review -> checks the diff against the spec
 |                       |  ship   -> commit + push + pull request
 |<----------------------|                                       |
 |  PR #42 ready for your review. Full trace in agents/3f9a2c1d/ |
```

Built from the Tactical Agentic Coding course (IndyDevDan) and the `adw_chore` repo already published at github.com/sulf4t/adw_chore.

---

## 1. Why this exists

### The problem we have today

With Copilot, Cursor or Claude Code, the developer is still the loop:

```
   THE MANUAL LOOP (what we do now)

   +--------+    prompt    +-------+    answer    +--------+
   |  you   | -----------> | agent | -----------> |  you   |
   +--------+              +-------+              +--------+
       ^                                              |
       |            read, judge, re-prompt, wait      |
       +----------------------------------------------+

   - Quality depends on who is prompting and how tired they are.
   - Nothing is reusable: the good prompt from Tuesday is gone on Wednesday.
   - One person = one agent at a time.
   - No trace: what was asked, what was checked, what it cost.
```

### The idea

**Template the engineering, then let a script drive the agent.**

Every step we already do by hand (plan, implement, run the tests, fix the failures, review, commit, open a PR) becomes a markdown file. A Python script chains those files and calls the agent for each one. The agent operates the codebase; you review the PR.

```
   THE ADW LOOP

   +--------+  issue or one line   +------------------+
   |  you   | -------------------> |  adw_full.py     |  deterministic Python
   +--------+                      +--------+---------+
       ^                                    |
       |                                    v
       |        +--------------------------------------------------------+
       |        |  /chore  ->  /implement  ->  /test  ->  /review  ->  /pr |  prompt templates
       |        +--------------------------------------------------------+
       |                                    |
       |                                    v
       |                           +----------------+
       +-------------------------- |  pull request  |  + agents/<id>/ trace
                 review the PR     +----------------+
```

### What is at stake for us (Osler, November demo)

- **A three-person, part-time team** (Zaga on the monorepo, Terry on integration, Edouard on architecture) has to ship demo-grade features on a Next.js + HAPI EHR + orchestration monorepo in weeks. Throughput is the constraint, not ideas.
- **Healthcare code needs a trail.** Every ADW run leaves the spec, the plan, the diff, the test output and the review in `agents/<adw_id>/` and in the PR. That is the audit trail a regulated product will need anyway.
- **Same standard whoever launches it.** Folder structure, commit format, "run the tests before you say done": all of it lives in the templates, not in someone's memory.
- **The model is a plugin.** Planning on a frontier model today, execution on a small local model tomorrow (the Qwen 7B PoC), Copilot in an environment where Claude Code is not allowed. Only the runner changes, never the workflow. This is principle P1 of the LLM selection workflow drafted with Henry and Mehdi.

### What you get, concretely

| Before | After |
|---|---|
| "Can you add X?" in a chat, 40 minutes of back and forth | `adw full "Add X"`, come back to a PR |
| Tests run if someone remembers | `/test` runs the suite every time, and fixes what it broke |
| Standards in a Confluence page nobody reads | Standards in `.claude/commands/*.md`, applied on every run |
| One dev, one agent | N issues in the AFK queue, processed one after the other (parallel worktrees on the roadmap) |
| "What did the AI change?" | `agents/<adw_id>/` has the full transcript, the final message and the cost |

---

## 2. How it works

### Two layers

```
   +----------------------------------------------------------------------+
   |  AGENTIC LAYER  (this kit + a few files copied into your repo)       |
   |                                                                      |
   |   .claude/commands/*.md    what the agent must do at each step       |
   |   specs/*.md               the plans the agent writes and follows    |
   |   adws/*.py                the scripts that chain the steps          |
   |   agents/<adw_id>/         everything each run produced              |
   |                                                                      |
   |   +--------------------------------------------------------------+   |
   |   |  APPLICATION LAYER  (your actual code)                       |   |
   |   |                                                              |   |
   |   |   apps/  packages/  Makefile  tests/  docker-compose.yml     |   |
   |   +--------------------------------------------------------------+   |
   +----------------------------------------------------------------------+
```

The agentic layer never contains business logic. It contains **instructions about how to work on the business logic**.

### Where each file lives, and what calls what

Two places. The kit is cloned once. Each repo gets its own copy of the prompt templates.

```
   ~/adw/  (the kit, cloned once, git pull to update)   your-repo/  (one per project, committed with the code)
   ├── adw.zsh                                          ├── .claude/commands/
   ├── adws/                                            │   ├── test.md      <- copied by adw init,
   │   ├── adw_test.py        the .py files             │   ├── prime.md        then edited by you
   │   ├── adw_full.py                                  │   └── ...          the .md files
   │   └── adw_modules/agent.py                         ├── specs/           <- written by the agent
   └── templates/commands/                              └── agents/          <- run outputs, gitignored
       └── test.md  (defaults)
```

What happens when you type `adwt` inside `~/code/osler`:

```
   adwt
    |  adw.zsh
    v
   uv run ~/adw/adws/adw_test.py --working-dir ~/code/osler
    |  the .py: builds the request, loops, parses the JSON
    v
   claude -p "/test"   executed INSIDE ~/code/osler
    |  Claude Code looks up the slash command in the current repo
    v
   ~/code/osler/.claude/commands/test.md   <- the prompt the agent actually receives
    |
    v
   the agent runs each command listed in test.md and returns JSON
    |
    v
   adw_test.py reads the JSON. A failure? It calls /resolve_failed_test, then /test again (max 4).
   Writes agents/<adw_id>/test_runner/. Exits 0 or 1.
```

The `.py` decides the sequence and the retries. The `.md` decides what the agent does at one step.
You change `.md` files in your repo. You change or add `.py` files in `~/adw` (a git clone: branch, edit, PR to the kit).

Every phase script is this skeleton, nothing more:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pydantic", "python-dotenv", "click", "rich"]
# ///
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "adw_modules"))
from workflow import run


def workflow(ctx, spec=""):
    """Write app_docs/feature-<id>.md from the diff and the spec."""
    doc = ctx.template("/document", [ctx.adw_id, spec], agent="documenter")  # reads <repo>/.claude/commands/document.md
    ctx.console.print(f"doc: {doc}")                                          # whatever the template's ## Report returned


if __name__ == "__main__":
    run(workflow)   # gives you --model, --working-dir, --dry-run, the adw_id, the summaries and the exit code
```

`ctx.template()` calls the CLI, retries, saves the transcript under `agents/<adw_id>/documenter/`, and raises if the step fails, which stops the chain.

The matching `document.md` is plain text: "read `git diff`, write `app_docs/feature-<id>.md`, return only the path". No code in it.

### Three primitives

| Primitive | Lives in | What it is | Example |
|---|---|---|---|
| **Prompt template** | `.claude/commands/<name>.md` | A slash command. Markdown with `$1`, `$2` placeholders, a fixed output format, and a `## Report` section that says exactly what to return | `chore.md` returns the path of the plan it wrote |
| **Spec** | `specs/<type>-<adw_id>-<slug>.md` | The plan the planning agent writes. Files to touch, ordered tasks, validation commands. The building agent reads it and does only that | `specs/feature-3f9a2c1d-csv-export.md` |
| **Workflow** | `adws/adw_<name>.py` | A Python script that calls the agent once per template, parses the `Report`, passes the result to the next step, stops on failure | `adw_full.py` = chore, implement, test, review, pr |

Every run gets an **adw_id** (8 characters, for example `3f9a2c1d`). It names the spec, the branch, the output folder and the PR, so you can always go from one to the others.

### The pipeline, step by step

```
   input                phase        template               output
   ------------------   ----------   --------------------   ---------------------------------
   "Add CSV export"  -> PLAN      -> /chore or /feature  -> specs/feature-<id>-csv-export.md
                                     or /bug
   spec path         -> BUILD     -> /implement          -> code changes in the working tree
   (nothing)         -> TEST      -> /test               -> JSON: one entry per test, pass/fail
      failed test    -> RESOLVE   -> /resolve_failed_test-> fix, then TEST again (max 4 loops)
   spec path         -> REVIEW    -> /review             -> JSON: success + issues by severity
      blocker        -> PATCH     -> /patch + /implement -> fix, then REVIEW again (max 2 loops)
   (nothing)         -> SHIP      -> /commit, /pull_request -> branch pushed, PR URL
```

Each phase is its own script (`adw_plan.py`, `adw_build.py`, `adw_test.py`, `adw_review.py`, `adw_ship.py`). `adw_full.py` only calls them in order. You can run any phase alone.

### Where the agent's work goes

```
   agents/
   └── 3f9a2c1d/                      one folder per run
       ├── workflow_summary.json      which phases ran, success, plan path, PR URL
       ├── planner/
       │   ├── cc_raw_output.jsonl    full transcript (every tool call)
       │   ├── cc_final_object.json   last message: result text, cost, duration
       │   └── custom_summary_output.json
       ├── test_results.json          what /test returned, one entry per test
       ├── review.json                what /review returned
       ├── builder/       ...
       ├── test_runner/   ...
       └── reviewer/      ...          + review_img/*.png when the UI was checked
```

When something looks wrong, open `cc_final_object.json` first (what the agent concluded), then `cc_raw_output.jsonl` (what it actually did).

---

## 3. Install (5 minutes, once per machine)

Prerequisites: `git`, `gh` (authenticated with `gh auth login`), [uv](https://docs.astral.sh/uv/), and [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (`claude --version` works).

```bash
git clone https://github.com/sulf4t/adw_template.git ~/adw
echo 'source ~/adw/adw.zsh' >> ~/.zshrc
source ~/.zshrc
adw doctor          # checks git, gh, uv, claude and your API key
```

Copy `~/adw/.env.sample` to `~/adw/.env`. Put your `ANTHROPIC_API_KEY` in it, or leave it empty if Claude Code is already logged in on this machine. Nothing else is needed.

### Then, once per repo

```bash
cd ~/code/osler
adwi                # short for: adw init
```

`adw init` does three things in the repo you are standing in (the first call can take a few minutes: the agent installs dependencies and reads the code):

1. Copies the default prompt templates into `.claude/commands/` (only the files that do not exist yet, it never overwrites yours).
2. Creates `specs/` and adds `agents/` to `.gitignore`.
3. Runs `/install` then `/prime`: the agent installs dependencies as described in `install.md`, reads the repo, and prints a summary of what it understood.

After that, commit `.claude/commands/` and `specs/`. They are part of the repo now: this is where the team's standards live.

---

## 4. Use it

### The commands

All commands act on the current directory. `adw` is a zsh function that runs the matching `~/adw/adws/adw_<name>.py` with `--working-dir "$PWD"`.

| Command | Short | What it does | Returns |
|---|---|---|---|
| `adw init` | `adwi` | Install templates in this repo, run `/install` and `/prime`. `--no-agent` copies the files only | summary of the repo |
| `adw prime` | `adwp` | Agent reads the repo (`prime.md`) and summarizes it. Run it when you want to check the agent sees what you see | summary |
| `adw prompt "<text>"` | `adw "<text>"` | One-shot prompt, no template. For questions and throwaway tasks | answer |
| `adw chore "<text>"` | | Plan a small task (docs, refactor, config) | spec path |
| `adw feature "<text>"` | | Plan a feature (user story, phases, tests, acceptance criteria) | spec path |
| `adw bug "<text>"` | | Plan a bug fix (reproduce, root cause, minimal change, regression test) | spec path |
| `adw build specs/<file>.md` | `adwb` | Implement a spec | diff stat |
| `adw test` | `adwt` | Run `test.md`, fix failures, re-run (max 4) | test_results.json |
| `adw review specs/<file>.md` | | Compare the diff to the spec, screenshots if UI, JSON verdict | review.json |
| `adw ship` | | Commit on the `adw/<id>-<slug>` branch, push, open the PR | PR URL |
| `adw full "<text>"` | `adwf` | chore or feature (auto-classified), build, test, review, ship | PR URL |
| `adw afk` | | Poll this repo's open GitHub issues every 20 s and run `adw full` on each new one. Labels them `adw-done`. `--once` does a single pass | runs forever |
| `adw doctor` | | Check prerequisites | |

Options on every command: `--model sonnet|opus` (default `sonnet`, or `ADW_MODEL` in `~/adw/.env`), `--dry-run` (show every step, call nothing), `--issue <number>` (each agent step posts a comment on that GitHub issue; only `adw afk` sets it today), `-h` (help).

### Your first run (10 minutes)

```
   1. cd ~/code/osler && adwp
      -> "This is a monorepo with apps/hapi (EHR), apps/triple-i (orchestration),
          apps/web (Next.js). Local dev via make dev. Tests via make test."
      If the summary is wrong, fix .claude/commands/prime.md (section 5.5) and run again.

   2. adw chore "Add a CONTRIBUTING.md that explains make dev, make seed and make test"
      -> specs/chore-8b1c04e2-add-contributing.md
      Open it. Read the "Step by Step Tasks". This is what will be executed. Edit it if you want.

   3. adwb specs/chore-8b1c04e2-add-contributing.md
      -> CONTRIBUTING.md created, git diff --stat printed

   4. adwt
      -> [{"test_name": "typecheck", "passed": true, ...}, ...]

   5. adw ship
      -> https://github.com/<org>/osler/pull/42

   Same thing in one line: adwf "Add a CONTRIBUTING.md that explains make dev, make seed and make test"
```

### Fire and forget with GitHub issues

```
   +-------------------+       +-----------+       +-------------------------+
   |  GitHub issue #57 | ----> |  adw afk  | ----> |  adw full "<title+body>" |
   |  "Export CSV..."  |  20 s |  (polling)|       |  -> PR, label adw-done   |
   +-------------------+       +-----------+       +-------------------------+
```

Run `adw afk` in a terminal (or a `screen`/`tmux` session) on any machine with the repo cloned. Write issues. Review PRs. Add `[adw skip]` in an issue title to make the agent ignore it. The issue gets a comment per phase as the run progresses, not just a final status comment.

---

## 5. Change it

This is the part most people will touch. The rule: **change a markdown file, not Python**, unless you are adding a new phase.

```
   I want to...                                    Edit this
   ---------------------------------------------   -----------------------------------------
   add or remove a test the agent runs             .claude/commands/test.md
   add a browser (E2E) test                        .claude/commands/e2e/test_<name>.md
   change what a plan looks like                   .claude/commands/chore.md / feature.md / bug.md
   tell the agent what to read first               .claude/commands/prime.md
   change how the repo is set up                   .claude/commands/install.md
   point the agent to docs for a specific topic    .claude/commands/conditional_docs.md
   change the commit or PR format                  .claude/commands/commit.md / pull_request.md
   change the default model                        ~/adw/.env  (ADW_MODEL=sonnet)
   add a new phase or a new chain                  ~/adw/adws/adw_<name>.py + one line in adw.zsh
```

### 5.1 Add a test (2 minutes)

`test.md` is a numbered list of commands. The agent runs them in order, stops at the first failure, and returns JSON. Add a block:

```md
6. **Lint the web app**
   - Preparation Command: None
   - Command: `cd apps/web && bun run lint`
   - test_name: "web_lint"
   - test_purpose: "Catches unused imports and style violations in the Next.js app"
```

That is all. `adwt` picks it up on the next run. Keep the command exact and runnable from the repo root; the `execution_command` field in the output is what the fixing agent will re-run.

Pin your commands early. With an empty sequence the agent discovers the test tool itself, which works but is slower and can pick a different tool from one run to the next (`unittest` today, `pytest` tomorrow). Explicit blocks run the same way every time.

### 5.2 Add an E2E test (5 minutes)

One markdown file per scenario in `.claude/commands/e2e/`. The agent drives a real browser (Playwright MCP) and takes screenshots.

```md
# E2E Test: Encounter CSV export

## User Story
As a clinician I want to export an encounter list to CSV so that I can share it.

## Test Steps
1. Navigate to the `Application URL`
2. Click "Encounters"
3. Take a screenshot of the list
4. Click "Export CSV"
5. **Verify** a file download starts and the toast says "Export ready"
6. Take a screenshot of the toast

## Success Criteria
- The download starts
- The toast is visible
- 2 screenshots are taken
```

Run it with `adw test --e2e e2e/test_csv_export.md`. `adw full` does not run E2E files on its own: the planning templates add the E2E file to the spec's validation commands, so the builder runs it, and you run it again with `adw test --e2e` whenever you want.

### 5.3 Change how the agent plans

`chore.md`, `feature.md` and `bug.md` end with a `## Plan Format` block. That block is the spec the agent will write. Add a section there (for example `## Migration Notes` or `## Security Checklist`) and every future plan will contain it. Keep the `## Report` section untouched: the scripts parse it.

### 5.4 Add a new phase (30 minutes)

Example: a `/document` phase that writes `app_docs/feature-<id>.md` after review.

1. Write `.claude/commands/document.md` in `~/adw/templates/commands/` (copy `review.md`, change the instructions, keep a strict `## Report`).
2. Copy `~/adw/adws/adw_build.py` to `adw_document.py`. Change the template name and what you do with the result. The whole script is about 30 lines: a `workflow(ctx, ...)` function that calls `ctx.template(...)`, and `run(workflow)` at the bottom.
3. Add `document` to the `case` block in `adw.zsh`.
4. Optional: insert it in `adw_full.py` between review and ship.

Convention: **one workflow = one file, one phase = one template, one template = one strict Report format** (a path, or JSON, nothing else). That is what keeps the chain deterministic.

### 5.5 Make the agent understand this repo

`prime.md` lists what the agent reads before doing anything (`git ls-files`, `README.md`, key entry points). If `adwp` gives a bad summary, the fix is there: add the files that matter, remove the noise. For a monorepo, list one entry file per app.

`conditional_docs.md` maps topics to docs: "if the task touches FHIR resources, read `docs/fhir-conventions.md` first". The planning agent checks it on every run.

### 5.6 Change the model or the runner

- Per run: `adw full "..." --model opus`.
- Default: `ADW_MODEL=sonnet` in `~/adw/.env`.
- Runner: `ADW_RUNNER=claude` (default and only one today). A `copilot` runner (GitHub Copilot CLI in programmatic mode, for environments where Claude Code is not allowed) is on the roadmap: same templates, same scripts, different binary. Only `adws/adw_modules/agent.py` knows how to call the CLI.

---

## 6. Repo layout

```
adw_template/
├── README.md                    this file
├── CHANGELOG.md                 one line per pull request, under Unreleased
├── adw.zsh                      the `adw` function and the adwi / adwp / adwb / adwt / adwf aliases
├── .env.sample                  ANTHROPIC_API_KEY, ADW_MODEL, ADW_RUNNER, CLAUDE_CODE_PATH
├── pytest.ini                   kit test config
├── scripts/test.sh              runs the kit tests (no Claude Code call, the runner is stubbed)
│
├── adws/                        workflows (Python, uv single-file scripts, no install step)
│   ├── adw_modules/
│   │   ├── agent.py             the Claude Code runner: builds the CLI call, retries, parses JSONL, writes agents/<id>/
│   │   └── workflow.py          the shared runtime: Ctx.template / Ctx.prompt / Ctx.sh, parsers, run()
│   ├── adw_init.py              copy templates into a repo, run /install + /prime
│   ├── adw_doctor.py            check git, uv, claude, gh
│   ├── adw_prompt.py            one-shot prompt
│   ├── adw_slash_command.py     run any template by name (adw prime uses it)
│   ├── adw_plan.py              /chore, /feature or /bug, prints the spec path
│   ├── adw_build.py             /implement
│   ├── adw_test.py              /test, then /resolve_failed_test loop (max 4); --e2e runs one /test_e2e
│   ├── adw_review.py            /review, then /patch + /implement loop (max 2)
│   ├── adw_ship.py              branch, /commit, push, /pull_request
│   ├── adw_full.py              /classify, plan, branch, build, test, review, ship
│   ├── adw_afk.py               GitHub issue poller
│   └── adw_tests/               tests of the kit itself: test_workflow.py, test_phases.py, test_init.py
│
├── templates/                   what `adw init` copies into a repo
│   ├── commands/
│   │   ├── prime.md  install.md  conditional_docs.md
│   │   ├── classify.md  chore.md  feature.md  bug.md
│   │   ├── implement.md
│   │   ├── test.md  resolve_failed_test.md  test_e2e.md
│   │   ├── review.md  patch.md
│   │   ├── commit.md  pull_request.md
│   │   └── e2e/test_example.md
│   └── gitignore.snippet        the agents/ line
│
└── docs/
    ├── how-it-works.md          one call traced end to end, what each layer owns
    └── decisions.md             why one kit for all repos, why markdown templates, why uv
```

Inside a repo after `adw init`:

```
your-repo/
├── .claude/commands/            copied templates, now yours to edit and commit
├── specs/                       plans written by the agent, committed with the PR
├── agents/                      run outputs, gitignored
└── (your code, untouched)
```

---

## 7. Contribute to the kit

1. Branch from `main`, one change per PR.
2. Templates: keep them short, one job each, a strict `## Report`. If a template returns free text, the next script cannot use it.
3. Scripts: no business logic. A script builds requests, calls the agent, checks the result, saves the summary, exits with a code. Under 150 lines is the target.
4. Run `./scripts/test.sh` and `adw full --dry-run "test"` before opening the PR.
5. Say in the PR what you ran and what you saw. A PR that says "should work" is sent back.
6. Add one line to `CHANGELOG.md` under `Unreleased`.

Roadmap, in order:

- `copilot` runner (bank environments).
- Isolated worktrees (`trees/<adw_id>/`) so several `adw full` run in parallel on the same repo with their own ports.
- Webhook trigger (instant, instead of 20 s polling).
- Small local model for the execution phases, frontier model for planning only.

---

## 8. Glossary

- **ADW**: AI Developer Workflow. A script that chains agent calls through templates.
- **adw_id**: 8-character id of a run. Names the spec, the branch, the output folder, the PR.
- **Template / slash command**: a markdown file in `.claude/commands/`. The agent receives it as its prompt.
- **Spec**: the plan written by the planning phase. The building phase does what the spec says, nothing more.
- **Prime**: the phase where the agent reads the repo before acting.
- **AFK**: away from keyboard. The mode where GitHub issues drive the workflow.
- **Runner**: the piece that knows how to call a given CLI (Claude Code today, Copilot later).
- **ZTE**: zero touch engineering. `adw full` plus auto-merge. Not enabled in this kit on purpose: a human merges.
