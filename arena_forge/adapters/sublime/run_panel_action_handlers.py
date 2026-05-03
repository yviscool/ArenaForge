from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict

from sublime import Region

from .command_action_catalog import SUPPORTED_TEST_MANAGER_ACTIONS
from .messages import product_log_message, status_message
from .run_panel_action_request import RunPanelActionRequest
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


@dataclass(frozen=True)
class RunPanelActionContext:
    command: Any
    edit: Any
    request: RunPanelActionRequest

    @property
    def view(self):
        return self.command.view


@dataclass(frozen=True)
class RunPanelActionHandler:
    callback: Callable[[RunPanelActionContext], None]
    sync_read_only: bool = True


def build_test_manager_action_handlers(context: RunPanelActionContext) -> Dict[str, RunPanelActionHandler]:
    handlers = {
        "insert_line": RunPanelActionHandler(lambda ctx: ctx.command.insert_text(ctx.edit)),
        "insert_cb": RunPanelActionHandler(lambda ctx: ctx.command.insert_cb(ctx.edit)),
        "insert_opd_input": RunPanelActionHandler(lambda ctx: _insert_panel_text(ctx, ctx.request.text)),
        "insert_opd_out": RunPanelActionHandler(lambda ctx: _insert_panel_text(ctx, ctx.request.text)),
        "replace": RunPanelActionHandler(
            lambda ctx: replace_region(ctx.view, ctx.edit, ctx.request.region, ctx.request.text)
        ),
        "erase": RunPanelActionHandler(lambda ctx: erase_region(ctx.view, ctx.edit, ctx.request.region)),
        "apply_edit_changes": RunPanelActionHandler(lambda ctx: ctx.command.apply_edit_changes()),
        "clear_all_tests": RunPanelActionHandler(lambda ctx: ctx.command.clear_all_tests()),
        "clear_current_input": RunPanelActionHandler(lambda ctx: clear_current_input(ctx.command, ctx.edit)),
        "history_next": RunPanelActionHandler(lambda ctx: history_next(ctx.command, ctx.edit)),
        "history_previous": RunPanelActionHandler(lambda ctx: history_previous(ctx.command, ctx.edit)),
        "make_opd": RunPanelActionHandler(lambda ctx: make_opd(ctx.command, ctx.edit, **ctx.request.to_make_opd_kwargs())),
        "redirect_var_value": RunPanelActionHandler(
            lambda ctx: ctx.command.redirect_var_value(ctx.request.var_name, pos=ctx.request.pos)
        ),
        "close": RunPanelActionHandler(_close_command),
        "redirect_frames": RunPanelActionHandler(lambda ctx: ctx.command.redirect_frames()),
        "select_frame": RunPanelActionHandler(lambda ctx: ctx.command.select_frame(ctx.request.frame_id)),
        "new_test": RunPanelActionHandler(lambda ctx: ctx.command.new_test(ctx.edit)),
        "toggle_new_test": RunPanelActionHandler(lambda ctx: ctx.command.toggle_new_test()),
        "delete_tests": RunPanelActionHandler(lambda ctx: ctx.command.delete_tests(ctx.edit)),
        "delete_previous_word": RunPanelActionHandler(lambda ctx: delete_previous_word(ctx.command, ctx.edit)),
        "accept_test": RunPanelActionHandler(lambda ctx: ctx.command.set_tests_status()),
        "decline_test": RunPanelActionHandler(lambda ctx: ctx.command.set_tests_status(accept=False)),
        "erase_all": RunPanelActionHandler(lambda ctx: replace_all(ctx.view, ctx.edit, "\n")),
        "show_text": RunPanelActionHandler(_show_text),
        "hide_text": RunPanelActionHandler(_hide_text),
        "kill_proc": RunPanelActionHandler(lambda ctx: ctx.command.state.tester.terminate()),
        "sync_read_only": RunPanelActionHandler(lambda ctx: ctx.command.sync_read_only()),
        "enable_edit_mode": RunPanelActionHandler(lambda ctx: ctx.command.enable_edit_mode(), sync_read_only=False),
        "set_test_input": RunPanelActionHandler(
            lambda ctx: ctx.command.set_test_input(id=ctx.request.id, test=ctx.request.data)
        ),
        "delete_test": RunPanelActionHandler(lambda ctx: ctx.command.delete_test(ctx.edit, ctx.request.id)),
        "swap_tests": RunPanelActionHandler(lambda ctx: ctx.command.swap_tests(ctx.edit, dir=ctx.request.dir)),
        "toggle_hide_phantoms": RunPanelActionHandler(lambda ctx: ctx.command.toggle_hide_phantoms()),
        "toggle_using_debugger": RunPanelActionHandler(_toggle_debugger),
        "move_input_line_start": RunPanelActionHandler(lambda ctx: move_input_line_start(ctx.command)),
        "move_input_line_end": RunPanelActionHandler(lambda ctx: move_input_line_end(ctx.command)),
        "move_input_backward_word": RunPanelActionHandler(lambda ctx: move_input_backward_word(ctx.command)),
        "move_input_forward_word": RunPanelActionHandler(lambda ctx: move_input_forward_word(ctx.command)),
        "set_cursor_to_end": RunPanelActionHandler(lambda ctx: set_cursor_to_end(ctx.view)),
    }
    assert tuple(sorted(handlers)) == tuple(sorted(SUPPORTED_TEST_MANAGER_ACTIONS))
    return handlers


def _close_command(context: RunPanelActionContext) -> None:
    try:
        if context.command.state.tester is not None:
            context.command.state.tester.process_manager.terminate()
    except Exception:
        product_log_message("error.process_termination_failed")


def _toggle_debugger(context: RunPanelActionContext) -> None:
    context.command.state.use_debugger = not context.command.state.use_debugger
    status_message(
        "status.debugger_enabled" if context.command.state.use_debugger else "status.debugger_disabled"
    )


def _insert_panel_text(context: RunPanelActionContext, text: str) -> None:
    if text is None:
        return
    context.view.insert(context.edit, context.command.state.delta_input, text)
    context.command.state.advance_panel_input(context.command.state.delta_input + len(text))


def _show_text(context: RunPanelActionContext) -> None:
    replace_all(context.view, context.edit, context.command.state.text_buffer)
    set_cursor_to_end(context.view)


def _hide_text(context: RunPanelActionContext) -> None:
    context.command.state.text_buffer = context.view.substr(Region(0, context.view.size()))
    context.command.state.sel_buffer = context.view.sel()
    context.view.run_command("test_manager", {"action": "erase_all"})
