import importlib
import sys
import types
import unittest
from contextlib import contextmanager


@contextmanager
def _patched_test_actions():
    module_names = (
        "sublime",
        "arena_forge.adapters.sublime.shared.messages",
        "arena_forge.adapters.sublime.shared.settings_bridge",
        "arena_forge.adapters.sublime.run_panel.input_actions",
        "arena_forge.adapters.sublime.run_panel.rendering",
        "arena_forge.adapters.sublime.run_panel.session_service",
        "arena_forge.adapters.sublime.run_panel.test_actions",
    )
    originals = {name: sys.modules.get(name) for name in module_names}
    sys.modules["sublime"] = types.SimpleNamespace(
        Region=lambda a, b=None: (a, b),
        Phantom=object,
        LAYOUT_BLOCK=0,
        platform=lambda: "windows",
    )
    sys.modules["arena_forge.adapters.sublime.shared.messages"] = types.SimpleNamespace(
        status_message=lambda *args, **kwargs: None,
        product_log_message=lambda *args, **kwargs: None,
        translate=lambda key, **kwargs: key,
        translate_status_code=lambda status: status,
        translate_verdict=lambda verdict: str(verdict),
    )
    sys.modules["arena_forge.adapters.sublime.shared.settings_bridge"] = types.SimpleNamespace(
        get_session_repository=lambda: None,
        get_settings=lambda: None,
        get_tests_file_path=lambda *args, **kwargs: None,
        infer_language_name=lambda *args, **kwargs: None,
        root_dir=".",
    )
    sys.modules["arena_forge.adapters.sublime.run_panel.input_actions"] = types.SimpleNamespace(
        push_input_history=lambda *args, **kwargs: None
    )
    sys.modules["arena_forge.adapters.sublime.run_panel.rendering"] = types.SimpleNamespace(
        build_accdec_phantom=lambda *args, **kwargs: None,
        build_compile_bar_phantom=lambda *args, **kwargs: None,
        build_next_test_title_phantom=lambda *args, **kwargs: None,
        build_test_config_phantom=lambda *args, **kwargs: None,
    )
    sys.modules["arena_forge.adapters.sublime.run_panel.session_service"] = types.SimpleNamespace(
        create_run_backend=lambda *args, **kwargs: None,
        prepare_tests_for_run=lambda *args, **kwargs: [],
        select_run_backend=lambda *args, **kwargs: None,
        save_tests_for_run=lambda *args, **kwargs: None
    )
    sys.modules.pop("arena_forge.adapters.sublime.run_panel.test_actions", None)
    try:
        yield
    finally:
        for name, original in originals.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original


class RunPanelTestActionsTests(unittest.TestCase):
    def test_handle_test_event_uses_shared_termination_helper_for_stop(self) -> None:
        with _patched_test_actions():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel.test_actions")
            calls = []
            tester = object()
            module.terminate_tester_with_logging = lambda value: calls.append(value)
            command = types.SimpleNamespace(view=object(), state=types.SimpleNamespace(tester=tester))

            module.handle_test_event(command, 0, "test-stop")

            self.assertEqual(calls, [tester])

    def test_clear_all_tests_resets_state_and_requests_a_fresh_test(self) -> None:
        with _patched_test_actions():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel.test_actions")
            calls = []
            module.memorize_tests = lambda *args, **kwargs: calls.append(("memorize_tests", None))
            tester = types.SimpleNamespace(
                proc_run=True,
                tests=[object()],
                prog_out=["out"],
                test_iter=1,
                running_test=0,
                running_new=True,
                get_tests=lambda: [],
            )
            module.terminate_tester_with_logging = lambda value: calls.append(("terminate", value))
            command = types.SimpleNamespace(
                view=types.SimpleNamespace(run_command=lambda name, payload: calls.append(("run", name, payload))),
                state=types.SimpleNamespace(
                    tester=tester,
                    source_file="main.cpp",
                    reset_panel_runtime=lambda: calls.append(("reset_runtime", None)),
                ),
                clear_all=lambda: calls.append(("clear_all", None)),
            )

            module.clear_all_tests(command)

            self.assertEqual(tester.tests, [])
            self.assertEqual(tester.prog_out, [])
            self.assertEqual(tester.test_iter, 0)
            self.assertIsNone(tester.running_test)
            self.assertIsNone(tester.running_new)
            self.assertEqual(
                calls,
                [
                    ("terminate", tester),
                    ("clear_all", None),
                    ("reset_runtime", None),
                    ("memorize_tests", None),
                    ("run", "test_manager", {"action": "new_test"}),
                ],
            )


if __name__ == "__main__":
    unittest.main()
