import unittest

from arena_forge.adapters.storage.workspace import WorkspaceLayout
from tests.helpers import local_test_workspace


class WorkspaceLayoutTests(unittest.TestCase):
    def test_next_gen_session_path_is_portable(self) -> None:
        layout = WorkspaceLayout()
        source = "C:/work/A.cpp"
        session_path = layout.session_path_for(source)
        self.assertTrue(
            str(session_path).replace("\\", "/").endswith(".arena-forge/tests/A.cpp.tests.json")
        )

    def test_resolve_session_path_points_to_current_index(self) -> None:
        with local_test_workspace("layout") as root:
            source = root / "A.cpp"
            source.write_text("", encoding="utf-8")
            layout = WorkspaceLayout()
            self.assertEqual(layout.resolve_session_path(str(source)), layout.session_path_for(str(source)))

    def test_snapshot_path_is_separate_from_tests_index(self) -> None:
        layout = WorkspaceLayout()
        source = "C:/work/A.cpp"
        snapshot_path = layout.snapshot_path_for(source)
        self.assertTrue(
            str(snapshot_path).replace("\\", "/").endswith(".arena-forge/sessions/A.cpp.session.json")
        )


if __name__ == "__main__":
    unittest.main()
