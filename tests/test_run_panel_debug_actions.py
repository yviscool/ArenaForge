import unittest
from types import SimpleNamespace

from arena_forge.adapters.sublime.run_panel import debug_actions


class _FakeView:
    def __init__(self, view_id, *, dirty=False):
        self._id = view_id
        self._dirty = dirty
        self.commands = []

    def id(self):
        return self._id

    def is_dirty(self):
        return self._dirty

    def run_command(self, name, payload=None):
        self.commands.append((name, payload))


def _build_command(*views, code_view_id=1, process_manager=None):
    window = SimpleNamespace(views=lambda: list(views))
    panel_view = SimpleNamespace(window=lambda: window)
    state = SimpleNamespace(
        code_view_id=code_view_id,
        tester=SimpleNamespace(process_manager=process_manager or object()),
    )
    return SimpleNamespace(view=panel_view, state=state)


class RunPanelDebugActionsTests(unittest.TestCase):
    def test_get_view_by_id_returns_matching_view(self) -> None:
        target = _FakeView(7)
        command = _build_command(_FakeView(3), target, code_view_id=7)

        result = debug_actions.get_view_by_id(command, 7)

        self.assertIs(result, target)

    def test_prepare_code_view_saves_only_dirty_code_view(self) -> None:
        clean = _FakeView(1, dirty=False)
        dirty = _FakeView(2, dirty=True)
        command = _build_command(clean, dirty, code_view_id=2)

        debug_actions.prepare_code_view(command)

        self.assertEqual(clean.commands, [])
        self.assertEqual(dirty.commands, [("save", None)])

    def test_redirect_var_value_skips_when_inspection_is_unsupported(self) -> None:
        code_view = _FakeView(11)
        process_manager = SimpleNamespace(get_var_value=lambda name: "unexpected")
        command = _build_command(code_view, code_view_id=11, process_manager=process_manager)
        original_supports = debug_actions.supports_variable_inspection
        try:
            debug_actions.supports_variable_inspection = lambda _: False

            debug_actions.redirect_var_value(command, "answer", pos=8)
        finally:
            debug_actions.supports_variable_inspection = original_supports

        self.assertEqual(code_view.commands, [])

    def test_redirect_var_value_shows_value_on_code_view(self) -> None:
        code_view = _FakeView(11)
        process_manager = SimpleNamespace(get_var_value=lambda name: f"value:{name}")
        command = _build_command(code_view, code_view_id=11, process_manager=process_manager)
        original_supports = debug_actions.supports_variable_inspection
        try:
            debug_actions.supports_variable_inspection = lambda _: True

            debug_actions.redirect_var_value(command, "answer", pos=8)
        finally:
            debug_actions.supports_variable_inspection = original_supports

        self.assertEqual(
            code_view.commands,
            [("debug_overlay", {"action": "show_var_value", "value": "value:answer", "pos": 8})],
        )

    def test_redirect_frames_shows_frames_on_code_view(self) -> None:
        code_view = _FakeView(9)
        command = _build_command(code_view, code_view_id=9, process_manager=object())
        original_read_frames = debug_actions.read_frames
        try:
            debug_actions.read_frames = lambda _: [{"name": "main"}]

            debug_actions.redirect_frames(command)
        finally:
            debug_actions.read_frames = original_read_frames

        self.assertEqual(
            code_view.commands,
            [("debug_overlay", {"action": "show_frames", "frames": [{"name": "main"}]})],
        )

    def test_select_frame_delegates_to_debug_protocol(self) -> None:
        calls = []
        command = _build_command(code_view_id=4, process_manager=object())
        original_select_frame = debug_actions.select_debugger_frame
        try:
            debug_actions.select_debugger_frame = lambda process_manager, frame_id: calls.append(
                (process_manager, frame_id)
            )

            debug_actions.select_frame(command, 3)
        finally:
            debug_actions.select_debugger_frame = original_select_frame

        self.assertEqual(calls, [(command.state.tester.process_manager, 3)])


if __name__ == "__main__":
    unittest.main()
