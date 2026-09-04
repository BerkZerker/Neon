"""Python backend: zero-execution discovery of functions via the stdlib.

Nothing in here may import or exec the target code. The target repo is
someone else's project — it may have side effects on import, missing
dependencies, or the planted bug. Parse text, produce data.

How it works, in one paragraph
------------------------------
`discover` walks a directory with pathlib and returns every `.py` file
that isn't in a junk directory (virtualenvs, caches, tests). `extract`
reads one of those files as plain text and hands it to the stdlib `ast`
module, which turns the text into a tree of nodes (Module -> ClassDef ->
FunctionDef -> ...) WITHOUT running any of it. We walk that tree, and
every FunctionDef we find becomes a FunctionInfo.

Decisions made here (the schema forces us to pick and stay consistent)
----------------------------------------------------------------------
* qualname: the dotted path of enclosing classes plus the function
  name — "Inventory.add_item", or "Outer.Inner.method" for a class
  nested in a class. This mirrors Python's own `__qualname__` for
  everything we emit, so enforcement can find the object by that path.
* Nested functions (a `def` inside another `def`) are SKIPPED. They
  live in a closure that can't be reached from outside to wrap with an
  assert, so a contract on them could never be enforced — and they'd
  bloat the triage queue. We still descend into classes nested inside
  classes, because those ARE reachable as attributes.
* `source` is the function's own text exactly as it sits in the file,
  leading indentation included. hashing.py dedents methods itself, so
  we do not strip it here.
* `discover` skips hidden directories (".venv", ".git", ".contracts-cache"
  are all dot-prefixed), a few well-known build/cache dirs, and test
  code. Contracting the tool's own virtualenv or a test suite would
  drown the coverage number in functions nobody wants contracted.
"""

from __future__ import annotations

import ast
from pathlib import Path

from ..schema import FunctionInfo

# Directory names that never contain code the user wants contracted.
# Hidden dirs (".venv", ".git", ".pytest_cache", ".contracts-cache", ...)
# are handled separately by the leading-dot check in `_is_junk_dir`.
_SKIP_DIRS = frozenset(
    {
        "__pycache__",
        "venv",
        "env",
        "node_modules",
        "build",
        "dist",
        "site-packages",
        "tests",
        "test",
    }
)


def _is_junk_dir(name: str) -> bool:
    """True if a directory with this name should not be descended into."""
    return name.startswith(".") or name in _SKIP_DIRS


def _is_test_file(path: Path) -> bool:
    """pytest's default naming: test_*.py or *_test.py."""
    return path.name.startswith("test_") or path.stem.endswith("_test")


def discover(path: Path) -> list[Path]:
    """Return every Python source file under `path` worth contracting.

    `path` may also be a single .py file, in which case it is returned
    as-is (handy for `neon scan some/module.py`).

    The result is sorted so two runs over the same tree print in the
    same order — determinism matters because scan output ends up in
    terminals, CI logs, and diffs.
    """
    if path.is_file():
        return [path] if path.suffix == ".py" else []

    found: list[Path] = []
    # `rglob("*.py")` recursively yields every path under `path` whose
    # name matches the glob. It does NOT know about our denylist, so we
    # filter afterwards by looking at each file's parent directories.
    for file in path.rglob("*.py"):
        # `relative_to(path)` strips the prefix the user passed in, so we
        # only judge directories *inside* the target — if the user
        # themselves is standing in a folder called "build", that's fine.
        # `.parts` is the tuple of path components; the last one is the
        # filename, so `[:-1]` leaves just the directories.
        inner_dirs = file.relative_to(path).parts[:-1]
        if any(_is_junk_dir(d) for d in inner_dirs):
            continue
        if _is_test_file(file):
            continue
        found.append(file)

    return sorted(found)


def _param_names(args: ast.arguments) -> list[str]:
    """Flatten an `ast.arguments` node into parameter names, in order.

    Python has five kinds of parameter and `ast` stores each kind in its
    own list on the `arguments` node. For `def f(a, /, b, *args, c, **kw)`:

        posonlyargs = [a]      before the `/`
        args        = [b]      ordinary positional-or-keyword
        vararg      = args     the single `*name`, or None
        kwonlyargs  = [c]      after the `*`
        kwarg       = kw       the single `**name`, or None

    Each of those is an `ast.arg` whose `.arg` attribute is the name.
    We only keep names (not defaults or annotations) — that's all the
    schema asks for in v1.
    """
    names = [a.arg for a in args.posonlyargs]
    names += [a.arg for a in args.args]
    if args.vararg is not None:
        names.append(args.vararg.arg)
    names += [a.arg for a in args.kwonlyargs]
    if args.kwarg is not None:
        names.append(args.kwarg.arg)
    return names


def _walk(
    node: ast.AST,
    scope: list[str],
    lines: list[str],
    file: Path,
    out: list[FunctionInfo],
) -> None:
    """Recursively visit `node`'s children, collecting functions into `out`.

    `scope` is the stack of enclosing class names — it's what turns a
    bare `add_item` into `Inventory.add_item`. We push a name when we
    enter a class body and pop when we leave it.

    We deliberately write our own recursion instead of using `ast.walk`:
    `ast.walk` visits every node in the tree but forgets where each one
    came from, and the whole point is knowing which class a def is in.
    """
    # `ast.iter_child_nodes` yields the direct children of a node — for a
    # Module or ClassDef that's the statements in its body.
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.append(_function_info(child, scope, lines, file))
            # Do NOT recurse into the function body: nested defs are
            # unreachable for enforcement (see module docstring).
        elif isinstance(child, ast.ClassDef):
            # Methods live in the class body; descend with the class name
            # pushed onto the scope so their qualnames get the prefix.
            scope.append(child.name)
            _walk(child, scope, lines, file, out)
            scope.pop()
        # Anything else (imports, assignments, if-blocks at module level,
        # ...) is ignored. We don't descend into `if` bodies either, so a
        # def guarded by `if TYPE_CHECKING:` is treated as not existing —
        # it also doesn't exist at runtime, so nothing could enforce it.


def _function_info(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    scope: list[str],
    lines: list[str],
    file: Path,
) -> FunctionInfo:
    """Build the FunctionInfo for one `def` node."""
    # Every ast node that came from source carries its position:
    # `lineno` / `end_lineno` are 1-indexed line numbers of the node's
    # first and last line. For a FunctionDef, `lineno` is the `def` line
    # itself — decorators above it are NOT included (they're in
    # `node.decorator_list` with their own positions).
    #
    # We slice whole lines rather than using `ast.get_source_segment`,
    # because that helper starts at the column of the `def` keyword and
    # would drop a method's leading indentation, which the schema says
    # to keep. `lines` was split with keepends=True so joining restores
    # the file's original newlines exactly.
    assert node.end_lineno is not None  # always set by ast.parse
    source = "".join(lines[node.lineno - 1 : node.end_lineno])

    return FunctionInfo(
        qualname=".".join([*scope, node.name]),
        source_path=file,
        lineno=node.lineno,
        params=_param_names(node.args),
        source=source,
        # `ast.get_docstring` returns the cleaned-up docstring (leading
        # indentation removed) or None if the first statement isn't a
        # string literal.
        docstring=ast.get_docstring(node),
    )


def extract(file: Path) -> list[FunctionInfo]:
    """Return one FunctionInfo per function defined in `file`.

    Result is in source order (by line number), which falls out of the
    walk naturally since ast keeps statements in the order written.

    If the file isn't valid Python, `ast.parse` raises SyntaxError. We
    pass the filename so the error message names the offending file;
    callers decide whether that's fatal.
    """
    text = file.read_text(encoding="utf-8")
    # `ast.parse` compiles text to a tree and stops there — no bytecode,
    # no execution. This is the whole "zero-execution" guarantee.
    tree = ast.parse(text, filename=str(file))
    # keepends=True keeps the "\n" on each line so re-joining a slice
    # reproduces the original text byte-for-byte.
    lines = text.splitlines(keepends=True)

    functions: list[FunctionInfo] = []
    _walk(tree, scope=[], lines=lines, file=file, out=functions)
    return functions
