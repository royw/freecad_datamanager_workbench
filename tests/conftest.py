"""Pytest configuration for the DataManager repository.

Adds the in-repo package path to `sys.path` so unit tests can import the
workbench modules without installation.
"""

from __future__ import annotations

from pathlib import Path
import sys
import types


_repo_root = Path(__file__).resolve().parents[1]
_sys_path_entry = str(_repo_root)
if _sys_path_entry not in sys.path:
    sys.path.insert(0, _sys_path_entry)


def _install_freecad_stubs() -> None:
    if "FreeCAD" not in sys.modules:
        freecad = types.ModuleType("FreeCAD")

        class _Qt:
            @staticmethod
            def translate(_context: str, text: str) -> str:
                return text

        class _Console:
            @staticmethod
            def PrintMessage(_text: str) -> None:
                return

        freecad.Qt = _Qt
        freecad.Console = _Console
        freecad.ActiveDocument = None
        sys.modules["FreeCAD"] = freecad

    if "FreeCADGui" not in sys.modules:
        sys.modules["FreeCADGui"] = types.ModuleType("FreeCADGui")


_install_freecad_stubs()
