"""GUI selection helpers for the DataManager workbench.

This module contains small utilities for selecting FreeCAD objects referenced
by expression items.

The helper functions route FreeCAD/FreeCADGui access through `FreeCadPort` so
they can be tested (or at least imported) outside FreeCAD.
"""

from .domain.expression_item import ExpressionItem
from .domain.parsing_helpers import parse_expression_item_object_name
from .ports.freecad_context import FreeCadContext
from .ports.freecad_port import get_port


def select_object_from_expression_item(
    expression_item: ExpressionItem | str,
    *,
    ctx: FreeCadContext | None = None,
) -> None:
    """Select the FreeCAD object referenced by an expression item.

    The expressions list in the panel can provide either:
    - an `ExpressionItem` instance, or
    - its display string (e.g. ``"Object.Property = expr"``).

    This function resolves the owning object name and selects it in the model
    tree.

    Args:
        expression_item: Expression item object or expression display string.
    """
    obj_name: str | None
    if isinstance(expression_item, ExpressionItem):
        obj_name = expression_item.object_name
    else:
        obj_name = parse_expression_item_object_name(expression_item)
    if obj_name is None:
        return

    port = get_port(ctx)
    doc = port.get_active_document()
    if doc is None:
        return

    obj = port.get_object(doc, obj_name)
    if obj is None:
        port.warn(port.translate("Log", f"Workbench MainPanel: cannot find object '{obj_name}'\n"))
        return

    doc_name = getattr(doc, "Name", None)
    obj_internal_name = getattr(obj, "Name", None)
    if not isinstance(doc_name, str) or not doc_name:
        return
    if not isinstance(obj_internal_name, str) or not obj_internal_name:
        return

    port.clear_selection()
    port.add_selection(doc_name=doc_name, obj_name=obj_internal_name)
