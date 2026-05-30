import importlib
import sys
import types
import unittest
from contextlib import contextmanager


@contextmanager
def _patched_messages(settings_bridge_module):
    original_sublime = sys.modules.get("sublime")
    original_settings_bridge = sys.modules.get("arena_forge.adapters.sublime.shared.settings_bridge")
    sys.modules["sublime"] = types.SimpleNamespace(
        status_message=lambda message: None,
        error_message=lambda message: None,
    )
    sys.modules["arena_forge.adapters.sublime.shared.settings_bridge"] = settings_bridge_module
    sys.modules.pop("arena_forge.adapters.sublime.shared.messages", None)
    try:
        yield
    finally:
        sys.modules.pop("arena_forge.adapters.sublime.shared.messages", None)
        if original_sublime is None:
            sys.modules.pop("sublime", None)
        else:
            sys.modules["sublime"] = original_sublime
        if original_settings_bridge is None:
            sys.modules.pop("arena_forge.adapters.sublime.shared.settings_bridge", None)
        else:
            sys.modules["arena_forge.adapters.sublime.shared.settings_bridge"] = original_settings_bridge


class MessagesTests(unittest.TestCase):
    def test_translate_falls_back_when_application_is_unavailable(self) -> None:
        def raise_runtime_error():
            raise RuntimeError("not initialized")

        with _patched_messages(types.SimpleNamespace(get_application=raise_runtime_error)):
            module = importlib.import_module("arena_forge.adapters.sublime.shared.messages")

            result = module.translate("status.running")

            self.assertEqual(result, "Running")

    def test_translate_falls_back_when_translator_raises_value_error(self) -> None:
        translator = types.SimpleNamespace(
            translate=lambda *args, **kwargs: (_ for _ in ()).throw(ValueError("bad locale payload"))
        )
        application = types.SimpleNamespace(translator=translator)
        with _patched_messages(types.SimpleNamespace(get_application=lambda: application)):
            module = importlib.import_module("arena_forge.adapters.sublime.shared.messages")

            result = module.translate("status.stopped")

            self.assertEqual(result, "Stopped")


if __name__ == "__main__":
    unittest.main()
