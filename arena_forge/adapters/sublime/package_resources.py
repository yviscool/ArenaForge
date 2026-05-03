from __future__ import annotations

from functools import lru_cache
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[3]


@lru_cache(maxsize=1)
def get_plugin_package_name() -> str:
    return ROOT_DIR.name


def get_plugin_root_dir() -> Path:
    return ROOT_DIR


def build_package_resource_path(*parts: str) -> str:
    normalized = [get_plugin_package_name()]
    normalized.extend(part.replace("\\", "/").strip("/") for part in parts if part)
    return "Packages/" + "/".join(normalized)


ARROW_LEFT_ICON_RESOURCE = build_package_resource_path("icons", "arrow_left.png")
ARROW_RIGHT_ICON_RESOURCE = build_package_resource_path("icons", "arrow_right.png")
STRESS_SYNTAX_RESOURCE = build_package_resource_path("StressSyntax.sublime-syntax")
TEST_SYNTAX_RESOURCE = build_package_resource_path("TestSyntax.sublime-syntax")
