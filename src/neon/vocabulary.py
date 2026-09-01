"""Shared vocabulary: domain predicates defined once, referenced by name.

A clause like `valid_account_id(account_id)` shouldn't restate what
"valid" means in every contract — it binds to ONE definition here, so
tightening the definition tightens every contract that uses it.

v1 shape: a single `contracts.vocab.yaml` at repo root:

    valid_account_id:
      doc: "Non-empty string of 8 hex digits."
      expr: "isinstance(x, str) and len(x) == 8"   # x = the argument

Enforcement folds vocabulary terms into the eval namespace as callables,
so check_exprs can use them like functions. Drafting includes the
vocabulary in its prompt so the LLM reuses terms instead of inventing
synonyms.

This module is deliberately thin in v1 — it earns its keep in v2, where
Godot contracts lean on engine-state predicates (is_inside_tree,
signal-emission claims) that MUST live in one place. Keep the interface
boring so that upgrade is additive.
"""

from __future__ import annotations

from pathlib import Path


def load(root: Path) -> dict[str, "VocabTerm"]:
    """Load contracts.vocab.yaml if present; empty dict if not.
    TODO(you): parse + validate, same discipline as sidecar.load."""
    raise NotImplementedError


def as_namespace(vocab: dict) -> dict:
    """Turn vocab terms into callables for the check_expr eval namespace.
    TODO(you): compile each expr into a one-arg lambda equivalent."""
    raise NotImplementedError


class VocabTerm:
    """TODO(you): dataclass — name, doc, expr. (Defined here rather than
    schema.py since it's vocab-file-shaped, not sidecar-shaped.)"""
