from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterable, Optional

from .domain import (
    LanguageProfile,
    OutputEvaluation,
    OutputMismatch,
    OutputReferenceKind,
    TestCase,
    Verdict,
)
from .ports import OutputChecker


def _default_translate(key: str, **kwargs: str) -> str:
    from arena_forge.adapters.i18n.catalog import translate_catalog
    return translate_catalog(key, **kwargs)


_translate: Callable[..., str] = _default_translate


def set_translate(fn: Callable[..., str]) -> None:
    global _translate
    _translate = fn


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def find_first_mismatch(expected_text: str, actual_text: str) -> Optional[OutputMismatch]:
    if expected_text == actual_text:
        return None

    expected_len = len(expected_text)
    actual_len = len(actual_text)
    expected_pos = 0
    actual_pos = 0
    line_index = 0

    while expected_pos <= expected_len or actual_pos <= actual_len:
        expected_nl = expected_text.find("\n", expected_pos)
        actual_nl = actual_text.find("\n", actual_pos)
        expected_end = expected_len if expected_nl == -1 else expected_nl
        actual_end = actual_len if actual_nl == -1 else actual_nl
        expected_line = expected_text[expected_pos:expected_end]
        actual_line = actual_text[actual_pos:actual_end]

        if expected_line != actual_line:
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

        if expected_nl == -1 and actual_nl == -1:
            break

        expected_pos = expected_end + 1 if expected_nl != -1 else expected_len + 1
        actual_pos = actual_end + 1 if actual_nl != -1 else actual_len + 1
        line_index += 1

    return OutputMismatch(line=line_index + 1, column=1, expected_excerpt="", actual_excerpt="")


class NormalizedTextOutputChecker:
    checker_name = "normalized_text"

    def evaluate(self, test_case: TestCase, output_text: str) -> OutputEvaluation:
        normalized_output = normalize_text(output_text)
        accepted_outputs = test_case.accepted_outputs
        rejected_outputs = test_case.rejected_outputs

        if accepted_outputs:
            for accepted_output in accepted_outputs:
                normalized_accepted = normalize_text(accepted_output)
                if normalized_output == normalized_accepted:
                    return OutputEvaluation(
                        checker_name=self.checker_name,
                        verdict=Verdict.ACCEPTED,
                        reference_kind=OutputReferenceKind.ACCEPTED,
                        normalized_actual=normalized_output,
                        normalized_expected=normalized_output,
                    )

        if rejected_outputs:
            for rejected_output in rejected_outputs:
                if normalized_output == normalize_text(rejected_output):
                    return OutputEvaluation(
                        checker_name=self.checker_name,
                        verdict=Verdict.REJECTED,
                        reference_kind=OutputReferenceKind.REJECTED,
                        normalized_actual=normalized_output,
                        normalized_expected=normalized_output,
                    )

        if accepted_outputs:
            expected_output = normalize_text(accepted_outputs[0])
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
    raise ValueError(_translate("error.unsupported_checker", checker_name=checker_name))


def evaluate_output_result(test_case: TestCase, output_text: str) -> OutputEvaluation:
    return get_output_checker(test_case.checker_name).evaluate(test_case, output_text)


def evaluate_output(test_case: TestCase, output_text: str) -> Verdict:
    return evaluate_output_result(test_case, output_text).verdict


def select_language_profile(source_file: str, profiles: Iterable[LanguageProfile]) -> LanguageProfile:
    ext = Path(source_file).suffix.lstrip(".")
    for profile in profiles:
        if ext in profile.extensions:
            return profile
    raise ValueError(_translate("error.unsupported_source_extension", ext=ext))
