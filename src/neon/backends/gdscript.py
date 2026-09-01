"""GDScript backend — v2, deliberately empty for now.

Kept as a file so the shape of the port stays visible while you build
v1. Do not implement until v1 works end-to-end on the toy repo.

The plan (SPEC: Godot backend notes):
  - Parsing: `gdtoolkit` (Python package) parses .gd files; map its tree
    to FunctionInfo, same as the ast walk in python.py.
  - Hashing: gdtoolkit's parse tree replaces `ast` in the normalizer —
    this is why hashing.py takes FunctionInfo, not an ast node.
  - Enforcement: source-transform injection of GDScript `assert()` at
    function entry/exit (Godot strips asserts from release exports, so
    dev-only enforcement is free). No wrapping/monkey-patching exists
    in GDScript.
  - Property tests: emit gdUnit4 fuzzer tests; run via `godot --headless`.
  - Vocabulary is load-bearing here: scene-tree/signal/lifecycle
    predicates (is_inside_tree, "emits X at most once") must resolve
    through vocabulary.py, not be restated per function.
"""
