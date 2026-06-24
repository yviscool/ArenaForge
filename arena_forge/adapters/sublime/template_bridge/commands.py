from __future__ import annotations

from os import listdir, path
from os.path import dirname

import sublime
import sublime_plugin
from sublime import Region

from ..shared.settings_bridge import (
    default_settings_file,
    get_algorithm_properties_path,
    get_settings,
    is_run_supported_ext,
    root_dir,
    settings_file,
)
from ..root_bridge import get_template_generator

gen_template = get_template_generator()


class TemplateBridgeCommand(sublime_plugin.TextCommand):
    ROOT = dirname(__file__)

    def run(self, edit, action=None, clr_tests=False, text=None, sync_out=True, reselect=False, smart_fold=False):
        view = self.view

        if action == "insert":
            if reselect:
                view.replace(edit, view.sel()[0], text)
                view.unfold(view.sel()[0])
                if smart_fold:
                    row_high, col = view.rowcol(view.sel()[0].b)
                    row_low, _ = view.rowcol(view.sel()[0].a)
                    row_high = min(row_high, row_low + 15)
                    view.fold(Region(view.text_point(row_high, col), view.sel()[0].b))
            else:
                view.insert(edit, view.sel()[0].begin(), text)
            return

        if action == "insert_template":
            word_selection = view.word(view.sel()[0])
            func = view.substr(view.word(word_selection)).strip()
            insert_snippet = get_settings().get("algorithms_base") and path.isfile(
                path.join(root_dir, get_settings().get("algorithms_base"), func + ".cpp")
            )
            if insert_snippet:
                snippet_file = path.join(root_dir, get_settings().get("algorithms_base"), func + ".cpp")
                with open(snippet_file, encoding="utf-8") as handle:
                    view.replace(edit, word_selection, handle.read())
                prop_path = get_algorithm_properties_path(snippet_file)
                if path.isfile(prop_path):
                    with open(prop_path, "r", encoding="utf-8") as handle:
                        prop = sublime.decode_value(handle.read())
                    if prop.get("fold") is not None:
                        for region in prop["fold"]:
                            view.fold(Region(word_selection.a + region[0], word_selection.a + region[1]))
                    if prop.get("move_cursor") is not None:
                        view.show_at_center(word_selection.a + prop["move_cursor"])
                        view.sel().clear()
                        view.sel().add(Region(word_selection.a + prop["move_cursor"], word_selection.a + prop["move_cursor"]))
            else:
                view.run_command("insert_best_completion", {"exact": False, "default": "\t"})
            return

        if action == "show_funcs":
            wind = view.window()

            def collect_all(base, entries, codes, prefix=""):
                for file in listdir(base):
                    current = path.join(base, file)
                    if path.isfile(current):
                        if file.endswith(".cpp"):
                            entries.append(prefix + "/" + file)
                            codes.append(current)
                    elif path.isdir(current) and file != ".git":
                        entries.append(prefix + "/" + file + " ->")
                        codes.append(current)
                        collect_all(current, entries, codes, prefix="\t" + prefix + ("/" if prefix else "*") + file)

            entries, codes = [], []
            collect_all(path.join(root_dir, get_settings().get("algorithms_base")), entries, codes)

            def on_done(ind, initial=view.substr(view.sel()[0])):
                if ind == -1:
                    self.view.run_command("template_bridge", {"text": initial, "action": "insert", "reselect": True})

            def on_highlight(ind, codes=codes, view=view):
                if path.isfile(codes[ind]):
                    with open(codes[ind], "r", encoding="utf-8") as handle:
                        code = handle.read()
                    view.run_command("template_bridge", {"text": code, "action": "insert", "reselect": True, "smart_fold": True})

            wind.show_quick_panel(entries, on_done, 1, 0, on_highlight)
            return

        if action == "open_settings":
            view.window().run_command("new_window")
            sublime.active_window().set_sidebar_visible(False)
            sublime.active_window().open_file(path.join(root_dir, default_settings_file))
            sublime.active_window().set_layout({"cols": [0, 0.5, 1], "rows": [0, 1], "cells": [[0, 0, 1, 1], [1, 0, 2, 1]]})
            options_path = path.join(sublime.packages_path(), "User", settings_file)
            if not path.exists(options_path):
                with open(options_path, "w", encoding="utf-8") as handle:
                    handle.write("{\n\t\n}")
            options_view = sublime.active_window().open_file(options_path)
            sublime.active_window().set_view_index(options_view, 1, 0)


class TemplateCompletionListener(sublime_plugin.EventListener):
    def try_expand(self, prefix):
        config = get_settings().get("cpp_complete_settings")
        if config is None:
            return None
        return gen_template(prefix, config)

    def on_text_command(self, view, command_name, args):
        if command_name == "debug_overlay":
            ext = path.splitext(view.file_name())[1][1:]
            if args["action"] == "make_opd":
                if not is_run_supported_ext(ext):
                    return ("template_bridge", {"action": "pass"})
            elif args["action"] == "toggle_using_debugger":
                if ext != "cpp":
                    return ("template_bridge", {"action": "pass"})

    def on_modified(self, view):
        if not len(view.sel()) or view.scope_name(view.sel()[0].a).find("source.c") == -1:
            return
        prefix = view.substr(view.word(view.sel()[0]))
        if len(prefix) <= 1:
            return
        if self.try_expand(prefix):
            view.run_command("hide_auto_complete")

            def run():
                view.run_command(
                    "auto_complete",
                    {
                        "disable_auto_insert": True,
                        "next_completion_if_showing": False,
                        "auto_complete_commit_on_tab": True,
                    },
                )

            sublime.set_timeout(run)

    def on_query_completions(self, view, prefix, locations):
        if not get_settings().get("cpp_complete_enabled"):
            return
        if len(prefix) == 1:
            return
        expand = self.try_expand(prefix)
        if (view.scope_name(view.sel()[0].a).find("source.c") != -1) and expand:
            if prefix == expand:
                return []
            return [(prefix + "\t" + expand, expand)]
        return []
