"""Python backend: parse-based function extraction (never import-based).

We parse with `ast` instead of importing the target module because the
spec requires zero-execution analysis: importing arbitrary repo code
runs its top-level side effects, and the tool must be safe to point at
any codebase.

Implementation hints for extract():
  - `ast.parse(path.read_text())`, then walk for FunctionDef /
    AsyncFunctionDef nodes.
  - Qualnames: you need "Inventory.add_item", not "add_item". `ast.walk`
    loses parentage, so either walk recursively yourself carrying a
    name-stack (recommended — it's ~15 lines and you'll understand it),
    or annotate parents in a prepass.
  - Function source text: `ast.get_source_segment(full_text, node)`.
  - Params: node.args covers positional/keyword/varargs — for v1,
    plain positional + keyword names are enough.
  - Docstring: `ast.get_docstring(node)`.
  - Nested functions: decide and document. Suggestion: skip them in v1
    (they're rarely worth contracting and inflate the triage queue).
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from ..schema import FunctionInfo
from . import Backend


class PythonBackend(Backend):
    extensions = (".py",)

    def discover(self, root: Path) -> Iterator[Path]:
        """TODO(you): rglob for *.py, filter out denylisted dirs and
        our own generated files (anything under .contracts-cache/,
        generated test files)."""
        raise NotImplementedError

    def extract(self, source_path: Path) -> Iterator[FunctionInfo]:
        """TODO(you): parse and yield FunctionInfo per function/method.
        See module docstring for the ast recipes."""
        raise NotImplementedError
