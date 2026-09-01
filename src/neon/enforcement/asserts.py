"""Runtime assertion enforcement for the Python backend.

Design choice you get for free in Python (and NOT in GDScript, where
this will be a source transformation): wrap functions at runtime
instead of editing source. The target repo's files are never modified.

How it fits together:
  - `checked(entry)` builds a decorator from a ContractEntry: evaluate
    PRE check_exprs against the bound arguments on entry, call the
    real function, evaluate POST check_exprs (with `result` bound) on
    exit. RAISES clauses check that raised exception types match.
  - An install hook applies the wrappers during the target's test runs.
    Simplest v1: a pytest plugin (conftest hook) that imports the
    target modules and monkey-patches contracted functions. Sampling /
    off-in-prod controls come later — v1 is dev/test only anyway.

Implementation hints:
  - Bind arguments by name with `inspect.signature(fn).bind(...)` +
    `apply_defaults()`, so check_exprs can say `item.weight > 0`
    regardless of positional/keyword call style.
  - Evaluate with `eval(expr, {"__builtins__": {}}, namespace)` where
    namespace = bound args (+ `result` for POST). Restricting builtins
    keeps clause exprs honest (pure predicates, no I/O). You'll want
    `len`/`isinstance`/`abs` etc. — pass an explicit allowlist dict.
  - A clause that FAILS must raise ContractViolation naming the
    function, the clause text, and the offending values. The error
    message is the product here — write it for the person debugging.
  - A clause whose expr itself blows up (NameError etc.) is a broken
    clause, not a violation — surface it distinctly so triage can fix it.
"""

from __future__ import annotations

from collections.abc import Callable

from ..schema import ContractEntry


class ContractViolation(AssertionError):
    """Raised when a function breaks its contract at runtime."""


def checked(entry: ContractEntry) -> Callable:
    """Return a decorator enforcing `entry` on the function it wraps.

    Enforces DRAFTED + CONFIRMED clauses with a check_expr; skips
    RELEASED and expr-less clauses.

    TODO(you): the wrapper described in the module docstring. Use
    functools.wraps so the wrapped function keeps its identity.
    """
    raise NotImplementedError


def install(root) -> None:
    """Apply contract wrappers across a repo's modules for a test run.

    TODO(you, after checked() works): load sidecars, import target
    modules, resolve qualnames to objects, monkey-patch. Start by just
    supporting module-level functions and methods one level deep.
    """
    raise NotImplementedError
