import importlib
import json
import sys
import types
import unittest
from contextlib import contextmanager
from pathlib import Path


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
    def test_translate_reads_default_locale_when_application_is_unavailable(self) -> None:
        with _patched_messages(
            types.SimpleNamespace(get_application=lambda: (_ for _ in ()).throw(RuntimeError("not initialized")))
        ):
            module = importlib.import_module("arena_forge.adapters.sublime.shared.messages")

            result = module.translate("status.running")
            en_catalog = json.loads(Path("arena_forge/locales/en.json").read_text(encoding="utf-8"))
            self.assertEqual(result, en_catalog["status.running"])

    def test_translate_uses_requested_locale_when_available(self) -> None:
        with _patched_messages(
            types.SimpleNamespace(get_application=lambda: (_ for _ in ()).throw(RuntimeError("not initialized")))
        ):
            module = importlib.import_module("arena_forge.adapters.sublime.shared.messages")

            result = module.translate("status.stopped", locale="zh-Hans")

            self.assertEqual(result, "已停止")

    def test_translate_prefers_application_locale(self) -> None:
        calls = []

        class _Translator:
            def translate(self, key, locale=None, **kwargs):
                calls.append((key, locale, kwargs))
                return f"{locale}:{key}"

        with _patched_messages(
            types.SimpleNamespace(get_application=lambda: types.SimpleNamespace(translator=_Translator()))
        ):
            module = importlib.import_module("arena_forge.adapters.sublime.shared.messages")

            self.assertEqual(module.translate("status.running"), "None:status.running")
            self.assertEqual(calls, [("status.running", None, {})])


if __name__ == "__main__":
    unittest.main()
