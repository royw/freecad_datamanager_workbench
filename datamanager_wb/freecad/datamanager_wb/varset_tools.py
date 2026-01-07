from typing import Iterator

import FreeCAD as App

# def getVarsetProperties(doc: App.Document, varset_name: str) -> dict[str, str]:
#     var_set = doc.getObject("VarSet")
#     result: dict[str, str] = {}
#     properties = var_set.PropertiesList
#     for prop in properties:
#         result[prop] = getattr(var_set, prop)
#     return result


def getVarsets() -> Iterator[str]:
    doc = App.ActiveDocument
    if doc is None:
        return
    for obj in doc.Objects:
        if obj.TypeId == "App::VarSet":
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
