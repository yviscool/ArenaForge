from __future__ import annotations

from os import path

import sublime
from sublime import Region

from arena_forge.core.domain import OutputEvaluation, Verdict

from ..messages import product_log_message, translate
from ..root_bridge import get_debugger_info_module
from ..settings_bridge import get_session_repository, get_settings, get_tests_file_path
from .launch_flow import RunPanelLaunchRequest, plan_run_panel_launch
from .logic import (
    build_run_panel_stop_plan,
)
from .process_actions import schedule_test_manager_command, terminate_command_tester
from .regions import clear_panel_view
from .session_service import create_run_backend, prepare_tests_for_run, select_run_backend
from .state import append_run_history


def resolve_stop_evaluation(tester, test_id, rtcode, *, compile_failed=False):
    if compile_failed:
        return OutputEvaluation(checker_name="normalized_text", verdict=Verdict.COMPILE_ERROR)
    if str(rtcode) == "0":
        return tester.evaluate_test(test_id)
    return None


def handle_process_stop(command, rtcode, runtime, crash_line=None, compile_failed=False) -> None:
    view = command.view
    tester = command.state.tester

    test_id = tester.running_test
    input_text = tester.tests[test_id].test_string
    evaluation = resolve_stop_evaluation(tester, test_id, rtcode, compile_failed=compile_failed)
    stop_plan = build_run_panel_stop_plan(
        return_code=rtcode,
        input_text=input_text,
        output_text=tester.prog_out[test_id],
        running_new=tester.running_new,
        have_pretests=tester.have_pretests(),
        evaluation=evaluation,
    )
    tester.tests[test_id].set_last_evaluation(stop_plan.evaluation)
    tester.tests[test_id].set_display_layout(
        None if stop_plan.clear_input else stop_plan.rendered_text,
        None if stop_plan.clear_input else stop_plan.output_start_offset,
    )

    tester.tests[test_id].set_cur_runtime(runtime)
    tester.tests[test_id].set_cur_rtcode(rtcode)

    view.erase_regions("type")
    line = view.line(command.state.input_start)
    input_end = view.line(Region(command.state.delta_input)).end()

    if stop_plan.clear_input:
        view.run_command(
            "test_manager",
            {"action": "replace", "region": (command.state.input_start, input_end), "text": ""},
        )
    else:
        view.run_command(
            "test_manager",
            {
                "action": "replace",
                "region": (command.state.input_start, input_end),
                "text": stop_plan.rendered_text,
            },
        )
        tester.tests[test_id].fold = False
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

    command.memorize_tests()
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
                subview.run_command("view_tester", {"action": "show_crash_line", "crash_line": crash_line})


def handle_compile_failure(command, rtcode) -> None:
    command.change_process_status("STOPPED")
    handle_process_stop(command, rtcode, 0, compile_failed=True)
    command.set_compile_bar("compilation error", type="error")


def clear_all(command) -> None:
    clear_panel_view(
        command.view,
        command.state.tester,
        command.REGION_BEGIN_KEY,
        command.REGION_END_KEY,
        [command.state.phantoms, *command.state.test_phantoms],
    )


def _schedule_rerun(view, command, request, launch_plan) -> None:
    terminate_command_tester(
        command,
        on_failure=lambda: product_log_message("error.process_termination_failed"),
    )
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
    backend = select_run_backend(use_debugger=command.state.use_debugger, debug_module=debug_module)
    process_manager = create_run_backend(
        backend,
        run_file=launch_session.run_file,
        build_sys=launch_session.build_sys,
        run_settings=get_settings().get("run_settings"),
    )
    return tests, process_manager, launch_session.sync_out


def _schedule_compile_start(command, view, process_manager, tests, sync_out) -> None:
    def compile_step(command=command, view=view):
        compile_result = process_manager.compile()
        command.change_process_status("COMPILED")
        command.state.advance_panel_input(0)
        if compile_result is None or compile_result[0] == 0:
            command.state.tester = command.Tester(
                process_manager,
                command.on_insert,
                command.on_out,
                command.on_stop,
                command.change_process_status,
                tests=tests,
                sync_out=sync_out,
                test_factory=command.Test,
                on_compile_error=lambda test_id, rtcode, output_text: handle_compile_failure(command, rtcode),
            )
            view.settings().set("edit_mode", False)
            view.run_command("test_manager", {"action": "new_test"})
        else:
            view.run_command("test_manager", {"action": "insert_opd_out", "text": "\n" + compile_result[1]})
            command.set_compile_bar("compilation error", type="error")

    command.set_compile_bar("compiling")
    sublime.set_timeout_async(compile_step, 10)


def make_opd(
    command,
    edit,
    *,
    run_file=None,
    build_sys=None,
    clr_tests=False,
    sync_out=False,
    code_view_id=None,
    use_debugger=False,
    load_session=False,
) -> None:
    view = command.view
    request = RunPanelLaunchRequest(
        run_file=run_file,
        build_sys=build_sys,
        clr_tests=clr_tests,
        sync_out=sync_out,
        code_view_id=code_view_id,
        use_debugger=use_debugger,
        load_session=load_session,
    )
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
        command.apply_edit_changes()

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
        command.set_compile_bar("session restore failed", type="error")
        return

    launch_session = launch_plan.session
    if launch_session is None:
        raise RuntimeError("Run-panel launch plan did not provide a launch session")

    command.state.set_launch_session(launch_session)
    if not request.load_session:
        product_log_message("status.session_saved")

    command.prepare_code_view()

    if not view.settings().get("word_wrap"):
        view.run_command("toggle_setting", {"setting": "word_wrap"})

    command.change_process_status("COMPILING")
    tests, process_manager, sync_out = _build_run_backend_state(command, launch_session)
    _schedule_compile_start(command, view, process_manager, tests, sync_out)
