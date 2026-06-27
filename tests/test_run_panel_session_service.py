import sys
import types
import unittest

_sublime_mock = types.SimpleNamespace(
    Region=type("Region", (), {}),
    Phantom=object,
    LAYOUT_BLOCK=0,
    set_timeout=lambda callback, delay=0: None,
    set_timeout_async=lambda callback, delay=0: None,
    platform=lambda: "windows",
    HOVER_TEXT=1,
    DRAW_NO_FILL=1,
    DRAW_STIPPLED_UNDERLINE=2,
    DRAW_NO_OUTLINE=4,
    DRAW_EMPTY_AS_OVERWRITE=8,
    HIDDEN=0,
)
if "sublime" not in sys.modules:
    sys.modules["sublime"] = _sublime_mock
if "sublime_plugin" not in sys.modules:
    sys.modules["sublime_plugin"] = types.SimpleNamespace(TextCommand=type("TextCommand", (), {}))

from arena_forge.adapters.sublime.run_panel.session_service import (  # noqa: E402
    create_run_backend,
    prepare_tests_for_run,
)


class RunPanelSessionServiceTests(unittest.TestCase):
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
            write_empty_tests_file=writes.append,
        )

        self.assertEqual(result, [])
        self.assertEqual(writes, ["tests.json"])

    def test_create_run_backend_uses_debugger_when_requested_and_available(self) -> None:
        process_calls = []
        debug_calls = []

        def fake_process_manager(run_file, build_sys, profiles):
            process_calls.append((run_file, build_sys, profiles))
            return "process"

        def fake_debugger(run_file):
            debug_calls.append(run_file)
            return "debugger"

        process_backend = create_run_backend(
            use_debugger=False,
            debug_module=fake_debugger,
            run_file="main.cpp",
            build_sys="source.c++",
            profiles=["cfg"],
            process_manager_factory=fake_process_manager,
        )
        debugger_backend = create_run_backend(
            use_debugger=True,
            debug_module=fake_debugger,
            run_file="main.cpp",
            build_sys="source.c++",
            profiles=["cfg"],
            process_manager_factory=fake_process_manager,
        )

        self.assertEqual(process_backend, "process")
        self.assertEqual(debugger_backend, "debugger")
        self.assertEqual(process_calls, [("main.cpp", "source.c++", ["cfg"])])
        self.assertEqual(debug_calls, ["main.cpp"])


if __name__ == "__main__":
    unittest.main()
