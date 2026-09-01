"""Tests for sidecar load/save. The one property that matters most:
determinism — same data in, byte-identical file out, every time."""

from pathlib import Path

import pytest

from neon import sidecar
from neon.schema import Clause, ClauseKind, ClauseStatus, ContractEntry, Sidecar


def sample(tmp_path: Path) -> Sidecar:
    src = tmp_path / "inventory.py"
    src.write_text("# fake\n")
    return Sidecar(
        source_path=src,
        entries={
            "Inventory.add_item": ContractEntry(
                qualname="Inventory.add_item",
                code_hash="a3f91cdeadbe",
                clauses=[
                    Clause(kind=ClauseKind.PRE, text="item.stack_size >= 1",
                           status=ClauseStatus.CONFIRMED, by="sam", at="2026-08-31"),
                    Clause(kind=ClauseKind.POST, text="total_weight() increases",
                           confidence=0.6),
                ],
            ),
        },
    )


@pytest.mark.skip(reason="TODO(you): unskip as you implement")
def test_round_trip(tmp_path):
    sc = sample(tmp_path)
    sidecar.save(sc)
    assert sidecar.load(sc.source_path).entries == sc.entries


@pytest.mark.skip(reason="TODO(you)")
def test_save_is_deterministic(tmp_path):
    sc = sample(tmp_path)
    sidecar.save(sc)
    first = sc.path.read_bytes()
    sidecar.save(sc)
    assert sc.path.read_bytes() == first


@pytest.mark.skip(reason="TODO(you)")
def test_entries_sorted_by_qualname(tmp_path):
    # Build a sidecar with entries inserted out of order; the saved YAML
    # must list them alphabetically.
    ...


@pytest.mark.skip(reason="TODO(you)")
def test_missing_sidecar_is_empty_not_error(tmp_path):
    src = tmp_path / "lonely.py"
    src.write_text("x = 1\n")
    assert sidecar.load(src).entries == {}


@pytest.mark.skip(reason="TODO(you)")
def test_bad_status_fails_loudly(tmp_path):
    # Hand-edited typo: status: "confrimed". Must raise SidecarError
    # whose message names the file and the entry.
    src = tmp_path / "inventory.py"
    src.write_text("# fake\n")
    (tmp_path / "inventory.py.contracts.yaml").write_text(
        "Inventory.add_item:\n"
        "  code_hash: abc123\n"
        "  clauses:\n"
        "    - kind: pre\n"
        "      text: x > 0\n"
        "      status: confrimed\n"
    )
    with pytest.raises(sidecar.SidecarError, match="Inventory.add_item"):
        sidecar.load(src)


@pytest.mark.skip(reason="TODO(you)")
def test_none_fields_omitted(tmp_path):
    # A drafted clause has no by/at — the YAML must not contain
    # "by: null" noise.
    sc = sample(tmp_path)
    sidecar.save(sc)
    text = sc.path.read_text()
    assert "null" not in text
