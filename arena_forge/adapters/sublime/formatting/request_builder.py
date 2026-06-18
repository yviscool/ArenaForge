from __future__ import annotations

import os
from dataclasses import replace
from pathlib import Path
from typing import Dict, Optional, Tuple

import sublime

from arena_forge.formatting.adapters.base import FormatterAdapter
from arena_forge.formatting.core.contracts import (
    ExecutableDiscovery,
    FormatRequest,
    RuntimeSettings,
    ViewSnapshot,
)
from arena_forge.formatting.core.discovery import discover_executable
from arena_forge.formatting.core.registry import ADAPTERS, selectors_for_adapter
from arena_forge.formatting.core.settings import load_runtime_settings
from arena_forge.formatting.core.text import detect_newline_style, make_text_range

from ..shared.messages import translate

SelectionOffsets = Tuple[Tuple[int, int], ...]
BuildRequestResult = Tuple[Optional[FormatRequest], Optional[ExecutableDiscovery], Optional[str]]


def _resolve_base_dir(view: sublime.View) -> Optional[str]:
    file_name = view.file_name()
    if file_name:
        return str(Path(file_name).resolve().parent)

    window = view.window()
    if window and window.folders():
        return str(Path(window.folders()[0]).resolve())

    try:
        return str(Path(os.getcwd()).resolve())
    except OSError:
        return None


def _view_context_dir(view: Optional[sublime.View]) -> Optional[str]:
    if not view:
        return None
    file_name = view.file_name()
    if file_name:
        return str(Path(file_name).resolve().parent)
    window = view.window()
    if window and window.folders():
        return str(Path(window.folders()[0]).resolve())
    return None


def _snapshot_view(view: sublime.View) -> ViewSnapshot:
    text = view.substr(sublime.Region(0, view.size()))
    selections = tuple((region.a, region.b) for region in view.sel())
    return ViewSnapshot(
        buffer_id=view.buffer_id(),
        change_count=view.change_count(),
        text=text,
        file_name=view.file_name(),
        syntax=view.settings().get("syntax"),
        base_dir=_resolve_base_dir(view),
        newline=detect_newline_style(text),
        selection_regions=selections,
    )


def _guess_stdin_filename(
    view: sublime.View,
    adapter: FormatterAdapter,
    base_dir: Optional[str],
) -> Optional[str]:
    if view.file_name():
        return view.file_name()

    if view.name():
        candidate = Path(view.name())
        if candidate.suffix:
            return str((Path(base_dir or os.getcwd()) / candidate.name).resolve())

    if not base_dir:
        return None

    return str((Path(base_dir) / f"untitled{adapter.default_extension}").resolve())


def _select_adapter(
    view: sublime.View,
    selector_overrides: Dict[str, Tuple[str, ...]],
) -> Tuple[Optional[FormatterAdapter], Tuple[str, ...]]:
    point = 0
    if view.size() > 0 and len(view.sel()) > 0:
        point = min(view.sel()[0].begin(), view.size() - 1)

    for adapter in ADAPTERS:
        selectors = selectors_for_adapter(adapter, selector_overrides)
        if any(view.match_selector(point, selector) for selector in selectors):
            return adapter, selectors
    return None, ()


def _format_ranges(
    view: sublime.View,
    mode: str,
    adapter: FormatterAdapter,
) -> Tuple[SelectionOffsets, Optional[str]]:
    non_empty = [region for region in view.sel() if not region.empty()]
    if mode == "document":
        return (), None
    if mode == "selection" and not non_empty:
        return (), translate("error.no_recommended_template", syntax="selection")
    if mode == "auto" and not non_empty:
        return (), None
    if not adapter.supports_range:
        return (), translate("error.no_recommended_template", syntax=adapter.display_name)
    if len(non_empty) > 1 and not adapter.supports_multiple_ranges:
        return (), translate("error.no_recommended_template", syntax=adapter.display_name)
    return tuple((region.begin(), region.end()) for region in non_empty), None


def _command_prefix(
    adapter: FormatterAdapter,
    runtime: RuntimeSettings,
    start_dir: Optional[str],
) -> Tuple[Tuple[str, ...], ExecutableDiscovery]:
    command_override = runtime.commands.get(adapter.id)
    if command_override:
        return command_override, ExecutableDiscovery(
            executable=command_override[0],
            source="settings",
            searched=command_override,
        )

    executable_info = discover_executable(
        binary_names=adapter.binary_names,
        project_relpaths=adapter.project_binary_relpaths(),
        override=(),
        start_dir=start_dir,
    )
    if not executable_info.executable:
        return (), executable_info
    return (executable_info.executable,), executable_info


def _build_request(view: sublime.View, mode: str) -> BuildRequestResult:
    runtime = load_runtime_settings(view)
    adapter, _selectors = _select_adapter(view, runtime.selector_overrides)
    if not adapter:
        syntax = view.settings().get("syntax") or "unknown syntax"
        return None, None, translate("status.no_formatter_for_syntax", syntax=syntax)

    offset_ranges, error = _format_ranges(view, mode, adapter)
    if error:
        return None, None, error

    snapshot = _snapshot_view(view)
    ranges = tuple(make_text_range(snapshot.text, start, end) for start, end in offset_ranges)
    stdin_filename = _guess_stdin_filename(view, adapter, snapshot.base_dir)
    command_prefix, executable_info = _command_prefix(adapter, runtime, snapshot.base_dir)
    if not command_prefix:
        return None, executable_info, translate("error.no_recommended_formatter", syntax=adapter.display_name)

    selection_mode = "selection" if ranges else "document"
    request = FormatRequest(
        adapter_id=adapter.id,
        adapter_name=adapter.display_name,
        executable=command_prefix[0],
        command_prefix=command_prefix,
        command=(),
        cwd=snapshot.base_dir,
        stdin_filename=stdin_filename,
        config_path=adapter.discover_config(snapshot.base_dir),
        selection_mode=selection_mode,
        ranges=ranges,
        snapshot=snapshot,
        timeout_ms=runtime.format_timeout_ms,
        executable_source=executable_info.source,
    )
    extra_args = runtime.extra_args.get("*", ()) + runtime.extra_args.get(adapter.id, ())
    command = tuple(adapter.build_command(request, extra_args))
    executable = command[0] if command else request.executable
    return replace(request, executable=executable, command=command), executable_info, None
