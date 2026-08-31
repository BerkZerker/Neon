# Contract Layer — Natural Language Spec

A tool that retrofits an existing codebase with per-function contracts: an LLM drafts them, a human triages them, and the system enforces them. The contract layer then serves as the trustworthy semantic view of the code.

This spec practices the provenance convention from our design discussion: `[stated]` lines came from you; `[inferred-high/med/low]` lines are my proposals at that confidence; `[agreed]` lines were proposals you reviewed and accepted. Review the remaining inferred lines before building.

## Target

- [agreed] The tool is a single Python codebase with per-language backends. The contract schema, sidecar format, and triage flow are language-neutral; only parsing and enforcement are per-backend.
- [agreed] Backend #1 (v1): Python. Contract enforcement via runtime assertions and Hypothesis property tests; mature ecosystem (icontract, deal) to borrow from or build on.
- [agreed] Backend #2 (v2): GDScript/Godot, targeting your mature Godot project. Parsing via `gdtoolkit` (Python GDScript parser); assertion injection via source transformation into GDScript `assert()`, which Godot strips from release export builds automatically; generated tests via gdUnit4 (fuzzer support) run headless (`godot --headless`) in CI.
- [inferred-med] Interface: CLI tool run against a repo, producing contract files plus a review UI (terminal or simple web view).
- [stated] Contracts live with the code in a fixed schema readable by both humans and the abstraction layer. [agreed] The adjacent sidecar file (below) satisfies this: same directory, same repo, same PR diff.

## Contract schema

- [stated] Every function gets a structured annotation stating expected input parameters and expected output.
- [inferred-high] Concretely, per function: preconditions (what must be true of inputs), postconditions (what is guaranteed of the return value and side effects), and exceptions (what it raises and when).
- [agreed] Format: parse-based, never import/introspection-based. GDScript has no user-definable decorators or annotations, so a decorator home is impossible there; for schema symmetry, Python uses the same parse-based representation. The sidecar is the source of truth; a later render step may inject read-only summaries into docstrings/doc comments.
- [inferred-med] Each contract line carries its own provenance tag: `drafted` (LLM-generated, untriaged), `confirmed` (human promoted to contract), `released` (human marked as incidental behavior, not a promise).
- [agreed] Contracts may reference a shared vocabulary file for domain terms so definitions bind to one place. For the Godot backend this is required, not optional: game-code contracts lean on engine-state predicates (e.g. `is_inside_tree(node)`, "emits `died` at most once") that must be defined once and reused.

## Storage: sidecar files

- [agreed] One sidecar per source file, adjacent to it: `player.gd` → `player.gd.contracts.yaml`, `foo.py` → `foo.py.contracts.yaml`. Adjacency localizes merge conflicts, moves with the file in refactors, and puts contract amendments in the same PR diff as the code they describe. (Godot fallback if editor-dock clutter annoys: a mirrored `contracts/` tree containing a `.gdignore`.)
- [agreed] Entries are keyed by qualified function name (`Inventory.add_item`) plus a hash of the function's normalized AST (whitespace/comment-insensitive). Hash mismatch = code changed since last triage → confirmed contracts flagged stale. Missing name + identical hash elsewhere = rename → relink instead of orphaning triage work.
- [agreed] Everything human- or LLM-authored lives in the sidecar together: contract clauses, provenance, triage status, confidence, who/when. No docstring/sidecar split — that doubles sync bugs.
- [agreed] Each clause is its own record (`kind`: pre/post/raises; `text`; `status`: drafted/confirmed/released; `confidence`; `by`; `at`), so triage is per-line.
- [agreed] Machine-derived state stays out: pass/fail status, last-run timestamps, and characterization traces go in a gitignored `.contracts-cache/` (or CI artifacts). Rule: the sidecar records human decisions and LLM proposals; anything recomputable by running checks is never committed. Every line in a sidecar diff is a semantic claim, never test-run noise.
- [agreed] Entries are sorted by qualified name so regeneration is deterministic and never produces spurious diffs. Sidecars are plain YAML with a strict schema; hand-edits in code review are legitimate and validated on next tool run.
- [agreed] No audit-log subsystem: `by`/`at` per clause plus git blame and PR history are the full history mechanism.

Example entry:

```yaml
Inventory.add_item:
  code_hash: "a3f91c…"
  clauses:
    - kind: pre
      text: "item.stack_size >= 1"
      status: confirmed
      by: sam
      at: 2026-08-31
    - kind: post
      text: "total_weight() increases by item.weight"
      status: drafted
      confidence: 0.6
    - kind: raises
      text: "InventoryFull when no slot accepts item"
      status: released   # observed behavior, not a promise
```

## Behaviors

- [stated] Drafting: given a function, the LLM generates its contract from the code, names, comments, and call sites.
- [stated] Enforcement: if a function violates its contract, the system detects it — a contract is only trusted if something runs the check.
- [inferred-high] Enforcement mechanisms, in order of implementation: (1) runtime assertions injected from the contract, on by default in dev/test, sampled or off in production; (2) property-based tests generated from the contract; (3) static call-site checking where feasible.
- [inferred-high] Triage flow: tool presents drafted contracts sorted by lowest LLM confidence first; human confirms, edits, or releases each line. Untriaged contracts still enforce (they pin current behavior) but are visually distinct.
- [inferred-med] Characterization fallback: where the LLM can't infer a meaningful contract, record observed input/output pairs from running existing tests and pin those as the contract until a human writes a better one.
- [inferred-high] Composition check: at every call site, verify the caller's state satisfies the callee's preconditions (statically where possible, via assertion otherwise). This is how per-function contracts chain into system-level claims.
- [stated] System invariants: a small set of cross-function invariants (e.g. conservation properties) declared separately, asserted at runtime.
- [inferred-med] Drift detection: on code change (CI hook or file watch), re-run that function's contract checks; if the code no longer satisfies its confirmed contract, fail loudly and require either a code fix or an explicit contract amendment. Contracts never silently rot.

## Views

- [stated] The abstraction layer reads contracts, not code: browsing a module shows each function's contract as its summary.
- [inferred-med] Dashboard states per function: passing / failing / untriaged / uncovered (no contract yet). Coverage is measured against functions, not lines.
- [inferred-low] Module-level rollup: a module's view is its public functions' contracts plus the system invariants it participates in.

## Invariants of the tool itself

- [stated] No contract exists without an enforcement mechanism attached.
- [inferred-high] A human-confirmed contract is never modified by the LLM; the LLM may only propose amendments for triage.
- [inferred-high] Contract generation and test generation are separate LLM calls with separate contexts, so a shared misreading can't self-confirm.
- [inferred-med] The tool never blocks on full coverage: untriaged and uncovered functions are legitimate resting states, made visible rather than forbidden.

## Godot backend notes (v2)

- [agreed] `assert()` stripping in release exports gives the spec's "on in dev/test, off in production" behavior natively; enforcement injection is a source transformation, not wrapping.
- [agreed] Property testing is weaker than Hypothesis but workable via gdUnit4 fuzzers; drift detection runs headless in CI.
- [agreed] Expect uneven contract quality by function kind: pure logic (inventory math, damage calc, save serialization) contracts well; `_process` and signal handlers will mostly end up `released` or characterization-pinned. Contracts about scene-tree state, signals, and node lifecycle route through the shared vocabulary.

## Out of scope for v1

- [inferred-high] Concurrency contracts, aliasing/ownership rules, formal verification backends, editing code through the contract view.
- [agreed] Non-Python enforcement is out of scope for v1, but the schema, sidecar format, and triage flow are language-neutral from day one so Godot lands as backend #2, not a fork.

## Resolved decisions

1. [agreed] Contract home: parse-based sidecar, not decorator or docstring (forced by GDScript, adopted for Python too).
2. [agreed] Triage state: in the sidecar, which is the single source of truth (see Storage).
3. [agreed] Target: v1 proves out on a small Python repo; the mature Godot project is the real target for the v2 backend.
