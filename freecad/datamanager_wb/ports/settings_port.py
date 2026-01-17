# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileNotice: Part of the DataManager addon.

"""Settings port abstraction for Qt settings persistence.

This module isolates QtCore.QSettings behind a small interface so the UI layer
can be tested with a fake settings store.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from PySide import QtCore


class SettingsPort(Protocol):
    """Port interface for reading/writing persistent UI settings."""

    def value(self, key: str, default: object | None = None) -> object | None:
        """Return a stored value for key, or default when unset."""

    def set_value(self, key: str, value: object) -> None:
        """Persist a value under the given key."""


class QtSettingsAdapter:
    """Runtime implementation of `SettingsPort` using QtCore.QSettings."""

    def __init__(self, *, group: str, app: str) -> None:
        self._group = group
        self._app = app

    def _get_settings(self) -> QtCore.QSettings:
        from PySide import QtCore

        return QtCore.QSettings(self._group, self._app)

    def value(self, key: str, default: object | None = None) -> object | None:
        """Return a stored value from Qt settings."""

        settings = self._get_settings()
        return settings.value(key, default)

    def set_value(self, key: str, value: object) -> None:
        """Persist a value to Qt settings."""

        settings = self._get_settings()
        settings.setValue(key, value)
