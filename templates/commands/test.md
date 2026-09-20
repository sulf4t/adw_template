# Test Suite

Run the repository's checks in order and return the results as JSON. A workflow script parses your answer with JSON.parse, so the answer must be the JSON array and nothing else.

## Variables
TEST_COMMAND_TIMEOUT: 5 minutes

## Instructions
- Run each test in the `Test Execution Sequence`, in order, from the repository root. Run `pwd` before each command.
- If the sequence below is empty or only contains the example, discover the project's own checks from `README.md` and the package manifest (`make test`, `npm test`, `bun test`, `uv run pytest`, `go test ./...`) and run them as tests named `discovered_<tool>`.
- Stop at the first failing test. Return the results gathered so far, the failing one first.
- A non-zero exit code is a failure. Put the last 30 lines of stderr or stdout in `error`.
- `execution_command` must be the exact command another agent can re-run from the repository root.
- IMPORTANT: Return ONLY the JSON array. No prose, no markdown fences.

## Test Execution Sequence

<!-- One block per check. Add, remove or edit blocks freely; keep the fields.

1. **Python syntax**
   - Command: `uv run python -m py_compile src/*.py`
   - test_name: "python_syntax"
   - test_purpose: "Catches syntax errors before anything else runs"

2. **Unit tests**
   - Command: `uv run pytest -q`
   - test_name: "unit_tests"
   - test_purpose: "Validates the behavior of every module"
-->

## Report

Return a JSON array, failed tests first:

```json
[
  {
    "test_name": "string",
    "passed": true,
    "execution_command": "string",
    "test_purpose": "string",
    "error": "optional string, only when passed is false"
  }
]
```
