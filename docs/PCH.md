# PCH Workflow

ArenaForge's C++ profile is tuned to use GCC precompiled headers when
`bits/stdc++.h.gch` exists next to the standard header.

## Generate

From Git Bash or another POSIX shell:

```bash
bash scripts/pch.sh
```

Environment overrides:

- `GXX_BIN` selects the compiler binary.
- `MINGW_DIR` forces the MinGW root if auto-detection is wrong.

The script generates:

```text
.../include/c++/<version>/<triplet>/bits/stdc++.h.gch
```

## Why it works

- The C++ compile command uses the same `-std=c++14`, `-g`, `-Wall`, and UTF-8
  flags as the generator.
- `-Winvalid-pch` makes GCC warn loudly when the header no longer matches.
- If the flags diverge, GCC falls back to the normal header and prints `x` in
  `-H` output.

## Verify

Quick check:

```bash
g++ -std=c++14 -g -Wall -Winvalid-pch -finput-charset=UTF-8 -fexec-charset=UTF-8 -H -c main.cpp
```

If PCH is active, GCC prints a `!` line for `stdc++.h.gch`.

## Maintenance

Regenerate the PCH when:

- you upgrade GCC or MinGW
- you change the compile flags
- you replace the C++ standard library headers
