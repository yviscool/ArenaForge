from __future__ import annotations

from importlib import import_module
from typing import Optional


def resolve_root_package_name(module_name: str) -> Optional[str]:
    parts = module_name.split(".")
    if len(parts) >= 5 and parts[1] == "arena_forge":
        return parts[0]
    if parts[0] != "arena_forge":
        return parts[0]
    return None


def _root_package_name() -> Optional[str]:
    return resolve_root_package_name(__name__)


def import_root_module(module_name: str):
    root_package_name = _root_package_name()
    if root_package_name is not None:
        return import_module(f"{root_package_name}.{module_name}")
    return import_module(module_name)


def get_debugger_info_module():
    return import_root_module("debug_backends.registry")


def get_highlight_function():
    return import_root_module("highlight_assets.cpp_var_highlight").highlight


def get_template_generator():
    return import_root_module("plugin_support.template_generation.generator").gen
