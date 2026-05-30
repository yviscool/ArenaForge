import importlib
import sys
import types
import unittest
from contextlib import contextmanager


@contextmanager
def _patched_test_actions():
    module_names = (
        "sublime",
        "arena_forge.adapters.sublime.run_panel.test_actions",
    )
    originals = {name: sys.modules.get(name) for name in module_names}
    sys.modules["sublime"] = types.SimpleNamespace(Region=lambda a, b=None: (a, b))
    sys.modules.pop("arena_forge.adapters.sublime.run_panel.test_actions", None)
    try:
        yield
    finally:
        for name, original in originals.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original


class RunPanelTestActionsTests(unittest.TestCase):
    def test_handle_test_event_uses_shared_termination_helper_for_stop(self) -> None:
        with _patched_test_actions():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel.test_actions")
            calls = []
            tester = object()
            module.terminate_tester_with_logging = lambda value: calls.append(value)
            command = types.SimpleNamespace(view=object(), state=types.SimpleNamespace(tester=tester))

            module.handle_test_event(command, 0, "test-stop")

            self.assertEqual(calls, [tester])

    def test_clear_all_tests_resets_state_and_requests_a_fresh_test(self) -> None:
        with _patched_test_actions():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel.test_actions")
            calls = []
            tester = types.SimpleNamespace(
                proc_run=True,
                tests=[object()],
                prog_out=["out"],
                test_iter=1,
                running_test=0,
                running_new=True,
            )
            module.terminate_tester_with_logging = lambda value: calls.append(("terminate", value))
            command = types.SimpleNamespace(
                view=types.SimpleNamespace(run_command=lambda name, payload: calls.append(("run", name, payload))),
                state=types.SimpleNamespace(
                    tester=tester,
                    reset_panel_runtime=lambda: calls.append(("reset_runtime", None)),
                ),
                clear_all=lambda: calls.append(("clear_all", None)),
                memorize_tests=lambda: calls.append(("memorize_tests", None)),
            )

            module.clear_all_tests(command)

            self.assertEqual(tester.tests, [])
            self.assertEqual(tester.prog_out, [])
            self.assertEqual(tester.test_iter, 0)
            self.assertIsNone(tester.running_test)
            self.assertIsNone(tester.running_new)
            self.assertEqual(
                calls,
                [
                    ("terminate", tester),
                    ("clear_all", None),
                    ("reset_runtime", None),
                    ("memorize_tests", None),
                    ("run", "test_manager", {"action": "new_test"}),
                ],
            )


if __name__ == "__main__":
    unittest.main()
