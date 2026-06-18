from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

import sublime

from arena_forge.formatting.adapters.base import FormatterAdapter
from arena_forge.formatting.core.templates import (
    ExistingHandlingStrategy,
    GenerationPlan,
    MaterializedTemplate,
    TargetCandidate,
    TemplateFile,
    TemplatePreset,
    apply_generation_plan,
    detect_workspace_languages,
    existing_strategy_options,
    openable_paths_from_results,
    plan_template_generation,
    preset_options,
    python_config_options,
    render_generation_plan,
    resolve_target_candidates,
    template_files_for_adapter,
    template_files_for_workspace,
)

from ..shared.messages import translate
from .presentation import _show_output_panel, _status


def _open_result_files(
    window: sublime.Window,
    results: Tuple[MaterializedTemplate, ...],
    *,
    include_existing: bool = False,
) -> None:
    for path in openable_paths_from_results(results, include_existing=include_existing):
        window.open_file(path)


def _status_from_materialized(materialized: Tuple[MaterializedTemplate, ...]) -> str:
    labels = (
        ("created", "created"),
        ("replaced", "replaced"),
        ("merged", "merged"),
        ("existing", "kept"),
        ("blocked", "blocked"),
    )
    parts = []
    for status, label in labels:
        count = sum(1 for item in materialized if item.status == status)
        if count:
            parts.append(f"{label} {count}")
    return ", ".join(parts) if parts else translate("status.no_config_files_generated")


def _render_generation_result(
    plan: GenerationPlan,
    results: Tuple[MaterializedTemplate, ...],
) -> str:
    lines = [render_generation_plan(plan), "", "Applied results:"]
    for item in results:
        lines.append(f"  [{item.status.upper()}] {Path(item.path).name}")
    return "\n".join(lines)


def _quick_panel_entries_for_presets(presets: Tuple[TemplatePreset, ...]) -> list:
    return [
        [f"{preset.caption}{' (Recommended)' if index == 0 else ''}", preset.description]
        for index, preset in enumerate(presets)
    ]


def _quick_panel_entries_for_targets(targets: Tuple[TargetCandidate, ...]) -> list:
    return [[target.caption, f"{target.path} | {target.description}"] for target in targets]


def _quick_panel_entries_for_strategies(
    strategies: Tuple[ExistingHandlingStrategy, ...],
) -> list:
    return [
        [f"{strategy.caption}{' (Recommended)' if index == 0 else ''}", strategy.description]
        for index, strategy in enumerate(strategies)
    ]


def _quick_panel_entries_for_python_config(options: Tuple[Tuple[str, str, str], ...]) -> list:
    return [[caption, description] for _config_kind, caption, description in options]


def _build_templates_for_selection(
    *,
    adapter: Optional[FormatterAdapter],
    workspace_mode: bool,
    target: TargetCandidate,
    preset_id: str,
    python_config_kind: str,
) -> Tuple[TemplateFile, ...]:
    if workspace_mode:
        return template_files_for_workspace(
            target.path,
            preset_id=preset_id,
            python_config_kind=python_config_kind,
        )
    if not adapter:
        return ()
    return template_files_for_adapter(
        adapter.id,
        preset_id=preset_id,
        python_config_kind=python_config_kind,
    )


def _workspace_needs_python_choice(target: TargetCandidate) -> bool:
    return "ruff" in detect_workspace_languages(target.path)


def _needs_python_choice(
    adapter: Optional[FormatterAdapter],
    workspace_mode: bool,
    target: TargetCandidate,
) -> bool:
    return bool((adapter and adapter.id == "ruff") or (workspace_mode and _workspace_needs_python_choice(target)))


def _apply_generation_plan(
    window: sublime.Window,
    plan: GenerationPlan,
    *,
    include_existing: bool,
) -> None:
    results = apply_generation_plan(plan)
    _open_result_files(window, results, include_existing=include_existing)
    _show_output_panel(window, _render_generation_result(plan, results))
    _status(f"{_status_from_materialized(results)} in {plan.target.path}.")


def run_generation_wizard(
    window: sublime.Window,
    *,
    adapter: Optional[FormatterAdapter],
    workspace_mode: bool,
    title: str,
    context_dir: Optional[str],
) -> None:
    targets = resolve_target_candidates(
        context_dir,
        window.folders(),
        adapter_id=adapter.id if adapter else None,
    )
    if not targets:
        _status(translate("status.open_file_or_workspace"))
        return

    presets = preset_options()
    strategies = existing_strategy_options()
    state = {
        "preset": presets[0],
        "target": targets[0],
        "python_config_kind": "ruff.toml",
        "strategy": strategies[0],
    }

    def show_preset_panel() -> None:
        window.show_quick_panel(_quick_panel_entries_for_presets(presets), on_preset_selected)

    def on_preset_selected(index: int) -> None:
        if index < 0:
            return
        state["preset"] = presets[index]
        window.show_quick_panel(_quick_panel_entries_for_targets(targets), on_target_selected)

    def on_target_selected(index: int) -> None:
        if index < 0:
            return
        target = targets[index]
        state["target"] = target
        if _needs_python_choice(adapter, workspace_mode, target):
            options = python_config_options(target.path)
            state["python_options"] = options
            window.show_quick_panel(_quick_panel_entries_for_python_config(options), on_python_config_selected)
            return
        state["python_config_kind"] = "ruff.toml"
        show_strategy_panel()

    def on_python_config_selected(index: int) -> None:
        if index < 0:
            return
        options = state.get("python_options", ())
        state["python_config_kind"] = options[index][0] if options else "ruff.toml"
        show_strategy_panel()

    def show_strategy_panel() -> None:
        window.show_quick_panel(_quick_panel_entries_for_strategies(strategies), on_strategy_selected)

    def on_strategy_selected(index: int) -> None:
        if index < 0:
            return
        strategy = strategies[index]
        state["strategy"] = strategy
        templates = _build_templates_for_selection(
            adapter=adapter,
            workspace_mode=workspace_mode,
            target=state["target"],
            preset_id=state["preset"].id,
            python_config_kind=state["python_config_kind"],
        )
        plan = plan_template_generation(
            title=title,
            preset_id=state["preset"].id,
            target=state["target"],
            existing_strategy_id=strategy.id,
            templates=templates,
        )
        _show_output_panel(window, render_generation_plan(plan))
        if not sublime.ok_cancel_dialog(translate("prompt.apply_generation_plan"), "Apply"):
            return
        _apply_generation_plan(window, plan, include_existing=not workspace_mode)

    show_preset_panel()
