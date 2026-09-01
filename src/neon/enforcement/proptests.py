"""Property-based test generation from contracts (Hypothesis).

The shape of every generated test is the same:

    @given(<strategies for the function's params>)
    def test_contract_<qualname>(...):
        assume(<all PRE check_exprs>)       # only test valid inputs
        result = <call function>            # RAISES clauses catch here
        assert <each POST check_expr>       # the actual property

Two ways to build this — pick one and document why:
  a) Generate .py test files into .contracts-cache/generated_tests/ and
     run pytest on them. Debuggable (you can read the test), and the
     natural fit for CI. Recommended for v1.
  b) Build tests dynamically in-process. Less artifact churn, harder
     to debug.

The hard sub-problem is strategies: what does Hypothesis generate for
each parameter? v1 ladder, simplest first:
  1. Type hints on the function -> `st.from_type()`.
  2. No hints -> ask the LLM for a strategy per param IN THE TEST-
     GENERATION CALL — which per SPEC (Invariants) is a separate LLM
     call from drafting, separate context, so a misread contract and a
     misread test can't agree by accident. Don't merge these calls.
  3. No idea -> skip the test, mark the clause "unenforceable by
     proptest" in the run report (asserts still cover it).

Failure reporting: a failing property = the code violates its contract
on discoverable input. Report function, clause, and Hypothesis's
minimal counterexample — that counterexample is gold; surface it.
"""

from __future__ import annotations

from pathlib import Path

from ..schema import ContractEntry, FunctionInfo


def generate_test_source(fn: FunctionInfo, entry: ContractEntry) -> str | None:
    """Return the source of a Hypothesis test module for one function,
    or None if no clause is property-testable.

    TODO(you): build the test text per the module docstring. f-strings
    or textwrap.dedent templates are fine; a real templating engine is
    overkill.
    """
    raise NotImplementedError


def write_tests(root: Path) -> Path:
    """Generate tests for every contracted function into
    .contracts-cache/generated_tests/ and return that directory.

    TODO(you): iterate sidecars, call generate_test_source, write files.
    """
    raise NotImplementedError
