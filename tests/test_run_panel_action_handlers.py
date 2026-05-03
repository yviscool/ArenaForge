import importlib
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
        LAYOUT_BLOCK=0,
        platform=lambda: "windows",
        status_message=lambda message: None,
        error_message=lambda message: None,
    )
    sys.modules["sublime"] = fake
    sys.modules.pop("arena_forge.adapters.sublime.run_panel_action_handlers", None)
    sys.modules.pop("arena_forge.adapters.sublime.messages", None)
    sys.modules.pop("arena_forge.adapters.sublime.view_actions", None)
    try:
        yield
    finally:
        sys.modules.pop("arena_forge.adapters.sublime.run_panel_action_handlers", None)
        sys.modules.pop("arena_forge.adapters.sublime.messages", None)
        sys.modules.pop("arena_forge.adapters.sublime.view_actions", None)
        if original is None:
            sys.modules.pop("sublime", None)
        else:
            sys.modules["sublime"] = original


class RunPanelActionHandlersTests(unittest.TestCase):
    def test_registry_matches_supported_action_surface(self) -> None:
        with _patched_sublime():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel_action_handlers")
            catalog = importlib.import_module("arena_forge.adapters.sublime.command_action_catalog")
            context = module.RunPanelActionContext(command=object(), edit=object(), request=object())

            handlers = module.build_test_manager_action_handlers(context)

            self.assertEqual(tuple(sorted(handlers)), tuple(sorted(catalog.SUPPORTED_TEST_MANAGER_ACTIONS)))

    def test_enable_edit_mode_is_the_only_handler_that_skips_read_only_sync(self) -> None:
        with _patched_sublime():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel_action_handlers")
            context = module.RunPanelActionContext(command=object(), edit=object(), request=object())

            handlers = module.build_test_manager_action_handlers(context)

            self.assertFalse(handlers["enable_edit_mode"].sync_read_only)
            sync_false = [name for name, handler in handlers.items() if not handler.sync_read_only]
            self.assertEqual(sync_false, ["enable_edit_mode"])


if __name__ == "__main__":
    unittest.main()
