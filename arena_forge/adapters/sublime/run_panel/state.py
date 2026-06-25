from __future__ import annotations

from typing import Optional

from arena_forge.core.domain import OutputEvaluation, TestCase

from .rendering import build_accdec_phantom, build_test_config_phantom


class PanelTestState:
    def __init__(self, prop, start=None, end=None):
        if isinstance(prop, str):
            self._input_text = prop
            self._accepted_outputs: set[str] = set()
            self._rejected_outputs: set[str] = set()
            self._checker_name = "normalized_text"
        else:
            self._input_text = prop["test"]
            self._accepted_outputs = set(prop.get("correct_answers", ()))
            self._rejected_outputs = set(prop.get("uncorrect_answers", ()))
            self._checker_name = prop.get("checker_name", "normalized_text")

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
        return self._input_text

    @input_text.setter
    def input_text(self, value):
        self._input_text = value

    @property
    def checker_name(self):
        return self._checker_name

    @property
    def correct_answers(self):
        return self._accepted_outputs

    @property
    def uncorrect_answers(self):
        return self._rejected_outputs

    @property
    def accepted_outputs(self):
        return self._accepted_outputs

    @property
    def rejected_outputs(self):
        return self._rejected_outputs

    def add_correct_answer(self, answer):
        self._accepted_outputs.add(answer.strip())

    def add_uncorrect_answer(self, answer):
        self._rejected_outputs.add(answer.strip())

    def remove_correct_answer(self, answer):
        self._accepted_outputs.discard(answer.strip())

    def remove_uncorrect_answer(self, answer):
        self._rejected_outputs.discard(answer.strip())

    def is_correct_answer(self, answer):
        answer = answer.strip()
        if answer in self._accepted_outputs:
            return True
        if answer in self._rejected_outputs:
            return False
        return None

    def append_string(self, value):
        self._input_text += value

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

    def to_payload(self):
        payload = {"test": self._input_text}
        if self._accepted_outputs:
            payload["correct_answers"] = sorted(self._accepted_outputs)
        if self._rejected_outputs:
            payload["uncorrect_answers"] = sorted(self._rejected_outputs)
        if self._checker_name != "normalized_text":
            payload["checker_name"] = self._checker_name
        return payload

    def to_test_case(self, index):
        return TestCase.from_mapping(index, self.to_payload())

    def __str__(self):
        return self._input_text
