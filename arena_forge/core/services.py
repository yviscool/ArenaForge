from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .domain import (
    LanguageProfile,
    OutputEvaluation,
    OutputMismatch,
    OutputReferenceKind,
    TestCase,
    Verdict,
)
from .ports import OutputChecker


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def find_first_mismatch(expected_text: str, actual_text: str) -> OutputMismatch | None:
    if expected_text == actual_text:
        return None

    expected_lines = expected_text.split("\n")
    actual_lines = actual_text.split("\n")
    total_lines = max(len(expected_lines), len(actual_lines))

    for line_index in range(total_lines):
        expected_line = expected_lines[line_index] if line_index < len(expected_lines) else ""
        actual_line = actual_lines[line_index] if line_index < len(actual_lines) else ""
        if expected_line == actual_line:
            continue
        max_columns = max(len(expected_line), len(actual_line))
        for column_index in range(max_columns):
            expected_char = expected_line[column_index] if column_index < len(expected_line) else ""
            actual_char = actual_line[column_index] if column_index < len(actual_line) else ""
            if expected_char != actual_char:
                return OutputMismatch(
                    line=line_index + 1,
                    column=column_index + 1,
                    expected_excerpt=expected_line,
                    actual_excerpt=actual_line,
                )
        return OutputMismatch(
            line=line_index + 1,
            column=max_columns + 1,
            expected_excerpt=expected_line,
            actual_excerpt=actual_line,
        )
    return OutputMismatch(
        line=total_lines + 1,
        column=1,
        expected_excerpt="",
        actual_excerpt="",
    )


class NormalizedTextOutputChecker:
    checker_name = "normalized_text"

    def evaluate(self, test_case: TestCase, output_text: str) -> OutputEvaluation:
        normalized_output = normalize_text(output_text)
        accepted = tuple(normalize_text(item) for item in test_case.accepted_outputs)
        rejected = tuple(normalize_text(item) for item in test_case.rejected_outputs)

        if normalized_output in accepted:
            return OutputEvaluation(
                checker_name=self.checker_name,
                verdict=Verdict.ACCEPTED,
                reference_kind=OutputReferenceKind.ACCEPTED,
                normalized_actual=normalized_output,
                normalized_expected=normalized_output,
            )

        if normalized_output in rejected:
            return OutputEvaluation(
                checker_name=self.checker_name,
                verdict=Verdict.REJECTED,
                reference_kind=OutputReferenceKind.REJECTED,
                normalized_actual=normalized_output,
                normalized_expected=normalized_output,
            )

        if accepted:
            expected_output = accepted[0]
            return OutputEvaluation(
                checker_name=self.checker_name,
                verdict=Verdict.REJECTED,
                reference_kind=OutputReferenceKind.ACCEPTED,
                normalized_actual=normalized_output,
                normalized_expected=expected_output,
                mismatch=find_first_mismatch(expected_output, normalized_output),
            )

        return OutputEvaluation(
            checker_name=self.checker_name,
            verdict=Verdict.UNKNOWN,
            reference_kind=OutputReferenceKind.NONE,
            normalized_actual=normalized_output,
        )


def get_output_checker(checker_name: str) -> OutputChecker:
    if checker_name == "normalized_text":
        return NormalizedTextOutputChecker()
    raise ValueError(f"Unsupported checker: {checker_name}")


def evaluate_output_result(test_case: TestCase, output_text: str) -> OutputEvaluation:
    return get_output_checker(test_case.checker_name).evaluate(test_case, output_text)


def evaluate_output(test_case: TestCase, output_text: str) -> Verdict:
    return evaluate_output_result(test_case, output_text).verdict


def infer_language(source_file: str, profiles: Iterable[LanguageProfile]) -> str:
    ext = Path(source_file).suffix.lstrip(".")
    for profile in profiles:
        if ext in profile.extensions:
            return profile.name
    raise ValueError(f"Unsupported source extension: {ext}")


def select_language_profile(source_file: str, profiles: Iterable[LanguageProfile]) -> LanguageProfile:
    ext = Path(source_file).suffix.lstrip(".")
    for profile in profiles:
        if ext in profile.extensions:
            return profile
    raise ValueError(f"Unsupported source extension: {ext}")
