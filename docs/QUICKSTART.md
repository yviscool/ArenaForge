# ArenaForge Quickstart

This guide is the fastest way to get ArenaForge working for daily problem solving.

## 1. Link the Package

On Windows development machines, prefer the repo junction:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\link_sublime_package.ps1
```

Then run `Tools -> Developer -> Reload Plugins` in Sublime Text.

## 2. Create User Settings

Edit:

```text
Packages/User/ArenaForge.sublime-settings
```

Minimal example:

```json
{
  "preferred_locale": "zh-Hans",
  "default_contest_language": "cpp",
  "language_profiles": {
    "profiles": {
      "cpp": {
        "compile_cmd": "g++ \"{source_file}\" -std=c++14 -g -Wall -Winvalid-pch -finput-charset=UTF-8 -fexec-charset=UTF-8 -o \"{source_file_dir}\\\\{file_name}.exe\"",
        "lint_compile_cmd": "g++ -std=c++14 -g -Wall -fsyntax-only -fdiagnostics-color=never -Winvalid-pch -finput-charset=UTF-8 -fexec-charset=UTF-8 \"{source_file}\" -I \"{source_file_dir}\""
      }
    }
  }
}
```

Best practice:

- keep personal paths here
- keep style rules in `.clang-format`, `pyproject.toml`, `rustfmt.toml`, and similar project files

## 3. Verify Toolchains

Make sure the languages you use are available locally.

Common examples:

- C++: `g++`
- Python: `python`
- Java: `javac` and `java`
- Kotlin: `kotlinc`
- Go: `go`
- Rust: `rustc` and `rustfmt`
- Python formatter: `ruff`

If anything looks wrong, run `ArenaForge: Doctor`.

## 4. First C++ Run

1. Open `A.cpp`.
2. Run `ArenaForge: Run`.
3. Add tests in the run panel.
4. Save the file and confirm diagnostics appear if you introduce a C++ error.
5. Run `ArenaForge: Format` or save with `format_on_save`.

Notes:

- C++ inline diagnostics depend on `lint_enabled` and the C++ profile's `lint_compile_cmd`.
- If you use `bits/stdc++.h`, generate the matching `.gch` once with `bash scripts/pch.sh`.
- If diagnostic markers do not appear, reload plugins and run `ArenaForge: Doctor`.

### Run Panel Shortcuts

The Windows keymap binds `Ctrl+Alt+B` to `ArenaForge: Run`.

Inside the run panel, the most useful shortcuts are:

- `Enter`: add a new test line
- `Ctrl+Enter`: create or toggle a test
- `Ctrl+C` / `Ctrl+X`: stop the current process
- `Ctrl+L`: clear all tests
- `Ctrl+U`: clear the current input
- `Ctrl+W`: delete the previous word
- `Alt+B` / `Alt+F`: move by word
- `Ctrl+Up` / `Ctrl+Down`: browse input history
- `Ctrl+Shift+Up` / `Ctrl+Shift+Down`: swap tests

These bindings only apply while the run panel is active.

## 5. First Python Run

1. Open `main.py`.
2. Run `ArenaForge: Run`.
3. Add sample input in the run panel.
4. Save or run `ArenaForge: Format`.

Python formatting uses `ruff format`.

## 6. First Java Run

1. Open `Main.java`.
2. Run `ArenaForge: Run`.
3. Use `ArenaForge: Format` after configuring `google-java-format` if needed.

ArenaForge also auto-detects `tools/google-java-format.jar` and `tools/ktfmt.jar` inside the project when `java` is available.

If you prefer an explicit override, or the JAR lives elsewhere, configure:

```json
{
  "formatting": {
    "commands": {
      "google-java-format": ["java", "-jar", "tools/google-java-format.jar"]
    }
  }
}
```

The same pattern works for `ktfmt` with `tools/ktfmt.jar`.

## 7. Create a Contest Workspace

1. Run `ArenaForge: Setup Contest`.
2. Paste a supported contest or problem URL.
3. Pick the target language in the language prompt.
4. ArenaForge creates the workspace, source files, tests, and metadata.

The selected language controls:

- source file extension
- built-in contest template
- later run behavior
- matched formatter

## 8. Formatters

Useful commands:

- `ArenaForge: Format`
- `ArenaForge: Diagnose Formatter`
- `ArenaForge: Formatter Install Guide`
- `ArenaForge: Create Workspace Format Configs`

Use `Diagnose Formatter` when a file is not being formatted as expected.

## 9. Daily Loop

Recommended daily pattern:

1. open file
2. run tests
3. format
4. fix diagnostics
5. stress test if needed
6. submit from contest workspace when ready
