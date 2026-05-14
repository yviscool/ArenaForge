from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from arena_forge.core.domain import CompilerIssue, DiagnosticSeverity

from .subprocess_runner import (
    _resolve_subprocess_spawn_options,
    build_command_argv,
    build_process_spawn_options,
    build_process_text_options,
)

_DIAGNOSTIC_PATTERN = re.compile(
    r"^(?P<source>.+?):(?P<line>\d+):(?P<column>\d+):\s*(?P<severity>[a-zA-Z ]+):\s*(?P<message>.*)$"
)


def _normalize_source_label(value: str) -> str:
    return value.replace("\\", "/").rstrip().casefold()


def _parse_severity(raw_value: str) -> DiagnosticSeverity:
    normalized = raw_value.strip().lower()
    if "warning" in normalized:
        return DiagnosticSeverity.WARNING
    if "error" in normalized:
        return DiagnosticSeverity.ERROR
    return DiagnosticSeverity.INFO


def parse_compiler_issues(output: str, source_file: Union[str, Path]) -> tuple[CompilerIssue, ...]:
    normalized_source = _normalize_source_label(str(source_file))
    issues: list[CompilerIssue] = []
    for line in output.splitlines():
        match = _DIAGNOSTIC_PATTERN.match(line)
        if match is None:
            continue
        if _normalize_source_label(match.group("source")) != normalized_source:
            continue
        issues.append(
            CompilerIssue(
                severity=_parse_severity(match.group("severity")),
                line=int(match.group("line")),
                column=int(match.group("column")),
                message=match.group("message").strip(),
            )
        )
    return tuple(issues)


@dataclass(frozen=True)
class DiagnosticsReport:
    command: tuple[str, ...]
    output: str
    issues: tuple[CompilerIssue, ...]


@dataclass(frozen=True)
class DiagnosticsScratchWorkspace:
    root_dir: Path
    relative_dir: str = "cmp_sense"
    file_name: str = "amin.cpp"

    def scratch_path(self) -> Path:
        return self.root_dir / self.relative_dir / self.file_name

    def write_source(self, source_text: str) -> Path:
        scratch_path = self.scratch_path()
        scratch_path.parent.mkdir(parents=True, exist_ok=True)
        scratch_path.write_text(source_text, encoding="utf-8")
        return scratch_path


class CompilerDiagnosticsService:
    def __init__(self, *, platform_name: Optional[str], scratch_workspace: DiagnosticsScratchWorkspace):
        self.platform_name = platform_name
        self.scratch_workspace = scratch_workspace

    def run(self, *, compile_cmd: str, source_text: str, source_file_dir: str) -> DiagnosticsReport:
        scratch_file = self.scratch_workspace.write_source(source_text)
        command = compile_cmd.format(source_file=str(scratch_file), source_file_dir=source_file_dir)
        argv = tuple(build_command_argv(command, platform_name=self.platform_name))
        spawn_options = _resolve_subprocess_spawn_options(build_process_spawn_options(self.platform_name))
        text_options = build_process_text_options(self.platform_name)
        completed = subprocess.run(
            argv,
            cwd=source_file_dir,
            capture_output=True,
            check=False,
            startupinfo=spawn_options["startupinfo"],
            creationflags=spawn_options["creationflags"],
            **text_options,
        )
        output = (completed.stdout or "") + (completed.stderr or "")
        return DiagnosticsReport(
            command=argv,
            output=output,
            issues=parse_compiler_issues(output, scratch_file),
        )
