from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import sublime
import sublime_plugin

from arena_forge.adapters.runners import CompilerDiagnosticsService, DiagnosticsScratchWorkspace
from arena_forge.core.domain import DiagnosticSeverity

from ..shared.messages import product_log_message, status_message, translate
from ..shared.package_resources import get_plugin_root_dir
from ..shared.settings_bridge import get_settings, is_lang_view

_DIAGNOSTIC_DEBOUNCE_MS = 250
_DIAGNOSTIC_RUN_FAILURES = (IndexError, KeyError, OSError, ValueError)


@dataclass
class _DiagnosticsState:
    enabled: bool = True
    generation: int = 0
    last_change_count: Optional[int] = None


_VIEW_STATES: dict[int, _DiagnosticsState] = {}


def _state_for(view) -> _DiagnosticsState:
    return _VIEW_STATES.setdefault(view.id(), _DiagnosticsState())


def _clear_marks(view) -> None:
    view.erase_regions("error_marks")
    view.erase_regions("warning_marks")
    view.erase_status("compile_error")


def _is_generation_current(view, generation: int) -> bool:
    state = _VIEW_STATES.get(view.id())
    return state is not None and state.enabled and state.generation == generation


def _log_parse_errors_failed() -> None:
    product_log_message("error.parse_errors_failed")


class IntelliSenseCommand(sublime_plugin.TextCommand):
    def get_compile_cmd(self):
        file_name = self.view.file_name()
        if not file_name:
            return None
        extension = Path(file_name).suffix.lstrip(".")
        for option in get_settings().get("run_settings", []):
            if extension in option.get("extensions", ()) and option.get("lint_compile_cmd"):
                return option.get("lint_compile_cmd", None)
        for option in get_settings().get("run_settings", []):
            if option.get("id") == "cpp" or option["name"] == "C++":
                return option.get("lint_compile_cmd", None)
        return None

    @staticmethod
    def _lint_timeout_ms() -> int:
        return max(0, int(get_settings().get("lint_timeout_ms") or 0))

    def stop_sense(self):
        state = _state_for(self.view)
        state.enabled = False
        state.generation += 1
        _clear_marks(self.view)

    def clear_sense_state(self):
        state = _VIEW_STATES.get(self.view.id())
        if state is not None:
            state.generation += 1
        _VIEW_STATES.pop(self.view.id(), None)
        _clear_marks(self.view)

    def sync(self):
        state = _state_for(self.view)
        if state.enabled:
            self.stop_sense()
            status_message("status.sense_disabled")
        else:
            state.enabled = True
            status_message("status.sense_enabled")
            self.run_sense(force=True)

    def run_sense(self, *, force: bool = False):
        view = self.view
        state = _state_for(view)
        compile_cmd = self.get_compile_cmd()
        if compile_cmd is None or not get_settings().get("lint_enabled"):
            state.last_change_count = None
            _clear_marks(view)
            return 0

        if not state.enabled:
            return 0

        change_count = view.change_count()
        if not force and state.last_change_count == change_count:
            return 0

        if state.last_change_count != change_count:
            _clear_marks(view)

        timeout_ms = self._lint_timeout_ms()

        state.generation += 1
        generation = state.generation

        def capture_snapshot(
            self=self,
            view=view,
            compile_cmd=compile_cmd,
            change_count=change_count,
            generation=generation,
            timeout_ms=timeout_ms,
        ):
            if not _is_generation_current(view, generation):
                return
            file_name = view.file_name()
            if not file_name:
                return

            source = view.substr(sublime.Region(0, view.size()))
            file_dir_path = str(Path(file_name).resolve().parent)
            sublime.set_timeout_async(
                lambda: self._collect_diagnostics(
                    view=view,
                    compile_cmd=compile_cmd,
                    source=source,
                    source_file=file_name,
                    file_dir_path=file_dir_path,
                    change_count=change_count,
                    generation=generation,
                    timeout_ms=timeout_ms,
                ),
                0,
            )

        sublime.set_timeout(capture_snapshot, _DIAGNOSTIC_DEBOUNCE_MS)
        return 0

    def _collect_diagnostics(
        self,
        *,
        view,
        compile_cmd: str,
        source: str,
        source_file: str,
        file_dir_path: str,
        change_count: int,
        generation: int,
        timeout_ms: int,
    ) -> None:
        if not _is_generation_current(view, generation):
            return
        try:
            report = self._diagnostics_service().run(
                compile_cmd=compile_cmd,
                source_text=source,
                source_file=source_file,
                source_file_dir=file_dir_path,
                scratch_label=f"view-{view.id()}-{generation}",
                timeout_ms=timeout_ms,
            )
        except _DIAGNOSTIC_RUN_FAILURES:
            sublime.set_timeout(_log_parse_errors_failed, 0)
            return

        sublime.set_timeout(
            lambda: self._apply_diagnostics(
                view=view,
                report=report,
                change_count=change_count,
                generation=generation,
            ),
            0,
        )

    def run(self, edit, action=None):
        if action == "run_sense":
            self.run_sense()
        elif action == "stop_sense":
            self.stop_sense()
        elif action == "clear_sense_state":
            self.clear_sense_state()
        elif action == "sync_sense":
            self.sync()
        elif action == "sync_modified":
            self.run_sense()

    def _diagnostics_service(self) -> CompilerDiagnosticsService:
        return CompilerDiagnosticsService(
            platform_name=sublime.platform(),
            scratch_workspace=DiagnosticsScratchWorkspace(Path(get_plugin_root_dir())),
        )

    def _apply_diagnostics(self, *, view, report, change_count: int, generation: int) -> None:
        if not _is_generation_current(view, generation):
            return
        state = _VIEW_STATES[view.id()]

        errors = getattr(report, "issues", None)
        if errors is None:
            product_log_message("error.parse_errors_failed")
            return

        state.last_change_count = change_count
        view.erase_regions("warning_marks")
        view.erase_regions("error_marks")

        for issue in errors:
            if issue.severity is DiagnosticSeverity.ERROR:
                view.set_status(
                    "compile_error",
                    translate(
                        "status.compile_issue",
                        line=issue.line,
                        column=issue.column,
                        message=issue.message,
                    ),
                )
                break
        else:
            for issue in errors:
                if issue.severity is DiagnosticSeverity.WARNING:
                    view.set_status(
                        "compile_error",
                        translate(
                            "status.compile_issue",
                            line=issue.line,
                            column=issue.column,
                            message=issue.message,
                        ),
                    )
                    break
            else:
                view.erase_status("compile_error")

        warn_regions = []
        error_regions = []
        for issue in errors:
            pt = view.text_point(max(issue.line - 1, 0), max(issue.column - 1, 0))
            if issue.severity is DiagnosticSeverity.WARNING:
                warn_regions.append(view.word(pt))
            elif issue.severity is DiagnosticSeverity.ERROR:
                error_regions.append(view.word(pt))

        view.add_regions(
            "warning_marks",
            warn_regions,
            get_settings().get("lint_warning_region_scope", "text.plain"),
            "dot",
            sublime.DRAW_NO_FILL,
        )
        view.add_regions(
            "error_marks",
            error_regions,
            get_settings().get("lint_error_region_scope", "text.plain"),
            "dot",
            sublime.DRAW_NO_FILL,
        )


class IntelliSenseListener(sublime_plugin.EventListener):
    def on_load(self, view):
        if is_lang_view(view, "C++"):
            view.run_command("intelli_sense", {"action": "run_sense"})

    def on_pre_close(self, view):
        if is_lang_view(view, "C++"):
            view.run_command("intelli_sense", {"action": "clear_sense_state"})

    def on_modified(self, view):
        if is_lang_view(view, "C++"):
            view.run_command("intelli_sense", {"action": "sync_modified"})

    def on_activated(self, view):
        if is_lang_view(view, "C++"):
            view.run_command("intelli_sense", {"action": "run_sense"})
