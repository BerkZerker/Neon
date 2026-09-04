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
from collections.abc import Callable
from pathlib import Path

from . import sidecar
from .backends import python as backend
from .schema import FunctionInfo, Sidecar


def _coverage(
    functions: list[FunctionInfo], sc: Sidecar
) -> tuple[list[str], list[str]]:
    """Split one file's functions into (covered, uncovered) qualnames.

    "Covered" means the sidecar has an entry keyed by that qualname —
    nothing more. Whether its clauses are drafted, confirmed, or stale
    is status/drift's concern; scan only answers "does a contract exist".

    Both lists keep source order (extract() returns by lineno) so the
    report reads top-to-bottom like the file, not alphabetically.
    """
    # `sc.entries` is a dict keyed by qualname, so `in` is a fast lookup.
    # Entries with no matching function (deleted/renamed code) are
    # simply never visited here — that's drift's problem, not scan's.
    covered = [fn.qualname for fn in functions if fn.qualname in sc.entries]
    uncovered = [fn.qualname for fn in functions if fn.qualname not in sc.entries]
    return covered, uncovered


def _percent(covered: int, total: int) -> str:
    """'20%' for 1 of 5. A file with no functions reports 'n/a' rather
    than dividing by zero — 0% would wrongly suggest work to do."""
    if total == 0:
        return "n/a"
    # round() to an integer percent; 1/3 -> "33%", 2/3 -> "67%".
    return f"{round(100 * covered / total)}%"


def cmd_scan(args: argparse.Namespace) -> int:
    """Discover functions, compare against sidecars, print coverage.

    A report, not a gate: always exits 0. No LLM calls.
    """
    files = backend.discover(args.path)
    if not files:
        print(f"no source files found under {args.path}")
        return 0

    total_functions = 0
    total_covered = 0
    for file in files:
        functions = backend.extract(file)
        # A malformed hand-edited sidecar is the one thing scan refuses
        # to paper over: a silent "0 covered" would hide the typo.
        try:
            sc = sidecar.load(file)
        except sidecar.SidecarError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        covered, uncovered = _coverage(functions, sc)
        total_functions += len(functions)
        total_covered += len(covered)

        print(file)
        print(
            f"  {len(functions)} functions, {len(covered)} covered "
            f"({_percent(len(covered), len(functions))})"
        )
        if uncovered:
            print("  uncovered:")
            for qualname in uncovered:
                print(f"    {qualname}")

    # Repo-wide summary only earns its line when there's more than one
    # file to sum over; for a single file it would just repeat itself.
    if len(files) > 1:
        print(
            f"total: {total_functions} functions, {total_covered} covered "
            f"({_percent(total_covered, total_functions)})"
        )

    return 0


def _not_implemented(args: argparse.Namespace) -> int:
    print(f"neon {args.command}: not implemented yet (path={args.path})")
    return 2


HANDLERS: dict[str, Callable[[argparse.Namespace], int]] = {
    "scan": cmd_scan,
    "draft": _not_implemented,
    "triage": _not_implemented,
    "check": _not_implemented,
    "drift": _not_implemented,
    "status": _not_implemented,
}


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

    # Each handler: load what it needs, call the owning module, print,
    # return an exit code (drift's is load-bearing — CI keys off it).
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
    #    Where you start: args.path (a directory). Where you have to get to,
    #    for the toy repo with no sidecar written yet:
    #
    #        $ neon scan examples/toy
    #        examples/toy/inventory.py
    #          5 functions, 0 covered (0%)
    #          uncovered:
    #            Inventory.add_item
    #            Inventory.total_weight
    #            Inventory.remove_item
    #            damage
    #            process
    #
    #    The comparison is two sets of qualnames: {fn.qualname for fn in
    #    extract(file)} vs sidecar.load(file).entries.keys(). Covered is the
    #    intersection; uncovered is functions minus entries. (An entry with
    #    no matching function is drift's problem, not scan's.)
    #
    #    Acceptance test (README step 3): hand-write a sidecar with one entry
    #    for Inventory.add_item and the same command must say
    #    "1 covered (20%)" with four names listed. sidecar.load returns an
    #    empty Sidecar for a missing file, so scan never special-cases that.
    #    Exit 0 regardless of coverage — scan is a report, not a gate.
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
    return HANDLERS[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
