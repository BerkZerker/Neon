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
        p.add_argument("path", nargs="?", default=".", type=Path,
                       help="repo root (default: cwd)")

    args = parser.parse_args(argv)

    # TODO(you): dispatch. A dict {command_name: handler} beats an
    # if/elif ladder. Each handler: load what it needs, call the owning
    # module, print, return an exit code (drift's is load-bearing — CI
    # keys off it).
    print(f"neon {args.command}: not implemented yet (path={args.path})")
    return 2


if __name__ == "__main__":
    sys.exit(main())
