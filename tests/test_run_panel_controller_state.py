import unittest

from arena_forge.adapters.sublime.run_panel.controller_state import (
    RunPanelControllerState,
    RunPanelInputHistoryState,
)


class RunPanelControllerStateTests(unittest.TestCase):
    def test_remember_and_restore_launch_session_keep_runtime_metadata(self) -> None:
        state = RunPanelControllerState()

        launch_session = state.remember_launch(
            run_file="main.cpp",
            build_sys="source.c++",
            clr_tests=False,
            sync_out=True,
            code_view_id=17,
            use_debugger=True,
        )

        state.use_debugger = False
        state.source_file = None
        state.code_view_id = None

        restored = state.restore_launch()

        self.assertEqual(restored, launch_session)
        self.assertTrue(state.use_debugger)
        self.assertEqual(state.source_file, "main.cpp")
        self.assertEqual(state.code_view_id, 17)

    def test_begin_panel_input_and_reset_runtime_state_reset_buffer_and_history(self) -> None:
        state = RunPanelControllerState()

        state.begin_panel_input(12)
        state.advance_panel_input(18)
        state.history.push("echo 1")
        state.history.index = 0
        state.history.draft = "draft"

        state.reset_panel_runtime()

        self.assertEqual(state.input_start, 0)
        self.assertEqual(state.delta_input, 0)
        self.assertEqual(state.history.entries, [])
        self.assertIsNone(state.history.index)
        self.assertEqual(state.history.draft, "")


class RunPanelInputHistoryStateTests(unittest.TestCase):
    def test_push_deduplicates_adjacent_entries_and_resets_navigation(self) -> None:
        history = RunPanelInputHistoryState(entries=["one"], index=0, draft="pending")

        history.push("one")
        history.push("two")

        self.assertEqual(history.entries, ["one", "two"])
        self.assertIsNone(history.index)
        self.assertEqual(history.draft, "")


if __name__ == "__main__":
    unittest.main()
