import importlib
import sys
import types
import unittest
from contextlib import contextmanager


class _FakeDiagnosticsView:
    def __init__(self, view_id: int = 1) -> None:
        self._view_id = view_id
        self.erased_regions = []
        self.statuses = []
        self.added_regions = []

    def id(self) -> int:
        return self._view_id

    def erase_regions(self, key: str) -> None:
        self.erased_regions.append(key)

    def erase_status(self, key: str) -> None:
        self.statuses.append(("erase", key))

    def set_status(self, key: str, value: str) -> None:
        self.statuses.append((key, value))

    def text_point(self, line: int, column: int):
        return (line, column)

    def word(self, point):
        return point

    def add_regions(self, key: str, regions, scope: str, icon: str, flags: int) -> None:
        self.added_regions.append((key, list(regions), scope, icon, flags))


@contextmanager
def _patched_sublime():
    original_sublime = sys.modules.get("sublime")
    original_sublime_plugin = sys.modules.get("sublime_plugin")
    original_settings_bridge = sys.modules.get("arena_forge.adapters.sublime.settings_bridge")
    sys.modules["sublime"] = types.SimpleNamespace(
        Region=lambda begin, end=None: (begin, end),
        platform=lambda: "windows",
        set_timeout=lambda callback, delay=0: callback(),
        set_timeout_async=lambda callback, delay=0: callback(),
        DRAW_NO_FILL=0,
    )
    sys.modules["sublime_plugin"] = types.SimpleNamespace(TextCommand=object, EventListener=object)
    sys.modules["arena_forge.adapters.sublime.settings_bridge"] = types.SimpleNamespace(
        get_settings=lambda: {"lint_enabled": True, "run_settings": []},
        is_lang_view=lambda view, lang: False,
    )
    sys.modules.pop("arena_forge.adapters.sublime.diagnostics_commands", None)
    try:
        yield
    finally:
        sys.modules.pop("arena_forge.adapters.sublime.diagnostics_commands", None)
        if original_sublime is None:
            sys.modules.pop("sublime", None)
        else:
            sys.modules["sublime"] = original_sublime
        if original_sublime_plugin is None:
            sys.modules.pop("sublime_plugin", None)
        else:
            sys.modules["sublime_plugin"] = original_sublime_plugin
        if original_settings_bridge is None:
            sys.modules.pop("arena_forge.adapters.sublime.settings_bridge", None)
        else:
            sys.modules["arena_forge.adapters.sublime.settings_bridge"] = original_settings_bridge


class DiagnosticsCommandsTests(unittest.TestCase):
    def test_collect_diagnostics_logs_expected_run_failures(self) -> None:
        with _patched_sublime():
            module = importlib.import_module("arena_forge.adapters.sublime.diagnostics_commands")
            logs = []
            module.product_log_message = lambda key, **kwargs: logs.append((key, kwargs))
            command = module.InteliSenseCommand.__new__(module.InteliSenseCommand)
            command._diagnostics_service = lambda: types.SimpleNamespace(
                run=lambda **kwargs: (_ for _ in ()).throw(OSError("boom"))
            )

            command._collect_diagnostics(
                view=_FakeDiagnosticsView(7),
                compile_cmd="g++ {source_file}",
                source="int main() {}\n",
                file_dir_path="C:\\repo",
                change_count=1,
                generation=2,
            )

            self.assertEqual(logs, [("error.parse_errors_failed", {})])

    def test_apply_diagnostics_logs_invalid_report_shape(self) -> None:
        with _patched_sublime():
            module = importlib.import_module("arena_forge.adapters.sublime.diagnostics_commands")
            module._VIEW_STATES.clear()
            logs = []
            module.product_log_message = lambda key, **kwargs: logs.append((key, kwargs))
            view = _FakeDiagnosticsView(11)
            module._VIEW_STATES[11] = module._DiagnosticsState(enabled=True, generation=3)
            command = module.InteliSenseCommand.__new__(module.InteliSenseCommand)

            command._apply_diagnostics(
                view=view,
                report=object(),
                change_count=9,
                generation=3,
            )

            self.assertEqual(logs, [("error.parse_errors_failed", {})])
            self.assertIsNone(module._VIEW_STATES[11].last_change_count)


if __name__ == "__main__":
    unittest.main()
