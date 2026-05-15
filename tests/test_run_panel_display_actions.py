import importlib
import sys
import types
import unittest
from contextlib import contextmanager
from types import SimpleNamespace


class _FakePhantomSet:
    def __init__(self, view, key):
        self.view = view
        self.key = key
        self.updated = None
        self.update_calls = 0

    def update(self, items):
        self.update_calls += 1
        self.updated = list(items)


class _FakeView:
    def __init__(self):
        self._settings = {"hide_phantoms": False}

    def settings(self):
        return self

    def get(self, key):
        return self._settings.get(key)


class _FakeTest:
    def __init__(self, name):
        self.name = name
        self.config_calls = 0
        self.accdec_calls = 0

    def get_config(self, test_id, point, callback, output_text, view, running=False):
        self.config_calls += 1
        return f"config:{self.name}:{test_id}:{point}:{running}"

    def get_accdec(self, test_id, point, callback, action_type, view):
        self.accdec_calls += 1
        return f"accdec:{self.name}:{test_id}:{point}:{action_type}"


@contextmanager
def _patched_sublime():
    original = sys.modules.get("sublime")
    original_rendering = sys.modules.get("arena_forge.adapters.sublime.run_panel_rendering")
    fake = types.SimpleNamespace(
        PhantomSet=_FakePhantomSet,
        LAYOUT_BLOCK=0,
        Phantom=lambda *args, **kwargs: None,
        Region=lambda *args, **kwargs: None,
    )
    sys.modules["sublime"] = fake
    sys.modules["arena_forge.adapters.sublime.run_panel_rendering"] = types.SimpleNamespace(
        build_next_test_title_phantom=lambda *args, **kwargs: "next-test"
    )
    sys.modules.pop("arena_forge.adapters.sublime.run_panel_display_actions", None)
    try:
        yield
    finally:
        sys.modules.pop("arena_forge.adapters.sublime.run_panel_display_actions", None)
        if original_rendering is None:
            sys.modules.pop("arena_forge.adapters.sublime.run_panel_rendering", None)
        else:
            sys.modules["arena_forge.adapters.sublime.run_panel_rendering"] = original_rendering
        if original is None:
            sys.modules.pop("sublime", None)
        else:
            sys.modules["sublime"] = original


class RunPanelDisplayActionsTests(unittest.TestCase):
    def test_update_configs_clears_stale_phantoms_when_update_last_true(self) -> None:
        with _patched_sublime():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel_display_actions")
            original_builder = module.build_panel_render_entries
            try:
                module.build_panel_render_entries = lambda *args, **kwargs: (
                    SimpleNamespace(
                        test_id=0,
                        config_point=0,
                        running=True,
                        accdec_point=None,
                        accdec_action=None,
                    ),
                )
                command = SimpleNamespace(
                    view=_FakeView(),
                    on_test_action=lambda *args: None,
                    on_accdec_action=lambda *args: None,
                    state=SimpleNamespace(
                        tester=SimpleNamespace(
                            tests=[_FakeTest("t1")],
                            prog_out=[""],
                            proc_run=True,
                            running_test=0,
                            test_iter=1,
                        ),
                        test_phantoms=[
                            _FakePhantomSet(None, "0"),
                            _FakePhantomSet(None, "1"),
                            _FakePhantomSet(None, "2"),
                        ],
                    ),
                )
                command.state.test_phantoms[1].updated = ["stale-accept"]
                command.state.test_phantoms[2].updated = ["stale-next"]

                module.update_configs(command, update_last=True)

                self.assertEqual(command.state.test_phantoms[0].updated, ["config:t1:0:0:True"])
                self.assertEqual(command.state.test_phantoms[1].updated, [])
                self.assertEqual(command.state.test_phantoms[2].updated, [])
            finally:
                module.build_panel_render_entries = original_builder

    def test_update_configs_skips_unchanged_slots_on_repeated_refresh(self) -> None:
        with _patched_sublime():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel_display_actions")
            original_builder = module.build_panel_render_entries
            try:
                test = _FakeTest("t1")
                module.build_panel_render_entries = lambda *args, **kwargs: (
                    SimpleNamespace(
                        test_id=0,
                        config_point=0,
                        running=True,
                        accdec_point=None,
                        accdec_action=None,
                    ),
                )
                command = SimpleNamespace(
                    view=_FakeView(),
                    on_test_action=lambda *args: None,
                    on_accdec_action=lambda *args: None,
                    state=SimpleNamespace(
                        tester=SimpleNamespace(
                            tests=[test],
                            prog_out=[""],
                            proc_run=True,
                            running_test=0,
                            test_iter=1,
                        ),
                        test_phantoms=[_FakePhantomSet(None, "0")],
                    ),
                )

                module.update_configs(command)
                module.update_configs(command)

                self.assertEqual(test.config_calls, 1)
                self.assertEqual(command.state.test_phantoms[0].update_calls, 1)
            finally:
                module.build_panel_render_entries = original_builder

    def test_update_configs_refreshes_hidden_slots_without_rebuilding_visible_content(self) -> None:
        with _patched_sublime():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel_display_actions")
            original_builder = module.build_panel_render_entries
            try:
                test = _FakeTest("t1")
                module.build_panel_render_entries = lambda *args, **kwargs: (
                    SimpleNamespace(
                        test_id=0,
                        config_point=0,
                        running=True,
                        accdec_point=None,
                        accdec_action=None,
                    ),
                )
                command = SimpleNamespace(
                    view=_FakeView(),
                    on_test_action=lambda *args: None,
                    on_accdec_action=lambda *args: None,
                    state=SimpleNamespace(
                        tester=SimpleNamespace(
                            tests=[test],
                            prog_out=[""],
                            proc_run=True,
                            running_test=0,
                            test_iter=1,
                        ),
                        test_phantoms=[_FakePhantomSet(None, "0")],
                    ),
                )

                module.update_configs(command)
                command.view._settings["hide_phantoms"] = True
                module.update_configs(command)
                module.update_configs(command)
                command.view._settings["hide_phantoms"] = False
                module.update_configs(command)

                self.assertEqual(test.config_calls, 2)
                self.assertEqual(command.state.test_phantoms[0].update_calls, 3)
                self.assertEqual(command.state.test_phantoms[0].updated, ["config:t1:0:0:True"])
            finally:
                module.build_panel_render_entries = original_builder


if __name__ == "__main__":
    unittest.main()
