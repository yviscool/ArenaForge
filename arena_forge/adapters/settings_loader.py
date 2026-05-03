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


def normalize_settings(raw_settings: Optional[Mapping[str, Any]], platform_name: str) -> dict[str, Any]:
    defaults = clone_defaults(platform_name)
    merged = clone_defaults(platform_name)
    payload = dict(raw_settings or {})
    _deep_merge(merged, payload)

    if not merged.get("tests_relative_dir"):
        merged["tests_relative_dir"] = defaults["tests_relative_dir"]
    if not merged.get("session_relative_dir"):
        merged["session_relative_dir"] = defaults["session_relative_dir"]
    if not merged.get("tests_file_suffix"):
        merged["tests_file_suffix"] = defaults["tests_file_suffix"]
    if not merged.get("algorithm_properties_suffix"):
        merged["algorithm_properties_suffix"] = defaults["algorithm_properties_suffix"]
    if not merged.get("contests_root"):
        merged["contests_root"] = defaults["contests_root"]
    if not merged.get("product_name"):
        merged["product_name"] = defaults["product_name"]
    if not merged.get("credential_backend"):
        merged["credential_backend"] = defaults["credential_backend"]
    if not merged.get("ui_variant"):
        merged["ui_variant"] = defaults["ui_variant"]
    if not merged.get("ui_density"):
        merged["ui_density"] = defaults["ui_density"]
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
                "name": str(profile["name"]),
                "extensions": [str(item) for item in profile.get("extensions", ())],
                "compile_cmd": profile.get("compile_cmd"),
                "run_cmd": profile.get("run_cmd"),
                "lint_compile_cmd": profile.get("lint_compile_cmd"),
            }
        )
    merged["run_settings"] = normalized_profiles
    return merged
