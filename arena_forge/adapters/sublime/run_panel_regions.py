from __future__ import annotations

from sublime import Region


def compute_tie_pos(tester, index):
    point = 0
    for offset in range(index):
        running = tester.proc_run and offset == tester.running_test
        if running:
            point += len(tester.tests[offset].test_string) + len(tester.prog_out[offset]) + 1
        elif not tester.tests[offset].fold:
            point += len(tester.tests[offset].test_string) + len(tester.prog_out[offset]) + 1
        if not tester.tests[offset].fold:
            point += 2
    return point


def clear_panel_view(view, tester, region_begin_key, region_end_key, phantom_sets):
    view.run_command("test_manager", {"action": "erase_all"})
    view.sel().clear()
    view.sel().add(Region(view.size(), view.size()))
    for phantom_set in phantom_sets:
        phantom_set.update([])
    if tester:
        view.erase_regions("type")
        for index in range(-1, tester.test_iter + 1):
            view.erase_regions(region_begin_key % index)
            view.erase_regions(region_end_key % index)
            view.erase_regions("line_%d" % index)
            view.erase_regions("test_error_%d" % index)


def sync_read_only_mode(view, tester, delta_input):
    err = True
    if tester and tester.proc_run:
        err = False
        forb_before = delta_input
        forb_after = view.line(delta_input).b
        forbidden = [Region(0, forb_before), Region(forb_after, view.size() - 1)]

        for forbid in forbidden:
            for selection in view.sel():
                if forbid.intersects(selection):
                    err = True

        delete_forb = False
        for selection in view.sel():
            if selection.a == delta_input or selection.begin() == 0:
                delete_forb = True
                break
        view.settings().set("delete_forb", delete_forb)

    view.set_read_only(err)
