from __future__ import annotations

import json
import logging
from typing import Optional

from arena_forge.core.domain import LanguageProfile, SessionSnapshot

from .workspace import WorkspaceLayout

_LOGGER = logging.getLogger(__name__)


class JsonSessionRepository:
    SCHEMA_VERSION = 1

    def __init__(self, layout: WorkspaceLayout, profiles: tuple[LanguageProfile, ...] = ()):
        self.layout = layout
        self.profiles = profiles

    def load(self, source_file: str) -> Optional[SessionSnapshot]:
        snapshot_path = self.layout.snapshot_path_for(source_file)
        if not snapshot_path.exists():
            return None
        try:
            payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
            return SessionSnapshot.from_mapping(payload)
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            _LOGGER.warning("Ignoring invalid session snapshot %s: %s", snapshot_path, exc)
            return None

    def save(self, session: SessionSnapshot) -> None:
        destination = self.layout.ensure_parent(self.layout.snapshot_path_for(session.source_file))
        payload = session.to_mapping()
        payload["schema_version"] = self.SCHEMA_VERSION
        serialized = json.dumps(payload, ensure_ascii=False, indent=2)
        if destination.exists() and destination.read_text(encoding="utf-8") == serialized:
            return
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.write_text(serialized, encoding="utf-8")
        temporary.replace(destination)
