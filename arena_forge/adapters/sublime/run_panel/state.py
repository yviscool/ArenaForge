from __future__ import annotations

from typing import Optional

import sublime

from arena_forge.core.domain import OutputEvaluation, RunHistoryEntry, SessionSnapshot, TestCase

from ..run_history import coerce_verdict
from ..shared.messages import product_log_message
from .rendering import build_accdec_phantom, build_test_config_phantom


class PanelTestState(object):
    def __init__(self, prop, start=None, end=None):
        super(PanelTestState, self).__init__()
        if isinstance(prop, str):
            self.test_string = prop
            self.correct_answers = set()
            self.uncorrect_answers = set()
        else:
            self.test_string = prop["test"]
            self.correct_answers = set(prop.get("correct_answers", set()))
            self.uncorrect_answers = set(prop.get("uncorrect_answers", set()))
        self.checker_name = prop.get("checker_name", "normalized_text") if isinstance(prop, dict) else "normalized_text"

        self.start = start
        self.fold = True
        self.end = end
        self.runtime = "-"
        self.rtcode = 0
        self.tie_pos = 0
        self.last_evaluation = None
        self.display_body_text = None
        self.output_start_offset = None

    def add_correct_answer(self, answer):
        self.correct_answers.add(answer.strip())

    def add_uncorrect_answer(self, answer):
        self.uncorrect_answers.add(answer.strip())

    def remove_correct_answer(self, answer):
        self.correct_answers.discard(answer.strip())

    def remove_uncorrect_answer(self, answer):
        self.uncorrect_answers.discard(answer.strip())

    def is_correct_answer(self, answer):
        answer = answer.strip()
        if answer in self.correct_answers:
            return True
        if answer in self.uncorrect_answers:
            return False
        return None

    def append_string(self, value):
        self.test_string += value

    def set_inner_range(self, start, end):
        self.start = start
        self.end = end

    def set_tie_pos(self, pos):
        self.tie_pos = pos

    def set_cur_runtime(self, runtime):
        self.runtime = runtime

    def set_cur_rtcode(self, rtcode):
        self.rtcode = rtcode

    def set_last_evaluation(self, evaluation: Optional[OutputEvaluation]):
        self.last_evaluation = evaluation

    def set_display_layout(self, body_text: Optional[str], output_start_offset: Optional[int]) -> None:
        self.display_body_text = body_text
        self.output_start_offset = output_start_offset

    def get_nice_runtime(self):
        runtime = self.runtime
        if runtime < 5000:
            return "&nbsp;" * (2 - len(str(runtime))) + str(runtime) + "ms"
        return str(runtime // 1000) + "s"

    def get_config(self, test_id, point, callback, output_text, view, running=False):
        return build_test_config_phantom(self, test_id, point, callback, output_text, view, running=running)

    def get_accdec(self, test_id, point, callback, action_type, view):
        return build_accdec_phantom(self, test_id, point, callback, action_type, view)

    def memorize(self):
        payload = {"test": self.test_string}
        if self.correct_answers:
            payload["correct_answers"] = sorted(self.correct_answers)
        if self.uncorrect_answers:
            payload["uncorrect_answers"] = sorted(self.uncorrect_answers)
        if self.checker_name != "normalized_text":
            payload["checker_name"] = self.checker_name
        return payload

    def to_core_test_case(self, index):
        return TestCase.from_mapping(index, self.memorize())

    def __str__(self):
        return self.test_string


def persist_panel_tests(source_file, tests, repository, infer_language_name, tests_file_path_factory):
    tests_payload = [test.memorize() for test in tests]
    encoded_tests = sublime.encode_value(tests_payload, True)
    tests_path = tests_file_path_factory(source_file, for_write=True)
    current_payload = _read_panel_tests_payload(tests_path)
    if current_payload != encoded_tests:
        with open(tests_path, "w", encoding="utf-8") as handle:
            handle.write(encoded_tests)

    language_name = infer_language_name(source_file)
    core_tests = tuple(test.to_core_test_case(index + 1) for index, test in enumerate(tests))
    snapshot = repository.load(source_file)
    if snapshot is not None and snapshot.language == language_name and snapshot.tests == core_tests:
        return
    session_kwargs = {
        "source_file": source_file,
        "language": language_name,
        "tests": core_tests,
        "run_history": snapshot.run_history if snapshot is not None else (),
    }
    if snapshot is not None:
        session_kwargs["updated_at"] = snapshot.updated_at
    repository.save(
        SessionSnapshot(
            **session_kwargs,
        )
    )


def _read_panel_tests_payload(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.read()
    except OSError:
        return None


def _decode_panel_tests_payload(payload_text):
    payload = sublime.decode_value(payload_text)
    if not isinstance(payload, list):
        raise ValueError("tests payload must be a list")
    decoded = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("test payload entries must be objects")
        if not str(item.get("test", "")).strip():
            continue
        decoded.append(item)
    return decoded


def append_run_history(
    repository,
    source_file,
    test_name,
    output_text,
    verdict,
    runtime_ms,
    return_code,
    evaluation=None,
):
    snapshot = repository.load(source_file)
    if snapshot is None:
        return
    history = list(snapshot.run_history)
    history.append(
        RunHistoryEntry(
            test_name=test_name,
            output_text=output_text,
            verdict=coerce_verdict(verdict),
            runtime_ms=runtime_ms,
            return_code=return_code,
            evaluation=evaluation,
        )
    )
    repository.save(
        SessionSnapshot(
            source_file=snapshot.source_file,
            language=snapshot.language,
            tests=snapshot.tests,
            run_history=tuple(history[-50:]),
            updated_at=snapshot.updated_at,
        )
    )


def load_panel_tests(source_file, test_factory, repository, tests_file_path_factory):
    tests_path = tests_file_path_factory(source_file)
    try:
        with open(tests_path, encoding="utf-8") as handle:
            decoded = _decode_panel_tests_payload(handle.read())
        return [test_factory(item) for item in decoded]
    except OSError:
        pass
    except (KeyError, TypeError, ValueError):
        product_log_message("error.tests_file_invalid", path=tests_path)

    snapshot = repository.load(source_file)
    if snapshot is None:
        return []
    return [test_factory(test.to_mapping()) for test in snapshot.tests if test.input_text.strip()]
