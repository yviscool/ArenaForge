import unittest
from dataclasses import dataclass
from typing import Optional

from arena_forge.adapters.sublime.run_panel.logic import (
    build_finished_display_layout,
    build_panel_render_entries,
    build_run_panel_stop_plan,
    coerce_history_return_code,
    display_test_number,
    history_verdict_from_result,
    normalize_finished_output,
    should_block_test_action,
    should_clear_finished_input,
    should_queue_follow_up_test,
)
from arena_forge.core.domain import OutputEvaluation, OutputReferenceKind, Verdict


@dataclass
class _FakeTest:
    test_string: str
    fold: bool = True
    rtcode: int = 0
    answer_check: Optional[bool] = None

    def is_correct_answer(self, answer: str) -> Optional[bool]:
        return self.answer_check


class RunPanelLogicTests(unittest.TestCase):
    def test_should_block_click_actions_only_while_running(self) -> None:
        self.assertTrue(should_block_test_action(True, "test-run"))
        self.assertFalse(should_block_test_action(False, "test-run"))
        self.assertFalse(should_block_test_action(True, "test-stop"))

    def test_build_panel_render_entries_marks_running_and_accdec_slots(self) -> None:
        tests = [
            _FakeTest("1\n", fold=False, answer_check=True),
            _FakeTest("2\n", fold=True),
        ]
        entries = build_panel_render_entries(
            tests,
            ["ok", ""],
            proc_run=False,
            running_test=None,
            test_iter=2,
        )
        self.assertEqual(entries[0].test_id, 0)
        self.assertEqual(entries[0].config_point, 0)
        self.assertEqual(entries[0].accdec_action, "decline")
        self.assertEqual(entries[0].accdec_point, len("1\nok"))
        self.assertEqual(entries[1].config_point, len("1\nok\n\n"))

    def test_normalize_finished_output_appends_spacing_for_new_test(self) -> None:
        self.assertEqual(normalize_finished_output("42\n", True), "42\n\n")
        self.assertEqual(normalize_finished_output("42\n", False), "42")

    def test_stop_helpers_capture_follow_up_rules(self) -> None:
        self.assertTrue(should_clear_finished_input(True, Verdict.ACCEPTED))
        self.assertFalse(should_clear_finished_input(True, Verdict.UNKNOWN))
        self.assertEqual(display_test_number(0), 1)
        self.assertEqual(display_test_number(4), 5)
        self.assertEqual(history_verdict_from_result(Verdict.ACCEPTED), "accepted")
        self.assertEqual(history_verdict_from_result(Verdict.REJECTED), "rejected")
        self.assertEqual(coerce_history_return_code(7), 7)
        self.assertEqual(coerce_history_return_code("oops"), -1)
        self.assertTrue(
            should_queue_follow_up_test(0, verdict=Verdict.ACCEPTED, running_new=True, have_pretests=True)
        )
        self.assertFalse(
            should_queue_follow_up_test(0, verdict=Verdict.REJECTED, running_new=True, have_pretests=True)
        )
        self.assertFalse(
            should_queue_follow_up_test(1, verdict=Verdict.ACCEPTED, running_new=True, have_pretests=True)
        )

    def test_build_run_panel_stop_plan_captures_rendering_history_and_follow_up(self) -> None:
        evaluation = OutputEvaluation(
            checker_name="normalized_text",
            verdict=Verdict.ACCEPTED,
            reference_kind=OutputReferenceKind.ACCEPTED,
            normalized_actual="42",
            normalized_expected="42",
        )

        plan = build_run_panel_stop_plan(
            return_code=0,
            input_text="1 2",
            output_text="42\n",
            running_new=True,
            have_pretests=True,
            evaluation=evaluation,
        )

        self.assertEqual(plan.output_text, "42\n\n")
        self.assertEqual(plan.verdict, Verdict.ACCEPTED)
        self.assertTrue(plan.clear_input)
        self.assertEqual(plan.rendered_text, "")
        self.assertEqual(plan.history_verdict, "accepted")
        self.assertEqual(plan.history_return_code, 0)
        self.assertTrue(plan.queue_follow_up)
        self.assertEqual(plan.evaluation, evaluation)

    def test_build_run_panel_stop_plan_preserves_output_for_rejected_or_runtime_error(self) -> None:
        rejected = OutputEvaluation(
            checker_name="normalized_text",
            verdict=Verdict.REJECTED,
            reference_kind=OutputReferenceKind.ACCEPTED,
            normalized_actual="0",
            normalized_expected="1",
        )
        rejected_plan = build_run_panel_stop_plan(
            return_code=0,
            input_text="input",
            output_text="0\n",
            running_new=True,
            have_pretests=True,
            evaluation=rejected,
        )
        runtime_error_plan = build_run_panel_stop_plan(
            return_code="crash",
            input_text="input",
            output_text="segfault\n",
            running_new=False,
            have_pretests=False,
            evaluation=None,
        )

        self.assertFalse(rejected_plan.clear_input)
        self.assertEqual(rejected_plan.rendered_text, "input\n0\n\n")
        self.assertFalse(rejected_plan.queue_follow_up)
        self.assertEqual(runtime_error_plan.verdict, Verdict.RUNTIME_ERROR)
        self.assertEqual(runtime_error_plan.history_return_code, -1)
        self.assertEqual(runtime_error_plan.rendered_text, "input\nsegfault\n\n")

    def test_build_finished_display_layout_merges_prompt_and_input_for_unknown_output(self) -> None:
        prompt = "\u8bf7\u8f93\u5165\u6b63\u6574\u6570:"
        layout = build_finished_display_layout(
            "12\n",
            prompt + "3 1\n\n",
            Verdict.UNKNOWN,
        )
        self.assertEqual(layout.body_text, prompt + "12\n3 1\n\n")
        self.assertEqual(layout.output_start_offset, len(prompt + "12\n"))

    def test_build_run_panel_stop_plan_preserves_raw_output_but_formats_display_output(self) -> None:
        plan = build_run_panel_stop_plan(
            return_code=0,
            input_text="12\n",
            output_text="\u8bf7\u8f93\u5165\u6b63\u6574\u6570:3 1\n",
            running_new=True,
            have_pretests=False,
            evaluation=OutputEvaluation(
                checker_name="normalized_text",
                verdict=Verdict.UNKNOWN,
                reference_kind=OutputReferenceKind.NONE,
                normalized_actual="\u8bf7\u8f93\u5165\u6b63\u6574\u6570:3 1",
            ),
        )
        self.assertEqual(plan.output_text, "\u8bf7\u8f93\u5165\u6b63\u6574\u6570:3 1\n\n")
        self.assertEqual(plan.rendered_text, "\u8bf7\u8f93\u5165\u6b63\u6574\u6570:12\n3 1\n\n")
        self.assertEqual(plan.output_start_offset, len("\u8bf7\u8f93\u5165\u6b63\u6574\u6570:12\n"))


if __name__ == "__main__":
    unittest.main()
