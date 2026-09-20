# E2E Test Runner

Execute one end-to-end test file with browser automation (Playwright MCP server) and return the result as JSON.

## Variables
adw_id: $1
agent_name: $2 (default `e2e_runner`)
e2e_test_file: $3
application_url: read it from `README.md` or `.env.sample` if the test file does not give one; default `http://localhost:5173`

## Instructions
- Start the application the way `README.md` says, in the background, if it is not already running.
- Read `e2e_test_file`. Understand the `User Story`, then execute the `Test Steps` in order with the browser.
- Every step that says **Verify** is an assertion. If it fails, stop, mark the test failed and say which step failed and why, for example `(Step 4) button "Export CSV" not found on http://localhost:5173/encounters`.
- Save every screenshot under `agents/{adw_id}/{agent_name}/img/<test file stem>/NN_<description>.png`, using absolute paths.
- Check the `Success Criteria` at the end.
- IMPORTANT: Return ONLY the JSON object below. No prose, no markdown fences.

## Report

```json
{
  "test_name": "string",
  "status": "passed or failed",
  "screenshots": ["absolute path", "..."],
  "error": null
}
```
