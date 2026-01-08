"""Typed parent/child references for list widget selections.

The UI stores these objects in `QListWidgetItem` user data to preserve a
structured representation of `parent.child` identifiers."""
from dataclasses import dataclass


@dataclass(frozen=True)
class ParentChildRef:
    parent: str
    child: str

    @property
    def text(self) -> str:
        return f"{self.parent}.{self.child}"


def parse_parent_child_ref(text: str) -> ParentChildRef | None:
    if "." not in text:
        return None
    parent, child = text.split(".", 1)
    if not parent or not child:
        return None
    return ParentChildRef(parent=parent, child=child)
