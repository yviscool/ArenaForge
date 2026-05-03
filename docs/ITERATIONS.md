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
