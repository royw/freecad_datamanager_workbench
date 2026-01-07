import FreeCAD as App
import FreeCADGui as Gui

translate = App.Qt.translate


def _get_object_name_from_expression_item(text: str) -> str | None:
    left = text.split("=", 1)[0].strip()
    obj_name = left.split(".", 1)[0].strip()
    if not obj_name:
        return None
    return obj_name


def select_object_from_expression_item(text: str) -> None:
    obj_name = _get_object_name_from_expression_item(text)
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
