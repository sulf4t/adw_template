"""adw_afk.process(): builds the adw_full.py subprocess call. No real gh/adw_full call."""
import adw_afk


class FakeResult:
    def __init__(self, returncode=0, stdout=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = ""


def test_process_passes_issue_number_to_adw_full(monkeypatch, tmp_path):
    calls = []

    def fake_run(argv, *args, **kwargs):
        calls.append(argv)
        return FakeResult()

    monkeypatch.setattr(adw_afk.subprocess, "run", fake_run)

    issue = {"number": 42, "title": "Export CSV", "body": "please add CSV export"}
    adw_afk.process(str(tmp_path), issue)

    adw_full_calls = [argv for argv in calls if "adw_full.py" in " ".join(argv)]
    assert len(adw_full_calls) == 1
    argv = adw_full_calls[0]
    assert "--issue" in argv
    assert argv[argv.index("--issue") + 1] == "42"
