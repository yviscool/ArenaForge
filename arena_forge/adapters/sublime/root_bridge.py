from __future__ import annotations

from importlib import import_module


def _root_package_name() -> str:
    parts = __name__.split(".")
    if parts[0] == "arena_forge":
        raise RuntimeError("Sublime root bridge requires package-qualified plugin imports")
    return parts[0]


def import_root_module(module_name: str):
    return import_module(f"{_root_package_name()}.{module_name}")


def get_debugger_info_module():
    return import_root_module("debuggers.debugger_info")


def get_highlight_function():
    return import_root_module("Highlight.CppVarHighlight").highlight


def get_template_generator():
    return import_root_module("Modules.ClassPregen.ClassPregen").gen
