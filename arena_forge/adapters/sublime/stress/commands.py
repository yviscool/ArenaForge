from __future__ import annotations

from dataclasses import dataclass
from os import path
from random import randint
from subprocess import TimeoutExpired

import sublime
import sublime_plugin

from arena_forge.adapters.runners import ProcessManager

from ..shared.messages import error_message, status_message
from ..shared.package_resources import STRESS_SYNTAX_RESOURCE
from ..shared.settings_bridge import get_settings


@dataclass(frozen=True)
class StressRunResult:
    success: bool
    output: str
    error_message: str


class StressManagerCommand(sublime_plugin.TextCommand):
    def provide_stress(self):
        view = self.view
        status_message("status.stressing_test", test_id=self.test_id)
        view.set_name("Stress: Test #" + str(self.test_id))
        result = self.start_test()
        self.test_id += 1
        if result["success"]:
            if not self.stop_stress:
                sublime.set_timeout_async(self.provide_stress)
            else:
                status_message("status.stress_stopped")

    def perform_run(self, process, input_text, tl) -> StressRunResult:
        process.run()
        try:
            outs, errs = process.communicate(input_text, timeout=tl)
            if process.is_stopped() != 0:
                return StressRunResult(
                    success=False,
                    output="",
                    error_message=process.file + ": crashed with exit code: %d" % process.is_stopped(),
                )
            return StressRunResult(success=True, output=outs, error_message="")
        except TimeoutExpired:
            process.terminate()
            return StressRunResult(
                success=False,
                output="",
                error_message=process.file + ": time limit exceeded (%d seconds)" % tl,
            )

    def _print_log(self, test_data, good_output, bad_output):
        text = "test #{test_id}:\n{test_data}\ngood:\n{good_output}\nbad:\n{bad_output}".format(
            test_id=self.test_id,
            test_data=self.shift_right(test_data),
            good_output=self.shift_right(good_output),
            bad_output=self.shift_right(bad_output),
        )
        self.view.run_command("stress_manager", {"action": "append_result", "text": text + "\n\n"})

    def start_test(self):
        seed = str(randint(0, int(1e9)))
        tl = get_settings().get("stress_time_limit_seconds")

        gen_result = self.perform_run(self.process["gen"], seed, tl)
        if not gen_result.success:
            self._print_log(gen_result.error_message, "", "")
            return {"success": False, "input": seed, "message": gen_result.error_message, "output": ""}

        test_data = gen_result.output
        self._print_log(test_data, "", "")

        good_result = self.perform_run(self.process["good"], test_data, tl)
        bad_result = self.perform_run(self.process["bad"], test_data, tl)

        good_output = good_result.output or good_result.error_message
        bad_output = bad_result.output or bad_result.error_message
        err = not good_result.success or not bad_result.success

        self._print_log(test_data, good_output, bad_output)

        resp = {
            "test_data": test_data,
            "good_output": good_output,
            "bad_output": bad_output,
            "log": True,
            "crash": False,
        }
        if good_output.strip() != bad_output.strip():
            resp["success"] = False
        else:
            resp["success"] = not err
        return resp

    def shift_right(self, s):
        return "\t" + s.replace("\n", "\n\t")

    def _print_compile_results(self, results):
        text = ""
        for key in self.process:
            text += self.process[key].file + ":" + "\n" + self.shift_right(results[key]) + "\n"
        self.view.run_command("stress_manager", {"action": "replace_result", "text": text})

    def _compile(self):
        results = {"gen": "compiling", "good": "compiling", "bad": "compiling"}
        self._print_compile_results(results)
        ce = False
        for key in self.process:
            p = self.process[key]
            _result = p.compile()
            if _result is None:
                code, s = 0, ""
            else:
                code, s = _result[0], _result[1]

            if code:
                ce = True
            results[key] = s if s else "compiled"
            self._print_compile_results(results)

        if not ce:
            self.test_id = 1
            sublime.set_timeout_async(self.provide_stress, 100)

    def run(self, edit, action=None, text="", file=None):
        view = self.view
        window = view.window()
        if action == "make_stress":
            stress_view = window.new_file()
            stress_view.run_command("stress_manager", {"action": "init", "file": view.file_name()})
            return

        if action == "init":
            view.set_name("Stress: Compile")
            view.set_syntax_file(STRESS_SYNTAX_RESOURCE)
            view.set_scratch(True)
            view.run_command("set_setting", {"setting": "line_numbers", "value": False})
            base_dir = path.dirname(file)
            task_name = path.splitext(path.split(file)[1])[0]

            def find_source(base_dir, name, run_settings):
                found = None
                for lang in run_settings:
                    for ext in lang["extensions"]:
                        src = path.join(base_dir, name + "." + ext)
                        if path.exists(src):
                            if found:
                                return [found, src]
                            found = src
                return found

            bad_source = file
            good_source = find_source(base_dir, task_name + "__Good", get_settings().get("run_settings"))
            gen_source = find_source(base_dir, task_name + "__Generator", get_settings().get("run_settings"))

            if not good_source:
                error_message("error.file_not_found", file=task_name + "__Good")
                return
            if not gen_source:
                error_message("error.file_not_found", file=task_name + "__Generator")
                return
            if isinstance(good_source, list):
                error_message("error.conflict_files", files=" and ".join(good_source))
                return
            if isinstance(gen_source, list):
                error_message("error.conflict_files", files=" and ".join(gen_source))
                return

            def check_exist(source):
                if not path.exists(source):
                    error_message("error.file_not_found", file=source)
                    return False
                return True

            if check_exist(good_source) and check_exist(bad_source) and check_exist(gen_source):
                self.process = {
                    "good": ProcessManager(good_source, None, run_settings=get_settings().get("run_settings")),
                    "bad": ProcessManager(bad_source, None, run_settings=get_settings().get("run_settings")),
                    "gen": ProcessManager(gen_source, None, run_settings=get_settings().get("run_settings")),
                }
                self.stop_stress = False
                sublime.set_timeout_async(self._compile)
            return

        if action == "provide_stress":
            self.provide_stress()
        elif action == "stop_stress":
            self.stop_stress = True
        elif action == "replace_result":
            view.replace(edit, sublime.Region(0, view.size()), text)
            view.sel().clear()
        elif action == "append_result":
            view.insert(edit, view.size(), text)
            view.sel().clear()


class StressListener(sublime_plugin.EventListener):
    def on_close(self, view):
        if "StressSyntax" in (view.settings().get("syntax") or ""):
            view.run_command("stress_manager", {"action": "stop_stress"})
