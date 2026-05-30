from __future__ import annotations

import platform
from typing import Optional

import sublime

from arena_forge.formatting.adapters.base import FormatterAdapter
from arena_forge.formatting.core.contracts import ExecutableDiscovery, FormatRequest, FormatResult
from arena_forge.formatting.core.settings import load_runtime_settings

from .request_builder import _resolve_base_dir, _select_adapter

OUTPUT_PANEL_NAME = "arena_forge_format"


def _status(message: str) -> None:
    sublime.status_message(f"ArenaForge: {message}")


def _render_diagnostic(
    view: sublime.View,
    request: Optional[FormatRequest],
    executable_info: Optional[ExecutableDiscovery],
    error: Optional[str],
) -> str:
    runtime = load_runtime_settings(view)
    adapter, selectors = _select_adapter(view, runtime.selector_overrides)
    non_empty = [region for region in view.sel() if not region.empty()]
    lines = [
        "ArenaForge Formatter Diagnose",
        "",
        f"File: {view.file_name() or '<unsaved>'}",
        f"Syntax: {view.settings().get('syntax') or '<unknown>'}",
        f"Matched adapter: {adapter.id if adapter else '<none>'}",
        f"Selector candidates: {', '.join(selectors) if selectors else '<none>'}",
        f"Base directory: {_resolve_base_dir(view) or '<none>'}",
        f"Selections: {len(view.sel())} total / {len(non_empty)} non-empty",
        "",
    ]
    if request:
        lines.extend(
            (
                f"Executable: {request.executable}",
                f"Executable source: {request.executable_source or '<unknown>'}",
                f"Command: {' '.join(request.command)}",
                f"Working directory: {request.cwd or '<none>'}",
                f"stdin filename: {request.stdin_filename or '<none>'}",
                f"Selection mode: {request.selection_mode}",
                f"Selection ranges: {len(request.ranges)}",
                f"Timeout: {'disabled' if request.timeout_ms <= 0 else f'{request.timeout_ms} ms'}",
                f"Config file: {request.config_path or '<none detected>'}",
            )
        )
    elif executable_info and executable_info.executable:
        lines.extend(
            (
                f"Executable: {executable_info.executable}",
                f"Executable source: {executable_info.source or '<unknown>'}",
            )
        )
    if executable_info:
        lines.extend(("", "Search log:"))
        for item in executable_info.searched:
            lines.append(f"  {item}")
    if error:
        lines.extend(("", f"Error: {error}"))
    return "\n".join(lines)


def _render_install_guide(
    adapter: FormatterAdapter,
    executable_info: Optional[ExecutableDiscovery],
) -> str:
    lines = [
        f"ArenaForge Formatter Install Guide: {adapter.display_name}",
        "",
        adapter.build_install_help(platform.system()),
    ]
    if executable_info:
        lines.extend(("", "Search log:"))
        for item in executable_info.searched:
            lines.append(f"  {item}")
    return "\n".join(lines)


def _show_output_panel(window: Optional[sublime.Window], content: str) -> None:
    if not window:
        return
    panel = window.create_output_panel(OUTPUT_PANEL_NAME)
    panel.run_command("arena_forge_format_render_panel", {"content": content})
    window.run_command("show_panel", {"panel": f"output.{OUTPUT_PANEL_NAME}"})


def _result_message(result: FormatResult) -> str:
    if result.system_error:
        return result.system_error
    if result.stderr.strip():
        return result.stderr.strip()
    if result.stdout.strip():
        return result.stdout.strip()
    return f"{result.request.adapter_name} exited with code {result.returncode}."


def _failure_panel_content(result: FormatResult, message: str) -> str:
    lines = [
        f"{result.request.adapter_name} failed",
        "",
        f"Command: {' '.join(result.request.command)}",
        f"Working directory: {result.request.cwd or '<none>'}",
        f"Executable source: {result.request.executable_source or '<unknown>'}",
        f"Elapsed: {result.elapsed_ms} ms",
        "",
        message,
    ]
    stdout = result.stdout.strip()
    stderr = result.stderr.strip()
    if stdout:
        lines.extend(("", "stdout:", stdout))
    if stderr and stderr != message:
        lines.extend(("", "stderr:", stderr))
    return "\n".join(lines)
