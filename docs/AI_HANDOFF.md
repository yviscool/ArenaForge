# ArenaForge AI Handoff

## Purpose

This document is the authoritative local handoff for the next AI agent.
Read it before making structural changes.

Migration note:
- The old flat Sublime adapter files named `run_panel_*.py` and `test_editor_*.py` were removed.
- Their code now lives under `arena_forge/adapters/sublime/run_panel/` and
  `arena_forge/adapters/sublime/test_editor/`.
- Formatting commands were moved from `format_commands.py` to
  `arena_forge/adapters/sublime/formatting/`.
- Contest, diagnostics, and stress commands now live under
  `arena_forge/adapters/sublime/contest/`, `diagnostics/`, and `stress/`.
- Template and debug-overlay commands now live under
  `arena_forge/adapters/sublime/template_bridge/` and `debug_overlay/`.
- Historical references to the old flat paths below are archival context unless explicitly updated.

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
  settings_plugin.py        # thin Sublime wrapper
  contest_plugin.py         # thin Sublime wrapper
  stress_plugin.py          # thin Sublime wrapper
  diagnostics_plugin.py     # thin Sublime wrapper
  template_plugin.py        # thin Sublime wrapper
  test_editor_plugin.py     # thin Sublime wrapper
  run_panel_plugin.py       # thin Sublime wrapper
  window_commands_plugin.py
  formatting_plugin.py
  history_plugin.py
  number_splitter.py
  highlight_assets/         # HTML/CSS render assets
  icons/                    # run-panel and debug icons
  debug_backends/           # debugger bridge modules
  plugin_support/           # root-level support bridges
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
- `shared/settings_bridge.py`
- `contest/commands.py`
- `stress/commands.py`
- `diagnostics/commands.py`
- `template_bridge/commands.py`
- `test_editor/commands.py`
- `run_panel/commands.py`
- `run_panel/state.py`
- `run_panel/tester.py`
- `run_panel/rendering.py`
- `debug_overlay/commands.py`
- `ui/window_commands.py`
- `ui/history_commands.py`
- `support/render_assets.py`
- `support/result_display.py`
- `root_bridge.py`

## Root Wrappers And Resource Bridges

Thin wrappers at repo root:

- `settings_plugin.py`
- `contest_plugin.py`
- `stress_plugin.py`
- `diagnostics_plugin.py`
- `template_plugin.py`
- `test_editor_plugin.py`
- `run_panel_plugin.py`
- `history_plugin.py`
- `window_commands_plugin.py`
- `formatting_plugin.py`
- `number_splitter.py`

Important bridge behavior:

- `arena_forge/adapters/sublime/root_bridge.py` is the approved way for Sublime
  adapters to reach root resources such as
  `highlight_assets.cpp_var_highlight`, `debug_backends.registry`, and
  `plugin_support.template_generation.*`
- non-Sublime modules should not import `root_bridge.py`

## Active Resources That Must Stay At Repo Root

These are still part of the active runtime path:

- `highlight_assets/`
- `icons/`
- `debug_backends/`
- `plugin_support/template_generation/`
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
  architectural hotspot, but `run_panel/commands.py` itself is now a thin
  registration shell

## Current Working Set

Most recent pass completed:

- extracted shared run-panel tester termination logging into
  `arena_forge/adapters/sublime/run_panel/process_actions.py`
- rewired `action_handlers.py`, `edit_actions.py`, `session_actions.py`, and
  `test_actions.py` to use the shared termination helpers instead of repeating
  inline failure callbacks
- added direct regression coverage for:
  - `tests/test_run_panel_edit_actions.py`
  - `tests/test_run_panel_command_mixin.py`
  - `tests/test_run_panel_test_actions.py`
- updated existing run-panel helper tests to match the shared termination flow
- full validation now passes with the expanded test suite

Primary files touched in the latest pass:

- `arena_forge/adapters/sublime/run_panel/process_actions.py`
- `arena_forge/adapters/sublime/run_panel/action_handlers.py`
- `arena_forge/adapters/sublime/run_panel/edit_actions.py`
- `arena_forge/adapters/sublime/run_panel/session_actions.py`
- `arena_forge/adapters/sublime/run_panel/test_actions.py`
- `tests/test_run_panel_process_actions.py`
- `tests/test_run_panel_action_handlers.py`
- `tests/test_run_panel_session_actions.py`
- `tests/test_run_panel_edit_actions.py`
- `tests/test_run_panel_command_mixin.py`
- `tests/test_run_panel_test_actions.py`

Latest regression tests added or expanded:

- expanded:
  - `tests/test_run_panel_process_actions.py`
  - `tests/test_run_panel_action_handlers.py`
  - `tests/test_run_panel_session_actions.py`
- added:
  - `tests/test_run_panel_edit_actions.py`
  - `tests/test_run_panel_command_mixin.py`
  - `tests/test_run_panel_test_actions.py`

## Validation Baseline

Run from repo root:

- `uv run python -m pytest`
  - expected result during this handoff: `220 passed`
- `uv run python -m mypy`
  - expected result: passing
- `uv run ruff check .`
  - expected result: passing
- `python -m compileall arena_forge tests run_panel_plugin.py test_editor_plugin.py settings_plugin.py contest_plugin.py stress_plugin.py diagnostics_plugin.py template_plugin.py formatting_plugin.py history_plugin.py window_commands_plugin.py number_splitter.py`
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
- `diagnostics/commands.py` now writes per-view labeled scratch files such as
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

- `arena_forge/adapters/sublime/run_panel/commands.py` is now a thin
  registration shell
- do not move extracted logic back into it
- future cleanup should continue targeting adjacent helper modules such as
  `run_panel/command_mixin.py`, `run_panel/action_handlers.py`, and
  `run_panel/session_actions.py`

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
   - `arena_forge/adapters/sublime/run_panel/commands.py`
   - `arena_forge/adapters/sublime/run_panel/tester.py`
   - `arena_forge/adapters/sublime/run_panel/state.py`
3. Run:
   - `uv run python -m pytest`
4. Only then start editing

## Suggested Next Mission

If continuing immediately, the best next mission is:

1. continue run-panel helper extraction around launch and stop orchestration:
   - `arena_forge/adapters/sublime/run_panel/session_actions.py`
   - `arena_forge/adapters/sublime/run_panel/action_handlers.py`
   - `arena_forge/adapters/sublime/run_panel/command_support.py`
2. expand direct unit coverage around the remaining higher-branching helpers:
   - `tests/test_run_panel_session_actions.py`
   - `tests/test_run_panel_display_actions.py`
   - `tests/test_run_panel_debug_actions.py` if new extraction lands there
3. keep the now-expanded regression and lint baseline green while touching
   legacy or adapter recovery paths

## Proposed Next Round Plan

### Mission 1: continue run-panel helper extraction

Target files:

- `arena_forge/adapters/sublime/run_panel/action_handlers.py`
- `arena_forge/adapters/sublime/run_panel/session_actions.py`
- `arena_forge/adapters/sublime/run_panel/command_support.py`
- `arena_forge/adapters/sublime/run_panel/display_actions.py`
- `arena_forge/adapters/sublime/run_panel/commands.py`

Goal:

- keep `run_panel/commands.py` as a thin registration surface
- keep process lifecycle and deferred command scheduling behind dedicated helper
  modules
- keep launch/stop/render orchestration moving toward smaller focused helpers
  without regressing the current action surface

Validation:

- `uv run python -m pytest tests/test_run_panel_*`

### Mission 2: expand run-panel helper coverage

Target files:

- `tests/test_run_panel_session_actions.py`
- `tests/test_run_panel_display_actions.py`
- `tests/test_run_panel_process_actions.py`

Goal:

- cover launch rerun/error branches, display update behavior, and any remaining
  lifecycle transitions that still rely on indirect coverage
- keep tests lightweight by stubbing Sublime APIs the same way the current
  run-panel helper tests do

Validation:

- `uv run python -m pytest tests/test_run_panel_*`

### Mission 3: keep the lint baseline green

Target files:

- repo root wrappers
- `highlight_assets/`
- `plugin_support/`
- `debug_backends/`

Goal:

- keep `uv run ruff check .` passing while touching legacy support code
- prefer small, behavior-preserving cleanup over larger rewrites

Validation:

- `uv run ruff check .`
- `uv run python -m pytest`
