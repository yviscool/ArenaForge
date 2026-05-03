from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


class Verdict(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    UNKNOWN = "unknown"
    COMPILE_ERROR = "compile_error"
    RUNTIME_ERROR = "runtime_error"
    TIMEOUT = "timeout"


class DiagnosticSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ProviderWorkspaceKind(str, Enum):
    CONTEST = "contest"
    PROBLEM = "problem"


@dataclass(frozen=True)
class LanguageProfile:
    name: str
    extensions: Tuple[str, ...]
    compile_cmd: Optional[str]
    run_cmd: Optional[str]
    lint_compile_cmd: Optional[str] = None

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "LanguageProfile":
        return cls(
            name=str(payload["name"]),
            extensions=tuple(str(item) for item in payload.get("extensions", ())),
            compile_cmd=payload.get("compile_cmd"),
            run_cmd=payload.get("run_cmd"),
            lint_compile_cmd=payload.get("lint_compile_cmd"),
        )


@dataclass(frozen=True)
class TestCase:
    name: str
    input_text: str
    accepted_outputs: Tuple[str, ...] = ()
    rejected_outputs: Tuple[str, ...] = ()
    runtime_ms: Optional[int] = None
    return_code: Optional[int] = None

    @classmethod
    def from_mapping(cls, index: int, payload: dict[str, Any]) -> "TestCase":
        return cls(
            name=str(payload.get("name") or f"Test {index}"),
            input_text=str(payload.get("test", "")),
            accepted_outputs=tuple(str(item) for item in payload.get("correct_answers", ())),
            rejected_outputs=tuple(str(item) for item in payload.get("uncorrect_answers", ())),
            runtime_ms=payload.get("runtime_ms"),
            return_code=payload.get("return_code"),
        )

    def to_mapping(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"name": self.name, "test": self.input_text}
        if self.accepted_outputs:
            payload["correct_answers"] = list(self.accepted_outputs)
        if self.rejected_outputs:
            payload["uncorrect_answers"] = list(self.rejected_outputs)
        if self.runtime_ms is not None:
            payload["runtime_ms"] = self.runtime_ms
        if self.return_code is not None:
            payload["return_code"] = self.return_code
        return payload


@dataclass(frozen=True)
class TestRunResult:
    output_text: str
    return_code: int
    runtime_ms: int
    verdict: Verdict
    command: Tuple[str, ...] = ()
    message: str = ""


@dataclass(frozen=True)
class CommandExecution:
    argv: Tuple[str, ...]
    return_code: int
    stdout: str
    runtime_ms: int


@dataclass(frozen=True)
class CompilerIssue:
    severity: DiagnosticSeverity
    line: int
    column: int
    message: str


@dataclass(frozen=True)
class ProviderCapabilities:
    workspace_kind: ProviderWorkspaceKind = ProviderWorkspaceKind.CONTEST
    supports_submission: bool = False
    requires_credentials: bool = False


@dataclass(frozen=True)
class CredentialRecord:
    username: str
    secret: str


@dataclass(frozen=True)
class SessionRunReport:
    compile_result: Optional[CommandExecution]
    test_results: Tuple[TestRunResult, ...]

    @property
    def compile_succeeded(self) -> bool:
        return self.compile_result is None or self.compile_result.return_code == 0


@dataclass(frozen=True)
class RunHistoryEntry:
    test_name: str
    output_text: str
    verdict: Verdict
    runtime_ms: int
    return_code: int


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class SessionSnapshot:
    source_file: str
    language: str
    tests: Tuple[TestCase, ...] = field(default_factory=tuple)
    run_history: Tuple[RunHistoryEntry, ...] = field(default_factory=tuple)
    updated_at: str = field(default_factory=_utc_timestamp)

    @property
    def source_path(self) -> Path:
        return Path(self.source_file)

    def to_mapping(self) -> Dict[str, Any]:
        return {
            "schema_version": 1,
            "source_file": self.source_file,
            "language": self.language,
            "updated_at": self.updated_at,
            "tests": [test.to_mapping() for test in self.tests],
            "run_history": [
                {
                    "test_name": item.test_name,
                    "output_text": item.output_text,
                    "verdict": item.verdict.value,
                    "runtime_ms": item.runtime_ms,
                    "return_code": item.return_code,
                }
                for item in self.run_history
            ],
        }

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "SessionSnapshot":
        tests = tuple(
            TestCase.from_mapping(index + 1, item)
            for index, item in enumerate(payload.get("tests", ()))
        )
        history = tuple(
            RunHistoryEntry(
                test_name=str(item["test_name"]),
                output_text=str(item["output_text"]),
                verdict=Verdict(str(item["verdict"])),
                runtime_ms=int(item["runtime_ms"]),
                return_code=int(item["return_code"]),
            )
            for item in payload.get("run_history", ())
        )
        return cls(
            source_file=str(payload["source_file"]),
            language=str(payload["language"]),
            tests=tests,
            run_history=history,
            updated_at=str(payload.get("updated_at") or _utc_timestamp()),
        )


@dataclass(frozen=True)
class ContestProblem:
    index: str
    title: str
    samples: Tuple[TestCase, ...]


@dataclass(frozen=True)
class ContestDescriptor:
    contest_id: str
    title: str
    provider: str
    problems: Tuple[ContestProblem, ...]
