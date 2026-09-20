"""The Claude Code runner, exercised with a fake `claude` binary."""
import os
import stat
import time

import agent
from agent import AgentPromptRequest, RetryCode, prompt_claude_code

RESULT_LINE = '{"type":"result","subtype":"success","is_error":false,"duration_ms":1,"duration_api_ms":1,"num_turns":1,"result":"hello","session_id":"s1","total_cost_usd":0.0}'


def fake_claude(tmp_path, body):
    script = tmp_path / "claude"
    script.write_text(f'#!/bin/bash\nif [ "$1" = "--version" ]; then echo 1.0; exit 0; fi\n{body}\n')
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return str(script)


def request(tmp_path):
    out = tmp_path / "repo" / "agents" / "abc12345" / "oneoff"
    out.mkdir(parents=True)
    return AgentPromptRequest(prompt="hi", adw_id="abc12345", agent_name="oneoff", model="sonnet",
                              dangerously_skip_permissions=True, output_file=str(out / "cc_raw_output.jsonl"),
                              working_dir=str(tmp_path / "repo"))


def test_success_parses_result_line_and_stdin_is_closed(tmp_path, monkeypatch):
    # `cat` blocks until stdin hits EOF: with an open pipe this would hang forever
    monkeypatch.setattr(agent, "CLAUDE_PATH", fake_claude(tmp_path, f"cat > /dev/null; echo '{RESULT_LINE}'"))
    start = time.time()
    response = prompt_claude_code(request(tmp_path))
    assert time.time() - start < 5
    assert response.success and response.output == "hello" and response.session_id == "s1"
    assert (tmp_path / "repo" / "agents" / "abc12345" / "oneoff" / "cc_final_object.json").exists()


def test_timeout_returns_retryable_error(tmp_path, monkeypatch):
    monkeypatch.setattr(agent, "CLAUDE_PATH", fake_claude(tmp_path, "sleep 30"))
    monkeypatch.setattr(agent, "STEP_TIMEOUT", 1)
    start = time.time()
    response = prompt_claude_code(request(tmp_path))
    assert time.time() - start < 5
    assert not response.success and response.retry_code == RetryCode.TIMEOUT_ERROR
    assert "ADW_STEP_TIMEOUT" in response.output


def test_cli_failure_reports_stderr_from_file(tmp_path, monkeypatch):
    monkeypatch.setattr(agent, "CLAUDE_PATH", fake_claude(tmp_path, "echo 'bad flag' >&2; exit 2"))
    response = prompt_claude_code(request(tmp_path))
    assert not response.success and "bad flag" in response.output
    assert (tmp_path / "repo" / "agents" / "abc12345" / "oneoff" / "cc_stderr.log").read_text().strip() == "bad flag"
