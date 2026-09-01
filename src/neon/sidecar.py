"""Sidecar I/O: load, validate, and deterministically save contract files.

The sidecar is the single source of truth for everything human- or
LLM-authored (SPEC: Storage). Two hard rules this module enforces:

  * Determinism: saving the same data twice produces byte-identical
    output. Entries sorted by qualname, clauses kept in stable order,
    no timestamps or environment leakage. Regeneration must never
    produce a spurious git diff.
  * Validation on load: sidecars are hand-editable YAML, so a human
    typo (bad status value, missing field) must fail loudly with the
    file and key named — not deserialize into garbage.

Implementation hints:
  - PyYAML: `yaml.safe_load` / `yaml.safe_dump(..., sort_keys=False)`.
    You control key order yourself by building dicts in schema order.
  - Round-tripping enums: store `.value`, parse back through the enum
    constructor (which raises ValueError on bad input — catch and
    re-raise as SidecarError with context).
  - Omit None fields on save (a drafted clause has no `by`/`at`; writing
    `by: null` everywhere is noise).
"""

from __future__ import annotations

from pathlib import Path

from .schema import Sidecar


class SidecarError(Exception):
    """A sidecar failed validation. Message must name the file, the
    entry, and what was wrong — the user hand-edits these files."""


def load(source_path: Path) -> Sidecar:
    """Load the sidecar adjacent to `source_path`.

    A missing sidecar file is NOT an error — it means the source file is
    uncovered; return an empty Sidecar for it.

    TODO(you): read YAML, validate every field, build schema objects.
    """
    raise NotImplementedError


def save(sidecar: Sidecar) -> None:
    """Write the sidecar next to its source file, deterministically.

    TODO(you): convert schema objects to plain dicts (entries sorted by
    qualname, None fields omitted), dump YAML, write. Consider writing
    to a temp file + rename so a crash never leaves a half-written
    sidecar (`os.replace` is atomic on the same filesystem).
    """
    raise NotImplementedError
