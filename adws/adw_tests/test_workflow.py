"""Runtime tests. The agent runner is stubbed: no Claude Code call."""
import json
import os

import pytest
from rich.console import Console

import workflow
from agent import AgentPromptResponse
from workflow import Ctx, StepFailed, json_block, spec_path


def make_ctx(tmp_path, adw_id="abc12345", dry_run=False):
    return Ctx(adw_id=adw_id, model="sonnet", working_dir=str(tmp_path), dry_run=dry_run,
               console=Console(file=open(os.devnull, "w")))


def test_template_returns_report_text_and_writes_summary_under_working_dir(tmp_path, monkeypatch):
    seen = {}

    def stub(request):
        seen["request"] = request
        return AgentPromptResponse(output="specs/chore-abc12345-x.md", success=True, session_id="s1")

    monkeypatch.setattr(workflow, "execute_template", stub)
    ctx = make_ctx(tmp_path)
    out = ctx.template("/chore", ["abc12345", "do x"], agent="planner")
    assert out == "specs/chore-abc12345-x.md"
    assert seen["request"].working_dir == str(tmp_path)
    summary = json.loads((tmp_path / "agents" / "abc12345" / "planner" / "custom_summary_output.json").read_text())
    assert summary["success"] and summary["input"] == "/chore abc12345 do x" and summary["session_id"] == "s1"


def test_parse_is_applied(tmp_path, monkeypatch):
    monkeypatch.setattr(workflow, "execute_template",
                        lambda r: AgentPromptResponse(output="Created plan at: specs/chore-abc12345-add-logging.md", success=True))
    assert make_ctx(tmp_path).template("/chore", ["a"], parse=spec_path) == "specs/chore-abc12345-add-logging.md"


def test_failure_raises_step_failed(tmp_path, monkeypatch):
    monkeypatch.setattr(workflow, "execute_template", lambda r: AgentPromptResponse(output="boom", success=False))
    with pytest.raises(StepFailed, match="boom"):
        make_ctx(tmp_path).template("/implement", ["x"])


def test_failure_not_required_returns_output(tmp_path, monkeypatch):
    monkeypatch.setattr(workflow, "execute_template", lambda r: AgentPromptResponse(output="boom", success=False))
    assert make_ctx(tmp_path).template("/implement", ["x"], required=False) == "boom"


def test_unparseable_output_raises_step_failed(tmp_path, monkeypatch):
    monkeypatch.setattr(workflow, "execute_template", lambda r: AgentPromptResponse(output="I did it", success=True))
    with pytest.raises(StepFailed, match="cannot parse"):
        make_ctx(tmp_path).template("/chore", ["a"], parse=spec_path)


def test_dry_run_calls_nothing_and_returns_dry_value(tmp_path, monkeypatch):
    def boom(request):
        raise AssertionError("must not be called")

    monkeypatch.setattr(workflow, "execute_template", boom)
    ctx = make_ctx(tmp_path, dry_run=True)
    assert ctx.template("/test", [], parse=json_block, dry=[]) == []
    assert ctx.template("/prime", []) == "[dry-run] /prime"
    assert ctx.sh(["git", "push"]) == ""


def test_spec_path_and_json_block():
    assert spec_path("done. path: specs/feature-1a2b3c4d-csv-export.md ok") == "specs/feature-1a2b3c4d-csv-export.md"
    assert json_block('```json\n[{"a": 1}]\n```') == [{"a": 1}]
    assert json_block('Here you go:\n{"success": true}\nthanks') == {"success": True}
    with pytest.raises(ValueError):
        json_block("no json here")


def test_save_writes_under_run_dir(tmp_path):
    ctx = make_ctx(tmp_path)
    path = ctx.save("x.json", {"k": 1})
    assert path == tmp_path / "agents" / "abc12345" / "x.json"
    assert json.loads(path.read_text()) == {"k": 1}


def test_step_posts_gh_comment_when_issue_set(tmp_path, monkeypatch):
    monkeypatch.setattr(workflow, "execute_template",
                        lambda r: AgentPromptResponse(output="ok", success=True))
    calls = []
    monkeypatch.setattr(workflow.subprocess, "run", lambda *a, **kw: calls.append((a, kw)))
    ctx = make_ctx(tmp_path)
    ctx.issue = "42"
    ctx.template("/chore", ["a"], agent="planner")
    assert len(calls) == 1
    args, kwargs = calls[0]
    argv = args[0]
    assert argv[:5] == ["gh", "issue", "comment", "42", "--body"]
    body = argv[5]
    assert kwargs["cwd"] == str(tmp_path)
    assert "planner" in body
    assert "succeeded" in body


def test_step_does_not_post_when_issue_not_set(tmp_path, monkeypatch):
    monkeypatch.setattr(workflow, "execute_template",
                        lambda r: AgentPromptResponse(output="ok", success=True))
    calls = []
    monkeypatch.setattr(workflow.subprocess, "run", lambda *a, **kw: calls.append((a, kw)))
    make_ctx(tmp_path).template("/chore", ["a"])
    assert calls == []


def test_step_does_not_post_in_dry_run(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(workflow.subprocess, "run", lambda *a, **kw: calls.append((a, kw)))
    ctx = make_ctx(tmp_path, dry_run=True)
    ctx.issue = "42"
    ctx.template("/chore", ["a"])
    assert calls == []


def test_gh_comment_failure_does_not_raise(tmp_path, monkeypatch):
    monkeypatch.setattr(workflow, "execute_template",
                        lambda r: AgentPromptResponse(output="ok", success=True))

    def boom(*a, **kw):
        raise OSError("gh not found")

    monkeypatch.setattr(workflow.subprocess, "run", boom)
    ctx = make_ctx(tmp_path)
    ctx.issue = "42"
    assert ctx.template("/chore", ["a"]) == "ok"
