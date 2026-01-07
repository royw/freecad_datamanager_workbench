import FreeCAD as App
import FreeCADGui as Gui

from .parsing_helpers import parse_expression_item_object_name

translate = App.Qt.translate


def select_object_from_expression_item(text: str) -> None:
    obj_name = parse_expression_item_object_name(text)
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
