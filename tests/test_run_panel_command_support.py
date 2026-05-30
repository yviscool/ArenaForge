import importlib
import sys
import types
import unittest
from contextlib import contextmanager
from types import SimpleNamespace


class _FakeRegion:
    def __init__(self, a, b=None):
        self.a = a
        self.b = a if b is None else b

    def __eq__(self, other):
        return isinstance(other, _FakeRegion) and (self.a, self.b) == (other.a, other.b)

    def __repr__(self):
        return f"_FakeRegion(a={self.a}, b={self.b})"

    def begin(self):
        return min(self.a, self.b)

    def end(self):
        return max(self.a, self.b)


class _FakeSelection(list):
    pass


class _FakeView:
    def __init__(self, text="", *, selections=None, regions=None):
        self.text = text
        self._selection = _FakeSelection(selections or [_FakeRegion(len(text), len(text))])
        self._regions = {key: list(value) for key, value in (regions or {}).items()}
        self.added_regions = []
        self.erased_regions = []
        self.statuses = {}

    def line(self, location):
        point = location.a if isinstance(location, _FakeRegion) else location
        start = self.text.rfind("\n", 0, point) + 1
        end = self.text.find("\n", point)
        if end == -1:
            end = len(self.text)
        return _FakeRegion(start, end)

    def sel(self):
        return self._selection

    def substr(self, region):
        return self.text[region.a : region.b]

    def insert(self, edit, point, text):
        self.text = self.text[:point] + text + self.text[point:]
        delta = len(text)
        for region in self._selection:
            if region.a >= point:
                region.a += delta
            if region.b >= point:
                region.b += delta

    def add_regions(self, key, regions, *props):
        self._regions[key] = list(regions)
        self.added_regions.append((key, list(regions), props))

    def get_regions(self, key):
        return list(self._regions.get(key, []))

    def erase_regions(self, key):
        self.erased_regions.append(key)
        self._regions.pop(key, None)

    def set_status(self, key, value):
        self.statuses[key] = value


class _FakeTester:
    def __init__(self, *, proc_run=False, checks=None):
        self.proc_run = proc_run
        self.inserts = []
        self._checks = list(checks or [])

    def insert(self, text, call_on_insert=False):
        self.inserts.append((text, call_on_insert))

    def get_tests(self):
        return ["T1", "T2"]

    def check_test(self, test_id):
        return self._checks[test_id]


class _FakePhantomSet:
    def __init__(self):
        self.updated = None

    def update(self, items):
        self.updated = list(items)


@contextmanager
def _patched_command_support_dependencies():
    module_names = (
        "sublime",
        "arena_forge.adapters.sublime.shared.messages",
        "arena_forge.adapters.sublime.shared.settings_bridge",
        "arena_forge.adapters.sublime.run_panel.input_actions",
        "arena_forge.adapters.sublime.run_panel.rendering",
        "arena_forge.adapters.sublime.run_panel.session_service",
        "arena_forge.adapters.sublime.run_panel.command_support",
    )
    originals = {name: sys.modules.get(name) for name in module_names}
    sys.modules["sublime"] = types.SimpleNamespace(
        Region=_FakeRegion,
        get_clipboard=lambda: "",
    )
    sys.modules["arena_forge.adapters.sublime.shared.messages"] = types.SimpleNamespace(
        translate_status_code=lambda status: f"translated:{status}"
    )
    sys.modules["arena_forge.adapters.sublime.shared.settings_bridge"] = types.SimpleNamespace(
        get_session_repository=lambda: "repository",
        get_tests_file_path=lambda source_file: f"tests:{source_file}",
        infer_language_name=lambda source_file: f"lang:{source_file}",
    )
    sys.modules["arena_forge.adapters.sublime.run_panel.input_actions"] = types.SimpleNamespace(
        push_input_history=lambda *args, **kwargs: None
    )
    sys.modules["arena_forge.adapters.sublime.run_panel.rendering"] = types.SimpleNamespace(
        build_compile_bar_phantom=lambda view, cmd, type="": ("phantom", cmd, type)
    )
    sys.modules["arena_forge.adapters.sublime.run_panel.session_service"] = types.SimpleNamespace(
        save_tests_for_run=lambda *args, **kwargs: None
    )
    sys.modules.pop("arena_forge.adapters.sublime.run_panel.command_support", None)
    try:
        yield
    finally:
        for name, original in originals.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original


class RunPanelCommandSupportTests(unittest.TestCase):
    def test_insert_panel_input_uses_explicit_text_and_records_history(self) -> None:
        with _patched_command_support_dependencies():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel.command_support")
            history = []
            module.push_input_history = lambda command, text: history.append((command, text))
            view = _FakeView("input", selections=[_FakeRegion(5, 5)])
            tester = _FakeTester(proc_run=True)
            advances = []
            command = SimpleNamespace(
                view=view,
                state=SimpleNamespace(
                    delta_input=5,
                    tester=tester,
                    advance_panel_input=lambda value: advances.append(value),
                ),
            )

            module.insert_panel_input(command, edit="EDIT", text="42")

            self.assertEqual(view.text, "input42\n")
            self.assertEqual(advances, [8])
            self.assertEqual(history, [(command, "42")])
            self.assertEqual(tester.inserts, [("42\n", False)])

    def test_insert_panel_input_uses_current_line_when_process_is_running(self) -> None:
        with _patched_command_support_dependencies():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel.command_support")
            history = []
            module.push_input_history = lambda command, text: history.append(text)
            view = _FakeView("promptabc", selections=[_FakeRegion(9, 9)])
            tester = _FakeTester(proc_run=True)
            advances = []
            command = SimpleNamespace(
                view=view,
                state=SimpleNamespace(
                    delta_input=6,
                    tester=tester,
                    advance_panel_input=lambda value: advances.append(value),
                ),
            )

            module.insert_panel_input(command, edit="EDIT")

            self.assertEqual(view.text, "promptabc\n")
            self.assertEqual(advances, [10])
            self.assertEqual(history, ["abc"])
            self.assertEqual(tester.inserts, [("abc\n", False)])

    def test_insert_panel_input_ignores_invalid_selection_or_stopped_process(self) -> None:
        with _patched_command_support_dependencies():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel.command_support")
            history = []
            module.push_input_history = lambda command, text: history.append(text)

            view = _FakeView("input", selections=[_FakeRegion(4, 4)])
            command = SimpleNamespace(
                view=view,
                state=SimpleNamespace(
                    delta_input=5,
                    tester=_FakeTester(proc_run=False),
                    advance_panel_input=lambda value: history.append(("advance", value)),
                ),
            )
            module.insert_panel_input(command, edit="EDIT", text="ignored")
            module.insert_panel_input(command, edit="EDIT")

            multi_view = _FakeView("input", selections=[_FakeRegion(5, 5), _FakeRegion(5, 5)])
            multi_command = SimpleNamespace(
                view=multi_view,
                state=SimpleNamespace(
                    delta_input=5,
                    tester=_FakeTester(proc_run=True),
                    advance_panel_input=lambda value: history.append(("advance", value)),
                ),
            )
            module.insert_panel_input(multi_command, edit="EDIT", text="ignored")

            self.assertEqual(view.text, "input")
            self.assertEqual(multi_view.text, "input")
            self.assertEqual(history, [])

    def test_insert_clipboard_input_sends_each_line(self) -> None:
        with _patched_command_support_dependencies():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel.command_support")
            module.sublime.get_clipboard = lambda: "one\ntwo"
            history = []
            module.push_input_history = lambda command, text: history.append(text)
            tester = _FakeTester(proc_run=True)
            command = SimpleNamespace(view=_FakeView(), state=SimpleNamespace(tester=tester))

            module.insert_clipboard_input(command, edit="EDIT")

            self.assertEqual(history, ["one", "two"])
            self.assertEqual(tester.inserts, [("one\n", True), ("two", True)])

    def test_memorize_tests_passes_storage_dependencies(self) -> None:
        with _patched_command_support_dependencies():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel.command_support")
            calls = []
            module.save_tests_for_run = lambda *args: calls.append(args)
            module.get_session_repository = lambda: "repo"
            module.get_tests_file_path = lambda source_file: f"path:{source_file}"
            module.infer_language_name = lambda source_file: f"lang:{source_file}"
            tester = _FakeTester(proc_run=True)
            command = SimpleNamespace(
                state=SimpleNamespace(source_file="main.cpp", tester=tester)
            )

            module.memorize_tests(command)

            self.assertEqual(
                calls,
                [("main.cpp", ["T1", "T2"], "repo", module.infer_language_name, module.get_tests_file_path)],
            )

    def test_add_transient_region_uses_generated_key_and_line_start(self) -> None:
        with _patched_command_support_dependencies():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel.command_support")
            original_randint = module.randint
            try:
                module.randint = lambda start, end: 123
                view = _FakeView("alpha\nbeta")
                command = SimpleNamespace(view=view)

                module.add_transient_region(command, 7, ("scope", "icon", 4))
            finally:
                module.randint = original_randint

            self.assertEqual(
                view.added_regions,
                [("123", [_FakeRegion(6, 7)], ("scope", "icon", 4))],
            )

    def test_change_process_status_and_compile_bar_update_view_state(self) -> None:
        with _patched_command_support_dependencies():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel.command_support")
            phantom_set = _FakePhantomSet()
            view = _FakeView()
            command = SimpleNamespace(
                view=view,
                state=SimpleNamespace(test_phantoms=[phantom_set]),
            )

            module.change_process_status(command, "RUNNING")
            module.set_compile_bar(command, "compiling", type="info")

            self.assertEqual(
                view.statuses,
                {"process_status_code": "RUNNING", "process_status": "translated:RUNNING"},
            )
            self.assertEqual(phantom_set.updated, [("phantom", "compiling", "info")])

    def test_get_style_test_status_maps_true_false_and_unknown(self) -> None:
        with _patched_command_support_dependencies():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel.command_support")
            command = SimpleNamespace(
                REGION_ACCEPT_PROP=("accept",),
                REGION_DECLINE_PROP=("decline",),
                REGION_UNKNOWN_PROP=("unknown",),
                state=SimpleNamespace(tester=_FakeTester(checks=[True, False, None])),
            )

            self.assertEqual(module.get_style_test_status(command, 0), ("accept",))
            self.assertEqual(module.get_style_test_status(command, 1), ("decline",))
            self.assertEqual(module.get_style_test_status(command, 2), ("unknown",))

    def test_renumerate_tests_moves_regions_from_original_index(self) -> None:
        with _patched_command_support_dependencies():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel.command_support")
            regions = {
                "test_begin_1": [_FakeRegion(10, 20)],
                "line_1": [_FakeRegion(21, 22)],
                "test_end_1": [_FakeRegion(30, 30)],
            }
            view = _FakeView("text", regions=regions)
            command = SimpleNamespace(
                view=view,
                REGION_BEGIN_KEY="test_begin_%d",
                REGION_END_KEY="test_end_%d",
                REGION_BEGIN_PROP=("begin", "icon", 1),
                REGION_END_PROP=("end", "icon", 2),
                REGION_LINE_PROP=("line", "icon", 3),
            )

            module.renumerate_tests(command, edit="EDIT", max_nth_test=2)

            self.assertEqual(view.get_regions("test_begin_0"), [_FakeRegion(10, 20)])
            self.assertEqual(view.get_regions("line_0"), [_FakeRegion(21, 22)])
            self.assertEqual(view.get_regions("test_end_0"), [_FakeRegion(30, 30)])
            self.assertEqual(view.get_regions("test_begin_1"), [])
            self.assertEqual(view.get_regions("line_1"), [])
            self.assertEqual(view.get_regions("test_end_1"), [])


if __name__ == "__main__":
    unittest.main()
