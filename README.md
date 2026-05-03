ArenaForge for Sublime Text
===============================

ArenaForge is a competitive-programming workbench with a typed core, portable storage,
safer process execution, and a path toward multi-editor reuse.

## What changed

- New editor-agnostic core under `arena_forge/`
- Portable test-session storage under `.arena-forge/tests/`
- Rich session snapshots under `.arena-forge/sessions/`
- Structured Codeforces sample parsing
- Provider-owned contest submission entry points
- Locale catalog foundation for future full i18n
- Safer subprocess command tokenization instead of broad shell execution
- Provider registry and workspace scaffolding for contest bootstrap

## Current feature set

- Compile and run inside a dedicated test panel
- Persist interactive tests per source file
- Stress testing with `__Good` and `__Generator`
- Snippet-style template expansion for contest code
- Realtime C++ diagnostics
- OSX LLDB debugger support
- Contest bootstrap and submission hooks

## Key bindings

- `ctrl+alt+b` on Windows/Linux: compile and run
- `ctrl+enter`: append a new test
- `ctrl+c`: terminate the active process in the run panel
- `ctrl+l`: clear all tests in the run panel
- `ctrl+u`: clear the current unsent input in the run panel
- `ctrl+w`: delete the previous word in the run panel input
- `ctrl+a`: move to the start of the current run panel input
- `ctrl+e`: move to the end of the current run panel input
- `alt+b`: move backward by one word in the current run panel input
- `alt+f`: move forward by one word in the current run panel input
- `ctrl+up`: recall the previous input from panel history
- `ctrl+down`: move forward in panel input history or restore the current draft
- `ctrl+x`: kill the active process
- `ctrl+d`: delete selected tests
- `ctrl+shift+up` / `ctrl+shift+down`: reorder tests
- `ctrl+k`, `ctrl+p`: toggle the right-side run panel

## Usage guide

### 1. Install and open

- Install the package into Sublime Text as a normal package folder.
- Open any supported source file such as `*.cpp`, `*.py`, or `*.java`.
- Run `ArenaForge: Open Settings` from the command palette if you want to customize paths, locale, UI density, or run profiles.

### 2. First-time setup

- Check `contests_root` if you want contest workspaces to be created outside the default `~/Contests/ArenaForge`.
- Check `run_settings` if your compiler or runtime command differs from the defaults.
- `credential_backend` defaults to `keyring`. Submission credentials are no longer stored in `ArenaForge.sublime-settings`.

### 3. Daily run workflow

- Press `ctrl+alt+b` in a source file to open the run panel and compile/run the current file.
- Use `ctrl+enter` to append a new test in the run panel.
- Use `enter` to send input to an active interactive process.
- Use `ctrl+c` to stop the current process with terminal-style behavior.
- Use `ctrl+l` to clear all tests and reset the panel to a fresh input slot.
- Use `ctrl+u` to clear the current unsent input line.
- Use `ctrl+w` to delete the previous word in the current input line.
- Use `ctrl+a` / `ctrl+e` to move to the start or end of the current input line.
- Use `alt+b` / `alt+f` to move backward or forward by one word.
- Use `ctrl+up` / `ctrl+down` to navigate previously submitted inputs, similar to shell history recall.
- Use `ctrl+x` to terminate the current process.
- Use `ctrl+d` to delete selected tests.
- Use `ctrl+shift+up` / `ctrl+shift+down` to reorder selected tests.
- Use `ctrl+k`, `ctrl+p` to collapse or restore the right-side run panel.

The default UI profile now uses a more terminal-like look:

- `ui_variant: "terminal"`
- `ui_density: "compact"`

### 4. Test editing and history

- Click `edit` in a test row to open the dedicated test editor view.
- Run `ArenaForge: Run History` to inspect recent runs for the current source file.
- Run `ArenaForge: Open History Source` from a history view to jump back to its source file.
- Run `ArenaForge: Clear All Tests` from the command palette if you want the same reset action without using the key binding.

### 5. Contest workflow

- Run `ArenaForge: Setup Contest`.
- Paste a supported contest or problem URL. Current built-in providers include Codeforces, AtCoder, Luogu, and AcWing.
- ArenaForge creates a workspace, source files, contest metadata, and sample tests under the configured contests root.

### 6. Submission and credentials

- Run `ArenaForge: Configure Credentials` inside a contest workspace before your first submission.
- Credentials are stored through the system keyring backend when available.
- Run `ArenaForge: Submit` from the current source file to submit it through the active provider.
- At the moment, full submission support is implemented for Codeforces. Other providers are scaffolded and capability-checked explicitly.

### 7. Stress testing and diagnostics

- Use `ArenaForge: Make Stress` to start stress testing with `<task>__Good` and `<task>__Generator`.
- Use `ArenaForge: Stop Stress` to stop an active stress session.
- C++ diagnostics run through the configured `lint_compile_cmd` and annotate the current buffer with warning/error regions.

## Architecture

- Core design: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- Migration notes: [docs/MIGRATION.md](docs/MIGRATION.md)
- Internationalization: [docs/I18N.md](docs/I18N.md)

## Development

- Python runtime: `3.8+`
- Project tooling: `uv`, `pytest`, `ruff`
- Bootstrap locally: `uv sync --group dev`
- Run tests: `uv run pytest`
- Run lint: `uv run ruff check arena_forge tests`

## Product stance

ArenaForge is treated as a clean-slate product. Storage, settings, and package naming are
all ArenaForge-native.
