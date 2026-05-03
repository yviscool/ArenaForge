from __future__ import annotations

from pathlib import Path

import sublime

from arena_forge.adapters.sublime.bootstrap import SublimeApplication, build_sublime_application
from arena_forge.core.services import infer_language
from arena_forge.product import SETTINGS_FILE

from .messages import product_status_message
from .package_resources import get_plugin_package_name, get_plugin_root_dir
from .package_resources import remap_package_syntax_resource

root_dir = str(get_plugin_root_dir())
base_name = get_plugin_package_name()
settings_file = SETTINGS_FILE
default_settings_file = "ArenaForge ({os}).sublime-settings".format(
    os={"windows": "Windows", "linux": "Linux", "osx": "OSX"}[sublime.platform().lower()]
)

tests_file_suffix = ".tests.json"
tests_relative_dir = ".arena-forge/tests"

settings = {}
run_supported_exts = set()
_application = None


def _settings_to_dict(settings_obj):
    data = {}
    if settings_obj is None:
        return data
    for key in ("product_name", "preferred_locale", "supported_locales", "credential_backend",
                "ui_variant", "ui_density", "workspace_dirname",
                "tests_relative_dir", "session_relative_dir", "tests_file_suffix",
                "algorithm_properties_suffix", "contests_root", "close_sidebar",
                "stress_time_limit_seconds", "lint_enabled", "lint_error_region_scope",
                "lint_warning_region_scope", "cpp_complete_enabled", "algorithms_base",
                "run_settings", "submission_language_ids", "cpp_complete_settings"):
        value = settings_obj.get(key)
        if value is not None:
            data[key] = value
    return data


def init_settings(_settings):
    global settings
    settings = _settings


def get_settings():
    return settings


def init_application(application: SublimeApplication):
    global _application
    _application = application
    init_settings(application.settings)


def get_application() -> SublimeApplication:
    if _application is None:
        raise RuntimeError("ArenaForge Sublime application has not been initialized yet")
    return _application


def is_run_supported_ext(ext):
    for option in get_settings().get("run_settings", []):
        if ext in option["extensions"]:
            return True
    return False


def get_supported_exts(lang):
    for option in get_settings().get("run_settings", []):
        if option["name"] == lang:
            return option["extensions"]
    return []


def is_lang_view(view, lang):
    if view.file_name() is None:
        return False
    return Path(view.file_name()).suffix.lstrip(".") in get_supported_exts(lang)


def try_load_settings():
    primary = sublime.load_settings(settings_file)
    application = build_sublime_application(
        _settings_to_dict(primary),
        platform_name=sublime.platform(),
        locale_directory=Path(root_dir) / "arena_forge" / "locales",
    )
    init_application(application)
    repair_open_view_syntaxes()
    product_status_message("status.settings_loaded")


def plugin_loaded():
    sublime.set_timeout(try_load_settings, 200)


def repair_open_view_syntaxes():
    for window in sublime.windows():
        for view in window.views():
            repair_view_syntax(view)


def repair_view_syntax(view):
    current_syntax = view.settings().get("syntax")
    corrected_syntax = remap_package_syntax_resource(current_syntax)
    if corrected_syntax is not None:
        view.set_syntax_file(corrected_syntax)


def get_tests_file_suffix():
    return get_settings().get("tests_file_suffix") or tests_file_suffix


def get_workspace_layout():
    return get_application().layout


def get_language_profiles():
    return get_application().profiles


def infer_language_name(file):
    return infer_language(file, get_language_profiles())


def get_session_repository():
    return get_application().repository


def get_tests_file_path(file, for_write=False):
    layout = get_workspace_layout()
    if for_write:
        return str(layout.ensure_parent(layout.session_path_for(file)))
    return str(layout.resolve_session_path(file))


def get_algorithm_properties_path(file, for_write=False):
    layout = get_workspace_layout()
    primary, legacy = layout.algorithm_properties_candidates(file)
    if for_write:
        return str(layout.ensure_parent(primary))
    if primary.exists():
        return str(primary)
    return str(legacy)


def get_contests_root():
    return str(get_workspace_layout().expanded_contests_root())
