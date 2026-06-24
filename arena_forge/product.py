from __future__ import annotations

import copy
from typing import Any, Optional

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
SUPPORTED_LOCALES = ("en", "zh-Hans", "ja", "ko", "ru")
DEFAULT_LINT_TIMEOUT_MS = 3000


def _binary_output(platform_name: str) -> tuple[str, str]:
    if platform_name == "windows":
        return "\"{source_file_dir}\\{file_name}.exe\"", "\"{source_file_dir}\\{file_name}.exe\" {args}"
    return "\"{file_name}\"", "./{file_name} {args}"


def _profile(
    *,
    id: str,
    name: str,
    extensions: list[str],
    syntax_selectors: list[str],
    compile_cmd: Optional[str],
    run_cmd: Optional[str],
    lint_compile_cmd: Optional[str],
    formatter: str,
    template_path: str,
    submission_key: Optional[str] = None,
) -> dict[str, Any]:
    return {
        "id": id,
        "name": name,
        "extensions": extensions,
        "syntax_selectors": syntax_selectors,
        "compile_cmd": compile_cmd,
        "run_cmd": run_cmd,
        "lint_compile_cmd": lint_compile_cmd,
        "formatter": formatter,
        "template_path": template_path,
        "submission_key": submission_key,
    }


def _default_run_settings(platform_name: str) -> list[dict[str, Any]]:
    platform_name = (platform_name or "windows").lower()
    native_binary, native_run = _binary_output(platform_name)
    kotlin_jar = (
        "\"{source_file_dir}\\{file_name}.jar\""
        if platform_name == "windows"
        else "\"{file_name}.jar\""
    )
    return [
        _profile(
            id="c",
            name="C",
            extensions=["c"],
            syntax_selectors=["source.c"],
            compile_cmd=f"gcc \"{{source_file}}\" -std=c17 -O2 -pipe -o {native_binary}",
            run_cmd=native_run,
            lint_compile_cmd=None,
            formatter="clang-format",
            template_path="templates/contest/main.c",
        ),
        _profile(
            id="cpp",
            name="C++",
            extensions=["cpp", "cc", "cxx"],
            syntax_selectors=["source.c++"],
            compile_cmd=f"g++ \"{{source_file}}\" -std=gnu++17 -O2 -pipe -o {native_binary}",
            run_cmd=native_run,
            lint_compile_cmd=(
                "g++ -std=gnu++17 -fsyntax-only -fdiagnostics-color=never "
                "\"{source_file}\" -I \"{source_file_dir}\""
            ),
            formatter="clang-format",
            template_path="templates/contest/main.cpp",
            submission_key="cpp",
        ),
        _profile(
            id="python",
            name="Python",
            extensions=["py"],
            syntax_selectors=["source.python"],
            compile_cmd=None,
            run_cmd="python \"{source_file}\" {args}",
            lint_compile_cmd=None,
            formatter="ruff",
            template_path="templates/contest/main.py",
            submission_key="py",
        ),
        _profile(
            id="java",
            name="Java",
            extensions=["java"],
            syntax_selectors=["source.java"],
            compile_cmd="javac -J-Dfile.encoding=utf8 -d \"{source_file_dir}\" \"{source_file}\"",
            run_cmd="java -classpath \"{source_file_dir}\" \"{file_name}\" {args}",
            lint_compile_cmd=None,
            formatter="google-java-format",
            template_path="templates/contest/Main.java",
            submission_key="java",
        ),
        _profile(
            id="kotlin",
            name="Kotlin",
            extensions=["kt"],
            syntax_selectors=["source.kotlin"],
            compile_cmd=f"kotlinc \"{{source_file}}\" -include-runtime -d {kotlin_jar}",
            run_cmd=f"java -jar {kotlin_jar} {{args}}",
            lint_compile_cmd=None,
            formatter="ktfmt",
            template_path="templates/contest/main.kt",
        ),
        _profile(
            id="go",
            name="Go",
            extensions=["go"],
            syntax_selectors=["source.go"],
            compile_cmd=f"go build -o {native_binary} \"{{source_file}}\"",
            run_cmd=native_run,
            lint_compile_cmd=None,
            formatter="gofmt",
            template_path="templates/contest/main.go",
        ),
        _profile(
            id="rust",
            name="Rust",
            extensions=["rs"],
            syntax_selectors=["source.rust"],
            compile_cmd=f"rustc \"{{source_file}}\" -O -o {native_binary}",
            run_cmd=native_run,
            lint_compile_cmd=None,
            formatter="rustfmt",
            template_path="templates/contest/main.rs",
        ),
        _profile(
            id="javascript",
            name="JavaScript",
            extensions=["js"],
            syntax_selectors=["source.js"],
            compile_cmd=None,
            run_cmd="node \"{source_file}\" {args}",
            lint_compile_cmd=None,
            formatter="oxfmt",
            template_path="templates/contest/main.js",
        ),
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
        "lint_timeout_ms": DEFAULT_LINT_TIMEOUT_MS,
        "lint_error_region_scope": "invalid.illegal",
        "lint_warning_region_scope": "constant",
        "cpp_complete_enabled": True,
        "algorithms_base": None,
        "default_contest_language": "cpp",
        "run_settings": _default_run_settings(platform_name),
        "formatting": {
            "format_on_save": False,
            "timeout_ms": 10000,
            "commands": {},
            "extra_args": {},
            "selector_overrides": {},
            "show_output_panel_on_error": True,
        },
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


SETTINGS_KEYS = tuple(build_default_settings("windows").keys())
