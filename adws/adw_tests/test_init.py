"""adw init copies templates without overwriting and prepares the repo."""
import os
import subprocess

from rich.console import Console

import adw_init
from workflow import Ctx


def test_install_templates_copies_everything_once(tmp_path):
    copied, skipped = adw_init.install_templates(str(tmp_path))
    assert "chore.md" in copied and os.path.join("e2e", "test_example.md") in copied and skipped == []
    assert (tmp_path / ".claude" / "commands" / "test.md").exists()
    assert (tmp_path / "specs").is_dir()
    assert "agents/" in (tmp_path / ".gitignore").read_text()

    copied2, skipped2 = adw_init.install_templates(str(tmp_path))
    assert copied2 == [] and sorted(skipped2) == sorted(copied)
    assert (tmp_path / ".gitignore").read_text().count("agents/") == 1


def test_install_templates_never_overwrites_a_customized_file(tmp_path):
    commands = tmp_path / ".claude" / "commands"
    commands.mkdir(parents=True)
    (commands / "test.md").write_text("# my own tests\n")
    (tmp_path / ".gitignore").write_text("node_modules\n")
    copied, skipped = adw_init.install_templates(str(tmp_path))
    assert "test.md" in skipped and "test.md" not in copied
    assert (commands / "test.md").read_text() == "# my own tests\n"
    assert (tmp_path / ".gitignore").read_text() == "node_modules\n# ADW run outputs (transcripts, summaries, screenshots)\nagents/\n"


def test_workflow_no_agent_skips_claude(tmp_path, monkeypatch):
    import workflow

    def boom(request):
        raise AssertionError("must not call the agent")

    monkeypatch.setattr(workflow, "execute_template", boom)
    ctx = Ctx(adw_id="abc12345", model="sonnet", working_dir=str(tmp_path), console=Console(file=open(os.devnull, "w")))
    adw_init.workflow(ctx, no_agent=True)
    assert (tmp_path / ".claude" / "commands" / "prime.md").exists()


def test_every_template_has_a_report_section():
    root = adw_init.TEMPLATES
    for path in root.rglob("*.md"):
        if path.parent.name == "e2e" or path.name == "conditional_docs.md":
            continue
        assert "## Report" in path.read_text(), path
