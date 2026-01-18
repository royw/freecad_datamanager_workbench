# DataManager FreeCAD Workbench

Manages FreeCAD VarSets and aliases.

Full Documentation: [royw.github.io/freecad_datamanager_workbench](https://royw.github.io/freecad_datamanager_workbench/)

Special thanks to OldBeard for his testing of the beta workbench and many great suggestions!

## Suggestion FreeCAD Preferences

Enable: 

- General --> Selection --> Tree 
- Selection Behavior --> Auto expand tree item when the corresponding object is selected in the 3D view.

## Usage

The workbench appears in the FreeCAD workbench selector as **Data Manager**.

### Annotated UI

<br/>
<img width = '400' src = '../Media/datamanager_wb_annotated.png' alt="DataManager workbench annotated UI"/>

Annotated UI legend:

1. Workbench selection (workbench selector, Data Manager menu, and toolbar icons)
1. VarSets and Aliases tabs
1. Available VarSets
1. VarSets filter
1. Exclude CopyOnChanged varsets checkbox
1. Variables list
1. Only Unused checkbox
1. Remove Selected Unused Variables button
1. Splitter (resizable pane divider)
1. Expressions list
1. Show Objects as: Name/Label radio buttons
1. Copy Selection Buttons
1. Shows selected expression selects object in model view

#### VarSets tab

- **VarSets list** (3)

  - Select one or more VarSets to populate the Variables list.
  - If a VarSet contains variables in multiple groups, the list may also include virtual entries like
    `VarSetName.GroupName`. Selecting a virtual entry filters the Variables list to that group.

- **VarSets filter** (4)

  - Filters VarSets by name using a glob match.
  - If you type no glob characters, the filter is treated as a substring match.

- **Exclude CopyOnChanged varsets** (5)

  - When you create Links to objects referencing a VarSet, FreeCAD may create hidden *copy-on-change* groups (typically `CopyOnChangeGroup*`) and generate copied VarSets (e.g. `VarSet001`).
  - Enabling this option hides those generated copies so the list focuses on the VarSets you created.

- **Variables filter**

  - Filters variables by variable name using a glob match.
  - The match is against the variable name only (not the `VarSetName.` prefix).

- **Only Unused** (7)

  - Shows only variables that have **no** expression references.

- **Remove Selected Unused Variables** (8)

  - Removes the selected unused variables from the VarSet.

- **Expressions list** (10)

  - Shows the expressions that reference each variable.
  - Clicking an expression selects the Object in the Model tree.
  - The list is resizable using a splitter (9).
  - Use the **Show Objects as: Name/Label** radio buttons (11) to control whether expression list entries display
    the FreeCAD object internal name or its label. The choice is persisted.

- **Copy Selected** (12)

  - Each list pane includes a Copy Selected button.
  - Clicking it copies the selected list items to the clipboard (one item per line).
  - You can also right-click a list to use **Copy** (and **Select All** where applicable).

- **Select object in model tree from expression** (13)

  - Clicking an expression entry attempts to select the referenced object in the FreeCAD model tree.

### Aliases tab

- The Aliases tab mirrors the VarSets layout and is resizable using a splitter.
- Alias definition rows are displayed using `:=` to distinguish definition from a normal expression (for example:
  `Spreadsheet.A1 := 'MyAlias`).
- The **Show Objects as: Name/Label** setting is independent from the VarSets tab and is persisted.

### Multiple open documents

If you have multiple FreeCAD documents open, the panel follows the currently active document in the model view and
refreshes the lists when you switch documents.
