from __future__ import annotations

from typing import List, Tuple

from arena_forge.formatting.adapters.base import FormatterAdapter
from arena_forge.formatting.core.contracts import FormatRequest
from arena_forge.formatting.core.text import utf8_byte_offset


class ClangFormatAdapter(FormatterAdapter):
    id = "clang-format"
    display_name = "clang-format"
    selectors = ("source.c", "source.c++", "source.objc", "source.objc++")
    supports_range = True
    supports_multiple_ranges = True
    binary_names = ("clang-format", "clang-format.exe")
    config_filenames = (".clang-format", "_clang-format")
    docs_url = "https://clang.llvm.org/docs/ClangFormat.html"
    default_extension = ".cpp"

    def build_command(self, request: FormatRequest, extra_args: Tuple[str, ...]) -> List[str]:
        command = list(request.command_prefix)
        if request.stdin_filename:
            command.extend(["--assume-filename", request.stdin_filename])
        if request.selection_mode == "selection":
            for text_range in request.ranges:
                byte_start = utf8_byte_offset(request.snapshot.text, text_range.start)
                byte_end = utf8_byte_offset(request.snapshot.text, text_range.end)
                command.extend(
                    [
                        "--offset",
                        str(byte_start),
                        "--length",
                        str(byte_end - byte_start),
                    ]
                )
        command.extend(extra_args)
        return command

    def build_install_help(self, platform_name: str, translate=None) -> str:
        if platform_name == "Windows":
            command = "winget install LLVM.LLVM"
        elif platform_name == "Darwin":
            command = "brew install clang-format"
        else:
            command = "sudo apt install clang-format"
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

        return "\n".join(
            (
                title,
                f"  {command}",
                docs,
            )
        )
