from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Protocol, Tuple, Union

from arena_forge.core.domain import OutputEvaluation, Verdict

_BLOCKED_TEST_EVENTS = frozenset({"test-click", "test-edit", "test-run"})
_PROMPT_DELIMITERS = (":", "\uff1a", ">", "?", "\uff1f")
_PROMPT_KEYWORDS = ("enter", "input", "please", "\u8bf7", "\u8f93\u5165")


class SupportsRenderTest(Protocol):
    test_string: str
    fold: bool
    rtcode: object

    def is_correct_answer(self, answer: str) -> Optional[bool]:
        ...


@dataclass(frozen=True)
class PanelRenderEntry:
    test_id: int
    config_point: int
    running: bool
    accdec_point: Optional[int] = None
    accdec_action: Optional[str] = None


@dataclass(frozen=True)
class RunPanelStopPlan:
    output_text: str
    verdict: Verdict
    evaluation: Optional[OutputEvaluation]
    clear_input: bool
    rendered_text: str
    output_start_offset: int
    history_verdict: str
    history_return_code: int
    queue_follow_up: bool


@dataclass(frozen=True)
class FinishedDisplayLayout:
    body_text: str
    output_start_offset: int


def should_block_test_action(proc_run: bool, event: str) -> bool:
    return proc_run and event in _BLOCKED_TEST_EVENTS


def build_panel_render_entries(
    tests: List[SupportsRenderTest],
    outputs: List[str],
    *,
    proc_run: bool,
    running_test: Optional[int],
    test_iter: int,
) -> Tuple[PanelRenderEntry, ...]:
    render_limit = test_iter + 1 if proc_run else test_iter
    render_limit = min(render_limit, len(tests))
    point = 0
    entries: List[PanelRenderEntry] = []
    for test_id in range(render_limit):
        test = tests[test_id]
        output = outputs[test_id] if test_id < len(outputs) else ""
        running = proc_run and test_id == running_test
        visible_text = resolve_visible_body_text(test, output, running=running)
        accdec_point = None
        accdec_action = None
        config_point = point

        if running or not test.fold:
            point += len(visible_text)

        if not running and not test.fold and str(test.rtcode) == "0" and output:
            accdec_point = point
            accdec_action = "decline" if test.is_correct_answer(output) else "accept"

        entries.append(
            PanelRenderEntry(
                test_id=test_id,
                config_point=config_point,
                running=running,
                accdec_point=accdec_point,
                accdec_action=accdec_action,
            )
        )
    return tuple(entries)


def normalize_finished_output(output_text: str, running_new: bool) -> str:
    output = output_text.rstrip()
    if running_new:
        return output + "\n\n"
    return output


def should_clear_finished_input(running_new: bool, verdict: Verdict) -> bool:
    return running_new and verdict == Verdict.ACCEPTED


def history_verdict_from_result(verdict: Verdict) -> str:
    return verdict.value


def display_test_number(test_id: int) -> int:
    return test_id + 1


def coerce_history_return_code(return_code: Union[int, str]) -> int:
    string_rtcode = str(return_code)
    if string_rtcode.lstrip("-").isdigit():
        return int(string_rtcode)
    return -1


def should_queue_follow_up_test(
    return_code: Union[int, str], *, verdict: Verdict, running_new: bool, have_pretests: bool
) -> bool:
    return str(return_code) == "0" and verdict != Verdict.REJECTED and running_new and have_pretests


def _default_finished_display_layout(input_text: str, output_text: str) -> FinishedDisplayLayout:
    separator = "" if not input_text or input_text.endswith("\n") else "\n"
    return FinishedDisplayLayout(
        body_text=input_text + separator + output_text,
        output_start_offset=len(input_text + separator),
    )


def _build_prompt_transcript_layout(
    input_text: str,
    output_text: str,
    verdict: Verdict,
) -> Optional[FinishedDisplayLayout]:
    if verdict != Verdict.UNKNOWN:
        return None
    stripped_input = input_text.rstrip("\r\n")
    if not stripped_input or "\n" in stripped_input:
        return None
    stripped_output = output_text.rstrip("\n")
    if "\n" in stripped_output:
        return None
    lowered_output = stripped_output.casefold()
    if not any(keyword in lowered_output for keyword in _PROMPT_KEYWORDS):
        return None
    split_index = max(stripped_output.rfind(marker) for marker in _PROMPT_DELIMITERS)
    if split_index < 0 or split_index >= len(stripped_output) - 1:
        return None
    prompt_text = stripped_output[: split_index + 1]
    result_text = stripped_output[split_index + 1 :].lstrip()
    if not result_text:
        return None
    trailing_newlines = output_text[len(stripped_output) :]
    first_line = prompt_text + stripped_input
    return FinishedDisplayLayout(
        body_text=first_line + "\n" + result_text + trailing_newlines,
        output_start_offset=len(first_line) + 1,
    )


def build_finished_display_layout(input_text: str, output_text: str, verdict: Verdict) -> FinishedDisplayLayout:
    prompt_transcript = _build_prompt_transcript_layout(input_text, output_text, verdict)
    if prompt_transcript is not None:
        return prompt_transcript
    return _default_finished_display_layout(input_text, output_text)


def resolve_visible_body_text(test, output_text: str, *, running: bool = False) -> str:
    if running:
        return _default_finished_display_layout(test.test_string, output_text).body_text
    display_body_text = getattr(test, "display_body_text", None)
    if display_body_text is not None:
        return display_body_text
    return _default_finished_display_layout(test.test_string, output_text).body_text


def build_run_panel_stop_plan(
    *,
    return_code: Union[int, str],
    input_text: str,
    output_text: str,
    running_new: bool,
    have_pretests: bool,
    evaluation: Optional[OutputEvaluation],
) -> RunPanelStopPlan:
    normalized_output = normalize_finished_output(output_text, running_new)
    verdict = evaluation.verdict if evaluation is not None else Verdict.RUNTIME_ERROR
    display_layout = build_finished_display_layout(input_text, normalized_output, verdict)
    clear_input = should_clear_finished_input(running_new, verdict)
    rendered_text = "" if clear_input else display_layout.body_text
    return RunPanelStopPlan(
        output_text=normalized_output,
        verdict=verdict,
        evaluation=evaluation,
        clear_input=clear_input,
        rendered_text=rendered_text,
        output_start_offset=display_layout.output_start_offset,
        history_verdict=history_verdict_from_result(verdict),
        history_return_code=coerce_history_return_code(return_code),
        queue_follow_up=should_queue_follow_up_test(
            return_code,
            verdict=verdict,
            running_new=running_new,
            have_pretests=have_pretests,
        ),
    )
