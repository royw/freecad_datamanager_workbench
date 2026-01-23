# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileNotice: Part of the DataManager addon.

"""
FreeCAD datamanager workbench
"""

try:
    import FreeCADGui as Gui  # pylint: disable=import-error
except Exception:  # pylint: disable=broad-exception-caught
    Gui = None

if Gui is not None:
    from .entrypoints.commands import register_commands
    from .entrypoints.workbench import DataManagerWorkbench
    from .freecad_version_check import check_python_and_freecad_version
    from .resources import TRANSLATIONSPATH
    from .ui.main_panel import get_main_panel

    Gui.addLanguagePath(TRANSLATIONSPATH)
    Gui.updateLocale()

    check_python_and_freecad_version()
    register_commands(get_main_panel)
    Gui.addWorkbench(DataManagerWorkbench())
