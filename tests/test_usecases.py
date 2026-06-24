import unittest

from arena_forge.core.domain import LanguageProfile, SessionSnapshot
from arena_forge.core.usecases import SessionService


class _StubRepository:
    def __init__(self):
        self._store = {}

    def load(self, source_file):
        return self._store.get(source_file)

    def save(self, session):
        self._store[session.source_file] = session


class UsecaseTests(unittest.TestCase):
    def test_ensure_session_creates_new_when_missing(self) -> None:
        repo = _StubRepository()
        profiles = (LanguageProfile(name="C++", extensions=("cpp",), compile_cmd="g++", run_cmd="./a.out"),)
        service = SessionService(repository=repo)
        session = service.ensure_session("A.cpp", profiles)
        self.assertEqual(session.source_file, "A.cpp")
        self.assertEqual(session.language, "cpp")
        self.assertEqual(session.tests, ())
        self.assertIs(service.ensure_session("A.cpp", profiles), session)

    def test_ensure_session_returns_existing(self) -> None:
        repo = _StubRepository()
        existing = SessionSnapshot(source_file="A.cpp", language="C++", tests=())
        repo.save(existing)
        service = SessionService(repository=repo)
        self.assertIs(service.ensure_session("A.cpp", ()), existing)


if __name__ == "__main__":
    unittest.main()
