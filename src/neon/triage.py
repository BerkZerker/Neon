"""Triage: the human decision loop over drafted clauses.

The state machine per clause is small and one-directional:

    DRAFTED --confirm--> CONFIRMED
    DRAFTED --edit-----> CONFIRMED   (human rewrote text/check_expr first)
    DRAFTED --release--> RELEASED    (real behavior, but not a promise)

Rules (SPEC: Invariants):
  * Only a human moves a clause out of DRAFTED. These functions are
    called by the review UI, never by drafting.
  * On any transition: set by/at, drop confidence (it described the
    draft, which no longer exists as a draft).
  * Confirming a clause also refreshes the entry's code_hash — the
    human just vouched for the contract against the CURRENT code, so
    "current" is what staleness is measured from.

Queue ordering: lowest LLM confidence first (SPEC: Triage flow) —
the model's least-sure guesses are where human attention pays most.

The UI itself: start with the dumbest thing that works — a terminal
loop that prints one clause + the function source and reads
[c]onfirm / [e]dit / [r]elease / [s]kip. Fancy comes later.
"""

from __future__ import annotations

from .schema import Clause, ContractEntry, Sidecar


def triage_queue(sidecars: list[Sidecar]) -> list[tuple[ContractEntry, Clause]]:
    """All DRAFTED clauses across the repo, lowest confidence first
    (None confidence sorts first — the model wouldn't even guess).

    TODO(you): flatten + sort. A list comprehension and one sort key.
    """
    raise NotImplementedError


def confirm(entry: ContractEntry, clause: Clause, by: str, new_hash: str) -> None:
    """Promote a drafted clause to CONFIRMED. `new_hash` is the current
    code_hash of the function (see module docstring for why).

    TODO(you): mutate clause + entry per the rules above. Reject (raise)
    if the clause isn't DRAFTED — re-confirming or resurrecting a
    RELEASED clause should be an explicit, separate act.
    """
    raise NotImplementedError


def release(entry: ContractEntry, clause: Clause, by: str) -> None:
    """Mark a drafted clause RELEASED: observed behavior, not a promise.
    Released clauses stay in the sidecar (they document reality and stop
    the LLM re-proposing the same line) but are never enforced.

    TODO(you).
    """
    raise NotImplementedError


def edit(entry: ContractEntry, clause: Clause, by: str, new_hash: str,
         text: str, check_expr: str | None) -> None:
    """Human rewrites a drafted clause, which confirms their version.

    TODO(you): update text/check_expr, then confirm.
    """
    raise NotImplementedError
