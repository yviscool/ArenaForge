import unittest

from arena_forge.adapters.sublime.run_panel_input_actions import find_previous_word_boundary


class RunPanelInputActionTests(unittest.TestCase):
    def test_find_previous_word_boundary_skips_trailing_spaces(self) -> None:
        self.assertEqual(find_previous_word_boundary("echo hello   "), 5)

    def test_find_previous_word_boundary_stops_at_line_start(self) -> None:
        self.assertEqual(find_previous_word_boundary("token"), 0)

    def test_find_previous_word_boundary_handles_multiple_words(self) -> None:
        self.assertEqual(find_previous_word_boundary("abc def ghi"), 8)


if __name__ == "__main__":
    unittest.main()
