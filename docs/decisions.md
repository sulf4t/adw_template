# Decisions

Short notes on choices that are easy to question later.

## One kit for all repos, templates copied per repo
The scripts live once in `~/adw`. The prompt templates are copied into each repo by `adw init` and committed there. Reason: the scripts are generic, the prompts are not (`test.md` lists this repo's test commands, `prime.md` its entry points). Copying rather than symlinking means a repo's standards survive kit upgrades and are visible to everyone who clones the repo. Cost: kit template improvements do not propagate automatically; re-run `adw init` and diff.

## Markdown templates, not Python prompts
A template is a file a non-developer can read and edit in the browser on GitHub. Its `## Report` section is the API. Keeping prompts out of Python keeps the scripts short and lets the team change how the agent works without a code review of the kit.

## One shared runtime instead of the course's copy-paste
The Tactical Agentic Coding course grows each script by copying the previous one (400 lines of plumbing per phase). `workflow.py` holds that plumbing once. A phase script is 20 to 60 lines and only describes the sequence. See the README, section 5.4.

## Outputs go to the repo, not the kit
`agents/<adw_id>/` is written under `--working-dir` (the repo), gitignored there. The course wrote it next to the scripts, which breaks as soon as the scripts are shared between repos.

## No zero touch (no auto-merge)
`adw ship` opens a pull request and stops. A human merges. This is deliberate for a healthcare codebase and for teams new to agentic development.

## uv single-file scripts
Each script declares its dependencies in a PEP 723 header. No virtualenv to manage, no install step: `uv run` resolves and caches. The kit's own tests pass the same dependencies to pytest (`scripts/test.sh`).

## Sonnet by default
Planning and building with `sonnet` is fast and cheap enough for most tasks. `--model opus` or `ADW_MODEL=opus` for hard ones. The model is one flag; the runner (which CLI) is one file (`agent.py`).
