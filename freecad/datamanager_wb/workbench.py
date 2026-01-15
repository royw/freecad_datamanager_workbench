"""Compatibility wrapper for FreeCAD workbench registration."""

from .entrypoints.workbench import DataManagerWorkbench

__all__ = [
    "DataManagerWorkbench",
]
