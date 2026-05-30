import unittest

from arena_forge.adapters.sublime.run_panel.input_actions import navigate_history


class RunPanelHistoryNavigationTests(unittest.TestCase):
    def test_history_previous_uses_current_text_as_draft(self) -> None:
        index, draft, text = navigate_history(["one", "two"], None, "", "draft", -1)
        self.assertEqual(index, 1)
        self.assertEqual(draft, "draft")
        self.assertEqual(text, "two")

    def test_history_next_restores_draft_after_last_entry(self) -> None:
        index, draft, text = navigate_history(["one", "two"], 1, "draft", "two", 1)
        self.assertIsNone(index)
        self.assertEqual(draft, "draft")
        self.assertEqual(text, "draft")

    def test_history_previous_clamps_at_first_entry(self) -> None:
        index, draft, text = navigate_history(["one", "two"], 0, "draft", "one", -1)
        self.assertEqual(index, 0)
        self.assertEqual(text, "one")


if __name__ == "__main__":
    unittest.main()
