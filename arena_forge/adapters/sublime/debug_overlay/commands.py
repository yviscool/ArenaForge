from __future__ import annotations

import ast
import os
from os import path

import sublime
import sublime_plugin

from ..root_bridge import get_highlight_function
from ..shared.messages import status_message
from ..shared.package_resources import ARROW_RIGHT_ICON_RESOURCE, TEST_SYNTAX_RESOURCE
from ..shared.settings_bridge import get_settings


def split_frame_description(desc):
    balance = 0
    for index, char in enumerate(desc):
        if char == "(":
            balance += 1
        elif char == ")":
            balance -= 1
            if balance == 0:
                return [desc[: index + 1], desc[index + 2 :]]
    return desc


def show_var_popup(view, value, pos, highlight_function):
    view.show_popup(highlight_function(value), sublime.HIDE_ON_MOUSE_MOVE_AWAY, pos)


def show_frame_quick_panel(view, frames, on_select, on_highlight):
    items = [split_frame_description(frame["desc"]) for frame in frames]
    view.window().show_quick_panel(items, on_select, sublime.MONOSPACE_FONT, 0, on_highlight)


def _schedule_sidebar_hide(window) -> None:
    hide_sidebar = getattr(window, "set_sidebar_visible", None)
    if callable(hide_sidebar):
        sublime.set_timeout_async(lambda: hide_sidebar(False), 50)


class DebugOverlayCommand(sublime_plugin.TextCommand):
    ROOT = path.dirname(__file__)
    ruler_opd_panel = 0.68
    have_tied_dbg = False
    use_debugger = False

    def create_opd(self, clr_tests=False, sync_out=True, use_debugger=False):
        view = self.view
        if view.is_dirty():
            view.run_command("save")
        file_syntax = view.scope_name(view.sel()[0].begin()).rstrip().split()[0]
        window = view.window()
        view.erase_regions("crash_line")

        if self.have_tied_dbg:
            prop = window.get_view_index(self.tied_dbg)
            need_new = prop == (-1, -1)
        else:
            need_new = True

        if not need_new:
            dbg_view = self.tied_dbg
        else:
            dbg_view = window.new_file()
            self.tied_dbg = dbg_view
            self.have_tied_dbg = True
            if get_settings().get("close_sidebar"):
                _schedule_sidebar_hide(window)
            dbg_view.run_command("toggle_setting", {"setting": "word_wrap"})

        if len(window.get_layout()["cols"]) != 3 or window.get_layout()["cols"][1] >= 0.89:
            window.set_layout(
                {
                    "cols": [0, self.ruler_opd_panel, 1],
                    "rows": [0, 1],
                    "cells": [[0, 0, 1, 1], [1, 0, 2, 1]],
                }
            )

        window.set_view_index(dbg_view, 1, 0)
        window.focus_view(view)
        window.focus_view(dbg_view)

        dbg_view.set_syntax_file(TEST_SYNTAX_RESOURCE)
        dbg_view.set_name(os.path.split(view.file_name())[-1] + " -run")
        dbg_view.run_command("set_setting", {"setting": "fold_buttons", "value": False})
        dbg_view.run_command(
            "test_manager",
            {
                "action": "make_opd",
                "build_sys": file_syntax,
                "run_file": view.file_name(),
                "clr_tests": clr_tests,
                "sync_out": sync_out,
                "code_view_id": view.id(),
                "use_debugger": use_debugger,
            },
        )

    def close_opds(self):
        window = self.view.window()
        tied_id = self.tied_dbg.id() if self.have_tied_dbg else None
        for view in window.views():
            if view.id() == tied_id:
                continue
            if view.name()[::-1][: len("-run")][::-1] == "-run":
                view.close()

    def get_var_value(self, pos=None):
        view = self.view
        point = view.sel()[0].begin() if pos is None else pos
        var_name = view.substr(view.word(point))
        if self.have_tied_dbg:
            self.tied_dbg.run_command(
                "test_manager",
                {"action": "redirect_var_value", "var_name": var_name, "pos": point},
            )

    def show_frames(self, frames=None):
        view = self.view
        if not self.have_tied_dbg:
            status_message("status.nothing_to_show")
            return

        dbg_view = self.tied_dbg
        if not frames:
            dbg_view.run_command("test_manager", {"action": "redirect_frames"})
            return

        frames = ast.literal_eval(frames)

        def on_select(idx):
            view.erase_regions("highlight")
            if idx == -1:
                return
            point = view.text_point(int(frames[idx]["line"]) - 1, 0)
            view.show_at_center(point)
            view.sel().clear()
            view.sel().add(view.line(point))
            view.run_command("debug_overlay", {"action": "show_crash_line", "crash_line": int(frames[idx]["line"])})
            dbg_view.run_command("test_manager", {"action": "select_frame", "frame_id": idx})

        def on_highlight(idx, frames=frames):
            point = view.text_point(int(frames[idx]["line"]) - 1, 0)
            view.show_at_center(point)
            view.add_regions("highlight", [view.line(point)], "variable.c++", "dot", sublime.HIDDEN)

        show_frame_quick_panel(view, frames, on_select, on_highlight)

    def show_var_value(self, value, pos=None):
        show_var_popup(self.view, value, pos, get_highlight_function())

    def toggle_using_debugger(self):
        self.use_debugger ^= 1
        status_message("status.debugger_enabled" if self.use_debugger else "status.debugger_disabled")

    def run(
        self,
        edit,
        action=None,
        clr_tests=False,
        text=None,
        sync_out=True,
        crash_line=None,
        value=None,
        pos=None,
        frames=None,
        use_debugger=False,
    ):
        view = self.view
        if action == "insert":
            view.insert(edit, view.sel()[0].begin(), text)
        elif action == "make_opd":
            if "OPDebugger" in (view.settings().get("syntax") or ""):
                view.run_command(
                    "test_manager",
                    {"action": "make_opd", "load_session": True, "use_debugger": use_debugger},
                )
            else:
                self.close_opds()
                self.create_opd(clr_tests=clr_tests, sync_out=sync_out, use_debugger=use_debugger)
        elif action == "show_crash_line":
            point = view.text_point(crash_line - 1, 0)
            view.erase_regions("crash_line")
            view.add_regions(
                "crash_line",
                [sublime.Region(point, point)],
                "variable.language.python",
                ARROW_RIGHT_ICON_RESOURCE,
                sublime.DRAW_SOLID_UNDERLINE,
            )
            sublime.set_timeout_async(lambda point=point: view.show_at_center(point), 39)
        elif action == "get_var_value":
            self.get_var_value(pos=pos)
        elif action == "show_var_value":
            self.show_var_value(value, pos=pos)
        elif action == "show_frames":
            self.show_frames(frames=frames)
        elif action == "toggle_using_debugger":
            self.toggle_using_debugger()
        elif action == "sync_opdebugs":
            window = view.window()
            layout = window.get_layout()
            if len(layout["cols"]) == 3:
                if layout["cols"][1] != 1:
                    self.ruler_opd_panel = min(layout["cols"][1], 0.93)
                    layout["cols"][1] = 1
                else:
                    layout["cols"][1] = self.ruler_opd_panel
                window.set_layout(layout)
