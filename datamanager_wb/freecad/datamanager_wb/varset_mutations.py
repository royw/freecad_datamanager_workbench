"""Mutation helpers for FreeCAD VarSets.

Contains operations that modify VarSets, such as removing a variable property.
"""

import FreeCAD as App

translate = App.Qt.translate


def removeVarsetVariable(varset_name: str, variable_name: str) -> bool:
    doc = App.ActiveDocument
    if doc is None:
        return False

    varset = doc.getObject(varset_name)
    if varset is None or getattr(varset, "TypeId", None) != "App::VarSet":
        return False

    props = set(getattr(varset, "PropertiesList", []) or [])
    if variable_name not in props:
        return False

    try:
        varset.removeProperty(variable_name)
    except Exception:  # pylint: disable=broad-exception-caught
        return False

    return True
