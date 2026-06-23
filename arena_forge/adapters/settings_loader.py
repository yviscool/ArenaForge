from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping, Optional

from arena_forge.product import clone_defaults


def _deep_merge(base: dict[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    for key, value in override.items():
        if isinstance(value, Mapping) and isinstance(base.get(key), dict):
            _deep_merge(base[key], value)
        else:
            base[key] = deepcopy(value)
    return base


def _normalize_string_map(value: object) -> dict[str, list[str]]:
    normalized: dict[str, list[str]] = {}
    if not isinstance(value, Mapping):
        return normalized
    for key, raw in value.items():
        if isinstance(raw, str) and raw.strip():
            normalized[str(key)] = [raw.strip()]
        elif isinstance(raw, (list, tuple)):
            items = [str(item).strip() for item in raw if str(item).strip()]
            if items:
                normalized[str(key)] = items
    return normalized


def normalize_settings(raw_settings: Optional[Mapping[str, Any]], platform_name: str) -> dict[str, Any]:
    defaults = clone_defaults(platform_name)
    merged = clone_defaults(platform_name)
    payload = dict(raw_settings or {})
    _deep_merge(merged, payload)

    for key in (
        "tests_relative_dir",
        "session_relative_dir",
        "tests_file_suffix",
        "algorithm_properties_suffix",
        "contests_root",
        "product_name",
        "credential_backend",
        "ui_variant",
        "ui_density",
    ):
        if not merged.get(key):
            merged[key] = defaults[key]

    supported_locales = [str(item) for item in merged.get("supported_locales", ()) if str(item)]
    if not supported_locales:
        supported_locales = list(defaults["supported_locales"])
    merged["supported_locales"] = supported_locales

    preferred_locale = str(merged.get("preferred_locale") or defaults["preferred_locale"])
    if preferred_locale not in supported_locales:
        preferred_locale = defaults["preferred_locale"]
    merged["preferred_locale"] = preferred_locale

    normalized_profiles = []
    for profile in merged.get("run_settings", ()):
        normalized_profiles.append(
            {
                "id": str(profile.get("id") or ""),
                "name": str(profile["name"]),
                "extensions": [str(item) for item in profile.get("extensions", ())],
                "syntax_selectors": [str(item) for item in profile.get("syntax_selectors", ())],
                "compile_cmd": profile.get("compile_cmd"),
                "run_cmd": profile.get("run_cmd"),
                "lint_compile_cmd": profile.get("lint_compile_cmd"),
                "formatter": profile.get("formatter"),
                "template_path": profile.get("template_path"),
                "submission_key": profile.get("submission_key"),
            }
        )
    merged["run_settings"] = normalized_profiles

    known_language_ids = {str(profile.get("id") or "").strip() for profile in normalized_profiles}
    default_contest_language = str(merged.get("default_contest_language") or defaults["default_contest_language"])
    if default_contest_language not in known_language_ids:
        default_contest_language = defaults["default_contest_language"]
    merged["default_contest_language"] = default_contest_language
    merged["lint_timeout_ms"] = max(0, int(merged.get("lint_timeout_ms") or defaults["lint_timeout_ms"]))

    formatting = deepcopy(defaults["formatting"])
    _deep_merge(formatting, merged.get("formatting", {}))
    formatting["format_on_save"] = bool(formatting.get("format_on_save"))
    formatting["timeout_ms"] = max(0, int(formatting.get("timeout_ms") or defaults["formatting"]["timeout_ms"]))
    formatting["show_output_panel_on_error"] = bool(formatting.get("show_output_panel_on_error", True))
    formatting["commands"] = _normalize_string_map(formatting.get("commands", {}))
    formatting["extra_args"] = _normalize_string_map(formatting.get("extra_args", {}))
    formatting["selector_overrides"] = _normalize_string_map(formatting.get("selector_overrides", {}))
    merged["formatting"] = formatting
    return merged
