import unittest

from arena_forge.adapters.runners.subprocess_runner import build_command_argv, build_process_spawn_options


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


if __name__ == "__main__":
    unittest.main()
