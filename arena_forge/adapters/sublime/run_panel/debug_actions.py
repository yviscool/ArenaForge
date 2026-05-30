from __future__ import annotations

from ..debug_protocol import read_frames, supports_variable_inspection
from ..debug_protocol import select_frame as select_debugger_frame


def get_view_by_id(command, view_id):
    for view in command.view.window().views():
        if view.id() == view_id:
            return view
    return None


def _get_code_view(command):
    return get_view_by_id(command, command.state.code_view_id)


def prepare_code_view(command) -> None:
    code_view = _get_code_view(command)
    if code_view and code_view.is_dirty():
        code_view.run_command("save")


def redirect_var_value(command, var_name, pos=None) -> None:
    if not supports_variable_inspection(command.state.tester.process_manager):
        return
    value = command.state.tester.process_manager.get_var_value(var_name)
    code_view = _get_code_view(command)
    if code_view is not None:
        code_view.run_command("debug_overlay", {"action": "show_var_value", "value": value, "pos": pos})


def redirect_frames(command) -> None:
    frames = read_frames(command.state.tester.process_manager)
    code_view = _get_code_view(command)
    if code_view is not None:
        code_view.run_command("debug_overlay", {"action": "show_frames", "frames": frames})


def select_frame(command, frame_id) -> None:
    select_debugger_frame(command.state.tester.process_manager, frame_id)
