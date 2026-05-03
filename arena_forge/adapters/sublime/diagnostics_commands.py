from __future__ import annotations

from pathlib import Path

import sublime
import sublime_plugin

from arena_forge.adapters.runners import CompilerDiagnosticsService, DiagnosticsScratchWorkspace
from arena_forge.core.domain import DiagnosticSeverity

from .messages import product_log_message, status_message, translate
from .package_resources import get_plugin_root_dir
from .settings_bridge import get_settings, is_lang_view


class InteliSenseCommand(sublime_plugin.TextCommand):
    run_status = ""
    timer_run = False

    def get_compile_cmd(self):
        for option in get_settings().get("run_settings", []):
            if option["name"] == "C++":
                return option.get("lint_compile_cmd", None)
        return None

    def stop_sense(self):
        self.run_status = "do_disable"

    def sync(self):
        if self.timer_run:
            self.stop_sense()
            status_message("status.sense_disabled")
        else:
            self.run_sense()
            status_message("status.sense_enabled")

    def run_sense(self):
        compile_cmd = self.get_compile_cmd()
        if compile_cmd is None or not get_settings().get("lint_enabled"):
            return
        if self.timer_run:
            self.run_status = "do_waited_sense"
            return 0
        self.run_status = "do_waited_sense"

        def sense_timer(self=self):
            view = self.view
            state = self.run_status
            if state == "do_waited_sense":
                view.erase_regions("error_marks")
                view.erase_regions("warning_marks")
                self.run_status = "do_sense"
            elif state == "do_sense":
                self.insert_error_marks()
                if self.run_status == "do_sense":
                    self.run_status = "sense_complete"
            elif state == "do_disable":
                view.erase_regions("error_marks")
                view.erase_regions("warning_marks")
                self.run_status = "disabled"
                self.timer_run = False
                return 0
            elif state == "":
                view.erase_regions("error_marks")
                view.erase_regions("warning_marks")
                self.timer_run = False
                return 0
            sublime.set_timeout_async(sense_timer, 500)

        self.timer_run = True
        sublime.set_timeout_async(sense_timer, 500)

    def run(self, edit, action=None):
        if action == "run_sense":
            self.run_sense()
        elif action == "stop_sense":
            self.stop_sense()
        elif action == "sync_sense":
            self.sync()
        elif action == "sync_modified":
            self.run_sense()

    def _diagnostics_service(self) -> CompilerDiagnosticsService:
        return CompilerDiagnosticsService(
            platform_name=sublime.platform(),
            scratch_workspace=DiagnosticsScratchWorkspace(Path(get_plugin_root_dir())),
        )

    def insert_error_marks(self):
        view = self.view
        source = view.substr(sublime.Region(0, view.size()))
        file_dir_path = str(Path(view.file_name()).resolve().parent)
        report = self._diagnostics_service().run(
            compile_cmd=self.get_compile_cmd(),
            source_text=source,
            source_file_dir=file_dir_path,
        )
        view.erase_regions("warning_marks")
        view.erase_regions("error_marks")
        try:
            errors = report.issues
        except Exception:
            product_log_message("error.parse_errors_failed")
            return 0

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
            pt = view.text_point(issue.line - 1, issue.column)
            if issue.severity is DiagnosticSeverity.WARNING:
                warn_regions.append(view.word(pt))
            elif issue.severity is DiagnosticSeverity.ERROR:
                error_regions.append(view.word(pt))

        if self.run_status == "do_sense":
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


class SenseListener(sublime_plugin.EventListener):
    def on_load(self, view):
        if is_lang_view(view, "C++"):
            view.run_command("inteli_sense", {"action": "run_sense"})

    def on_pre_close(self, view):
        if is_lang_view(view, "C++"):
            view.run_command("inteli_sense", {"action": "stop_sense"})

    def on_modified(self, view):
        if is_lang_view(view, "C++"):
            view.run_command("inteli_sense", {"action": "sync_modified"})

    def on_deactivated(self, view):
        if is_lang_view(view, "C++"):
            view.run_command("inteli_sense", {"action": "stop_sense"})

    def on_activated(self, view):
        if is_lang_view(view, "C++"):
            view.run_command("inteli_sense", {"action": "run_sense"})
