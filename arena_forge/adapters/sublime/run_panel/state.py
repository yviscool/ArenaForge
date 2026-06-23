from __future__ import annotations

from typing import Optional

from arena_forge.core.domain import OutputEvaluation, TestCase

from .rendering import build_accdec_phantom, build_test_config_phantom


class PanelTestState:
    def __init__(self, prop, start=None, end=None):
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

    @property
    def input_text(self):
        return self.test_string

    @input_text.setter
    def input_text(self, value):
        self.test_string = value

    @property
    def accepted_outputs(self):
        return self.correct_answers

    @property
    def rejected_outputs(self):
        return self.uncorrect_answers

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
