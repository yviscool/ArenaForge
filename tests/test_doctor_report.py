import unittest
from pathlib import Path

from arena_forge.adapters.sublime.doctor_report import build_doctor_report


class DoctorReportTests(unittest.TestCase):
    def test_report_includes_resource_and_backend_status(self) -> None:
        report = build_doctor_report(
            package_name="ArenaForge",
            package_root=Path("C:/Packages/ArenaForge"),
            package_resource_root="Packages/ArenaForge",
            discovered_resources={
                "TestSyntax.sublime-syntax": ["Packages/ArenaForge/TestSyntax.sublime-syntax"],
                "StressSyntax.sublime-syntax": ["Packages/ArenaForge/StressSyntax.sublime-syntax"],
            },
            settings={"run_settings": [{"name": "C++", "lint_compile_cmd": "g++"}]},
            contests_root="C:/Contests/ArenaForge",
            credential_backend="keyring",
            credential_available=True,
        )
        self.assertIn("ArenaForge Doctor", report)
        self.assertIn("Credential backend: keyring (available)", report)
        self.assertIn("Resource TestSyntax.sublime-syntax", report)
        self.assertIn("Run profiles", report)


if __name__ == "__main__":
    unittest.main()
