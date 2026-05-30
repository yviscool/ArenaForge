from __future__ import annotations

import importlib
import sys
import types
from contextlib import contextmanager
from pathlib import Path

import pytest

from arena_forge.formatting.adapters.java import GoogleJavaFormatAdapter
from arena_forge.formatting.adapters.kotlin import KtfmtAdapter
from arena_forge.formatting.core.contracts import RuntimeSettings
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
