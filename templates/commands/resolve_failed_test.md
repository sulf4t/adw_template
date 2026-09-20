# Resolve a failed test

Fix one failing test using the failure details below.

## Instructions
1. Read the test name, purpose, command and error in `Test Failure Input`.
2. Run `git diff --stat` to see recent changes. If a spec in `specs/*.md` relates to them, read it.
3. Reproduce: run the `execution_command` exactly and read the full output.
4. Fix the root cause with the smallest change. Do not change unrelated code and do not weaken the test.
5. Re-run the same `execution_command` until it passes. Do not run the whole suite.

## Test Failure Input
$ARGUMENTS

## Report
- Root cause, in one or two sentences.
- The fix, with the files changed.
- The command you re-ran and its result.
