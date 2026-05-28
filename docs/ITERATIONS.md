# ArenaForge Iterations

## Iteration 1

- Renamed the package and product to `ArenaForge`
- Standardized the product surface around the new name

## Iteration 2

- Added `JsonSessionRepository`
- Introduced durable session snapshots under `.arena-forge/sessions/`

## Iteration 3

- Added `SettingsBackedRunner`
- Added `RunSessionService` and `SessionRunReport`

## Iteration 4

- Added `ProviderRegistry`
- Added provider URL resolution and contest-id extraction

## Iteration 5

- Added `ContestWorkspaceScaffolder`
- Contest bootstrap now has a reusable scaffolding layer for metadata, source files, and samples

## Iteration 6

- Moved the active Codeforces submission path into
  `arena_forge/adapters/providers/codeforces_submit.py`
- Removed the runtime dependency on root-level `ContestHandlers/` from the
  main contest command flow
- Replaced `bs4`-based CSRF parsing with a standard-library HTML parser

## Iteration 7

- Added secure credential storage through `keyring`
- Added provider capabilities and submission service contracts
- Added `Luogu` and `AcWing` provider integrations
- Added render-asset caching and localized template labels

## Iteration 8

- Split run-panel flow into dispatch, display, session, edit, debug, and
  test-action helper modules
- Added explicit command/action surface tests for `test_manager` and `test_edit`
- Added `Run History` panel plus source-file reopen entry points

## Iteration 9

- Moved manual run-panel reruns off the synchronous compile path
- Hardened snapshot and tests-file recovery against invalid JSON payloads
- Added timeout-aware submission transport and normalized submission error
  wrapping
- Switched diagnostics scratch files from a single shared path to per-view
  labeled files
- Added regression coverage for run-panel async compile, submission transport,
  diagnostics scratch paths, credential rotation, and contest submission entry
  points

## Iteration 10

- Made repo-root Sublime registration shims export imported commands/listeners
  explicitly via `__all__`
- Cleared repo-wide `ruff` debt across wrappers and low-risk legacy modules in
  `Highlight/`, `Modules/`, and `debuggers/`
- Switched debugger module registration to runtime loading so subclass
  discovery stays intact without import-order lint violations
- Normalized legacy `debuggers/debugod.py` enough for Python 3 tooling so
  `uv run ruff check .` now passes

## Iteration 11

- Narrowed broad exception handling across the targeted Sublime adapter files
  to explicit recovery paths
- Removed the remaining blanket `except` usage from
  `run_panel_action_handlers.py`, `test_editor_dispatch.py`,
  `messages.py`, `diagnostics_commands.py`, `debug_overlay_commands.py`,
  `run_panel_tester.py`, and `run_panel_commands.py`
- Added regression coverage for diagnostics/logging fallbacks, translation
  fallback, sidebar capability probing, and process-termination recovery
- Expanded the baseline suite to `196 passed` while keeping `ruff`, `mypy`,
  and `compileall` green

## Iteration 12

- Added `run_panel_process_actions.py` to centralize run-panel tester
  termination and deferred `test_manager` command scheduling
- Rewired run-panel close / kill / stop / clear-all / rerun / edit-mode retry
  flows through the shared lifecycle helper
- Narrowed the remaining broad exception boundaries in
  `submission_service.py`, `keyring_store.py`, and `atcoder.py`
- Added regression coverage for the shared run-panel lifecycle helper and the
  narrowed provider/security recovery paths
- Expanded the baseline suite to `204 passed` while keeping `ruff`, `mypy`,
  and `compileall` green
