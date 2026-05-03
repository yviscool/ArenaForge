from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .domain import LanguageProfile, TestCase, Verdict


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def evaluate_output(test_case: TestCase, output_text: str) -> Verdict:
    normalized_output = normalize_text(output_text)
    accepted = {normalize_text(item) for item in test_case.accepted_outputs}
    rejected = {normalize_text(item) for item in test_case.rejected_outputs}

    if normalized_output in accepted:
        return Verdict.ACCEPTED
    if normalized_output in rejected:
        return Verdict.REJECTED
    return Verdict.UNKNOWN


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
