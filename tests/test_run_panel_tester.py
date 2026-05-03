import importlib
import sys
import types
import unittest
from contextlib import contextmanager


class _DummyTest:
    def __init__(self, test_string: str):
        self.test_string = test_string
        self.tie_pos = None
        self.correct_answers = set()
        self.uncorrect_answers = set()

    def append_string(self, value: str) -> None:
        self.test_string += value

    def set_tie_pos(self, pos: int) -> None:
        self.tie_pos = pos

    def add_correct_answer(self, answer: str) -> None:
        self.correct_answers.add(answer.strip())

    def remove_uncorrect_answer(self, answer: str) -> None:
        self.uncorrect_answers.discard(answer.strip())

    def remove_correct_answer(self, answer: str) -> None:
        self.correct_answers.discard(answer.strip())

    def add_uncorrect_answer(self, answer: str) -> None:
        self.uncorrect_answers.add(answer.strip())

    def is_correct_answer(self, answer: str):
        stripped = answer.strip()
        if stripped in self.correct_answers:
            return True
        if stripped in self.uncorrect_answers:
            return False
        return None


class _FakeProcessManager:
    def __init__(self):
        self.calls = []
        self.on_out = None
        self.on_stop = None
        self.on_status_change = None

    def set_calls(self, on_out, on_stop, on_status_change):
        self.on_out = on_out
        self.on_stop = on_stop
        self.on_status_change = on_status_change

    def run(self):
        self.calls.append("run")

    def write(self, value: str):
        self.calls.append(("write", value))

    def compile(self):
        self.calls.append("compile")

    def terminate(self):
        self.calls.append("terminate")


@contextmanager
def _patched_sublime():
    original = sys.modules.get("sublime")
    fake = types.SimpleNamespace(
        set_timeout_async=lambda callback, delay=0: callback(),
        status_message=lambda message: None,
    )
    sys.modules["sublime"] = fake
    sys.modules.pop("arena_forge.adapters.sublime.run_panel_tester", None)
    try:
        yield
    finally:
        sys.modules.pop("arena_forge.adapters.sublime.run_panel_tester", None)
        if original is None:
            sys.modules.pop("sublime", None)
        else:
            sys.modules["sublime"] = original


class RunPanelTesterTests(unittest.TestCase):
    def test_next_test_creates_test_and_starts_process(self) -> None:
        with _patched_sublime():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel_tester")
            process = _FakeProcessManager()
            inserted = []
            stopped = []
            statuses = []
            tester = module.RunPanelTester(
                process,
                on_insert=inserted.append,
                on_out=lambda chunk: None,
                on_stop=lambda *args, **kwargs: stopped.append(args),
                on_status_change=statuses.append,
                tests=[],
                test_factory=_DummyTest,
                schedule_async=lambda callback, delay=0: callback(),
                show_status=statuses.append,
            )
            tester.next_test(12, lambda: statuses.append("updated"))
            self.assertEqual(process.calls[0], "run")
            self.assertEqual(process.calls[1], ("write", ""))
            self.assertEqual(inserted, [""])
            self.assertEqual(tester.running_test, 0)
            self.assertTrue(tester.running_new)
            self.assertEqual(tester.tests[0].tie_pos, 12)

    def test_next_test_reports_running_state_without_mutation(self) -> None:
        with _patched_sublime():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel_tester")
            process = _FakeProcessManager()
            messages = []
            tester = module.RunPanelTester(
                process,
                on_insert=lambda chunk: None,
                on_out=lambda chunk: None,
                on_stop=lambda *args, **kwargs: None,
                on_status_change=lambda status: None,
                tests=[_DummyTest("1")],
                test_factory=_DummyTest,
                schedule_async=lambda callback, delay=0: callback(),
                show_status=lambda: messages.append("process already running"),
            )
            tester.proc_run = True
            tester.next_test(1, lambda: None)
            self.assertEqual(messages, ["process already running"])
            self.assertEqual(len(tester.tests), 1)

    def test_run_test_compiles_resets_output_and_starts_process(self) -> None:
        with _patched_sublime():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel_tester")
            process = _FakeProcessManager()
            statuses = []
            tester = module.RunPanelTester(
                process,
                on_insert=lambda chunk: None,
                on_out=lambda chunk: None,
                on_stop=lambda *args, **kwargs: None,
                on_status_change=statuses.append,
                tests=[_DummyTest("abc")],
                test_factory=_DummyTest,
                schedule_async=lambda callback, delay=0: callback(),
                show_status=statuses.append,
            )
            tester.prog_out = ["stale"]
            tester.run_test(0)
            self.assertEqual(process.calls[0], "compile")
            self.assertEqual(process.calls[1], "run")
            self.assertEqual(process.calls[2], ("write", "abc"))
            self.assertEqual(tester.prog_out[0], "")
            self.assertEqual(statuses[0], "COMPILE")

    def test_set_tests_rebuilds_output_slots_and_iteration(self) -> None:
        with _patched_sublime():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel_tester")
            process = _FakeProcessManager()
            tester = module.RunPanelTester(
                process,
                on_insert=lambda chunk: None,
                on_out=lambda chunk: None,
                on_stop=lambda *args, **kwargs: None,
                on_status_change=lambda status: None,
                tests=[_DummyTest("abc")],
                test_factory=_DummyTest,
                schedule_async=lambda callback, delay=0: callback(),
                show_status=lambda: None,
            )
            tester.prog_out = ["old-output"]
            tester.set_tests(["x", "y"])
            self.assertEqual(len(tester.tests), 2)
            self.assertEqual(tester.prog_out, ["old-output", ""])
            self.assertEqual(tester.test_iter, 2)


if __name__ == "__main__":
    unittest.main()
