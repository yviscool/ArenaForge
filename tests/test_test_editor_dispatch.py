import importlib
import sys
import types
import unittest
from contextlib import contextmanager


@contextmanager
def _patched_sublime():
    original_sublime = sys.modules.get("sublime")
    sys.modules["sublime"] = types.SimpleNamespace(
        Region=lambda begin, end=None: (begin, end),
        status_message=lambda message: None,
        error_message=lambda message: None,
    )
    sys.modules.pop("arena_forge.adapters.sublime.test_editor_dispatch", None)
    sys.modules.pop("arena_forge.adapters.sublime.messages", None)
    sys.modules.pop("arena_forge.adapters.sublime.view_actions", None)
    try:
        yield
    finally:
        sys.modules.pop("arena_forge.adapters.sublime.test_editor_dispatch", None)
        sys.modules.pop("arena_forge.adapters.sublime.messages", None)
        sys.modules.pop("arena_forge.adapters.sublime.view_actions", None)
        if original_sublime is None:
            sys.modules.pop("sublime", None)
        else:
            sys.modules["sublime"] = original_sublime


class TestEditorDispatchTests(unittest.TestCase):
    def test_close_action_logs_process_termination_failures(self) -> None:
        with _patched_sublime():
            module = importlib.import_module("arena_forge.adapters.sublime.test_editor_dispatch")
            logs = []
            module.product_log_message = lambda key, **kwargs: logs.append((key, kwargs))

            def fail_terminate() -> None:
                raise OSError("boom")

            command = types.SimpleNamespace(
                view=object(),
                state=types.SimpleNamespace(tester=types.SimpleNamespace(terminate=fail_terminate)),
                sync_read_only=lambda: None,
            )

            module.dispatch_test_editor_action(command, edit=None, action="close")

            self.assertEqual(logs, [("error.process_termination_failed", {})])

    def test_close_action_ignores_missing_tester(self) -> None:
        with _patched_sublime():
            module = importlib.import_module("arena_forge.adapters.sublime.test_editor_dispatch")
            logs = []
            module.product_log_message = lambda key, **kwargs: logs.append((key, kwargs))
            command = types.SimpleNamespace(
                view=object(),
                state=types.SimpleNamespace(tester=None),
                sync_read_only=lambda: None,
            )

            result = module.dispatch_test_editor_action(command, edit=None, action="close")

            self.assertTrue(result)
            self.assertEqual(logs, [])


if __name__ == "__main__":
    unittest.main()
