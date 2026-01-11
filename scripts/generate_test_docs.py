#!/usr/bin/env python3
"""Generate test documentation from test docstrings.

This script extracts test information from test files and generates a markdown
table for documentation purposes.
"""

import ast
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import NamedTuple


class TestInfo(NamedTuple):
    """Information about a test method."""

    class_name: str
    method_name: str
    docstring: str
    file_path: str


def extract_tests_from_file(file_path: Path) -> list[TestInfo]:
    """Extract test information from a Python test file.

    Args:
        file_path: Path to the test file

    Returns:
        List of TestInfo objects
    """
    tests = []

    try:
        with open(file_path, encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(file_path))
    except Exception as e:
        print(f"Warning: Could not parse {file_path}: {e}")
        return tests

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            class_name = node.name
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name.startswith("test_"):
                    docstring = ast.get_docstring(item) or "No description provided."
                    # Clean up docstring - take first line only
                    docstring = docstring.split("\n")[0].strip()
                    tests.append(
                        TestInfo(
                            class_name=class_name,
                            method_name=item.name,
                            docstring=docstring,
                            file_path=str(file_path.relative_to(Path.cwd())),
                        )
                    )

    return tests


def generate_markdown_table(tests: list[TestInfo], title: str) -> str:
    """Generate a markdown table from test information.

    Args:
        tests: List of TestInfo objects
        title: Section title

    Returns:
        Markdown formatted string
    """
    if not tests:
        return ""

    lines = [f"## {title}\n"]
    lines.append("| Test Class | Test Name | Description |")
    lines.append("|------------|-----------|-------------|")

    for test in sorted(tests, key=lambda t: (t.class_name, t.method_name)):
        # Escape special markdown characters in docstrings
        description = test.docstring.replace("|", "\\|")
        # Escape underscores that start words (e.g., _get_sourcing_instructions)
        description = re.sub(r'\b_', r'\\_', description)
        lines.append(f"| {test.class_name} | `{test.method_name}` | {description} |")

    lines.append("")  # Empty line after table
    return "\n".join(lines)


def extract_table_content(content: str) -> str:
    """Extract just the table content, excluding timestamp metadata.

    Args:
        content: Full markdown content

    Returns:
        Content without timestamp lines
    """
    lines = content.split("\n")
    # Skip lines that contain timestamp
    filtered_lines = [
        line for line in lines if not line.startswith("> **Auto-generated**")
    ]
    return "\n".join(filtered_lines)


def main() -> None:
    """Main entry point for test documentation generation."""
    project_root = Path.cwd()
    tests_dir = project_root / "tests"
    output_file = project_root / "docs" / "tests.md"

    # Ensure docs directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Collect all test files
    test_files = {
        "E2E Tests": list((tests_dir / "e2e").glob("test_*.py")),
        "Unit Tests": list((tests_dir / "unit").glob("test_*.py")),
    }

    # Extract test information
    all_tests = {}
    total_count = 0

    for category, files in test_files.items():
        category_tests = []
        for file_path in sorted(files):
            category_tests.extend(extract_tests_from_file(file_path))
        all_tests[category] = category_tests
        total_count += len(category_tests)

    # Generate markdown content
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content = [
        "# Test Documentation\n",
        f"> **Auto-generated** on {timestamp}",
        f"> **Total Tests**: {total_count}\n",
        "This page provides a comprehensive overview of all tests in the project, "
        "automatically extracted from test docstrings.\n",
    ]

    # Add tables for each category
    for category, tests in all_tests.items():
        if tests:
            content.append(generate_markdown_table(tests, category))

    new_content = "\n".join(content)

    # Check if file exists and compare content (excluding timestamp)
    if output_file.exists():
        existing_content = output_file.read_text(encoding="utf-8")
        existing_tables = extract_table_content(existing_content)
        new_tables = extract_table_content(new_content)

        if existing_tables == new_tables:
            # Tables haven't changed, don't update file
            print(f"ℹ️  Test documentation unchanged: {output_file}")
            print(f"   Total tests documented: {total_count}")
            return

    # Write to file (either new file or content has changed)
    output_file.write_text(new_content, encoding="utf-8")
    print(f"✅ Generated test documentation: {output_file}")
    print(f"   Total tests documented: {total_count}")


if __name__ == "__main__":
    main()
