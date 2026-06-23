from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from arena_forge.product import (
    DEFAULT_ALGORITHM_PROPERTIES_SUFFIX,
    DEFAULT_CONTESTS_ROOT,
    DEFAULT_SESSION_RELATIVE_DIR,
    DEFAULT_TESTS_FILE_SUFFIX,
    DEFAULT_TESTS_RELATIVE_DIR,
)


@dataclass(frozen=True)
class WorkspaceLayout:
    tests_relative_dir: str = DEFAULT_TESTS_RELATIVE_DIR
    session_relative_dir: str = DEFAULT_SESSION_RELATIVE_DIR
    tests_file_suffix: str = DEFAULT_TESTS_FILE_SUFFIX
    algorithm_properties_suffix: str = DEFAULT_ALGORITHM_PROPERTIES_SUFFIX
    contests_root: str = DEFAULT_CONTESTS_ROOT

    @classmethod
    def from_settings(cls, settings: Mapping[str, object]) -> "WorkspaceLayout":
        return cls(
            tests_relative_dir=str(settings.get("tests_relative_dir") or DEFAULT_TESTS_RELATIVE_DIR),
            session_relative_dir=str(settings.get("session_relative_dir") or DEFAULT_SESSION_RELATIVE_DIR),
            tests_file_suffix=str(settings.get("tests_file_suffix") or DEFAULT_TESTS_FILE_SUFFIX),
            algorithm_properties_suffix=str(
                settings.get("algorithm_properties_suffix") or DEFAULT_ALGORITHM_PROPERTIES_SUFFIX
            ),
            contests_root=str(settings.get("contests_root") or DEFAULT_CONTESTS_ROOT),
        )

    def _tests_directory(self, source_file: str) -> Path:
        return Path(source_file).resolve().parent / self.tests_relative_dir

    def _session_directory(self, source_file: str) -> Path:
        return Path(source_file).resolve().parent / self.session_relative_dir

    def session_path_for(self, source_file: str) -> Path:
        base = Path(source_file).resolve()
        return self._tests_directory(source_file) / f"{base.name}{self.tests_file_suffix}"

    def snapshot_path_for(self, source_file: str) -> Path:
        base = Path(source_file).resolve()
        return self._session_directory(source_file) / f"{base.name}.session.json"

    def ensure_parent(self, destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        return destination

    def algorithm_properties_path_for(self, snippet_file: str) -> Path:
        snippet_path = Path(snippet_file)
        return snippet_path.with_name(snippet_path.name + self.algorithm_properties_suffix)

    def expanded_contests_root(self) -> Path:
        return Path(self.contests_root).expanduser()

    def write_tests_index(self, source_file: str, tests_payload: list[dict[str, object]]) -> Path:
        destination = self.ensure_parent(self.session_path_for(source_file))
        serialized = json.dumps(tests_payload, ensure_ascii=False, indent=2)
        if not destination.exists() or destination.read_text(encoding="utf-8") != serialized:
            destination.write_text(serialized, encoding="utf-8")
        return destination
