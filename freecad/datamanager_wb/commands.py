"""Compatibility wrapper for FreeCAD command registration."""

from .entrypoints.commands import register_commands

__all__ = [
    "register_commands",
]
