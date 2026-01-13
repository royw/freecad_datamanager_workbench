"""Query helpers for FreeCAD VarSets.

Provides functions to list varsets, list their variables, and find expression
references to varset variables.
"""

import re
from collections.abc import Iterator

import FreeCAD as App

from .freecad_helpers import (
    build_expression_key,
    get_active_document,
    get_copy_on_change_names,
    get_object_name,
    get_typed_object,
    iter_document_objects,
    iter_named_expression_engine_entries,
)

translate = App.Qt.translate


def _get_active_doc() -> object | None:
    doc = get_active_document()
    if doc is None:
        return None
    return doc


def _iter_varset_names(doc: object) -> Iterator[str]:
    for obj in _iter_varset_objects(doc):
        name = get_object_name(obj)
        if name is not None:
            yield name


def _iter_filtered_varset_names(
    *,
    doc: object,
    excluded: set[str],
    exclude_copy_on_change: bool,
) -> Iterator[str]:
    for name in _iter_varset_names(doc):
        if exclude_copy_on_change and name in excluded:
            continue
        yield name


def _build_varset_search(
    *,
    varset_name: str,
    variable_name: str | None,
) -> tuple[list[str], re.Pattern[str] | None]:
    patterns: list[str] = [f"<<{varset_name}>>"]
    if not variable_name:
        return patterns, None

    patterns = [
        f"<<{varset_name}>>.{variable_name}",
        f"{varset_name}.{variable_name}",
    ]
    internal_var_re = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(variable_name)}(?![A-Za-z0-9_])")
    return patterns, internal_var_re


def _matches_varset_expression(
    *,
    expr_text: object,
    patterns: list[str],
    internal_var_re: re.Pattern[str] | None,
    obj: object,
    varset_name: str,
) -> bool:
    text = str(expr_text)
    if any(p in text for p in patterns):
        return True
    return _matches_internal_var_ref(
        internal_var_re=internal_var_re,
        obj=obj,
        varset_name=varset_name,
        text=text,
    )


def _matches_internal_var_ref(
    *,
    internal_var_re: re.Pattern[str] | None,
    obj: object,
    varset_name: str,
    text: str,
) -> bool:
    if internal_var_re is None:
        return False
    if getattr(obj, "TypeId", None) != "App::VarSet":
        return False
    if getattr(obj, "Name", None) != varset_name:
        return False
    return internal_var_re.search(text) is not None


def _get_copy_on_change_varset_names(doc: "App.Document") -> set[str]:
    return get_copy_on_change_names(doc=doc, type_id="App::VarSet")


def _iter_varset_objects(doc: object) -> Iterator[object]:
    for obj in iter_document_objects(doc):
        if getattr(obj, "TypeId", None) == "App::VarSet":
            yield obj


def getVarsets(*, exclude_copy_on_change: bool = False) -> Iterator[str]:
    """Yield VarSet object names from the active document.

    Args:
        exclude_copy_on_change: When true, filters out VarSets that are created
            by FreeCAD's copy-on-change mechanism.

    Yields:
        The `Name` of each `App::VarSet` object.
    """
    doc = _get_active_doc()
    if doc is None:
        return

    excluded: set[str] = _get_copy_on_change_varset_names(doc) if exclude_copy_on_change else set()
    yield from _iter_filtered_varset_names(
        doc=doc,
        excluded=excluded,
        exclude_copy_on_change=exclude_copy_on_change,
    )


def _is_excluded_varset_property(prop: object) -> bool:
    excluded = {
        "ExpressionEngine",
        "Label",
        "Label2",
        "Visibility",
        "Placement",
        "Group",
        "Material",
        "Proxy",
        "Shape",
        "State",
        "ViewObject",
    }
    return str(prop) in excluded


def _get_varset(doc: object, varset_name: str) -> object | None:
    varset = get_typed_object(doc, varset_name, type_id="App::VarSet")
    if varset is None:
        return None
    return varset


def _collect_varset_variable_names(varset: object) -> list[str]:
    names: list[str] = []
    for prop in getattr(varset, "PropertiesList", []):
        if _is_excluded_varset_property(prop):
            continue
        names.append(str(prop))
    names.sort()
    return names


def _get_varset_property_group(varset: object, prop: str) -> str:
    get_group = getattr(varset, "getGroupOfProperty", None)
    if not callable(get_group):
        return "Base"
    try:
        group = str(get_group(prop) or "").strip()
    except Exception:  # pylint: disable=broad-exception-caught
        return "Base"
    return group or "Base"


def getVarsetVariableGroups(varset_name: str) -> dict[str, str]:
    """Return mapping of variable/property name -> group for a VarSet.

    FreeCAD VarSet variables are stored as properties and may be organized into
    groups (property group). When no group is defined, FreeCAD uses "Base".
    """

    doc = _get_active_doc()
    if doc is None:
        return {}

    varset = _get_varset(doc, varset_name)
    if varset is None:
        return {}

    groups: dict[str, str] = {}
    for prop in getattr(varset, "PropertiesList", []):
        if _is_excluded_varset_property(prop):
            continue
        name = str(prop)
        groups[name] = _get_varset_property_group(varset, name)
    return groups


def getVarsetVariableNamesForGroup(varset_name: str, group_name: str | None) -> list[str]:
    """Return variable/property names defined on a VarSet, optionally filtered by group."""

    names = getVarsetVariableNames(varset_name)
    if not group_name:
        return names

    wanted = group_name.strip() or "Base"
    groups = getVarsetVariableGroups(varset_name)
    filtered = [n for n in names if groups.get(n, "Base") == wanted]
    filtered.sort()
    return filtered


def getVarsetVariableNames(varset_name: str) -> list[str]:
    """Return variable/property names defined on a VarSet.

    Args:
        varset_name: Name of the `App::VarSet` object.

    Returns:
        Sorted list of variable/property names. Built-in FreeCAD properties
        (Label, Placement, etc.) are excluded.
    """
    doc = _get_active_doc()
    if doc is None:
        return []

    varset = _get_varset(doc, varset_name)
    if varset is None:
        return []

    return _collect_varset_variable_names(varset)


def getVarsetReferences(varset_name: str, variable_name: str | None = None) -> dict[str, str]:
    """Find expression engine entries that reference a VarSet or variable.

    Args:
        varset_name: VarSet name.
        variable_name: Optional variable name to scope matches. When omitted,
            all expressions containing `<<VarSet>>` are considered.

    Returns:
        Mapping of ``"Object.Property"`` -> expression string.
    """
    doc = get_active_document()
    if doc is None:
        return {}

    patterns, internal_var_re = _build_varset_search(
        varset_name=varset_name,
        variable_name=variable_name,
    )

    results: dict[str, str] = {}
    for obj_name, lhs, expr_text in iter_named_expression_engine_entries(doc):
        if not _matches_varset_expression(
            expr_text=expr_text,
            patterns=patterns,
            internal_var_re=internal_var_re,
            obj=get_typed_object(doc, obj_name, type_id="App::VarSet") or object(),
            varset_name=varset_name,
        ):
            continue
        key = build_expression_key(obj_name=obj_name, lhs=lhs)
        results[key] = str(expr_text)
    return results
