from __future__ import annotations

import sublime_plugin

from .messages import status_message


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
        _ensure_view(self.window).run_command("olympic_funcs", {"action": "open_settings"})


class ArenaForgeAutoCommand(sublime_plugin.WindowCommand):
    def run(self) -> None:
        view = _active_file_view(self.window)
        if view is None:
            return
        view.run_command("olympic_funcs", {"action": "show_funcs"})


class ArenaForgeRunCommand(sublime_plugin.WindowCommand):
    def run(self) -> None:
        view = _active_file_view(self.window)
        if view is None:
            return
        syntax = view.settings().get("syntax") or ""
        if "TestSyntax" in syntax:
            view.run_command("test_manager", {"action": "make_opd", "load_session": True, "use_debugger": False})
        else:
            view.run_command("view_tester", {"action": "make_opd"})


class ArenaForgeSelectFrameCommand(sublime_plugin.WindowCommand):
    def run(self) -> None:
        view = _active_file_view(self.window)
        if view is None:
            return
        view.run_command("view_tester", {"action": "show_frames"})


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
