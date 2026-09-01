"""Normalized AST hashing — powers drift detection and rename relinking.

The goal: two versions of a function that differ only in whitespace,
comments, or (your call) docstrings must hash the SAME; any semantic
change must hash DIFFERENTLY.

Why AST and not the source text: hashing raw text would flag a re-indent
or a comment edit as "code changed", spamming stale warnings and eroding
trust in the tool. Parsing to an AST throws away formatting for free.

Suggested approach (stdlib only):
  1. `ast.parse()` the function source (you may need `textwrap.dedent`
     first — a method extracted from a class body has leading indentation
     that ast.parse rejects).
  2. Normalize: `ast.dump()` the tree WITHOUT location info
     (annotate_fields/include_attributes flags are your friends).
     Decide whether the docstring counts as semantic; document the choice.
  3. Hash the dump with `hashlib.sha256`, return a short hex prefix
     (12-16 chars is plenty; collisions across one repo are negligible).

Note for v2: GDScript won't go through `ast`. Keep this module's public
signature language-neutral (take FunctionInfo, not an ast node) so the
Godot backend can plug in its own normalizer behind the same call.
"""

from __future__ import annotations

from .schema import FunctionInfo


def code_hash(fn: FunctionInfo) -> str:
    """Return the normalized hash of a function's implementation.

    TODO(you): implement per the module docstring. Start by writing the
    tests in tests/test_hashing.py — they define "same" and "different"
    precisely, and this function just has to satisfy them.
    """
    raise NotImplementedError
