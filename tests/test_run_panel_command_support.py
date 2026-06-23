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


@contextmanager
def _patched_command_support_dependencies():
    module_names = (
        "sublime",
        "arena_forge.adapters.sublime.run_panel.input_actions",
        "arena_forge.adapters.sublime.run_panel.command_support",
    )
    originals = {name: sys.modules.get(name) for name in module_names}
    sys.modules["sublime"] = types.SimpleNamespace(
        Region=_FakeRegion,
        get_clipboard=lambda: "",
    )
    sys.modules["arena_forge.adapters.sublime.run_panel.input_actions"] = types.SimpleNamespace(
        push_input_history=lambda *args, **kwargs: None
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

if __name__ == "__main__":
    unittest.main()
