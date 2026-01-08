from typing import Iterator

import FreeCAD as App

translate = App.Qt.translate


def _get_copy_on_change_varset_names(doc: "App.Document") -> set[str]:
    # Copy-on-change produces one or more hidden App::LinkGroup objects with label like
    # "CopyOnChangeGroup" (and sometimes with a suffix). These groups do not expose a
    # "Group" property; their contents are reachable via OutList.

    groups: list[object] = []

    direct = doc.getObject("CopyOnChangeGroup")
    if direct is not None:
        groups.append(direct)

    for obj in getattr(doc, "Objects", []):
        label = getattr(obj, "Label", None)
        if isinstance(label, str) and label.startswith("CopyOnChangeGroup"):
            groups.append(obj)

    seen: set[int] = set()
    names: set[str] = set()

    def visit(o: object) -> None:
        oid = id(o)
        if oid in seen:
            return
        seen.add(oid)

        if getattr(o, "TypeId", None) == "App::VarSet":
            name = getattr(o, "Name", None)
            if isinstance(name, str) and name:
                names.add(name)
            return

        if hasattr(o, "Group"):
            for child in getattr(o, "Group", []) or []:
                visit(child)

        # For App::LinkGroup and many other objects, OutList is the easiest way to
        # discover contained / referenced objects.
        for child in getattr(o, "OutList", []) or []:
            visit(child)

    for group in groups:
        visit(group)

    return names


def getVarsets(*, exclude_copy_on_change: bool = False) -> Iterator[str]:
    doc = App.ActiveDocument
    if doc is None:
        return

    excluded: set[str] = set()
    if exclude_copy_on_change:
        excluded = _get_copy_on_change_varset_names(doc)

    for obj in doc.Objects:
        if obj.TypeId == "App::VarSet":
            if exclude_copy_on_change and obj.Name in excluded:
                continue
            yield obj.Name


def getVarsetVariableNames(varset_name: str) -> list[str]:
    doc = App.ActiveDocument
    if doc is None:
        return []

    varset = doc.getObject(varset_name)
    if varset is None or getattr(varset, "TypeId", None) != "App::VarSet":
        return []

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

    names: list[str] = []
    for prop in getattr(varset, "PropertiesList", []):
        if prop in excluded:
            continue

        names.append(prop)

    names.sort()
    return names


def getVarsetReferences(varset_name: str, variable_name: str | None = None) -> dict[str, str]:
    # Find all objects that use expressions involving a specific VarSet
    doc = App.ActiveDocument
    if doc is None:
        return {}

    patterns: list[str] = [f"<<{varset_name}>>"]
    if variable_name:
        patterns = [
            f"<<{varset_name}>>.{variable_name}",
            f"{varset_name}.{variable_name}",
        ]

    results: dict[str, str] = {}
    for obj in doc.Objects:
        if hasattr(obj, "ExpressionEngine") and obj.ExpressionEngine:
            expressions = obj.ExpressionEngine
            for expr in expressions:
                expr_text = expr[1]
                if any(p in expr_text for p in patterns):
                    results[f"{obj.Name}.{expr[0]}"] = expr_text

    return results
