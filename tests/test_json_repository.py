import unittest

from arena_forge.adapters.storage.json_repository import JsonSessionRepository
from arena_forge.adapters.storage.workspace import WorkspaceLayout
from arena_forge.core.domain import (
    LanguageProfile,
    OutputEvaluation,
    OutputMismatch,
    OutputReferenceKind,
    RunHistoryEntry,
    SessionSnapshot,
    TestCase,
    Verdict,
)
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
                run_history=(
                    RunHistoryEntry(
                        test_name="T1",
                        output_text="3",
                        verdict=Verdict.REJECTED,
                        runtime_ms=12,
                        return_code=0,
                        evaluation=OutputEvaluation(
                            checker_name="normalized_text",
                            verdict=Verdict.REJECTED,
                            reference_kind=OutputReferenceKind.ACCEPTED,
                            normalized_actual="3",
                            normalized_expected="2",
                            mismatch=OutputMismatch(
                                line=1,
                                column=1,
                                expected_excerpt="2",
                                actual_excerpt="3",
                            ),
                        ),
                    ),
                ),
            )
            repository.save(session)
            loaded = repository.load(str(source))
            self.assertEqual(loaded, session)

    def test_load_returns_none_for_invalid_snapshot_payload(self) -> None:
        with local_test_workspace("json-repo-invalid") as root:
            source = root / "A.cpp"
            source.write_text("//", encoding="utf-8")
            repository = JsonSessionRepository(WorkspaceLayout())
            snapshot_path = repository.layout.snapshot_path_for(str(source))
            snapshot_path.parent.mkdir(parents=True, exist_ok=True)
            snapshot_path.write_text("{bad json", encoding="utf-8")

            self.assertIsNone(repository.load(str(source)))


if __name__ == "__main__":
    unittest.main()
