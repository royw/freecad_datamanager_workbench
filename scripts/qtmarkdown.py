#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileNotice: Part of the DataManager addon.

import argparse
import sys
from pathlib import Path

# Prefer PySide6, but allow running under older FreeCAD/Qt bundles (PySide2/PySide).
# This script is intended as a quick way to validate that our Markdown renders in a
# Qt QTextBrowser similarly to how the FreeCAD Addon Manager will display it.
try:
    from PySide6 import QtCore, QtGui, QtWidgets  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    try:
        from PySide2 import QtCore, QtGui, QtWidgets  # type: ignore
    except ModuleNotFoundError:  # pragma: no cover
        from PySide import QtCore, QtGui, QtWidgets  # type: ignore


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="qtmarkdown",
        description="Render a Markdown file using Qt QTextBrowser (for FreeCAD Addon Manager compatibility checks).",
    )
    parser.add_argument("markdown_path", help="Path to the markdown file to render")
    parser.add_argument(
        "--title",
        default=None,
        help="Optional window title (defaults to file name)",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=900,
        help="Initial window width in pixels",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=700,
        help="Initial window height in pixels",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = _parse_args(argv)

    # Reuse an existing QApplication if we are launched from an embedded context.
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)

    browser = QtWidgets.QTextBrowser()
    browser.setOpenExternalLinks(False)
    browser.setReadOnly(True)

    # Base URL used to resolve relative Markdown links (e.g. "./Usage/User-Guide.md").
    base_url: QtCore.QUrl | None = None

    def load_markdown(path: Path) -> None:
        nonlocal base_url

        if not path.exists() or not path.is_file():
            raise FileNotFoundError(path)

        text = path.read_text(encoding="utf-8")
        base_dir = path.parent

        # QTextBrowser resolves relative links against the document base URL.
        base_url = QtCore.QUrl.fromLocalFile(str(base_dir) + "/")
        browser.document().setBaseUrl(base_url)

        try:
            # Qt6 provides Markdown rendering; older Qt versions may not.
            browser.setMarkdown(text)
        except (AttributeError, TypeError):
            # Fallback: show the raw Markdown (still useful for link navigation testing).
            browser.setPlainText(text)

        browser.setWindowTitle(args.title or path.name)

    def on_anchor_clicked(url: QtCore.QUrl) -> None:
        # QTextBrowser emits the clicked URL exactly as written in the document.
        # Resolve relative URLs against our current base directory.
        if base_url is None:
            resolved = url
        else:
            resolved = base_url.resolved(url)

        if resolved.isLocalFile():
            path = Path(resolved.toLocalFile())
            if path.suffix.lower() in {".md", ".markdown"}:
                # Navigate within local markdown files in-place.
                load_markdown(path)
                return

        # For everything else (web URLs, PDFs, images, etc.), delegate to the OS.
        QtGui.QDesktopServices.openUrl(resolved)

    browser.anchorClicked.connect(on_anchor_clicked)

    md_path = Path(args.markdown_path).expanduser().resolve()
    try:
        load_markdown(md_path)
    except FileNotFoundError:
        print(f"error: not a file: {md_path}", file=sys.stderr)
        return 2

    browser.resize(args.width, args.height)

    browser.show()
    return int(app.exec())


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
