from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from arena_forge.core.domain import CompilerIssue, DiagnosticSeverity

from .subprocess_runner import (
    build_command_argv,
    build_command_context,
    execute_subprocess,
)

_DIAGNOSTIC_PATTERN = re.compile(
    r"^(?P<source>.+?):(?P<line>\d+):(?P<column>\d+):\s*(?P<severity>[a-zA-Z ]+):\s*(?P<message>.*)$"
)
_ANSI_ESCAPE_PATTERN = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def _normalize_source_label(value: str) -> str:
    return value.replace("\\", "/").rstrip().casefold()


def _parse_severity(raw_value: str) -> DiagnosticSeverity:
    normalized = raw_value.strip().lower()
    if "warning" in normalized:
        return DiagnosticSeverity.WARNING
    if "error" in normalized:
        return DiagnosticSeverity.ERROR
    return DiagnosticSeverity.INFO


def _strip_ansi_escape_codes(value: str) -> str:
    return _ANSI_ESCAPE_PATTERN.sub("", value)


def parse_compiler_issues(output: str, source_file: Union[str, Path]) -> tuple[CompilerIssue, ...]:
    normalized_source = _normalize_source_label(str(source_file))
    issues: list[CompilerIssue] = []
    for raw_line in output.splitlines():
        line = _strip_ansi_escape_codes(raw_line)
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
    runtime_ms: int
    timed_out: bool = False


@dataclass(frozen=True)
class DiagnosticsScratchWorkspace:
    root_dir: Path
    relative_dir: str = ".arena-forge/diagnostics"
    file_name: str = "amin.cpp"

    def scratch_path(self, label: Optional[str] = None) -> Path:
        if label is None:
            return self.root_dir / self.relative_dir / self.file_name
        normalized = self._normalize_label(label)
        suffix = Path(self.file_name).suffix or ".tmp"
        return self.root_dir / self.relative_dir / f"{normalized}{suffix}"

    def write_source(self, source_text: str, *, label: Optional[str] = None) -> Path:
        scratch_path = self.scratch_path(label=label)
        scratch_path.parent.mkdir(parents=True, exist_ok=True)
        scratch_path.write_text(source_text, encoding="utf-8")
        return scratch_path

    @staticmethod
    def _normalize_label(label: str) -> str:
        normalized = re.sub(r"[^A-Za-z0-9_.-]+", "_", label).strip("._")
        return normalized or "amin"


class CompilerDiagnosticsService:
    def __init__(self, *, platform_name: Optional[str], scratch_workspace: DiagnosticsScratchWorkspace):
        self.platform_name = platform_name
        self.scratch_workspace = scratch_workspace

    def run(
        self,
        *,
        compile_cmd: str,
        source_text: str,
        source_file: str,
        source_file_dir: str,
        scratch_label: Optional[str] = None,
        timeout_ms: int = 0,
    ) -> DiagnosticsReport:
        scratch_file = self.scratch_workspace.write_source(source_text, label=scratch_label)
        command_context = build_command_context(source_file)
        command_context["source_file"] = str(scratch_file)
        command_context["source_file_dir"] = source_file_dir
        command = compile_cmd.format(**command_context)
        argv = tuple(build_command_argv(command, platform_name=self.platform_name))
        result = execute_subprocess(
            argv,
            cwd=source_file_dir,
            timeout_ms=timeout_ms,
            platform_name=self.platform_name,
        )
        output = result.stdout + result.stderr
        try:
            return DiagnosticsReport(
                command=result.argv,
                output=output,
                issues=parse_compiler_issues(output, scratch_file),
                runtime_ms=result.runtime_ms,
                timed_out=result.timed_out,
            )
        finally:
            try:
                scratch_file.unlink()
            except OSError:
                pass
