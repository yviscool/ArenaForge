from __future__ import annotations

from collections.abc import Mapping
from typing import Dict, Tuple

import sublime

from arena_forge.formatting.core.contracts import RuntimeSettings
from arena_forge.product import SETTINGS_FILE

SETTINGS_FILENAME = SETTINGS_FILE
PRODUCT_SETTINGS_KEY = "ArenaForge"
FORMATTING_KEY = "formatting"

DEFAULT_SETTINGS = RuntimeSettings(
    format_on_save=False,
    commands={},
    extra_args={},
    selector_overrides={},
    format_timeout_ms=10000,
    show_output_panel_on_error=True,
)


def _mapping(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return value
    return {}


def _normalize_string_map(value: object) -> Dict[str, Tuple[str, ...]]:
    normalized = {}  # type: Dict[str, Tuple[str, ...]]
    for key, raw in _mapping(value).items():
        if isinstance(raw, str) and raw.strip():
            normalized[str(key)] = (raw.strip(),)
        elif isinstance(raw, (list, tuple)):
            items = tuple(str(item).strip() for item in raw if str(item).strip())
            if items:
                normalized[str(key)] = items
    return normalized


def _merge_string_maps(*maps: object) -> Dict[str, Tuple[str, ...]]:
    merged = {}  # type: Dict[str, Tuple[str, ...]]
    for value in maps:
        merged.update(_normalize_string_map(value))
    return merged


def _plugin_settings(settings: sublime.Settings) -> Mapping[str, object]:
    return _mapping(settings.get(FORMATTING_KEY, {}))


def _project_settings(window: sublime.Window) -> Mapping[str, object]:
    if not window:
        return {}

    project_data = window.project_data() or {}
    settings = project_data.get("settings") or {}
    if not isinstance(settings, Mapping):
        return {}
    arena_forge_settings = _mapping(settings.get(PRODUCT_SETTINGS_KEY, {}))
    return _mapping(arena_forge_settings.get(FORMATTING_KEY, {}))


def _view_settings(view: sublime.View) -> Mapping[str, object]:
    arena_forge_settings = _mapping(view.settings().get(PRODUCT_SETTINGS_KEY, {}))
    return _mapping(arena_forge_settings.get(FORMATTING_KEY, {}))


def _setting_value(
    plugin_settings: Mapping[str, object],
    view_settings: Mapping[str, object],
    project_settings: Mapping[str, object],
    key: str,
    default: object,
) -> object:
    return project_settings.get(
        key,
        view_settings.get(
            key,
            plugin_settings.get(key, default),
        ),
    )


def _int_setting(
    plugin_settings: Mapping[str, object],
    view_settings: Mapping[str, object],
    project_settings: Mapping[str, object],
    key: str,
    default: int,
) -> int:
    raw_value = _setting_value(plugin_settings, view_settings, project_settings, key, default)
    if isinstance(raw_value, bool):
        return default
    try:
        return max(0, int(raw_value))
    except (TypeError, ValueError):
        return default


def load_runtime_settings(view: sublime.View) -> RuntimeSettings:
    settings = sublime.load_settings(SETTINGS_FILENAME)
    plugin_settings = _plugin_settings(settings)
    project_settings = _project_settings(view.window())
    view_settings = _view_settings(view)

    format_on_save = bool(
        _setting_value(
            plugin_settings,
            view_settings,
            project_settings,
            "format_on_save",
            DEFAULT_SETTINGS.format_on_save,
        )
    )
    show_output_panel_on_error = bool(
        _setting_value(
            plugin_settings,
            view_settings,
            project_settings,
            "show_output_panel_on_error",
            DEFAULT_SETTINGS.show_output_panel_on_error,
        )
    )
    format_timeout_ms = _int_setting(
        plugin_settings,
        view_settings,
        project_settings,
        "format_timeout_ms",
        DEFAULT_SETTINGS.format_timeout_ms,
    )

    commands = _merge_string_maps(
        plugin_settings.get("commands", {}),
        view_settings.get("commands", {}),
        project_settings.get("commands", {}),
    )
    extra_args = _merge_string_maps(
        plugin_settings.get("extra_args", {}),
        view_settings.get("extra_args", {}),
        project_settings.get("extra_args", {}),
    )
    selector_overrides = _merge_string_maps(
        plugin_settings.get("selector_overrides", {}),
        view_settings.get("selector_overrides", {}),
        project_settings.get("selector_overrides", {}),
    )

    return RuntimeSettings(
        format_on_save=format_on_save,
        commands=commands,
        extra_args=extra_args,
        selector_overrides=selector_overrides,
        format_timeout_ms=format_timeout_ms,
        show_output_panel_on_error=show_output_panel_on_error,
    )
