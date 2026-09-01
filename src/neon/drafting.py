"""LLM drafting: propose contract clauses for a function.

Provider-agnostic by design — `draft()` takes a FunctionInfo and returns
Clauses; how you call the model (Anthropic SDK, local model, whatever)
is an implementation detail behind this function.

Spec invariants this module must uphold:
  * Drafted clauses are proposals: status=DRAFTED, confidence set,
    by/at left None. drafting NEVER touches a CONFIRMED clause — if an
    entry already exists, only propose additions/amendments for triage.
  * Separate contexts: contract drafting and test generation are
    SEPARATE LLM calls with separate prompts (SPEC: Invariants), so a
    shared misreading can't self-confirm. Don't "optimize" them into
    one call.

Prompt-design notes (the interesting part — take your time here):
  - Input: the function source, its docstring, and ideally a few call
    sites (grep the repo for `qualname(`; even crude call-site context
    dramatically improves precondition quality).
  - Ask for STRUCTURED output: kind, text, check_expr, confidence per
    clause. Parse strictly; discard clauses whose check_expr doesn't
    even compile (`compile(expr, "<clause>", "eval")`).
  - check_expr may reference the function's parameters by name, and
    `result` for POST clauses. Tell the model this vocabulary exactly.
  - Low confidence is a feature, not a failure: triage sorts by lowest
    confidence first, so honest uncertainty routes human attention.

Characterization fallback (SPEC, inferred-med — can wait until the main
path works): when the LLM can't infer a meaningful contract, record
observed input/output pairs from running existing tests and pin those.
"""

from __future__ import annotations

from .schema import Clause, ContractEntry, FunctionInfo


def draft(fn: FunctionInfo, existing: ContractEntry | None = None) -> list[Clause]:
    """Return proposed clauses for `fn`, all status=DRAFTED.

    If `existing` has confirmed clauses, propose only what's new —
    never restate or contradict a confirmed clause; a proposed
    amendment to one is a new DRAFTED clause the human triages.

    TODO(you): build the prompt, call your model, parse and validate
    the structured response into Clause objects.
    """
    raise NotImplementedError
