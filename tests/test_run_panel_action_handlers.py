import sys
import types
import unittest
from contextlib import contextmanager


@contextmanager
def _patched_sublime():
    original = sys.modules.get("sublime")
    fake = types.SimpleNamespace(
        Region=lambda a, b=None: (a, b),
        Phantom=object,
        PhantomSet=object,
        LAYOUT_BLOCK=0,
        platform=lambda: "windows",
        status_message=lambda message: None,
        error_message=lambda message: None,
        DRAW_NO_FILL=0,
        DRAW_STIPPLED_UNDERLINE=0,
        DRAW_NO_OUTLINE=0,
        DRAW_EMPTY_AS_OVERWRITE=0,
        HIDDEN=0,
        HOVER_TEXT=1,
        TextCommand=object,
    )
    sys.modules["sublime"] = fake
    sys.modules["sublime_plugin"] = types.SimpleNamespace(TextCommand=object, EventListener=object)
    try:
        yield
    finally:
        if original is None:
            sys.modules.pop("sublime", None)
        else:
            sys.modules["sublime"] = original
        sys.modules.pop("sublime_plugin", None)


class RunPanelActionHandlersTests(unittest.TestCase):
    def test_enable_edit_mode_is_the_only_handler_that_skips_read_only_sync(self) -> None:
        with _patched_sublime():
            from arena_forge.adapters.sublime.run_panel.commands import _ACTION_HANDLERS

            sync_false = [name for name, (_, sync) in _ACTION_HANDLERS.items() if not sync]
            self.assertEqual(sync_false, ["enable_edit_mode"])

    def test_close_command_logs_process_termination_failures(self) -> None:
        with _patched_sublime():
            from arena_forge.adapters.sublime.run_panel.commands import _terminate_command

            logs = []
            import arena_forge.adapters.sublime.shared.messages as messages_module
            messages_module.product_log_message = lambda key, **kwargs: logs.append((key, kwargs))

            def fail_terminate() -> None:
                raise OSError("boom")

            command = types.SimpleNamespace(
                state=types.SimpleNamespace(tester=types.SimpleNamespace(terminate=fail_terminate)),
                view=object(),
            )

            _terminate_command(command, None, object())

            self.assertEqual(logs, [("error.process_termination_failed", {})])

    def test_close_command_ignores_missing_tester(self) -> None:
        with _patched_sublime():
            from arena_forge.adapters.sublime.run_panel.commands import _terminate_command

            logs = []
            import arena_forge.adapters.sublime.shared.messages as messages_module
            messages_module.product_log_message = lambda key, **kwargs: logs.append((key, kwargs))

            command = types.SimpleNamespace(state=types.SimpleNamespace(tester=None), view=object())

            _terminate_command(command, None, object())

            self.assertEqual(logs, [])


if __name__ == "__main__":
    unittest.main()
