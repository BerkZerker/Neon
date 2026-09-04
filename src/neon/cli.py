"""CLI entry point. Thin by design: parse args, call one module, print.

If a subcommand grows real logic, that logic is in the wrong file —
push it down into the module that owns it. The payoff: every feature
stays testable without invoking the CLI.

Subcommands (matching the data flow in __init__.py):

    neon scan     [path]   discover functions, report coverage
                           (what exists / what's uncovered — no LLM)
    neon draft    [path]   LLM-draft contracts for uncovered functions,
                           write sidecars with DRAFTED clauses
    neon triage   [path]   interactive review queue, lowest confidence
                           first; writes triage decisions to sidecars
    neon check    [path]   run enforcement (asserts via the target's
                           tests + generated property tests); write
                           results to .contracts-cache/
    neon drift    [path]   compare sidecar hashes vs current code;
                           nonzero exit if confirmed contracts are stale
    neon status   [path]   the dashboard: per-function state + coverage

Suggested build order: scan -> (hand-write a sidecar) -> check ->
drift -> triage -> draft -> status. Note draft is LAST even though the
pipeline runs it first — everything else is testable with hand-written
sidecars, and building enforcement first means you'll know drafted
contracts actually run the moment drafting comes online.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="neon",
        description="Contract layer: draft, triage, enforce.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    for name, help_text in [
        ("scan", "discover functions and report contract coverage"),
        ("draft", "LLM-draft contracts for uncovered functions"),
        ("triage", "review drafted clauses (lowest confidence first)"),
        ("check", "run contract enforcement"),
        ("drift", "detect contracts invalidated by code changes"),
        ("status", "per-function dashboard"),
    ]:
        p = sub.add_parser(name, help=help_text)
        p.add_argument(
            "path", nargs="?", default=".", type=Path, help="repo root (default: cwd)"
        )

    args = parser.parse_args(argv)

    print("args:", args)

    # TODO(you): dispatch. A dict {command_name: handler} beats an
    # if/elif ladder. Each handler: load what it needs, call the owning
    # module, print, return an exit code (drift's is load-bearing — CI
    # keys off it).
    #
    # Command responsibilities:
    # -------------------------------------------------------------------------
    # 1. scan [path]
    #    - Zero-execution discovery: backend.discover(path) finds source files,
    #      backend.extract(file) AST-parses FunctionInfo (qualname, params, etc.).
    #    - Sidecar loading: sidecar.load(file) reads existing .contracts.yaml.
    #    - Compare extracted functions vs sidecar entries to identify covered vs
    #      uncovered functions.
    #    - Report coverage metrics: total functions found, count/percentage
    #      covered vs uncovered, and list uncovered functions. (No LLM calls).
    #
    # 2. draft [path]
    #    - Find uncovered functions (or functions needing contract additions).
    #    - Call drafting.draft(fn, existing) to prompt LLM for proposed PRE,
    #      POST, RAISES clauses with status=DRAFTED and confidence scores.
    #    - Compute AST code_hash via hashing.code_hash(fn) for the ContractEntry.
    #    - Write/update sidecar files via sidecar.save().
    #
    # 3. triage [path]
    #    - Load all sidecars under path via sidecar.load().
    #    - Build review queue sorted lowest confidence first via triage.triage_queue().
    #    - Run interactive CLI loop showing function source + proposed clause:
    #      [c]onfirm, [e]dit, [r]elease, or [s]kip.
    #    - Call triage.confirm/edit/release to mutate clauses, update author (by)
    #      and timestamp (at), refresh entry.code_hash to current, and save sidecars.
    #
    # 4. check [path]
    #    - Lower contracts into executable checks.
    #    - Apply runtime assert wrappers (enforcement.asserts.install()) and/or
    #      generate Hypothesis property tests (enforcement.proptests.write_tests()).
    #    - Run the test suite (e.g. pytest) against the target code.
    #    - Save run outcomes to .contracts-cache/ and print violation reports.
    #    - Return non-zero exit code if contract violations occur.
    #
    # 5. drift [path]
    #    - AST-parse current functions with backend.extract() and hash them.
    #    - Load stored ContractEntry objects from existing sidecars.
    #    - Call drift.check(entries, functions) to classify:
    #      CURRENT (hashes match), STALE (qualname exists, hash differs),
    #      RENAMED (qualname gone, identical hash), DELETED (qualname gone, no match).
    #    - Automatically apply renames via drift.relink().
    #    - Print drift report.
    #    - Return non-zero exit code if any confirmed contract is STALE (crucial for CI).
    #
    # 6. status [path]
    #    - Dashboard view: combine sidecars, drift status, and .contracts-cache/ results.
    #    - Call views.build(path) to evaluate FunctionState for each function
    #      (PASSING, FAILING, UNTRIAGED, STALE, UNCOVERED).
    #    - Render a formatted table/overview showing per-function state, clause
    #      summaries, and repo-wide contract coverage statistics.
    # -------------------------------------------------------------------------
    print(f"neon {args.command}: not implemented yet (path={args.path})")
    return 2


if __name__ == "__main__":
    sys.exit(main())
