from __future__ import annotations

from typing import Optional, Protocol

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


class OutputChecker(Protocol):
    checker_name: str

    def evaluate(self, test_case: TestCase, output_text: str) -> OutputEvaluation:
        ...
