from __future__ import annotations

import json
from typing import Optional

from arena_forge.core.domain import LanguageProfile, SessionSnapshot

from .workspace import WorkspaceLayout


class JsonSessionRepository:
    SCHEMA_VERSION = 1

    def __init__(self, layout: WorkspaceLayout, profiles: tuple[LanguageProfile, ...] = ()):
        self.layout = layout
        self.profiles = profiles

    def load(self, source_file: str) -> Optional[SessionSnapshot]:
        snapshot_path = self.layout.snapshot_path_for(source_file)
        if not snapshot_path.exists():
            return None
        payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
        return SessionSnapshot.from_mapping(payload)

    def save(self, session: SessionSnapshot) -> None:
        destination = self.layout.ensure_parent(self.layout.snapshot_path_for(session.source_file))
        payload = session.to_mapping()
        payload["schema_version"] = self.SCHEMA_VERSION
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(destination)
