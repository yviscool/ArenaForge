from __future__ import annotations

from sublime import Region

from .messages import status_message


def toggle_test_fold(command, test_id):
    view = command.view
    tester = command.state.tester
    input_text = tester.tests[test_id].test_string
    output_text = tester.prog_out[test_id]
    text = input_text + "\n" + output_text.rstrip() + "\n\n"
    tie_pos = command.get_tie_pos(test_id)

    if tester.tests[test_id].fold:
        view.run_command("test_manager", {"action": "replace", "region": (tie_pos + 1, tie_pos + 1), "text": text})
        view.add_regions(command.REGION_BEGIN_KEY % test_id, [Region(tie_pos + 1)], *command.REGION_BEGIN_PROP)
        view.add_regions(
            "test_end_%d" % test_id,
            [Region(tie_pos + len(input_text) + 2, tie_pos + len(input_text) + 2)],
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


def delete_selected_tests(command, edit):
    view = command.view
    tester = command.state.tester

    if tester.proc_run:
        status_message("status.stop_process_before_delete")
        return

    k = tester.test_iter + 1 if tester.proc_run else tester.test_iter
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
        command.delete_test(edit, test)
    command.memorize_tests()


def swap_selected_tests(command, edit, direction=-1):
    tester = command.state.tester
    view = command.view
    selected = []

    for i in range(len(tester.tests)):
        begin = command.get_tie_pos(i)
        end = command.get_tie_pos(i + 1)
        tester.tests[i].__sel = []

        for reg in view.sel():
            if reg.intersects(Region(begin, end)):
                selected.append(i)
                inter = reg.intersection(Region(begin, end))
                tester.tests[i].__sel.append(Region(inter.a - begin, inter.b - begin))
                break

    for i in range(len(tester.tests)):
        if not tester.tests[i].fold:
            tester.tests[i].__unfold = True
            command.toggle_fold(i)
        else:
            tester.tests[i].__unfold = False

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
        if tester.tests[i].__unfold:
            command.toggle_fold(i)
    view.sel().clear()
    for i in range(len(tester.tests)):
        for reg in tester.tests[i].__sel:
            begin = command.get_tie_pos(i)
            view.sel().add(Region(begin + reg.a, begin + reg.b))
