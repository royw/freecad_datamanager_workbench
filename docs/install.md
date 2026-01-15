# Installation

## Install via FreeCAD Addon Manager

This is the recommended installation method for most users.

1. Open FreeCAD.
1. Open `Tools` -> `Addon manager...`.
1. Search for `DataManager` (or `Data Manager`).
1. Select the workbench and click `Install`/`Update`.
1. Restart FreeCAD.

Notes:

- Addon Manager installs workbenches into your FreeCAD user `Mod/` directory.
- After install/update, a FreeCAD restart is usually required for workbench discovery and command registration.

## Development installation (from GitHub)

FreeCAD discovers user workbenches by scanning your FreeCAD `Mod/` directory. For development (and for installing
from a cloned repo), the recommended workflow is to clone this repository and then create a link into your `Mod/`
directory pointing at the repository root.

After adding/removing a workbench (or changing the link), **restart FreeCAD**.

### 1) Clone the repository

```sh
git clone https://github.com/royw/freecad_datamanager_workbench.git
```

### 2) Locate your FreeCAD `Mod/` directory

FreeCAD’s per-user data directory is versioned. Typical locations:

#### Linux

- `~/.local/share/FreeCAD/<version>/Mod`
- Example: `~/.local/share/FreeCAD/v1-2/Mod`

#### macOS

- `~/Library/Application Support/FreeCAD/<version>/Mod`

#### Windows

- `%APPDATA%\\FreeCAD\\<version>\\Mod`

#### Find your FreeCAD `Mod/` directory

If you’re unsure, in FreeCAD go to:

- `Edit` -> `Preferences` -> `General` -> `Macro`

The macro directory is typically adjacent to your user `Mod/` directory.
If you find the `Macro/` directory and there is not a `Mod/` directory, create a `Mod/` directory in the same location.

### 3) Create the link

Link the repository’s directory into your FreeCAD user `Mod/` directory.

#### Linux (symlink)

```sh
ln -s /path/to/FreeCAD_Workbench_DataManager ~/.local/share/FreeCAD/<version>/Mod/datamanager_wb
```

#### macOS (symlink)

```sh
ln -s /path/to/FreeCAD_Workbench_DataManager "$HOME/Library/Application Support/FreeCAD/<version>/Mod/datamanager_wb"
```

#### Windows (PowerShell junction)

Use a directory junction:

```powershell
New-Item -ItemType Junction -Path "$env:APPDATA\\FreeCAD\\<version>\\Mod\\datamanager_wb" -Target "C:\\path\\to\\FreeCAD_Workbench_DataManager"
```
