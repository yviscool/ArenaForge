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

    def build_install_help(self, platform_name: str) -> str:
        del platform_name
        jar_path = self.project_jar_relpaths[0]
        return "\n".join(
            (
                "Project-local auto-detect path:",
                f"  {jar_path}",
                "Recommended command override:",
                self._command_override_example(jar_path),
                f"Docs: {self.docs_url}",
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
