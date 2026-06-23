from __future__ import annotations

from typing import List, Tuple

from arena_forge.formatting.adapters.base import FormatterAdapter
from arena_forge.formatting.core.contracts import FormatRequest


class GoFormatAdapter(FormatterAdapter):
    id = "gofmt"
    display_name = "gofmt"
    selectors = ("source.go",)
    supports_range = False
    binary_names = ("gofmt", "gofmt.exe")
    docs_url = "https://pkg.go.dev/cmd/gofmt"
    default_extension = ".go"

    def build_command(
        self,
        request: FormatRequest,
        extra_args: Tuple[str, ...],
    ) -> List[str]:
        command = list(request.command_prefix)
        command.extend(extra_args)
        return command

    def build_install_help(self, platform_name: str, translate=None) -> str:
        if platform_name == "Windows":
            command = "winget install GoLang.Go"
        elif platform_name == "Darwin":
            command = "brew install go"
        else:
            command = "sudo apt install golang-go"
        return self._build_standard_install_help(
            command,
            translate=translate,
            note_key="formatting.install_guide_official_docs_equivalent",
            note_fallback="gofmt ships with the Go toolchain.",
        )
