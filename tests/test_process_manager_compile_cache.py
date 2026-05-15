import importlib
import os
import subprocess
import sys
import tempfile
import types
import unittest
from contextlib import contextmanager
from pathlib import Path


class _FakePopen:
    calls = []
    outputs = []
    returncodes = []

    def __init__(self, argv, **kwargs):
        self.argv = tuple(argv)
        self.kwargs = kwargs
        self.returncode = self.returncodes.pop(0)
        self._output = self.outputs.pop(0)
        self.calls.append((self.argv, kwargs.get("cwd")))

    def communicate(self):
        return (self._output,)


@contextmanager
def _patched_sublime():
    original = sys.modules.get("sublime")
    sys.modules["sublime"] = types.SimpleNamespace(platform=lambda: "windows")
    sys.modules.pop("arena_forge.adapters.runners.process_manager", None)
    try:
        yield
    finally:
        sys.modules.pop("arena_forge.adapters.runners.process_manager", None)
        if original is None:
            sys.modules.pop("sublime", None)
        else:
            sys.modules["sublime"] = original


def _import_process_manager_module():
    module = importlib.import_module("arena_forge.adapters.runners.process_manager")
    module._COMPILE_CACHE.clear()
    module.build_command_argv = lambda command, platform_name=None: [command]
    module.build_process_spawn_options = lambda platform_name=None: {"startupinfo": None, "creationflags": 0}
    module.build_process_text_options = lambda platform_name=None: {}
    module.subprocess = types.SimpleNamespace(
        Popen=_FakePopen,
        PIPE=subprocess.PIPE,
        STDOUT=subprocess.STDOUT,
    )
    return module


def _make_manager(module, source_file: str, compile_cmd):
    return module.ProcessManager(
        source_file,
        None,
        run_settings=[
            {
                "extensions": ["cpp"],
                "compile_cmd": compile_cmd,
                "run_cmd": "runner",
            }
        ],
    )


class ProcessManagerCompileCacheTests(unittest.TestCase):
    def setUp(self) -> None:
        _FakePopen.calls = []
        _FakePopen.outputs = []
        _FakePopen.returncodes = []

    def test_compile_reuses_cached_result_across_process_managers(self) -> None:
        with _patched_sublime():
            module = _import_process_manager_module()
            with tempfile.TemporaryDirectory() as temp_dir:
                source_file = Path(temp_dir) / "main.cpp"
                source_file.write_text("int main() { return 0; }\n", encoding="utf-8")
                _FakePopen.outputs = ["compiled once"]
                _FakePopen.returncodes = [0]

                first = _make_manager(module, str(source_file), 'compiler "{source_file}" -o "{file_name}"')
                second = _make_manager(module, str(source_file), 'compiler "{source_file}" -o "{file_name}"')

                self.assertEqual(first.compile(), (0, "compiled once"))
                self.assertEqual(second.compile(), (0, "compiled once"))
                self.assertEqual(len(_FakePopen.calls), 1)

    def test_compile_recompiles_when_source_timestamp_changes(self) -> None:
        with _patched_sublime():
            module = _import_process_manager_module()
            with tempfile.TemporaryDirectory() as temp_dir:
                source_file = Path(temp_dir) / "main.cpp"
                source_file.write_text("int main() { return 0; }\n", encoding="utf-8")
                _FakePopen.outputs = ["first build", "second build"]
                _FakePopen.returncodes = [0, 0]

                manager = _make_manager(module, str(source_file), 'compiler "{source_file}" -o "{file_name}"')
                self.assertEqual(manager.compile(), (0, "first build"))

                source_file.write_text("int main() { return 1; }\n", encoding="utf-8")
                updated_stat = source_file.stat()
                os.utime(
                    source_file,
                    ns=(updated_stat.st_atime_ns, updated_stat.st_mtime_ns + 1_000_000_000),
                )

                reloaded = _make_manager(module, str(source_file), 'compiler "{source_file}" -o "{file_name}"')
                self.assertEqual(reloaded.compile(), (0, "second build"))
                self.assertEqual(len(_FakePopen.calls), 2)

    def test_compile_recompiles_when_rendered_command_changes(self) -> None:
        with _patched_sublime():
            module = _import_process_manager_module()
            with tempfile.TemporaryDirectory() as temp_dir:
                source_file = Path(temp_dir) / "main.cpp"
                source_file.write_text("int main() { return 0; }\n", encoding="utf-8")
                _FakePopen.outputs = ["debug build", "release build"]
                _FakePopen.returncodes = [0, 0]

                debug_manager = _make_manager(module, str(source_file), 'compiler "{source_file}" -O0')
                release_manager = _make_manager(module, str(source_file), 'compiler "{source_file}" -O2')

                self.assertEqual(debug_manager.compile(), (0, "debug build"))
                self.assertEqual(release_manager.compile(), (0, "release build"))
                self.assertEqual(len(_FakePopen.calls), 2)

    def test_compile_returns_none_without_compile_command(self) -> None:
        with _patched_sublime():
            module = _import_process_manager_module()
            with tempfile.TemporaryDirectory() as temp_dir:
                source_file = Path(temp_dir) / "main.py"
                source_file.write_text("print('hi')\n", encoding="utf-8")
                manager = module.ProcessManager(
                    str(source_file),
                    None,
                    run_settings=[
                        {
                            "extensions": ["py"],
                            "compile_cmd": None,
                            "run_cmd": "python",
                        }
                    ],
                )

                self.assertIsNone(manager.compile())
                self.assertEqual(_FakePopen.calls, [])

    def test_failed_compile_result_is_not_reused_from_cache(self) -> None:
        with _patched_sublime():
            module = _import_process_manager_module()
            with tempfile.TemporaryDirectory() as temp_dir:
                source_file = Path(temp_dir) / "main.cpp"
                source_file.write_text("int main() { return 0; }\n", encoding="utf-8")
                _FakePopen.outputs = ["compile error", "compile error again"]
                _FakePopen.returncodes = [1, 1]

                first = _make_manager(module, str(source_file), 'compiler "{source_file}" -o "{file_name}"')
                second = _make_manager(module, str(source_file), 'compiler "{source_file}" -o "{file_name}"')

                self.assertEqual(first.compile(), (1, "compile error"))
                self.assertEqual(second.compile(), (1, "compile error again"))
                self.assertEqual(len(_FakePopen.calls), 2)


if __name__ == "__main__":
    unittest.main()
