from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

try:
    from arena_forge.adapters.runners import ProcessManager
except ImportError:  # pragma: no cover - depends on Sublime host runtime
    ProcessManager = None


@dataclass(frozen=True)
class RunPanelTestBootstrapPlan:
    action: str


@dataclass(frozen=True)
class RunPanelBackendSelection:
    kind: str
    debug_module: Optional[Callable[[str], object]] = None


def plan_test_bootstrap(*, clr_tests: bool) -> RunPanelTestBootstrapPlan:
    return RunPanelTestBootstrapPlan(action="clear" if clr_tests else "load")


def _write_empty_tests_file(destination: str) -> None:
    with open(destination, "w", encoding="utf-8") as handle:
        handle.write("[]")


def load_tests_for_run(source_file, test_factory, repository, tests_file_path_factory):
    from .state import load_panel_tests

    return load_panel_tests(source_file, test_factory, repository, tests_file_path_factory)


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
    if load_tests is None:
        load_tests = load_tests_for_run
    plan = plan_test_bootstrap(clr_tests=clr_tests)
    if plan.action == "clear":
        write_empty_tests_file(tests_file_path_factory(source_file, for_write=True))
        return []
    return load_tests(source_file, test_factory, repository, tests_file_path_factory)


def save_tests_for_run(source_file, tests, repository, infer_language_name, tests_file_path_factory):
    from .state import persist_panel_tests

    persist_panel_tests(
        source_file,
        tests,
        repository,
        infer_language_name,
        tests_file_path_factory,
    )


def create_process_manager(run_file, build_sys, run_settings):
    if ProcessManager is None:
        raise RuntimeError("ProcessManager is unavailable outside the Sublime host")
    return ProcessManager(run_file, build_sys, run_settings=run_settings)


def select_run_backend(*, use_debugger: bool, debug_module) -> RunPanelBackendSelection:
    if use_debugger and debug_module is not None:
        return RunPanelBackendSelection(kind="debugger", debug_module=debug_module)
    return RunPanelBackendSelection(kind="process_manager")


def create_run_backend(
    selection: RunPanelBackendSelection,
    *,
    run_file,
    build_sys,
    run_settings,
    process_manager_factory=create_process_manager,
):
    if selection.kind == "debugger":
        if selection.debug_module is None:
            raise RuntimeError("Debugger backend selection requires a debugger module")
        return selection.debug_module(run_file)
    return process_manager_factory(run_file, build_sys, run_settings)
