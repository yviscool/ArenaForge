from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from ..shared.messages import translate
from ..shared.settings_bridge import get_settings, root_dir

ASSET_ROOT = Path(root_dir) / "highlight_assets"
THEME_STYLES = {
    "Spacegray Light.sublime-theme": "test_styles_spacegraylight.css",
    "Spacegray.sublime-theme": "test_styles_spacegray.css",
}
TEMPLATE_LABELS = {
    "test_config.html": {
        "test_label": "ui.test",
        "edit_label": "ui.edit",
        "run_label": "ui.run",
        "time_label": "ui.time",
        "result_label": "ui.result",
    },
    "test_running.html": {
        "test_label": "ui.test",
        "stop_label": "ui.stop",
    },
    "test_next.html": {
        "next_test_label": "ui.next_test",
    },
    "test_edit.html": {
        "test_label": "ui.test",
        "save_label": "ui.save",
        "delete_label": "ui.delete",
    },
    "test_accdec.html": {
        "accept_label": "ui.accept",
        "decline_label": "ui.decline",
    },
    "compile.html": {
        "run_label": "ui.run",
    },
}


@lru_cache(maxsize=None)
def _read_asset(asset_name: str) -> str:
    return (ASSET_ROOT / asset_name).read_text(encoding="utf-8")


def _style_asset_name(theme_name: Optional[str]) -> str:
    return THEME_STYLES.get(theme_name or "", "test_styles.css")


def _variant_css(ui_variant: str, ui_density: str) -> str:
    gap = "2px" if ui_variant == "terminal" else "3px" if ui_density == "compact" else "6px"
    padding = "2px 6px" if ui_variant == "terminal" else "3px 8px" if ui_density == "compact" else "4px 10px"
    border_radius = "0px" if ui_variant == "terminal" else "4px" if ui_variant == "legacy" else "7px"
    shadow = "none" if ui_variant in {"legacy", "terminal"} else "0 1px 0 color(var(--background) alpha(0.35))"
    panel_alpha = "0.10" if ui_variant == "terminal" else "0.14"
    chip_alpha = "0.16" if ui_variant == "terminal" else "0.22"
    muted_alpha = "0.72" if ui_variant == "terminal" else "0.78"
    font_family = "monospace" if ui_variant == "terminal" else "inherit"
    return (
        "html {"
        f"--af-gap: {gap};"
        f"--af-chip-padding: {padding};"
        f"--af-chip-radius: {border_radius};"
        f"--af-chip-shadow: {shadow};"
        f"--panel-color: color(var(--foreground) alpha({panel_alpha}));"
        f"--chip-color: color(var(--foreground) alpha({chip_alpha}));"
        f"--muted-color: color(var(--foreground) alpha({muted_alpha}));"
        f"--af-font-family: {font_family};"
        "}"
    )


@lru_cache(maxsize=None)
def _base_styles(theme_name: Optional[str]) -> str:
    return _read_asset(_style_asset_name(theme_name))


def build_styles(view) -> str:
    settings = get_settings()
    return (
        _base_styles(view.settings().get("theme"))
        + _variant_css(settings.get("ui_variant", "refined"), settings.get("ui_density", "comfortable"))
    )


def render_template(asset_name: str, **context: object) -> str:
    labels = {name: translate(key) for name, key in TEMPLATE_LABELS.get(asset_name, {}).items()}
    return _read_asset(asset_name).format(**labels, **context)
