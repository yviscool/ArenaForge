from __future__ import annotations

from sublime import Region

import sublime
import sublime_plugin
from sublime import PhantomSet

from ..shared.messages import status_message
from ..shared.package_resources import ARROW_LEFT_ICON_RESOURCE, ARROW_RIGHT_ICON_RESOURCE
from ..view_actions import erase_region, replace_all, replace_region, set_cursor_to_end
from .action_request import RunPanelActionRequest
from .controller_state import RunPanelControllerState
from .debug_actions import redirect_frames, redirect_var_value, select_frame
from .display_actions import start_new_test, update_configs
from .edit_actions import apply_edit_changes, enable_edit_mode, get_begin_region, toggle_new_test
from .input_actions import (
    clear_current_input,
    delete_previous_word,
    history_next,
    history_previous,
    insert_clipboard_input,
    insert_panel_input,
    move_input_backward_word,
    move_input_forward_word,
    move_input_line_end,
    move_input_line_start,
)
from .logic import should_block_test_action
from .process_actions import terminate_command_tester_with_logging
from .regions import compute_tie_pos, sync_read_only_mode
from .session_actions import clear_all, handle_process_stop, make_opd
from .state import PanelTestState
from .test_actions import (
    clear_all_tests,
    delete_nth_test,
    delete_test,
    delete_tests,
    fold_accept_tests,
    handle_accdec_event,
    handle_test_event,
    open_test_edit,
    set_test_input,
    set_test_status,
    set_tests_status,
    swap_tests,
    toggle_fold,
    toggle_hide_phantoms,
)
from .tester import RunPanelTester


def _insert_panel_text(command, edit, request):
    text = request.text
    if text is None:
        return
    command.view.insert(edit, command.state.delta_input, text)
    command.state.advance_panel_input(command.state.delta_input + len(text))


def _show_text(command, edit, request):
    replace_all(command.view, edit, command.state.text_buffer)
    set_cursor_to_end(command.view)


def _hide_text(command, edit, request):
    command.state.text_buffer = command.view.substr(Region(0, command.view.size()))
    command.state.sel_buffer = command.view.sel()
    command.view.run_command("test_manager", {"action": "erase_all"})


def _terminate_command(command, edit, request):
    terminate_command_tester_with_logging(command)


def _toggle_debugger(command, edit, request):
    command.state.use_debugger = not command.state.use_debugger
    status_message(
        "status.debugger_enabled" if command.state.use_debugger else "status.debugger_disabled"
    )


_ACTION_HANDLERS = {
    "insert_line": (lambda cmd, edit, req: insert_panel_input(cmd, edit), True),
    "insert_cb": (lambda cmd, edit, req: insert_clipboard_input(cmd, edit), True),
    "insert_opd_input": (_insert_panel_text, True),
    "insert_opd_out": (_insert_panel_text, True),
    "replace": (lambda cmd, edit, req: replace_region(cmd.view, edit, req.region, req.text), True),
    "erase": (lambda cmd, edit, req: erase_region(cmd.view, edit, req.region), True),
    "apply_edit_changes": (lambda cmd, edit, req: apply_edit_changes(cmd), True),
    "clear_all_tests": (lambda cmd, edit, req: clear_all_tests(cmd), True),
    "clear_current_input": (lambda cmd, edit, req: clear_current_input(cmd, edit), True),
    "history_next": (lambda cmd, edit, req: history_next(cmd, edit), True),
    "history_previous": (lambda cmd, edit, req: history_previous(cmd, edit), True),
    "make_opd": (lambda cmd, edit, req: make_opd(cmd, edit, request=req), True),
    "redirect_var_value": (lambda cmd, edit, req: redirect_var_value(cmd, req.var_name, pos=req.pos), True),
    "close": (_terminate_command, True),
    "redirect_frames": (lambda cmd, edit, req: redirect_frames(cmd), True),
    "select_frame": (lambda cmd, edit, req: select_frame(cmd, req.frame_id), True),
    "new_test": (lambda cmd, edit, req: start_new_test(cmd, edit), True),
    "toggle_new_test": (lambda cmd, edit, req: toggle_new_test(cmd), True),
    "delete_tests": (lambda cmd, edit, req: delete_tests(cmd, edit), True),
    "delete_previous_word": (lambda cmd, edit, req: delete_previous_word(cmd, edit), True),
    "accept_test": (lambda cmd, edit, req: set_tests_status(cmd), True),
    "decline_test": (lambda cmd, edit, req: set_tests_status(cmd, accept=False), True),
    "erase_all": (lambda cmd, edit, req: replace_all(cmd.view, edit, "\n"), True),
    "show_text": (_show_text, True),
    "hide_text": (_hide_text, True),
    "kill_proc": (_terminate_command, True),
    "sync_read_only": (lambda cmd, edit, req: sync_read_only_mode(cmd.view, cmd.state.tester, cmd.state.delta_input), True),
    "enable_edit_mode": (lambda cmd, edit, req: enable_edit_mode(cmd), False),
    "set_test_input": (lambda cmd, edit, req: set_test_input(cmd, test=req.data, test_id=req.id), True),
    "delete_test": (lambda cmd, edit, req: delete_test(cmd, edit, req.id), True),
    "swap_tests": (lambda cmd, edit, req: swap_tests(cmd, edit, direction=req.dir), True),
    "toggle_hide_phantoms": (lambda cmd, edit, req: toggle_hide_phantoms(cmd), True),
    "toggle_using_debugger": (_toggle_debugger, True),
    "move_input_line_start": (lambda cmd, edit, req: move_input_line_start(cmd), True),
    "move_input_line_end": (lambda cmd, edit, req: move_input_line_end(cmd), True),
    "move_input_backward_word": (lambda cmd, edit, req: move_input_backward_word(cmd), True),
    "move_input_forward_word": (lambda cmd, edit, req: move_input_forward_word(cmd), True),
    "set_cursor_to_end": (lambda cmd, edit, req: set_cursor_to_end(cmd.view), True),
}


def _dispatch_action(command, edit, request):
    entry = _ACTION_HANDLERS.get(request.action)
    if entry is None:
        return True
    callback, sync_read_only = entry
    callback(command, edit, request)
    return sync_read_only


class TestManagerCommand(sublime_plugin.TextCommand):
    BEGIN_TEST_STRING = 'Test %d {'
    OUT_TEST_STRING = ''
    END_TEST_STRING = '} rtcode %s'
    REGION_BEGIN_KEY = 'test_begin_%d'
    REGION_OUT_KEY = 'test_out_%d'
    REGION_END_KEY = 'test_end_%d'
    REGION_POS_PROP = ['', '', sublime.HIDDEN]
    REGION_ACCEPT_PROP = ['string', 'dot', sublime.HIDDEN]
    REGION_DECLINE_PROP = ['variable.c++', 'dot', sublime.HIDDEN]
    REGION_UNKNOWN_PROP = ['text.plain', 'dot', sublime.HIDDEN]
    REGION_OUT_PROP = ['entity.name.function.opd', 'bookmark', sublime.HIDDEN]
    REGION_BEGIN_PROP = ['string', ARROW_RIGHT_ICON_RESOURCE,
                         sublime.DRAW_NO_FILL | sublime.DRAW_STIPPLED_UNDERLINE |
                         sublime.DRAW_NO_OUTLINE | sublime.DRAW_EMPTY_AS_OVERWRITE]
    REGION_END_PROP = ['variable.c++', ARROW_LEFT_ICON_RESOURCE, sublime.HIDDEN]
    REGION_LINE_PROP = ['string', 'dot',
                        sublime.DRAW_NO_FILL | sublime.DRAW_STIPPLED_UNDERLINE |
                        sublime.DRAW_NO_OUTLINE | sublime.DRAW_EMPTY_AS_OVERWRITE]

    def __init__(self, view):
        self.view = view
        self.state = RunPanelControllerState(
            phantoms=PhantomSet(view, 'test-phantoms'),
            test_phantoms=[PhantomSet(view, 'test-phantoms-' + str(i)) for i in range(10)],
        )

    Test = PanelTestState

    Tester = RunPanelTester

    def get_tie_pos(self, index):
        return compute_tie_pos(self.state.tester, index)

    def on_test_action(self, index, event):
        tester = self.state.tester
        if should_block_test_action(tester.proc_run, event):
            status_message("status.action_while_running", action=event)
            return
        handle_test_event(self, index, event)

    def on_accdec_action(self, index, event):
        handle_accdec_event(self, index, event)

    def update_configs(self, update_last=None):
        update_configs(self, update_last=update_last)

    def on_insert(self, text):
        self.view.run_command("test_manager", {"action": "insert_opd_input", "text": text})

    def on_out(self, text):
        self.view.run_command("test_manager", {"action": "insert_opd_out", "text": text})

    def on_stop(self, rtcode, runtime, crash_line=None):
        handle_process_stop(self, rtcode, runtime, crash_line=crash_line)

    def run(
        self,
        edit,
        **kwargs,
    ):
        self.view.set_read_only(False)
        request = RunPanelActionRequest(**kwargs)
        should_sync = _dispatch_action(self, edit, request)
        if should_sync:
            sync_read_only_mode(self.view, self.state.tester, self.state.delta_input)


class ModifiedListener(sublime_plugin.EventListener):
    def on_selection_modified(self, view):
        if view.get_status('opd_info') == 'opdebugger-file' and not view.settings().get('edit_mode'):
            view.run_command('test_manager', {'action': 'sync_read_only'})

    def on_hover(self, view, point, hover_zone):
        if hover_zone == sublime.HOVER_TEXT:
            view.run_command('debug_overlay', {'action': 'get_var_value', 'pos': point})


class CloseListener(sublime_plugin.EventListener):
    """Listen to Close"""
    def on_pre_close(self, view):
        if view.get_status('opd_info') == 'opdebugger-file':
            view.run_command('test_manager', {'action': 'close'})


class LayoutListener(sublime_plugin.EventListener):
    def move_syncer(self, view):
        w = view.window()
        if w is None:
            return

        prop = w.get_view_index(view)
        view_name = view.name() or ''
        if view_name.endswith('-run'):
            w.set_view_index(view, 1, 0)
            return

        if prop[0] != 1:
            return

        active_view = w.active_view_in_group(0)
        if active_view is None:
            return
        active_view_index = w.get_view_index(active_view)[1]
        w.set_view_index(view, 0, active_view_index + 1)
