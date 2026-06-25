from __future__ import annotations

from pathlib import Path
from typing import Optional

import sublime

from arena_forge.adapters.sublime.bootstrap import SublimeApplication, build_sublime_application
from arena_forge.core.services import select_language_profile
from arena_forge.product import SETTINGS_FILE, SETTINGS_KEYS

from .messages import product_status_message
from .package_resources import get_plugin_package_name, get_plugin_root_dir, remap_package_syntax_resource

root_dir = str(get_plugin_root_dir())
base_name = get_plugin_package_name()
settings_file = SETTINGS_FILE
default_settings_file = "ArenaForge ({os}).sublime-settings".format(
    os={"windows": "Windows", "linux": "Linux", "osx": "OSX"}[sublime.platform().lower()]
)

tests_file_suffix = ".tests.json"
tests_relative_dir = ".arena-forge/tests"


class SettingsContext:
    def __init__(self) -> None:
        self.settings: dict = {}
        self._application: Optional[SublimeApplication] = None

    def init_settings(self, _settings: dict) -> None:
        self.settings = _settings

    def get_settings(self) -> dict:
        return self.settings

    def init_application(self, application: SublimeApplication) -> None:
        self._application = application
        self.init_settings(application.settings)

    def get_application(self) -> SublimeApplication:
        if self._application is None:
            try_load_settings()
        return self._application


_context = SettingsContext()


def _settings_to_dict(settings_obj):
    data = {}
    if settings_obj is None:
        return data
    for key in SETTINGS_KEYS:
        value = settings_obj.get(key)
        if value is not None:
            data[key] = value
    return data


def init_settings(_settings):
    _context.init_settings(_settings)


def get_settings():
    return _context.get_settings()


def init_application(application: SublimeApplication):
    _context.init_application(application)


def get_application() -> SublimeApplication:
    return _context.get_application()


def is_run_supported_ext(ext):
    for profile in get_application().profiles:
        if ext in profile.extensions:
            return True
    return False


def get_supported_exts(lang):
    for profile in get_application().profiles:
        if lang in {profile.name, profile.id, profile.identifier}:
            return profile.extensions
    return ()


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
    return select_language_profile(file, get_language_profiles()).identifier


def get_default_contest_language() -> str:
    return str(get_settings().get("default_contest_language") or "cpp")


def get_session_repository():
    return get_application().repository


def get_tests_file_path(file, for_write=False):
    layout = get_workspace_layout()
    if for_write:
        return str(layout.ensure_parent(layout.session_path_for(file)))
    return str(layout.session_path_for(file))


def get_algorithm_properties_path(file, for_write=False):
    layout = get_workspace_layout()
    primary = layout.algorithm_properties_path_for(file)
    if for_write:
        return str(layout.ensure_parent(primary))
    return str(primary)


def get_contests_root():
    return str(get_workspace_layout().expanded_contests_root())
