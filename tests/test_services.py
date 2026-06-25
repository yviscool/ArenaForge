import unittest

from arena_forge.core.domain import LanguageProfile, OutputReferenceKind, TestCase, Verdict
from arena_forge.core.services import (
    evaluate_output,
    evaluate_output_result,
    find_first_mismatch,
    normalize_text,
    select_language_profile,
)


class ServiceTests(unittest.TestCase):
    def test_normalize_text_trims_line_endings_and_trailing_space(self) -> None:
        self.assertEqual(normalize_text("1  \r\n2\r\n\r\n"), "1\n2")

    def test_evaluate_output_accepts_normalized_match(self) -> None:
        test_case = TestCase(name="Test 1", input_text="1", accepted_outputs=("42\n",))
        self.assertEqual(evaluate_output(test_case, "42\r\n"), Verdict.ACCEPTED)

    def test_evaluate_output_rejects_known_bad_output(self) -> None:
        test_case = TestCase(name="Test 1", input_text="1", rejected_outputs=("0",))
        self.assertEqual(evaluate_output(test_case, "0\n"), Verdict.REJECTED)

    def test_evaluate_output_result_reports_first_mismatch(self) -> None:
        test_case = TestCase(name="Test 1", input_text="1", accepted_outputs=("42\n17",))
        evaluation = evaluate_output_result(test_case, "42\n99")
        self.assertEqual(evaluation.verdict, Verdict.REJECTED)
        self.assertEqual(evaluation.reference_kind, OutputReferenceKind.ACCEPTED)
        self.assertIsNotNone(evaluation.mismatch)
        self.assertEqual(evaluation.mismatch.line, 2)
        self.assertEqual(evaluation.mismatch.column, 1)

    def test_find_first_mismatch_handles_missing_trailing_output(self) -> None:
        mismatch = find_first_mismatch("42\n17", "42")
        self.assertIsNotNone(mismatch)
        self.assertEqual(mismatch.line, 2)
        self.assertEqual(mismatch.column, 1)

    def test_select_language_profile_matches_by_extension(self) -> None:
        cpp = LanguageProfile(name="C++", extensions=("cpp", "cc"), compile_cmd="g++", run_cmd="./a.out")
        py = LanguageProfile(name="Python", extensions=("py",), compile_cmd=None, run_cmd="python {source_file}")
        profile = select_language_profile("main.cpp", (cpp, py))
        self.assertEqual(profile.name, "C++")

    def test_select_language_profile_raises_for_unknown_extension(self) -> None:
        cpp = LanguageProfile(name="C++", extensions=("cpp",), compile_cmd="g++", run_cmd="./a.out")
        with self.assertRaises(ValueError):
            select_language_profile("main.xyz", (cpp,))


if __name__ == "__main__":
    unittest.main()
