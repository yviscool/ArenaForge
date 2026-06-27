# Configuration

ArenaForge now treats language profiles as the primary configuration surface.
The shape is explicit and ordered:

```json
{
  "language_profiles": {
    "order": ["c", "cpp", "python", "java", "kotlin", "go", "rust", "javascript"],
    "profiles": {
      "cpp": {
        "compile_cmd": "g++ \"{source_file}\" -std=c++14 -g -Wall -Winvalid-pch -finput-charset=UTF-8 -fexec-charset=UTF-8 -o \"{source_file_dir}\\\\{file_name}.exe\"",
        "lint_compile_cmd": "g++ -std=c++14 -g -Wall -fsyntax-only -fdiagnostics-color=never -Winvalid-pch -finput-charset=UTF-8 -fexec-charset=UTF-8 \"{source_file}\" -I \"{source_file_dir}\""
      }
    }
  }
}
```

## Design goals

- Profiles are keyed by `id`, so users can override one language without rewriting the rest.
- `order` controls display and selection priority.
- The `profiles` map stores the actual command templates, extensions, syntax selectors, and template paths.
- Partial overrides are merged into the built-in defaults by `id`.

## Common overrides

- Repoint a local compiler or formatter by editing one profile.
- Reorder languages in contest setup by changing `language_profiles.order`.
- Add a new language by adding a new profile entry and placing its `id` in `order`.

## Formatting

Formatting is configured in the same user settings file:

```text
Packages/User/ArenaForge.sublime-settings
```

Use the `formatting` object for machine-local behavior:

```json
{
  "formatting": {
    "format_on_save": true,
    "timeout_ms": 10000,
    "commands": {
      "clang-format": ["C:/Program Files/LLVM/bin/clang-format.exe"]
    },
    "extra_args": {
      "ruff": ["--line-length", "100"]
    },
    "selector_overrides": {}
  }
}
```

- `format_on_save` toggles synchronous save-time formatting.
- `commands` overrides formatter executables or command prefixes.
- `extra_args` adds formatter-specific flags.
- `selector_overrides` remaps formatter selection for specific scopes.
- `timeout_ms` controls how long formatting may run.

The command palette still exposes `ArenaForge: Format`, `ArenaForge: Format Document`, and `ArenaForge: Format Selection`.

## C++ PCH

The shipped C++ profile already includes `-Winvalid-pch` and matches the repo PCH workflow.
If you generate `bits/stdc++.h.gch`, ArenaForge will use it automatically during `ArenaForge: Run` and `Ctrl+Alt+B`.

See [PCH workflow](PCH.md) for the generator script and verification steps.
