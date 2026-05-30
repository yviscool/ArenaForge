import unittest

from arena_forge.adapters.sublime.run_panel.session_service import (
    RunPanelBackendSelection,
    create_run_backend,
    plan_test_bootstrap,
    prepare_tests_for_run,
    select_run_backend,
)


class RunPanelSessionServiceTests(unittest.TestCase):
    def test_plan_test_bootstrap_uses_clear_action_when_requested(self) -> None:
        plan = plan_test_bootstrap(clr_tests=True)

        self.assertEqual(plan.action, "clear")

    def test_prepare_tests_for_run_loads_tests_when_not_clearing(self) -> None:
        loaded = []

        def fake_load(source_file, test_factory, repository, tests_file_path_factory):
            loaded.append((source_file, test_factory, repository, tests_file_path_factory))
            return ["a", "b"]

        result = prepare_tests_for_run(
            "main.cpp",
            clr_tests=False,
            test_factory="factory",
            repository="repo",
            tests_file_path_factory="path-factory",
            load_tests=fake_load,
        )

        self.assertEqual(result, ["a", "b"])
        self.assertEqual(loaded, [("main.cpp", "factory", "repo", "path-factory")])

    def test_prepare_tests_for_run_clears_storage_and_returns_empty_tests(self) -> None:
        writes = []

        def fake_paths(source_file, for_write=False):
            self.assertEqual(source_file, "main.cpp")
            self.assertTrue(for_write)
            return "tests.json"

        result = prepare_tests_for_run(
            "main.cpp",
            clr_tests=True,
            test_factory="factory",
            repository="repo",
            tests_file_path_factory=fake_paths,
            load_tests=lambda *args, **kwargs: ["unexpected"],
            write_empty_tests_file=writes.append,
        )

        self.assertEqual(result, [])
        self.assertEqual(writes, ["tests.json"])

    def test_select_run_backend_prefers_debugger_only_when_available(self) -> None:
        debugger = object()

        self.assertEqual(
            select_run_backend(use_debugger=False, debug_module=debugger),
            RunPanelBackendSelection(kind="process_manager"),
        )
        self.assertEqual(
            select_run_backend(use_debugger=True, debug_module=None),
            RunPanelBackendSelection(kind="process_manager"),
        )
        self.assertEqual(
            select_run_backend(use_debugger=True, debug_module=debugger),
            RunPanelBackendSelection(kind="debugger", debug_module=debugger),
        )

    def test_create_run_backend_uses_selected_backend_factory(self) -> None:
        process_calls = []
        debug_calls = []

        def fake_process_manager(run_file, build_sys, run_settings):
            process_calls.append((run_file, build_sys, run_settings))
            return "process"

        def fake_debugger(run_file):
            debug_calls.append(run_file)
            return "debugger"

        process_backend = create_run_backend(
            RunPanelBackendSelection(kind="process_manager"),
            run_file="main.cpp",
            build_sys="source.c++",
            run_settings=["cfg"],
            process_manager_factory=fake_process_manager,
        )
        debugger_backend = create_run_backend(
            RunPanelBackendSelection(kind="debugger", debug_module=fake_debugger),
            run_file="main.cpp",
            build_sys="source.c++",
            run_settings=["cfg"],
            process_manager_factory=fake_process_manager,
        )

        self.assertEqual(process_backend, "process")
        self.assertEqual(debugger_backend, "debugger")
        self.assertEqual(process_calls, [("main.cpp", "source.c++", ["cfg"])])
        self.assertEqual(debug_calls, ["main.cpp"])


if __name__ == "__main__":
    unittest.main()
