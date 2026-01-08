"""Parsing helpers for workbench UI display strings.

This module centralizes small string parsers used to interpret `parent.child`
references and expression list display text."""

from .parent_child_ref import parse_parent_child_ref


def parse_varset_variable_item(text: str) -> tuple[str, str] | None:
    """Parse a UI list item of the form `VarSetName.VariableName`.

    Args:
        text: Display text from the variables list.

    Returns:
        Tuple of ``(varset_name, variable_name)`` if parsing succeeds;
        otherwise ``None``.
    """

    ref = parse_parent_child_ref(text)
    if ref is None:
        return None
    return ref.parent, ref.child


def parse_expression_item_object_name(text: str) -> str | None:
    """Extract the FreeCAD object name from an expression display string.

    The expressions list displays items like ``"Object.Property = expr"``.
    This helper extracts the object name portion (``"Object"``).

    Args:
        text: Expression list display string.

    Returns:
        The owning object name if it can be parsed, otherwise ``None``.
    """

    left = text.split("=", 1)[0].strip()
    ref = parse_parent_child_ref(left)
    if ref is None:
        return None
    return ref.parent
