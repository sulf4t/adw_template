# Commit

Stage and commit the current changes with a well-formed message.

## Variables
adw_id: $1
spec: $2 (path to the spec that drove the work, or `none`)

## Instructions
- Run `git status --porcelain` and `git diff HEAD --stat`. If there is nothing to commit, say so and stop.
- Read `spec` if it is a file, to describe the change accurately.
- Never stage `.env`, credentials, or anything under `agents/`.
- Message format, first line 50 characters or less, present tense, no period:
  `<type>: <what changed>` where `<type>` is `feat`, `fix`, `chore`, `docs`, `test` or `refactor`.
- Body: one or two lines on why, then a blank line, then `ADW: {adw_id}` and `Spec: {spec}`.

## Run
1. `git add -A`
2. `git reset -q -- .env agents 2>/dev/null` (in case they were staged)
3. `git commit -m "<first line>" -m "<body>"`

## Report
Return ONLY the first line of the commit message, nothing else.
