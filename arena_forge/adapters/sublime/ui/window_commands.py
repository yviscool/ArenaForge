from __future__ import annotations

from pathlib import Path

import sublime
import sublime_plugin

from ..doctor_report import build_doctor_report
from ..shared.messages import status_message, translate
from ..shared.package_resources import (
    STRESS_SYNTAX_RESOURCE,
    TEST_SYNTAX_RESOURCE,
    get_package_resource_root,
    get_plugin_package_name,
    get_plugin_root_dir,
)
from ..shared.settings_bridge import get_application, get_contests_root


def _ensure_view(window):
    view = window.active_view()
    if view is None:
        view = window.new_file()
        view.set_scratch(True)
    return view


def _active_file_view(window):
    view = window.active_view()
    if view is None:
        status_message("error.active_view_required")
        return None
    if view.file_name() is None and not view.settings().get("arena_forge.history_source_file"):
        status_message("error.file_view_required")
        return None
    return view


class ArenaForgeOpenSettingsCommand(sublime_plugin.WindowCommand):
    def run(self) -> None:
        _ensure_view(self.window).run_command("template_bridge", {"action": "open_settings"})


class ArenaForgeAutoCommand(sublime_plugin.WindowCommand):
    def run(self) -> None:
        view = _active_file_view(self.window)
        if view is None:
            return
        view.run_command("template_bridge", {"action": "show_funcs"})


class ArenaForgeRunCommand(sublime_plugin.WindowCommand):
    def run(self) -> None:
        view = _active_file_view(self.window)
        if view is None:
            return
        syntax = view.settings().get("syntax") or ""
        if "TestSyntax" in syntax:
            view.run_command("test_manager", {"action": "make_opd", "load_session": True, "use_debugger": False})
        else:
            view.run_command("debug_overlay", {"action": "make_opd"})


class ArenaForgeSelectFrameCommand(sublime_plugin.WindowCommand):
    def run(self) -> None:
        view = _active_file_view(self.window)
        if view is None:
            return
        view.run_command("debug_overlay", {"action": "show_frames"})


class ArenaForgeMakeStressCommand(sublime_plugin.WindowCommand):
    def run(self) -> None:
        view = _active_file_view(self.window)
        if view is None:
            return
        view.run_command("stress_manager", {"action": "make_stress"})


class ArenaForgeStopStressCommand(sublime_plugin.WindowCommand):
    def run(self) -> None:
        view = self.window.active_view()
        if view is None:
            status_message("error.active_view_required")
            return
        view.run_command("stress_manager", {"action": "stop_stress"})


class ArenaForgeSetupContestCommand(sublime_plugin.WindowCommand):
    def run(self) -> None:
        _ensure_view(self.window).run_command("contest_handler", {"action": "setup_contest"})


class ArenaForgeSubmitCommand(sublime_plugin.WindowCommand):
    def run(self) -> None:
        view = _active_file_view(self.window)
        if view is None:
            return
        view.run_command("contest_handler", {"action": "submit"})


class ArenaForgeConfigureCredentialsCommand(sublime_plugin.WindowCommand):
    def run(self) -> None:
        view = _active_file_view(self.window)
        if view is None:
            return
        view.run_command("contest_handler", {"action": "configure_credentials"})


class ArenaForgeRunHistoryCommand(sublime_plugin.WindowCommand):
    def run(self) -> None:
        view = _active_file_view(self.window)
        if view is None:
            return
        view.run_command("run_history_panel")


class ArenaForgeOpenHistorySourceCommand(sublime_plugin.WindowCommand):
    def run(self) -> None:
        view = self.window.active_view()
        if view is None:
            status_message("error.active_view_required")
            return
        view.run_command("run_history_open_source")


class ArenaForgeClearAllTestsCommand(sublime_plugin.WindowCommand):
    def run(self) -> None:
        view = self.window.active_view()
        if view is None:
            status_message("error.active_view_required")
            return
        view.run_command("test_manager", {"action": "clear_all_tests"})


class ArenaForgeDoctorCommand(sublime_plugin.WindowCommand):
    def run(self) -> None:
        application = get_application()
        credential_store = application.credential_store
        credential_available = bool(
            getattr(credential_store, "is_available", lambda: False)()
        )
        report = build_doctor_report(
            package_name=get_plugin_package_name(),
            package_root=Path(get_plugin_root_dir()),
            package_resource_root=get_package_resource_root(),
            discovered_resources={
                "TestSyntax.sublime-syntax": sublime.find_resources("TestSyntax.sublime-syntax"),
                "StressSyntax.sublime-syntax": sublime.find_resources("StressSyntax.sublime-syntax"),
                TEST_SYNTAX_RESOURCE: (
                    [TEST_SYNTAX_RESOURCE]
                    if sublime.find_resources("TestSyntax.sublime-syntax")
                    else []
                ),
                STRESS_SYNTAX_RESOURCE: [STRESS_SYNTAX_RESOURCE]
                if sublime.find_resources("StressSyntax.sublime-syntax")
                else [],
            },
            profiles=application.profiles,
            settings=application.settings,
            contests_root=get_contests_root(),
            credential_backend=str(getattr(credential_store, "backend_name", "unknown")),
            credential_available=credential_available,
            translate_text=translate,
        )
        view = self.window.new_file()
        view.set_name(translate("doctor.title"))
        view.set_scratch(True)
        view.run_command("append", {"characters": report, "force": True, "scroll_to_end": False})
        status_message("status.doctor_report_ready")
