from __future__ import annotations

from dataclasses import replace
from typing import Callable, Optional, Sequence

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


def _default_translate(key: str, **kwargs: str) -> str:
    from arena_forge.adapters.i18n.catalog import translate_catalog
    return translate_catalog(key, **kwargs)


class SessionService:
    def __init__(
        self,
        repository: SessionRepository,
        runner: Optional[Runner] = None,
        translate: Optional[Callable[..., str]] = None,
    ):
        self.repository = repository
        self.runner = runner
        self._translate = translate or _default_translate

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

    def _evaluate_run_result(self, session: SessionSnapshot, test_case: TestCase) -> TestRunResult:
        result = self.runner.run(session.source_file, session.language, test_case.input_text)
        if result.verdict != Verdict.UNKNOWN:
            return result
        evaluation = evaluate_output_result(test_case, result.output_text)
        return replace(result, verdict=evaluation.verdict, evaluation=evaluation)

    def run_test(self, session: SessionSnapshot, test_case: TestCase) -> TestRunResult:
        if self.runner is None:
            raise RuntimeError(self._translate("error.no_runner_configured"))
        return self._evaluate_run_result(session, test_case)

    def compile_session(self, session: SessionSnapshot) -> Optional[CommandExecution]:
        if self.runner is None:
            raise RuntimeError(self._translate("error.no_runner_configured"))
        return self.runner.compile(session.source_file, session.language)

    def run_all_tests(self, session: SessionSnapshot) -> SessionRunReport:
        compile_result = self.compile_session(session)
        if compile_result is not None and compile_result.return_code != 0:
            return SessionRunReport(compile_result=compile_result, test_results=())
        results = tuple(self._evaluate_run_result(session, test_case) for test_case in session.tests)
        return SessionRunReport(compile_result=compile_result, test_results=results)
