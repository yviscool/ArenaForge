from __future__ import annotations

from os import path

import sublime
from sublime import Region

from arena_forge.core.domain import OutputEvaluation, Verdict

from ..root_bridge import get_debugger_info_module
from ..shared.messages import product_log_message, translate, translate_status_code
from ..shared.settings_bridge import get_session_repository, get_settings, get_tests_file_path
from .launch_flow import plan_run_panel_launch
from .logic import (
    build_run_panel_stop_plan,
)
from .persistence import append_run_history
from .process_actions import (
    schedule_test_manager_command,
    terminate_command_tester_with_logging,
)
from .regions import clear_panel_view
from .session_service import create_run_backend, prepare_tests_for_run, save_tests_for_run


def resolve_stop_evaluation(tester, test_id, rtcode, *, compile_failed=False):
    if compile_failed:
        return OutputEvaluation(checker_name="normalized_text", verdict=Verdict.COMPILE_ERROR)
    if str(rtcode) == "0":
        return tester.evaluate_test(test_id)
    return None


def _change_process_status(command, status: str) -> None:
    callback = getattr(command, "change_process_status", None)
    if callback is not None:
        callback(status)
        return
    command.view.set_status("process_status_code", status)
    command.view.set_status("process_status", translate_status_code(status))


def _set_compile_bar(command, cmd: str, type: str = "") -> None:
    callback = getattr(command, "set_compile_bar", None)
    if callback is not None:
        callback(cmd, type=type)
        return
    from .rendering import build_compile_bar_phantom

    command.state.test_phantoms[0].update([build_compile_bar_phantom(command.view, cmd, type=type)])


def memorize_tests(command) -> None:
    callback = getattr(command, "memorize_tests", None)
    if callback is not None:
        callback()
        return
    from ..shared.settings_bridge import get_session_repository, get_tests_file_path, infer_language_name

    save_tests_for_run(
        command.state.source_file,
        command.state.tester.get_tests(),
        get_session_repository(),
        infer_language_name,
        get_tests_file_path,
    )


def _prepare_code_view(command) -> None:
    callback = getattr(command, "prepare_code_view", None)
    if callback is not None:
        callback()
        return
    from .debug_actions import prepare_code_view

    prepare_code_view(command)


def _update_test_from_stop_plan(tester, test_id, stop_plan, runtime, rtcode):
    tester.tests[test_id].set_last_evaluation(stop_plan.evaluation)
    tester.tests[test_id].set_display_layout(
        None if stop_plan.clear_input else stop_plan.rendered_text,
        None if stop_plan.clear_input else stop_plan.output_start_offset,
    )
    tester.tests[test_id].set_cur_runtime(runtime)
    tester.tests[test_id].set_cur_rtcode(rtcode)


def _render_stop_regions(view, command, test_id, stop_plan):
    view.erase_regions("type")
    line = view.line(command.state.input_start)
    input_end = view.line(Region(command.state.delta_input)).end()

    replacement_text = "" if stop_plan.clear_input else stop_plan.rendered_text
    view.run_command(
        "test_manager",
        {"action": "replace", "region": (command.state.input_start, input_end), "text": replacement_text},
    )

    if not stop_plan.clear_input:
        command.state.tester.tests[test_id].fold = False
        view.add_regions(
            command.REGION_BEGIN_KEY % test_id,
            [Region(line.begin(), line.end())],
            *command.REGION_BEGIN_PROP,
        )

    view.show(command.state.input_start + 20)
    view.add_regions(
        "test_end_%d" % test_id,
        [Region(line.begin() + stop_plan.output_start_offset, line.begin() + stop_plan.output_start_offset)],
        *command.REGION_END_PROP,
    )
    view.run_command("test_manager", {"action": "set_cursor_to_end"})


def handle_process_stop(command, rtcode, runtime, crash_line=None, compile_failed=False) -> None:
    view = command.view
    tester = command.state.tester

    test_id = tester.running_test
    input_text = tester.tests[test_id].input_text
    evaluation = resolve_stop_evaluation(tester, test_id, rtcode, compile_failed=compile_failed)
    stop_plan = build_run_panel_stop_plan(
        return_code=rtcode,
        input_text=input_text,
        output_text=tester.prog_out[test_id],
        running_new=tester.running_new,
        have_pretests=tester.have_pretests(),
        evaluation=evaluation,
    )

    _update_test_from_stop_plan(tester, test_id, stop_plan, runtime, rtcode)
    _render_stop_regions(view, command, test_id, stop_plan)

    memorize_tests(command)
    append_run_history(
        get_session_repository(),
        command.state.source_file,
        "Test %d" % (test_id + 1),
        stop_plan.output_text,
        stop_plan.history_verdict,
        runtime,
        stop_plan.history_return_code,
        evaluation=stop_plan.evaluation,
    )
    if stop_plan.queue_follow_up:
        command.update_configs(update_last=True)
        sublime.set_timeout(lambda: view.run_command("test_manager", {"action": "new_test"}), 10)
    else:
        sublime.set_timeout(command.update_configs, 100)

    if crash_line is not None:
        for subview in view.window().views():
            if subview.id() == command.state.code_view_id:
                subview.run_command("debug_overlay", {"action": "show_crash_line", "crash_line": crash_line})


def handle_compile_failure(command, rtcode) -> None:
    _change_process_status(command, "STOPPED")
    handle_process_stop(command, rtcode, 0, compile_failed=True)
    _set_compile_bar(command, translate("error.compilation_error"), type="error")


def clear_all(command) -> None:
    clear_panel_view(
        command.view,
        command.state.tester,
        command.REGION_BEGIN_KEY,
        command.REGION_END_KEY,
        [command.state.phantoms, *command.state.test_phantoms],
    )


def _schedule_rerun(view, command, request, launch_plan) -> None:
    terminate_command_tester_with_logging(command)
    kwargs = launch_plan.command_args or request.to_command_args()
    schedule_test_manager_command(view, kwargs, delay=30)


def _build_run_backend_state(command, launch_session):
    tests = prepare_tests_for_run(
        launch_session.run_file,
        clr_tests=launch_session.clr_tests,
        test_factory=command.Test,
        repository=get_session_repository(),
        tests_file_path_factory=get_tests_file_path,
    )
    file_ext = path.splitext(launch_session.run_file)[1][1:]
    debugger_info = get_debugger_info_module()
    debug_module = debugger_info.get_best_debug_module(file_ext)
    process_manager = create_run_backend(
        use_debugger=command.state.use_debugger,
        debug_module=debug_module,
        run_file=launch_session.run_file,
        build_sys=launch_session.build_sys,
        run_settings=get_settings().get("run_settings"),
    )
    return tests, process_manager, launch_session.sync_out


def _schedule_compile_start(command, view, process_manager, tests, sync_out) -> None:
    def compile_step(command=command, view=view):
        compile_result = process_manager.compile()
        _change_process_status(command, "COMPILED")
        command.state.advance_panel_input(0)
        if compile_result is None or compile_result[0] == 0:
            command.state.tester = command.Tester(
                process_manager,
                command.on_insert,
                command.on_out,
                command.on_stop,
                lambda status: _change_process_status(command, status),
                tests=tests,
                sync_out=sync_out,
                test_factory=command.Test,
                on_compile_error=lambda test_id, rtcode, output_text: handle_compile_failure(command, rtcode),
            )
            view.settings().set("edit_mode", False)
            view.run_command("test_manager", {"action": "new_test"})
        else:
            view.run_command("test_manager", {"action": "insert_opd_out", "text": "\n" + compile_result[1]})
            _set_compile_bar(command, translate("error.compilation_error"), type="error")

    _set_compile_bar(command, translate("status.compiling"))
    sublime.set_timeout_async(compile_step, 10)


def make_opd(command, edit, *, request) -> None:
    view = command.view
    launch_plan = plan_run_panel_launch(
        status_code=view.get_status("process_status_code"),
        request=request,
        saved_session=command.state.launch_session,
    )

    if launch_plan.action == "noop":
        return

    if launch_plan.action == "rerun":
        _schedule_rerun(view, command, request, launch_plan)
        return

    if view.settings().get("edit_mode"):
        from .edit_actions import apply_edit_changes
        apply_edit_changes(command)

    view.set_scratch(True)
    view.run_command("set_setting", {"setting": "fold_buttons", "value": False})
    view.run_command("set_setting", {"setting": "line_numbers", "value": False})
    view.set_status("opd_info", "opdebugger-file")
    clear_all(command)
    if launch_plan.action == "error":
        view.run_command(
            "append",
            {
                "characters": translate(launch_plan.error_key or "error.session_restore_failed"),
                "force": True,
                "scroll_to_end": False,
            },
        )
        _set_compile_bar(command, translate("error.session_restore_failed"), type="error")
        return

    launch_session = launch_plan.session
    if launch_session is None:
        raise RuntimeError(translate("error.no_launch_session"))

    command.state.set_launch_session(launch_session)
    if not request.load_session:
        product_log_message("status.session_saved")

    _prepare_code_view(command)

    if not view.settings().get("word_wrap"):
        view.run_command("toggle_setting", {"setting": "word_wrap"})

    _change_process_status(command, "COMPILING")
    tests, process_manager, sync_out = _build_run_backend_state(command, launch_session)
    _schedule_compile_start(command, view, process_manager, tests, sync_out)
