import unittest

from arena_forge.adapters.runners.diagnostics import (
    CompilerDiagnosticsService,
    DiagnosticsScratchWorkspace,
    parse_compiler_issues,
)
from arena_forge.core.domain import DiagnosticSeverity
from tests.helpers import local_test_workspace


class DiagnosticsRunnerTests(unittest.TestCase):
    def test_parse_compiler_issues_filters_by_source_and_severity(self) -> None:
        source = r"C:\repo\cmp_sense\amin.cpp"
        output = "\n".join(
            [
                r"C:\repo\cmp_sense\amin.cpp:3:9: warning: unused variable 'x'",
                r"C:\repo\cmp_sense\amin.cpp:8:4: error: expected ';' after expression",
                r"C:\repo\other.cpp:1:1: error: ignored",
            ]
        )
        issues = parse_compiler_issues(output, source)
        self.assertEqual(len(issues), 2)
        self.assertEqual(issues[0].severity, DiagnosticSeverity.WARNING)
        self.assertEqual(issues[1].severity, DiagnosticSeverity.ERROR)
        self.assertEqual(issues[1].line, 8)

    def test_scratch_workspace_writes_source_under_cmp_sense(self) -> None:
        with local_test_workspace("diagnostics-scratch") as root:
            workspace = DiagnosticsScratchWorkspace(root)
            scratch_path = workspace.write_source("int main() {}\n")
            self.assertEqual(scratch_path, root / "cmp_sense" / "amin.cpp")
            self.assertEqual(scratch_path.read_text(encoding="utf-8"), "int main() {}\n")

    def test_scratch_workspace_sanitizes_unique_labels(self) -> None:
        with local_test_workspace("diagnostics-scratch-labels") as root:
            workspace = DiagnosticsScratchWorkspace(root)
            scratch_path = workspace.write_source("int main() {}\n", label="view:12/34")
            self.assertEqual(scratch_path.name, "view_12_34.cpp")
            self.assertEqual(scratch_path.read_text(encoding="utf-8"), "int main() {}\n")

    def test_service_runs_command_and_parses_output(self) -> None:
        with local_test_workspace("diagnostics-service") as root:
            service = CompilerDiagnosticsService(
                platform_name="windows",
                scratch_workspace=DiagnosticsScratchWorkspace(root),
            )
            compile_cmd = (
                'python -c "import pathlib;'
                "p = pathlib.Path(r'{source_file}');"
                "print(f'{{p}}:{{2}}:{{5}}: warning: sample warning');"
                "print(f'{{p}}:{{4}}:{{1}}: error: sample error')\""
            )
            report = service.run(
                compile_cmd=compile_cmd,
                source_text="int main() {}\n",
                source_file_dir=str(root),
            )
            self.assertEqual(len(report.command), 3)
            self.assertEqual(len(report.issues), 2)
            self.assertEqual(report.issues[0].severity, DiagnosticSeverity.WARNING)
            self.assertEqual(report.issues[1].message, "sample error")


if __name__ == "__main__":
    unittest.main()
