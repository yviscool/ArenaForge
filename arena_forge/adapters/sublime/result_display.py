from __future__ import annotations

from typing import Optional

from arena_forge.core.domain import OutputEvaluation, OutputReferenceKind, Verdict

from .messages import translate


def format_output_evaluation_summary(evaluation: Optional[OutputEvaluation]) -> str:
    if evaluation is None:
        return ""
    if evaluation.verdict == Verdict.ACCEPTED and evaluation.reference_kind == OutputReferenceKind.ACCEPTED:
        return translate("result.matches_expected")
    if evaluation.verdict == Verdict.REJECTED and evaluation.reference_kind == OutputReferenceKind.REJECTED:
        return translate("result.matches_rejected")
    if evaluation.verdict == Verdict.REJECTED and evaluation.mismatch is not None:
        return translate(
            "result.first_mismatch",
            line=evaluation.mismatch.line,
            column=evaluation.mismatch.column,
        )
    if evaluation.verdict == Verdict.UNKNOWN:
        return translate("result.no_expected_output")
    return evaluation.verdict.value


def format_output_evaluation_detail(evaluation: Optional[OutputEvaluation]) -> str:
    if evaluation is None or evaluation.mismatch is None:
        return ""
    expected_label = translate("ui.expected")
    actual_label = translate("ui.actual")
    expected_excerpt = evaluation.mismatch.expected_excerpt or ""
    actual_excerpt = evaluation.mismatch.actual_excerpt or ""
    return f"{expected_label}: {expected_excerpt} | {actual_label}: {actual_excerpt}"


def result_summary_css_class(evaluation: Optional[OutputEvaluation]) -> str:
    if evaluation is None:
        return ""
    if evaluation.verdict == Verdict.ACCEPTED:
        return "summary-accept"
    if evaluation.verdict == Verdict.REJECTED:
        return "summary-decline"
    return "summary-unknown"
