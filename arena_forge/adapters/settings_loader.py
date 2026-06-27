from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping, Optional, Type, cast

from arena_forge.product import clone_defaults


def _deep_merge(base: dict[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    for key, value in override.items():
        if isinstance(value, Mapping) and isinstance(base.get(key), dict):
            _deep_merge(base[key], value)
        else:
            base[key] = deepcopy(value)
    return base


def normalize_string_map(
    value: object,
    *,
    container: Type = list,
) -> dict:
    normalized: dict = {}
    if not isinstance(value, Mapping):
        return normalized
    for key, raw in value.items():
        if isinstance(raw, str) and raw.strip():
            normalized[str(key)] = container([raw.strip()])
        elif isinstance(raw, (list, tuple)):
            items = container(str(item).strip() for item in raw if str(item).strip())
            if items:
                normalized[str(key)] = items
    return normalized


def _normalize_string_map(value: object) -> dict[str, list[str]]:
    return normalize_string_map(value, container=list)


def _normalize_optional_string(value: object) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize_string_list(value: object) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    result = [str(item).strip() for item in value if str(item).strip()]
    return result


def _normalize_language_profile(
    profile_id: str,
    profile: Mapping[str, Any],
    defaults: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    normalized = deepcopy(defaults) if defaults is not None else {}
    _deep_merge(normalized, profile)
    normalized["id"] = str(normalized.get("id") or profile_id)
    normalized["name"] = str(normalized.get("name") or profile_id)
    normalized["extensions"] = _normalize_string_list(normalized.get("extensions", ()))
    normalized["syntax_selectors"] = _normalize_string_list(normalized.get("syntax_selectors", ()))
    normalized["compile_cmd"] = _normalize_optional_string(normalized.get("compile_cmd"))
    normalized["run_cmd"] = _normalize_optional_string(normalized.get("run_cmd"))
    normalized["lint_compile_cmd"] = _normalize_optional_string(normalized.get("lint_compile_cmd"))
    normalized["formatter"] = _normalize_optional_string(normalized.get("formatter"))
    normalized["template_path"] = _normalize_optional_string(normalized.get("template_path"))
    normalized["submission_key"] = _normalize_optional_string(normalized.get("submission_key"))
    return normalized


def normalize_language_profiles(value: object, defaults: Mapping[str, Any]) -> dict[str, Any]:
    default_profiles = cast(Mapping[str, Mapping[str, Any]], defaults.get("profiles", {}))
    default_order = [str(item).strip() for item in defaults.get("order", ()) if str(item).strip()]
    raw_profiles = value if isinstance(value, Mapping) else {}
    normalized = deepcopy(defaults)
    if isinstance(raw_profiles, Mapping):
        _deep_merge(normalized, raw_profiles)

    merged_profiles = cast(Mapping[str, Mapping[str, Any]], normalized.get("profiles", {}))
    ordered_profiles: dict[str, dict[str, Any]] = {}
    for profile_id, default_profile in default_profiles.items():
        raw_profile = merged_profiles.get(profile_id, {})
        if not isinstance(raw_profile, Mapping):
            raw_profile = {}
        ordered_profiles[str(profile_id)] = _normalize_language_profile(
            str(profile_id),
            raw_profile,
            defaults=default_profile,
        )

    for profile_id, raw_profile in merged_profiles.items():
        normalized_id = str(profile_id)
        if normalized_id in ordered_profiles:
            continue
        if not isinstance(raw_profile, Mapping):
            raw_profile = {}
        ordered_profiles[normalized_id] = _normalize_language_profile(normalized_id, raw_profile)

    order = [str(item).strip() for item in normalized.get("order", ()) if str(item).strip()]
    if not order:
        order = list(default_order)
    order = list(dict.fromkeys(order))
    for profile_id in ordered_profiles:
        if profile_id not in order:
            order.append(profile_id)

    normalized["order"] = order
    normalized["profiles"] = ordered_profiles
    return normalized


def iter_language_profile_mappings(language_profiles: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    profiles = language_profiles.get("profiles", {})
    order = language_profiles.get("order", ())
    if not isinstance(profiles, Mapping):
        return ()
    ordered_ids = [str(item).strip() for item in order if str(item).strip()]
    ordered_ids = list(dict.fromkeys(ordered_ids))
    for profile_id in profiles:
        normalized_id = str(profile_id)
        if normalized_id not in ordered_ids:
            ordered_ids.append(normalized_id)
    return tuple(deepcopy(profiles[profile_id]) for profile_id in ordered_ids if profile_id in profiles)


def normalize_settings(raw_settings: Optional[Mapping[str, Any]], platform_name: str) -> dict[str, Any]:
    defaults = clone_defaults(platform_name)
    merged = deepcopy(defaults)
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

    merged["language_profiles"] = normalize_language_profiles(
        merged.get("language_profiles", {}),
        defaults["language_profiles"],
    )

    known_language_ids = set(merged["language_profiles"]["profiles"].keys())
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
