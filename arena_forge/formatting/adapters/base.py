from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from arena_forge.formatting.core.contracts import FormatRequest
from arena_forge.formatting.core.discovery import find_named_file_upwards


class FormatterAdapter(ABC):
    id = ""
    display_name = ""
    selectors = ()  # type: Tuple[str, ...]
    supports_range = False
    supports_multiple_ranges = False
    binary_names = ()  # type: Tuple[str, ...]
    config_filenames = ()  # type: Tuple[str, ...]
    docs_url = ""
    default_extension = ".txt"

    def project_binary_relpaths(self) -> Tuple[str, ...]:
        return ()

    def discover_config(self, start_dir: Optional[str]) -> Optional[str]:
        return find_named_file_upwards(start_dir, self.config_filenames)

    @abstractmethod
    def build_command(self, request: FormatRequest, extra_args: Tuple[str, ...]) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    def build_install_help(self, platform_name: str, translate=None) -> str:
        raise NotImplementedError

    @staticmethod
    def _help_line(translate, key: str, fallback: str, **kwargs) -> str:
        if translate:
            return translate(key, **kwargs)
        return fallback.format(**kwargs) if kwargs else fallback

    def _build_standard_install_help(
        self,
        install_command: str,
        *,
        translate=None,
        note_key: str = "",
        note_fallback: str = "",
        alternative_key: str = "",
        alternative_fallback: str = "",
        alternative_command: str = "",
    ) -> str:
        title = self._help_line(
            translate, "formatting.install_guide_recommended_install", "Recommended install command:"
        )
        docs = self._help_line(
            translate, "formatting.install_guide_docs", "Docs: {url}", url=self.docs_url
        )
        parts = [title, f"  {install_command}"]
        if note_key:
            parts.append(self._help_line(translate, note_key, note_fallback))
        if alternative_key and alternative_command:
            parts.append(self._help_line(translate, alternative_key, alternative_fallback))
            parts.append(f"  {alternative_command}")
        parts.append(docs)
        return "\n".join(parts)
