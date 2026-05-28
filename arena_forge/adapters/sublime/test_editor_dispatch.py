from __future__ import annotations

from typing import Optional

from .command_action_catalog import SUPPORTED_TEST_EDITOR_ACTIONS
from .messages import product_log_message, status_message
from .run_panel_process_actions import terminate_tester
from .view_actions import erase_region, replace_all, replace_region, set_cursor_to_end


def dispatch_test_editor_action(
    command,
    edit,
    *,
    action=None,
    run_file=None,
    build_sys=None,
    text=None,
    clr_tests=False,
    test="",
    source_view_id=None,
    var_name=None,
    test_id=None,
    pos=None,
    load_session=False,
    region=None,
    frame_id=None,
) -> bool:
    view = command.view

    def close_command() -> None:
        terminate_tester(
            command.state.tester,
            on_failure=lambda: product_log_message("error.process_termination_failed"),
        )

    def toggle_debugger() -> None:
        command.state.use_debugger = not command.state.use_debugger
        status_message("status.debugger_enabled" if command.state.use_debugger else "status.debugger_disabled")

    action_handlers = {
        "insert_line": lambda: command.insert_text(edit),
        "insert_cb": lambda: command.insert_cb(edit),
        "insert_opd_input": lambda: _insert_panel_input(command, edit, text),
        "insert_opd_out": lambda: _append_panel_output(command, edit, text),
        "replace": lambda: replace_region(view, edit, region, text),
        "erase": lambda: erase_region(view, edit, region),
        "init": lambda: command.init(
            edit,
            run_file=run_file,
            build_sys=build_sys,
            clr_tests=clr_tests,
            test=test,
            source_view_id=source_view_id,
            test_id=test_id,
            load_session=load_session,
        ),
        "close": close_command,
        "erase_all": lambda: replace_all(view, edit, "\n"),
        "sync_read_only": command.sync_read_only,
        "toggle_using_debugger": toggle_debugger,
        "set_cursor_to_end": lambda: set_cursor_to_end(view),
    }
    assert tuple(sorted(action_handlers)) == tuple(sorted(SUPPORTED_TEST_EDITOR_ACTIONS))
    handler = action_handlers.get(action)
    if handler is None:
        return True
    handler()
    return True


def _insert_panel_input(command, edit, text: Optional[str]) -> None:
    if text is None:
        return
    command.view.insert(edit, command.state.delta_input, text)
    command.state.delta_input += len(text)


def _append_panel_output(command, edit, text: Optional[str]) -> None:
    if text is None:
        return
    command.state.delta_input += len(text)
    command.view.insert(edit, command.view.size(), text)
