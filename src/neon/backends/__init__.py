"""Language backends. Everything language-specific lives behind this
interface; everything above it (sidecars, triage, drift, views) is
language-neutral. That separation is what makes Godot a backend later
instead of a fork (SPEC: Target).

A backend owns exactly two jobs:
  1. Parsing: walk source files, extract FunctionInfo per function.
  2. Enforcement lowering: turn confirmed/drafted clauses into something
     that runs (asserts, generated tests) for that language.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from pathlib import Path

from ..schema import FunctionInfo


class Backend(ABC):
    """Interface every language backend implements."""

    #: file extensions this backend claims, e.g. (".py",)
    extensions: tuple[str, ...] = ()

    @abstractmethod
    def discover(self, root: Path) -> Iterator[Path]:
        """Yield source files under `root` this backend can parse.

        Skip junk the user never wants contracted: virtualenvs, vendored
        deps, generated code. A simple denylist of directory names is
        fine for v1 (".venv", "node_modules", ".git", ...).
        """

    @abstractmethod
    def extract(self, source_path: Path) -> Iterator[FunctionInfo]:
        """Yield a FunctionInfo for every function/method in one file."""


def get_backend(name: str) -> Backend:
    """Registry lookup: "python" -> PythonBackend, later "gdscript".

    TODO(you): a dict of constructors is all this needs. Import inside
    the function to avoid importing every backend's deps at startup.
    """
    raise NotImplementedError
