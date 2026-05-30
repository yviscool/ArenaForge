import importlib
import sys
import types
import unittest
from contextlib import contextmanager


@contextmanager
def _patched_sublime(callbacks):
    original_sublime = sys.modules.get("sublime")
    original_sublime_plugin = sys.modules.get("sublime_plugin")
    original_messages = sys.modules.get("arena_forge.adapters.sublime.shared.messages")
    original_package_resources = sys.modules.get("arena_forge.adapters.sublime.shared.package_resources")
    original_root_bridge = sys.modules.get("arena_forge.adapters.sublime.root_bridge")
    original_settings_bridge = sys.modules.get("arena_forge.adapters.sublime.shared.settings_bridge")
    sys.modules["sublime"] = types.SimpleNamespace(
        HIDE_ON_MOUSE_MOVE_AWAY=0,
        MONOSPACE_FONT=0,
        HIDDEN=0,
        DRAW_SOLID_UNDERLINE=0,
        Region=lambda begin, end=None: (begin, end),
        set_timeout_async=lambda callback, delay=0: callbacks.append((callback, delay)),
    )
    sys.modules["sublime_plugin"] = types.SimpleNamespace(TextCommand=object, EventListener=object)
    sys.modules["arena_forge.adapters.sublime.shared.messages"] = types.SimpleNamespace(
        status_message=lambda key, **kwargs: None
    )
    sys.modules["arena_forge.adapters.sublime.shared.package_resources"] = types.SimpleNamespace(
        ARROW_RIGHT_ICON_RESOURCE="arrow",
        TEST_SYNTAX_RESOURCE="syntax",
    )
    sys.modules["arena_forge.adapters.sublime.root_bridge"] = types.SimpleNamespace(
        get_highlight_function=lambda: (lambda value: value)
    )
    sys.modules["arena_forge.adapters.sublime.shared.settings_bridge"] = types.SimpleNamespace(
        get_settings=lambda: {"close_sidebar": True}
    )
    sys.modules.pop("arena_forge.adapters.sublime.debug_overlay.commands", None)
    try:
        yield
    finally:
        sys.modules.pop("arena_forge.adapters.sublime.debug_overlay.commands", None)
        if original_sublime is None:
            sys.modules.pop("sublime", None)
        else:
            sys.modules["sublime"] = original_sublime
        if original_sublime_plugin is None:
            sys.modules.pop("sublime_plugin", None)
        else:
            sys.modules["sublime_plugin"] = original_sublime_plugin
        if original_messages is None:
            sys.modules.pop("arena_forge.adapters.sublime.shared.messages", None)
        else:
            sys.modules["arena_forge.adapters.sublime.shared.messages"] = original_messages
        if original_package_resources is None:
            sys.modules.pop("arena_forge.adapters.sublime.shared.package_resources", None)
        else:
            sys.modules["arena_forge.adapters.sublime.shared.package_resources"] = original_package_resources
        if original_root_bridge is None:
            sys.modules.pop("arena_forge.adapters.sublime.root_bridge", None)
        else:
            sys.modules["arena_forge.adapters.sublime.root_bridge"] = original_root_bridge
        if original_settings_bridge is None:
            sys.modules.pop("arena_forge.adapters.sublime.shared.settings_bridge", None)
        else:
            sys.modules["arena_forge.adapters.sublime.shared.settings_bridge"] = original_settings_bridge


class DebugOverlayCommandsTests(unittest.TestCase):
    def test_schedule_sidebar_hide_only_uses_supported_window_api(self) -> None:
        callbacks = []
        with _patched_sublime(callbacks):
            module = importlib.import_module("arena_forge.adapters.sublime.debug_overlay.commands")
            calls = []
            window = types.SimpleNamespace(set_sidebar_visible=lambda visible: calls.append(visible))

            module._schedule_sidebar_hide(window)

            self.assertEqual(len(callbacks), 1)
            self.assertEqual(callbacks[0][1], 50)
            callbacks[0][0]()
            self.assertEqual(calls, [False])

    def test_schedule_sidebar_hide_skips_windows_without_sidebar_api(self) -> None:
        callbacks = []
        with _patched_sublime(callbacks):
            module = importlib.import_module("arena_forge.adapters.sublime.debug_overlay.commands")

            module._schedule_sidebar_hide(object())

            self.assertEqual(callbacks, [])


if __name__ == "__main__":
    unittest.main()
