from __future__ import annotations

from typing import List, Optional, Tuple

from arena_forge.formatting.adapters.base import FormatterAdapter
from arena_forge.formatting.core.contracts import FormatRequest
from arena_forge.formatting.core.discovery import (
    find_named_file_upwards,
    iter_ancestor_dirs,
    pyproject_has_tool_table,
)


class RuffFormatAdapter(FormatterAdapter):
    id = "ruff"
    display_name = "Ruff Formatter"
    selectors = ("source.python",)
    supports_range = True
    binary_names = ("ruff", "ruff.exe")
    docs_url = "https://docs.astral.sh/ruff/formatter/"
    default_extension = ".py"

    def project_binary_relpaths(self) -> Tuple[str, ...]:
        return (
            ".venv/Scripts/ruff.exe",
            "venv/Scripts/ruff.exe",
            ".venv/bin/ruff",
            "venv/bin/ruff",
        )

    def discover_config(self, start_dir: Optional[str]) -> Optional[str]:
        direct = find_named_file_upwards(start_dir, (".ruff.toml", "ruff.toml"))
        if direct:
            return direct

        for ancestor in iter_ancestor_dirs(start_dir):
            candidate = ancestor / "pyproject.toml"
            if candidate.is_file() and pyproject_has_tool_table(str(candidate), "tool", "ruff"):
                return str(candidate)

        return None

    def build_command(self, request: FormatRequest, extra_args: Tuple[str, ...]) -> List[str]:
        command = list(request.command_prefix)
        command.append("format")
        if request.stdin_filename:
            command.extend(["--stdin-filename", request.stdin_filename])
        if request.selection_mode == "selection" and request.ranges:
            text_range = request.ranges[0]
            command.extend(
                [
                    "--range",
                    f"{text_range.start_line}:{text_range.start_col}-{text_range.end_line}:{text_range.end_col}",
                ]
            )
        command.extend(extra_args)
        command.append("-")
        return command

    def build_install_help(self, platform_name: str, translate=None) -> str:
        del platform_name
        title = (
            translate("formatting.install_guide_recommended_install")
            if translate
            else "Recommended install command:"
        )
        alternative = (
            translate("formatting.install_guide_recommended_project_install")
            if translate
            else "Project-local alternative:"
        )
        docs = translate("formatting.install_guide_docs", url=self.docs_url) if translate else f"Docs: {self.docs_url}"
        return "\n".join(
            (
                title,
                "  uv tool install ruff",
                alternative,
                "  uv add --dev ruff",
                docs,
            )
        )
