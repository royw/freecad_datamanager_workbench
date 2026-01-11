"""Mutation helpers for FreeCAD VarSets.

Contains operations that modify VarSets, such as removing a variable property.
"""

from typing import cast

import FreeCAD as App

translate = App.Qt.translate


def _get_active_doc() -> object | None:
    doc = App.ActiveDocument
    if doc is None:
        return None
    return cast(object, doc)


def _get_varset(doc: object, varset_name: str) -> object | None:
    getter = getattr(doc, "getObject", None)
    if not callable(getter):
        return None
    varset = getter(varset_name)
    if varset is None or getattr(varset, "TypeId", None) != "App::VarSet":
        return None
    return cast(object, varset)


def _has_property(obj: object, property_name: str) -> bool:
    props = set(getattr(obj, "PropertiesList", []) or [])
    return property_name in props


def _try_remove_property(obj: object, property_name: str) -> bool:
    remover = getattr(obj, "removeProperty", None)
    if not callable(remover):
        return False
    try:
        remover(property_name)
    except Exception:  # pylint: disable=broad-exception-caught
        return False
    return True


def removeVarsetVariable(varset_name: str, variable_name: str) -> bool:
    """Remove a variable/property from a VarSet.

    Args:
        varset_name: Name of the `App::VarSet` object in the active document.
        variable_name: Name of the property to remove.

    Returns:
        ``True`` if the property was removed, otherwise ``False``.
    """
    doc = _get_active_doc()
    if doc is None:
        return False

    varset = _get_varset(doc, varset_name)
    if varset is None:
        return False

    if not _has_property(varset, variable_name):
        return False

    return _try_remove_property(varset, variable_name)
