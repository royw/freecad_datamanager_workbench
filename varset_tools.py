doc = App.ActiveDocument

def getVarsetProperties(doc, varset_name: str) -> dict[str, str]:
    var_set = doc.getObject("VarSet")

    properties = var_set.PropertiesList
    for prop in properties:
        result[prop] = getattr(var_set, prop)
    return result

def getVarsets(doc) -> Iterator[str]:
    for obj in doc.Objects:
        if obj.TypeId == "App::VarSet":
            yield obj.Name

def getVarsetReferences(doc, varset_name:str, value: str|None=None) -> dict[str, str]:
    # Find all objects that use expressions involving a specific VarSet
    for obj in doc.Objects:
        if hasattr(obj, "ExpressionEngine") and obj.ExpressionEngine:
            expressions = obj.ExpressionEngine
            for expr in expressions:
                if varset_name in expr[1]:
                    if (value and value in expr[1]) or not value:
                        print(f"{obj.Name}.{varset_name} found in {obj.Label}({obj.Name}): {expr}")


getVarsetReferences(doc, "VarSet", "TriangleHoleSideLength")
