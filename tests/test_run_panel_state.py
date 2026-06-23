import importlib
import json
import os
import sys
import tempfile
import types
import unittest
from contextlib import contextmanager
from unittest.mock import patch

from arena_forge.core.domain import RunHistoryEntry, SessionSnapshot, TestCase, Verdict


class _FakeRepository:
    def __init__(self, snapshot=None):
        self.snapshot = snapshot
        self.load_calls = []
        self.save_calls = []

    def load(self, source_file):
        self.load_calls.append(source_file)
        return self.snapshot

    def save(self, snapshot):
        self.save_calls.append(snapshot)
        self.snapshot = snapshot


@contextmanager
def _patched_sublime():
    original = sys.modules.get("sublime")
    original_rendering = sys.modules.get("arena_forge.adapters.sublime.run_panel.rendering")
    fake = types.SimpleNamespace(
        encode_value=lambda value, pretty=False: json.dumps(value, indent=4 if pretty else None),
        decode_value=json.loads,
    )
    sys.modules["sublime"] = fake
    sys.modules["arena_forge.adapters.sublime.run_panel.rendering"] = types.SimpleNamespace(
        build_accdec_phantom=lambda *args, **kwargs: None,
        build_test_config_phantom=lambda *args, **kwargs: None,
    )
    sys.modules.pop("arena_forge.adapters.sublime.run_panel.state", None)
    sys.modules.pop("arena_forge.adapters.sublime.run_panel.persistence", None)
    try:
        yield
    finally:
        sys.modules.pop("arena_forge.adapters.sublime.run_panel.state", None)
        sys.modules.pop("arena_forge.adapters.sublime.run_panel.persistence", None)
        if original_rendering is None:
            sys.modules.pop("arena_forge.adapters.sublime.run_panel.rendering", None)
        else:
            sys.modules["arena_forge.adapters.sublime.run_panel.rendering"] = original_rendering
        if original is None:
            sys.modules.pop("sublime", None)
        else:
            sys.modules["sublime"] = original


class RunPanelStateTests(unittest.TestCase):
    def test_panel_test_state_memorize_sorts_answer_sets(self) -> None:
        with _patched_sublime():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel.state")

            test_state = module.PanelTestState(
                {
                    "test": "1 2\n",
                    "correct_answers": ["z", "a"],
                    "uncorrect_answers": ["d", "b"],
                }
            )

            self.assertEqual(
                test_state.memorize(),
                {
                    "test": "1 2\n",
                    "correct_answers": ["a", "z"],
                    "uncorrect_answers": ["b", "d"],
                },
            )

    def test_persist_panel_tests_skips_rewrite_and_save_when_payload_is_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            with _patched_sublime():
                state_module = importlib.import_module("arena_forge.adapters.sublime.run_panel.state")
                persist_module = importlib.import_module("arena_forge.adapters.sublime.run_panel.persistence")
                test_state = state_module.PanelTestState({"test": "1 2\n", "correct_answers": ["ok", "alt"]})
                tests_path = os.path.join(tempdir, "tests.json")
                expected_payload = persist_module.sublime.encode_value([test_state.memorize()], True)
                with open(tests_path, "w", encoding="utf-8") as handle:
                    handle.write(expected_payload)

                repository = _FakeRepository(
                    SessionSnapshot(
                        source_file="main.cpp",
                        language="cpp",
                        tests=(test_state.to_core_test_case(1),),
                    )
                )
                real_open = open
                write_attempts = []

                def guarded_open(path, mode="r", *args, **kwargs):
                    if os.fspath(path) == tests_path and "w" in mode:
                        write_attempts.append(mode)
                        raise AssertionError("unexpected rewrite")
                    return real_open(path, mode, *args, **kwargs)

                with patch("builtins.open", guarded_open):
                    persist_module.persist_panel_tests(
                        "main.cpp",
                        [test_state],
                        repository,
                        lambda source_file: "cpp",
                        lambda source_file, for_write=False: tests_path,
                    )

                self.assertEqual(write_attempts, [])
                self.assertEqual(repository.save_calls, [])
                with open(tests_path, encoding="utf-8") as handle:
                    self.assertEqual(handle.read(), expected_payload)

    def test_persist_panel_tests_writes_and_saves_when_payload_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            with _patched_sublime():
                state_module = importlib.import_module("arena_forge.adapters.sublime.run_panel.state")
                persist_module = importlib.import_module("arena_forge.adapters.sublime.run_panel.persistence")
                test_state = state_module.PanelTestState({"test": "1 2\n", "correct_answers": ["ok", "alt"]})
                tests_path = os.path.join(tempdir, "tests.json")
                with open(tests_path, "w", encoding="utf-8") as handle:
                    handle.write("[]")

                repository = _FakeRepository()

                persist_module.persist_panel_tests(
                    "main.cpp",
                    [test_state],
                    repository,
                    lambda source_file: "cpp",
                    lambda source_file, for_write=False: tests_path,
                )

                self.assertEqual(len(repository.save_calls), 1)
                self.assertEqual(repository.save_calls[0].language, "cpp")
                self.assertEqual(repository.save_calls[0].tests, (test_state.to_core_test_case(1),))
                with open(tests_path, encoding="utf-8") as handle:
                    self.assertEqual(handle.read(), persist_module.sublime.encode_value([test_state.memorize()], True))

    def test_persist_panel_tests_preserves_existing_run_history(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            with _patched_sublime():
                state_module = importlib.import_module("arena_forge.adapters.sublime.run_panel.state")
                persist_module = importlib.import_module("arena_forge.adapters.sublime.run_panel.persistence")
                test_state = state_module.PanelTestState({"test": "1 2\n"})
                tests_path = os.path.join(tempdir, "tests.json")
                with open(tests_path, "w", encoding="utf-8") as handle:
                    handle.write("[]")

                history_entry = RunHistoryEntry(
                    test_name="Test 1",
                    output_text="42",
                    verdict=Verdict.ACCEPTED,
                    runtime_ms=7,
                    return_code=0,
                )
                repository = _FakeRepository(
                    SessionSnapshot(
                        source_file="main.cpp",
                        language="cpp",
                        tests=(),
                        run_history=(history_entry,),
                    )
                )

                persist_module.persist_panel_tests(
                    "main.cpp",
                    [test_state],
                    repository,
                    lambda source_file: "cpp",
                    lambda source_file, for_write=False: tests_path,
                )

                self.assertEqual(repository.save_calls[-1].run_history, (history_entry,))

    def test_load_panel_tests_logs_invalid_payload_and_falls_back_to_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            with _patched_sublime():
                persist_module = importlib.import_module("arena_forge.adapters.sublime.run_panel.persistence")
                tests_path = os.path.join(tempdir, "tests.json")
                with open(tests_path, "w", encoding="utf-8") as handle:
                    handle.write("{bad json")

                repository = _FakeRepository(
                    SessionSnapshot(
                        source_file="main.cpp",
                        language="cpp",
                        tests=(TestCase(name="T1", input_text="42"),),
                    )
                )
                logs = []
                persist_module.product_log_message = lambda key, **kwargs: logs.append((key, kwargs))

                result = persist_module.load_panel_tests(
                    "main.cpp",
                    lambda item: item,
                    repository,
                    lambda source_file, for_write=False: tests_path,
                )

                self.assertEqual(result, [{"name": "T1", "test": "42"}])
                self.assertEqual(logs, [("error.tests_file_invalid", {"path": tests_path})])


if __name__ == "__main__":
    unittest.main()
