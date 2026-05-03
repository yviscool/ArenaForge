import json
import unittest

from arena_forge.adapters.storage import JsonSessionRepository, WorkspaceLayout
from arena_forge.adapters.workspace import ContestWorkspaceScaffolder
from arena_forge.core.domain import ContestDescriptor, ContestProblem, LanguageProfile, TestCase
from tests.helpers import local_test_workspace


class ScaffolderTests(unittest.TestCase):
    def test_scaffold_creates_sources_and_metadata(self) -> None:
        with local_test_workspace("scaffolder") as root:
            layout = WorkspaceLayout()
            profiles = (LanguageProfile(name="C++", extensions=("cpp",), compile_cmd=None, run_cmd=None),)
            repository = JsonSessionRepository(layout, profiles=profiles)
            scaffolder = ContestWorkspaceScaffolder(layout, repository, profiles)
            contest = ContestDescriptor(
                contest_id="123",
                title="Round / 123",
                provider="codeforces",
                problems=(
                    ContestProblem(
                        index="A",
                        title="A",
                        samples=(TestCase(name="A-1", input_text="1", accepted_outputs=("2",)),),
                    ),
                ),
            )
            base = scaffolder.scaffold(root, contest, template_text="// template\n")
            self.assertTrue((base / "A.cpp").exists())
            self.assertTrue((base / "contest.json").exists())
            self.assertTrue((base / "_contest.sublime-settings").exists())
            metadata = json.loads((base / "contest.json").read_text(encoding="utf-8"))
            self.assertEqual(metadata["contest_id"], "123")


if __name__ == "__main__":
    unittest.main()
