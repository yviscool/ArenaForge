from __future__ import annotations

from sublime import PhantomSet, Region

from .run_panel_logic import build_panel_render_entries
from .run_panel_rendering import build_next_test_title_phantom

_UNKNOWN_PHANTOM_SIGNATURE = object()


def _ensure_test_phantom_capacity(command, count: int) -> None:
    view = command.view
    while len(command.state.test_phantoms) < count:
        command.state.test_phantoms.append(
            PhantomSet(view, "test-phantom-" + str(len(command.state.test_phantoms)))
        )


def _get_test_phantom_signatures(state):
    signatures = getattr(state, "_test_phantom_signatures", None)
    if signatures is None:
        signatures = [_UNKNOWN_PHANTOM_SIGNATURE] * len(state.test_phantoms)
        setattr(state, "_test_phantom_signatures", signatures)
    elif len(signatures) < len(state.test_phantoms):
        signatures.extend([_UNKNOWN_PHANTOM_SIGNATURE] * (len(state.test_phantoms) - len(signatures)))
    return signatures


def _config_signature(theme_name, entry, test_state, output_text):
    return (
        "config",
        theme_name,
        entry.test_id,
        entry.config_point,
        entry.running,
        getattr(test_state, "fold", True),
        getattr(test_state, "runtime", "-"),
        str(getattr(test_state, "rtcode", 0)),
        getattr(test_state, "last_evaluation", None),
        getattr(test_state, "display_body_text", None),
        getattr(test_state, "output_start_offset", None),
        output_text,
    )


def _accdec_signature(theme_name, entry, test_state):
    return (
        "accdec",
        theme_name,
        entry.test_id,
        entry.accdec_point,
        entry.accdec_action,
        getattr(test_state, "runtime", "-"),
    )


def _build_test_phantom_descriptors(command, theme_name):
    tester = command.state.tester
    descriptors = []
    for entry in build_panel_render_entries(
        tester.tests,
        tester.prog_out,
        proc_run=tester.proc_run,
        running_test=tester.running_test,
        test_iter=tester.test_iter,
    ):
        test_state = tester.tests[entry.test_id]
        output_text = tester.prog_out[entry.test_id]
        descriptors.append(
            (
                _config_signature(theme_name, entry, test_state, output_text),
                lambda test_state=test_state, entry=entry, output_text=output_text: test_state.get_config(
                    entry.test_id,
                    entry.config_point,
                    command.on_test_action,
                    output_text,
                    command.view,
                    running=entry.running,
                ),
            )
        )

        if entry.accdec_action is not None and entry.accdec_point is not None:
            descriptors.append(
                (
                    _accdec_signature(theme_name, entry, test_state),
                    lambda test_state=test_state, entry=entry: test_state.get_accdec(
                        entry.test_id,
                        entry.accdec_point,
                        command.on_accdec_action,
                        entry.accdec_action,
                        command.view,
                    ),
                )
            )

    if not tester.proc_run:
        descriptors.append(
            (
                ("next-test", theme_name, max(command.view.size() - 1, 0)),
                lambda: build_next_test_title_phantom(
                    command.view,
                    lambda event, view=command.view: view.run_command("test_manager", {"action": "new_test"}),
                ),
            )
        )
    return descriptors


def update_configs(command, update_last=None) -> None:
    view = command.view
    hide_phantoms = bool(view.settings().get("hide_phantoms"))
    theme_name = view.settings().get("theme")
    descriptors = _build_test_phantom_descriptors(command, theme_name)

    _ensure_test_phantom_capacity(command, len(descriptors))
    signatures = _get_test_phantom_signatures(command.state)
    for index, (signature, factory) in enumerate(descriptors):
        target_signature = ("hidden",) if hide_phantoms else signature
        if signatures[index] == target_signature:
            continue
        command.state.test_phantoms[index].update([] if hide_phantoms else [factory()])
        signatures[index] = target_signature

    for index in range(len(descriptors), len(command.state.test_phantoms)):
        if signatures[index] is None:
            continue
        command.state.test_phantoms[index].update([])
        signatures[index] = None


def start_new_test(command, edit) -> None:
    view = command.view
    command.state.begin_panel_input(view.size())

    view.add_regions("type", [Region(view.size(), view.size())], *command.REGION_BEGIN_PROP)
    view.sel().clear()
    view.sel().add(Region(view.size()))
    command.state.tester.next_test(view.size() - 1, lambda: update_configs(command, update_last=True))
