from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_REPO_ROOT_SENTINELS = ("pyproject.toml", "TestSyntax.sublime-syntax", "Default.sublime-commands")


@dataclass(frozen=True)
class PackageLayout:
    package_name: str
    resource_subpath: tuple[str, ...]


def resolve_package_layout(module_name: str) -> PackageLayout:
    parts = module_name.split(".")
    last_inner_package_index = max(index for index, part in enumerate(parts) if part == "arena_forge")
    if parts[0] == "arena_forge":
        return PackageLayout(package_name="arena_forge", resource_subpath=())
    return PackageLayout(
        package_name=parts[0],
        resource_subpath=tuple(parts[1:last_inner_package_index]),
    )


@lru_cache(maxsize=1)
def get_plugin_package_name() -> str:
    return resolve_package_layout(__name__).package_name


@lru_cache(maxsize=1)
def get_package_resource_root() -> str:
    layout = resolve_package_layout(__name__)
    parts = [layout.package_name, *layout.resource_subpath]
    return "Packages/" + "/".join(parts)


@lru_cache(maxsize=1)
def get_plugin_root_dir() -> Path:
    current = Path(__file__).resolve()
    for candidate in current.parents:
        if all((candidate / sentinel).exists() for sentinel in _REPO_ROOT_SENTINELS):
            return candidate
    raise RuntimeError("Unable to locate ArenaForge repository root from package_resources.py")


def build_package_resource_path(*parts: str) -> str:
    normalized = [get_package_resource_root()]
    normalized.extend(part.replace("\\", "/").strip("/") for part in parts if part)
    return "/".join(normalized)


ARROW_LEFT_ICON_RESOURCE = build_package_resource_path("icons", "arrow_left.png")
ARROW_RIGHT_ICON_RESOURCE = build_package_resource_path("icons", "arrow_right.png")
STRESS_SYNTAX_RESOURCE = build_package_resource_path("StressSyntax.sublime-syntax")
TEST_SYNTAX_RESOURCE = build_package_resource_path("TestSyntax.sublime-syntax")


def remap_package_syntax_resource(current_syntax: str | None) -> str | None:
    if not current_syntax or not current_syntax.startswith("Packages/"):
        return None
    package_name = get_plugin_package_name()
    if f"/{package_name}/" not in f"/{current_syntax}":
        return None
    if current_syntax.endswith("/TestSyntax.sublime-syntax") and current_syntax != TEST_SYNTAX_RESOURCE:
        return TEST_SYNTAX_RESOURCE
    if current_syntax.endswith("/StressSyntax.sublime-syntax") and current_syntax != STRESS_SYNTAX_RESOURCE:
        return STRESS_SYNTAX_RESOURCE
    return None
