# Development

## Historical notes (template provenance)

This repository was originally created from the FreeCAD Workbench-Starterkit template. The original template documentation is preserved here:

- [https://github.com/FreeCAD/freecad.workbench_starterkit](https://github.com/FreeCAD/freecad.workbench_starterkit)

- [HISTORICAL_README.md](HISTORICAL_README.md)

## Installing the workbench for development (symlink)

FreeCAD discovers user workbenches by scanning your user `Mod/` directory. During development, the simplest workflow is to create a symbolic link from FreeCAD’s `Mod/` directory to this repository root.

FreeCAD generally discovers available workbenches only during startup. After adding or removing a workbench (or updating a symlink), restart FreeCAD to ensure the workbench is detected.

### Find your `Mod/` directory

You can find the user `Mod/` directory in a few ways:

1. **In FreeCAD**

   - Open `Edit` -> `Preferences` -> `General` -> `Macro`.
   - Note the macro path shown there; the user `Mod/` directory is typically adjacent to it.

1. **Common Linux default**

   - FreeCAD stores per-version user data under `~/.local/share/FreeCAD/<version>/`.
   - For example:
     - `~/.local/share/FreeCAD/v1-2/Mod`

1. **Search your home directory**

   - If you’re unsure which version directory is active:
     - `find ~/.local/share/FreeCAD -maxdepth 3 -type d -name Mod`

### Create the symlink

From your FreeCAD user `Mod/` directory:

```sh
cd ~/.local/share/FreeCAD/v1-2/Mod
ln -s {path to project} DataManager
```

After creating the symlink, restart FreeCAD. The workbench should appear in the workbench selector.

### Reloading during development (Python console)

For iterative development, the normal procedure is to restart FreeCAD. However, you can sometimes reload Python modules from the FreeCAD Python console.

```py
import importlib
import freecad.DataManager
importlib.reload(freecad.DataManager)
```

Notes:

1. Reloading is useful for pure-Python changes, but it is not a full substitute for restarting FreeCAD.
1. FreeCAD’s workbench discovery and command registration are primarily done at startup; if you add/remove the workbench (e.g. create/remove the `Mod/` symlink), you still need to restart.
1. GUI objects, registered commands, and existing Qt widgets may keep references to old classes/functions; after a reload you may need to close/re-open the panel or restart FreeCAD if you see inconsistent behavior.

## Project layout and entrypoints

This project is distributed primarily as a FreeCAD Addon (installed into `Mod/`), but it is also structured as a Python package under the `freecad/` namespace.

Key entrypoints:

- `freecad/DataManager/init_gui.py`
  - FreeCAD GUI initialization hook.
  - Registers commands and adds the workbench (`Gui.addWorkbench`).
- `freecad/DataManager/entrypoints/workbench.py`
  - Defines `DataManagerWorkbench(Gui.Workbench)` (menus/toolbars, activation logging).
- `freecad/DataManager/entrypoints/commands.py`
  - Defines and registers FreeCAD commands.
  - Commands open/activate the UI panel.
- `freecad/DataManager/ui/main_panel.py`
  - Loads the Qt `.ui` file and implements the panel widget.

Key UI layers and boundaries:

- `freecad/DataManager/ui/main_panel_presenter.py`
  - Presenter responsible for formatting and computing UI list state.
  - Keeps the Qt widget thin.
- Ports/adapters that isolate runtime dependencies:
  - `freecad/DataManager/ports/freecad_context.py` / `freecad/DataManager/ports/freecad_port.py`
    - FreeCAD runtime access (`FreeCadContext`, `FreeCadPort`, `get_port(ctx)`).
  - `freecad/DataManager/ports/app_port.py`
    - Translation boundary (`App.Qt.translate`).
  - `freecad/DataManager/ports/gui_port.py`
    - FreeCADGui boundary (UI loading, MDI integration).
  - `freecad/DataManager/ports/settings_port.py`
    - Settings persistence boundary (wraps Qt settings).

Implementation note:

- Entry modules are structured with guarded/lazy imports so they can be imported by tooling/tests outside FreeCAD.

## Where to put changes (by layer)

The project is structured so that most logic can be tested outside FreeCAD.

When adding new behavior, prefer placing it in the lowest layer that makes sense:

- **UI wiring and rendering (Qt)**
  - `freecad/DataManager/ui/main_panel.py`
  - Keep this layer focused on widget lookup, signal wiring, and applying render state.
- **Presenter (UI state + formatting)**
  - `freecad/DataManager/ui/main_panel_presenter.py`
  - Owns list state computation, display formatting (Name vs Label), and orchestration plans.
- **UI-facing orchestration (FreeCAD refresh boundary)**
  - `freecad/DataManager/ui/panel_controller.py`
  - Owns document recompute + GUI refresh through `FreeCadPort`.
- **Reusable tab logic (domain-agnostic)**
  - `freecad/DataManager/domain/tab_controller.py`
  - Filtering, only-unused logic, selection rules.
- **Domain adapters (VarSets / Spreadsheets)**
  - `freecad/DataManager/varsets/varset_datasource.py`
  - `freecad/DataManager/spreadsheets/spreadsheet_datasource.py`
- **Low-level queries/mutations**
  - `freecad/DataManager/varsets/varset_query.py`, `freecad/DataManager/varsets/varset_mutations.py`
  - `freecad/DataManager/spreadsheets/spreadsheet_query.py`, `freecad/DataManager/spreadsheets/spreadsheet_mutations.py`
- **Runtime boundaries (ports/adapters)**
  - `freecad/DataManager/ports/freecad_context.py`, `freecad/DataManager/ports/freecad_port.py`
  - `freecad/DataManager/ports/app_port.py`, `freecad/DataManager/ports/gui_port.py`, `freecad/DataManager/ports/settings_port.py`

## Developer tooling

This section describes the tooling and recommended workflow.

### Prerequisite: FreeCAD type stubs (freecad-stubs)

Static type checking (mypy) for FreeCAD APIs requires type stubs. This project is set up to use:

- [https://github.com/ostr00000/freecad-stubs](https://github.com/ostr00000/freecad-stubs)

#### 1) Clone the stubs repo

Clone the repository somewhere on your machine (example uses `~/src`):

```sh
git clone https://github.com/ostr00000/freecad-stubs.git
```

#### 2) Select a branch that matches your FreeCAD version

The stubs repository provides version-specific branches. Pick the one closest to your FreeCAD version.

Example:

```sh
git -C freecad-stubs branch -r
git -C freecad-stubs checkout FreeCAD-0-20
```

If you are unsure, start with the newest available branch or `main` and adjust if you see type mismatches.

#### 3) Point mypy at the stubs

This repository uses `pyproject.toml` for mypy configuration. Ensure `tool.mypy.mypy_path` includes the stubs path.

Example (adjust to where you cloned `freecad-stubs`):

```toml
[tool.mypy]
mypy_path = "./:/path/to/freecad-stubs"
```

Then re-run:

```sh
task check
```

#### 4) (Optional) Configure your IDE

If you use VS Code / Pylance, configure the stub path similarly (so the editor resolves FreeCAD imports):

- Set `python.analysis.stubPath` to your `freecad-stubs` checkout path.
- Ensure your workspace interpreter is the same one you use for `uv run ...` / `task check`.

### Taskfile

The repository uses a `Taskfile.yml` to standardize common workflows. Note that the set of tasks is my python application development and includes tasks not directly related to FreeCAD Addon development, for example the release tasks.

### Required tools

`task check` is an orchestration task that calls formatting, linting, metrics, and test sub-tasks. The following tools are expected to be available (either as system executables, or installed into the active `uv` environment).

- **task**
  - Task runner used to invoke `task check` and its sub-tasks.
- **uv**
  - Python environment + tool runner (`uv run ...`, `uv tool install ...`).
- **python3**
  - Used both directly (small helper scripts) and via `uv run python`.
- **git**
  - Checked by `task env:check`.
- **pipx / pipxu**
  - Checked by `task env:check` (used for local deployment tasks).

Tools commonly invoked under `uv run ...` by `task check`:

- **ruff**
  - Formatting and linting.
- **mypy**
  - Type checking.
- **pytest**
  - Test runner (with plugins configured in `pyproject.toml`, e.g. xdist/timeout).
- **pymarkdownlnt**
  - Markdown linting.
- **mdformat**
  - Markdown formatting.
- **deadcode**
  - Dead-code detection.
- **radon**
  - Complexity checks.

Additional executables used by some subtasks:

- **bash**, **grep**, **sed**, **find**
  - Used by various helper tasks (shell wrappers and simple checks).
- **designer6**
  - Qt Designer (checked by `task env:check`; used when editing `.ui` files).

Common commands:

- `task check`
  - Runs formatting, linters, deadcode checks, complexity checks, and tests.
- `task docs`
  - Builds the MkDocs site and starts a local server.
- `task lint:markdown`
  - Runs markdown lint.
- `task help`
  - Lists available tasks.
- `task help:lint`
  - Lists available lint tasks.
- `task help:all`
  - Lists all tasks.

Taskfile documentation:

- [Taskfile documentation](https://taskfile.dev/)

Taskfile locations:

- Taskfile.yml
- taskfiles/Taskfile-\*.yml

### uv

The `uv` tool is used for dependency management. It is a drop-in replacement for `pip` and `poetry`.

Run: `uv sync` or `task env:install` to install dependencies and setup the virtual environment, `.venv\`.

### Editing the Qt .ui file

The panel UI is defined in:

- `freecad/DataManager/resources/ui/main_panel.ui`

Notes:

- Use `designer6` (Qt Designer) to edit the `.ui` file.
- Keep widget `objectName` values stable. `freecad/DataManager/ui/main_panel.py` expects specific names at runtime.
- After editing:
  - Run `task check`.
  - Launch FreeCAD and open the panel to verify the UI loads and widgets are found.

### Metrics

A custom metrics tool, `scripts/dev-metrics.py`, is provided to measure code quality metrics. This is normally ran with `task metrics`.

### scripts/

The repository includes small helper scripts in `scripts/` that are invoked by tasks or used during development:

- **scripts/check_docstrs.py**
  - AST-based docstring checker used by `task check`.
  - Verifies every module has a non-empty module docstring and that public functions/classes/methods have docstrings.
- **scripts/custom_argparse.py**
  - A custom `argparse.ArgumentParser` implementation that provides improved usage/help formatting.
  - Used by scripts in `scripts/` to present consistent CLI help output.
- **scripts/dev-metrics.py**
  - Aggregates project metrics (SLOC, complexity, coverage summary, risk/duplication-style signals) and prints a report.
  - Typically run via `task metrics`.
- **scripts/generate_test_docs.py**
  - Extracts test docstrings from the `tests/` tree and generates a Markdown table for documentation.
  - Used to keep test documentation in sync with the test suite.

### Testing

`task test` runs the test suite.
`task test:coverage` runs tests with coverage.

The test suite is designed to run outside of FreeCAD when possible.

Guidance:

- Prefer unit tests for parsing/formatting helpers and query logic that can be exercised without a live FreeCAD GUI.
- FreeCAD and Qt integration is inherently harder to test; keep GUI-facing behavior thin and delegate logic into testable helpers.

### Code Quality

`task check` runs formatting, linters, deadcode checks, complexity checks, and tests.
`task metrics` runs code quality metrics.

## Recommended workflow

Fork the [repository on GitHub](https://github.com/royw/freecad_datamanager_workbench) and clone it to your local machine. Then change into the cloned directory.

### Initial setup

Initial setup will install dependencies and verify that the required tools are installed and working:

1. `task env:install`
1. `task check`
1. `task test`
1. `task docs`

### Normal development workflow

The normal development workflow cycle is:

1. change code
1. `task check` $ verify no errors or warnings
1. commit changes

Make sure to update the documentation when your changes affect it:

1. change documenation
1. `task docs` # verify no errors or warnings and then the docs are correct using the local server.
1. commit changes

When your changes are finished:

1. `task check` # verify no errors or warnings
1. `task metrics` # for your own edification
1. `git push` # push your changes to your fork
1. create a pull request on GitHub.

Note: The master repository maintainer is responsible for updating the version number using `task version:bump` or `task version:bump:minor` or `task version:bump:major`.

## Manual smoke test (in FreeCAD)

Unit tests are designed to run outside FreeCAD, but the workbench still needs quick manual validation in FreeCAD before a release.

Suggested checklist:

- **Workbench registration**
  - Restart FreeCAD.
  - Confirm the workbench appears in the selector.
- **Commands and panel**
  - Run both commands (VarSets and Aliases) and confirm they open/focus the panel.
- **Multi-document behavior**
  - Create/open two documents.
  - Switch active document and confirm the panel refreshes correctly.
- **VarSets tab**
  - Filter parents/children.
  - Toggle Only Unused.
  - Remove unused variables (verify document recompute is stable).
  - Toggle Name/Label mode and verify display formatting.
- **Aliases tab**
  - Filter parents/children.
  - Toggle Only Unused.
  - Remove unused aliases.
  - Toggle Name/Label mode and verify display formatting.
- **Expression list actions**
  - Select an expression entry and confirm selection behavior (object highlight) is correct.
- **Persistence**
  - Close and reopen the panel.
  - Verify splitter state and display-mode settings persisted.

## Dependency injection for FreeCAD runtime access

Non-UI modules avoid importing `FreeCAD` / `FreeCADGui` at module import time. Instead, functions and classes that need access to the FreeCAD runtime accept an optional `ctx: FreeCadContext | None` argument.

Notes:

1. When `ctx` is omitted, the code falls back to the live FreeCAD runtime via `get_runtime_context()`.
1. In unit tests, you can pass a fake `FreeCadContext` (or `None` if the test only exercises pure logic).
1. For code that delegates through the query/mutation layer, passing `ctx` at the controller/data-source level ensures the entire call chain stays testable.

UI ports:

- `MainPanel` accepts injected ports for UI runtime boundaries:
  - `GuiPort` (FreeCADGui / UI loading and MDI integration)
  - `AppPort` (translation)
  - `SettingsPort` (persisted UI settings)

These ports default to runtime adapters, but can be replaced with fakes in unit tests.

Common patterns:

- `PanelController(ctx=...)` (threads `ctx` into both tab data sources).
- `VarsetDataSource(ctx=...)` / `SpreadsheetDataSource(ctx=...)`.
- For tests that only need to validate higher-level behavior, it is often simplest to monkeypatch query functions (e.g. `getVarsets`, `getSpreadsheetAliasReferences`) and assert that the datasource/controller produces the expected results.

Common commands:

- `task test`
- `uv run pytest`

TBD:

- Whether to add a dedicated “in-FreeCAD smoke test checklist” section (manual steps) per release.

## Documentation

To build the documentation, run `task docs:build`.

To serve the documentation, run `task docs:serve`. The Ctrl+C to stop the server.

To do both at the same time, run `task docs`.

### Warnings

When running `task docs`, you will see some INFO messages from MERMAID2 and a warning about an unrecognized relative link 'reference/DataManager/'. These are expected and can be ignored:

- **MERMAID2 INFO messages**
  - These are emitted by the `mermaid2` MkDocs plugin when it initializes.
  - They typically indicate which Mermaid JavaScript bundle is being used and that it detected the Mermaid superfences configuration.
- **Unrecognized relative link warning**
  - The API reference pages under `docs/reference/` are generated during the MkDocs build by `docs/gen_ref_pages.py`.
  - MkDocs validates links against the set of source documentation files before generation is complete, so links into the generated API reference can be reported as “unrecognized” even though they work in the final built site.

```bash
task docs                             Python 3.12.12 [freecad-workbench-datamanager] royw@roy-manjaro
COMMIT Generating test documentation...
ℹ️  Test documentation unchanged: /home/royw/src/FreeCAD_Workbench_DataManager/docs/tests.md
   Total tests documented: 36
DOCS Building documentation...
INFO    -  MERMAID2  - Initialization arguments: {}
INFO    -  MERMAID2  - Using javascript library (10.4.0):
              https://unpkg.com/mermaid@10.4.0/dist/mermaid.esm.min.mjs
INFO    -  Cleaning site directory
INFO    -  Building documentation to directory: /home/royw/src/FreeCAD_Workbench_DataManager/site
INFO    -  Doc file 'index.md' contains an unrecognized relative link 'reference/DataManager/', it was left as is. Did you mean
           'reference/DataManager/index.md'?
INFO    -  MERMAID2  - Found superfences config: {'custom_fences': [{'name': 'mermaid', 'class': 'mermaid', 'format': <function fence_code_format at
           0x7f4db7e2a3e0>}]}
INFO    -  Documentation built in 1.45 seconds
PASS Documentation built successfully in site/
SERVER Starting documentation server...
INFO    -  Building documentation...
INFO    -  MERMAID2  - Initialization arguments: {}
INFO    -  MERMAID2  - Using javascript library (10.4.0):
              https://unpkg.com/mermaid@10.4.0/dist/mermaid.esm.min.mjs
INFO    -  Cleaning site directory
INFO    -  Doc file 'index.md' contains an unrecognized relative link 'reference/DataManager/', it was left as is. Did you mean
           'reference/DataManager/index.md'?
INFO    -  MERMAID2  - Found superfences config: {'custom_fences': [{'name': 'mermaid', 'class': 'mermaid', 'format': <function fence_code_format at
           0x7fdccc04c540>}]}
INFO    -  Documentation built in 1.33 seconds
INFO    -  [11:30:12] Serving on http://127.0.0.1:8000/freecad_datamanager_workbench/
```

## Packaging and distribution (FreeCAD Addon)

This workbench is intended to be installed via the FreeCAD Addon ecosystem.

While the workbench can be packaged and distributed via PyPI (there are tasks for this), it is not recommended. Instead the workbench is intended to be installed via the FreeCAD Addon Manager which runs the workbench from the source tree.

Notes:

- The Addon install mechanism typically places the repository (or a ZIP snapshot) under the user `Mod/` directory.
- Because of this, relative paths and packaged resources must work directly from the source tree.
- UI/resources live under `freecad/DataManager/resources/`.

TBD:

- Exact Addon Manager metadata requirements (for example which fields/files are required for listing).
- Whether releases will be Git tags, GitHub releases, or both.

## Publishing to FreeCAD Addon Manager

The FreeCAD Addon Manager catalog is maintained in:

- [FreeCAD/FreeCAD-addons](https://github.com/FreeCAD/FreeCAD-addons/)

This repository is not the catalog itself. To publish/update the workbench in Addon Manager, you submit a pull request to the FreeCAD-addons repository.

### Workflow

1. Clone the addon catalog repository.
1. Add this workbench as a git submodule.
1. Ensure the submodule entry is inserted in sorted order in `.gitmodules`.
1. Add the workbench entry to `AddonCatalog.json` (also in sorted order).
1. Open a pull request.

### Submodule entry (`.gitmodules`)

Add an entry like this (sorted among existing submodules):

```ini
[submodule "DataManager"]
    path = DataManager
    url = https://github.com/royw/freecad_datamanager_workbench
    branch = master
```

In practice you typically create it via:

```sh
git submodule add -b master https://github.com/royw/freecad_datamanager_workbench DataManager
```

### Addon catalog entry (`AddonCatalog.json`)

Add an entry like this (sorted among existing addons):

```json
{
  "DataManager": [
    {
      "repository": "https://github.com/royw/freecad_datamanager_workbench",
      "git_ref": "master",
      "branch_display_name": "master",
      "zip_url": "https://github.com/royw/freecad_datamanager_workbench/archive/refs/heads/master.zip"
    }
  ]
}
```

## Versioning and release process

The project version is defined in `pyproject.toml` and is the single source of truth.

Suggested release checklist (TBD):

1. Update `pyproject.toml` version.
1. Update `CHANGELOG.md`.
1. Run `task check`.
1. Verify a clean install via Addon Manager or a ZIP install into `Mod/`.
1. Tag the release in git (TBD: tag format).
1. Publish/update Addon listing (TBD: process and where the listing lives).

## Debugging and logging

Logging is typically visible in FreeCAD’s Report View.

Tips:

- Use `App.Console.PrintMessage(...)` for lightweight logging.
- For UI issues, verify the `.ui` file loads correctly and required widgets are found (missing widget names will raise at runtime).
- When debugging selection behavior, confirm whether you’re working with `Object.Name` (internal) or `Object.Label` (user-facing).

TBD:

- Whether to add a debug flag / verbose mode toggle for more detailed logging.

## Contributing

Style and quality gates are enforced by the repo tasks.

Expectations:

- Keep `task check` passing.
- Prefer small, focused changes.
- Avoid adding FreeCAD-specific behavior deep inside generic helpers when it can be isolated.

TBD:

- Contribution workflow (issues/PRs, branching strategy).
- Coding conventions that are specific to this workbench beyond the linters.

## Features

### How VarSets are discovered

The workbench discovers VarSets by scanning the active document (`App.ActiveDocument`) and selecting objects with `TypeId == "App::VarSet"`.

Implementation:

- `freecad/DataManager/varsets/varset_query.py:getVarsets`
- `freecad/DataManager/freecad_helpers.py:iter_document_objects`

### How variables are discovered

Variables are discovered from each selected VarSet’s properties.

Implementation:

- `freecad/DataManager/varsets/varset_query.py:getVarsetVariableNames`

Details:

- Variables are derived from the VarSet’s `PropertiesList`.
- A set of built-in/non-variable properties are excluded (for example `Label`, `Placement`, `ExpressionEngine`, etc.).
- The result is a sorted list of variable names.

### How expressions are discovered

Expressions are discovered by scanning every document object’s `ExpressionEngine` entries.

Implementation:

- `freecad/DataManager/freecad_helpers.py:iter_named_expression_engine_entries`

Details:

- The workbench iterates `doc.Objects` and reads each object’s `ExpressionEngine` iterable.
- Each entry is expected to be sequence-like (`(lhs, rhs, ...)`), where `lhs` is a property (like `"Length"` or `".Constraints.Constraint1"`) and `rhs` is the expression text.
- Expression rows are keyed as `ObjectName.Property` using `freecad/DataManager/freecad_helpers.py:build_expression_key`.

### How aliases are discovered

Aliases are spreadsheet cell aliases.

Implementation:

- `freecad/DataManager/spreadsheets/spreadsheet_query.py:getAliases`

Details:

- Aliases are discovered from a selected `Spreadsheet::Sheet` using multiple fallbacks (for example `getAliases()`, `Aliases`/`Alias` properties, `getAlias(cell)` scans).
- The workbench normalizes the alias map so it ends up as `alias_name -> cell` regardless of the FreeCAD API variant.

### How spreadsheets are discovered

The workbench discovers spreadsheets by scanning the active document and selecting objects with `TypeId == "Spreadsheet::Sheet"`.

Implementation:

- `freecad/DataManager/spreadsheets/spreadsheet_query.py:getSpreadsheets`

### How alias references are discovered

Alias references are discovered in two places:

- Expression engine entries across the document (same mechanism as VarSets).
- Direct spreadsheet cell contents (to detect aliases referenced within spreadsheets).

Implementation:

- `freecad/DataManager/spreadsheets/spreadsheet_query.py:getAliasReferences`

Details:

- Expression engine matching looks for patterns like `<<SpreadsheetLabelOrName>>.AliasName` and `SpreadsheetLabelOrName.AliasName`.
- To handle internal spreadsheet usage, the workbench also scans non-empty cell contents and uses a word-boundary-style regex to detect the alias token.

### Filtering (glob vs substring)

Parent and child filters in the UI use glob matching. If you type no glob characters, the filter is treated as a substring match by implicitly wrapping your input in `*`.

Implementation:

- `freecad/DataManager/domain/tab_controller.py:_normalize_glob_pattern`
- `freecad/DataManager/domain/tab_controller.py:get_filtered_parents`
- `freecad/DataManager/domain/tab_controller.py:get_filtered_child_items`

### Name normalization

The workbench does not perform global name normalization (it does not lower-case object names, trim whitespace, etc.).

In FreeCAD:

- `Object.Name` is an internal identifier and is generally already normalized by FreeCAD.
- `Object.Label` is user-facing and may contain spaces and mixed case.

This matters most for aliases: the Aliases tab may use either spreadsheet `Label` or `Name` when building match patterns.

### Copy-on-change (`CopyOnChangeGroup`)

When you create Links to objects that reference a VarSet or Spreadsheet, FreeCAD may create hidden *copy-on-change* groups (typically named or labeled `CopyOnChangeGroup*`) and generate copied objects (for example `VarSet001`, `Spreadsheet001`, etc.). These are internal implementation details used to make linked objects independent.

The workbench’s “exclude copy-on-change” filters are implemented by:

- Finding copy-on-change groups by:
  - Looking for an object literally named `CopyOnChangeGroup`, and
  - Scanning for any object with `Label` that starts with `CopyOnChangeGroup`.
- Walking each such group’s children via `Group` and `OutList`.
- Collecting the `Name` of any objects of the relevant `TypeId` encountered.

Implementation:

- `freecad/DataManager/freecad_helpers.py:get_copy_on_change_groups`
- `freecad/DataManager/freecad_helpers.py:get_copy_on_change_names`

#### VarSets and copy-on-change

In the DataManager UI, the option **"Exclude CopyOnChanged varsets"** filters out VarSets discovered under `CopyOnChangeGroup*` so the VarSets list focuses on the “real” VarSets you created.

To test:

1. Create an object that uses a VarSet.
1. Create a Link to that object.
1. Open the DataManager panel.
1. Toggle **"Exclude CopyOnChanged varsets"** and confirm that the copied VarSets disappear from the VarSets list.

#### Spreadsheets and copy-on-change

The same mechanism applies to spreadsheets.

To test:

1. Create an object that uses a Spreadsheet.
1. Create a Link to that object.
1. Open the DataManager panel.
1. Toggle **"Exclude CopyOnChanged spreadsheets"** and confirm that copied spreadsheets disappear from the list.

### UI

#### Auto-expanding tree items

The workbench does not currently force-expand the FreeCAD model tree.

If you want tree items to auto-expand when selecting objects in the 3D view, this is a FreeCAD preference:

- `Edit` -> `Preferences` -> `General` -> `Selection` -> `Tree Selection Behavior` -> `Auto expand tree item when the corresponding object is selected in the 3D view`

#### Persisting UI state

The UI state is persisted through `SettingsPort`.

Implementation:

- `freecad/DataManager/ports/settings_port.py` (`SettingsPort`, `QtSettingsAdapter`)
- `freecad/DataManager/ui/main_panel.py` (uses injected `SettingsPort`)

Persisted keys:

- `varsets/object_display_mode` (`name` or `label`)
- `aliases/object_display_mode` (`name` or `label`)
- `varsets/splitter_state`
- `aliases/splitter_state`

## Development Notes

### Qt version (FreeCAD)

FreeCAD is transitioning from Qt5 to Qt6, with the 1.1 release planned to make Qt6 the default.

### Tested On

```text
OS: Manjaro Linux (KDE/plasma/wayland)
Architecture: x86_64
Version: 1.2.0dev.20260106 (Git shallow) AppImage
Build date: 2026/01/06 15:36:19
Build type: Release
Branch: (HEAD detached at 9b64da8)
Hash: 9b64da827a112d88a025be26316e3d023ff491dc
Python 3.11.14, Qt 6.8.3, Coin 4.0.3, Vtk 9.3.1, boost 1_86, Eigen3 3.4.0, PySide 6.8.3
shiboken 6.8.3, xerces-c 3.3.0, IfcOpenShell 0.8.2, OCC 7.8.1
Locale: English/United States (en_US)
Navigation Style/Orbit Style/Rotation Mode: CAD/Rounded Arcball/Window center
Stylesheet/Theme/QtStyle: FreeCAD.qss/FreeCAD Dark/
Logical DPI/Physical DPI/Pixel Ratio: 96/40.64/1.5
Installed mods:
  * DataManager
  * OpenTheme 2025.5.20
```

```text
OS: macOS 26.0.1
Architecture: arm64
Version: 1.0.2.39319 (Git) Conda
Build type: Release
Branch: (HEAD detached at 1.0.2)
Hash: 256fc7eff3379911ab5daf88e10182c509aa8052
Python 3.11.13, Qt 5.15.15, Coin 4.0.3, Vtk 9.3.0, OCC 7.8.1
Locale: C/Default (C)
Stylesheet/Theme/QtStyle: FreeCAD Dark.qss/FreeCAD Dark/Fusion
Installed mods:
  * DataManager
```
