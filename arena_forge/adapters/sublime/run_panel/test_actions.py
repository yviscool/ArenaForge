from __future__ import annotations

from sublime import Region

from .operations import delete_selected_tests, swap_selected_tests, toggle_test_fold
from .process_actions import terminate_tester_with_logging


def toggle_fold(command, test_id) -> None:
    toggle_test_fold(command, test_id)


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
            "test": tester.tests[test_id].test_string,
            "source_view_id": view.id(),
        },
    )


def handle_test_event(command, test_id, event: str) -> None:
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
        command.prepare_code_view()
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
    command.memorize_tests()


def set_test_input(command, *, test=None, test_id=None) -> None:
    tester = command.state.tester
    unfolded = False
    if not tester.tests[test_id].fold:
        toggle_fold(command, test_id)
        unfolded = True
    tester.tests[test_id].test_string = test
    if unfolded:
        toggle_fold(command, test_id)
    command.memorize_tests()


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
        begin = view.get_regions(command.REGION_BEGIN_KEY % index)[0].begin()
        end = view.line(view.get_regions(command.REGION_END_KEY % index)[0].begin()).end()
        region = Region(begin, end)
        for selection in view.sel():
            if selection.intersects(region):
                set_test_status(command, index, accept=accept)
    command.memorize_tests()


def fold_accept_tests(command) -> None:
    view = command.view
    for index in range(command.state.tester.test_iter):
        if command.state.tester.check_test(index):
            begin = view.get_regions(command.REGION_BEGIN_KEY % index)[0].begin()
            end = view.line(view.get_regions(command.REGION_END_KEY % index)[0].begin()).end()
            view.fold(Region(view.word(begin + 5).end(), end))


def delete_nth_test(command, edit, nth, fixed_end=None) -> None:
    view = command.view
    begin = view.get_regions(command.REGION_BEGIN_KEY % nth)[0].begin()
    if fixed_end is not None:
        end = fixed_end
    elif command.get_begin_region(nth + 1):
        end = command.get_begin_region(nth + 1)[0].begin()
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
    command.memorize_tests()
    command.update_configs()


def delete_tests(command, edit) -> None:
    delete_selected_tests(command, edit)


def swap_tests(command, edit, direction=-1) -> None:
    swap_selected_tests(command, edit, direction=direction)


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
    command.clear_all()
    command.state.reset_panel_runtime()
    command.memorize_tests()
    command.view.run_command("test_manager", {"action": "new_test"})
