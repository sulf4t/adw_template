# Feature Planning

Create a plan to implement the feature, using the `Plan Format` below. Research the codebase first.

## Variables
adw_id: $1
prompt: $2

## Instructions
- If `adw_id` or `prompt` is missing, stop and say so.
- Start by reading `README.md`, then `.claude/commands/conditional_docs.md` and any document it points to for this task.
- Think hard about requirements, design and the existing patterns of this codebase. Follow them.
- Write the plan to `specs/feature-{adw_id}-{descriptive-name}.md`. `{descriptive-name}` is a short slug, for example `csv-export`, `retry-logic`.
- If the feature has a user interface, add a task that creates an E2E test file in `.claude/commands/e2e/test_<name>.md` modeled on `.claude/commands/e2e/test_example.md`, and list it in the validation commands.
- Replace every `<placeholder>` in the `Plan Format`.

## Plan Format

```md
# Feature: <feature name>

## Metadata
adw_id: `{adw_id}`
prompt: `{prompt}`

## Feature Description
<what the feature does and why it is valuable>

## User Story
As a <type of user>
I want to <action>
So that <benefit>

## Problem Statement
<the specific problem or opportunity>

## Solution Statement
<the approach and how it solves the problem>

## Relevant Files
<files to read or change, one bullet each, with why. New files under an h3 'New Files' section>

## Implementation Plan
### Phase 1: Foundation
### Phase 2: Core Implementation
### Phase 3: Integration

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. <first task>
- <specific action>

### 2. <second task>
- <specific action>

<include writing tests as you go; last task validates the work>

## Testing Strategy
### Unit Tests
### Edge Cases

## Acceptance Criteria
<specific, measurable criteria>

## Validation Commands
<exact commands to run and what they must show>

## Notes
<optional context; new libraries and how to add them>
```

## Report
Return ONLY the path to the plan file you created, nothing else.
