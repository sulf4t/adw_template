"""Phase scripts, chained with a scripted stub runner. No Claude Code call."""
import json
import os

import pytest
from rich.console import Console

import workflow
from agent import AgentPromptResponse
from workflow import Ctx, StepFailed

import adw_full
import adw_plan
import adw_review
import adw_ship
import adw_test


class Stub:
    """Answers each slash command from a queue of outputs, records every call."""

    def __init__(self, answers):
        self.answers = {k: list(v) for k, v in answers.items()}
        self.calls = []

    def __call__(self, request):
        self.calls.append((request.slash_command, list(request.args), request.agent_name))
        queue = self.answers.get(request.slash_command)
        if not queue:
            raise AssertionError(f"unexpected call {request.slash_command}")
        out = queue.pop(0)
        if isinstance(out, dict) or isinstance(out, list):
            out = json.dumps(out)
        return AgentPromptResponse(output=out, success=True)

    def commands(self):
        return [c[0] for c in self.calls]


def make_ctx(tmp_path):
    return Ctx(adw_id="abc12345", model="sonnet", working_dir=str(tmp_path), console=Console(file=open(os.devnull, "w")))


PASS = [{"test_name": "unit", "passed": True, "execution_command": "pytest", "test_purpose": "p"}]
FAIL = [{"test_name": "unit", "passed": False, "execution_command": "pytest", "test_purpose": "p", "error": "E"}]


def test_plan_rejects_unknown_kind(tmp_path):
    with pytest.raises(StepFailed, match="kind must be one of"):
        adw_plan.workflow(make_ctx(tmp_path), "epic", "x")


def test_test_phase_fixes_then_passes(tmp_path, monkeypatch):
    stub = Stub({"/test": [FAIL, FAIL, PASS], "/resolve_failed_test": ["fixed", "fixed"]})
    monkeypatch.setattr(workflow, "execute_template", stub)
    results = adw_test.workflow(make_ctx(tmp_path))
    assert results == PASS
    assert stub.commands() == ["/test", "/resolve_failed_test", "/test", "/resolve_failed_test", "/test"]
    assert json.loads(stub.calls[1][1][0])["test_name"] == "unit"
    assert json.loads((tmp_path / "agents" / "abc12345" / "test_results.json").read_text()) == PASS


def test_test_phase_gives_up_after_four_attempts(tmp_path, monkeypatch):
    stub = Stub({"/test": [FAIL] * 4, "/resolve_failed_test": ["tried"] * 3})
    monkeypatch.setattr(workflow, "execute_template", stub)
    with pytest.raises(StepFailed, match="still failing after 4 attempts: unit"):
        adw_test.workflow(make_ctx(tmp_path))
    assert stub.commands().count("/test") == 4 and stub.commands().count("/resolve_failed_test") == 3


def test_e2e_option_runs_one_file(tmp_path, monkeypatch):
    stub = Stub({"/test_e2e": [{"test_name": "csv", "status": "passed", "screenshots": [], "error": None}]})
    monkeypatch.setattr(workflow, "execute_template", stub)
    result = adw_test.workflow(make_ctx(tmp_path), e2e="e2e/test_csv.md")
    assert result["status"] == "passed"
    assert stub.calls[0][1] == ["abc12345", "e2e_runner", "e2e/test_csv.md"]


def test_review_patches_blockers_then_passes(tmp_path, monkeypatch):
    blocker = {"review_issue_number": 1, "screenshot_path": "", "issue_description": "button missing",
               "issue_resolution": "add it", "issue_severity": "blocker"}
    stub = Stub({
        "/review": [{"success": False, "review_summary": "nope", "review_issues": [blocker], "screenshots": []},
                    {"success": True, "review_summary": "ok", "review_issues": [], "screenshots": []}],
        "/patch": ["specs/patch/patch-abc12345-add-button.md"],
        "/implement": ["done"],
    })
    monkeypatch.setattr(workflow, "execute_template", stub)
    result = adw_review.workflow(make_ctx(tmp_path), "specs/feature-abc12345-x.md")
    assert result["success"] is True
    assert stub.commands() == ["/review", "/patch", "/implement", "/review"]
    assert stub.calls[2][1] == ["specs/patch/patch-abc12345-add-button.md"]


def test_review_gives_up_after_two_passes(tmp_path, monkeypatch):
    blocker = {"issue_description": "x", "issue_resolution": "y", "issue_severity": "blocker"}
    bad = {"success": False, "review_summary": "nope", "review_issues": [blocker], "screenshots": []}
    stub = Stub({"/review": [bad, bad], "/patch": ["specs/patch/p.md"], "/implement": ["done"]})
    monkeypatch.setattr(workflow, "execute_template", stub)
    with pytest.raises(StepFailed, match="1 blocker\\(s\\) remain after 2 review passes"):
        adw_review.workflow(make_ctx(tmp_path), "specs/x.md")


def test_ship_branches_from_main_commits_pushes_and_opens_pr(tmp_path, monkeypatch):
    stub = Stub({"/commit": ["chore: add docs"], "/pull_request": ["https://github.com/o/r/pull/7\n"]})
    monkeypatch.setattr(workflow, "execute_template", stub)
    shell = []

    def fake_sh(self, cmd, check=True):
        shell.append(cmd)
        return "main\n" if cmd[:2] == ["git", "rev-parse"] else ""

    monkeypatch.setattr(Ctx, "sh", fake_sh)
    url = adw_ship.workflow(make_ctx(tmp_path), "specs/chore-abc12345-add-docs.md")
    assert url == "https://github.com/o/r/pull/7"
    assert ["git", "checkout", "-b", "adw/abc12345-add-docs"] in shell
    assert ["git", "push", "-u", "origin", "adw/abc12345-add-docs"] in shell
    assert stub.commands() == ["/commit", "/pull_request"]


def test_ship_keeps_existing_feature_branch(tmp_path, monkeypatch):
    stub = Stub({"/commit": ["fix: x"], "/pull_request": ["https://github.com/o/r/pull/8"]})
    monkeypatch.setattr(workflow, "execute_template", stub)
    shell = []
    monkeypatch.setattr(Ctx, "sh", lambda self, cmd, check=True: (shell.append(cmd), "feat/x\n")[1])
    adw_ship.workflow(make_ctx(tmp_path))
    assert not any(c[:2] == ["git", "checkout"] for c in shell)
    assert ["git", "push", "-u", "origin", "feat/x"] in shell


def test_slug():
    assert adw_ship.slug("specs/chore-3f9a2c1d-add-logging.md") == "add-logging"
    assert adw_ship.slug("specs/Some Thing.md") == "some-thing"
    assert adw_ship.slug("") == "changes"


def test_full_runs_every_phase_in_order(tmp_path, monkeypatch):
    stub = Stub({
        "/classify": ["/feature"],
        "/feature": ["specs/feature-abc12345-csv-export.md"],
        "/implement": ["done"],
        "/test": [PASS],
        "/review": [{"success": True, "review_summary": "ok", "review_issues": [], "screenshots": []}],
        "/commit": ["feat: csv export"],
        "/pull_request": ["https://github.com/o/r/pull/42"],
    })
    monkeypatch.setattr(workflow, "execute_template", stub)
    shell = []
    monkeypatch.setattr(Ctx, "sh", lambda self, cmd, check=True: (shell.append(cmd), "main\n" if cmd[:2] == ["git", "rev-parse"] else "")[1])
    monkeypatch.setattr("pathlib.Path.exists", lambda self: True)
    url = adw_full.workflow(make_ctx(tmp_path), "Export encounters to CSV")
    assert url == "https://github.com/o/r/pull/42"
    assert stub.commands() == ["/classify", "/feature", "/implement", "/test", "/review", "/commit", "/pull_request"]
    assert stub.calls[1][1] == ["abc12345", "Export encounters to CSV"]
    assert ["git", "checkout", "-b", "adw/abc12345-csv-export"] in shell


def test_full_stops_when_tests_keep_failing(tmp_path, monkeypatch):
    stub = Stub({"/classify": ["/chore"], "/chore": ["specs/chore-abc12345-x.md"], "/implement": ["done"],
                 "/test": [FAIL] * 4, "/resolve_failed_test": ["tried"] * 3})
    monkeypatch.setattr(workflow, "execute_template", stub)
    monkeypatch.setattr(Ctx, "sh", lambda self, cmd, check=True: "feat/x\n")
    monkeypatch.setattr("pathlib.Path.exists", lambda self: True)
    with pytest.raises(StepFailed, match="still failing"):
        adw_full.workflow(make_ctx(tmp_path), "x")
    assert "/review" not in stub.commands() and "/commit" not in stub.commands()


def test_full_rejects_unclassifiable_prompt(tmp_path, monkeypatch):
    stub = Stub({"/classify": ["0"]})
    monkeypatch.setattr(workflow, "execute_template", stub)
    with pytest.raises(StepFailed, match="cannot parse"):
        adw_full.workflow(make_ctx(tmp_path), "hello")
