from __future__ import annotations

import importlib
import sys
import types
from contextlib import contextmanager
from pathlib import Path

import pytest

from arena_forge.formatting.adapters.java import GoogleJavaFormatAdapter
from arena_forge.formatting.adapters.kotlin import KtfmtAdapter
from arena_forge.formatting.core.contracts import FormatRequest, RuntimeSettings
from arena_forge.formatting.core.discovery import clear_discovery_caches


class _FakeRegion:
    def __init__(self, a: int, b: int) -> None:
        self.a = a
        self.b = b

    def begin(self) -> int:
        return self.a

    def end(self) -> int:
        return self.b

    def empty(self) -> bool:
        return self.a == self.b


class _FakeSettings:
    def __init__(self, syntax: str) -> None:
        self._syntax = syntax

    def get(self, key: str, default: object = None) -> object:
        if key == "syntax":
            return self._syntax
        return default


class _FakeView:
    def __init__(self, path: Path, text: str, syntax: str) -> None:
        self._path = path
        self._text = text
        self._settings = _FakeSettings(syntax)
        self._selection = [_FakeRegion(0, 0)]
        self.commands = []

    def buffer_id(self) -> int:
        return 1

    def change_count(self) -> int:
        return 1

    def file_name(self) -> str:
        return str(self._path)

    def name(self) -> None:
        return None

    def settings(self) -> _FakeSettings:
        return self._settings

    def sel(self) -> list[_FakeRegion]:
        return self._selection

    def size(self) -> int:
        return len(self._text)

    def substr(self, region: _FakeRegion) -> str:
        return self._text[region.a : region.b]

    def window(self) -> None:
        return None

    def run_command(self, name: str, args: dict[str, object] | None = None) -> None:
        self.commands.append((name, args or {}))


@contextmanager
def _patched_request_builder_module():
    original_sublime = sys.modules.get("sublime")
    original_sublime_plugin = sys.modules.get("sublime_plugin")
    fake_sublime = types.SimpleNamespace(
        Region=_FakeRegion,
        status_message=lambda _message: None,
        set_timeout=lambda callback, *_args, **_kwargs: callback(),
        set_timeout_async=lambda callback, *_args, **_kwargs: callback(),
    )
    fake_sublime_plugin = types.SimpleNamespace(
        TextCommand=object,
        WindowCommand=object,
        EventListener=object,
    )
    sys.modules["sublime"] = fake_sublime
    sys.modules["sublime_plugin"] = fake_sublime_plugin
    sys.modules.pop("arena_forge.adapters.sublime.formatting.request_builder", None)
    try:
        yield importlib.import_module("arena_forge.adapters.sublime.formatting.request_builder")
    finally:
        sys.modules.pop("arena_forge.adapters.sublime.formatting.request_builder", None)
        if original_sublime is None:
            sys.modules.pop("sublime", None)
        else:
            sys.modules["sublime"] = original_sublime
        if original_sublime_plugin is None:
            sys.modules.pop("sublime_plugin", None)
        else:
            sys.modules["sublime_plugin"] = original_sublime_plugin


@contextmanager
def _patched_formatting_commands_module():
    original_sublime = sys.modules.get("sublime")
    original_sublime_plugin = sys.modules.get("sublime_plugin")
    timeout_callbacks = []
    async_callbacks = []

    fake_sublime = types.SimpleNamespace(
        Region=_FakeRegion,
        status_message=lambda _message: None,
        set_timeout=lambda callback, *_args, **_kwargs: timeout_callbacks.append(callback),
        set_timeout_async=lambda callback, *_args, **_kwargs: async_callbacks.append(callback),
    )
    fake_sublime_plugin = types.SimpleNamespace(
        TextCommand=object,
        WindowCommand=object,
        EventListener=object,
    )
    sys.modules["sublime"] = fake_sublime
    sys.modules["sublime_plugin"] = fake_sublime_plugin
    sys.modules.pop("arena_forge.adapters.sublime.formatting.commands", None)
    try:
        module = importlib.import_module("arena_forge.adapters.sublime.formatting.commands")
        yield module, timeout_callbacks, async_callbacks
    finally:
        sys.modules.pop("arena_forge.adapters.sublime.formatting.commands", None)
        if original_sublime is None:
            sys.modules.pop("sublime", None)
        else:
            sys.modules["sublime"] = original_sublime
        if original_sublime_plugin is None:
            sys.modules.pop("sublime_plugin", None)
        else:
            sys.modules["sublime_plugin"] = original_sublime_plugin


def _make_text_command(command_cls: type, view: object):
    command = object.__new__(command_cls)
    command.view = view
    return command


@pytest.mark.parametrize(
    ("adapter", "relative_source", "source_text", "syntax", "relative_jar"),
    (
        (
            GoogleJavaFormatAdapter(),
            Path("src/Main.java"),
            "class Main {}\n",
            "Packages/Java/Java.sublime-syntax",
            Path("tools/google-java-format.jar"),
        ),
        (
            KtfmtAdapter(),
            Path("src/Main.kt"),
            'fun main() = println("hi")\n',
            "Packages/Kotlin/Kotlin.sublime-syntax",
            Path("tools/ktfmt.jar"),
        ),
    ),
)
def test_build_request_uses_project_local_jvm_formatter_jar(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    adapter,
    relative_source: Path,
    source_text: str,
    syntax: str,
    relative_jar: Path,
) -> None:
    project = tmp_path / "project"
    source_path = project / relative_source
    source_path.parent.mkdir(parents=True)
    source_path.write_text(source_text, encoding="utf-8")
    jar_path = project / relative_jar
    jar_path.parent.mkdir(parents=True, exist_ok=True)
    jar_path.write_text("placeholder", encoding="utf-8")

    clear_discovery_caches()
    with _patched_request_builder_module() as module:
        monkeypatch.setattr(module, "load_runtime_settings", lambda _view: RuntimeSettings())
        monkeypatch.setattr(
            module,
            "_select_adapter",
            lambda _view, _selector_overrides: (adapter, adapter.selectors),
        )

        request, executable_info, error = module._build_request(
            _FakeView(source_path, source_text, syntax),
            "document",
        )

    clear_discovery_caches()
    assert error is None
    assert request is not None
    assert executable_info is not None
    assert request.command_prefix == (str(jar_path),)
    assert request.command == ("java", "-jar", str(jar_path), "-")
    assert request.executable == "java"
    assert request.executable_source == "project-local"
    assert executable_info.executable == str(jar_path)
    assert executable_info.source == "project-local"


def test_save_path_is_sync_and_manual_path_is_async(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project = tmp_path / "project"
    source_path = project / "main.py"
    source_path.parent.mkdir(parents=True)
    source_path.write_text("print('hi')\n", encoding="utf-8")
    view = _FakeView(source_path, "print('hi')\n", "Packages/Python/Python.sublime-syntax")

    with _patched_formatting_commands_module() as (module, timeout_callbacks, async_callbacks):
        request = FormatRequest(
            adapter_id="ruff",
            adapter_name="Ruff Formatter",
            executable="ruff",
            command_prefix=("ruff",),
            command=("ruff", "format", "-"),
            cwd=str(project),
            stdin_filename=str(source_path),
            config_path=None,
            selection_mode="document",
            ranges=(),
            snapshot=types.SimpleNamespace(
                buffer_id=1,
                change_count=1,
                text="print('hi')\n",
                file_name=str(source_path),
                syntax="Packages/Python/Python.sublime-syntax",
                base_dir=str(project),
                newline="\n",
                selection_regions=((0, 0),),
            ),
            timeout_ms=1000,
        )
        fake_result = types.SimpleNamespace(
            request=request,
            returncode=0,
            stdout="print('hi')\n",
            stderr="",
            elapsed_ms=8,
            timed_out=False,
            system_error=None,
            ok=True,
        )

        monkeypatch.setattr(module, "load_runtime_settings", lambda _view: RuntimeSettings(format_on_save=True))
        monkeypatch.setattr(module, "_build_request", lambda _view, _mode: (request, None, None))
        monkeypatch.setattr(module, "_execute_request", lambda _request: fake_result)

        command = _make_text_command(module.ArenaForgeFormatCommand, view)
        command.run(None, mode="document", trigger="save")

        assert view.commands and view.commands[0][0] == "arena_forge_format_apply_result"
        assert not timeout_callbacks
        assert not async_callbacks

        manual = _make_text_command(module.ArenaForgeFormatCommand, view)
        manual.run(None, mode="document", trigger="manual")
        assert len(async_callbacks) == 1
