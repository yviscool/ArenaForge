from __future__ import annotations

from arena_forge.adapters.runners import ProcessManager

from .run_panel_state import load_panel_tests, persist_panel_tests


def load_tests_for_run(source_file, test_factory, repository, tests_file_path_factory):
    return load_panel_tests(source_file, test_factory, repository, tests_file_path_factory)


def save_tests_for_run(source_file, tests, repository, infer_language_name, tests_file_path_factory):
    persist_panel_tests(
        source_file,
        tests,
        repository,
        infer_language_name,
        tests_file_path_factory,
    )


def create_process_manager(run_file, build_sys, run_settings):
    return ProcessManager(run_file, build_sys, run_settings=run_settings)
