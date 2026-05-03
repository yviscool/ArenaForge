from __future__ import annotations

import copy
from typing import Any

__version__ = "3.0.0"

PRODUCT_SLUG = "arena_forge"
DISPLAY_NAME = "ArenaForge"

SETTINGS_FILE = "ArenaForge.sublime-settings"

WORKSPACE_DIRNAME = ".arena-forge"
DEFAULT_TESTS_RELATIVE_DIR = WORKSPACE_DIRNAME + "/tests"
DEFAULT_SESSION_RELATIVE_DIR = WORKSPACE_DIRNAME + "/sessions"
DEFAULT_TESTS_FILE_SUFFIX = ".tests.json"
DEFAULT_ALGORITHM_PROPERTIES_SUFFIX = ".cpp.properties.json"
DEFAULT_CONTESTS_ROOT = "~/Contests/ArenaForge"
SUPPORTED_LOCALES = ("en", "zh-Hans")


def _default_run_settings(platform_name: str) -> list[dict[str, Any]]:
    platform_name = (platform_name or "windows").lower()
    if platform_name == "windows":
        cpp_run = "\"{source_file_dir}\\{file_name}.exe\" {args}"
    else:
        cpp_run = "./{file_name} {args}"

    return [
        {
            "name": "C++",
            "extensions": ["cpp"],
            "compile_cmd": "g++ \"{source_file}\" -std=gnu++17 -O2 -pipe -o \"{file_name}\"",
            "run_cmd": cpp_run,
            "lint_compile_cmd": "g++ -std=gnu++17 \"{source_file}\" -I \"{source_file_dir}\"",
        },
        {
            "name": "Python",
            "extensions": ["py"],
            "compile_cmd": None,
            "run_cmd": "python \"{source_file}\"",
            "lint_compile_cmd": None,
        },
        {
            "name": "Java",
            "extensions": ["java"],
            "compile_cmd": "javac -J-Dfile.encoding=utf8 -d \"{source_file_dir}\" \"{source_file}\"",
            "run_cmd": "java -classpath \"{source_file_dir}\" \"{file_name}\"",
            "lint_compile_cmd": None,
        },
    ]


def build_default_settings(platform_name: str) -> dict[str, Any]:
    return {
        "product_name": DISPLAY_NAME,
        "preferred_locale": "en",
        "supported_locales": list(SUPPORTED_LOCALES),
        "credential_backend": "keyring",
        "ui_variant": "terminal",
        "ui_density": "compact",
        "workspace_dirname": WORKSPACE_DIRNAME,
        "tests_relative_dir": DEFAULT_TESTS_RELATIVE_DIR,
        "session_relative_dir": DEFAULT_SESSION_RELATIVE_DIR,
        "tests_file_suffix": DEFAULT_TESTS_FILE_SUFFIX,
        "algorithm_properties_suffix": DEFAULT_ALGORITHM_PROPERTIES_SUFFIX,
        "contests_root": DEFAULT_CONTESTS_ROOT,
        "close_sidebar": True,
        "stress_time_limit_seconds": 2,
        "lint_enabled": True,
        "lint_error_region_scope": "invalid.illegal",
        "lint_warning_region_scope": "constant",
        "cpp_complete_enabled": True,
        "algorithms_base": None,
        "run_settings": _default_run_settings(platform_name),
        "submission_language_ids": {
            "codeforces": {
                "cpp": 54,
                "py": 31,
                "java": 60,
            },
            "atcoder": {},
            "luogu": {},
            "acwing": {},
        },
        "cpp_complete_settings": {
            "classes": {
                "int": {"template_size": 0},
                "char": {"template_size": 0},
                "string": {"template_size": 0},
                "pair": {"template_size": 2},
                "vector": {"template_size": 1},
                "bool": {"template_size": 0},
                "ll": {"template_size": 0},
                "double": {"template_size": 0},
                "set": {"template_size": 1, "bind": "S"},
                "map": {"template_size": 2},
            },
            "dont_expand": ["pii"],
        },
    }


def clone_defaults(platform_name: str) -> dict[str, Any]:
    return copy.deepcopy(build_default_settings(platform_name))
