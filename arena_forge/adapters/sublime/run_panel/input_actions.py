from __future__ import annotations


def find_previous_word_boundary(text: str) -> int:
    index = len(text)
    while index > 0 and text[index - 1].isspace():
        index -= 1
    while index > 0 and not text[index - 1].isspace():
        index -= 1
    return index


def find_next_word_boundary(text: str, start_index: int = 0) -> int:
    index = start_index
    length = len(text)
    while index < length and text[index].isspace():
        index += 1
    while index < length and not text[index].isspace():
        index += 1
    return index


def push_input_history(command, text: str) -> None:
    command.state.history.push(text)


def navigate_history(entries, current_index, draft, current_text, direction):
    if not entries:
        return current_index, draft, current_text

    if current_index is None:
        if direction > 0:
            return None, draft, current_text
        return len(entries) - 1, current_text, entries[-1]

    next_index = current_index + direction
    if next_index < 0:
        next_index = 0
    if next_index >= len(entries):
        return None, draft, draft
    return next_index, draft, entries[next_index]


def _editable_region(command):
    tester = command.state.tester
    if tester is None or command.view.size() == 0:
        return None
    start = command.state.delta_input
    end = command.view.line(start).end()
    return start, end


def _clamped_cursor(command, *, require_single_selection=False):
    region = _editable_region(command)
    if region is None:
        return None
    if require_single_selection and len(command.view.sel()) != 1:
        return None
    start, end = region
    selection = command.view.sel()[0]
    cursor = min(max(selection.b, start), end)
    return start, end, cursor


def get_current_input(command):
    from sublime import Region

    region = _editable_region(command)
    if region is None:
        return ""
    start, end = region
    return command.view.substr(Region(start, end))


def set_current_input(command, edit, text: str) -> None:
    from sublime import Region

    region = _editable_region(command)
    if region is None:
        return
    start, end = region
    command.view.replace(edit, Region(start, end), text)
    command.view.sel().clear()
    command.view.sel().add(Region(start + len(text), start + len(text)))


def clear_current_input(command, edit) -> None:
    set_current_input(command, edit, "")


def delete_previous_word(command, edit) -> None:
    from sublime import Region

    info = _clamped_cursor(command, require_single_selection=True)
    if info is None:
        return
    start, end, cursor = info
    if cursor <= start:
        return
    text = command.view.substr(Region(start, cursor))
    delete_start = start + find_previous_word_boundary(text)
    if delete_start >= cursor:
        return
    command.view.erase(edit, Region(delete_start, cursor))
    command.view.sel().clear()
    command.view.sel().add(Region(delete_start, delete_start))


def move_input_line_start(command) -> None:
    from sublime import Region

    region = _editable_region(command)
    if region is None:
        return
    start, _ = region
    command.view.sel().clear()
    command.view.sel().add(Region(start, start))


def move_input_line_end(command) -> None:
    from sublime import Region

    region = _editable_region(command)
    if region is None:
        return
    _, end = region
    command.view.sel().clear()
    command.view.sel().add(Region(end, end))


def move_input_backward_word(command) -> None:
    from sublime import Region

    info = _clamped_cursor(command, require_single_selection=True)
    if info is None:
        return
    start, end, cursor = info
    if cursor <= start:
        return
    text = command.view.substr(Region(start, cursor))
    new_cursor = start + find_previous_word_boundary(text)
    command.view.sel().clear()
    command.view.sel().add(Region(new_cursor, new_cursor))


def move_input_forward_word(command) -> None:
    from sublime import Region

    info = _clamped_cursor(command, require_single_selection=True)
    if info is None:
        return
    start, end, cursor = info
    if cursor >= end:
        return
    text = command.view.substr(Region(cursor, end))
    new_cursor = cursor + find_next_word_boundary(text)
    command.view.sel().clear()
    command.view.sel().add(Region(new_cursor, new_cursor))


def history_previous(command, edit) -> None:
    current_text = get_current_input(command)
    index, draft, text = navigate_history(
        command.state.history.entries,
        command.state.history.index,
        command.state.history.draft,
        current_text,
        -1,
    )
    command.state.history.index = index
    command.state.history.draft = draft
    set_current_input(command, edit, text)


def history_next(command, edit) -> None:
    current_text = get_current_input(command)
    index, draft, text = navigate_history(
        command.state.history.entries,
        command.state.history.index,
        command.state.history.draft,
        current_text,
        1,
    )
    command.state.history.index = index
    command.state.history.draft = draft
    set_current_input(command, edit, text)
