"""Lightweight representation of an expression binding.

This module defines a small dataclass used to display and select expression
engine entries in the UI."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ExpressionItem:
    """A single expression binding shown in the UI.

    Instances represent one expression assignment (left-hand side and right-hand
    side) that belongs to a particular FreeCAD object. The UI uses these items
    to populate the expressions list and to select the referenced object when a
    user clicks an entry.

    Attributes:
        object_name: Name/label of the FreeCAD object that owns the expression.
        lhs: Left-hand side of the expression (typically "Object.Property").
        rhs: Right-hand side expression string.
        operator: Infix operator shown between `lhs` and `rhs` in the UI.
    """

    object_name: str
    lhs: str
    rhs: str
    operator: str = "="

    @property
    def display_text(self) -> str:
        """Return the display string shown in the expressions list."""
        return f"{self.lhs} {self.operator} {self.rhs}"
