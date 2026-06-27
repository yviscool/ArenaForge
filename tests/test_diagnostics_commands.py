import importlib
import sys
import types
import unittest
from contextlib import contextmanager

from arena_forge.core.domain import LanguageProfile


class _FakeDiagnosticsView:
    def __init__(
        self,
        view_id: int = 1,
        *,
        file_name: str = r"C:\repo\main.cpp",
        source_text: str = "int main() {}\n",
    ) -> None:
        self._view_id = view_id
        self._file_name = file_name
        self._source_text = source_text
        self._change_count = 0
        self.erased_regions = []
        self.statuses = []
        self.added_regions = []

    def id(self) -> int:
        return self._view_id

    def file_name(self) -> str:
        return self._file_name

    def change_count(self) -> int:
        return self._change_count

    def set_change_count(self, value: int) -> None:
        self._change_count = value

    def size(self) -> int:
        return len(self._source_text)

    def substr(self, region) -> str:
        return self._source_text

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
    original_settings_bridge = sys.modules.get("arena_forge.adapters.sublime.shared.settings_bridge")
    sys.modules["sublime"] = types.SimpleNamespace(
        Region=lambda begin, end=None: (begin, end),
        platform=lambda: "windows",
        set_timeout=lambda callback, delay=0: callback(),
        set_timeout_async=lambda callback, delay=0: callback(),
        DRAW_NO_FILL=0,
    )
    sys.modules["sublime_plugin"] = types.SimpleNamespace(TextCommand=object, EventListener=object)
    sys.modules["arena_forge.adapters.sublime.shared.settings_bridge"] = types.SimpleNamespace(
        get_settings=lambda: {"lint_enabled": True},
        get_language_profiles=lambda: (
            LanguageProfile(
                name="C++",
                extensions=("cpp",),
                compile_cmd="g++",
                run_cmd="main.exe",
                lint_compile_cmd="g++ -fsyntax-only",
            ),
        ),
        is_lang_view=lambda view, lang: False,
    )
    sys.modules.pop("arena_forge.adapters.sublime.diagnostics.commands", None)
    try:
        yield
    finally:
        sys.modules.pop("arena_forge.adapters.sublime.diagnostics.commands", None)
        if original_sublime is None:
            sys.modules.pop("sublime", None)
        else:
            sys.modules["sublime"] = original_sublime
        if original_sublime_plugin is None:
            sys.modules.pop("sublime_plugin", None)
        else:
            sys.modules["sublime_plugin"] = original_sublime_plugin
        if original_settings_bridge is None:
            sys.modules.pop("arena_forge.adapters.sublime.shared.settings_bridge", None)
        else:
            sys.modules["arena_forge.adapters.sublime.shared.settings_bridge"] = original_settings_bridge


class DiagnosticsCommandsTests(unittest.TestCase):
    def test_run_sense_uses_unique_scratch_labels_per_generation(self) -> None:
        with _patched_sublime():
            module = importlib.import_module("arena_forge.adapters.sublime.diagnostics.commands")
            module._VIEW_STATES.clear()
            labels = []
            view = _FakeDiagnosticsView(7)
            view.set_change_count(1)
            command = module.IntelliSenseCommand.__new__(module.IntelliSenseCommand)
            command.view = view
            command.get_compile_cmd = lambda: "g++ {source_file}"
            command._diagnostics_service = lambda: types.SimpleNamespace(
                run=lambda **kwargs: labels.append(kwargs["scratch_label"])
                or types.SimpleNamespace(issues=(), output="", command=(), runtime_ms=0, timed_out=False)
            )

            command.run_sense(force=True)
            view.set_change_count(2)
            command.run_sense(force=True)

            self.assertEqual(labels, ["view-7-1", "view-7-2"])

    def test_run_sense_clears_existing_marks_before_failed_refresh(self) -> None:
        with _patched_sublime():
            module = importlib.import_module("arena_forge.adapters.sublime.diagnostics.commands")
            module._VIEW_STATES.clear()
            view = _FakeDiagnosticsView(9)
            view.set_change_count(3)
            command = module.IntelliSenseCommand.__new__(module.IntelliSenseCommand)
            command.view = view
            command.get_compile_cmd = lambda: "g++ {source_file}"
            command._diagnostics_service = lambda: types.SimpleNamespace(
                run=lambda **kwargs: (_ for _ in ()).throw(OSError("boom"))
            )

            command.run_sense()

            self.assertEqual(view.erased_regions[:2], ["error_marks", "warning_marks"])
            self.assertEqual(view.statuses[0], ("erase", "compile_error"))

    def test_collect_diagnostics_skips_stale_generations_before_running_subprocess(self) -> None:
        with _patched_sublime():
            module = importlib.import_module("arena_forge.adapters.sublime.diagnostics.commands")
            module._VIEW_STATES.clear()
            calls = []
            view = _FakeDiagnosticsView(13)
            module._VIEW_STATES[13] = module._DiagnosticsState(enabled=True, generation=5)
            command = module.IntelliSenseCommand.__new__(module.IntelliSenseCommand)
            command._diagnostics_service = lambda: types.SimpleNamespace(
                run=lambda **kwargs: calls.append(kwargs)
                or types.SimpleNamespace(issues=(), output="", command=(), runtime_ms=0, timed_out=False)
            )

            command._collect_diagnostics(
                view=view,
                compile_cmd="g++ {source_file}",
                source="int main() {}\n",
                source_file=r"C:\repo\main.cpp",
                file_dir_path="C:\\repo",
                change_count=1,
                generation=4,
                timeout_ms=3000,
            )

            self.assertEqual(calls, [])

    def test_collect_diagnostics_logs_expected_run_failures(self) -> None:
        with _patched_sublime():
            module = importlib.import_module("arena_forge.adapters.sublime.diagnostics.commands")
            module._VIEW_STATES.clear()
            logs = []
            module.product_log_message = lambda key, **kwargs: logs.append((key, kwargs))
            module._VIEW_STATES[7] = module._DiagnosticsState(enabled=True, generation=2)
            command = module.IntelliSenseCommand.__new__(module.IntelliSenseCommand)
            command._diagnostics_service = lambda: types.SimpleNamespace(
                run=lambda **kwargs: (_ for _ in ()).throw(OSError("boom"))
            )

            command._collect_diagnostics(
                view=_FakeDiagnosticsView(7),
                compile_cmd="g++ {source_file}",
                source="int main() {}\n",
                source_file=r"C:\repo\main.cpp",
                file_dir_path="C:\\repo",
                change_count=1,
                generation=2,
                timeout_ms=3000,
            )

            self.assertEqual(logs, [("error.parse_errors_failed", {})])

    def test_apply_diagnostics_logs_invalid_report_shape(self) -> None:
        with _patched_sublime():
            module = importlib.import_module("arena_forge.adapters.sublime.diagnostics.commands")
            module._VIEW_STATES.clear()
            logs = []
            module.product_log_message = lambda key, **kwargs: logs.append((key, kwargs))
            view = _FakeDiagnosticsView(11)
            module._VIEW_STATES[11] = module._DiagnosticsState(enabled=True, generation=3)
            command = module.IntelliSenseCommand.__new__(module.IntelliSenseCommand)

            command._apply_diagnostics(
                view=view,
                report=object(),
                change_count=9,
                generation=3,
            )

            self.assertEqual(logs, [("error.parse_errors_failed", {})])
            self.assertIsNone(module._VIEW_STATES[11].last_change_count)

    def test_schedule_sense_bumps_generation_without_settings_lookup(self) -> None:
        with _patched_sublime():
            module = importlib.import_module("arena_forge.adapters.sublime.diagnostics.commands")
            module._VIEW_STATES.clear()
            call_log = []
            view = _FakeDiagnosticsView(42)
            view.set_change_count(1)

            command = module.IntelliSenseCommand.__new__(module.IntelliSenseCommand)
            command.view = view
            command.get_compile_cmd = lambda: (call_log.append("get_compile_cmd"), "g++ {source_file}")[1]
            command._diagnostics_service = lambda: types.SimpleNamespace(
                run=lambda **kwargs: types.SimpleNamespace(issues=(), output="", command=(), runtime_ms=0, timed_out=False)
            )

            state = module._state_for(view)
            state.enabled = True

            call_log.clear()
            command.schedule_sense()

            self.assertEqual(state.generation, 2)
            self.assertEqual(call_log.count("get_compile_cmd"), 1)
            self.assertEqual(call_log[-1], "get_compile_cmd")

    def test_schedule_sense_clears_marks_on_content_change(self) -> None:
        with _patched_sublime():
            module = importlib.import_module("arena_forge.adapters.sublime.diagnostics.commands")
            module._VIEW_STATES.clear()
            view = _FakeDiagnosticsView(55)
            view.set_change_count(1)

            command = module.IntelliSenseCommand.__new__(module.IntelliSenseCommand)
            command.view = view
            command.get_compile_cmd = lambda: None

            state = module._state_for(view)
            state.enabled = True
            state.last_change_count = 0

            command.schedule_sense()

            self.assertIn("error_marks", view.erased_regions)
            self.assertIn("warning_marks", view.erased_regions)
            self.assertIn(("erase", "compile_error"), view.statuses)


if __name__ == "__main__":
    unittest.main()
