from __future__ import annotations

import platform
import uuid

import sublime
import sublime_plugin

from arena_forge.formatting.core.contracts import FormatRequest, FormatResult
from arena_forge.formatting.core.process import run_subprocess
from arena_forge.formatting.core.registry import ADAPTERS
from arena_forge.formatting.core.settings import load_runtime_settings
from arena_forge.formatting.core.text import clamp_point, normalize_newlines, remap_selection_regions

from .generation import run_generation_wizard
from .presentation import (
    _failure_panel_content,
    _render_diagnostic,
    _render_install_guide,
    _result_message,
    _show_output_panel,
    _status,
)
from .request_builder import (
    _build_request,
    _command_prefix,
    _resolve_base_dir,
    _select_adapter,
    _view_context_dir,
)

PENDING_RESULTS = {}  # type: dict[str, FormatResult]


def _execute_request(request: FormatRequest) -> FormatResult:
    process_result = run_subprocess(
        request.command,
        request.snapshot.text,
        request.cwd,
        request.timeout_ms,
    )
    return FormatResult(
        request=request,
        returncode=process_result.returncode,
        stdout=process_result.stdout,
        stderr=process_result.stderr,
        elapsed_ms=process_result.elapsed_ms,
        timed_out=process_result.timed_out,
        system_error=process_result.system_error,
    )


def _schedule_apply(view: sublime.View, result: FormatResult) -> None:
    token = uuid.uuid4().hex
    PENDING_RESULTS[token] = result
    view.run_command("arena_forge_format_apply_result", {"token": token})


def _run_request_async(view: sublime.View, request: FormatRequest) -> None:
    def runner() -> None:
        result = _execute_request(request)
        sublime.set_timeout(lambda: _schedule_apply(view, result))

    sublime.set_timeout_async(runner)


class ArenaForgeFormatCommand(sublime_plugin.TextCommand):
    def run(self, edit: sublime.Edit, mode: str = "auto", trigger: str = "manual") -> None:
        del edit
        runtime = load_runtime_settings(self.view)
        request, executable_info, error = _build_request(self.view, mode)
        if error:
            _status(error)
            if executable_info and runtime.show_output_panel_on_error:
                adapter, _selectors = _select_adapter(self.view, runtime.selector_overrides)
                if adapter:
                    _show_output_panel(self.view.window(), _render_install_guide(adapter, executable_info))
            return

        if request is None:
            return

        if trigger == "save":
            _schedule_apply(self.view, _execute_request(request))
            return

        _status(f"running {request.adapter_name}...")
        _run_request_async(self.view, request)


class ArenaForgeFormatDocumentCommand(sublime_plugin.TextCommand):
    def run(self, edit: sublime.Edit) -> None:
        del edit
        self.view.run_command("arena_forge_format", {"mode": "document"})


class ArenaForgeFormatSelectionCommand(sublime_plugin.TextCommand):
    def run(self, edit: sublime.Edit) -> None:
        del edit
        self.view.run_command("arena_forge_format", {"mode": "selection"})


class ArenaForgeFormatApplyResultCommand(sublime_plugin.TextCommand):
    def run(self, edit: sublime.Edit, token: str) -> None:
        result = PENDING_RESULTS.pop(token, None)
        if not result:
            return

        if self.view.change_count() != result.request.snapshot.change_count:
            _show_output_panel(
                self.view.window(),
                "\n".join(
                    (
                        "ArenaForge Formatter",
                        "",
                        "The buffer changed before the formatter result could be applied.",
                        "The formatter output was discarded to avoid overwriting newer edits.",
                    )
                ),
            )
            return

        if not result.ok:
            runtime = load_runtime_settings(self.view)
            message = _result_message(result)
            _status(message)
            if runtime.show_output_panel_on_error:
                _show_output_panel(self.view.window(), _failure_panel_content(result, message))
            return

        formatted = normalize_newlines(result.stdout, result.request.snapshot.newline)
        if formatted == result.request.snapshot.text:
            _status(f"{result.request.adapter_name} made no changes ({result.elapsed_ms} ms).")
            return

        remapped_regions = remap_selection_regions(
            result.request.snapshot.text,
            formatted,
            result.request.snapshot.selection_regions,
        )
        self.view.replace(edit, sublime.Region(0, self.view.size()), formatted)
        size = self.view.size()
        self.view.sel().clear()
        for begin, end in remapped_regions:
            self.view.sel().add(sublime.Region(clamp_point(begin, size), clamp_point(end, size)))

        if result.stderr.strip():
            _show_output_panel(
                self.view.window(),
                "\n".join(
                    (
                        f"{result.request.adapter_name} warnings",
                        "",
                        f"Elapsed: {result.elapsed_ms} ms",
                        "",
                        result.stderr.strip(),
                    )
                ),
            )
        _status(f"formatted with {result.request.adapter_name} ({result.elapsed_ms} ms).")


class ArenaForgeFormatDiagnoseCommand(sublime_plugin.WindowCommand):
    def run(self) -> None:
        view = self.window.active_view()
        if not view:
            return
        request, executable_info, error = _build_request(view, "auto")
        _show_output_panel(self.window, _render_diagnostic(view, request, executable_info, error))


class ArenaForgeFormatInstallGuideCommand(sublime_plugin.WindowCommand):
    def run(self) -> None:
        view = self.window.active_view()
        if not view:
            return

        runtime = load_runtime_settings(view)
        adapter, _selectors = _select_adapter(view, runtime.selector_overrides)
        if not adapter:
            guide = ["ArenaForge Formatter Install Guide", ""]
            for item in ADAPTERS:
                guide.extend((f"[{item.display_name}]", item.build_install_help(platform.system()), ""))
            _show_output_panel(self.window, "\n".join(guide).rstrip())
            return

        _command_prefix_value, executable_info = _command_prefix(adapter, runtime, _resolve_base_dir(view))
        _show_output_panel(self.window, _render_install_guide(adapter, executable_info))


class ArenaForgeFormatCreateConfigCommand(sublime_plugin.WindowCommand):
    def run(self) -> None:
        view = self.window.active_view()
        if not view:
            _status("no active view to inspect.")
            return

        runtime = load_runtime_settings(view)
        adapter, _selectors = _select_adapter(view, runtime.selector_overrides)
        if not adapter:
            syntax = view.settings().get("syntax") or "unknown syntax"
            _status(f"no recommended template for {syntax}.")
            return

        run_generation_wizard(
            self.window,
            adapter=adapter,
            workspace_mode=False,
            title=f"ArenaForge Formatter Config Generator: {adapter.display_name}",
            context_dir=_view_context_dir(view),
        )


class ArenaForgeFormatCreateWorkspaceConfigsCommand(sublime_plugin.WindowCommand):
    def run(self) -> None:
        run_generation_wizard(
            self.window,
            adapter=None,
            workspace_mode=True,
            title="ArenaForge Workspace Formatter Config Generator",
            context_dir=_view_context_dir(self.window.active_view()),
        )


class ArenaForgeFormatRenderPanelCommand(sublime_plugin.TextCommand):
    def run(self, edit: sublime.Edit, content: str) -> None:
        self.view.set_read_only(False)
        self.view.replace(edit, sublime.Region(0, self.view.size()), content)
        self.view.set_read_only(True)


class ArenaForgeFormatEventListener(sublime_plugin.EventListener):
    def on_pre_save(self, view: sublime.View) -> None:
        runtime = load_runtime_settings(view)
        if runtime.format_on_save and _select_adapter(view, runtime.selector_overrides)[0]:
            view.run_command("arena_forge_format", {"mode": "document", "trigger": "save"})
