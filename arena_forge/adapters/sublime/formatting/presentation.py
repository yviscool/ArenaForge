from __future__ import annotations

import platform
from typing import Optional

import sublime

from arena_forge.formatting.adapters.base import FormatterAdapter
from arena_forge.formatting.core.contracts import ExecutableDiscovery, FormatRequest, FormatResult
from arena_forge.formatting.core.settings import load_runtime_settings

from ..shared.messages import translate
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
    timeout = "disabled" if request is None or request.timeout_ms <= 0 else f"{request.timeout_ms} ms"
    lines = [
        translate("command.format_diagnose"),
        "",
        f"{translate('diagnostic.file')}: {view.file_name() or '<unsaved>'}",
        f"{translate('diagnostic.syntax')}: {view.settings().get('syntax') or '<unknown>'}",
        f"{translate('diagnostic.matched_adapter')}: {adapter.id if adapter else '<none>'}",
        f"{translate('diagnostic.selector_candidates')}: {', '.join(selectors) if selectors else '<none>'}",
        f"{translate('diagnostic.base_directory')}: {_resolve_base_dir(view) or '<none>'}",
        f"{translate('diagnostic.selections')}: {len(view.sel())} total / {len(non_empty)} non-empty",
        "",
    ]
    if request:
        lines.extend(
            (
                f"{translate('diagnostic.executable')}: {request.executable}",
                f"{translate('diagnostic.executable_source')}: {request.executable_source or '<unknown>'}",
                f"{translate('diagnostic.command')}: {' '.join(request.command)}",
                f"{translate('diagnostic.working_directory')}: {request.cwd or '<none>'}",
                f"{translate('diagnostic.stdin_filename')}: {request.stdin_filename or '<none>'}",
                f"{translate('diagnostic.selection_mode')}: {request.selection_mode}",
                f"{translate('diagnostic.selection_ranges')}: {len(request.ranges)}",
                f"{translate('diagnostic.timeout')}: {timeout}",
                f"{translate('diagnostic.config_file')}: {request.config_path or '<none detected>'}",
            )
        )
    elif executable_info and executable_info.executable:
        lines.extend(
            (
                f"{translate('diagnostic.executable')}: {executable_info.executable}",
                f"{translate('diagnostic.executable_source')}: {executable_info.source or '<unknown>'}",
            )
        )
    if executable_info:
        lines.extend(("", translate("diagnostic.search_log")))
        for item in executable_info.searched:
            lines.append(f"  {item}")
    if error:
        lines.extend(("", f"{translate('diagnostic.error')}: {error}"))
    return "\n".join(lines)


def _render_install_guide(
    adapter: FormatterAdapter,
    executable_info: Optional[ExecutableDiscovery],
) -> str:
    lines = [
        translate("formatting.install_guide_title", adapter=adapter.display_name),
        "",
        adapter.build_install_help(platform.system(), translate=translate),
    ]
    if executable_info:
        lines.extend(("", translate("diagnostic.search_log")))
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
    return translate("result.exit_code", adapter=result.request.adapter_name, returncode=result.returncode)


def _failure_panel_content(result: FormatResult, message: str) -> str:
    lines = [
        translate("result.failed", adapter=result.request.adapter_name),
        "",
        f"{translate('diagnostic.command')}: {' '.join(result.request.command)}",
        f"{translate('diagnostic.working_directory')}: {result.request.cwd or '<none>'}",
        f"{translate('diagnostic.executable_source')}: {result.request.executable_source or '<unknown>'}",
        f"{translate('diagnostic.elapsed')}: {result.elapsed_ms} ms",
        "",
        message,
    ]
    stdout = result.stdout.strip()
    stderr = result.stderr.strip()
    if stdout:
        lines.extend(("", f"{translate('diagnostic.stdout')}:", stdout))
    if stderr and stderr != message:
        lines.extend(("", f"{translate('diagnostic.stderr')}:", stderr))
    return "\n".join(lines)
