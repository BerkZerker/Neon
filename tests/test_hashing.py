"""Tests for hashing.code_hash — write these FIRST, then make hashing.py
satisfy them. They are the definition of "the code changed".
"""

from pathlib import Path

import pytest

from neon.hashing import code_hash
from neon.schema import FunctionInfo


def fn(source: str, qualname: str = "f") -> FunctionInfo:
    """Helper: wrap raw source text as a FunctionInfo for hashing."""
    return FunctionInfo(qualname=qualname, source_path=Path("x.py"),
                        lineno=1, params=[], source=source)


class TestHashStability:
    def test_identical_source_same_hash(self):
        a = fn("def f(x):\n    return x + 1\n")
        b = fn("def f(x):\n    return x + 1\n")
        assert code_hash(a) == code_hash(b)

    @pytest.mark.skip(reason="TODO(you): unskip as you implement")
    def test_comment_change_same_hash(self):
        # A comment edit is not a semantic change — must NOT read as drift.
        a = fn("def f(x):\n    return x + 1\n")
        b = fn("def f(x):\n    # tweak\n    return x + 1\n")
        assert code_hash(a) == code_hash(b)

    @pytest.mark.skip(reason="TODO(you)")
    def test_whitespace_change_same_hash(self):
        a = fn("def f(x):\n    return x + 1\n")
        b = fn("def f(x):\n\n    return (x + 1)\n")
        assert code_hash(a) == code_hash(b)

    @pytest.mark.skip(reason="TODO(you)")
    def test_indented_method_source_parses(self):
        # extract() hands you method source with leading indentation —
        # hashing must cope (hint: textwrap.dedent).
        a = fn("    def f(self):\n        return 1\n")
        assert code_hash(a)


class TestHashSensitivity:
    @pytest.mark.skip(reason="TODO(you)")
    def test_semantic_change_different_hash(self):
        a = fn("def f(x):\n    return x + 1\n")
        b = fn("def f(x):\n    return x + 2\n")
        assert code_hash(a) != code_hash(b)

    @pytest.mark.skip(reason="TODO(you)")
    def test_rename_only_same_hash(self):
        # Load-bearing for drift's RENAMED detection: same body under a
        # new name must produce the SAME hash. Decide: does the function
        # NAME participate in the hash? (It must not, or renames are
        # undetectable. Params must, though — changing a signature is
        # semantic.)
        a = fn("def f(x):\n    return x * 2\n", qualname="f")
        b = fn("def g(x):\n    return x * 2\n", qualname="g")
        assert code_hash(a) == code_hash(b)
