from __future__ import annotations

from sublime import Region

from ..shared.messages import status_message
from .edit_actions import get_begin_region
from .logic import resolve_visible_body_text
from .process_actions import terminate_tester_with_logging
from .session_actions import clear_all, memorize_tests


def _get_test_range(view, command, test_id):
    begin = view.get_regions(command.REGION_BEGIN_KEY % test_id)[0].begin()
    end = view.line(view.get_regions(command.REGION_END_KEY % test_id)[0].begin()).end()
    return begin, end


def toggle_fold(command, test_id) -> None:
    view = command.view
    tester = command.state.tester
    text = resolve_visible_body_text(tester.tests[test_id], tester.prog_out[test_id])
    output_start_offset = getattr(tester.tests[test_id], "output_start_offset", None)
    if output_start_offset is None:
        input_text = tester.tests[test_id].input_text
        separator = "" if not input_text or input_text.endswith("\n") else "\n"
        output_start_offset = len(input_text + separator)
    tie_pos = command.get_tie_pos(test_id)

    if tester.tests[test_id].fold:
        view.run_command("test_manager", {"action": "replace", "region": (tie_pos + 1, tie_pos + 1), "text": text})
        view.add_regions(command.REGION_BEGIN_KEY % test_id, [Region(tie_pos + 1)], *command.REGION_BEGIN_PROP)
        view.add_regions(
            "test_end_%d" % test_id,
            [Region(tie_pos + 1 + output_start_offset, tie_pos + 1 + output_start_offset)],
            *command.REGION_END_PROP,
        )
        delta = len(text)
        for index in range(test_id + 1, command.state.tester.test_iter):
            command.state.tester.tests[index].tie_pos += delta
        tester.tests[test_id].fold = False
    else:
        view.run_command(
            "test_manager",
            {"action": "replace", "region": (tie_pos + 1, tie_pos + 1 + len(text)), "text": ""},
        )
        view.erase_regions(command.REGION_BEGIN_KEY % test_id)
        view.erase_regions("test_end_%d" % test_id)
        delta = len(text)
        for index in range(test_id + 1, tester.test_iter):
            tester.tests[index].tie_pos -= delta
        tester.tests[test_id].fold = True

    view.sel().clear()
    view.sel().add(Region(view.size()))
    command.update_configs()


def open_test_edit(command, test_id) -> None:
    view = command.view
    tester = command.state.tester
    view.window().focus_group(1)
    edit_view = view.window().new_file()
    view.window().set_view_index(edit_view, 1, 1)
    edit_view.run_command(
        "test_edit",
        {
            "action": "init",
            "test_id": test_id,
            "test": tester.tests[test_id].input_text,
            "source_view_id": view.id(),
        },
    )


def handle_test_event(command, test_id, event: str) -> None:
    from .debug_actions import prepare_code_view

    view = command.view
    tester = command.state.tester
    if event == "test-click":
        toggle_fold(command, test_id)
    elif event == "test-edit":
        open_test_edit(command, test_id)
    elif event == "test-stop":
        terminate_tester_with_logging(tester)
    elif event == "test-run":
        if not tester.tests[test_id].fold:
            toggle_fold(command, test_id)
        tie_pos = command.get_tie_pos(test_id)
        view.run_command("test_manager", {"action": "replace", "region": (tie_pos, tie_pos), "text": "\n\n"})
        view.add_regions("type", [Region(tie_pos + 1)], *command.REGION_BEGIN_PROP)
        command.state.input_start = tie_pos + 1
        command.state.delta_input = tie_pos + 1
        view.sel().clear()
        view.sel().add(Region(tie_pos + 1))
        prepare_code_view(command)
        tester.run_test(test_id)
        command.update_configs()


def handle_accdec_event(command, test_id, event: str) -> None:
    tester = command.state.tester
    if event == "click-accept":
        tester.accept_out(test_id)
    elif event == "click-decline":
        tester.decline_out(test_id)
    tester.tests[test_id].set_last_evaluation(tester.evaluate_test(test_id))
    command.update_configs()
    memorize_tests(command)


def set_test_input(command, *, test=None, test_id=None) -> None:
    tester = command.state.tester
    unfolded = False
    if not tester.tests[test_id].fold:
        toggle_fold(command, test_id)
        unfolded = True
    tester.tests[test_id].input_text = test
    if unfolded:
        toggle_fold(command, test_id)
    memorize_tests(command)


def set_test_status(command, test_id, accept=True, call_tester=True) -> None:
    view = command.view
    begin_key = command.REGION_BEGIN_KEY % test_id
    region = view.get_regions(begin_key)[0]
    view.erase_regions(begin_key)
    if accept:
        prop = command.REGION_ACCEPT_PROP
        if call_tester:
            command.state.tester.accept_out(test_id)
    elif accept is False:
        prop = command.REGION_DECLINE_PROP
        if call_tester:
            command.state.tester.decline_out(test_id)
    else:
        prop = command.REGION_UNKNOWN_PROP
    view.add_regions(begin_key, [region], *prop)
    if call_tester:
        command.state.tester.tests[test_id].set_last_evaluation(command.state.tester.evaluate_test(test_id))


def set_tests_status(command, accept=True) -> None:
    view = command.view
    for index in range(command.state.tester.test_iter):
        begin, end = _get_test_range(view, command, index)
        region = Region(begin, end)
        for selection in view.sel():
            if selection.intersects(region):
                set_test_status(command, index, accept=accept)
    memorize_tests(command)


def fold_accept_tests(command) -> None:
    view = command.view
    for index in range(command.state.tester.test_iter):
        if command.state.tester.check_test(index):
            begin, end = _get_test_range(view, command, index)
            view.fold(Region(view.word(begin + 5).end(), end))


def delete_nth_test(command, edit, nth, fixed_end=None) -> None:
    view = command.view
    begin = view.get_regions(command.REGION_BEGIN_KEY % nth)[0].begin()
    if fixed_end is not None:
        end = fixed_end
    elif get_begin_region(command, nth + 1):
        end = get_begin_region(command, nth + 1)[0].begin()
    else:
        end = view.size()
    view.replace(edit, Region(begin, end), "")
    view.erase_regions(command.REGION_BEGIN_KEY % nth)
    view.erase_regions(command.REGION_END_KEY % nth)
    view.erase_regions("line_%d" % nth)


def delete_test(command, edit, test_id) -> None:
    view = command.view
    tester = command.state.tester
    if not tester.tests[test_id].fold:
        toggle_fold(command, test_id)

    total = tester.test_iter + (1 if tester.proc_run else 0)
    current = 0
    for index in range(total):
        if not tester.tests[index].fold:
            begin_region = view.get_regions(command.REGION_BEGIN_KEY % index)
            end_region = view.get_regions("test_end_%d" % index)
            view.erase_regions(command.REGION_BEGIN_KEY % index)
            view.erase_regions("test_end_%d" % index)
            view.add_regions(command.REGION_BEGIN_KEY % current, begin_region, *command.REGION_BEGIN_PROP)
            view.add_regions("test_end_%d" % current, end_region, *command.REGION_END_PROP)
        if index != test_id:
            current += 1

    del tester.tests[test_id]
    del tester.prog_out[test_id]
    tester.test_iter -= 1
    memorize_tests(command)
    command.update_configs()


def delete_tests(command, edit) -> None:
    view = command.view
    tester = command.state.tester

    if tester.proc_run:
        status_message("status.stop_process_before_delete")
        return

    k = tester.test_iter
    to_delete = []
    for i in range(k):
        begin = command.get_tie_pos(i)
        end = view.size() if i == k - 1 else command.get_tie_pos(i + 1)
        region = Region(begin, end)
        for selection in view.sel():
            if selection.intersects(region):
                to_delete.append(i)

    status_message("status.tests_deleted", tests=", ".join(str(x + 1) for x in to_delete))
    for test in reversed(to_delete):
        delete_test(command, edit, test)
    memorize_tests(command)


def swap_tests(command, edit, direction=-1) -> None:
    tester = command.state.tester
    view = command.view
    selected = []
    selections_by_test = {}
    fold_states = {}

    for i in range(len(tester.tests)):
        begin = command.get_tie_pos(i)
        end = command.get_tie_pos(i + 1)
        selections_by_test[i] = []

        for reg in view.sel():
            if reg.intersects(Region(begin, end)):
                selected.append(i)
                inter = reg.intersection(Region(begin, end))
                selections_by_test[i].append(Region(inter.a - begin, inter.b - begin))
                break

    for i in range(len(tester.tests)):
        if not tester.tests[i].fold:
            fold_states[i] = True
            toggle_fold(command, i)
        else:
            fold_states[i] = False

    if direction == 1:
        selected.reverse()
    for sel in selected:
        if 0 <= sel + direction < len(tester.tests):
            tester.tests[sel], tester.tests[sel + direction] = tester.tests[sel + direction], tester.tests[sel]
            tester.prog_out[sel], tester.prog_out[sel + direction] = (
                tester.prog_out[sel + direction],
                tester.prog_out[sel],
            )

    for i in range(len(tester.tests)):
        if fold_states.get(i):
            toggle_fold(command, i)
    view.sel().clear()
    for i in range(len(tester.tests)):
        for reg in selections_by_test.get(i, []):
            begin = command.get_tie_pos(i)
            view.sel().add(Region(begin + reg.a, begin + reg.b))


def toggle_hide_phantoms(command) -> None:
    view = command.view
    view.settings().set("hide_phantoms", not view.settings().get("hide_phantoms"))
    command.update_configs()


def clear_all_tests(command) -> None:
    tester = command.state.tester
    if tester is None:
        return
    if tester.proc_run:
        terminate_tester_with_logging(tester)
    tester.tests = []
    tester.prog_out = []
    tester.test_iter = 0
    tester.running_test = None
    tester.running_new = None
    clear_all(command)
    command.state.reset_panel_runtime()
    memorize_tests(command)
    command.view.run_command("test_manager", {"action": "new_test"})
