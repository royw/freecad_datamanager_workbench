# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileNotice: Part of the DataManager addon.

"""Typed parent/child references for list widget selections.

The UI stores these objects in `QListWidgetItem` user data to preserve a
structured representation of `parent.child` identifiers."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ParentChildRef:
    """Structured identifier of a `parent.child` reference.

    This type is used as a stable representation of list items in the UI
    (VarSet variables and Spreadsheet aliases). The UI often renders items as a
    string but needs to retain the structured parts for querying and mutations.

    Attributes:
        parent: The parent container name (e.g. VarSet name, Spreadsheet name).
        child: The child identifier within the parent (e.g. variable/alias).
    """

    parent: str
    child: str

    @property
    def text(self) -> str:
        """Return the canonical `parent.child` string form."""
        return f"{self.parent}.{self.child}"


def parse_parent_child_ref(text: str) -> ParentChildRef | None:
    """Parse a `parent.child` string into a :class:`ParentChildRef`.

    Args:
        text: A string expected to contain exactly one dot separating parent
            and child.

    Returns:
        A :class:`ParentChildRef` when parsing succeeds, otherwise ``None``.
    """

    if "." not in text:
        return None
    parent, child = text.split(".", 1)
    if not parent or not child:
        return None
    return ParentChildRef(parent=parent, child=child)


def normalize_parent_child_items(items: list[ParentChildRef] | list[str]) -> list[str]:
    """Normalize a list of selection items to their `parent.child` string form."""
    normalized: list[str] = []
    for item in items:
        if isinstance(item, ParentChildRef):
            normalized.append(item.text)
        else:
            normalized.append(item)
    return normalized
