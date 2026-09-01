"""Views: the abstraction layer reads contracts, not code (SPEC: Views).

Browsing a module shows each function's contract as its summary. This
module computes that view; cli.py renders it.

Per-function state (schema.FunctionState), derived from three inputs —
sidecars, drift report, and the latest enforcement results from
.contracts-cache/ — with this precedence:

    no entry                      -> UNCOVERED
    drift says stale              -> STALE
    any enforced clause failing   -> FAILING
    any clause still DRAFTED      -> UNTRIAGED   (enforced, but visually
                                                  distinct: pinned, not
                                                  promised)
    otherwise                     -> PASSING

Coverage is measured against functions, not lines: "34/61 functions
contracted, 12 untriaged" is the headline number.

Module rollup (post-v1, inferred-low in SPEC): a module's view is its
public functions' contracts plus the system invariants it touches.
Skip until the flat per-function view works.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .schema import FunctionState


@dataclass
class FunctionView:
    qualname: str
    source_path: Path
    state: FunctionState
    summary: list[str]     # one line per clause: "[confirmed] pre: item.stack_size >= 1"


def build(root: Path) -> list[FunctionView]:
    """Compute the dashboard for a repo.

    TODO(you): discover functions via the backend, load sidecars, run
    drift.check, read enforcement results from .contracts-cache/, apply
    the precedence table above.
    """
    raise NotImplementedError
