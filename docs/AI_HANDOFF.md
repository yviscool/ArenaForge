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
- `arena_forge/adapters/sublime/run_panel_commands.py` is still the main
  remaining architectural hotspot

## Validation Baseline

Run from repo root:

- `uv run pytest -q`
  - expected result during this handoff: `91 passed`
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

- `cmp_sense/amin.cpp` is a runtime scratch file
- it is intentionally git-ignored
- `diagnostics_commands.py` rewrites it on each lint pass

### 4. Sublime-dependent imports in tests

- `arena_forge/adapters/runners/__init__.py` intentionally uses optional import
  for `ProcessManager`
- this keeps plain Python tests from requiring `sublime`

### 5. Run panel controller size

- `arena_forge/adapters/sublime/run_panel_commands.py` is still too large
- do not move extracted logic back into it
- future cleanup should continue shifting state and controller behavior behind
  `RunPanelControllerState` and adjacent helper modules

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
   - `uv run pytest -q`
4. Only then start editing

## Suggested Next Mission

If continuing immediately, the best next mission is:

1. continue shrinking `arena_forge/adapters/sublime/run_panel_commands.py`
2. keep moving controller state behind `RunPanelControllerState`
3. formalize debugger and diagnostics interfaces once the controller cleanup is
   smaller
