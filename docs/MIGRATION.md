# Migration Notes

## Product Reset

ArenaForge is now treated as a clean-slate product rather than a compatibility layer.

## Test Storage

ArenaForge writes portable JSON test files under:

`.arena-forge/tests/<source>.tests.json`

ArenaForge also writes richer session snapshots under:

`.arena-forge/sessions/<source>.session.json`

## Template Metadata

Template properties now prefer:

`<snippet>.cpp.properties.json`
