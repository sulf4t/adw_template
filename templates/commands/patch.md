# Patch Plan

Create a small, focused plan that resolves one review issue. Nothing else.

## Variables
adw_id: $1
review_change_request: $2
spec_path: $3 (may be `none`)

## Instructions
- Read `spec_path` if given, for context. The `review_change_request` is what must be fixed.
- Run `git diff --stat` to see what exists. Plan the minimal change.
- Write the plan to `specs/patch/patch-{adw_id}-{descriptive-name}.md` (create the directory if needed).
- Replace every `<placeholder>` in the `Plan Format`.

## Plan Format

```md
# Patch: <title>

## Metadata
adw_id: `{adw_id}`
review_change_request: `{review_change_request}`
spec: `{spec_path}`

## Issue
<the problem, in two sentences>

## Fix
<the change, in two sentences>

## Files to Modify
<one bullet per file, with the exact change>

## Step by Step Tasks
### 1. <task>
### 2. <validate>

## Validation Commands
<exact commands>
```

## Report
Return ONLY the path to the patch plan file you created, nothing else.
