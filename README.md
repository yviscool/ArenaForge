[中文说明](README.zh-CN.md)

# ArenaForge

ArenaForge is a competitive-programming toolkit for Sublime Text.
It is built for the day-to-day loop of solving problems: open a file, run it quickly, keep sample tests in order, and create a clean workspace from a problem or contest URL.

The package keeps that workflow inside the editor.
Run history, stress testing, diagnostics, template insertion, contest setup, and Codeforces submission are all part of the same working surface.

## What It Does

- Run the current file in a dedicated test panel.
- Store sample tests and richer session snapshots as JSON files near your source tree.
- Compare output with expected answers and show the first mismatch position.
- Keep interactive input history and basic terminal-style editing inside the run panel.
- Open a dedicated test editor and a separate run-history view for the current source file.
- Bootstrap contest or problem workspaces from Codeforces, AtCoder, Luogu, and AcWing URLs.
- Submit Codeforces solutions from inside Sublime Text, with credentials stored through `keyring`.
- Run stress tests with `<task>__Good` and `<task>__Generator`.
- Insert local algorithm templates and provide lightweight C++ completion helpers.
- Run C++ diagnostics from `lint_compile_cmd`.
- Show a simple `Doctor` report for package files, resources, run profiles, and credential backend availability.

## Current Provider Support

| Provider | Workspace bootstrap | Submission |
| --- | --- | --- |
| Codeforces | Contest workspace with parsed samples | Yes |
| AtCoder | Contest workspace with parsed samples | No |
| Luogu | Single problem workspace | No |
| AcWing | Single problem workspace | No |

Codeforces submission needs `requests` and a working `keyring` backend.
The repository declares `requests` in `dependencies.json`.

## Project Layout

- `arena_forge/core`: typed domain models, output checking, and session use cases
- `arena_forge/adapters`: Sublime integration, providers, storage, runners, i18n, workspace scaffolding, and credential storage
- `tests`: pytest coverage for providers, storage, settings, run-panel behavior, and command surfaces
- `docs`: architecture, migration, and i18n notes
- repo root: Sublime package resources such as keymaps, syntax files, HTML render assets, icons, debuggers, and thin wrapper commands

## Installation

1. Put this folder under your Sublime Text `Packages/` directory.
2. If you install it manually, rename the outer package folder to `ArenaForge`.
3. Restart Sublime Text.
4. Open the command palette and run `ArenaForge: Open Settings`.

You still need local toolchains for the languages you want to run, such as `g++`, `python`, or `javac`.

## Basic Workflow

1. Open a source file such as `A.cpp` or `main.py`.
2. Run `ArenaForge: Run`.
3. Add or edit tests in the run panel.
4. Use `ArenaForge: Setup Contest` when you want to create a contest or problem workspace from a URL.
5. Use `ArenaForge: Configure Credentials` once before your first Codeforces submission.
6. Use `ArenaForge: Submit` from a file inside a contest workspace.

Common shortcuts:

- Run current file: `Ctrl+Alt+B` on Windows/Linux, `Ctrl+B` on macOS
- Add a new test: `Ctrl+Enter`
- Stop the current process: `Ctrl+C` on all platforms, `Ctrl+X` on Windows/Linux

For the full list, see:

- `Default (Windows).sublime-keymap`
- `Default (Linux).sublime-keymap`
- `Default (OSX).sublime-keymap`

## Configuration

The main settings file is `ArenaForge.sublime-settings`.
The repository also includes recommended per-platform defaults in:

- `ArenaForge (Windows).sublime-settings`
- `ArenaForge (Linux).sublime-settings`
- `ArenaForge (OSX).sublime-settings`

The settings you will most likely touch are:

- `run_settings`: language profiles, file extensions, compile commands, run commands, and optional `lint_compile_cmd`
- `contests_root`: where generated contest or problem workspaces are created
- `tests_relative_dir`, `session_relative_dir`, `tests_file_suffix`: where test indexes and session snapshots are stored
- `preferred_locale`: `en` or `zh-Hans`
- `credential_backend`: currently `keyring`
- `stress_time_limit_seconds`: timeout used by stress tests
- `algorithms_base`: base directory for local C++ templates or snippets
- `cpp_complete_enabled` and `cpp_complete_settings`: lightweight C++ completion behavior
- `submission_language_ids`: per-provider language id mapping for submission
- `ui_variant` and `ui_density`: basic run-panel presentation

Example:

```json
{
  "preferred_locale": "en",
  "contests_root": "~/Contests/ArenaForge",
  "tests_relative_dir": ".arena-forge/tests",
  "session_relative_dir": ".arena-forge/sessions",
  "stress_time_limit_seconds": 2,
  "credential_backend": "keyring",
  "algorithms_base": "Algorithms",
  "run_settings": [
    {
      "name": "C++",
      "extensions": ["cpp", "cc", "cxx"],
      "compile_cmd": "g++ \"{source_file}\" -std=gnu++17 -O2 -pipe -o \"{file_name}\"",
      "run_cmd": "./{file_name} {args}",
      "lint_compile_cmd": "g++ -std=gnu++17 \"{source_file}\" -I \"{source_file_dir}\""
    },
    {
      "name": "Python",
      "extensions": ["py"],
      "compile_cmd": null,
      "run_cmd": "python \"{source_file}\"",
      "lint_compile_cmd": null
    }
  ]
}
```

Tests and session data are stored as normal JSON files next to your working source tree.
The exact locations depend on your `tests_relative_dir` and `session_relative_dir` settings.
The shipped settings files use slightly different layouts by platform, so treat the example above as a template, not a required literal copy.

## Development

- Python: `3.8+`
- Dependency manager: `uv`
- Runtime dependency: `keyring`
- Test command: `uv run pytest`
- Lint command: `uv run ruff check arena_forge tests`

## Thanks

This project builds on ideas and workflow from [FastOlympicCoding](https://github.com/Jatana/FastOlympicCoding) by Jatana.

The current codebase keeps the same competitive-programming focus, but reorganizes the implementation around a typed core, portable JSON storage, and cleaner Sublime adapters.
