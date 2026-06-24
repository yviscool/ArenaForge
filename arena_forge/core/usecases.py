from __future__ import annotations

from typing import Sequence

from .domain import LanguageProfile, SessionSnapshot
from .ports import SessionRepository
from .services import infer_language


class SessionService:
    def __init__(self, repository: SessionRepository) -> None:
        self.repository = repository

    def ensure_session(self, source_file: str, profiles: Sequence[LanguageProfile]) -> SessionSnapshot:
        session = self.repository.load(source_file)
        if session is not None:
            return session
        language = infer_language(source_file, profiles)
        session = SessionSnapshot(source_file=source_file, language=language, tests=())
        self.repository.save(session)
        return session
