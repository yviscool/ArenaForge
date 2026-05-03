import unittest

from arena_forge.core.domain import TestCase, Verdict
from arena_forge.core.services import evaluate_output, normalize_text


class ServiceTests(unittest.TestCase):
    def test_normalize_text_trims_line_endings_and_trailing_space(self) -> None:
        self.assertEqual(normalize_text("1  \r\n2\r\n\r\n"), "1\n2")

    def test_evaluate_output_accepts_normalized_match(self) -> None:
        test_case = TestCase(name="Test 1", input_text="1", accepted_outputs=("42\n",))
        self.assertEqual(evaluate_output(test_case, "42\r\n"), Verdict.ACCEPTED)

    def test_evaluate_output_rejects_known_bad_output(self) -> None:
        test_case = TestCase(name="Test 1", input_text="1", rejected_outputs=("0",))
        self.assertEqual(evaluate_output(test_case, "0\n"), Verdict.REJECTED)


if __name__ == "__main__":
    unittest.main()
