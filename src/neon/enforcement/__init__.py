"""Enforcement: a contract is only trusted if something runs the check.

SPEC's invariant — no contract exists without an enforcement mechanism —
is operationalized here. Two mechanisms in v1, in build order:

  1. asserts.py — runtime checks wrapped around the real function,
     active in dev/test. Cheap, immediate, catches violations in
     whatever code paths actually run.
  2. proptests.py — Hypothesis tests generated FROM the contract, so
     violations are hunted rather than waited for.

(Mechanism 3, static call-site checking, is post-v1.)

Enforcement runs both DRAFTED and CONFIRMED clauses — drafted contracts
pin current behavior (SPEC: Triage flow). RELEASED clauses are never
enforced. Results (pass/fail per clause) go to .contracts-cache/, never
into sidecars.
"""
