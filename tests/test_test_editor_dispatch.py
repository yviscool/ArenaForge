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
    sys.modules.pop("arena_forge.adapters.sublime.test_editor.dispatch", None)
    sys.modules.pop("arena_forge.adapters.sublime.shared.messages", None)
    sys.modules.pop("arena_forge.adapters.sublime.view_actions", None)
    try:
        yield
    finally:
        sys.modules.pop("arena_forge.adapters.sublime.test_editor.dispatch", None)
        sys.modules.pop("arena_forge.adapters.sublime.shared.messages", None)
        sys.modules.pop("arena_forge.adapters.sublime.view_actions", None)
        if original_sublime is None:
            sys.modules.pop("sublime", None)
        else:
            sys.modules["sublime"] = original_sublime


class TestEditorDispatchTests(unittest.TestCase):
    def test_init_action_forwards_only_editor_fields(self) -> None:
        with _patched_sublime():
            module = importlib.import_module("arena_forge.adapters.sublime.test_editor.dispatch")
            init_calls = []
            command = types.SimpleNamespace(
                view=object(),
                state=types.SimpleNamespace(tester=None),
                insert_text=lambda edit: None,
                insert_cb=lambda edit: None,
                sync_read_only=lambda: None,
                init=lambda edit, test="", source_view_id=None, test_id=None: init_calls.append(
                    (edit, test, source_view_id, test_id)
                ),
            )

            result = module.dispatch_test_editor_action(
                command,
                edit="EDIT",
                action="init",
                test="sample",
                source_view_id=11,
                test_id=2,
            )

            self.assertIsNone(result)
            self.assertEqual(init_calls, [("EDIT", "sample", 11, 2)])

    def test_replace_action_forwards_region_and_text(self) -> None:
        with _patched_sublime():
            module = importlib.import_module("arena_forge.adapters.sublime.test_editor.dispatch")
            replace_calls = []
            command = types.SimpleNamespace(
                view=object(),
                state=types.SimpleNamespace(tester=None),
                sync_read_only=lambda: None,
            )
            module.replace_region = lambda view, edit, region, text: replace_calls.append((view, edit, region, text))

            module.dispatch_test_editor_action(command, edit="EDIT", action="replace", region=(1, 3), text="abc")

            self.assertEqual(replace_calls, [(command.view, "EDIT", (1, 3), "abc")])

    def test_unknown_action_is_ignored(self) -> None:
        with _patched_sublime():
            module = importlib.import_module("arena_forge.adapters.sublime.test_editor.dispatch")
            command = types.SimpleNamespace(view=object(), state=types.SimpleNamespace(tester=None))

            result = module.dispatch_test_editor_action(command, edit=None, action="close")

            self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
