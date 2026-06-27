#!/usr/bin/env bash
set -euo pipefail

GXX_BIN="${GXX_BIN:-g++}"

if ! command -v "$GXX_BIN" >/dev/null 2>&1; then
  echo "g++ not found on PATH"
  exit 1
fi

if [ -n "${MINGW_DIR:-}" ]; then
  ROOT_DIR="$MINGW_DIR"
else
  GXX_PATH="$(command -v "$GXX_BIN")"
  ROOT_DIR="$(cd "$(dirname "$GXX_PATH")/.." && pwd)"
fi

HEADER_PATH="$(find "$ROOT_DIR/include/c++" -path '*/bits/stdc++.h' | head -n 1)"
if [ -z "$HEADER_PATH" ]; then
  echo "bits/stdc++.h not found under $ROOT_DIR"
  exit 1
fi

echo "Detected header: $HEADER_PATH"
echo "Generating precompiled header..."
"$GXX_BIN" -std=c++14 -g -Wall -Winvalid-pch -finput-charset=UTF-8 -fexec-charset=UTF-8 \
  -x c++-header "$HEADER_PATH" -o "$HEADER_PATH.gch"
echo "Done: $HEADER_PATH.gch"
