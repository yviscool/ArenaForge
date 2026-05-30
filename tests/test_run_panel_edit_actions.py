import importlib
import sys
import types
import unittest
from contextlib import contextmanager


class _FakeRegion:
    def __init__(self, a, b=None) -> None:
        self.a = a
        self.b = a if b is None else b

    def begin(self) -> int:
        return self.a


class _FakeSettings:
    def __init__(self, values=None) -> None:
        self.values = dict(values or {})

    def get(self, key, default=None):
        return self.values.get(key, default)

    def set(self, key, value) -> None:
        self.values[key] = value


class _FakeView:
    def __init__(self, *, text="", regions=None, edit_mode=False) -> None:
        self._text = text
        self._regions = dict(regions or {})
        self._settings = _FakeSettings({"edit_mode": edit_mode})
        self.commands = []

    def settings(self):
        return self._settings

    def get_regions(self, key):
        return self._regions.get(key, [])

    def size(self) -> int:
        return len(self._text)

    def substr(self, region) -> str:
        return self._text[region.a : region.b]

    def erase_regions(self, key) -> None:
        self.commands.append(("erase_regions", key))

    def run_command(self, name, payload) -> None:
        self.commands.append((name, payload))


@contextmanager
def _patched_edit_actions():
    module_names = (
        "sublime",
        "arena_forge.adapters.sublime.run_panel.edit_actions",
    )
    originals = {name: sys.modules.get(name) for name in module_names}
    sys.modules["sublime"] = types.SimpleNamespace(Region=_FakeRegion)
    sys.modules.pop("arena_forge.adapters.sublime.run_panel.edit_actions", None)
    try:
        yield
    finally:
        for name, original in originals.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original


class RunPanelEditActionsTests(unittest.TestCase):
    def test_enable_edit_mode_defers_when_process_is_running(self) -> None:
        with _patched_edit_actions():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel.edit_actions")
            calls = []
            module.terminate_command_tester_with_logging = lambda command: calls.append(("terminate", command))
            module.schedule_test_manager_action = lambda view, action, delay=0, **kwargs: calls.append(
                ("schedule", view, action, delay, kwargs)
            )
            view = _FakeView()
            command = types.SimpleNamespace(
                view=view,
                state=types.SimpleNamespace(tester=types.SimpleNamespace(proc_run=True)),
            )

            module.enable_edit_mode(command)

            self.assertEqual(
                calls,
                [
                    ("terminate", command),
                    ("schedule", view, "enable_edit_mode", 500, {}),
                ],
            )
            self.assertFalse(view.settings().get("edit_mode"))

    def test_apply_edit_changes_rebuilds_test_list_from_marked_regions(self) -> None:
        with _patched_edit_actions():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel.edit_actions")
            captured = []
            view = _FakeView(
                text="alpha\nbeta",
                regions={
                    "begin_0": [_FakeRegion(0)],
                    "begin_1": [_FakeRegion(6)],
                    "begin_2": [],
                },
            )
            command = types.SimpleNamespace(
                view=view,
                REGION_BEGIN_KEY="begin_%d",
                state=types.SimpleNamespace(
                    tester=types.SimpleNamespace(set_tests=lambda tests: captured.append(("tests", tests)))
                ),
                memorize_tests=lambda: captured.append(("memorized", None)),
            )

            module.apply_edit_changes(command)

            self.assertEqual(
                captured,
                [
                    ("tests", ["alpha\n", "beta\n"]),
                    ("memorized", None),
                ],
            )


if __name__ == "__main__":
    unittest.main()
