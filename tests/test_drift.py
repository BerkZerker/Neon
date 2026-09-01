"""Tests for drift.check. Each test is one row of the classification
table in drift.py's docstring. Depends on hashing working first."""

import pytest


@pytest.mark.skip(reason="TODO(you): after hashing.py")
def test_unchanged_function_is_current():
    ...


@pytest.mark.skip(reason="TODO(you)")
def test_changed_body_is_stale():
    ...


@pytest.mark.skip(reason="TODO(you)")
def test_renamed_function_relinks_not_deletes():
    # Same body, new qualname, entry under old name only.
    # Expect: report.renamed == [(old, new)], nothing in deleted.
    # This is THE test that justifies hashing ignoring the name.
    ...


@pytest.mark.skip(reason="TODO(you)")
def test_removed_function_is_deleted():
    ...


@pytest.mark.skip(reason="TODO(you)")
def test_stale_confirmed_clause_fails_ci():
    # DriftReport.fails_ci is what CI keys off — pin it precisely:
    # stale + confirmed clause -> True; stale + only drafted -> False.
    ...
