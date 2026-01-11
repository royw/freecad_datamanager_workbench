"""Query helpers for FreeCAD VarSets.

Provides functions to list varsets, list their variables, and find expression
references to varset variables.
"""

import re
from collections.abc import Iterator
from typing import cast

import FreeCAD as App

translate = App.Qt.translate


def _get_active_doc() -> object | None:
    doc = App.ActiveDocument
    if doc is None:
        return None
    return cast(object, doc)


def _iter_varset_names(doc: object) -> Iterator[str]:
    for obj in _iter_varset_objects(doc):
        name = _get_object_name(obj)
        if name is not None:
            yield name


def _iter_filtered_varset_names(
    *,
    doc: object,
    excluded: set[str],
    exclude_copy_on_change: bool,
) -> Iterator[str]:
    for name in _iter_varset_names(doc):
        if _should_exclude_varset(
            exclude_copy_on_change=exclude_copy_on_change,
            name=name,
            excluded=excluded,
        ):
            continue
        yield name


def _iter_doc_objects(doc: object) -> Iterator[object]:
    for obj in getattr(doc, "Objects", []) or []:
        if obj is not None:
            yield obj


def _get_object_name(obj: object) -> str | None:
    name = getattr(obj, "Name", None)
    if isinstance(name, str) and name:
        return name
    return None


def _build_expression_key(*, obj_name: str, lhs: object) -> str:
    if str(lhs).startswith("."):
        return f"{obj_name}{lhs}"
    return f"{obj_name}.{lhs}"


def _iter_expression_engine_entries(doc: object) -> Iterator[tuple[object, object, object]]:
    for obj in _iter_doc_objects(doc):
        expressions = getattr(obj, "ExpressionEngine", None)
        if not expressions:
            continue
        for expr in expressions:
            try:
                lhs = expr[0]
                expr_text = expr[1]
            except Exception:  # pylint: disable=broad-exception-caught
                continue
            yield obj, lhs, expr_text


def _get_copy_on_change_groups(doc: "App.Document") -> list[object]:
    groups: list[object] = []
    direct = doc.getObject("CopyOnChangeGroup")
    if direct is not None:
        groups.append(direct)
    for obj in getattr(doc, "Objects", []):
        label = getattr(obj, "Label", None)
        if isinstance(label, str) and label.startswith("CopyOnChangeGroup"):
            groups.append(obj)
    return groups


def _add_varset_name_from_object(o: object, names: set[str]) -> bool:
    if getattr(o, "TypeId", None) != "App::VarSet":
        return False
    name = _get_object_name(o)
    if name is not None:
        names.add(name)
    return True


def _iter_object_children(o: object) -> Iterator[object]:
    group = getattr(o, "Group", None)
    if group:
        for child in group:
            yield child
    out_list = getattr(o, "OutList", None)
    if out_list:
        for child in out_list:
            yield child


def _visit_copy_on_change(o: object, *, seen: set[int], names: set[str]) -> None:
    oid = id(o)
    if oid in seen:
        return
    seen.add(oid)
    if _add_varset_name_from_object(o, names):
        return
    for child in _iter_object_children(o):
        _visit_copy_on_change(child, seen=seen, names=names)


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
    # Copy-on-change produces one or more hidden App::LinkGroup objects with label like
    # "CopyOnChangeGroup" (and sometimes with a suffix). These groups do not expose a
    # "Group" property; their contents are reachable via OutList.

    seen: set[int] = set()
    names: set[str] = set()
    for group in _get_copy_on_change_groups(doc):
        _visit_copy_on_change(group, seen=seen, names=names)
    return names


def _iter_varset_objects(doc: object) -> Iterator[object]:
    for obj in _iter_doc_objects(doc):
        if getattr(obj, "TypeId", None) == "App::VarSet":
            yield obj


def _should_exclude_varset(
    *,
    exclude_copy_on_change: bool,
    name: str,
    excluded: set[str],
) -> bool:
    return bool(exclude_copy_on_change and name in excluded)


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
    getter = getattr(doc, "getObject", None)
    if not callable(getter):
        return None
    varset = getter(varset_name)
    if varset is None or getattr(varset, "TypeId", None) != "App::VarSet":
        return None
    return cast(object, varset)


def _collect_varset_variable_names(varset: object) -> list[str]:
    names: list[str] = []
    for prop in getattr(varset, "PropertiesList", []):
        if _is_excluded_varset_property(prop):
            continue
        names.append(str(prop))
    names.sort()
    return names


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
    # Find all objects that use expressions involving a specific VarSet
    doc = App.ActiveDocument
    if doc is None:
        return {}

    patterns, internal_var_re = _build_varset_search(
        varset_name=varset_name,
        variable_name=variable_name,
    )

    results: dict[str, str] = {}
    for obj, lhs, expr_text in _iter_expression_engine_entries(doc):
        obj_name = _get_object_name(obj)
        if obj_name is None:
            continue
        if not _matches_varset_expression(
            expr_text=expr_text,
            patterns=patterns,
            internal_var_re=internal_var_re,
            obj=obj,
            varset_name=varset_name,
        ):
            continue
        key = _build_expression_key(obj_name=obj_name, lhs=lhs)
        results[key] = str(expr_text)
    return results
