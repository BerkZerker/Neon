"""Drift detection: contracts never silently rot (SPEC: Behaviors).

Run on code change (CI, file watch, or just `neon drift` manually):
compare each sidecar entry's stored code_hash against the hash of the
function as it exists NOW, and classify:

  CURRENT   hashes match — triage state still describes this code.
  STALE     qualname exists, hash differs — code changed since a human
            last vouched. Confirmed contracts here must fail loudly:
            the fix is either a code fix or an explicit contract
            amendment, never silence.
  RENAMED   qualname gone, but some new function has an IDENTICAL hash
            and no entry of its own — relink the entry to the new name
            instead of orphaning the triage work. (Identical hash =
            identical normalized body; a same-body-different-name
            coincidence is possible but rare enough to accept in v1.)
  DELETED   qualname gone, no hash match anywhere — function removed;
            report so the human can delete the entry deliberately.

Ordering matters: detect renames BEFORE declaring deletions, or every
rename reports as a delete + an uncovered new function.

Exit-code contract for CI: any STALE entry with confirmed clauses =
nonzero exit. That single rule is the whole "fail loudly" mechanism.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .schema import ContractEntry, FunctionInfo


@dataclass
class DriftReport:
    current: list[str] = field(default_factory=list)    # qualnames
    stale: list[str] = field(default_factory=list)
    renamed: list[tuple[str, str]] = field(default_factory=list)  # (old, new)
    deleted: list[str] = field(default_factory=list)

    @property
    def fails_ci(self) -> bool:
        """TODO(you): True iff any stale entry has a confirmed clause.
        (You'll need more than qualnames stored above to answer this —
        adjust the fields when you get here.)"""
        raise NotImplementedError


def check(entries: dict[str, ContractEntry],
          functions: dict[str, FunctionInfo]) -> DriftReport:
    """Classify every entry against the currently-extracted functions.

    TODO(you): hash the current functions (hashing.code_hash), then a
    few dict passes: match -> current/stale; leftover entries vs
    leftover hashes -> renamed; remainder -> deleted.
    """
    raise NotImplementedError


def relink(entries: dict[str, ContractEntry], old: str, new: str) -> None:
    """Apply one detected rename to the sidecar data. TODO(you)."""
    raise NotImplementedError
