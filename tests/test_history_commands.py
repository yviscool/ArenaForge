import sys
import types
import unittest

sys.modules.setdefault(
    "sublime",
    types.SimpleNamespace(status_message=lambda _: None, platform=lambda: "windows"),
)
sys.modules.setdefault("sublime_plugin", types.SimpleNamespace(TextCommand=object))


class HistoryCommandTests(unittest.TestCase):
    def test_history_source_key_constant(self) -> None:
        from arena_forge.adapters.sublime.history_commands import HISTORY_SOURCE_FILE_KEY

        self.assertEqual(HISTORY_SOURCE_FILE_KEY, "arena_forge.history_source_file")

    def test_build_history_report_handles_empty_snapshot(self) -> None:
        from arena_forge.adapters.sublime.history_commands import build_history_report

        report = build_history_report("main.cpp", None, product_name="ArenaForge")
        self.assertIn("ArenaForge", report)
        self.assertIn("main.cpp", report)

    def test_build_history_report_renders_latest_first(self) -> None:
        from arena_forge.adapters.sublime.history_commands import build_history_report
        from arena_forge.core.domain import (
            OutputEvaluation,
            OutputMismatch,
            OutputReferenceKind,
            RunHistoryEntry,
            SessionSnapshot,
            Verdict,
        )

        snapshot = SessionSnapshot(
            source_file="main.cpp",
            language="C++",
            run_history=(
                RunHistoryEntry(
                    test_name="Test 1",
                    output_text="older",
                    verdict=Verdict.UNKNOWN,
                    runtime_ms=10,
                    return_code=0,
                ),
                RunHistoryEntry(
                    test_name="Test 2",
                    output_text="newer",
                    verdict=Verdict.REJECTED,
                    runtime_ms=12,
                    return_code=0,
                    evaluation=OutputEvaluation(
                        checker_name="normalized_text",
                        verdict=Verdict.REJECTED,
                        reference_kind=OutputReferenceKind.ACCEPTED,
                        normalized_actual="newer",
                        normalized_expected="expected",
                        mismatch=OutputMismatch(
                            line=1,
                            column=2,
                            expected_excerpt="expected",
                            actual_excerpt="newer",
                        ),
                    ),
                ),
            ),
        )
        report = build_history_report("main.cpp", snapshot, product_name="ArenaForge")
        self.assertLess(report.index("Test 2"), report.index("Test 1"))
        self.assertIn("newer", report)
        self.assertIn("first mismatch at line 1, column 2", report)
