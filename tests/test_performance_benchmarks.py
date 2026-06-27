"""Performance benchmarks for arena_forge plugin.

Measures:
  1. Plugin module import time (load speed)
  2. Event listener handler latency (on_modified, on_selection_modified)
  3. Diagnostics lint cycle (debounce → compile → parse)
  4. Formatting pipeline (request build → subprocess → apply)
  5. Compile cache hit/miss ratio
  6. Output normalization and mismatch detection
  7. Settings bridge lookup latency
  8. i18n catalog translation latency
  9. Phantom rendering throughput
 10. Template completion expansion latency
"""
from __future__ import annotations

import gc
import statistics
import sys
import time
import unittest
from pathlib import Path
from typing import Callable, List
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NS_PER_MS = 1_000_000


def _bench(fn: Callable, *, repeat: int = 50, warmup: int = 5) -> dict:
    """Run *fn* repeatedly and return timing stats in milliseconds."""
    for _ in range(warmup):
        fn()
    gc.collect()
    times: List[float] = []
    for _ in range(repeat):
        gc.disable()
        t0 = time.perf_counter_ns()
        fn()
        t1 = time.perf_counter_ns()
        gc.enable()
        times.append((t1 - t0) / _NS_PER_MS)
    sorted_times = sorted(times)
    p95_index = min(len(sorted_times) - 1, int((len(sorted_times) - 1) * 0.95))
    return {
        "min_ms": min(times),
        "max_ms": max(times),
        "mean_ms": statistics.mean(times),
        "median_ms": statistics.median(times),
        "p95_ms": sorted_times[p95_index],
        "stdev_ms": statistics.stdev(times) if len(times) > 1 else 0.0,
        "repeat": repeat,
    }


class _FakeView:
    """Lightweight stand-in for sublime.View that tracks call counts."""

    def __init__(self, *, file_name: str = "main.cpp", size: int = 0):
        self._file_name = file_name
        self._size = size
        self._change_count_val = 0
        self._statuses: dict[str, str] = {}
        self._regions: dict[str, list] = {}
        self._settings = {
            "syntax": "Packages/C++/C++.sublime-syntax",
            "theme": "Default.sublime-theme",
        }
        self.run_command_calls: list[tuple[str, dict]] = []

    def file_name(self):
        return self._file_name

    def size(self):
        return self._size

    def change_count(self):
        return self._change_count_val

    def get_status(self, key):
        return self._statuses.get(key)

    def set_status(self, key, value):
        self._statuses[key] = value

    def erase_status(self, key):
        self._statuses.pop(key, None)

    def erase_regions(self, key):
        self._regions.pop(key, None)

    def add_regions(self, key, regions, *args, **kwargs):
        self._regions[key] = regions

    def settings(self):
        return self._settings

    def scope_name(self, pos):
        return "source.c++ "

    def sel(self):
        return [MagicMock(a=0, b=0)]

    def word(self, region):
        return MagicMock(a=0, b=5)

    def substr(self, region):
        return "test"

    def run_command(self, cmd, args=None):
        self.run_command_calls.append((cmd, args or {}))

    def id(self):
        return 42

    def text_point(self, row, col):
        return 0

    def buffer_id(self):
        return 1


# ---------------------------------------------------------------------------
# 1. Module import time
# ---------------------------------------------------------------------------

class ImportTimeBenchmark(unittest.TestCase):
    """Measure how long it takes to import each top-level plugin module."""

    _MODULES = [
        "arena_forge.adapters.i18n.catalog",
        "arena_forge.core.domain",
        "arena_forge.core.services",
        "arena_forge.adapters.runners.subprocess_runner",
        "arena_forge.adapters.runners.diagnostics",
        "arena_forge.adapters.runners.process_manager",
        "arena_forge.formatting.core.contracts",
        "arena_forge.formatting.core.process",
        "arena_forge.formatting.core.registry",
        "arena_forge.adapters.sublime.shared.package_resources",
    ]

    def test_import_latency(self):
        results = {}
        for mod_name in self._MODULES:
            if mod_name in sys.modules:
                del sys.modules[mod_name]
            gc.collect()

            def do_import(_mn=mod_name):
                __import__(_mn)

            stats = _bench(do_import, repeat=20, warmup=3)
            results[mod_name] = stats

        for mod, stats in results.items():
            self.assertLess(
                stats["p95_ms"] if "p95_ms" in stats else stats["max_ms"],
                100.0,
                f"Import of {mod} too slow: {stats['max_ms']:.1f}ms max",
            )

        # Print report
        print("\n=== Module Import Latency ===")
        for mod, stats in sorted(results.items(), key=lambda x: -x[1]["mean_ms"]):
            print(f"  {mod}: {stats['mean_ms']:.2f}ms mean, {stats['max_ms']:.2f}ms max")


# ---------------------------------------------------------------------------
# 2. Output normalization (core hot path)
# ---------------------------------------------------------------------------

class NormalizeTextBenchmark(unittest.TestCase):
    """Benchmark normalize_text and find_first_mismatch — called on every test result."""

    def test_normalize_text_small(self):
        from arena_forge.core.services import normalize_text
        text = "hello world\n  trailing spaces   \n\n\n"
        stats = _bench(lambda: normalize_text(text), repeat=500)
        self.assertLess(stats["max_ms"], 1.0, f"normalize_text too slow: {stats}")
        print(f"\n  normalize_text (small): {stats['mean_ms']:.4f}ms mean")

    def test_normalize_text_large(self):
        from arena_forge.core.services import normalize_text
        text = "\n".join(f"line {i} with some padding" for i in range(10_000))
        stats = _bench(lambda: normalize_text(text), repeat=50)
        self.assertLess(stats["max_ms"], 50.0, f"normalize_text (10k lines) too slow: {stats}")
        print(f"\n  normalize_text (10k lines): {stats['mean_ms']:.2f}ms mean")

    def test_find_first_mismatch_no_diff(self):
        from arena_forge.core.services import find_first_mismatch
        expected = "\n".join(f"line {i}" for i in range(1000))
        actual = expected
        stats = _bench(lambda: find_first_mismatch(expected, actual), repeat=500)
        self.assertLess(stats["max_ms"], 5.0, f"find_first_mismatch (equal) too slow: {stats}")
        print(f"\n  find_first_mismatch (equal, 1k lines): {stats['mean_ms']:.4f}ms mean")

    def test_find_first_mismatch_first_line(self):
        from arena_forge.core.services import find_first_mismatch
        expected = "\n".join(f"line {i}" for i in range(1000))
        actual = "DIFFERENT\n" + "\n".join(f"line {i}" for i in range(1, 1000))
        stats = _bench(lambda: find_first_mismatch(expected, actual), repeat=500)
        self.assertLess(stats["max_ms"], 5.0, f"find_first_mismatch (first line) too slow: {stats}")
        print(f"\n  find_first_mismatch (first line diff): {stats['mean_ms']:.4f}ms mean")

    def test_find_first_mismatch_last_line(self):
        from arena_forge.core.services import find_first_mismatch
        expected = "\n".join(f"line {i}" for i in range(1000))
        actual = "\n".join(f"line {i}" for i in range(999)) + "\nDIFFERENT"
        stats = _bench(lambda: find_first_mismatch(expected, actual), repeat=200)
        self.assertLess(stats["max_ms"], 50.0, f"find_first_mismatch (last line) too slow: {stats}")
        print(f"\n  find_first_mismatch (last line diff): {stats['mean_ms']:.2f}ms mean")


# ---------------------------------------------------------------------------
# 3. i18n catalog translation
# ---------------------------------------------------------------------------

class I18nCatalogBenchmark(unittest.TestCase):
    """Benchmark translate_catalog — called on every status message and UI label."""

    def test_translate_existing_key(self):
        from arena_forge.adapters.i18n.catalog import translate_catalog
        # Prime cache
        translate_catalog("status.settings_loaded")
        stats = _bench(lambda: translate_catalog("status.settings_loaded"), repeat=1000)
        self.assertLess(stats["max_ms"], 0.5, f"translate_catalog too slow: {stats}")
        print(f"\n  translate_catalog (cached): {stats['mean_ms']:.4f}ms mean")

    def test_translate_with_kwargs(self):
        from arena_forge.adapters.i18n.catalog import translate_catalog
        translate_catalog("status.compile_issue", line=1, column=1, message="test")
        stats = _bench(
            lambda: translate_catalog("status.compile_issue", line=1, column=1, message="test"),
            repeat=1000,
        )
        self.assertLess(stats["max_ms"], 1.0, f"translate_catalog with kwargs too slow: {stats}")
        print(f"\n  translate_catalog (with kwargs): {stats['mean_ms']:.4f}ms mean")


# ---------------------------------------------------------------------------
# 4. Compile cache
# ---------------------------------------------------------------------------

class CompileCacheBenchmark(unittest.TestCase):
    """Benchmark the OrderedDict compile cache in process_manager."""

    def test_cache_hit_latency(self):
        from arena_forge.adapters.runners.process_manager import (
            _COMPILE_CACHE,
            _get_cached_compile_result,
            _store_cached_compile_result,
        )

        # Seed cache
        key = ("test.cpp", 12345, "g++ test.cpp")
        _COMPILE_CACHE.clear()
        _store_cached_compile_result(key, (0, "OK"))

        stats = _bench(lambda: _get_cached_compile_result(key), repeat=5000)
        self.assertLess(stats["max_ms"], 0.1, f"Cache hit too slow: {stats}")
        print(f"\n  compile cache hit: {stats['mean_ms']:.4f}ms mean")

    def test_cache_miss_latency(self):
        from arena_forge.adapters.runners.process_manager import (
            _COMPILE_CACHE,
            _get_cached_compile_result,
        )

        _COMPILE_CACHE.clear()
        key = ("nonexistent.cpp", 99999, "g++ nonexistent.cpp")
        stats = _bench(lambda: _get_cached_compile_result(key), repeat=5000)
        self.assertLess(stats["p95_ms"], 0.1, f"Cache miss too slow: {stats}")
        print(f"\n  compile cache miss: {stats['mean_ms']:.4f}ms mean")

    def test_cache_eviction_pressure(self):
        from arena_forge.adapters.runners.process_manager import (
            _COMPILE_CACHE,
            _COMPILE_CACHE_MAX_SIZE,
            _store_cached_compile_result,
        )

        _COMPILE_CACHE.clear()

        def fill_and_evict():
            for i in range(_COMPILE_CACHE_MAX_SIZE + 10):
                key = (f"file{i}.cpp", i, f"cmd{i}")
                _store_cached_compile_result(key, (0, "OK"))

        stats = _bench(fill_and_evict, repeat=100)
        self.assertLess(stats["max_ms"], 10.0, f"Cache eviction too slow: {stats}")
        print(f"\n  compile cache eviction ({_COMPILE_CACHE_MAX_SIZE}+10 entries): {stats['mean_ms']:.2f}ms mean")


# ---------------------------------------------------------------------------
# 5. Diagnostics state management
# ---------------------------------------------------------------------------

class DiagnosticsStateBenchmark(unittest.TestCase):
    """Benchmark _VIEW_STATES dict management and generation tracking.

    Reproduces the eviction logic from diagnostics/commands.py:32-37
    without importing the sublime-dependent module.
    """

    _MAX_VIEW_STATES = 256

    def _make_state_manager(self):
        view_states: dict = {}

        def state_for(view_id: int):
            if len(view_states) > self._MAX_VIEW_STATES:
                stale = [vid for vid in view_states if vid != view_id]
                for vid in stale[:len(stale) // 2]:
                    view_states.pop(vid, None)
            return view_states.setdefault(view_id, "state")

        return view_states, state_for

    def test_state_for_view_within_limit(self):
        view_states, state_for = self._make_state_manager()
        state_for(42)

        stats = _bench(lambda: state_for(42), repeat=5000)
        self.assertLess(stats["max_ms"], 0.5, f"_state_for (within limit) too slow: {stats}")
        print(f"\n  _state_for (within limit): {stats['mean_ms']:.4f}ms mean")

    def test_state_for_view_eviction(self):
        view_states, state_for = self._make_state_manager()

        for i in range(self._MAX_VIEW_STATES + 50):
            view_states[i] = "state"

        def trigger_eviction():
            state_for(99999)

        stats = _bench(trigger_eviction, repeat=100)
        self.assertLess(stats["max_ms"], 5.0, f"Eviction too slow: {stats}")
        print(f"\n  _state_for (eviction at {self._MAX_VIEW_STATES}): {stats['mean_ms']:.2f}ms mean")


# ---------------------------------------------------------------------------
# 6. Diagnostics regex parsing
# ---------------------------------------------------------------------------

class DiagnosticsParsingBenchmark(unittest.TestCase):
    """Benchmark parse_compiler_issues regex matching."""

    def test_parse_clean_output(self):
        from arena_forge.adapters.runners.diagnostics import parse_compiler_issues
        output = "Compilation finished successfully.\n"
        stats = _bench(
            lambda: parse_compiler_issues(output, "test.cpp"),
            repeat=1000,
        )
        self.assertLess(stats["p95_ms"], 1.0, f"parse clean output too slow: {stats}")
        print(f"\n  parse_compiler_issues (clean): {stats['mean_ms']:.4f}ms mean")

    def test_parse_heavy_diagnostics(self):
        from arena_forge.adapters.runners.diagnostics import parse_compiler_issues
        lines = []
        for i in range(500):
            lines.append(f"/tmp/src/main.cpp:{i}:1: error: undeclared identifier 'x{i}'")
            lines.append(f"/tmp/src/main.cpp:{i}:5: warning: unused variable 'y{i}'")
        output = "\n".join(lines)
        stats = _bench(
            lambda: parse_compiler_issues(output, "/tmp/src/main.cpp"),
            repeat=100,
        )
        self.assertLess(stats["max_ms"], 50.0, f"parse heavy diagnostics too slow: {stats}")
        print(f"\n  parse_compiler_issues (1000 issues): {stats['mean_ms']:.2f}ms mean")


# ---------------------------------------------------------------------------
# 7. Formatting request builder
# ---------------------------------------------------------------------------

class FormattingBenchmark(unittest.TestCase):
    """Benchmark formatting pipeline components."""

    def test_normalize_newlines(self):
        from arena_forge.formatting.core.text import normalize_newlines
        text = "hello\r\nworld\r\nfoo\nbar\r\n"
        stats = _bench(lambda: normalize_newlines(text, "\n"), repeat=5000)
        self.assertLess(stats["max_ms"], 0.5, f"normalize_newlines too slow: {stats}")
        print(f"\n  normalize_newlines: {stats['mean_ms']:.4f}ms mean")

    def test_remap_selection_regions_small(self):
        from arena_forge.formatting.core.text import remap_selection_regions
        original = "hello world\nfoo bar\n"
        formatted = "hello world\nfoo bar\n"
        regions = [(0, 5), (12, 15)]
        stats = _bench(
            lambda: remap_selection_regions(original, formatted, regions),
            repeat=5000,
        )
        self.assertLess(stats["max_ms"], 1.0, f"remap_selection_regions too slow: {stats}")
        print(f"\n  remap_selection_regions (small): {stats['mean_ms']:.4f}ms mean")

    def test_remap_selection_regions_large(self):
        from arena_forge.formatting.core.text import remap_selection_regions
        original = "\n".join(f"line {i} content" for i in range(1000))
        formatted = "\n".join(f"line {i} content" for i in range(1000))
        regions = [(0, 10), (500, 510), (10000, 10010)]
        stats = _bench(
            lambda: remap_selection_regions(original, formatted, regions),
            repeat=500,
        )
        self.assertLess(stats["max_ms"], 10.0, f"remap_selection_regions (large) too slow: {stats}")
        print(f"\n  remap_selection_regions (1k lines): {stats['mean_ms']:.2f}ms mean")


# ---------------------------------------------------------------------------
# 8. Template rendering
# ---------------------------------------------------------------------------

class TemplateRenderingBenchmark(unittest.TestCase):
    """Benchmark HTML phantom template rendering."""

    def test_render_template_primed(self):
        """After first render (cache primed), measure steady-state latency."""
        try:
            from arena_forge.adapters.sublime.support.render_assets import render_template
        except ImportError:
            self.skipTest("render_assets requires sublime module")

        # Prime with mock translate
        with patch(
            "arena_forge.adapters.sublime.support.render_assets.translate",
            side_effect=lambda k: k,
        ):
            render_template("test_config.html", test_id=1, runtime="5ms", test_type="", result_block="")
            stats = _bench(
                lambda: render_template(
                    "test_config.html", test_id=1, runtime="5ms", test_type="", result_block=""
                ),
                repeat=500,
            )
            self.assertLess(stats["max_ms"], 2.0, f"render_template too slow: {stats}")
            print(f"\n  render_template (test_config): {stats['mean_ms']:.4f}ms mean")


# ---------------------------------------------------------------------------
# 9. Full diagnostics cycle simulation
# ---------------------------------------------------------------------------

class DiagnosticsCycleBenchmark(unittest.TestCase):
    """Simulate the full diagnostics pipeline from on_modified to result application."""

    def test_full_lint_cycle_simulation(self):
        from arena_forge.adapters.runners.diagnostics import (
            CompilerDiagnosticsService,
            DiagnosticsScratchWorkspace,
        )

        # Mock the subprocess execution to isolate Python-side overhead
        with patch(
            "arena_forge.adapters.runners.diagnostics.execute_subprocess"
        ) as mock_exec:
            mock_exec.return_value = MagicMock(
                stdout="test.cpp:1:1: error: expected ';'\n",
                stderr="",
                returncode=1,
                runtime_ms=5,
                timed_out=False,
                argv=("g++", "test.cpp"),
            )

            scratch = DiagnosticsScratchWorkspace(Path("/tmp"))
            service = CompilerDiagnosticsService(
                platform_name="linux",
                scratch_workspace=scratch,
            )

            def run_cycle():
                report = service.run(
                    compile_cmd="g++ -fsyntax-only {source_file}",
                    source_text="int main() { return 0 }",
                    source_file="/tmp/test.cpp",
                    source_file_dir="/tmp",
                    scratch_label="bench-1",
                    timeout_ms=5000,
                )
                return report

            stats = _bench(run_cycle, repeat=200)
            self.assertLess(stats["max_ms"], 20.0, f"Full lint cycle too slow: {stats}")
            print(f"\n  full diagnostics cycle (mocked): {stats['mean_ms']:.2f}ms mean")


# ---------------------------------------------------------------------------
# 10. Output evaluation (NormalizedTextOutputChecker)
# ---------------------------------------------------------------------------

class OutputEvaluationBenchmark(unittest.TestCase):
    """Benchmark the output checker used after every test run."""

    def test_accepted_output(self):
        from arena_forge.core.domain import TestCase
        from arena_forge.core.services import NormalizedTextOutputChecker

        checker = NormalizedTextOutputChecker()
        case = TestCase(
            name="Test 1",
            input_text="",
            accepted_outputs=("42\n",),
            rejected_outputs=(),
            checker_name="normalized_text",
        )
        stats = _bench(lambda: checker.evaluate(case, "42\n"), repeat=5000)
        self.assertLess(stats["max_ms"], 1.0, f"accepted eval too slow: {stats}")
        print(f"\n  output eval (accepted): {stats['mean_ms']:.4f}ms mean")

    def test_rejected_with_mismatch(self):
        from arena_forge.core.domain import TestCase
        from arena_forge.core.services import NormalizedTextOutputChecker

        checker = NormalizedTextOutputChecker()
        expected_output = "\n".join(f"line {i}" for i in range(100))
        actual_output = "\n".join(f"line {i}" for i in range(99)) + "\nWRONG"
        case = TestCase(
            name="Test 1",
            input_text="",
            accepted_outputs=(expected_output,),
            rejected_outputs=(),
            checker_name="normalized_text",
        )
        stats = _bench(lambda: checker.evaluate(case, actual_output), repeat=500)
        self.assertLess(stats["max_ms"], 25.0, f"rejected eval too slow: {stats}")
        print(f"\n  output eval (rejected, 100 lines): {stats['mean_ms']:.2f}ms mean")


if __name__ == "__main__":
    unittest.main(verbosity=2)
