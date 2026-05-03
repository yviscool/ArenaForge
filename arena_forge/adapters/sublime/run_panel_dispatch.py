from __future__ import annotations

from typing import Optional

from sublime import Region

from .command_action_catalog import SUPPORTED_TEST_MANAGER_ACTIONS
from .messages import product_log_message, status_message
from .run_panel_input_actions import (
    clear_current_input,
    delete_previous_word,
    history_next,
    history_previous,
    move_input_backward_word,
    move_input_forward_word,
    move_input_line_end,
    move_input_line_start,
)
from .run_panel_session_actions import make_opd
from .view_actions import erase_region, replace_all, replace_region, set_cursor_to_end


def dispatch_test_manager_action(
    command,
    edit,
    *,
    action=None,
    run_file=None,
    build_sys=None,
    text=None,
    clr_tests=False,
    sync_out=False,
    code_view_id=None,
    var_name=None,
    use_debugger=False,
    pos=None,
    load_session=False,
    region=None,
    frame_id=None,
    data=None,
    id=None,
    dir=1,
) -> bool:
    view = command.view

    def close_command() -> None:
        try:
            if command.state.tester is not None:
                command.state.tester.process_manager.terminate()
        except Exception:
            product_log_message("error.process_termination_failed")

    def toggle_debugger() -> None:
        command.state.use_debugger = not command.state.use_debugger
        status_message("status.debugger_enabled" if command.state.use_debugger else "status.debugger_disabled")

    action_handlers = {
        "insert_line": lambda: command.insert_text(edit),
        "insert_cb": lambda: command.insert_cb(edit),
        "insert_opd_input": lambda: _insert_panel_text(command, edit, text),
        "insert_opd_out": lambda: _insert_panel_text(command, edit, text),
        "replace": lambda: replace_region(view, edit, region, text),
        "erase": lambda: erase_region(view, edit, region),
        "apply_edit_changes": command.apply_edit_changes,
        "clear_all_tests": command.clear_all_tests,
        "clear_current_input": lambda: clear_current_input(command, edit),
        "history_next": lambda: history_next(command, edit),
        "history_previous": lambda: history_previous(command, edit),
        "make_opd": lambda: make_opd(
            command,
            edit,
            run_file=run_file,
            build_sys=build_sys,
            clr_tests=clr_tests,
            sync_out=sync_out,
            code_view_id=code_view_id,
            use_debugger=use_debugger,
            load_session=load_session,
        ),
        "redirect_var_value": lambda: command.redirect_var_value(var_name, pos=pos),
        "close": close_command,
        "redirect_frames": command.redirect_frames,
        "select_frame": lambda: command.select_frame(frame_id),
        "new_test": lambda: command.new_test(edit),
        "toggle_new_test": command.toggle_new_test,
        "delete_tests": lambda: command.delete_tests(edit),
        "delete_previous_word": lambda: delete_previous_word(command, edit),
        "accept_test": command.set_tests_status,
        "decline_test": lambda: command.set_tests_status(accept=False),
        "erase_all": lambda: replace_all(view, edit, "\n"),
        "show_text": lambda: _show_text(command, edit),
        "hide_text": lambda: _hide_text(command),
        "kill_proc": lambda: command.state.tester.terminate(),
        "sync_read_only": command.sync_read_only,
        "enable_edit_mode": command.enable_edit_mode,
        "set_test_input": lambda: command.set_test_input(id=id, test=data),
        "delete_test": lambda: command.delete_test(edit, id),
        "swap_tests": lambda: command.swap_tests(edit, dir=dir),
        "toggle_hide_phantoms": command.toggle_hide_phantoms,
        "toggle_using_debugger": toggle_debugger,
        "move_input_line_start": lambda: move_input_line_start(command),
        "move_input_line_end": lambda: move_input_line_end(command),
        "move_input_backward_word": lambda: move_input_backward_word(command),
        "move_input_forward_word": lambda: move_input_forward_word(command),
        "set_cursor_to_end": lambda: set_cursor_to_end(view),
    }
    assert tuple(sorted(action_handlers)) == tuple(sorted(SUPPORTED_TEST_MANAGER_ACTIONS))

    handler = action_handlers.get(action)
    if handler is None:
        return True
    handler()
    return action != "enable_edit_mode"


def _insert_panel_text(command, edit, text: Optional[str]) -> None:
    if text is None:
        return
    command.view.insert(edit, command.state.delta_input, text)
    command.state.delta_input += len(text)


def _show_text(command, edit) -> None:
    replace_all(command.view, edit, command.state.text_buffer)
    set_cursor_to_end(command.view)


def _hide_text(command) -> None:
    command.state.text_buffer = command.view.substr(Region(0, command.view.size()))
    command.state.sel_buffer = command.view.sel()
    command.view.run_command("test_manager", {"action": "erase_all"})
