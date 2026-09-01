# Neon

A contract layer for existing codebases: an LLM drafts per-function
contracts, a human triages them, the system enforces them. Full design
in [SPEC.md](SPEC.md). Python first; GDScript/Godot as backend #2.

## Layout

```
src/neon/
  schema.py           the shared types (fully defined — start by reading it)
  hashing.py          normalized AST hash          -> drift detection
  sidecar.py          YAML load/save               -> source of truth
  backends/           language-specific parsing (python.py now, gdscript.py v2)
  drafting.py         LLM proposes clauses
  triage.py           human confirm/edit/release
  enforcement/        asserts.py + proptests.py    -> "a contract only
                                                      exists if checked"
  drift.py            stale/renamed/deleted classification
  vocabulary.py       shared domain predicates
  views.py            per-function dashboard state
  cli.py              thin argparse dispatch
examples/toy/         tiny target repo to develop against (contains one
                      planted bug for enforcement to catch)
tests/                stub tests; unskip as you implement
```

## Setup

```
uv venv && uv pip install -e ".[dev]"
source .venv/bin/activate
pytest            # everything skipped/failing until you build it
neon scan .       # CLI wiring works; commands say "not implemented"
```

(The repo pins Python 3.12 via `.python-version`; uv picks it up
automatically.)

## Suggested build order

Each step is independently testable before the next; LLM drafting is
deliberately LAST so everything downstream of it already works when it
comes online.

1. **hashing.py** — unskip tests/test_hashing.py one at a time.
2. **sidecar.py** — same, tests/test_sidecar.py. After this you can
   hand-write a sidecar for `examples/toy/inventory.py`.
3. **backends/python.py** — `neon scan examples/toy` should report
   5 functions, coverage 0 (then N after your hand-written sidecar).
4. **enforcement/asserts.py** — `checked()` first; wrap `add_item` by
   hand in a scratch script and watch a violation raise.
5. **drift.py** — edit a toy function, `neon drift` flags it stale.
6. **triage.py + cli triage loop** — confirm your hand-written clauses.
7. **enforcement/proptests.py** — this should find the planted bug in
   `remove_item`.
8. **drafting.py** — the LLM call. Its output flows into a pipeline
   you already trust.
9. **views.py / neon status** — the dashboard, now that every state it
   displays can actually occur.
