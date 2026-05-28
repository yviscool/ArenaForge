import importlib
import sys
import types
import unittest
from contextlib import contextmanager


class _FakeView:
    def __init__(self, file_name: str, content: str) -> None:
        self._file_name = file_name
        self._content = content

    def size(self) -> int:
        return len(self._content)

    def substr(self, region) -> str:
        del region
        return self._content

    def file_name(self) -> str:
        return self._file_name


@contextmanager
def _patched_sublime():
    original_sublime = sys.modules.get("sublime")
    original_sublime_plugin = sys.modules.get("sublime_plugin")
    fake_sublime = types.SimpleNamespace(
        Region=lambda begin, end: (begin, end),
        platform=lambda: "windows",
        set_timeout=lambda callback, delay=0: callback(),
        set_timeout_async=lambda callback, delay=0: callback(),
    )
    fake_sublime_plugin = types.SimpleNamespace(TextCommand=object)
    sys.modules["sublime"] = fake_sublime
    sys.modules["sublime_plugin"] = fake_sublime_plugin
    sys.modules.pop("arena_forge.adapters.sublime.contest_commands", None)
    try:
        yield
    finally:
        sys.modules.pop("arena_forge.adapters.sublime.contest_commands", None)
        if original_sublime is None:
            sys.modules.pop("sublime", None)
        else:
            sys.modules["sublime"] = original_sublime
        if original_sublime_plugin is None:
            sys.modules.pop("sublime_plugin", None)
        else:
            sys.modules["sublime_plugin"] = original_sublime_plugin


class ContestCommandsTests(unittest.TestCase):
    def test_submit_current_view_dispatches_submission_request(self) -> None:
        with _patched_sublime():
            module = importlib.import_module("arena_forge.adapters.sublime.contest_commands")
            requests = []
            statuses = []
            app = types.SimpleNamespace(
                profiles=(),
                session_service=types.SimpleNamespace(
                    ensure_session=lambda source_file, profiles: types.SimpleNamespace(language="cpp")
                ),
                submission_service=types.SimpleNamespace(submit=requests.append),
            )
            module.get_application = lambda: app
            module.product_status_message = lambda key, **kwargs: statuses.append((key, kwargs))
            module.product_log_message = lambda *args, **kwargs: None

            command = module.ContestHandlerCommand.__new__(module.ContestHandlerCommand)
            command.view = _FakeView(r"C:\contest\A.cpp", "print(42)\n")
            command._read_contest_settings = lambda: {"provider": "codeforces", "contestID": "1000"}

            command._submit_current_view()

            self.assertEqual(len(requests), 1)
            request = requests[0]
            self.assertEqual(request.provider_name, "codeforces")
            self.assertEqual(request.contest_id, "1000")
            self.assertEqual(request.problem_id, "A")
            self.assertEqual(request.language_name, "cpp")
            self.assertEqual(request.code, "print(42)\n")
            self.assertEqual(
                statuses,
                [
                    ("status.submitting", {"provider": "codeforces"}),
                    ("status.submission_complete", {"provider": "codeforces"}),
                ],
            )


if __name__ == "__main__":
    unittest.main()
