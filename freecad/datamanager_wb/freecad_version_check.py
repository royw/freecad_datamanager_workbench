"""Runtime version checks for supported FreeCAD and Python versions.

This module validates that the current FreeCAD and Python runtime meet the
minimum required versions for the workbench.
"""

import sys

import FreeCAD as App

# only works with 0.21.2 and above
FC_MAJOR_VER_REQUIRED = 1
FC_MINOR_VER_REQUIRED = 0
FC_PATCH_VER_REQUIRED = 2
FC_COMMIT_REQUIRED = 33772


def check_supported_python_version(
    major_ver: int, minor_ver: int, patch_ver: int = 0, git_ver: int = 0
) -> bool:
    """Return whether the given FreeCAD version tuple meets the minimum.

    Despite the historical name, this helper compares the provided FreeCAD
    version tuple against the minimum version constants defined in this module.

    Args:
        major_ver: FreeCAD major version.
        minor_ver: FreeCAD minor version.
        patch_ver: FreeCAD patch version.
        git_ver: FreeCAD build/commit number when available.

    Returns:
        ``True`` if the version is supported, otherwise ``False``.
    """

    return (major_ver, minor_ver, patch_ver, git_ver) >= (
        FC_MAJOR_VER_REQUIRED,
        FC_MINOR_VER_REQUIRED,
        FC_PATCH_VER_REQUIRED,
        FC_COMMIT_REQUIRED,
    )


def check_python_and_freecad_version() -> None:
    """Validate that the current runtime is compatible with the workbench.

    This function checks:

    - The running Python version (must satisfy the minimum required by the
      supported FreeCAD releases).
    - The running FreeCAD version/commit (when available).

    Failures are reported via `App.Console.PrintWarning` / `PrintLog`.
    No exception is raised; the workbench may continue to load with reduced
    functionality.
    """

    if not (sys.version_info[0] == 3 and sys.version_info[1] >= 11):
        App.Console.PrintWarning(
            App.Qt.translate(
                "Log",
                "Python version (currently {}.{}.{}) must be at least 3.11 "
                "in order to work with FreeCAD 1.0 and above\n",
            ).format(sys.version_info[0], sys.version_info[1], sys.version_info[2])
        )
        return

    # Check FreeCAD version
    App.Console.PrintLog(App.Qt.translate("Log", "Checking FreeCAD version\n"))
    ver = App.Version()
    major_ver = int(ver[0])
    minor_ver = int(ver[1])
    patch_ver = int(ver[2])
    gitver = ver[3].split()
    if gitver:
        gitver = gitver[0]
    if gitver and gitver != "Unknown":
        gitver = int(gitver)
    else:
        # If we don't have the git version, assume it's OK.
        gitver = FC_COMMIT_REQUIRED

    if not check_supported_python_version(major_ver, minor_ver, patch_ver, gitver):
        App.Console.PrintWarning(
            App.Qt.translate(
                "Log",
                "FreeCAD version (currently {}.{}.{} ({})) must be at least {}.{}.{} ({}) "
                "in order to work with Python 3.11 and above\n",
            ).format(
                major_ver,
                minor_ver,
                patch_ver,
                gitver,
                FC_MAJOR_VER_REQUIRED,
                FC_MINOR_VER_REQUIRED,
                FC_PATCH_VER_REQUIRED,
                FC_COMMIT_REQUIRED,
            )
        )
