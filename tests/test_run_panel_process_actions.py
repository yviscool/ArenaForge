import importlib
import sys
import types
import unittest
from contextlib import contextmanager


@contextmanager
def _patched_sublime():
    original_sublime = sys.modules.get("sublime")
    original_messages = sys.modules.get("arena_forge.adapters.sublime.shared.messages")
    scheduled = []
    sys.modules["sublime"] = types.SimpleNamespace(
        set_timeout_async=lambda callback, delay=0: scheduled.append((callback, delay))
    )
    sys.modules["arena_forge.adapters.sublime.shared.messages"] = types.SimpleNamespace(
        product_log_message=lambda *args, **kwargs: None
    )
    sys.modules.pop("arena_forge.adapters.sublime.run_panel.process_actions", None)
    try:
        yield scheduled
    finally:
        sys.modules.pop("arena_forge.adapters.sublime.run_panel.process_actions", None)
        if original_messages is None:
            sys.modules.pop("arena_forge.adapters.sublime.shared.messages", None)
        else:
            sys.modules["arena_forge.adapters.sublime.shared.messages"] = original_messages
        if original_sublime is None:
            sys.modules.pop("sublime", None)
        else:
            sys.modules["sublime"] = original_sublime


class RunPanelProcessActionsTests(unittest.TestCase):
    def test_terminate_tester_returns_true_on_success(self) -> None:
        with _patched_sublime():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel.process_actions")
            calls = []
            tester = types.SimpleNamespace(terminate=lambda: calls.append("terminated"))

            result = module.terminate_tester(tester)

            self.assertTrue(result)
            self.assertEqual(calls, ["terminated"])

    def test_terminate_tester_calls_failure_callback_for_expected_errors(self) -> None:
        with _patched_sublime():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel.process_actions")
            failures = []

            def fail_terminate() -> None:
                raise OSError("boom")

            result = module.terminate_tester(
                types.SimpleNamespace(terminate=fail_terminate),
                on_failure=lambda: failures.append("failed"),
            )

            self.assertFalse(result)
            self.assertEqual(failures, ["failed"])

    def test_terminate_tester_with_logging_uses_shared_failure_message(self) -> None:
        with _patched_sublime():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel.process_actions")
            logs = []
            sys.modules["arena_forge.adapters.sublime.shared.messages"].product_log_message = (
                lambda key, **kwargs: logs.append((key, kwargs))
            )

            result = module.terminate_tester_with_logging(
                types.SimpleNamespace(terminate=lambda: (_ for _ in ()).throw(OSError("boom")))
            )

            self.assertFalse(result)
            self.assertEqual(logs, [("error.process_termination_failed", {})])

    def test_terminate_command_tester_with_logging_uses_command_state(self) -> None:
        with _patched_sublime():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel.process_actions")
            calls = []
            command = types.SimpleNamespace(
                state=types.SimpleNamespace(
                    tester=types.SimpleNamespace(terminate=lambda: calls.append("terminated"))
                )
            )

            result = module.terminate_command_tester_with_logging(command)

            self.assertTrue(result)
            self.assertEqual(calls, ["terminated"])

    def test_schedule_test_manager_action_dispatches_expected_payload(self) -> None:
        with _patched_sublime() as scheduled:
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel.process_actions")
            calls = []
            view = types.SimpleNamespace(run_command=lambda name, payload: calls.append((name, payload)))

            module.schedule_test_manager_action(view, "enable_edit_mode", delay=25, flag=True)

            self.assertEqual(len(scheduled), 1)
            callback, delay = scheduled[0]
            self.assertEqual(delay, 25)
            callback()
            self.assertEqual(calls, [("test_manager", {"action": "enable_edit_mode", "flag": True})])

    def test_schedule_test_manager_command_preserves_full_command_payload(self) -> None:
        with _patched_sublime() as scheduled:
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel.process_actions")
            calls = []
            view = types.SimpleNamespace(run_command=lambda name, payload: calls.append((name, payload)))

            module.schedule_test_manager_command(view, {"action": "make_opd", "load_session": True}, delay=30)

            callback, delay = scheduled[0]
            self.assertEqual(delay, 30)
            callback()
            self.assertEqual(calls, [("test_manager", {"action": "make_opd", "load_session": True})])


if __name__ == "__main__":
    unittest.main()
