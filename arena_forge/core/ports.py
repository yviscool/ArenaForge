from __future__ import annotations

from typing import Optional, Protocol

from .domain import (
    CommandExecution,
    ContestDescriptor,
    CredentialRecord,
    ProviderCapabilities,
    SessionSnapshot,
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


class DebuggerBackend(Protocol):
    supported_exts: list[str]
    RUN_PRIOR: float

    @staticmethod
    def is_runnable():
        ...

    def compile(self):
        ...

    def run(self, args=""):
        ...

    def set_calls(self, on_out, on_stop, on_status_change):
        ...

    def terminate(self):
        ...

    def has_var_view_api(self) -> bool:
        ...

    def get_var_value(self, var_name: str, frame_id=None):
        ...

    def get_frames(self):
        ...

    def select_frame(self, frame_id):
        ...
