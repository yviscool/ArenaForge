from __future__ import annotations

from typing import Callable, Optional, Protocol

from .domain import (
    CommandExecution,
    ContestDescriptor,
    CredentialRecord,
    OutputEvaluation,
    ProviderCapabilities,
    SessionSnapshot,
    TestCase,
    TestRunResult,
)


class SessionRepository(Protocol):
    def load(self, source_file: str) -> Optional[SessionSnapshot]:
        ...

    def save(self, session: SessionSnapshot) -> None:
        ...


class Runner(Protocol):
    def compile(self, source_file: str, language: str) -> Optional[CommandExecution]:
        ...

    def run(self, source_file: str, language: str, input_text: str) -> TestRunResult:
        ...


class ContestProvider(Protocol):
    provider_name: str
    capabilities: ProviderCapabilities

    def load_contest(self, contest_id: str) -> ContestDescriptor:
        ...

    def submit_solution(
        self,
        contest_id: str,
        problem_id: str,
        language_id: int,
        code: str,
        credentials: CredentialRecord,
    ) -> None:
        ...


class CredentialStore(Protocol):
    backend_name: str

    def is_available(self) -> bool:
        ...

    def get_credentials(self, provider_name: str) -> Optional[CredentialRecord]:
        ...

    def set_credentials(self, provider_name: str, username: str, secret: str) -> CredentialRecord:
        ...


class Translator(Protocol):
    def translate(self, key: str, locale: Optional[str] = None, **kwargs: str) -> str:
        ...


class OutputChecker(Protocol):
    checker_name: str

    def evaluate(self, test_case: TestCase, output_text: str) -> OutputEvaluation:
        ...


class DebuggerBackend(Protocol):
    supported_exts: list[str]
    RUN_PRIOR: float

    @staticmethod
    def is_runnable() -> bool:
        ...

    def compile(self) -> tuple[int, str] | None:
        ...

    def run(self, args: str = "") -> None:
        ...

    def set_calls(
        self,
        on_out: Callable[..., None],
        on_stop: Callable[..., None],
        on_status_change: Callable[[str], None],
    ) -> None:
        ...

    def terminate(self) -> None:
        ...

    def has_var_view_api(self) -> bool:
        ...

    def get_var_value(self, var_name: str, frame_id: int | None = None) -> str | None:
        ...

    def get_frames(self) -> list[dict[str, object]]:
        ...

    def select_frame(self, frame_id: int) -> None:
        ...
