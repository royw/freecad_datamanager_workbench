"""GUI selection helpers for the DataManager workbench.

This module contains small utilities for selecting FreeCAD objects referenced
by expression items."""

import FreeCAD as App
import FreeCADGui as Gui

from .expression_item import ExpressionItem
from .parsing_helpers import parse_expression_item_object_name

translate = App.Qt.translate


def select_object_from_expression_item(expression_item: ExpressionItem | str) -> None:
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

    doc = App.ActiveDocument
    if doc is None:
        return

    obj = doc.getObject(obj_name)
    if obj is None:
        App.Console.PrintWarning(
            translate("Log", f"Workbench MainPanel: cannot find object '{obj_name}'\n")
        )
        return

    Gui.Selection.clearSelection()
    Gui.Selection.addSelection(doc.Name, obj.Name)
