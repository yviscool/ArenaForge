import unittest

from arena_forge.core.domain import (
    CommandExecution,
    OutputReferenceKind,
    SessionSnapshot,
    TestCase,
    TestRunResult,
    Verdict,
)
from arena_forge.core.usecases import SessionService


class _StubRepository:
    def __init__(self):
        self._store = {}

    def load(self, source_file):
        return self._store.get(source_file)

    def save(self, session):
        self._store[session.source_file] = session


class _StubRunner:
    def __init__(self, compile_result=None, run_results=None):
        self.compile_result = compile_result
        self.run_results = list(run_results or [])
        self.compile_calls = []
        self.run_calls = []

    def compile(self, source_file: str, language: str):
        self.compile_calls.append((source_file, language))
        return self.compile_result

    def run(self, source_file: str, language: str, input_text: str):
        self.run_calls.append((source_file, language, input_text))
        return self.run_results.pop(0)


class UsecaseTests(unittest.TestCase):
    def test_compile_failure_short_circuits_batch(self) -> None:
        runner = _StubRunner(
            compile_result=CommandExecution(argv=("g++",), return_code=1, stdout="boom", runtime_ms=10)
        )
        service = SessionService(repository=_StubRepository(), runner=runner)
        session = SessionSnapshot(source_file="A.cpp", language="C++", tests=(TestCase(name="T1", input_text="1"),))
        report = service.run_all_tests(session)
        self.assertFalse(report.compile_succeeded)
        self.assertEqual(report.test_results, ())

    def test_batch_evaluates_unknown_outputs(self) -> None:
        runner = _StubRunner(
            compile_result=None,
            run_results=[
                TestRunResult(output_text="42\n", return_code=0, runtime_ms=5, verdict=Verdict.UNKNOWN),
            ],
        )
        service = SessionService(repository=_StubRepository(), runner=runner)
        session = SessionSnapshot(
            source_file="A.cpp",
            language="C++",
            tests=(TestCase(name="T1", input_text="1", accepted_outputs=("42",)),),
        )
        report = service.run_all_tests(session)
        self.assertTrue(report.compile_succeeded)
        self.assertEqual(report.test_results[0].verdict, Verdict.ACCEPTED)
        self.assertIsNotNone(report.test_results[0].evaluation)
        self.assertEqual(report.test_results[0].evaluation.reference_kind, OutputReferenceKind.ACCEPTED)


if __name__ == "__main__":
    unittest.main()
