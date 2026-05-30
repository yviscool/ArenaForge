from __future__ import annotations

from sublime import Region

from ..messages import product_log_message
from .process_actions import schedule_test_manager_action, terminate_command_tester


def get_begin_region(command, test_id):
    return command.view.get_regions(command.REGION_BEGIN_KEY % test_id)


def enable_edit_mode(command) -> None:
    view = command.view
    if command.state.tester.proc_run:
        terminate_command_tester(
            command,
            on_failure=lambda: product_log_message("error.process_termination_failed"),
        )
        schedule_test_manager_action(view, "enable_edit_mode", delay=500)
        return

    if view.settings().get("edit_mode"):
        return
    view.settings().set("edit_mode", True)

    tests = command.state.tester.test_iter
    for index in range(tests):
        out_begin = view.get_regions(command.REGION_END_KEY % index)[0].begin()
        if index == tests - 1:
            out_end = view.size()
        else:
            out_end = view.get_regions(command.REGION_BEGIN_KEY % (index + 1))[0].begin()
        view.erase_regions(command.REGION_END_KEY % index)
        view.erase_regions("line_%d" % index)
        view.erase_regions("test_error_%d" % index)
        view.run_command("test_manager", {"action": "erase", "region": (out_begin, out_end)})
    command.sync_read_only()


def apply_edit_changes(command) -> None:
    view = command.view
    tests = []
    index = 0
    while get_begin_region(command, index):
        start = get_begin_region(command, index)[0].begin()
        if not get_begin_region(command, index + 1):
            end = view.size()
        else:
            end = get_begin_region(command, index + 1)[0].begin()
        tests.append(view.substr(Region(start, end)).strip() + "\n")
        index += 1
    command.state.tester.set_tests(tests)
    command.memorize_tests()


def toggle_new_test(command) -> None:
    view = command.view
    places = []
    index = 0
    while get_begin_region(command, index):
        places.append(get_begin_region(command, index)[0].begin())
        index += 1
    current = view.line(view.sel()[0].begin()).begin()
    if current in places:
        places.remove(current)
        view.erase_regions(command.REGION_BEGIN_KEY % len(places))
    else:
        places.append(current)
        places.sort()

    for index, place in enumerate(places):
        view.erase_regions(command.REGION_BEGIN_KEY % index)
        view.add_regions(
            command.REGION_BEGIN_KEY % index,
            [Region(place, place)],
            *command.REGION_BEGIN_PROP,
        )
