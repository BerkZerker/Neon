"""The contract schema: the one module that is fully defined for you.

Everything else in the codebase speaks in these types. They mirror the
sidecar YAML from SPEC.md exactly — if you change a field here, the
sidecar format changes, so treat this file as the design's anchor.

Deliberately plain: dataclasses + enums, no behavior. Logic that
*operates* on these types lives in sidecar.py, triage.py, drift.py, etc.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class ClauseKind(str, Enum):
    """What a clause claims about the function."""

    PRE = "pre"          # must be true of inputs on entry
    POST = "post"        # guaranteed of return value / side effects on exit
    RAISES = "raises"    # what it raises, and when


class ClauseStatus(str, Enum):
    """Triage state of a single clause (per-line, per SPEC)."""

    DRAFTED = "drafted"        # LLM-generated, untriaged; still enforced (pins behavior)
    CONFIRMED = "confirmed"    # human promoted to a real promise; LLM may never edit
    RELEASED = "released"      # human marked as incidental behavior, not a promise


@dataclass
class Clause:
    """One contract line. The unit of triage.

    `text` is the human-readable claim. For v1, enforcement translates it
    into an executable check via `check_expr` — a Python expression over
    the function's parameters (and `result` for POST clauses). `check_expr`
    may be None when no executable form exists yet (the clause is then
    display-only and the dashboard should show it as unenforced... except
    SPEC says no contract exists without enforcement, so drafting should
    always try to produce one).
    """

    kind: ClauseKind
    text: str
    status: ClauseStatus = ClauseStatus.DRAFTED
    check_expr: str | None = None
    confidence: float | None = None   # LLM's own confidence, only while DRAFTED
    by: str | None = None             # who triaged (None until a human touches it)
    at: str | None = None             # ISO date of triage decision


@dataclass
class ContractEntry:
    """The contract for one function, keyed by qualified name in the sidecar.

    `code_hash` is the normalized-AST hash of the function body at the time
    the entry was last drafted or triaged. drift.py compares it against the
    current source to detect staleness and renames.
    """

    qualname: str                     # e.g. "Inventory.add_item"
    code_hash: str
    clauses: list[Clause] = field(default_factory=list)


@dataclass
class Sidecar:
    """One sidecar file: all contract entries for one source file.

    `source_path` is the code file it describes; `path` is where the
    sidecar itself lives (adjacent: foo.py -> foo.py.contracts.yaml).
    Entries stay sorted by qualname so serialization is deterministic.
    """

    source_path: Path
    entries: dict[str, ContractEntry] = field(default_factory=dict)

    @property
    def path(self) -> Path:
        return self.source_path.with_name(self.source_path.name + ".contracts.yaml")


@dataclass
class FunctionInfo:
    """What a language backend extracts per function — the input to
    hashing, drafting, and enforcement. Language-neutral on purpose.
    """

    qualname: str
    source_path: Path
    lineno: int                       # 1-indexed start line in source
    params: list[str]                 # parameter names, in order
    source: str                       # the function's own source text
    docstring: str | None = None


class FunctionState(str, Enum):
    """Dashboard state per function (SPEC: Views). Coverage is measured
    against functions, not lines."""

    PASSING = "passing"
    FAILING = "failing"
    UNTRIAGED = "untriaged"    # has drafted clauses awaiting a human
    STALE = "stale"            # code changed since triage (drift.py sets this)
    UNCOVERED = "uncovered"    # no contract entry at all
