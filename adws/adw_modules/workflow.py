"""Shared runtime for ADW scripts.

A workflow is a plain function `def workflow(ctx, *args, **options)`. It calls
`ctx.template("/chore", [...])` or `ctx.prompt("...")` and returns. Everything
else lives here: CLI flags (--model, --working-dir, --dry-run), the adw_id,
console panels, per-step summary files, the workflow summary and the exit code.

    from workflow import run, spec_path

    def workflow(ctx, prompt):
        "Plan a chore, then implement the plan."
        plan = ctx.template("/chore", [ctx.adw_id, prompt], agent="planner", parse=spec_path)
        ctx.template("/implement", [plan], agent="builder")

    if __name__ == "__main__":
        run(workflow)
"""

import inspect
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, List, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agent import (  # noqa: E402
    OUTPUT_JSONL,
    SUMMARY_JSON,
    AgentPromptRequest,
    AgentPromptResponse,
    AgentTemplateRequest,
    agents_root,
    execute_template,
    generate_short_id,
    prompt_claude_code_with_retry,
)

MODELS = ("sonnet", "opus", "fable")
RUNNER = os.getenv("ADW_RUNNER", "claude")


class StepFailed(Exception):
    """A step returned success=False, or its output could not be parsed."""


@dataclass
class Step:
    agent: str
    input: str
    success: bool
    output: str
    session_id: Optional[str] = None


@dataclass
class Ctx:
    """What a workflow function receives. Two methods matter: template() and prompt()."""

    adw_id: str
    model: str
    working_dir: str
    dry_run: bool = False
    issue: Optional[str] = None
    console: Console = field(default_factory=Console)
    steps: list = field(default_factory=list)

    def template(
        self,
        slash_command: str,
        args: Iterable[Any] = (),
        agent: str = "executor",
        parse: Optional[Callable[[str], Any]] = None,
        required: bool = True,
        dry: Any = None,
        model: Optional[str] = None,
    ) -> Any:
        """Run a slash command from <working_dir>/.claude/commands/.

        Returns the text of the template's `## Report`, or parse(text) when parse is given.
        In --dry-run nothing is called: returns `dry` if given, else a placeholder string.
        """
        args = [str(a) for a in args]
        request = AgentTemplateRequest(
            agent_name=agent,
            slash_command=slash_command,
            args=args,
            adw_id=self.adw_id,
            model=model or self.model,
            working_dir=self.working_dir,
        )
        label = f"{slash_command} {' '.join(args)}".strip()
        return self._call(request, execute_template, label, parse, required, dry)

    def prompt(
        self,
        text: str,
        agent: str = "oneoff",
        parse: Optional[Callable[[str], Any]] = None,
        required: bool = True,
        dry: Any = None,
    ) -> Any:
        """Run a free prompt, no template. Returns the answer text, or parse(text)."""
        out_dir = self.agent_dir(agent)
        out_dir.mkdir(parents=True, exist_ok=True)
        request = AgentPromptRequest(
            prompt=text,
            adw_id=self.adw_id,
            agent_name=agent,
            model=self.model,
            dangerously_skip_permissions=True,
            output_file=str(out_dir / OUTPUT_JSONL),
            working_dir=self.working_dir,
        )
        return self._call(request, prompt_claude_code_with_retry, text, parse, required, dry)

    def sh(self, cmd: List[str], check: bool = True) -> str:
        """Run a shell command in the working directory and return its stdout. Skipped in --dry-run."""
        self.console.print(f"[dim]$ {' '.join(cmd)}[/dim]")
        if self.dry_run:
            return ""
        result = subprocess.run(cmd, cwd=self.working_dir, capture_output=True, text=True)
        if check and result.returncode != 0:
            raise StepFailed(f"command failed: {' '.join(cmd)}\n{result.stderr.strip()}")
        return result.stdout

    @property
    def run_dir(self) -> Path:
        return Path(agents_root(self.working_dir)) / self.adw_id

    def agent_dir(self, agent: str) -> Path:
        return self.run_dir / agent

    def save(self, name: str, data: Any) -> Path:
        """Write a JSON file into agents/<adw_id>/ and return its path."""
        self.run_dir.mkdir(parents=True, exist_ok=True)
        path = self.run_dir / name
        path.write_text(json.dumps(data, indent=2, default=str))
        return path

    # plumbing

    def _call(self, request, execute, label, parse, required, dry):
        self._show_inputs(request.agent_name, label)
        if self.dry_run:
            response = AgentPromptResponse(output=f"[dry-run] {label}", success=True)
        else:
            with self.console.status(f"[yellow]{request.agent_name}: running...[/yellow]"):
                response = execute(request)
        self._record(request.agent_name, label, response)
        if self.dry_run:
            return dry if dry is not None else response.output
        if not response.success:
            if required:
                raise StepFailed(f"{request.agent_name} failed: {response.output}")
            return response.output
        if parse:
            try:
                return parse(response.output)
            except Exception as e:
                raise StepFailed(
                    f"{request.agent_name}: cannot parse output ({e}):\n{response.output}"
                )
        return response.output

    def _record(self, agent: str, label: str, response: AgentPromptResponse) -> None:
        self.steps.append(Step(agent, label, response.success, response.output, response.session_id))
        out_dir = self.agent_dir(agent)
        out_dir.mkdir(parents=True, exist_ok=True)
        retry = getattr(response.retry_code, "value", str(response.retry_code))
        (out_dir / SUMMARY_JSON).write_text(
            json.dumps(
                {
                    "adw_id": self.adw_id,
                    "agent": agent,
                    "input": label,
                    "model": self.model,
                    "working_dir": self.working_dir,
                    "success": response.success,
                    "session_id": response.session_id,
                    "retry_code": retry,
                    "output": response.output,
                },
                indent=2,
            )
        )
        style, title = ("green", "Success") if response.success else ("red", "Failed")
        self.console.print(
            Panel(
                response.output or "(empty)",
                title=f"[bold {style}]{agent}: {title}[/bold {style}]",
                border_style=style,
            )
        )
        self.console.print(f"[dim]-> {out_dir}/[/dim]\n")
        self._notify_issue(agent, label, response)

    def _notify_issue(self, agent: str, label: str, response: AgentPromptResponse) -> None:
        """Best-effort: post a short comment on self.issue reporting this step. Never raises."""
        if not self.issue or self.dry_run:
            return
        status = "succeeded" if response.success else "failed"
        short_label = label if len(label) < 400 else label[:400] + "..."
        body = (
            f"ADW {self.adw_id}: {agent} {status}.\n"
            f"{short_label}\n"
            f"Trace: agents/{self.adw_id}/{agent}/"
        )
        try:
            subprocess.run(
                ["gh", "issue", "comment", str(self.issue), "--body", body],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError:
            pass

    def _show_inputs(self, agent: str, label: str) -> None:
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column(style="bold cyan")
        table.add_column()
        table.add_row("Agent", agent)
        table.add_row("Input", label if len(label) < 400 else label[:400] + "...")
        table.add_row("Model", self.model)
        self.console.print(Panel(table, title="[bold blue]Step[/bold blue]", border_style="blue"))


# Parsers shared by the phase scripts

SPEC_PATH = re.compile(r"specs/[\w\-./]+\.md")


def spec_path(text: str) -> str:
    """First specs/...md path found in a template's report."""
    match = SPEC_PATH.search(text)
    if not match:
        raise ValueError("no specs/*.md path in the output")
    return match.group(0)


def json_block(text: str) -> Any:
    """Parse the JSON object or array in a report, tolerating ``` fences and surrounding prose."""
    stripped = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", stripped, re.DOTALL)
    if fenced:
        stripped = fenced.group(1).strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        start = min((i for i in (stripped.find("["), stripped.find("{")) if i >= 0), default=-1)
        end = max(stripped.rfind("]"), stripped.rfind("}"))
        if start < 0 or end < start:
            raise ValueError("no JSON found in the output")
        return json.loads(stripped[start : end + 1])


def run(fn: Callable, *extra_options) -> None:
    """Turn `fn(ctx, *args, **options)` into a CLI with --model, --working-dir and --dry-run.

    `extra_options` are click.option decorators; their values are passed to fn as keywords.
    """
    name = Path(sys.argv[0]).stem
    signature = inspect.signature(fn)
    params = [p for p in list(signature.parameters.values())[1:] if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD, p.VAR_POSITIONAL)]
    usage = " ".join(
        f"[{p.name}...]" if p.kind is p.VAR_POSITIONAL
        else (f"[{p.name}]" if p.default is not p.empty else f"<{p.name}>")
        for p in params
    )

    def main(args, model, working_dir, dry_run, issue, **options):
        if RUNNER != "claude":
            raise click.UsageError(f"ADW_RUNNER={RUNNER} is not implemented yet; only 'claude' is")
        try:
            signature.bind(None, *args, **options)
        except TypeError:
            raise click.UsageError(f"expected: {name} {usage}")

        ctx = Ctx(
            adw_id=generate_short_id(),
            model=model,
            working_dir=working_dir or os.getcwd(),
            dry_run=dry_run,
            issue=issue,
        )
        header = f"[cyan]ADW[/cyan] {name}   [cyan]id[/cyan] {ctx.adw_id}   [cyan]dir[/cyan] {ctx.working_dir}"
        if dry_run:
            header += "   [yellow]dry-run[/yellow]"
        ctx.console.print(Panel(header, border_style="blue"))

        code, error = 0, None
        try:
            fn(ctx, *args, **options)
        except StepFailed as e:
            code, error = 1, str(e)
            ctx.console.print(Panel(error, title="[bold red]Workflow failed[/bold red]", border_style="red"))

        summary_path = _write_workflow_summary(ctx, name, args, code, error)
        verdict = "[bold green]Done[/bold green]" if code == 0 else "[bold red]Failed[/bold red]"
        ctx.console.print(f"{verdict}  {summary_path}")
        sys.exit(code)

    command = main
    for option in reversed(extra_options):
        command = option(command)
    command = click.option("--dry-run", is_flag=True, help="Show each step without calling Claude Code.")(command)
    command = click.option(
        "--issue", default=None, help="GitHub issue number; each agent step posts a comment there."
    )(command)
    command = click.option(
        "--working-dir",
        type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
        default=None,
        help="Repo to operate on (default: current directory).",
    )(command)
    command = click.option(
        "--model", type=click.Choice(MODELS), default=os.getenv("ADW_MODEL", "sonnet"), show_default=True
    )(command)
    command = click.argument("args", nargs=-1, metavar=usage)(command)
    command = click.command(help=fn.__doc__, context_settings={"help_option_names": ["-h", "--help"]})(command)
    command()


def _write_workflow_summary(ctx: Ctx, name: str, args, code: int, error: Optional[str]) -> Path:
    return ctx.save(
        "workflow_summary.json",
        {
            "workflow": name,
            "adw_id": ctx.adw_id,
            "args": list(args),
            "model": ctx.model,
            "working_dir": ctx.working_dir,
            "dry_run": ctx.dry_run,
            "overall_success": code == 0,
            "error": error,
            "steps": [s.__dict__ for s in ctx.steps],
        },
    )
