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
from typing import Any

import yaml

from .schema import Clause, ClauseKind, ClauseStatus, ContractEntry, Sidecar

# The keys a sidecar may contain, in the order save() writes them. load()
# rejects anything else so a typo like "cheque_expr" fails instead of
# silently being ignored.
_ENTRY_KEYS = ("code_hash", "clauses")
_CLAUSE_KEYS = ("kind", "text", "status", "check_expr", "confidence", "by", "at")


class SidecarError(Exception):
    """A sidecar failed validation. Message must name the file, the
    entry, and what was wrong — the user hand-edits these files."""


def _fail(path: Path, entry: str | None, msg: str) -> SidecarError:
    """Build a SidecarError whose message always names the file (and the
    entry, when we're inside one). Returned, not raised, so call sites
    read `raise _fail(...)` and the traceback points at them."""
    where = f"{path}" if entry is None else f"{path} [{entry}]"
    return SidecarError(f"{where}: {msg}")


def _check_keys(
    data: dict[str, Any], allowed: tuple[str, ...], path: Path, entry: str, what: str
) -> None:
    """Reject unknown keys — the only defense against hand-edit typos in
    optional fields, which would otherwise just vanish on load."""
    unknown = sorted(set(data) - set(allowed))
    if unknown:
        raise _fail(
            path,
            entry,
            f"{what} has unknown key(s) {unknown}; allowed: {list(allowed)}",
        )


def _parse_clause(raw: Any, path: Path, entry: str, index: int) -> Clause:
    """Validate one item of an entry's `clauses:` list and build a Clause."""
    what = f"clause #{index}"
    if not isinstance(raw, dict):
        raise _fail(path, entry, f"{what} must be a mapping, got {type(raw).__name__}")
    _check_keys(raw, _CLAUSE_KEYS, path, entry, what)

    for required in ("kind", "text"):
        if required not in raw:
            raise _fail(path, entry, f"{what} is missing required field '{required}'")

    # Enums round-trip through their .value: the YAML holds "pre", and
    # calling ClauseKind("pre") gives back ClauseKind.PRE. A bad value
    # ("confrimed") makes the enum constructor raise ValueError, which we
    # turn into a SidecarError that says where and lists valid options.
    try:
        kind = ClauseKind(raw["kind"])
    except ValueError:
        raise _fail(
            path,
            entry,
            f"{what} has invalid kind {raw['kind']!r}; "
            f"expected one of {[k.value for k in ClauseKind]}",
        ) from None

    # `status` is optional in the file; a clause with no status is a
    # freshly drafted one (the schema's default).
    try:
        status = ClauseStatus(raw.get("status", ClauseStatus.DRAFTED.value))
    except ValueError:
        raise _fail(
            path,
            entry,
            f"{what} has invalid status {raw['status']!r}; "
            f"expected one of {[s.value for s in ClauseStatus]}",
        ) from None

    text = raw["text"]
    if not isinstance(text, str):
        raise _fail(path, entry, f"{what} 'text' must be a string")

    # Optional fields: absent (or explicitly null) means None. YAML is
    # loosely typed — `at: 2026-08-31` unquoted parses as a datetime.date,
    # not a string, so we str() the string-ish ones rather than reject
    # them; `confidence` must be a real number.
    confidence = raw.get("confidence")
    if confidence is not None and not isinstance(confidence, (int, float)):
        raise _fail(path, entry, f"{what} 'confidence' must be a number")

    def opt_str(key: str) -> str | None:
        value = raw.get(key)
        return None if value is None else str(value)

    return Clause(
        kind=kind,
        text=text,
        status=status,
        check_expr=opt_str("check_expr"),
        confidence=None if confidence is None else float(confidence),
        by=opt_str("by"),
        at=opt_str("at"),
    )


def _parse_entry(qualname: str, raw: Any, path: Path) -> ContractEntry:
    """Validate one top-level `qualname: {...}` block and build a ContractEntry."""
    if not isinstance(raw, dict):
        raise _fail(
            path, qualname, f"entry must be a mapping, got {type(raw).__name__}"
        )
    _check_keys(raw, _ENTRY_KEYS, path, qualname, "entry")

    code_hash = raw.get("code_hash")
    if not isinstance(code_hash, str) or not code_hash:
        raise _fail(path, qualname, "entry is missing required field 'code_hash'")

    # `clauses:` may be omitted or left empty (`clauses: []`) — both mean
    # "no clauses yet"; PyYAML gives None for an empty `clauses:` line.
    raw_clauses = raw.get("clauses") or []
    if not isinstance(raw_clauses, list):
        raise _fail(path, qualname, "'clauses' must be a list")

    clauses = [_parse_clause(c, path, qualname, i) for i, c in enumerate(raw_clauses)]
    return ContractEntry(qualname=qualname, code_hash=code_hash, clauses=clauses)


def load(source_path: Path) -> Sidecar:
    """Load the sidecar adjacent to `source_path`.

    A missing sidecar file is NOT an error — it means the source file is
    uncovered; return an empty Sidecar for it.

    File shape (top-level keys are qualnames, the `qualname` field of
    ContractEntry is implied by the key, not repeated inside):

        Inventory.add_item:
          code_hash: a3f91cdeadbe
          clauses:
            - kind: pre
              text: item.stack_size >= 1
              status: confirmed
              by: sam
              at: "2026-08-31"
    """
    sidecar = Sidecar(source_path=source_path)
    path = sidecar.path  # foo.py -> foo.py.contracts.yaml, next to the source
    if not path.exists():
        return sidecar

    # `yaml.safe_load` parses YAML into plain Python objects (dict / list /
    # str / int / ...). "safe" matters: full `yaml.load` can instantiate
    # arbitrary Python objects from tags in the file, which is a code
    # execution hole in a hand-editable file.
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise _fail(path, None, f"not valid YAML: {e}") from None

    # An empty file parses to None — treat it as "no entries".
    if raw is None:
        return sidecar
    if not isinstance(raw, dict):
        raise _fail(path, None, "top level must be a mapping of qualname -> entry")

    for qualname, raw_entry in raw.items():
        if not isinstance(qualname, str):
            raise _fail(path, None, f"entry key {qualname!r} must be a string qualname")
        sidecar.entries[qualname] = _parse_entry(qualname, raw_entry, path)

    # Keep entries sorted by qualname regardless of how the human ordered
    # them in the file — the schema promises this and save() relies on it.
    sidecar.entries = dict(sorted(sidecar.entries.items()))
    return sidecar


def save(sidecar: Sidecar) -> None:
    """Write the sidecar next to its source file, deterministically.

    TODO(you): convert schema objects to plain dicts (entries sorted by
    qualname, None fields omitted), dump YAML, write. Consider writing
    to a temp file + rename so a crash never leaves a half-written
    sidecar (`os.replace` is atomic on the same filesystem).
    """
    raise NotImplementedError
