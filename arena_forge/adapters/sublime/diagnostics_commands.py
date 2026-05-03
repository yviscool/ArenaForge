from __future__ import annotations

import re
from os import path
from subprocess import PIPE, STDOUT, Popen

import sublime
import sublime_plugin

from arena_forge.adapters.runners.subprocess_runner import build_command_argv, build_process_spawn_options

from .messages import product_log_message, status_message, translate
from .settings_bridge import get_settings, is_lang_view

ROOT_DIR = path.dirname(path.dirname(path.dirname(path.dirname(__file__))))
CMP_SENSE_RUN_FILE = path.join(ROOT_DIR, "cmp_sense", "amin.cpp")
ERROR_PATTERN = re.compile(r"(:)(\d+)(:)(\d+)(:)( *)([a-zA-Z ]+)(:)( *)(.*)")


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

    def parse_cpp_errors_smart(self, output, run_file_path):
        errors = []
        for line in output.splitlines():
            if not line.startswith(run_file_path):
                continue
            match = ERROR_PATTERN.match(line[len(run_file_path) :])
            if match is None:
                continue
            row, column, error_type, error_string = match.group(2, 4, 7, 10)
            y, x = int(row), int(column)
            errors.append(
                {
                    "type": "error" if error_type.strip() == "fatal error" else error_type.strip(),
                    "position": (y - 1, x),
                    "error_string": error_string.strip(),
                }
            )
        return errors

    def insert_error_marks(self):
        view = self.view
        source = view.substr(sublime.Region(0, view.size()))
        with open(CMP_SENSE_RUN_FILE, "wb") as handle:
            handle.write(source.encode())
        file_dir_path = path.split(view.file_name())[0]
        cmd = self.get_compile_cmd().format(source_file=CMP_SENSE_RUN_FILE, source_file_dir=file_dir_path)
        spawn_options = build_process_spawn_options(sublime.platform())
        process = Popen(
            build_command_argv(cmd, platform_name=sublime.platform()),
            shell=False,
            stdin=PIPE,
            stdout=PIPE,
            stderr=STDOUT,
            startupinfo=spawn_options["startupinfo"],
            creationflags=spawn_options["creationflags"],
        )
        output = process.communicate()[0].decode()
        view.erase_regions("warning_marks")
        view.erase_regions("error_marks")
        try:
            errors = self.parse_cpp_errors_smart(output, CMP_SENSE_RUN_FILE)
        except Exception:
            product_log_message("error.parse_errors_failed")
            return 0

        for x in errors:
            if x["type"] == "error":
                view.set_status(
                    "compile_error",
                    translate(
                        "status.compile_issue",
                        line=x["position"][0] + 1,
                        column=x["position"][1],
                        message=x["error_string"],
                    ),
                )
                break
        else:
            for x in errors:
                if x["type"] == "warning":
                    view.set_status(
                        "compile_error",
                        translate(
                            "status.compile_issue",
                            line=x["position"][0] + 1,
                            column=x["position"][1],
                            message=x["error_string"],
                        ),
                    )
                    break
            else:
                view.erase_status("compile_error")

        warn_regions = []
        error_regions = []
        for x in errors:
            pt = view.text_point(*x["position"])
            if x["type"] == "warning":
                warn_regions.append(view.word(pt))
            elif x["type"] == "error":
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
