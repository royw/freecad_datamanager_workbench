"""
FreeCAD datamanager workbench
"""

try:
    import FreeCADGui as Gui  # pylint: disable=import-error
except Exception:  # pylint: disable=broad-exception-caught
    Gui = None

if Gui is not None:
    from ..freecad_version_check import check_python_and_freecad_version
    from ..resources import TRANSLATIONSPATH
    from ..ui.main_panel import get_main_panel
    from .commands import register_commands
    from .workbench import DataManagerWorkbench

    Gui.addLanguagePath(TRANSLATIONSPATH)
    Gui.updateLocale()

    check_python_and_freecad_version()
    register_commands(get_main_panel)
    Gui.addWorkbench(DataManagerWorkbench())
