from __future__ import annotations

from typing import List, Tuple

from arena_forge.formatting.adapters.base import FormatterAdapter
from arena_forge.formatting.core.contracts import FormatRequest


class OxcFormatAdapter(FormatterAdapter):
    id = "oxfmt"
    display_name = "Oxc Formatter"
    selectors = (
        "source.js",
        "source.jsx",
        "source.ts",
        "source.tsx",
        "source.json",
        "source.jsonc",
        "source.json5",
        "source.css",
        "source.scss",
        "source.less",
        "source.graphql",
        "source.yaml",
        "source.toml",
        "text.html",
        "text.html.markdown",
        "text.html.vue",
        "text.html.svelte",
        "text.md",
        "text.mdx",
    )
    supports_range = False
    binary_names = ("oxfmt", "oxfmt.cmd", "oxfmt.exe")
    config_filenames = (
        ".oxfmtrc.json",
        ".oxfmtrc.jsonc",
        "oxfmt.config.ts",
        "oxfmt.config.mts",
        "oxfmt.config.cts",
        "oxfmt.config.js",
        "oxfmt.config.mjs",
        "oxfmt.config.cjs",
    )
    docs_url = "https://oxc.rs/docs/guide/usage/formatter.html"
    default_extension = ".ts"

    def project_binary_relpaths(self) -> Tuple[str, ...]:
        return (
            "node_modules/.bin/oxfmt.cmd",
            "node_modules/.bin/oxfmt",
        )

    def build_command(self, request: FormatRequest, extra_args: Tuple[str, ...]) -> List[str]:
        command = list(request.command_prefix)
        if request.stdin_filename:
            command.extend(["--stdin-filepath", request.stdin_filename])
        command.extend(extra_args)
        return command

    def build_install_help(self, platform_name: str, translate=None) -> str:
        del platform_name
        title = (
            translate("formatting.install_guide_recommended_project_install")
            if translate
            else "Recommended project-local install command:"
        )
        note = (
            translate("formatting.install_guide_official_docs_pnpm")
            if translate
            else "Official docs show pnpm examples;"
        )
        equivalent = (
            translate("formatting.install_guide_official_docs_equivalent")
            if translate
            else "the npm command above is the equivalent inference."
        )
        docs = translate("formatting.install_guide_docs", url=self.docs_url) if translate else f"Docs: {self.docs_url}"
        return "\n".join(
            (
                title,
                "  npm install --save-dev oxfmt",
                note,
                equivalent,
                docs,
            )
        )
