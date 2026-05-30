from __future__ import annotations

from typing import Callable, Mapping, Optional

import sublime

_PROCESS_TERMINATION_FAILURES = (AttributeError, OSError)


def log_process_termination_failure() -> None:
    from ..shared.messages import product_log_message

    product_log_message("error.process_termination_failed")


def terminate_tester(
    tester,
    *,
    on_failure: Optional[Callable[[], None]] = None,
) -> bool:
    if tester is None:
        return False
    try:
        tester.terminate()
    except _PROCESS_TERMINATION_FAILURES:
        if on_failure is not None:
            on_failure()
        return False
    return True


def terminate_command_tester(
    command,
    *,
    on_failure: Optional[Callable[[], None]] = None,
) -> bool:
    return terminate_tester(command.state.tester, on_failure=on_failure)


def terminate_tester_with_logging(tester) -> bool:
    return terminate_tester(tester, on_failure=log_process_termination_failure)


def terminate_command_tester_with_logging(command) -> bool:
    return terminate_command_tester(command, on_failure=log_process_termination_failure)


def schedule_test_manager_action(
    view,
    action: str,
    *,
    delay: int = 0,
    **kwargs: object,
) -> None:
    payload = {"action": action, **kwargs}
    sublime.set_timeout_async(lambda payload=payload: view.run_command("test_manager", payload), delay)


def schedule_test_manager_command(
    view,
    command_args: Mapping[str, object],
    *,
    delay: int = 0,
) -> None:
    payload = dict(command_args)
    sublime.set_timeout_async(lambda payload=payload: view.run_command("test_manager", payload), delay)
