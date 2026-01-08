"""GUI selection helpers for the DataManager workbench.

This module contains small utilities for selecting FreeCAD objects referenced
by expression items."""

import FreeCAD as App
import FreeCADGui as Gui

from .expression_item import ExpressionItem
from .parsing_helpers import parse_expression_item_object_name

translate = App.Qt.translate


def select_object_from_expression_item(expression_item: ExpressionItem | str) -> None:
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
