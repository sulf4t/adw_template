# Classify a task

Decide which planning template applies to the `Task` below.

## Instructions
- Respond with exactly one line and nothing else.
- `/chore` for maintenance, documentation, configuration, refactoring, dependency updates.
- `/bug` for something that exists and behaves wrongly.
- `/feature` for new behavior or a change in what the product does.
- `0` if the text is not a development task at all.

## Task

$ARGUMENTS

## Report
Return ONLY one of /chore, /bug, /feature or 0, with no backticks, quotes or punctuation.
