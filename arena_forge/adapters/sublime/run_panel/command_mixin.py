from __future__ import annotations

from ..shared.messages import status_message
from .action_request import RunPanelActionRequest
from .command_support import (
    add_transient_region as add_run_panel_transient_region,
)
from .command_support import (
    change_process_status as change_run_panel_process_status,
)
from .command_support import (
    get_style_test_status as get_run_panel_style_test_status,
)
from .command_support import (
    insert_clipboard_input as insert_run_panel_clipboard_input,
)
from .command_support import (
    insert_panel_input as insert_run_panel_input,
)
from .command_support import (
    memorize_tests as memorize_run_panel_tests,
)
from .command_support import (
    renumerate_tests as renumerate_run_panel_tests,
)
from .command_support import (
    set_compile_bar as set_run_panel_compile_bar,
)
from .debug_actions import (
    get_view_by_id as get_run_panel_view_by_id,
)
from .debug_actions import (
    prepare_code_view as prepare_run_panel_code_view,
)
from .debug_actions import (
    redirect_frames as redirect_run_panel_frames,
)
from .debug_actions import (
    redirect_var_value as redirect_run_panel_var_value,
)
from .debug_actions import (
    select_frame as select_run_panel_frame,
)
from .dispatch import dispatch_test_manager_action
from .display_actions import start_new_test
from .display_actions import update_configs as update_run_panel_configs
from .edit_actions import (
    apply_edit_changes as apply_run_panel_edit_changes,
)
from .edit_actions import (
    enable_edit_mode as enable_run_panel_edit_mode,
)
from .edit_actions import (
    get_begin_region as get_run_panel_begin_region,
)
from .edit_actions import (
    toggle_new_test as toggle_run_panel_new_test,
)
from .logic import should_block_test_action
from .regions import compute_tie_pos, sync_read_only_mode
from .session_actions import clear_all as clear_run_panel
from .session_actions import handle_process_stop
from .session_actions import make_opd as make_run_panel
from .test_actions import (
    clear_all_tests as clear_run_panel_all_tests,
)
from .test_actions import (
    delete_nth_test as delete_run_panel_nth_test,
)
from .test_actions import (
    delete_test as delete_run_panel_test,
)
from .test_actions import (
    delete_tests as delete_run_panel_tests,
)
from .test_actions import (
    fold_accept_tests as fold_run_panel_accept_tests,
)
from .test_actions import (
    handle_accdec_event as handle_run_panel_accdec_event,
)
from .test_actions import (
    handle_test_event as handle_run_panel_test_event,
)
from .test_actions import (
    open_test_edit as open_run_panel_test_edit,
)
from .test_actions import (
    set_test_input as set_run_panel_test_input,
)
from .test_actions import (
    set_test_status as set_run_panel_test_status,
)
from .test_actions import (
    set_tests_status as set_run_panel_tests_status,
)
from .test_actions import (
    swap_tests as swap_run_panel_tests,
)
from .test_actions import (
    toggle_fold as toggle_run_panel_fold,
)
from .test_actions import (
    toggle_hide_phantoms as toggle_run_panel_hide_phantoms,
)


class RunPanelCommandMixin:
    def insert_text(self, edit, text=None):
        insert_run_panel_input(self, edit, text=text)

    def insert_cb(self, edit):
        insert_run_panel_clipboard_input(self, edit)

    def toggle_fold(self, index):
        toggle_run_panel_fold(self, index)

    def open_test_edit(self, index):
        open_run_panel_test_edit(self, index)

    def get_tie_pos(self, index):
        return compute_tie_pos(self.state.tester, index)

    def on_test_action(self, index, event):
        tester = self.state.tester
        if should_block_test_action(tester.proc_run, event):
            status_message("status.action_while_running", action=event)
            return
        handle_run_panel_test_event(self, index, event)

    def on_accdec_action(self, index, event):
        handle_run_panel_accdec_event(self, index, event)

    def set_test_input(self, test=None, id=None):
        set_run_panel_test_input(self, test=test, test_id=id)

    def update_configs(self, update_last=None):
        update_run_panel_configs(self, update_last=update_last)

    def new_test(self, edit):
        start_new_test(self, edit)

    def memorize_tests(self):
        memorize_run_panel_tests(self)

    def on_insert(self, text):
        self.view.run_command("test_manager", {"action": "insert_opd_input", "text": text})

    def on_out(self, text):
        self.view.run_command("test_manager", {"action": "insert_opd_out", "text": text})

    def add_region(self, line, region_prop):
        add_run_panel_transient_region(self, line, region_prop)

    def on_stop(self, rtcode, runtime, crash_line=None):
        handle_process_stop(self, rtcode, runtime, crash_line=crash_line)

    def redirect_var_value(self, var_name, pos=None):
        redirect_run_panel_var_value(self, var_name, pos=pos)

    def redirect_frames(self):
        redirect_run_panel_frames(self)

    def select_frame(self, id):
        select_run_panel_frame(self, id)

    def toggle_side_bar(self):
        self.view.window().run_command("toggle_side_bar")

    def set_test_status(self, nth, accept=True, call_tester=True):
        set_run_panel_test_status(self, nth, accept=accept, call_tester=call_tester)

    def set_tests_status(self, accept=True):
        set_run_panel_tests_status(self, accept=accept)

    def fold_accept_tests(self):
        fold_run_panel_accept_tests(self)

    def change_process_status(self, status):
        change_run_panel_process_status(self, status)

    def clear_all(self):
        clear_run_panel(self)

    def set_compile_bar(self, cmd, type=""):
        set_run_panel_compile_bar(self, cmd, type=type)

    def get_view_by_id(self, id):
        return get_run_panel_view_by_id(self, id)

    def prepare_code_view(self):
        prepare_run_panel_code_view(self)

    def make_opd(
        self,
        edit,
        run_file=None,
        build_sys=None,
        clr_tests=False,
        sync_out=False,
        code_view_id=None,
        use_debugger=False,
        load_session=False,
    ):
        make_run_panel(
            self,
            edit,
            run_file=run_file,
            build_sys=build_sys,
            clr_tests=clr_tests,
            sync_out=sync_out,
            code_view_id=code_view_id,
            use_debugger=use_debugger,
            load_session=load_session,
        )

    def delete_nth_test(self, edit, nth, fixed_end=None):
        delete_run_panel_nth_test(self, edit, nth, fixed_end=fixed_end)

    def delete_test(self, edit, id):
        delete_run_panel_test(self, edit, id)

    def get_style_test_status(self, nth):
        return get_run_panel_style_test_status(self, nth)

    def renumerate_tests(self, edit, max_nth_test):
        renumerate_run_panel_tests(self, edit, max_nth_test)

    def delete_tests(self, edit):
        delete_run_panel_tests(self, edit)

    def sync_read_only(self):
        sync_read_only_mode(self.view, self.state.tester, self.state.delta_input)

    def enable_edit_mode(self):
        enable_run_panel_edit_mode(self)

    def get_begin_region(self, id):
        return get_run_panel_begin_region(self, id)

    def apply_edit_changes(self):
        apply_run_panel_edit_changes(self)

    def toggle_new_test(self):
        toggle_run_panel_new_test(self)

    def swap_tests(self, edit, dir=-1):
        swap_run_panel_tests(self, edit, direction=dir)

    def toggle_hide_phantoms(self):
        toggle_run_panel_hide_phantoms(self)

    def clear_all_tests(self):
        clear_run_panel_all_tests(self)

    def run(
        self,
        edit,
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
    ):
        self.view.set_read_only(False)
        request = RunPanelActionRequest.from_command_args(
            action=action,
            run_file=run_file,
            build_sys=build_sys,
            text=text,
            clr_tests=clr_tests,
            sync_out=sync_out,
            code_view_id=code_view_id,
            var_name=var_name,
            use_debugger=use_debugger,
            pos=pos,
            load_session=load_session,
            region=region,
            frame_id=frame_id,
            data=data,
            id=id,
            dir=dir,
        )
        should_sync = dispatch_test_manager_action(
            self,
            edit,
            request,
        )
        if should_sync:
            self.sync_read_only()

    def isEnabled(self, args):
        pass
