from __future__ import annotations

from sublime import PhantomSet, Region

from .run_panel_logic import build_panel_render_entries
from .run_panel_rendering import build_next_test_title_phantom


def update_configs(command, update_last=None) -> None:
    view = command.view
    tester = command.state.tester
    configs = []
    last_test_entry = -1
    for entry in build_panel_render_entries(
        tester.tests,
        tester.prog_out,
        proc_run=tester.proc_run,
        running_test=tester.running_test,
        test_iter=tester.test_iter,
    ):
        config = tester.tests[entry.test_id].get_config(
            entry.test_id,
            entry.config_point,
            command.on_test_action,
            tester.prog_out[entry.test_id],
            command.view,
            running=entry.running,
        )
        last_test_entry = len(configs)
        configs.append(config)

        if entry.accdec_action is not None and entry.accdec_point is not None:
            configs.append(
                tester.tests[entry.test_id].get_accdec(
                    entry.test_id,
                    entry.accdec_point,
                    command.on_accdec_action,
                    entry.accdec_action,
                    command.view,
                )
            )

    if not tester.proc_run:
        configs.append(
            build_next_test_title_phantom(
                command.view,
                lambda event, view=command.view: view.run_command("test_manager", {"action": "new_test"}),
            )
        )

    while len(command.state.test_phantoms) < len(configs):
        command.state.test_phantoms.append(
            PhantomSet(view, "test-phantom-" + str(len(command.state.test_phantoms)))
        )

    hide_phantoms = view.settings().get("hide_phantoms")
    if update_last:
        command.state.test_phantoms[last_test_entry].update(
            [configs[last_test_entry]] if not hide_phantoms else []
        )
        return

    for index, config in enumerate(configs):
        command.state.test_phantoms[index].update([config] if not hide_phantoms else [])

    for index in range(len(configs), len(command.state.test_phantoms)):
        command.state.test_phantoms[index].update([])


def start_new_test(command, edit) -> None:
    view = command.view
    command.state.begin_panel_input(view.size())

    view.add_regions("type", [Region(view.size(), view.size())], *command.REGION_BEGIN_PROP)
    view.sel().clear()
    view.sel().add(Region(view.size()))
    command.state.tester.next_test(view.size() - 1, lambda: update_configs(command, update_last=True))
