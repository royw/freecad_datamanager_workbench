"""Mutation helpers for FreeCAD VarSets.

Contains operations that modify VarSets, such as removing a variable property.
"""

from .freecad_context import FreeCadContext
from .freecad_port import get_port


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


def removeVarsetVariable(
    varset_name: str,
    variable_name: str,
    *,
    ctx: FreeCadContext | None = None,
) -> bool:
    """Remove a variable/property from a VarSet.

    Args:
        varset_name: Name of the `App::VarSet` object in the active document.
        variable_name: Name of the property to remove.

    Returns:
        ``True`` if the property was removed, otherwise ``False``.
    """
    doc = get_port(ctx).get_active_document()
    if doc is None:
        return False

    varset = get_port().get_typed_object(doc, varset_name, type_id="App::VarSet")
    if varset is None:
        return False

    if not _has_property(varset, variable_name):
        return False

    return _try_remove_property(varset, variable_name)
