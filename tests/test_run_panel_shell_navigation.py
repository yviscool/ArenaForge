import unittest

from arena_forge.adapters.sublime.run_panel_input_actions import (
    find_next_word_boundary,
    find_previous_word_boundary,
)


class RunPanelShellNavigationTests(unittest.TestCase):
    def test_find_next_word_boundary_skips_leading_spaces(self) -> None:
        self.assertEqual(find_next_word_boundary("   hello world"), 8)

    def test_find_next_word_boundary_stops_after_current_word(self) -> None:
        self.assertEqual(find_next_word_boundary("token rest"), 5)

    def test_find_previous_word_boundary_keeps_terminal_word_behavior(self) -> None:
        self.assertEqual(find_previous_word_boundary("one two three"), 8)


if __name__ == "__main__":
    unittest.main()
