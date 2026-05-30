from __future__ import annotations

from time import time

import sublime

from arena_forge.core.services import evaluate_output_result

from ..messages import status_message


class RunPanelTester(object):
    def __init__(
        self,
        process_manager,
        on_insert,
        on_out,
        on_stop,
        on_status_change,
        sync_out=False,
        tests=None,
        test_factory=None,
        schedule_async=None,
        show_status=None,
        on_compile_error=None,
    ):
        super(RunPanelTester, self).__init__()
        self.process_manager = process_manager
        self.sync_out = sync_out
        self.tests = list(tests or [])
        self.test_factory = test_factory
        self.test_iter = 0
        self.running_test = None
        self.running_new = None
        self.on_insert = on_insert
        self.on_out = on_out
        self.on_stop = on_stop
        self.proc_run = False
        self.prog_out = []
        self.on_status_change = on_status_change
        self.schedule_async = schedule_async or sublime.set_timeout_async
        self.show_status = show_status or (lambda: status_message("status.process_already_running"))
        self.on_compile_error = on_compile_error or (lambda test_id, return_code, output_text: None)
        if type(self.process_manager).__name__ != "ProcessManager":
            self.process_manager.set_calls(self.__on_out, self.__on_stop, on_status_change)

    def _ensure_output_slot(self, index):
        while len(self.prog_out) <= index:
            self.prog_out.append("")

    def __on_stop(self, rtcode, runtime=-1, crash_line=None):
        self.prog_out[self.running_test] = self.prog_out[self.running_test].rstrip()
        self.proc_run = False

        if self.running_new:
            self.test_iter += 1

        if type(self.process_manager).__name__ == "ProcessManager":
            self.on_status_change("STOPPED")

        self.on_stop(rtcode, runtime, crash_line=crash_line)

    def __on_out(self, s):
        self.prog_out[self.running_test] += s
        self.on_out(s)

    def __process_listener(self):
        proc = self.process_manager
        start_time = time()
        while proc.is_stopped() is None:
            if self.sync_out:
                output = proc.read(bfsize=1)
            else:
                output = proc.read(bfsize=4096)
            if not output:
                continue
            self.__on_out(output)
        try:
            output = proc.read()
            self.__on_out(output)
        except (OSError, ValueError):
            pass
        runtime = int((time() - start_time) * 1000)
        self.__on_stop(proc.is_stopped(), runtime)

    def insert(self, s, call_on_insert=False):
        if self.proc_run:
            self.tests[self.running_test].append_string(s)
            self.process_manager.write(s)
            if call_on_insert:
                self.on_insert(s)

    def insert_test(self, id=None):
        if id is None:
            id = self.test_iter
        if type(self.process_manager).__name__ == "ProcessManager":
            self.on_status_change("RUNNING")

        self.proc_run = True
        self.process_manager.run()
        self.process_manager.write(self.tests[id].test_string)
        self.on_insert(self.tests[id].test_string)

    def next_test(self, tie_pos, cb):
        if self.proc_run:
            self.show_status()
            return

        if self.test_iter >= len(self.tests):
            if self.test_factory is None:
                raise RuntimeError("Test state factory unavailable")
            self.tests.append(self.test_factory(""))
        self._ensure_output_slot(self.test_iter)
        self.tests[self.test_iter].set_tie_pos(tie_pos)
        self.running_test = self.test_iter
        self.running_new = True

        def go(self=self, cb=cb):
            self.insert_test()
            if type(self.process_manager).__name__ == "ProcessManager":
                self.schedule_async(self.__process_listener)
            cb()

        self.schedule_async(go, 10)

    def run_test(self, id):
        self.on_status_change("COMPILE")
        self.running_test = id
        self.running_new = False
        self._ensure_output_slot(id)
        self.prog_out[id] = ""

        def compile_and_run():
            compile_result = self.process_manager.compile()
            if compile_result is not None and compile_result[0] != 0:
                self.prog_out[id] = compile_result[1]
                self.on_compile_error(id, compile_result[0], compile_result[1])
                return
            self.insert_test(id)
            if type(self.process_manager).__name__ == "ProcessManager":
                self.schedule_async(self.__process_listener)

        self.schedule_async(compile_and_run, 0)

    def have_pretests(self):
        return self.test_iter < len(self.tests)

    def get_tests(self):
        return self.tests

    def del_test(self, nth):
        self.test_iter -= 1
        self.tests.pop(nth)
        self.prog_out.pop(nth)

    def set_tests(self, tests, test_factory=None):
        factory = test_factory or self.test_factory
        if factory is None:
            raise RuntimeError("Test state factory unavailable")
        existing_outputs = list(self.prog_out)
        self.tests.clear()
        for test in tests:
            self.tests.append(factory(test))
        self.prog_out = [
            existing_outputs[index] if index < len(existing_outputs) else ""
            for index in range(len(self.tests))
        ]
        self.test_iter = len(self.tests)

    def del_tests(self, to_del):
        dont_add = set(to_del)
        new_tests = []
        new_out = []
        for i in range(len(self.tests)):
            if i not in dont_add:
                new_tests.append(self.tests[i])
                new_out.append(self.prog_out[i])
        self.tests = new_tests
        self.prog_out = new_out
        self.test_iter -= len(to_del)

    def accept_out(self, nth):
        if nth >= len(self.prog_out):
            return None
        self.tests[nth].add_correct_answer(self.prog_out[nth].strip())
        self.tests[nth].remove_uncorrect_answer(self.prog_out[nth].strip())

    def decline_out(self, nth):
        if nth >= len(self.prog_out):
            return None
        self.tests[nth].remove_correct_answer(self.prog_out[nth].strip())
        self.tests[nth].add_uncorrect_answer(self.prog_out[nth].strip())

    def check_test(self, nth):
        return self.tests[nth].is_correct_answer(self.prog_out[nth])

    def evaluate_test(self, nth):
        return evaluate_output_result(self.tests[nth].to_core_test_case(nth + 1), self.prog_out[nth])

    def terminate(self):
        self.process_manager.terminate()
