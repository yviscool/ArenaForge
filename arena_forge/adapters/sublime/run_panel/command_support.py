from __future__ import annotations

from random import randint

import sublime
from sublime import Region

from ..messages import translate_status_code
from ..settings_bridge import get_session_repository, get_tests_file_path, infer_language_name
from .input_actions import push_input_history
from .rendering import build_compile_bar_phantom
from .session_service import save_tests_for_run


def insert_panel_input(command, edit, text=None) -> None:
    view = command.view
    expected = view.line(command.state.delta_input).end()
    if len(view.sel()) > 1:
        return
    if view.sel()[0].a != expected or view.sel()[0].b != expected:
        return
    if text is None:
        if not command.state.tester.proc_run:
            return
        to_insert = view.substr(Region(command.state.delta_input, view.sel()[0].b))
        view.insert(edit, view.sel()[0].b, "\n")
    else:
        to_insert = text
        view.insert(edit, view.sel()[0].b, to_insert + "\n")
    command.state.advance_panel_input(view.sel()[0].b)
    push_input_history(command, to_insert)
    command.state.tester.insert(to_insert + "\n")


def insert_clipboard_input(command, edit) -> None:
    clipboard_text = sublime.get_clipboard()
    lines = clipboard_text.split("\n")
    for line in lines[:-1]:
        push_input_history(command, line)
        command.state.tester.insert(line + "\n", call_on_insert=True)
    push_input_history(command, lines[-1])
    command.state.tester.insert(lines[-1], call_on_insert=True)


def memorize_tests(command) -> None:
    save_tests_for_run(
        command.state.source_file,
        command.state.tester.get_tests(),
        get_session_repository(),
        infer_language_name,
        get_tests_file_path,
    )


def add_transient_region(command, line, region_prop) -> None:
    view = command.view
    position = view.line(line)
    view.add_regions(str(randint(0, int(1e9))), [Region(position.a, position.a + 1)], *region_prop)


def change_process_status(command, status: str) -> None:
    command.view.set_status("process_status_code", status)
    command.view.set_status("process_status", translate_status_code(status))


def set_compile_bar(command, cmd: str, type: str = "") -> None:
    command.state.test_phantoms[0].update([build_compile_bar_phantom(command.view, cmd, type=type)])


def get_style_test_status(command, test_id):
    check = command.state.tester.check_test(test_id)
    if check:
        return command.REGION_ACCEPT_PROP
    if check is False:
        return command.REGION_DECLINE_PROP
    return command.REGION_UNKNOWN_PROP


def renumerate_tests(command, edit, max_nth_test):
    view = command.view
    current = 0
    for index in range(max_nth_test):
        begin_key = command.REGION_BEGIN_KEY % index
        begin_regions = view.get_regions(begin_key)
        if not begin_regions:
            continue
        begin_region = begin_regions[0]
        view.erase_regions(begin_key)
        view.add_regions(command.REGION_BEGIN_KEY % current, [begin_region], *command.REGION_BEGIN_PROP)

        line_regions = view.get_regions("line_%d" % current)
        view.erase_regions("line_%d" % index)
        view.add_regions("line_%d" % current, line_regions, *command.REGION_LINE_PROP)

        end_key = command.REGION_END_KEY % index
        end_regions = view.get_regions(end_key)
        if end_regions:
            end_region = end_regions[0]
            view.erase_regions(end_key)
            view.add_regions(command.REGION_END_KEY % current, [end_region], *command.REGION_END_PROP)

        current += 1
