import unittest

from arena_forge.adapters.storage.json_repository import JsonSessionRepository
from arena_forge.adapters.storage.workspace import WorkspaceLayout
from arena_forge.core.domain import LanguageProfile, SessionSnapshot, TestCase
from tests.helpers import local_test_workspace


class JsonRepositoryTests(unittest.TestCase):
    def test_save_and_load_snapshot(self) -> None:
        with local_test_workspace("json-repo") as root:
            source = root / "A.cpp"
            source.write_text("//", encoding="utf-8")
            layout = WorkspaceLayout()
            profiles = (
                LanguageProfile(name="C++", extensions=("cpp",), compile_cmd=None, run_cmd=None),
            )
            repository = JsonSessionRepository(layout, profiles=profiles)
            session = SessionSnapshot(
                source_file=str(source.resolve()),
                language="C++",
                tests=(TestCase(name="T1", input_text="1", accepted_outputs=("2",)),),
            )
            repository.save(session)
            loaded = repository.load(str(source))
            self.assertEqual(loaded, session)


if __name__ == "__main__":
    unittest.main()
