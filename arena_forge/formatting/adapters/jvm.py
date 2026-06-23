from __future__ import annotations

from typing import List, Tuple

from arena_forge.formatting.adapters.base import FormatterAdapter
from arena_forge.formatting.core.contracts import FormatRequest


class JvmJarFormatterAdapter(FormatterAdapter):
    project_jar_relpaths = ()  # type: Tuple[str, ...]

    def project_binary_relpaths(self) -> Tuple[str, ...]:
        return self.project_jar_relpaths

    def build_command(self, request: FormatRequest, extra_args: Tuple[str, ...]) -> List[str]:
        command = self._command_prefix_for_request(request)
        command.extend(extra_args)
        command.append("-")
        return command

    def build_install_help(self, platform_name: str, translate=None) -> str:
        del platform_name
        jar_path = self.project_jar_relpaths[0]
        auto_detect = self._help_line(
            translate,
            "formatting.install_guide_project_auto_detect_path",
            "Project-local auto-detect path:",
        )
        override = self._help_line(
            translate,
            "formatting.install_guide_recommended_command_override",
            "Recommended command override:",
        )
        docs = self._help_line(
            translate, "formatting.install_guide_docs", "Docs: {url}", url=self.docs_url
        )
        return "\n".join(
            (
                auto_detect,
                f"  {jar_path}",
                override,
                self._command_override_example(jar_path),
                docs,
            )
        )

    def _command_prefix_for_request(self, request: FormatRequest) -> List[str]:
        command_prefix = request.command_prefix
        if len(command_prefix) == 1 and command_prefix[0].lower().endswith(".jar"):
            return ["java", "-jar", command_prefix[0]]
        return list(command_prefix)

    def _command_override_example(self, jar_path: str) -> str:
        return (
            f'  "formatting": {{ "commands": {{ "{self.id}": ["java", "-jar", '
            f'"{jar_path}"] }} }}'
        )
