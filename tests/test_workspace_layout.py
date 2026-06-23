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

    def test_snapshot_path_is_separate_from_tests_index(self) -> None:
        layout = WorkspaceLayout()
        source = "C:/work/A.cpp"
        snapshot_path = layout.snapshot_path_for(source)
        self.assertTrue(
            str(snapshot_path).replace("\\", "/").endswith(".arena-forge/sessions/A.cpp.session.json")
        )

    def test_algorithm_properties_path_uses_portable_json_suffix(self) -> None:
        layout = WorkspaceLayout()
        properties_path = layout.algorithm_properties_path_for("C:/work/snippet.cpp")
        self.assertTrue(str(properties_path).replace("\\", "/").endswith("snippet.cpp.cpp.properties.json"))


if __name__ == "__main__":
    unittest.main()
