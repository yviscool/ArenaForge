# ArenaForge Architecture

## Intent

ArenaForge is built as an editor-agnostic competitive-programming workbench.
The Sublime Text package is now a thin shell around a reusable Python core.

## Layers

1. `arena_forge/core`
   - Typed domain models
   - Pure services for normalization and verdict evaluation
   - Use cases that depend only on ports
2. `arena_forge/adapters`
   - Storage layout and settings normalization
   - Snapshot repository and workspace scaffolding
   - Safe subprocess command building
   - Contest-provider implementations and registry
   - Locale catalogs
3. Root package modules
   - Sublime command entry points
   - Thin shells over the ArenaForge core

## Hard rules

- No editor APIs inside the core.
- No alternate data streams for durable storage.
- No command execution through ad-hoc shell strings when argv is sufficient.
- No HTML scraping by string slicing when structured parsing is available.
- User-visible strings must be catalog-backed.

## Product Direction

ArenaForge prioritizes internal coherence over backward compatibility. The codebase is
organized so root command modules can shrink over time while the core keeps expanding.
