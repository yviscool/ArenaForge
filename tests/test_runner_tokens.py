import subprocess
import sys
import unittest

from arena_forge.adapters.runners.subprocess_runner import (
    build_command_argv,
    build_process_spawn_options,
    build_process_text_options,
)


class RunnerTokenTests(unittest.TestCase):
    def test_windows_quoted_paths_are_unwrapped(self) -> None:
        command = r'"C:\Users\Administrator\Desktop\A.exe" arg1 arg2'
        self.assertEqual(
            build_command_argv(command, platform_name="windows"),
            [r"C:\Users\Administrator\Desktop\A.exe", "arg1", "arg2"],
        )

    def test_windows_process_spawn_options_hide_console_window(self) -> None:
        options = build_process_spawn_options("windows")
        self.assertIsNotNone(options["startupinfo"])
        self.assertGreaterEqual(options["creationflags"], 0)
        self.assertIsNone(options["preexec_fn"])

    def test_text_options_decode_utf8_process_output(self) -> None:
        prompt = "\u8bf7\u8f93\u5165\u6b63\u6574\u6570:"
        process = subprocess.Popen(
            [
                sys.executable,
                "-c",
                f"import sys; sys.stdout.buffer.write({prompt!r}.encode('utf-8')); sys.stdout.flush()",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            **build_process_text_options("windows"),
        )
        self.addCleanup(lambda: process.poll() is None and process.kill())
        self.addCleanup(lambda: process.stdout is not None and process.stdout.close())
        first = process.stdout.read(1)
        rest = process.stdout.read()
        process.wait(timeout=5)
        self.assertEqual((first or "") + (rest or ""), prompt)


if __name__ == "__main__":
    unittest.main()
