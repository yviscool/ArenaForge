from __future__ import annotations

from .debug_protocol import read_frames, supports_variable_inspection
from .debug_protocol import select_frame as select_debugger_frame


def get_view_by_id(command, view_id):
    for view in command.view.window().views():
        if view.id() == view_id:
            return view
    return None


def prepare_code_view(command) -> None:
    code_view = get_view_by_id(command, command.state.code_view_id)
    if code_view and code_view.is_dirty():
        code_view.run_command("save")


def redirect_var_value(command, var_name, pos=None) -> None:
    if not supports_variable_inspection(command.state.tester.process_manager):
        return
    value = command.state.tester.process_manager.get_var_value(var_name)
    for view in command.view.window().views():
        if view.id() == command.state.code_view_id:
            view.run_command("view_tester", {"action": "show_var_value", "value": value, "pos": pos})


def redirect_frames(command) -> None:
    frames = read_frames(command.state.tester.process_manager)
    for view in command.view.window().views():
        if view.id() == command.state.code_view_id:
            view.run_command("view_tester", {"action": "show_frames", "frames": frames})


def select_frame(command, frame_id) -> None:
    select_debugger_frame(command.state.tester.process_manager, frame_id)
