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
            progress_events = []
            base = scaffolder.scaffold(
                root,
                contest,
                template_text="// template\n",
                progress=lambda completed, total, problem: progress_events.append((completed, total, problem)),
            )
            self.assertTrue((base / "A.cpp").exists())
            self.assertTrue((base / "contest.json").exists())
            self.assertTrue((base / "_contest.sublime-settings").exists())
            metadata = json.loads((base / "contest.json").read_text(encoding="utf-8"))
            self.assertEqual(metadata["contest_id"], "123")
            self.assertEqual(metadata["language_id"], "cpp")
            self.assertEqual(progress_events, [(1, 1, "A")])

    def test_scaffold_uses_language_profile_template(self) -> None:
        with local_test_workspace("scaffolder-java") as root:
            layout = WorkspaceLayout()
            profiles = (
                LanguageProfile(
                    name="Java",
                    extensions=("java",),
                    compile_cmd=None,
                    run_cmd=None,
                    id="java",
                    template_path="templates/contest/Main.java",
                ),
            )
            repository = JsonSessionRepository(layout, profiles=profiles)
            scaffolder = ContestWorkspaceScaffolder(layout, repository, profiles)
            contest = ContestDescriptor(
                contest_id="123",
                title="Round / 123",
                provider="codeforces",
                problems=(ContestProblem(index="A", title="A", samples=()),),
            )

            base = scaffolder.scaffold(root, contest, language_id="java")

            java_source = (base / "A.java").read_text(encoding="utf-8")
            self.assertIn("public class A", java_source)


if __name__ == "__main__":
    unittest.main()
