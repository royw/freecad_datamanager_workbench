import FreeCAD as App

translate = App.Qt.translate


def _get_alias_map(spreadsheet: object) -> dict[str, str]:
    getter = getattr(spreadsheet, "getAliases", None)
    if callable(getter):
        aliases = getter()
        if isinstance(aliases, dict):
            return {str(k): str(v) for k, v in aliases.items()}

    alias_prop = getattr(spreadsheet, "Alias", None)
    if isinstance(alias_prop, dict):
        return {str(k): str(v) for k, v in alias_prop.items()}

    return {}


def removeSpreadsheetAlias(spreadsheet_name: str, alias_name: str) -> bool:
    doc = App.ActiveDocument
    if doc is None:
        return False

    sheet = doc.getObject(spreadsheet_name)
    if sheet is None or getattr(sheet, "TypeId", None) != "Spreadsheet::Sheet":
        return False

    aliases = _get_alias_map(sheet)
    cell = aliases.get(alias_name)
    if not cell:
        return False

    setter = getattr(sheet, "setAlias", None)
    if not callable(setter):
        return False

    try:
        setter(cell, "")
    except Exception:  # pylint: disable=broad-exception-caught
        try:
            setter(cell, None)
        except Exception:  # pylint: disable=broad-exception-caught
            return False

    return True
