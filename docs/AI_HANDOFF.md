# ArenaForge AI Handoff

## Purpose

This document is the authoritative local handoff for the next AI agent.
Read it before making structural changes.

## Product Identity

- Product name: `ArenaForge`
- Product stance: clean-slate product, no backward-compatibility goal
- Repository root: git root and Sublime package shell
- Primary Python package: `arena_forge/`
- Current host shell: Sublime Text package

## Repository Layout

```text
repo_root/
  arena_forge/              # core + adapters + product defaults + locales
  docs/                     # architecture and migration notes
  tests/                    # pytest suite
  settings.py               # thin Sublime wrapper
  ContestHandler.py         # thin Sublime wrapper
  stress_manager.py         # thin Sublime wrapper
  Cpp_Intellij_Sense.py     # thin Sublime wrapper
  olympic_funcs.py          # thin Sublime wrapper
  test_edit.py              # thin Sublime wrapper
  test_manager.py           # thin Sublime wrapper
  arenaforge_window_commands.py
  NumberSpliter.py
  Highlight/                # HTML/CSS render assets
  icons/                    # run-panel and debug icons
  debuggers/                # debugger bridge modules
  Modules/                  # template generator bridge
  cmp_sense/                # runtime diagnostics scratch dir
  *.sublime-settings
  *.sublime-keymap
  *.sublime-syntax
  Default.sublime-commands
  Main.sublime-menu
```

## Architecture

### Core layer

Located in:

- `arena_forge/core/domain.py`
- `arena_forge/core/ports.py`
- `arena_forge/core/services.py`
- `arena_forge/core/usecases.py`

Responsibilities:

- domain models
- ports and protocols
- normalization and verdict evaluation
- session and run use cases

Important use cases:

- `SessionService`
- `RunSessionService`

### Adapter layer

Located in `arena_forge/adapters/`.

Subareas:

- `i18n/`
- `providers/`
- `runners/`
- `security/`
- `storage/`
- `sublime/`
- `workspace/`

### Sublime adapter layer

Located in `arena_forge/adapters/sublime/`.

This is the real shell implementation. Root-level Python files are registration
wrappers only. New behavior should go under `arena_forge/adapters/sublime/`,
not back into the repo root.

Important files:

- `bootstrap.py`
- `settings_bridge.py`
- `contest_commands.py`
- `stress_commands.py`
- `diagnostics_commands.py`
- `template_commands.py`
- `test_editor_commands.py`
- `run_panel_commands.py`
- `run_panel_controller_state.py`
- `run_panel_state.py`
- `run_panel_tester.py`
- `run_panel_rendering.py`
- `run_panel_session_service.py`
- `run_panel_regions.py`
- `debug_overlay_commands.py`
- `root_bridge.py`

## Root Wrappers And Resource Bridges

Thin wrappers at repo root:

- `settings.py`
- `ContestHandler.py`
- `stress_manager.py`
- `Cpp_Intellij_Sense.py`
- `olympic_funcs.py`
- `Modules/ProcessManager.py`
- `test_edit.py`
- `test_manager.py`
- `arenaforge_window_commands.py`

Important bridge behavior:

- `arena_forge/adapters/sublime/root_bridge.py` is the approved way for Sublime
  adapters to reach root resources such as `Highlight.*`, `debuggers.*`, and
  `Modules.ClassPregen.*`
- non-Sublime modules should not import `root_bridge.py`

## Active Resources That Must Stay At Repo Root

These are still part of the active runtime path:

- `Highlight/`
- `icons/`
- `debuggers/`
- `Modules/ClassPregen/`
- `cmp_sense/`
- `StressSyntax.sublime-syntax`
- `TestSyntax.sublime-syntax`
- `TestSyntax.sublime-settings`
- `*.sublime-settings`
- `*.sublime-keymap`
- `Default.sublime-commands`
- `Main.sublime-menu`
- `dependencies.json`

## Migration Status

Completed:

- repository root was normalized so the git root is now the single project root
- product code now lives under the inner package `arena_forge/`
- tests, docs, Sublime shell files, and runtime resources were moved into the
  git root
- legacy `ContestHandlers/`, `contest_foundry/`, screenshots, and generated
  HTML docs were removed from the active tree

Still true:

- root wrappers are intentionally thin
- the broader run-panel controller flow is still the main remaining
  architectural hotspot, but `run_panel_commands.py` itself is now a thin
  registration shell

## Current Working Set

Most recent pass completed:

- added `run_panel_process_actions.py` to centralize run-panel tester
  termination and deferred `test_manager` command scheduling
- rewired run-panel close / kill / stop / clear-all / rerun / edit-mode retry
  flows through the shared process-action helper instead of duplicating
  per-module process control
- continued shrinking `run_panel_session_actions.py` by extracting rerun and
  compile-launch helpers around backend preparation and async start
- removed the remaining broad exception boundaries in:
  - `arena_forge/adapters/providers/submission_service.py`
  - `arena_forge/adapters/security/keyring_store.py`
  - `arena_forge/adapters/providers/atcoder.py`
- added regression coverage for the new run-panel lifecycle helper and the
  narrowed provider/security recovery paths
- full validation now passes with the expanded test suite

Primary files touched in the latest pass:

- `arena_forge/adapters/sublime/run_panel_process_actions.py`
- `arena_forge/adapters/sublime/run_panel_action_handlers.py`
- `arena_forge/adapters/sublime/test_editor_dispatch.py`
- `arena_forge/adapters/sublime/run_panel_edit_actions.py`
- `arena_forge/adapters/sublime/run_panel_test_actions.py`
- `arena_forge/adapters/sublime/run_panel_session_actions.py`
- `arena_forge/adapters/providers/submission_service.py`
- `arena_forge/adapters/security/keyring_store.py`
- `arena_forge/adapters/providers/atcoder.py`

Latest regression tests added or expanded:

- added:
  - `tests/test_run_panel_process_actions.py`
- expanded:
  - `tests/test_run_panel_session_actions.py`
  - `tests/test_submission_service.py`
  - `tests/test_keyring_store.py`
  - `tests/test_atcoder_provider.py`

## Validation Baseline

Run from repo root:

- `uv run python -m pytest`
  - expected result during this handoff: `204 passed`
- `uv run python -m mypy`
  - expected result: `Success: no issues found in 10 source files`
- `uv run ruff check .`
  - expected result: passing
- `python -m compileall arena_forge tests test_manager.py test_edit.py settings.py ContestHandler.py stress_manager.py Cpp_Intellij_Sense.py olympic_funcs.py Modules/ProcessManager.py`
  - expected result: passing

## Known Technical Quirks

### 1. Sublime package import naming

- package resource paths are derived from the actual outer package folder name
- `arena_forge/adapters/sublime/root_bridge.py` supports both:
  - direct Python imports from the repo root
  - Sublime package installs where the outer package may or may not match the
    inner `arena_forge/` package name
- keep the inner Python package named `arena_forge/`; the outer Sublime package
  folder can now be either `ArenaForge` or `arena_forge`

### 2. Sublime host Python version

- this package must keep `.python-version` at `3.8` for Sublime Text package
  loading
- changing `.python-version` to a project runtime such as `3.14` breaks command
  registration in Sublime because the package will no longer load under the
  expected plugin host
- project tooling may use newer interpreters externally, but the package host
  target is `3.8`

### 3. Diagnostics scratch file

- `cmp_sense/` is a runtime scratch directory
- it is intentionally git-ignored
- `diagnostics_commands.py` now writes per-view labeled scratch files such as
  `amin-<view>-<generation>.cpp`

### 3.5. `uv` trampoline quirk on Windows

- in this environment, `uv run pytest` and `uv run mypy` may fail with:
  `uv trampoline failed to canonicalize script path`
- use `uv run python -m pytest` and `uv run python -m mypy` instead
- keep this in mind before diagnosing false build failures

### 4. Sublime-dependent imports in tests

- `arena_forge/adapters/runners/__init__.py` intentionally uses optional import
  for `ProcessManager`
- this keeps plain Python tests from requiring `sublime`

### 5. Run panel controller surface

- `arena_forge/adapters/sublime/run_panel_commands.py` is now a thin
  registration shell
- do not move extracted logic back into it
- future cleanup should continue targeting adjacent helper modules such as
  `run_panel_command_mixin.py`, `run_panel_action_handlers.py`, and
  `run_panel_session_actions.py`

## Recommended Do / Do Not

### Do

- keep new logic under `arena_forge/`
- keep repo-root Python wrappers thin
- use `root_bridge.py` for repo-root resource access from Sublime adapters
- run tests after structural changes
- add tests when changing storage, parsing, providers, or runner behavior

### Do Not

- do not reintroduce compatibility logic for old product names
- do not move business logic back into root wrappers
- do not create another nested git repository inside `arena_forge/`
- do not reintroduce broad `shell=True` execution patterns
- do not delete active root resources until the adapter layer fully replaces
  their runtime usage

## Suggested Session Start Checklist

1. Read:
   - `docs/ARCHITECTURE.md`
   - `docs/SUBLIME_SHELL_MIGRATION.md`
   - this file
2. Inspect:
   - `arena_forge/adapters/sublime/run_panel_commands.py`
   - `arena_forge/adapters/sublime/run_panel_tester.py`
   - `arena_forge/adapters/sublime/run_panel_state.py`
3. Run:
   - `uv run python -m pytest`
4. Only then start editing

## Suggested Next Mission

If continuing immediately, the best next mission is:

1. continue run-panel helper extraction in the still stateful modules:
   - `arena_forge/adapters/sublime/run_panel_command_mixin.py`
   - `arena_forge/adapters/sublime/run_panel_edit_actions.py`
   - `arena_forge/adapters/sublime/run_panel_test_actions.py`
2. add direct unit coverage for run-panel edit/test action modules, which still
   contain user-visible control flow but have thinner dedicated tests than the
   surrounding helper modules
3. keep the now-expanded regression and lint baseline green while touching
   legacy or adapter recovery paths

## Proposed Next Round Plan

### Mission 1: continue run-panel helper extraction

Target files:

- `arena_forge/adapters/sublime/run_panel_command_mixin.py`
- `arena_forge/adapters/sublime/run_panel_action_handlers.py`
- `arena_forge/adapters/sublime/run_panel_edit_actions.py`
- `arena_forge/adapters/sublime/run_panel_test_actions.py`
- `arena_forge/adapters/sublime/run_panel_session_actions.py`
- `arena_forge/adapters/sublime/run_panel_commands.py`

Goal:

- keep `run_panel_commands.py` as a thin registration surface
- keep process lifecycle and deferred command scheduling behind dedicated helper
  modules
- move any remaining event plumbing or small UI helpers into focused helpers
  without regressing the current action surface

Validation:

- `uv run python -m pytest tests/test_run_panel_*`

### Mission 2: expand run-panel action coverage

Target files:

- `tests/test_run_panel_edit_actions.py`
- `tests/test_run_panel_test_actions.py`
- `tests/test_run_panel_command_mixin.py`

Goal:

- cover edit-mode retry, stop/clear behavior, and any remaining lifecycle
  transitions that currently rely on indirect coverage
- keep tests lightweight by stubbing Sublime APIs the same way the current
  run-panel helper tests do

Validation:

- `uv run python -m pytest tests/test_run_panel_*`

### Mission 3: keep the lint baseline green

Target files:

- repo root wrappers
- `Highlight/`
- `Modules/`
- `debuggers/`

Goal:

- keep `uv run ruff check .` passing while touching legacy support code
- prefer small, behavior-preserving cleanup over larger rewrites

Validation:

- `uv run ruff check .`
- `uv run python -m pytest`
