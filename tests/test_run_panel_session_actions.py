import importlib
import sys
import types
import unittest
from contextlib import contextmanager

from arena_forge.core.domain import Verdict


class _FakeRequest:
    def __init__(
        self,
        *,
        run_file=None,
        build_sys=None,
        clr_tests=False,
        sync_out=False,
        code_view_id=None,
        use_debugger=False,
        load_session=False,
    ):
        self.run_file = run_file
        self.build_sys = build_sys
        self.clr_tests = clr_tests
        self.sync_out = sync_out
        self.code_view_id = code_view_id
        self.use_debugger = use_debugger
        self.load_session = load_session

    def to_command_args(self):
        return {
            "action": "make_opd",
            "run_file": self.run_file,
            "build_sys": self.build_sys,
            "clr_tests": self.clr_tests,
            "sync_out": self.sync_out,
            "code_view_id": self.code_view_id,
            "use_debugger": self.use_debugger,
            "load_session": self.load_session,
        }


class _FakeSettings:
    def __init__(self, initial=None):
        self.values = dict(initial or {})

    def get(self, key, default=None):
        return self.values.get(key, default)

    def set(self, key, value):
        self.values[key] = value


class _FakeRegion:
    def __init__(self, a, b=None):
        self.a = a
        self.b = a if b is None else b

    def begin(self):
        return min(self.a, self.b)

    def end(self):
        return max(self.a, self.b)

    def __eq__(self, other):
        return isinstance(other, _FakeRegion) and (self.a, self.b) == (other.a, other.b)

    def __repr__(self):
        return f"_FakeRegion(a={self.a}, b={self.b})"


class _FakeView:
    def __init__(self, *, statuses=None, settings=None, text="", window_views=None):
        self._statuses = dict(statuses or {})
        self._settings = _FakeSettings(settings)
        self.text = text
        self.commands = []
        self.scratch_values = []
        self.erased_regions = []
        self.added_regions = []
        self.shown_points = []
        self._window = types.SimpleNamespace(views=lambda: list(window_views or []))

    def get_status(self, key):
        return self._statuses.get(key)

    def set_status(self, key, value):
        self._statuses[key] = value

    def settings(self):
        return self._settings

    def set_scratch(self, value):
        self.scratch_values.append(value)

    def run_command(self, name, payload=None):
        self.commands.append((name, payload))

    def erase_regions(self, key):
        self.erased_regions.append(key)

    def add_regions(self, key, regions, *props):
        self.added_regions.append((key, list(regions), props))

    def line(self, location):
        point = location.begin() if hasattr(location, "begin") else int(location)
        return _FakeRegion(point, point + 10)

    def show(self, point):
        self.shown_points.append(point)

    def window(self):
        return self._window


class _FakeState:
    def __init__(self, *, launch_session=None):
        self.launch_session = launch_session
        self.set_launch_session_calls = []
        self.advance_panel_input_calls = []
        self.use_debugger = False
        self.tester = None

    def set_launch_session(self, launch_session):
        self.launch_session = launch_session
        self.set_launch_session_calls.append(launch_session)

    def advance_panel_input(self, value):
        self.advance_panel_input_calls.append(value)


class _FakePanelTest:
    def __init__(self, test_string):
        self.test_string = test_string
        self.fold = True
        self.last_evaluation = None
        self.display_layout = None
        self.runtime = None
        self.rtcode = None

    def set_last_evaluation(self, evaluation):
        self.last_evaluation = evaluation

    def set_display_layout(self, body_text, output_start_offset):
        self.display_layout = (body_text, output_start_offset)

    def set_cur_runtime(self, runtime):
        self.runtime = runtime

    def set_cur_rtcode(self, rtcode):
        self.rtcode = rtcode


@contextmanager
def _patched_session_action_dependencies():
    module_names = (
        "sublime",
        "arena_forge.adapters.sublime.shared.messages",
        "arena_forge.adapters.sublime.root_bridge",
        "arena_forge.adapters.sublime.run_panel.launch_flow",
        "arena_forge.adapters.sublime.run_panel.logic",
        "arena_forge.adapters.sublime.run_panel.process_actions",
        "arena_forge.adapters.sublime.run_panel.regions",
        "arena_forge.adapters.sublime.run_panel.session_service",
        "arena_forge.adapters.sublime.run_panel.state",
        "arena_forge.adapters.sublime.shared.settings_bridge",
        "arena_forge.adapters.sublime.run_panel.session_actions",
    )
    originals = {name: sys.modules.get(name) for name in module_names}
    sys.modules["sublime"] = types.SimpleNamespace(
        Region=_FakeRegion,
        set_timeout=lambda callback, delay=0: None,
        set_timeout_async=lambda callback, delay=0: None,
    )
    sys.modules["arena_forge.adapters.sublime.shared.messages"] = types.SimpleNamespace(
        product_log_message=lambda *args, **kwargs: None,
        translate=lambda key, **kwargs: key,
    )
    sys.modules["arena_forge.adapters.sublime.root_bridge"] = types.SimpleNamespace(
        get_debugger_info_module=lambda: None
    )
    sys.modules["arena_forge.adapters.sublime.run_panel.launch_flow"] = types.SimpleNamespace(
        RunPanelLaunchRequest=_FakeRequest,
        plan_run_panel_launch=lambda *args, **kwargs: None,
    )
    sys.modules["arena_forge.adapters.sublime.run_panel.logic"] = types.SimpleNamespace(
        build_run_panel_stop_plan=lambda *args, **kwargs: None
    )
    sys.modules["arena_forge.adapters.sublime.run_panel.process_actions"] = types.SimpleNamespace(
        schedule_test_manager_command=lambda *args, **kwargs: None,
        terminate_command_tester_with_logging=lambda *args, **kwargs: None,
    )
    sys.modules["arena_forge.adapters.sublime.run_panel.regions"] = types.SimpleNamespace(
        clear_panel_view=lambda *args, **kwargs: None
    )
    sys.modules["arena_forge.adapters.sublime.run_panel.session_service"] = types.SimpleNamespace(
        create_run_backend=lambda *args, **kwargs: None,
        prepare_tests_for_run=lambda *args, **kwargs: [],
        select_run_backend=lambda *args, **kwargs: None,
    )
    sys.modules["arena_forge.adapters.sublime.run_panel.state"] = types.SimpleNamespace(
        append_run_history=lambda *args, **kwargs: None
    )
    sys.modules["arena_forge.adapters.sublime.shared.settings_bridge"] = types.SimpleNamespace(
        get_session_repository=lambda: None,
        get_settings=lambda: None,
        get_tests_file_path=lambda *args, **kwargs: None,
    )
    sys.modules.pop("arena_forge.adapters.sublime.run_panel.session_actions", None)
    try:
        yield
    finally:
        for name, original in originals.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original


class RunPanelSessionActionsTests(unittest.TestCase):
    def test_resolve_stop_evaluation_returns_compile_error_for_failed_compile(self) -> None:
        with _patched_session_action_dependencies():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel.session_actions")
            tester = types.SimpleNamespace(evaluate_test=lambda test_id: "unexpected")

            evaluation = module.resolve_stop_evaluation(tester, 0, 1, compile_failed=True)

            self.assertEqual(evaluation.verdict, Verdict.COMPILE_ERROR)

    def test_resolve_stop_evaluation_uses_runtime_evaluation_only_for_success(self) -> None:
        with _patched_session_action_dependencies():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel.session_actions")
            expected = object()
            tester = types.SimpleNamespace(evaluate_test=lambda test_id: expected)

            self.assertIs(module.resolve_stop_evaluation(tester, 0, 0), expected)
            self.assertIsNone(module.resolve_stop_evaluation(tester, 0, 7))

    def test_schedule_rerun_terminates_existing_tester_and_reuses_launch_args(self) -> None:
        with _patched_session_action_dependencies():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel.session_actions")
            calls = []
            module.terminate_command_tester_with_logging = lambda command: calls.append(("terminate", command))
            module.schedule_test_manager_command = lambda view, payload, delay=0: calls.append(
                ("schedule", view, payload, delay)
            )
            view = object()
            command = object()
            request = types.SimpleNamespace(to_command_args=lambda: {"action": "make_opd"})
            launch_plan = types.SimpleNamespace(command_args={"action": "make_opd", "load_session": True})

            module._schedule_rerun(view, command, request, launch_plan)

            self.assertEqual(
                calls,
                [
                    ("terminate", command),
                    ("schedule", view, {"action": "make_opd", "load_session": True}, 30),
                ],
            )

    def test_handle_compile_failure_marks_stopped_and_sets_error_bar(self) -> None:
        with _patched_session_action_dependencies():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel.session_actions")
            calls = []
            command = types.SimpleNamespace(
                change_process_status=lambda status: calls.append(("status", status)),
                set_compile_bar=lambda text, type="": calls.append(("bar", text, type)),
            )
            module.handle_process_stop = lambda command, rtcode, runtime, compile_failed=False: calls.append(
                ("stop", command, rtcode, runtime, compile_failed)
            )

            module.handle_compile_failure(command, 9)

            self.assertEqual(
                calls,
                [
                    ("status", "STOPPED"),
                    ("stop", command, 9, 0, True),
                    ("bar", "error.compilation_error", "error"),
                ],
            )

    def test_handle_process_stop_clears_input_queues_follow_up_and_marks_crash_line(self) -> None:
        with _patched_session_action_dependencies():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel.session_actions")
            scheduled = []
            module.sublime.set_timeout = lambda callback, delay=0: scheduled.append((callback, delay))
            evaluation = object()
            stop_plan = types.SimpleNamespace(
                evaluation=evaluation,
                clear_input=True,
                rendered_text="ignored",
                output_start_offset=5,
                output_text="program output\n\n",
                history_verdict="accepted",
                history_return_code=0,
                queue_follow_up=True,
            )
            plan_calls = []
            module.resolve_stop_evaluation = lambda tester, test_id, rtcode, compile_failed=False: (
                plan_calls.append(("resolve", tester, test_id, rtcode, compile_failed)) or evaluation
            )
            module.build_run_panel_stop_plan = lambda **kwargs: plan_calls.append(("plan", kwargs)) or stop_plan
            history_calls = []
            module.get_session_repository = lambda: "repo"
            module.append_run_history = lambda *args, **kwargs: history_calls.append((args, kwargs))

            code_view = types.SimpleNamespace(
                id=lambda: 99,
                commands=[],
                run_command=lambda name, payload=None: code_view.commands.append((name, payload)),
            )
            other_view = types.SimpleNamespace(
                id=lambda: 5,
                commands=[],
                run_command=lambda name, payload=None: other_view.commands.append((name, payload)),
            )
            view = _FakeView(window_views=[other_view, code_view])
            panel_test = _FakePanelTest("1 2 3")
            tester = types.SimpleNamespace(
                running_test=0,
                tests=[panel_test],
                prog_out=["hello"],
                running_new=True,
                have_pretests=lambda: True,
            )
            update_calls = []
            command = types.SimpleNamespace(
                view=view,
                state=types.SimpleNamespace(
                    tester=tester,
                    input_start=2,
                    delta_input=6,
                    source_file="main.cpp",
                    code_view_id=99,
                ),
                REGION_BEGIN_KEY="test_begin_%d",
                REGION_BEGIN_PROP=("begin", "icon", 1),
                REGION_END_PROP=("end", "icon", 2),
                memorize_tests=lambda: update_calls.append(("memorize", None)),
                update_configs=lambda update_last=None: update_calls.append(("update", update_last)),
            )

            module.handle_process_stop(command, 0, 321, crash_line=77)

            self.assertEqual(plan_calls[0], ("resolve", tester, 0, 0, False))
            self.assertEqual(plan_calls[1][0], "plan")
            self.assertEqual(panel_test.last_evaluation, evaluation)
            self.assertEqual(panel_test.display_layout, (None, None))
            self.assertEqual(panel_test.runtime, 321)
            self.assertEqual(panel_test.rtcode, 0)
            self.assertEqual(view.erased_regions, ["type"])
            self.assertEqual(
                view.commands[:2],
                [
                    ("test_manager", {"action": "replace", "region": (2, 16), "text": ""}),
                    ("test_manager", {"action": "set_cursor_to_end"}),
                ],
            )
            self.assertEqual(view.added_regions, [("test_end_0", [_FakeRegion(7, 7)], (("end", "icon", 2)))])
            self.assertEqual(view.shown_points, [22])
            self.assertEqual(update_calls, [("memorize", None), ("update", True)])
            self.assertEqual(len(scheduled), 1)
            callback, delay = scheduled.pop(0)
            self.assertEqual(delay, 10)
            callback()
            self.assertEqual(view.commands[-1], ("test_manager", {"action": "new_test"}))
            self.assertEqual(
                history_calls,
                [
                    (
                        ("repo", "main.cpp", "Test 1", "program output\n\n", "accepted", 321, 0),
                        {"evaluation": evaluation},
                    )
                ],
            )
            self.assertEqual(code_view.commands, [("debug_overlay", {"action": "show_crash_line", "crash_line": 77})])
            self.assertEqual(other_view.commands, [])

    def test_handle_process_stop_preserves_rendered_output_and_schedules_refresh(self) -> None:
        with _patched_session_action_dependencies():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel.session_actions")
            scheduled = []
            module.sublime.set_timeout = lambda callback, delay=0: scheduled.append((callback, delay))
            evaluation = object()
            stop_plan = types.SimpleNamespace(
                evaluation=evaluation,
                clear_input=False,
                rendered_text="input\nanswer\n\n",
                output_start_offset=6,
                output_text="answer\n\n",
                history_verdict="runtime_error",
                history_return_code=-1,
                queue_follow_up=False,
            )
            module.resolve_stop_evaluation = lambda *args, **kwargs: evaluation
            module.build_run_panel_stop_plan = lambda **kwargs: stop_plan
            module.get_session_repository = lambda: "repo"
            module.append_run_history = lambda *args, **kwargs: None

            view = _FakeView(window_views=[])
            panel_test = _FakePanelTest("abc")
            tester = types.SimpleNamespace(
                running_test=0,
                tests=[panel_test],
                prog_out=["segfault"],
                running_new=False,
                have_pretests=lambda: False,
            )
            update_calls = []
            command = types.SimpleNamespace(
                view=view,
                state=types.SimpleNamespace(
                    tester=tester,
                    input_start=4,
                    delta_input=8,
                    source_file="main.cpp",
                    code_view_id=99,
                ),
                REGION_BEGIN_KEY="test_begin_%d",
                REGION_BEGIN_PROP=("begin", "icon", 1),
                REGION_END_PROP=("end", "icon", 2),
                memorize_tests=lambda: update_calls.append(("memorize", None)),
                update_configs=lambda update_last=None: update_calls.append(("update", update_last)),
            )

            module.handle_process_stop(command, "oops", 99)

            self.assertEqual(panel_test.display_layout, ("input\nanswer\n\n", 6))
            self.assertEqual(panel_test.fold, False)
            self.assertEqual(
                view.commands[:2],
                [
                    ("test_manager", {"action": "replace", "region": (4, 18), "text": "input\nanswer\n\n"}),
                    ("test_manager", {"action": "set_cursor_to_end"}),
                ],
            )
            self.assertEqual(
                view.added_regions,
                [
                    ("test_begin_0", [_FakeRegion(4, 14)], (("begin", "icon", 1))),
                    ("test_end_0", [_FakeRegion(10, 10)], (("end", "icon", 2))),
                ],
            )
            self.assertEqual(update_calls, [("memorize", None)])
            self.assertEqual(len(scheduled), 1)
            callback, delay = scheduled.pop(0)
            self.assertEqual(delay, 100)
            callback()
            self.assertEqual(update_calls, [("memorize", None), ("update", None)])

    def test_schedule_compile_start_initializes_tester_after_successful_compile(self) -> None:
        with _patched_session_action_dependencies():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel.session_actions")
            scheduled = []
            module.sublime.set_timeout_async = lambda callback, delay=0: scheduled.append((callback, delay))
            compile_failure_calls = []
            module.handle_compile_failure = lambda command, rtcode: compile_failure_calls.append((command, rtcode))

            view = _FakeView(settings={"edit_mode": True})
            state = _FakeState()
            created = {}

            def tester_factory(*args, **kwargs):
                created["args"] = args
                created["kwargs"] = kwargs
                return types.SimpleNamespace(kind="tester", args=args, kwargs=kwargs)

            process_manager = types.SimpleNamespace(compile=lambda: None)
            command = types.SimpleNamespace(
                state=state,
                Tester=tester_factory,
                Test="TEST_FACTORY",
                on_insert="INSERT",
                on_out="OUT",
                on_stop="STOP",
                change_process_status=lambda status: created.setdefault("statuses", []).append(status),
                set_compile_bar=lambda text, type="": created.setdefault("compile_bars", []).append((text, type)),
            )

            module._schedule_compile_start(command, view, process_manager, ["T1"], True)

            self.assertEqual(created["compile_bars"], [("status.compiling", "")])
            self.assertEqual(len(scheduled), 1)
            callback, delay = scheduled.pop(0)
            self.assertEqual(delay, 10)

            callback()

            self.assertEqual(created["statuses"], ["COMPILED"])
            self.assertEqual(state.advance_panel_input_calls, [0])
            self.assertEqual(command.state.tester.kind, "tester")
            self.assertEqual(created["kwargs"]["tests"], ["T1"])
            self.assertTrue(created["kwargs"]["sync_out"])
            self.assertEqual(created["kwargs"]["test_factory"], "TEST_FACTORY")
            self.assertFalse(view.settings().get("edit_mode"))
            self.assertEqual(view.commands, [("test_manager", {"action": "new_test"})])
            self.assertEqual(created["compile_bars"], [("status.compiling", "")])

            created["kwargs"]["on_compile_error"](3, 17, "boom")
            self.assertEqual(compile_failure_calls, [(command, 17)])

    def test_schedule_compile_start_reports_compile_errors_without_creating_tester(self) -> None:
        with _patched_session_action_dependencies():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel.session_actions")
            scheduled = []
            module.sublime.set_timeout_async = lambda callback, delay=0: scheduled.append((callback, delay))

            view = _FakeView(settings={"edit_mode": True})
            state = _FakeState()
            process_manager = types.SimpleNamespace(compile=lambda: (2, "boom"))
            command = types.SimpleNamespace(
                state=state,
                Tester=lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("tester should not be created")),
                Test="TEST_FACTORY",
                on_insert="INSERT",
                on_out="OUT",
                on_stop="STOP",
                change_process_status=lambda status: setattr(command, "status", status),
                set_compile_bar=lambda text, type="": command.compile_bars.append((text, type)),
                compile_bars=[],
            )

            module._schedule_compile_start(command, view, process_manager, ["T1"], False)
            callback, delay = scheduled.pop(0)
            self.assertEqual(delay, 10)

            callback()

            self.assertEqual(command.status, "COMPILED")
            self.assertEqual(state.advance_panel_input_calls, [0])
            self.assertEqual(
                command.compile_bars,
                [("status.compiling", ""), ("error.compilation_error", "error")],
            )
            self.assertEqual(view.commands, [("test_manager", {"action": "insert_opd_out", "text": "\nboom"})])
            self.assertIsNone(command.state.tester)
            self.assertTrue(view.settings().get("edit_mode"))

    def test_make_opd_rerun_short_circuits_before_panel_reset(self) -> None:
        with _patched_session_action_dependencies():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel.session_actions")
            view = _FakeView(statuses={"process_status_code": "RUNNING"}, settings={"edit_mode": True})
            state = _FakeState(launch_session="saved-session")
            captured = {}
            module.plan_run_panel_launch = lambda **kwargs: types.SimpleNamespace(action="rerun", command_args=None)
            module._schedule_rerun = lambda view, command, request, launch_plan: captured.update(
                {"view": view, "command": command, "request": request, "plan": launch_plan}
            )
            command = types.SimpleNamespace(
                view=view,
                state=state,
                apply_edit_changes=lambda: setattr(command, "applied", True),
            )

            module.make_opd(command, edit="EDIT", run_file="main.cpp", sync_out=True)

            self.assertEqual(captured["view"], view)
            self.assertEqual(captured["command"], command)
            self.assertEqual(captured["request"].run_file, "main.cpp")
            self.assertTrue(captured["request"].sync_out)
            self.assertFalse(hasattr(command, "applied"))
            self.assertEqual(view.commands, [])
            self.assertEqual(view.scratch_values, [])

    def test_make_opd_reports_restore_errors_after_resetting_panel(self) -> None:
        with _patched_session_action_dependencies():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel.session_actions")
            view = _FakeView(statuses={"process_status_code": "STOPPED"}, settings={"edit_mode": True})
            state = _FakeState()
            calls = []
            module.plan_run_panel_launch = lambda **kwargs: types.SimpleNamespace(
                action="error",
                error_key="error.custom_restore_failed",
            )
            module.clear_all = lambda command: calls.append(("clear", command))
            module.translate = lambda key, **kwargs: "translated:" + key
            command = types.SimpleNamespace(
                view=view,
                state=state,
                apply_edit_changes=lambda: calls.append(("apply", None)),
                set_compile_bar=lambda text, type="": calls.append(("bar", text, type)),
                prepare_code_view=lambda: calls.append(("prepare", None)),
                change_process_status=lambda status: calls.append(("status", status)),
            )

            module.make_opd(command, edit="EDIT", load_session=True)

            self.assertEqual(
                calls,
                [("apply", None), ("clear", command), ("bar", "translated:error.session_restore_failed", "error")],
            )
            self.assertEqual(view.scratch_values, [True])
            self.assertEqual(view.get_status("opd_info"), "opdebugger-file")
            self.assertEqual(
                view.commands,
                [
                    ("set_setting", {"setting": "fold_buttons", "value": False}),
                    ("set_setting", {"setting": "line_numbers", "value": False}),
                    (
                        "append",
                        {
                            "characters": "translated:error.custom_restore_failed",
                            "force": True,
                            "scroll_to_end": False,
                        },
                    ),
                ],
            )

    def test_make_opd_launches_session_and_schedules_compile(self) -> None:
        with _patched_session_action_dependencies():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel.session_actions")
            launch_session = types.SimpleNamespace(run_file="main.cpp", build_sys="ninja", sync_out=True)
            view = _FakeView(
                statuses={"process_status_code": "STOPPED"},
                settings={"edit_mode": True, "word_wrap": False},
            )
            state = _FakeState(launch_session="saved-session")
            calls = []
            module.plan_run_panel_launch = lambda **kwargs: types.SimpleNamespace(
                action="launch",
                session=launch_session,
            )
            module.clear_all = lambda command: calls.append(("clear", command))
            module.product_log_message = lambda key, **kwargs: calls.append(("log", key))
            module._build_run_backend_state = lambda command, session: (
                calls.append(("build", session)) or (["T1"], "PROCESS", True)
            )
            module._schedule_compile_start = lambda command, view, process_manager, tests, sync_out: calls.append(
                ("schedule", command, view, process_manager, tests, sync_out)
            )
            command = types.SimpleNamespace(
                view=view,
                state=state,
                apply_edit_changes=lambda: calls.append(("apply", None)),
                set_compile_bar=lambda text, type="": calls.append(("bar", text, type)),
                prepare_code_view=lambda: calls.append(("prepare", None)),
                change_process_status=lambda status: calls.append(("status", status)),
            )

            module.make_opd(
                command,
                edit="EDIT",
                run_file="main.cpp",
                build_sys="ninja",
                sync_out=True,
                code_view_id=4,
            )

            self.assertEqual(state.set_launch_session_calls, [launch_session])
            self.assertEqual(
                calls,
                [
                    ("apply", None),
                    ("clear", command),
                    ("log", "status.session_saved"),
                    ("prepare", None),
                    ("status", "COMPILING"),
                    ("build", launch_session),
                    ("schedule", command, view, "PROCESS", ["T1"], True),
                ],
            )
            self.assertEqual(view.scratch_values, [True])
            self.assertEqual(view.get_status("opd_info"), "opdebugger-file")
            self.assertEqual(
                view.commands,
                [
                    ("set_setting", {"setting": "fold_buttons", "value": False}),
                    ("set_setting", {"setting": "line_numbers", "value": False}),
                    ("toggle_setting", {"setting": "word_wrap"}),
                ],
            )

    def test_make_opd_raises_when_launch_plan_omits_session(self) -> None:
        with _patched_session_action_dependencies():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel.session_actions")
            module.plan_run_panel_launch = lambda **kwargs: types.SimpleNamespace(action="launch", session=None)
            module.clear_all = lambda command: None
            view = _FakeView(statuses={"process_status_code": "STOPPED"}, settings={"edit_mode": False})
            command = types.SimpleNamespace(
                view=view,
                state=_FakeState(),
                apply_edit_changes=lambda: None,
            )

            with self.assertRaisesRegex(RuntimeError, "error.no_launch_session"):
                module.make_opd(command, edit="EDIT", run_file="main.cpp")


if __name__ == "__main__":
    unittest.main()
