[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Русский](README.ru.md)

# ArenaForge

[![CI](https://github.com/yviscool/ArenaForge/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/yviscool/ArenaForge/actions/workflows/ci.yml)

ArenaForge is an all-in-one Sublime Text workbench for competitive programming.
It combines fast local runs, sample management, contest workspace generation, formatter integration, C++ diagnostics, stress testing, and Codeforces submission inside one package.

## Quick Links

- [Quickstart](docs/QUICKSTART.md)
- [Configuration](docs/CONFIGURATION.md)
- [PCH workflow](docs/PCH.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Sublime shell migration notes](docs/SUBLIME_SHELL_MIGRATION.md)

## What It Does

- Run the current file in a dedicated test panel.
- Store tests and session snapshots as JSON files near your source tree.
- Compare output against expected answers and show the first mismatch.
- Keep input history and terminal-style editing inside the run panel.
- Bootstrap contest or problem workspaces from supported OJ URLs.
- Ask for the target language before creating contest source files.
- Format supported languages from inside ArenaForge.
- Show C++ diagnostic markers from `lint_compile_cmd`.
- Run stress tests with `<task>__Good` and `<task>__Generator`.
- Submit Codeforces solutions with credentials stored through `keyring`.
- Generate formatter config files for the current file or whole workspace.

## Language Support

### Run / Contest Templates

| Language | Run | Contest template | Formatter |
| --- | --- | --- | --- |
| C | Yes | Yes | `clang-format` |
| C++ | Yes | Yes | `clang-format` |
| Python | Yes | Yes | `ruff format` |
| Java | Yes | Yes | `google-java-format` |
| Kotlin | Yes | Yes | `ktfmt` |
| Go | Yes | Yes | `gofmt` |
| Rust | Yes | Yes | `rustfmt` |
| JavaScript | Yes | Yes | `oxfmt` |

### Format-Only Through `oxfmt`

ArenaForge also routes formatting for common web and text formats through `oxfmt`, including:

- TypeScript / TSX
- JSON / YAML / TOML
- HTML / Vue / Svelte
- CSS / SCSS / Less
- Markdown / MDX
- GraphQL

## Provider Support

| Provider | Workspace bootstrap | Submission |
| --- | --- | --- |
| Codeforces | Contest workspace with parsed samples | Yes |
| AtCoder | Contest workspace with parsed samples | No |
| Luogu | Single problem workspace | No |
| AcWing | Single problem workspace | No |

Codeforces submission needs `requests` and a working `keyring` backend.
The repository declares `requests` in `dependencies.json`.

## Installation

### Normal Install

1. Put this folder under Sublime Text `Packages/`.
2. Keep the outer package directory name as `ArenaForge`.
3. Restart Sublime Text, or run `Tools -> Developer -> Reload Plugins`.
4. Open the command palette and run `ArenaForge: Open Settings`.

You still need the local toolchains and formatter binaries you want to use, such as `g++`, `python`, `javac`, `ruff`, or `rustfmt`.

### Development Link on Windows

For local development, prefer a junction over manual copies into `Packages/`.
That keeps Sublime pointed at your working tree and avoids stale package copies.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\link_sublime_package.ps1
```

With your current layout, that creates:

```text
C:\software\Sublime Text 4\Data\Packages\ArenaForge
-> C:\Users\Administrator\Desktop\manage_svn\sub\arena_forge
```

## Commands

### Run / Contest

- `ArenaForge: Run`
- `ArenaForge: Setup Contest`
- `ArenaForge: Submit`
- `ArenaForge: Configure Credentials`
- `ArenaForge: Doctor`
- `ArenaForge: Run History`

The default Windows keymap binds `Ctrl+Alt+B` to `ArenaForge: Run`.

### Formatting

- `ArenaForge: Format`
- `ArenaForge: Format Document`
- `ArenaForge: Format Selection`
- `ArenaForge: Diagnose Formatter`
- `ArenaForge: Formatter Install Guide`
- `ArenaForge: Create Format Config For Current File`
- `ArenaForge: Create Workspace Format Configs`

## Recommended Workflow

1. Link the package into Sublime with the junction script if you are developing locally.
2. Put personal overrides in `Packages/User/ArenaForge.sublime-settings`.
3. Open a source file such as `A.cpp`, `main.py`, or `Main.java`.
4. Run `ArenaForge: Run` and edit tests in the run panel.
5. Run `ArenaForge: Format` when needed, or enable `format_on_save`.
6. Run `ArenaForge: Setup Contest` when you want a clean workspace from a URL.
7. Pick the target language in the contest setup prompt.
8. Run `ArenaForge: Doctor` after changing compiler or formatter paths.

See [Quickstart](docs/QUICKSTART.md) for concrete C++ / Python / Java examples.

## User Settings

The main shipped settings file is `ArenaForge.sublime-settings`.
Your personal overrides should live in:

```text
Packages/User/ArenaForge.sublime-settings
```

Best practice:

- Keep user settings focused on personal paths and workflow switches.
- Keep formatting style policy in project-native config files such as `.clang-format`, `pyproject.toml`, and `rustfmt.toml`.
- Keep ArenaForge formatter runtime settings in the `formatting` block of `ArenaForge.sublime-settings`.
- Use `formatting.commands` for machine-local executable paths or command prefixes.
- Avoid embedding long formatter style blobs in editor settings.

Example user settings:

```json
{
  "preferred_locale": "zh-Hans",
  "default_contest_language": "cpp",
  "close_sidebar": false,
  "language_profiles": {
    "profiles": {
      "cpp": {
        "compile_cmd": "g++ \"{source_file}\" -std=c++14 -g -Wall -Winvalid-pch -finput-charset=UTF-8 -fexec-charset=UTF-8 -o \"{source_file_dir}\\\\{file_name}.exe\"",
        "lint_compile_cmd": "g++ -std=c++14 -g -Wall -fsyntax-only -fdiagnostics-color=never -Winvalid-pch -finput-charset=UTF-8 -fexec-charset=UTF-8 \"{source_file}\" -I \"{source_file_dir}\""
      }
    },
    "order": ["c", "cpp", "python", "java", "kotlin", "go", "rust", "javascript"]
  }
}
```

### Formatter Notes

- Java and Kotlin formatters also auto-detect `tools/google-java-format.jar` and `tools/ktfmt.jar` inside the project.
- If a JAR lives elsewhere, use `formatting.commands` with an explicit `["java", "-jar", "..."]` prefix.

## Key Settings

- `default_contest_language`: default language highlighted in `Setup Contest`
- `language_profiles`: ordered language profile map for run / compile / template behavior
- `formatting.format_on_save`: synchronous format before save
- `formatting.commands`: machine-local formatter command prefixes
- `formatting.extra_args`: extra runtime flags for formatters
- `submission_language_ids`: provider-specific submission language mapping
- `stress_time_limit_seconds`: timeout used by stress testing
- `tests_relative_dir`, `session_relative_dir`, `tests_file_suffix`: test and snapshot storage layout

## Troubleshooting

### No C++ diagnostic boxes or error markers

ArenaForge currently shows inline diagnostic marks only for C++.

Check:

- `lint_enabled` is `true`
- your active file is a supported C++ extension such as `.cpp`
- the `language_profiles.profiles.cpp.lint_compile_cmd` setting is still valid
- `g++` is callable in the same environment Sublime uses
- the generated `bits/stdc++.h.gch` matches the active compiler and flags
- you reloaded plugins after changing settings

If needed, run:

- `ArenaForge: Doctor`
- `bash scripts/pch.sh`
- `Tools -> Developer -> Reload Plugins`

### Format command does nothing

Check:

- the current syntax is supported by one of the formatter adapters
- the formatter binary exists on `PATH`, is configured in `formatting.commands`, or for Java/Kotlin is available as `tools/google-java-format.jar` or `tools/ktfmt.jar`
- the file is not in an unsupported selection-format mode

Use `ArenaForge: Diagnose Formatter` to inspect the matched adapter, command, and config file lookup.

### Contest workspace uses the wrong language

Check:

- the language you selected in `ArenaForge: Setup Contest`
- `default_contest_language` in your user settings

## Project Layout

- `arena_forge/core`: typed domain models, output checking, and session use cases
- `arena_forge/adapters`: Sublime integration, providers, storage, runners, i18n, workspace scaffolding, and credential storage
- `arena_forge/adapters/sublime/run_panel`: run-panel command orchestration, state, rendering, and session flow
- `arena_forge/adapters/sublime/test_editor`: dedicated test-editor commands and dispatch
- `arena_forge/adapters/sublime/formatting`: formatting request building, command execution, panel output, and config generation
- `arena_forge/adapters/sublime/contest`, `diagnostics`, `stress`: domain-specific Sublime command packages
- `arena_forge/formatting`: formatter adapters, discovery, config generation, and formatting runtime
- `arena_forge/templates`: built-in contest templates
- `tests`: pytest coverage for providers, storage, settings, run-panel behavior, and formatting
- `docs`: architecture, migration notes, and quickstart docs

## Development

- Python: `3.8+`
- Dependency manager: `uv`
- Runtime dependency: `keyring`

Local checks:

```bash
uv sync --group dev
uv run ruff check arena_forge tests
uv run pytest -q
uv run mypy
```

## Thanks

This project builds on ideas and workflow from [FastOlympicCoding](https://github.com/Jatana/FastOlympicCoding) by Jatana.

The current codebase keeps the competitive-programming focus, but reorganizes the implementation around a typed core, portable JSON storage, integrated formatting, and cleaner Sublime adapters.
