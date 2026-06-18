from __future__ import annotations

from typing import List, Tuple

from arena_forge.formatting.adapters.base import FormatterAdapter
from arena_forge.formatting.core.contracts import FormatRequest
from arena_forge.formatting.core.discovery import find_rust_edition


class RustFormatAdapter(FormatterAdapter):
    id = "rustfmt"
    display_name = "rustfmt"
    selectors = ("source.rust",)
    supports_range = False
    binary_names = ("rustfmt", "rustfmt.exe")
    config_filenames = ("rustfmt.toml", ".rustfmt.toml")
    docs_url = "https://github.com/rust-lang/rustfmt"
    default_extension = ".rs"

    def build_command(
        self,
        request: FormatRequest,
        extra_args: Tuple[str, ...],
    ) -> List[str]:
        command = list(request.command_prefix)
        command.extend(["--emit", "stdout"])
        edition = find_rust_edition(request.cwd)
        if edition:
            command.extend(["--edition", edition])
        command.extend(extra_args)
        return command

    def build_install_help(self, platform_name: str, translate=None) -> str:
        del platform_name
        title = (
            translate("formatting.install_guide_recommended_install")
            if translate
            else "Recommended install command:"
        )
        docs = (
            translate("formatting.install_guide_docs", url=self.docs_url)
            if translate
            else f"Docs: {self.docs_url}"
        )
        note = (
            translate("formatting.install_guide_official_docs_equivalent")
            if translate
            else "rustfmt is installed as a Rust toolchain component."
        )
        return "\n".join(
            (
                title,
                "  rustup component add rustfmt",
                note,
                docs,
            )
        )
