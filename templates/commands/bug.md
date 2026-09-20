# Bug Planning

Create a plan to fix the bug, using the `Plan Format` below. Reproduce it before planning.

## Variables
adw_id: $1
prompt: $2

## Instructions
- If `adw_id` or `prompt` is missing, stop and say so.
- Start by reading `README.md`, then `.claude/commands/conditional_docs.md` and any document it points to for this task.
- Reproduce the bug. Find the root cause. Plan the smallest change that fixes the cause and a test that would have caught it.
- Be surgical: fix this bug, do not fall off track.
- Write the plan to `specs/bug-{adw_id}-{descriptive-name}.md`. `{descriptive-name}` is a short slug, for example `fix-login-error`, `resolve-timeout`.
- If the bug is in a user interface, add a task that creates an E2E test file in `.claude/commands/e2e/test_<name>.md` modeled on `.claude/commands/e2e/test_example.md`.
- Replace every `<placeholder>` in the `Plan Format`.

## Plan Format

```md
# Bug: <bug name>

## Metadata
adw_id: `{adw_id}`
prompt: `{prompt}`

## Bug Description
<symptoms, expected behavior, actual behavior>

## Steps to Reproduce
<exact steps or command>

## Root Cause Analysis
<what is wrong and where, with file and line>

## Solution Statement
<the minimal fix and the regression test>

## Relevant Files
<files to read or change, one bullet each, with why>

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. <write the failing test>
### 2. <fix>
### 3. <validate>

## Validation Commands
<exact commands to run and what they must show>

## Notes
<optional context>
```

## Report
Return ONLY the path to the plan file you created, nothing else.
