from __future__ import annotations

from dataclasses import replace
from typing import Optional, Sequence

from arena_forge.adapters.i18n.catalog import translate_catalog as translate

from .domain import (
    CommandExecution,
    LanguageProfile,
    SessionRunReport,
    SessionSnapshot,
    TestCase,
    TestRunResult,
    Verdict,
)
from .ports import Runner, SessionRepository
from .services import evaluate_output_result, infer_language


class SessionService:
    def __init__(self, repository: SessionRepository, runner: Optional[Runner] = None):
        self.repository = repository
        self.runner = runner

    def ensure_session(self, source_file: str, profiles: Sequence[LanguageProfile]) -> SessionSnapshot:
        session = self.repository.load(source_file)
        if session is not None:
            return session
        language = infer_language(source_file, profiles)
        session = SessionSnapshot(source_file=source_file, language=language, tests=())
        self.repository.save(session)
        return session

    def save_tests(self, source_file: str, language: str, tests: tuple[TestCase, ...]) -> SessionSnapshot:
        session = SessionSnapshot(source_file=source_file, language=language, tests=tests)
        self.repository.save(session)
        return session

    def run_test(self, session: SessionSnapshot, test_case: TestCase) -> TestRunResult:
        if self.runner is None:
            raise RuntimeError(translate("error.no_runner_configured"))
        result = self.runner.run(session.source_file, session.language, test_case.input_text)
        if result.verdict != Verdict.UNKNOWN:
            return result
        evaluation = evaluate_output_result(test_case, result.output_text)
        return replace(result, verdict=evaluation.verdict, evaluation=evaluation)


class RunSessionService:
    def __init__(self, runner: Runner):
        self.runner = runner

    def compile_session(self, session: SessionSnapshot) -> Optional[CommandExecution]:
        return self.runner.compile(session.source_file, session.language)

    def run_all_tests(self, session: SessionSnapshot) -> SessionRunReport:
        compile_result = self.compile_session(session)
        if compile_result is not None and compile_result.return_code != 0:
            return SessionRunReport(compile_result=compile_result, test_results=())
        results = tuple(self._run_test(session, test_case) for test_case in session.tests)
        return SessionRunReport(compile_result=compile_result, test_results=results)

    def _run_test(self, session: SessionSnapshot, test_case: TestCase) -> TestRunResult:
        result = self.runner.run(session.source_file, session.language, test_case.input_text)
        if result.verdict != Verdict.UNKNOWN:
            return result
        evaluation = evaluate_output_result(test_case, result.output_text)
        return replace(result, verdict=evaluation.verdict, evaluation=evaluation)
