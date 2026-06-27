from __future__ import annotations

from arena_forge.adapters.i18n.catalog import translate_catalog as translate

from .persistence import load_panel_tests, persist_panel_tests

try:
    from arena_forge.adapters.runners import ProcessManager
except ImportError:  # pragma: no cover - depends on Sublime host runtime
    ProcessManager = None


def _write_empty_tests_file(destination: str) -> None:
    with open(destination, "w", encoding="utf-8") as handle:
        handle.write("[]")


def prepare_tests_for_run(
    source_file,
    *,
    clr_tests,
    test_factory,
    repository,
    tests_file_path_factory,
    load_tests=None,
    write_empty_tests_file=_write_empty_tests_file,
):
    if clr_tests:
        write_empty_tests_file(tests_file_path_factory(source_file, for_write=True))
        return []
    if load_tests is not None:
        return load_tests(source_file, test_factory, repository, tests_file_path_factory)
    return load_panel_tests(source_file, test_factory, repository, tests_file_path_factory)


def save_tests_for_run(source_file, tests, repository, infer_language_name, tests_file_path_factory):
    persist_panel_tests(
        source_file,
        tests,
        repository,
        infer_language_name,
        tests_file_path_factory,
    )


def create_process_manager(run_file, build_sys, profiles):
    if ProcessManager is None:
        raise RuntimeError(translate("error.process_manager_unavailable"))
    return ProcessManager(run_file, build_sys, profiles=profiles)


def create_run_backend(
    *,
    use_debugger,
    debug_module,
    run_file,
    build_sys,
    profiles,
    process_manager_factory=create_process_manager,
):
    if use_debugger and debug_module is not None:
        return debug_module(run_file)
    return process_manager_factory(run_file, build_sys, profiles)
