from __future__ import annotations

from typing import List, Tuple

from arena_forge.formatting.adapters.base import FormatterAdapter
from arena_forge.formatting.core.contracts import FormatRequest


class GoogleJavaFormatAdapter(FormatterAdapter):
    id = "google-java-format"
    display_name = "google-java-format"
    selectors = ("source.java",)
    supports_range = False
    binary_names = ("google-java-format", "google-java-format.exe")
    docs_url = "https://github.com/google/google-java-format"
    default_extension = ".java"

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
                '  "formatting": { "commands": { "google-java-format": ["java", "-jar", "tools/google-java-format.jar"] } }',
                f"Docs: {self.docs_url}",
            )
        )
