from __future__ import annotations

from os import path

import sublime
from sublime import Region

from arena_forge.core.domain import Verdict

from .messages import product_log_message, translate
from .root_bridge import get_debugger_info_module
from .run_panel_logic import (
    history_verdict_from_result,
    normalize_finished_output,
    should_clear_finished_input,
    should_queue_follow_up_test,
)
from .run_panel_regions import clear_panel_view
from .run_panel_session_service import create_process_manager, load_tests_for_run
from .run_panel_state import append_run_history
from .settings_bridge import get_session_repository, get_settings, get_tests_file_path


def handle_process_stop(command, rtcode, runtime, crash_line=None) -> None:
    view = command.view
    tester = command.state.tester

    test_id = tester.running_test
    input_text = tester.tests[test_id].test_string
    output_text = normalize_finished_output(tester.prog_out[test_id], tester.running_new)
    evaluation = None
    if str(rtcode) == "0":
        evaluation = tester.evaluate_test(test_id)
        tester.tests[test_id].set_last_evaluation(evaluation)
    else:
        tester.tests[test_id].set_last_evaluation(None)
    verdict = evaluation.verdict if evaluation is not None else Verdict.RUNTIME_ERROR

    tester.tests[test_id].set_cur_runtime(runtime)
    tester.tests[test_id].set_cur_rtcode(rtcode)

    view.erase_regions("type")
    line = view.line(command.state.input_start)
    input_end = view.line(Region(command.state.delta_input)).end()

    if should_clear_finished_input(tester.running_new, verdict):
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
                "text": input_text + "\n" + output_text,
            },
        )
        tester.tests[test_id].fold = False
        view.add_regions(
            command.REGION_BEGIN_KEY % test_id,
            [Region(line.begin(), line.end())],
            *command.REGION_BEGIN_PROP,
        )

    view.show(command.state.input_start + 20)
    string_rtcode = str(rtcode)
    view.add_regions(
        "test_end_%d" % test_id,
        [Region(command.state.input_start + len(input_text) + 1, command.state.input_start + len(input_text) + 1)],
        *command.REGION_END_PROP,
    )
    view.run_command("test_manager", {"action": "set_cursor_to_end"})

    command.memorize_tests()
    append_run_history(
        get_session_repository(),
        command.state.dbg_file,
        "Test %d" % (test_id + 1),
        output_text,
        history_verdict_from_result(verdict),
        runtime,
        int(string_rtcode) if string_rtcode.lstrip("-").isdigit() else -1,
        evaluation=evaluation,
    )
    if should_queue_follow_up_test(
        string_rtcode,
        verdict=verdict,
        running_new=tester.running_new,
        have_pretests=tester.have_pretests(),
    ):
        command.update_configs(update_last=True)
        sublime.set_timeout(lambda: view.run_command("test_manager", {"action": "new_test"}), 10)
    else:
        sublime.set_timeout(command.update_configs, 100)

    if crash_line is not None:
        for subview in view.window().views():
            if subview.id() == command.state.code_view_id:
                subview.run_command("view_tester", {"action": "show_crash_line", "crash_line": crash_line})


def clear_all(command) -> None:
    clear_panel_view(
        command.view,
        command.state.tester,
        command.REGION_BEGIN_KEY,
        command.REGION_END_KEY,
        [command.state.phantoms, *command.state.test_phantoms],
    )


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
    command.state.use_debugger = use_debugger
    view = command.view

    if view.get_status("process_status_code") == "COMPILING":
        return

    if view.get_status("process_status_code") == "RUNNING":
        command.state.tester.terminate()
        kwargs = {
            "run_file": run_file,
            "build_sys": build_sys,
            "clr_tests": clr_tests,
            "sync_out": sync_out,
            "code_view_id": code_view_id,
            "use_debugger": use_debugger,
            "load_session": load_session,
            "action": "make_opd",
        }
        sublime.set_timeout_async(lambda kwargs=kwargs: view.run_command("test_manager", kwargs), 30)
        return

    if view.settings().get("edit_mode"):
        command.apply_edit_changes()

    view.set_scratch(True)
    view.run_command("set_setting", {"setting": "fold_buttons", "value": False})
    view.run_command("set_setting", {"setting": "line_numbers", "value": False})
    view.set_status("opd_info", "opdebugger-file")
    clear_all(command)
    if load_session:
        if command.state.session is None:
            view.run_command(
                "test_manager",
                {"action": "insert_opd_out", "text": translate("error.session_restore_failed")},
            )
        else:
            run_file = command.state.session["run_file"]
            build_sys = command.state.session["build_sys"]
            clr_tests = command.state.session["clr_tests"]
            sync_out = command.state.session["sync_out"]
            code_view_id = command.state.session["code_view_id"]
            use_debugger = command.state.session["use_debugger"]
    else:
        product_log_message("status.session_saved")
        command.state.session = {
            "run_file": run_file,
            "build_sys": build_sys,
            "clr_tests": clr_tests,
            "sync_out": sync_out,
            "code_view_id": code_view_id,
            "use_debugger": use_debugger,
        }
        command.state.dbg_file = run_file
        command.state.code_view_id = code_view_id

    command.prepare_code_view()

    if not view.settings().get("word_wrap"):
        view.run_command("toggle_setting", {"setting": "word_wrap"})

    if not clr_tests:
        tests = load_tests_for_run(run_file, command.Test, get_session_repository(), get_tests_file_path)
    else:
        with open(get_tests_file_path(run_file, for_write=True), "w") as handle:
            handle.write("[]")
        tests = []
    file_ext = path.splitext(run_file)[1][1:]

    command.change_process_status("COMPILING")

    debugger_info = get_debugger_info_module()
    debug_module = debugger_info.get_best_debug_module(file_ext)
    if (not command.state.use_debugger) or (debug_module is None):
        process_manager = create_process_manager(run_file, build_sys, get_settings().get("run_settings"))
    else:
        process_manager = debug_module(run_file)

    def compile_step(command=command, view=view):
        compile_result = process_manager.compile()
        command.change_process_status("COMPILED")
        command.state.delta_input = 0
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
            )
            view.settings().set("edit_mode", False)
            view.run_command("test_manager", {"action": "new_test"})
        else:
            view.run_command("test_manager", {"action": "insert_opd_out", "text": "\n" + compile_result[1]})
            command.set_compile_bar("compilation error", type="error")

    command.set_compile_bar("compiling")
    sublime.set_timeout_async(compile_step, 10)
