from __future__ import annotations

from typing import List, Tuple

from arena_forge.formatting.adapters.base import FormatterAdapter
from arena_forge.formatting.core.contracts import FormatRequest


class KtfmtAdapter(FormatterAdapter):
    id = "ktfmt"
    display_name = "ktfmt"
    selectors = ("source.kotlin",)
    supports_range = False
    binary_names = ("ktfmt", "ktfmt.exe")
    docs_url = "https://github.com/facebook/ktfmt"
    default_extension = ".kt"

    def build_command(self, request: FormatRequest, extra_args: Tuple[str, ...]) -> List[str]:
        command = list(request.command_prefix)
        command.extend(extra_args)
        command.append("-")
        return command

    def build_install_help(self, platform_name: str) -> str:
        del platform_name
        return "\n".join(
            (
                "Recommended command override:",
                '  "formatting": { "commands": { "ktfmt": ["java", "-jar", "tools/ktfmt.jar"] } }',
                f"Docs: {self.docs_url}",
            )
        )
