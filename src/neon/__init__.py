"""Neon: a contract layer for existing codebases.

An LLM drafts per-function contracts, a human triages them, and the
system enforces them. See SPEC.md at the repo root for the full design.

Data flow, end to end:

    discovery (backend parses source) -> FunctionInfo
        -> drafting (LLM proposes clauses) -> sidecar (drafted)
        -> triage (human confirms/edits/releases) -> sidecar (confirmed/released)
        -> enforcement (asserts + property tests) -> .contracts-cache/ results
        -> drift (hash check on change) -> stale flags
        -> views (dashboard reads sidecars + cache, never source)
"""

__version__ = "0.1.0"
