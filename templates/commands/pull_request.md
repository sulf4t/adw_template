# Pull Request

Open a pull request for the current branch.

## Variables
branch_name: $1
spec: $2 (path to the spec that drove the work, or `none`)
adw_id: $3

## Instructions
- Find the default branch: `git remote show origin | sed -n '/HEAD branch/s/.*: //p'`.
- Run `git log <default>..HEAD --oneline` and `git diff <default>...HEAD --stat` to know what the PR contains.
- Read `spec` if it is a file.
- Title: `<type>: <what changed>` (same type words as commits), 70 characters or less.
- Body, in markdown: a Summary section (3 to 5 lines), a Changes section (bullets from the diff), a Validation section (what was run and its result), then `Spec: <spec>` and `ADW: <adw_id>`.
- Do not merge. Do not enable auto-merge. A human merges.

## Run
1. `gh pr create --base <default> --head <branch_name> --title "<title>" --body "<body>"`
2. If a PR already exists for the branch, run `gh pr view --json url -q .url` instead.

## Report
Return ONLY the pull request URL, nothing else.
