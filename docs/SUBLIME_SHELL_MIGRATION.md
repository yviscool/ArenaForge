# Sublime Shell Migration

Status note:
- The root Sublime bridge files referenced below were later renamed to a
  consistent `*_plugin.py` scheme.
- Historical mentions of names like `ContestHandler.py` and `test_manager.py`
  are archival context unless explicitly updated.
- The debugger support directory was later renamed from `debuggers/` to
  `debug_backends/`.

## Short Answer

Yes, the ArenaForge kernel is formed enough to begin a large shell migration.

It already owns:

- product defaults and naming
- settings normalization
- storage layout
- session repository
- runners
- provider registry
- contest workspace scaffolding
- core session and run use cases

What is still root-heavy is the Sublime presentation and event shell.

## Current Split

### Kernel-owned today

- `arena_forge/product.py`
- `arena_forge/core/*`
- `arena_forge/adapters/storage/*`
- `arena_forge/adapters/runners/*`
- `arena_forge/adapters/providers/*`
- `arena_forge/adapters/workspace/*`
- `arena_forge/adapters/sublime/bootstrap.py`

### Root-shell-heavy today

- `settings.py` -> thin re-export wrapper
- `ContestHandler.py` -> thin re-export wrapper
- `test_manager.py` -> thin re-export wrapper
- `test_edit.py` -> thin re-export wrapper
- `stress_manager.py` -> thin re-export wrapper
- `olympic_funcs.py` -> thin re-export wrapper
- `Cpp_Intellij_Sense.py` -> thin re-export wrapper
- `Modules/ProcessManager.py` -> thin re-export wrapper

## Migration Principle

Move behavior inward, leave resources outward.

Resources that may stay at repo root for a long time:

- `*.sublime-keymap`
- `*.sublime-settings`
- `*.sublime-syntax`
- `Main.sublime-menu`
- `Default.sublime-commands`
- `icons/`
- `Highlight/`

Python code should continue moving into `arena_forge/adapters/sublime/`.

## Target Ownership

### Phase 1

- `settings.py`
  target: `arena_forge/adapters/sublime/settings_bridge.py`
  goal: centralize `SublimeApplication` construction
  status: done

- `ContestHandler.py`
  target: `arena_forge/adapters/sublime/contest_commands.py`
  goal: shell only gathers user input and delegates to application services
  status: done

### Phase 2

- `stress_manager.py`
  target: `arena_forge/adapters/sublime/stress_commands.py`
  goal: move stress orchestration behind a reusable service
  status: done

- `Cpp_Intellij_Sense.py`
  target: `arena_forge/adapters/sublime/diagnostics_commands.py`
  goal: isolate Sublime diagnostics rendering from compile probing
  status: done

### Phase 3

- `olympic_funcs.py`
  target: `arena_forge/adapters/sublime/template_commands.py`
  goal: rename away historical language and isolate template browsing
  status: done

- `Modules/ProcessManager.py`
  target: delete or fold into `arena_forge/adapters/runners/`
  goal: stop owning execution logic outside the runner layer
  status: done

### Phase 4

- `test_edit.py`
  target: `arena_forge/adapters/sublime/test_editor_commands.py`
  status: done as file move, further cleanup pending

- `test_manager.py`
  target: split into:
  - `run_panel_commands.py`
  - `run_panel_state.py`
  - `run_panel_rendering.py`
  - `debug_overlay_commands.py`
  status: main split completed, cleanup still in progress

This is the largest move and should happen last.

## Kernel Maturity Verdict

### Strong enough now

- storage model
- contest workspace scaffolding
- runner abstraction
- session and run use cases
- bootstrap container

### Not fully formed yet

- diagnostics model
- test panel state model
- debugger state abstraction
- application-level error and reporting envelope

So the answer is:

The kernel is formed enough to start migrating most shell code now, but not yet
complete enough to absorb the whole `test_manager.py` blob without one more round
of state-model extraction.

## Recent Progress Beyond The Original Plan

- `ViewTesterCommand` was extracted into `debug_overlay_commands.py`
- `RunPanelTester` was extracted into `run_panel_tester.py`
- panel test persistence was extracted into `run_panel_state.py`
- tie-position, clear, and read-only helpers were extracted into `run_panel_regions.py`
- a basic debugger contract was introduced in `arena_forge/core/ports.py`
- thin root wrappers now exist for:
  - `test_manager.py`
  - `test_edit.py`
