from __future__ import annotations

import sublime
from sublime import Region

from .input_actions import push_input_history


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
