from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

WORKSPACE_TEMPLATE_ORDER = ("clang-format", "gofmt", "google-java-format", "ktfmt", "ruff", "rustfmt", "oxfmt")
SUPPORTED_ADAPTER_ORDER = WORKSPACE_TEMPLATE_ORDER
IGNORED_SCAN_DIRS = frozenset(
    (
        ".git",
        ".hg",
        ".svn",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "build",
        "dist",
        "target",
    )
)
VCS_ROOT_MARKERS = (".git", ".hg", ".svn")


@dataclass(frozen=True)
class TemplatePreset:
    id: str
    caption: str
    description: str
    line_width: int


@dataclass(frozen=True)
class TemplateFile:
    filename: str
    description: str
    content: str
    adapter_id: Optional[str] = None
    write_mode: str = "plain"


@dataclass(frozen=True)
class MaterializedTemplate:
    template: TemplateFile
    path: str
    status: str


@dataclass(frozen=True)
class TargetCandidate:
    id: str
    caption: str
    description: str
    path: str
    reason: str


@dataclass(frozen=True)
class ExistingHandlingStrategy:
    id: str
    caption: str
    description: str


@dataclass(frozen=True)
class PlannedTemplateWrite:
    template: TemplateFile
    path: str
    action: str
    description: str
    content: Optional[str] = None
    existing_path: Optional[str] = None


@dataclass(frozen=True)
class GenerationPlan:
    title: str
    preset: TemplatePreset
    target: TargetCandidate
    existing_strategy: ExistingHandlingStrategy
    items: Tuple[PlannedTemplateWrite, ...]


PRESETS = (
    TemplatePreset(
        id="recommended",
        caption="Recommended",
        description="Balanced defaults with 100-column width.",
        line_width=100,
    ),
    TemplatePreset(
        id="compact",
        caption="Compact",
        description="Tighter 88-column width for denser diffs.",
        line_width=88,
    ),
    TemplatePreset(
        id="wide",
        caption="Wide",
        description="Looser 120-column width for larger displays.",
        line_width=120,
    ),
)

EXISTING_STRATEGIES = (
    ExistingHandlingStrategy(
        id="skip",
        caption="Skip Existing",
        description="Leave existing config files untouched.",
    ),
    ExistingHandlingStrategy(
        id="example",
        caption="Create .example",
        description="Write side-by-side example files for collisions.",
    ),
    ExistingHandlingStrategy(
        id="replace",
        caption="Replace Existing",
        description="Overwrite colliding formatter config files.",
    ),
)

PYTHON_CONFIG_CHOICES = (
    ("ruff.toml", "Use ruff.toml", "Create or update a dedicated Ruff config file."),
    ("pyproject.toml", "Use pyproject.toml", "Create or merge Ruff settings into pyproject.toml."),
)

DETECTION_MARKERS = {
    "clang-format": (
        ".clang-format",
        "_clang-format",
        "cmakelists.txt",
        "compile_commands.json",
        "meson.build",
    ),
    "google-java-format": (
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
        "settings.gradle",
        "settings.gradle.kts",
    ),
    "ktfmt": (
        "build.gradle",
        "build.gradle.kts",
        "settings.gradle",
        "settings.gradle.kts",
    ),
    "ruff": ("pyproject.toml", "ruff.toml", ".ruff.toml", "requirements.txt", "setup.py"),
    "rustfmt": ("cargo.toml", "rustfmt.toml", ".rustfmt.toml"),
    "gofmt": ("go.mod", "go.work"),
    "oxfmt": (
        "package.json",
        "tsconfig.json",
        "jsconfig.json",
        "deno.json",
        "deno.jsonc",
        ".oxfmtrc.json",
        ".oxfmtrc.jsonc",
        "oxfmt.config.ts",
        "oxfmt.config.mts",
        "oxfmt.config.cts",
        "oxfmt.config.js",
        "oxfmt.config.mjs",
        "oxfmt.config.cjs",
    ),
}

DETECTION_EXTENSIONS = {
    "clang-format": frozenset(
        (".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx", ".m", ".mm")
    ),
    "ruff": frozenset((".py", ".pyi", ".pyw")),
    "google-java-format": frozenset((".java",)),
    "ktfmt": frozenset((".kt", ".kts")),
    "rustfmt": frozenset((".rs",)),
    "gofmt": frozenset((".go",)),
    "oxfmt": frozenset(
        (
            ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts",
            ".css", ".scss", ".less", ".html", ".vue", ".svelte",
            ".md", ".mdx", ".graphql", ".gql",
            ".json", ".jsonc", ".json5", ".yaml", ".yml",
        )
    ),
}


def preset_options() -> Tuple[TemplatePreset, ...]:
    return PRESETS


def preset_by_id(preset_id: str) -> TemplatePreset:
    for preset in PRESETS:
        if preset.id == preset_id:
            return preset
    return PRESETS[0]


def existing_strategy_options() -> Tuple[ExistingHandlingStrategy, ...]:
    return EXISTING_STRATEGIES


def existing_strategy_by_id(strategy_id: str) -> ExistingHandlingStrategy:
    for strategy in EXISTING_STRATEGIES:
        if strategy.id == strategy_id:
            return strategy
    return EXISTING_STRATEGIES[0]


def python_config_options(target_dir: str) -> Tuple[Tuple[str, str, str], ...]:
    from pathlib import Path

    path = Path(target_dir)
    preferred = "pyproject.toml" if (path / "pyproject.toml").is_file() else "ruff.toml"
    options = []
    for config_kind, caption, description in PYTHON_CONFIG_CHOICES:
        label = caption
        if config_kind == preferred:
            label = f"{caption} (Recommended)"
        options.append((config_kind, label, description))
    return tuple(options)
