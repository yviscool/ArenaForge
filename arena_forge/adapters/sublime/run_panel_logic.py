from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Protocol, Tuple, Union

_BLOCKED_TEST_EVENTS = frozenset({"test-click", "test-edit", "test-run"})


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
        accdec_point = None
        accdec_action = None
        config_point = point

        if running:
            point += len(test.test_string) + len(output) + 2
        elif not test.fold:
            point += len(test.test_string) + len(output) + 1

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

        if not test.fold:
            point += 2
    return tuple(entries)


def normalize_finished_output(output_text: str, running_new: bool) -> str:
    output = output_text.rstrip()
    if running_new:
        return output + "\n\n"
    return output


def should_clear_finished_input(running_new: bool, check_result: Optional[bool]) -> bool:
    return running_new and check_result is True


def history_verdict_from_check(check_result: Optional[bool]) -> str:
    return "accepted" if check_result else "unknown"


def should_queue_follow_up_test(return_code: Union[int, str], *, running_new: bool, have_pretests: bool) -> bool:
    return str(return_code) == "0" and running_new and have_pretests
