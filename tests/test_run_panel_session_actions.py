import importlib
import sys
import types
import unittest
from contextlib import contextmanager

from arena_forge.core.domain import Verdict


@contextmanager
def _patched_session_action_dependencies():
    module_names = (
        "sublime",
        "arena_forge.adapters.sublime.messages",
        "arena_forge.adapters.sublime.root_bridge",
        "arena_forge.adapters.sublime.run_panel_launch_flow",
        "arena_forge.adapters.sublime.run_panel_logic",
        "arena_forge.adapters.sublime.run_panel_process_actions",
        "arena_forge.adapters.sublime.run_panel_regions",
        "arena_forge.adapters.sublime.run_panel_session_service",
        "arena_forge.adapters.sublime.run_panel_state",
        "arena_forge.adapters.sublime.settings_bridge",
        "arena_forge.adapters.sublime.run_panel_session_actions",
    )
    originals = {name: sys.modules.get(name) for name in module_names}
    sys.modules["sublime"] = types.SimpleNamespace(
        Region=lambda a, b=None: (a, b),
        set_timeout=lambda callback, delay=0: None,
        set_timeout_async=lambda callback, delay=0: None,
    )
    sys.modules["arena_forge.adapters.sublime.messages"] = types.SimpleNamespace(
        product_log_message=lambda *args, **kwargs: None,
        translate=lambda key, **kwargs: key,
    )
    sys.modules["arena_forge.adapters.sublime.root_bridge"] = types.SimpleNamespace(
        get_debugger_info_module=lambda: None
    )
    sys.modules["arena_forge.adapters.sublime.run_panel_launch_flow"] = types.SimpleNamespace(
        RunPanelLaunchRequest=object,
        plan_run_panel_launch=lambda *args, **kwargs: None,
    )
    sys.modules["arena_forge.adapters.sublime.run_panel_logic"] = types.SimpleNamespace(
        build_run_panel_stop_plan=lambda *args, **kwargs: None
    )
    sys.modules["arena_forge.adapters.sublime.run_panel_process_actions"] = types.SimpleNamespace(
        schedule_test_manager_command=lambda *args, **kwargs: None,
        terminate_command_tester=lambda *args, **kwargs: None,
    )
    sys.modules["arena_forge.adapters.sublime.run_panel_regions"] = types.SimpleNamespace(
        clear_panel_view=lambda *args, **kwargs: None
    )
    sys.modules["arena_forge.adapters.sublime.run_panel_session_service"] = types.SimpleNamespace(
        create_run_backend=lambda *args, **kwargs: None,
        prepare_tests_for_run=lambda *args, **kwargs: [],
        select_run_backend=lambda *args, **kwargs: None,
    )
    sys.modules["arena_forge.adapters.sublime.run_panel_state"] = types.SimpleNamespace(
        append_run_history=lambda *args, **kwargs: None
    )
    sys.modules["arena_forge.adapters.sublime.settings_bridge"] = types.SimpleNamespace(
        get_session_repository=lambda: None,
        get_settings=lambda: None,
        get_tests_file_path=lambda *args, **kwargs: None,
    )
    sys.modules.pop("arena_forge.adapters.sublime.run_panel_session_actions", None)
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
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel_session_actions")
            tester = types.SimpleNamespace(evaluate_test=lambda test_id: "unexpected")

            evaluation = module.resolve_stop_evaluation(tester, 0, 1, compile_failed=True)

            self.assertEqual(evaluation.verdict, Verdict.COMPILE_ERROR)

    def test_resolve_stop_evaluation_uses_runtime_evaluation_only_for_success(self) -> None:
        with _patched_session_action_dependencies():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel_session_actions")
            expected = object()
            tester = types.SimpleNamespace(evaluate_test=lambda test_id: expected)

            self.assertIs(module.resolve_stop_evaluation(tester, 0, 0), expected)
            self.assertIsNone(module.resolve_stop_evaluation(tester, 0, 7))

    def test_schedule_rerun_terminates_existing_tester_and_reuses_launch_args(self) -> None:
        with _patched_session_action_dependencies():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel_session_actions")
            calls = []
            module.terminate_command_tester = lambda command, **kwargs: calls.append(("terminate", command, kwargs))
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
                    ("terminate", command, {"on_failure": unittest.mock.ANY}),
                    ("schedule", view, {"action": "make_opd", "load_session": True}, 30),
                ],
            )


if __name__ == "__main__":
    unittest.main()
