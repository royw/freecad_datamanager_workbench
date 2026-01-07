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
    return (major_ver, minor_ver, patch_ver, git_ver) >= (
        FC_MAJOR_VER_REQUIRED,
        FC_MINOR_VER_REQUIRED,
        FC_PATCH_VER_REQUIRED,
        FC_COMMIT_REQUIRED,
    )


def check_python_and_freecad_version() -> None:
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
