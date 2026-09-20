# Chore Planning

Create a plan to complete the chore, using the `Plan Format` below. Research the codebase first.

## Variables
adw_id: $1
prompt: $2

## Instructions
- If `adw_id` or `prompt` is missing, stop and say so.
- Start by reading `README.md`, then `.claude/commands/conditional_docs.md` and any document it points to for this task.
- The plan must be simple, thorough and precise. Only what the chore needs, nothing more.
- Write the plan to `specs/chore-{adw_id}-{descriptive-name}.md`. `{descriptive-name}` is a short slug, for example `update-readme`, `add-logging`.
- Replace every `<placeholder>` in the `Plan Format`.

## Plan Format

```md
# Chore: <chore name>

## Metadata
adw_id: `{adw_id}`
prompt: `{prompt}`

## Chore Description
<what the chore is, based on the prompt and on what you found in the code>

## Relevant Files
<files to read or change, one bullet each, with why. New files under an h3 'New Files' section>

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. <first task>
- <specific action>

### 2. <second task>
- <specific action>

<last task validates the work>

## Validation Commands
<exact commands to run and what they must show>

## Notes
<optional context>
```

## Report
Return ONLY the path to the plan file you created, nothing else.
