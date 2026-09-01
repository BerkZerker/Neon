"""Toy target codebase: what `neon` gets pointed at during development.

Small on purpose, but each function exercises a different part of the
tool. It also contains one REAL BUG (find it — or better, let your
enforcement find it) so "neon check" has something to catch.
"""

from dataclasses import dataclass, field


class InventoryFull(Exception):
    pass


@dataclass
class Item:
    name: str
    weight: float
    stack_size: int = 1


@dataclass
class Inventory:
    capacity: float
    items: list[Item] = field(default_factory=list)

    # Easy contract: pre (item fits, stack_size >= 1), post (weight grew),
    # raises (InventoryFull). The LLM should nail this one.
    def add_item(self, item: Item) -> int:
        if self.total_weight() + item.weight > self.capacity:
            raise InventoryFull(item.name)
        self.items.append(item)
        return len(self.items) - 1

    # Pure function, ideal for property tests.
    def total_weight(self) -> float:
        return sum(i.weight * i.stack_size for i in self.items)

    # The buggy one: remove_item's implicit contract is that the item is
    # gone and total weight decreased — but watch what happens when two
    # items share a name. A drafted postcondition should catch it.
    def remove_item(self, name: str) -> Item | None:
        found = None
        for i in self.items:
            if i.name == name:
                found = i
        if found is not None:
            self.items = [i for i in self.items if i.name != name]
        return found


# Module-level function with type hints -> exercises st.from_type()
# strategies. Its contract: result is non-negative, and zero iff
# armor >= attack.
def damage(attack: int, armor: int) -> int:
    return max(0, attack - armor)


# A function with a vague name and no hints — the kind the LLM will be
# least confident about. Good triage-queue fodder.
def process(data):
    out = {}
    for k, v in data.items():
        if v is not None:
            out[k.strip().lower()] = v
    return out
