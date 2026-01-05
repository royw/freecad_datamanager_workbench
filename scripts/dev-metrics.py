#!/usr/bin/env python3
"""Project Metrics Summary Script.

Provides a concise overview of project statistics including:
- Source code metrics (files, SLOC, complexity)
- Test code metrics (coverage, test counts)
- Code quality metrics (duplication, risk analysis)

Architecture:
1. Data gathering phase - collect all metrics into data structures
2. Report generation phase - format and display results
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
import json
from pathlib import Path
import re
import subprocess
import sys
from textwrap import dedent
import tomllib
from typing import Any

from custom_argparse import CustomArgumentParser as ArgumentParser


# ANSI color codes
class Colors:
    """ANSI color codes for terminal output."""

    BOLD = "\033[1m"
    CYAN = "\033[0;36m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[0;33m"
    RED = "\033[0;31m"
    NC = "\033[0m"  # No Color


@dataclass
class MetricsConfig:
    """Configuration for metrics script."""

    src_paths: list[Path] = field(default_factory=list)  # [Path("src")]
    tests_paths: list[Path] = field(default_factory=list)  # [Path("tests")]
    radon_list: list[str] = field(default_factory=list)  # ["radon"]
    pylint_list: list[str] = field(default_factory=list)  # ["pylint"]
    pytest_list: list[str] = field(default_factory=list)  # ["pytest"]
    test_pattern: str = "test_*.py"
    test_types: list[str] = field(default_factory=list)  # List of subdirectory filters (e.g., "unit", "functional")
    package: str = ""  # Top-level package name (auto-detected if empty)
    excluded_files: list[str] = field(default_factory=list)  # List of files to exclude from untested files report


@dataclass
class SourceMetrics:
    """Source code metrics."""

    total_files: int = 0
    max_lines: int = 0
    avg_lines: int = 0
    total_sloc: int = 0
    avg_code_paths: float = 0.0
    max_code_paths: int = 0
    duplication_score: str = "N/A"
    top_imports: list[tuple[str, int]] = field(default_factory=list)
    complexity_exclusions: list[str] = field(default_factory=list)


@dataclass
class TestMetrics:
    """Test code metrics."""

    total_test_files: int = 0
    total_sloc: int = 0
    unit_tests: int = 0
    functional_tests: int = 0
    integration_tests: int = 0
    e2e_tests: int = 0
    regression_tests: int = 0
    untested_files: list[tuple[str, int]] = field(default_factory=list)


@dataclass
class ComplexityMetrics:
    """Complexity metrics."""

    top5_complex: list[tuple[str, int]] = field(default_factory=list)
    total_paths: int = 0
    avg_paths: float = 0.0
    max_paths: int = 0
    files_high_cc: int = 0
    all_complexities: dict[str, int] = field(default_factory=dict)


@dataclass
class CoverageMetrics:
    """Coverage metrics."""

    overall_coverage: str = "N/A"
    coverage_distribution: dict[str, int] = field(default_factory=dict)
    coverage_sloc_distribution: dict[str, int] = field(default_factory=dict)
    test_results: str = ""


@dataclass
class RiskMetrics:
    """Risk analysis metrics."""

    high_risk_files: list[tuple[str, int, float, float, int]] = field(default_factory=list)


@dataclass
class ProjectMetrics:
    """Complete project metrics."""

    source: SourceMetrics = field(default_factory=SourceMetrics)
    tests: TestMetrics = field(default_factory=TestMetrics)
    complexity: ComplexityMetrics = field(default_factory=ComplexityMetrics)
    coverage: CoverageMetrics = field(default_factory=CoverageMetrics)
    risk: RiskMetrics = field(default_factory=RiskMetrics)


def output(message: str) -> None:
    print(message)  # noqa: T201


def error(message: str, exception: Exception | None = None) -> None:
    print(f"{Colors.RED}{message}{Colors.NC}")  # noqa: T201
    if exception:
        print(f"{Colors.RED}{exception}{Colors.NC}")  # noqa: T201


def run_command(cmd: list[str], message: str = "") -> subprocess.CompletedProcess[str]:
    """Run a shell command and return the result."""
    if message:
        output(f"{Colors.CYAN}{message}{Colors.NC}")
    else:
        output(f"Running: {' '.join(cmd)}...")
    return subprocess.run(cmd, capture_output=True, text=True, check=False)  # noqa: S603


# ============================================================================
# METRICS GATHERING
# ============================================================================


def detect_package_name(src_paths: list[Path]) -> str:
    """Auto-detect package name from src directory or pyproject.toml.

    Strategy:
    1. If exactly one package directory (containing __init__.py) exists in src_path, use it
    2. Otherwise, use snake_case of project.name from pyproject.toml
    3. Fallback to "appimage_updater"
    """
    # Look for package directories (containing __init__.py) in src_path
    packages = []
    for src_path in src_paths:
        if src_path.exists():
            packages.extend([d.name for d in src_path.iterdir() if d.is_dir() and (d / "__init__.py").exists()])

    # If exactly one package, use it
    if len(packages) == 1:
        return packages[0]

    # Otherwise, use snake_case of project name from pyproject.toml
    try:
        with open("pyproject.toml", "rb") as f:
            data = tomllib.load(f)
            project_name: str = data.get("project", {}).get("name", "")
            # Convert to snake_case
            return project_name.replace("-", "_")
    except Exception as ex:
        error("unable to detect project name from pyproject.toml", ex)
    return "unknown_project"  # fallback


def load_complexity_exclusions() -> list[str]:
    """Load complexity exclusion list from pyproject.toml."""
    try:
        with open("pyproject.toml", "rb") as f:
            data = tomllib.load(f)
        project_name = data.get("project", {}).get("name")
        if not project_name:
            return []
        exclusions = data.get("tool", {}).get(project_name, {}).get("complexity", {}).get("exclude", [])
        # Ensure we return a list of strings
        if isinstance(exclusions, list):
            return [str(item) for item in exclusions]
        return []
    except Exception:
        return []


def _path_list_to_str_parts(path_list: list[Path]) -> list[str]:
    return [str(p) for p in path_list]


def _path_list_to_str(path_list: list[Path]) -> str:
    return " ".join(_path_list_to_str_parts(path_list))


def gather_complexity_metrics(config: MetricsConfig) -> ComplexityMetrics:
    """Gather complexity metrics using radon."""
    metrics = ComplexityMetrics()

    try:
        result = run_command(config.radon_list + ["cc", *_path_list_to_str_parts(config.src_paths), "-a", "-j"])
        if result.returncode != 0:
            return metrics

        data = json.loads(result.stdout)

        # Calculate metrics
        file_complexities = []
        file_code_paths = []
        total_code_paths = 0

        for filepath, blocks in data.items():
            if not blocks:
                continue
            max_complexity = max(block.get("complexity", 0) for block in blocks)
            file_complexities.append((filepath, max_complexity))

            file_total = sum(block.get("complexity", 0) for block in blocks)
            file_code_paths.append(file_total)
            total_code_paths += file_total

        file_complexities.sort(key=lambda x: x[1], reverse=True)

        avg_paths_per_file = total_code_paths / len(file_code_paths) if file_code_paths else 0
        max_paths_in_file = max(file_code_paths) if file_code_paths else 0

        # Count files with complexity > 5 (grade B or worse)
        # Radon grades: A=1-5, B=6-10, C=11-20, D=21-50, E=51-100, F=100+
        files_high_cc = sum(1 for _, complexity in file_complexities if complexity > 5)

        metrics.top5_complex = file_complexities[:5]
        metrics.total_paths = total_code_paths
        metrics.avg_paths = avg_paths_per_file
        metrics.max_paths = max_paths_in_file
        metrics.files_high_cc = files_high_cc
        metrics.all_complexities = dict(file_complexities)

    except Exception as e:
        output(f"{Colors.YELLOW}Error calculating complexity: {e}{Colors.NC}")

    return metrics


def gather_source_metrics(complexity: ComplexityMetrics, config: MetricsConfig) -> SourceMetrics:
    """Gather source code metrics."""
    metrics = SourceMetrics()

    # Load complexity exclusions
    metrics.complexity_exclusions = load_complexity_exclusions()

    py_files = []
    for src_path in config.src_paths:
        py_files.extend(list(src_path.rglob("*.py")))
    metrics.total_files = len(py_files)

    # Lines per file statistics
    line_counts = [len(f.read_text().splitlines()) for f in py_files]
    metrics.max_lines = max(line_counts) if line_counts else 0
    metrics.avg_lines = sum(line_counts) // len(line_counts) if line_counts else 0

    # SLOC calculation
    for f in py_files:
        lines = f.read_text().splitlines()
        metrics.total_sloc += sum(1 for line in lines if line.strip() and not line.strip().startswith("#"))

    # Code paths from complexity
    metrics.avg_code_paths = complexity.avg_paths
    metrics.max_code_paths = complexity.max_paths

    # Duplication score
    # noinspection PyBroadException
    try:
        result = run_command(
            config.pylint_list
            + ["--disable=all", "--enable=duplicate-code", *_path_list_to_str_parts(config.src_paths)]
        )
        for line in result.stdout.split("\n"):
            if "Your code has been rated at" in line:
                metrics.duplication_score = line.split("Your code has been rated at")[1].split("/")[0].strip() + "/10"
                break
    except Exception as e:
        # Duplication score is optional, continue without it
        output(f"{Colors.YELLOW}Could not calculate duplication score: {e}{Colors.NC}")

    # Top imports
    import_counts = []
    for f in py_files:
        content = f.read_text()
        count = sum(1 for line in content.splitlines() if line.startswith(("import ", "from ")))
        import_counts.append((str(f), count))
    import_counts.sort(key=lambda x: x[1], reverse=True)
    metrics.top_imports = import_counts[:5]

    return metrics


def gather_test_metrics(config: MetricsConfig, sloc_map: dict[str, int] | None = None) -> TestMetrics:
    """Gather test code metrics."""
    metrics = TestMetrics()

    # tests_path can be space-separated list of paths
    tests_files: list[Path] = []
    for tests_path in config.tests_paths:
        # Apply test_type filter if specified
        for test_type in config.test_types:
            if tests_path.name == test_type:
                # If test_path already ends with the test_type, use it as-is; otherwise append
                search_path = tests_path if tests_path.name == test_type else tests_path / test_type
            else:
                search_path = tests_path

            if search_path.exists():
                # Use configured test pattern
                tests_files.extend(search_path.rglob(config.test_pattern))

    metrics.total_test_files = len(tests_files)

    # Test SLOC
    for f in tests_files:
        lines = f.read_text().splitlines()
        metrics.total_sloc += sum(1 for line in lines if line.strip() and not line.strip().startswith("#"))

    # Count test functions by type
    _count_test_functions_by_type(metrics, config)

    # Find untested files
    _find_untested_files(metrics, config, sloc_map)

    return metrics


def _get_base_test_path(config: MetricsConfig) -> Path:
    """Get the base test directory path."""
    base_test_path = config.tests_paths[0]
    if base_test_path.parent.name == "tests" or base_test_path.name != "tests":
        # We have specific subdirectories, use parent
        base_test_path = base_test_path.parent if base_test_path.parent.name == "tests" else Path("tests")
    return base_test_path


def _generate_test_type_mapping(config: MetricsConfig, base_test_path: Path) -> list[tuple[str, str]]:
    """Generate test type mapping from test paths or subdirectories."""
    test_type_mapping = []

    # If we have multiple specific test paths, use them
    if len(config.tests_paths) > 1 or (
        len(config.tests_paths) == 1 and config.tests_paths[0].name in config.test_types
    ):
        for test_path in config.tests_paths:
            test_type = test_path.name
            attr_name = f"{test_type}_tests"
            test_type_mapping.append((test_type, attr_name))
    # Otherwise, discover from base directory
    elif base_test_path.exists():
        for subdir in base_test_path.iterdir():
            if subdir.is_dir() and not subdir.name.startswith(("_", ".")):
                attr_name = f"{subdir.name}_tests"
                test_type_mapping.append((subdir.name, attr_name))

    # Fallback to common test types if no subdirectories found
    if not test_type_mapping:
        test_type_mapping = [
            ("unit", "unit_tests"),
            ("functional", "functional_tests"),
            ("integration", "integration_tests"),
            ("e2e", "e2e_tests"),
            ("regression", "regression_tests"),
        ]

    return test_type_mapping


def _get_test_function_pattern(config: MetricsConfig) -> str:
    """Extract function pattern from test_pattern (e.g., 'test_*.py' -> 'def test_')."""
    func_prefix = config.test_pattern.split("_")[0] if "_" in config.test_pattern else "test"
    return f"def {func_prefix}_"


def _count_test_functions_in_dir(test_dir: Path, test_pattern: str, func_pattern: str) -> int:
    """Count test functions in a directory."""
    count = 0
    for f in test_dir.rglob(test_pattern):
        content = f.read_text()
        count += sum(1 for line in content.splitlines() if line.strip().startswith(func_pattern))
    return count


def _count_test_functions_by_type(metrics: TestMetrics, config: MetricsConfig) -> None:
    """Count test functions by test type."""
    if not config.tests_paths:
        return

    base_test_path = _get_base_test_path(config)
    test_type_mapping = _generate_test_type_mapping(config, base_test_path)
    func_pattern = _get_test_function_pattern(config)

    # Filter test types based on config.test_types if specified
    filtered_test_paths = _filter_test_paths_by_types(config.tests_paths, config.test_types)
    filtered_test_type_names = {path.name for path in filtered_test_paths}

    for test_type, attr_name in test_type_mapping:
        # Only count if this test type is in the filtered list (or no filter applied)
        if not config.test_types or test_type in filtered_test_type_names:
            test_dir = base_test_path / test_type
            if test_dir.exists():
                count = _count_test_functions_in_dir(test_dir, config.test_pattern, func_pattern)
                setattr(metrics, attr_name, count)


def _collect_source_files_with_sloc(config: MetricsConfig, sloc_map: dict[str, int] | None = None) -> dict[str, int]:
    """Collect source files with their SLOC counts (only files with SLOC > 20)."""
    src_files_with_sloc: dict[str, int] = {}
    for src_path in config.src_paths:
        for src_file in src_path.rglob("*.py"):
            if "__pycache__" in str(src_file):
                continue
            # Use radon SLOC if available, otherwise fall back to simple counting
            sloc = _calculate_file_sloc(str(src_file), sloc_map)
            if sloc > 20:
                src_files_with_sloc[str(Path(*src_file.parts[1:]))] = sloc
    return src_files_with_sloc


def _extract_tested_modules(config: MetricsConfig) -> set[str]:
    """Extract module paths that are imported in test files."""
    tested_modules = set()
    for tests_path in config.tests_paths:
        if not tests_path.exists():
            continue
        for tests_file in tests_path.rglob(config.test_pattern):
            content = tests_file.read_text()
            # Use config.package for import matching
            imports = re.findall(rf"from {config.package}\.(\S+) import", content)
            imports += re.findall(rf"import {config.package}\.(\S+)", content)
            for imp in imports:
                module_path = imp.replace(".", "/")
                tested_modules.add(f"{config.package}/{module_path}.py")
    return tested_modules


def _filter_untested_files(
    src_files_with_sloc: dict[str, int], tested_modules: set[str], excluded_files: list[str]
) -> list[tuple[str, int]]:
    """Filter source files to find untested ones."""
    untested: list[tuple[str, int]] = []
    for source_file, sloc in src_files_with_sloc.items():
        normalized: str = str(source_file).replace("\\", "/")
        if normalized not in tested_modules and not any(x in normalized for x in excluded_files):
            untested.append((normalized, sloc))
    untested.sort(key=lambda x: x[1], reverse=True)
    return untested[:10]


def _find_untested_files(metrics: TestMetrics, config: MetricsConfig, sloc_map: dict[str, int] | None = None) -> None:
    """Find source files without corresponding tests."""
    src_files_with_sloc = _collect_source_files_with_sloc(config, sloc_map)
    tested_modules = _extract_tested_modules(config)
    metrics.untested_files = _filter_untested_files(src_files_with_sloc, tested_modules, config.excluded_files)


def _filter_test_paths_by_types(test_paths: list[Path], test_types: list[str]) -> list[Path]:
    """Build test paths by combining base paths with test type subdirectories.

    If test_types is empty, return all test_paths as-is.
    Otherwise, for each base test path, append each test type subdirectory
    that actually exists.

    Example:
        test_paths = [Path("tests")]
        test_types = ["unit", "functional"]
        Returns: [Path("tests/unit"), Path("tests/functional")]
    """
    if not test_types:
        return test_paths

    filtered_paths = []
    for base_path in test_paths:
        for test_type in test_types:
            # Combine base path with test type subdirectory
            full_path = base_path / test_type
            # Only include if the directory exists
            if full_path.exists() and full_path.is_dir():
                filtered_paths.append(full_path)

    return filtered_paths


def gather_coverage_metrics(config: MetricsConfig, sloc_map: dict[str, int] | None = None) -> CoverageMetrics:
    """Gather coverage metrics by running pytest."""
    metrics = CoverageMetrics()

    cov_list = [f"--cov={p}/{config.package}" for p in config.src_paths]

    # Filter test paths by test_types if specified
    test_paths = _filter_test_paths_by_types(config.tests_paths, config.test_types)

    result = run_command(
        [
            *config.pytest_list,
            "--timeout",
            "30",
            *_path_list_to_str_parts(test_paths),
            *cov_list,
            "--cov-report=json:coverage.json",
            "--cov-report=html:htmlcov",
            "--quiet",
            "--no-header",
            "--tb=no",
        ]
    )

    # Extract test results
    _extract_test_results(result, metrics)

    if not Path("coverage.json").exists():
        return metrics

    _parse_coverage_json(metrics, sloc_map)

    return metrics


def _extract_test_results(result: subprocess.CompletedProcess[str], metrics: CoverageMetrics) -> None:
    """Extract test results from pytest output."""
    for line in result.stdout.split("\n"):
        if "passed" in line or "failed" in line or "xfailed" in line:
            metrics.test_results = line.strip()
            break


def _parse_coverage_json(metrics: CoverageMetrics, sloc_map: dict[str, int] | None = None) -> None:
    """Parse coverage.json file for coverage metrics."""
    try:
        with open("coverage.json") as f:
            data = json.load(f)

        totals = data.get("totals", {})
        percent_covered = totals.get("percent_covered", 0)
        metrics.overall_coverage = f"{percent_covered:.1f}%"

        # Coverage distribution
        _calculate_coverage_distribution_from_json(data, metrics, sloc_map)

    except FileNotFoundError:
        output(f"{Colors.YELLOW}Error: coverage.json not found{Colors.NC}")
    except Exception as e:
        output(f"{Colors.YELLOW}Error parsing coverage: {e}{Colors.NC}")


def _calculate_coverage_distribution_from_json(
    data: dict[str, Any], metrics: CoverageMetrics, sloc_map: dict[str, int] | None = None
) -> None:
    """Calculate coverage distribution across files from JSON data."""
    ranges: dict[str, int] = defaultdict(int)
    sloc_ranges: dict[str, int] = defaultdict(int)
    files = data.get("files", {})
    for filepath, file_data in files.items():
        if "__pycache__" in filepath:
            continue

        summary = file_data.get("summary", {})
        percent_covered = summary.get("percent_covered", 0)
        coverage_pct = int(percent_covered)
        range_key = _get_coverage_range(coverage_pct)
        ranges[range_key] += 1

        # Add actual SLOC for this file to the range
        sloc = _calculate_file_sloc(filepath, sloc_map)
        sloc_ranges[range_key] += sloc

    metrics.coverage_distribution = dict(ranges)
    metrics.coverage_sloc_distribution = dict(sloc_ranges)


def _get_sloc_from_radon(config: MetricsConfig) -> dict[str, int]:
    """Get SLOC counts for all files using radon raw."""
    sloc_map = {}
    try:
        result = run_command([*config.radon_list, "raw", *_path_list_to_str_parts(config.src_paths), "--json"])
        if result.returncode == 0:
            data = json.loads(result.stdout)
            for filepath, metrics in data.items():
                # Normalize path for comparison
                normalized = filepath.replace("\\", "/")
                sloc_map[normalized] = metrics.get("sloc", 0)
    except Exception:
        pass
    return sloc_map


def _calculate_file_sloc(filepath: str, sloc_map: dict[str, int] | None = None) -> int:
    """Calculate actual SLOC for a file.

    If sloc_map is provided (from radon), use that. Otherwise fall back to simple counting.
    """
    if sloc_map:
        normalized = filepath.replace("\\", "/")
        return sloc_map.get(normalized, 0)

    # Fallback: simple counting (less accurate, includes docstrings)
    try:
        with open(filepath, encoding="utf-8") as f:
            lines = f.readlines()
        return sum(1 for line in lines if line.strip() and not line.strip().startswith("#"))
    except Exception:
        return 0


def _get_coverage_range(coverage_pct: int) -> str:
    """Get coverage range bucket for a given percentage."""
    ranges = [
        (100, "100%"),
        (90, "90-99%"),
        (80, "80-89%"),
        (70, "70-79%"),
        (60, "60-69%"),
        (50, "50-59%"),
        (40, "40-49%"),
        (30, "30-39%"),
        (20, "20-29%"),
        (10, "10-19%"),
    ]
    for threshold, label in ranges:
        if coverage_pct >= threshold:
            return label
    return "0-9%"


def gather_risk_metrics(
    complexity: ComplexityMetrics, config: MetricsConfig, sloc_map: dict[str, int] | None = None
) -> RiskMetrics:
    """Gather risk analysis metrics."""
    metrics = RiskMetrics()

    if not Path("coverage.json").exists() or not complexity.all_complexities:
        return metrics

    try:
        with open("coverage.json") as f:
            data = json.load(f)

        # Build file coverage and SLOC map from JSON
        file_coverage = {}
        file_sloc = {}
        files = data.get("files", {})
        for filepath, file_data in files.items():
            if "__pycache__" in filepath:
                continue
            summary = file_data.get("summary", {})
            percent_covered = summary.get("percent_covered", 0)
            # Calculate actual SLOC using radon data if available
            sloc = _calculate_file_sloc(filepath, sloc_map)
            # Normalize path for comparison
            normalized = filepath.replace("\\", "/")
            file_coverage[normalized] = percent_covered
            file_sloc[normalized] = sloc

        # Calculate risk scores
        ratios = []
        for filepath, comp in complexity.all_complexities.items():
            normalized = filepath.replace("\\", "/")
            # Check if path starts with any of the src_paths
            if not any(normalized.startswith(str(src_path)) for src_path in config.src_paths):
                # Try prepending each src_path with package name
                for src_path in config.src_paths:
                    candidate = f"{src_path}/{config.package}/{normalized}"
                    if candidate in file_coverage:
                        normalized = candidate
                        break

            coverage = file_coverage.get(normalized, 0)
            sloc = file_sloc.get(normalized, 0)
            risk_score = comp * (100 - coverage) / 100
            ratios.append((normalized, comp, coverage, risk_score, sloc))

        ratios.sort(key=lambda x: x[3], reverse=True)
        metrics.high_risk_files = ratios[:5]

    except Exception as e:
        output(f"{Colors.YELLOW}Error calculating risk: {e}{Colors.NC}")

    return metrics


def gather_all_metrics(config: MetricsConfig) -> ProjectMetrics:
    """Gather all project metrics using configuration."""
    metrics = ProjectMetrics()

    # Get SLOC map from radon once for all functions to use
    sloc_map = _get_sloc_from_radon(config)

    # Order matters - complexity needed for other metrics
    metrics.complexity = gather_complexity_metrics(config)
    metrics.source = gather_source_metrics(metrics.complexity, config)
    metrics.tests = gather_test_metrics(config, sloc_map)
    metrics.coverage = gather_coverage_metrics(config, sloc_map)
    metrics.risk = gather_risk_metrics(metrics.complexity, config, sloc_map)

    return metrics


# ============================================================================
# REPORT GENERATION PHASE
# ============================================================================


def output_header(text: str) -> None:
    """output a colored header."""
    output(f"\n{Colors.BOLD}{Colors.GREEN}{text}{Colors.NC}")


def output_section_header(text: str) -> None:
    """output a colored section header."""
    output(f"\n{Colors.BOLD}{Colors.CYAN}{text}{Colors.NC}\n")


def report_source_metrics(metrics: SourceMetrics) -> None:
    """Display source code metrics."""
    output_header("Source Code (src/)")
    output(f"  Total files: {metrics.total_files}")
    output(f"  Maximum lines in a file: {metrics.max_lines}")
    output(f"  Average lines per file: {metrics.avg_lines}")
    output(f"  Total SLOC: {metrics.total_sloc}")
    output(f"  Average code paths per file: {metrics.avg_code_paths:.1f}")
    output(f"  Maximum code paths in a file: {metrics.max_code_paths}")
    output(f"  Code duplication score: {metrics.duplication_score}")
    output("  Top 5 files with most imports:")
    for filepath, count in metrics.top_imports:
        output(f"    {filepath:60s} ({count} imports)")


def report_complexity_exclusions(metrics: SourceMetrics) -> None:
    """Display complexity exclusions."""
    if not metrics.complexity_exclusions:
        return

    output_header("Functions Excluded from Complexity Checks")
    output(f"  Total excluded: {len(metrics.complexity_exclusions)}")
    output("  Excluded functions (legitimate domain complexity):")
    for func in metrics.complexity_exclusions:
        output(f"    - {func}")


def report_test_metrics(metrics: TestMetrics) -> None:
    """Display test code metrics."""
    output_header("Test Code (tests/)")
    output(f"  Total test files: {metrics.total_test_files}")
    output(f"  Total SLOC: {metrics.total_sloc}")
    output("  Test breakdown:")
    # Only show test types that have counts > 0
    if metrics.unit_tests > 0:
        output(f"    Unit: {metrics.unit_tests}")
    if metrics.functional_tests > 0:
        output(f"    Functional: {metrics.functional_tests}")
    if metrics.integration_tests > 0:
        output(f"    Integration: {metrics.integration_tests}")
    if metrics.e2e_tests > 0:
        output(f"    E2E: {metrics.e2e_tests}")
    if metrics.regression_tests > 0:
        output(f"    Regression: {metrics.regression_tests}")
    output("  Source files (SLOC > 20) without tests:")
    if metrics.untested_files:
        for filepath, sloc in metrics.untested_files:
            output(f"    {filepath:60s} (SLOC: {sloc})")
    else:
        output("    None - all significant files have tests!")


def report_risk_metrics(metrics: RiskMetrics) -> None:
    """Display risk analysis metrics."""
    output("  Top 5 highest risk files (high complexity + low coverage):")
    if metrics.high_risk_files:
        for filepath, complexity, coverage, risk_score, sloc in metrics.high_risk_files:
            output(
                f"    {filepath:60s} "
                f"(complexity: {complexity}, coverage: {coverage:.1f}%, risk: {risk_score:.1f}, SLOC: {sloc})"
            )
    else:
        output(f"    {Colors.YELLOW}N/A (requires coverage.xml and radon){Colors.NC}")


def report_complexity_metrics(metrics: ComplexityMetrics) -> None:
    """Display cyclomatic complexity metrics."""
    output_header("Cyclomatic Complexity")
    if metrics.top5_complex:
        output("  Top 5 most complex files:")
        for filepath, max_cc in metrics.top5_complex:
            output(f"    {filepath:60s} (max: {max_cc})")
        output(f"  Files with complexity > 5: {metrics.files_high_cc}")
        output(f"  Total code paths: {metrics.total_paths}")
    else:
        output(f"  {Colors.YELLOW}radon not installed - skipping complexity analysis{Colors.NC}")


def report_coverage_metrics(metrics: CoverageMetrics) -> None:
    """Display code coverage metrics."""
    output_header("Code Coverage")
    if metrics.test_results:
        output(f"  {metrics.test_results}")
    output(f"  Overall coverage: {metrics.overall_coverage}")

    if metrics.coverage_distribution:
        output("  Coverage distribution:")
        order = [
            "100%",
            "90-99%",
            "80-89%",
            "70-79%",
            "60-69%",
            "50-59%",
            "40-49%",
            "30-39%",
            "20-29%",
            "10-19%",
            "0-9%",
        ]
        for range_key in order:
            if range_key in metrics.coverage_distribution:
                count = metrics.coverage_distribution[range_key]
                sloc = metrics.coverage_sloc_distribution.get(range_key, 0)
                output(f"    {range_key:8s}: {count:3d} files, {sloc:5d} SLOC")


def report_summary(metrics: ProjectMetrics) -> None:
    """Display summary statistics."""
    output_section_header("=== Summary ===")

    total_tests = (
        metrics.tests.unit_tests
        + metrics.tests.functional_tests
        + metrics.tests.integration_tests
        + metrics.tests.e2e_tests
        + metrics.tests.regression_tests
    )

    output(
        f"  Source files: {metrics.source.total_files} | "
        f"Test files: {metrics.tests.total_test_files} | "
        f"Tests: {total_tests}"
    )

    if metrics.complexity.total_paths:
        test_path_ratio = total_tests / metrics.complexity.total_paths
        output(f"  Code paths: {metrics.complexity.total_paths}")
        output(
            f"  Test/Path ratio: {test_path_ratio:.2f} "
            f"({total_tests} tests / {metrics.complexity.total_paths} code paths)"
        )

    if metrics.coverage.overall_coverage != "N/A":
        output(f"  Coverage: {metrics.coverage.overall_coverage}")

    output("")


def generate_report(metrics: ProjectMetrics) -> None:
    """Generate and display the complete metrics report."""
    output_section_header("=== Project Metrics Summary ===")

    report_source_metrics(metrics.source)
    report_complexity_exclusions(metrics.source)
    report_test_metrics(metrics.tests)
    report_risk_metrics(metrics.risk)
    report_complexity_metrics(metrics.complexity)
    report_coverage_metrics(metrics.coverage)
    report_summary(metrics)


# ============================================================================
# MAIN
# ============================================================================


def load_config_from_pyproject() -> dict[str, str | list[str]]:
    """Load dev-metrics configuration from pyproject.toml."""
    try:
        with open("pyproject.toml", "rb") as f:
            data: dict[str, str | list[str]] = tomllib.load(f).get("tool", {}).get("dev-metrics", {})
            return data
    except FileNotFoundError:
        return {}


def save_config_to_pyproject(config: MetricsConfig) -> None:
    """Save resolved configuration to pyproject.toml [tool.dev-metrics] section.

    Creates or replaces the [tool.dev-metrics] section with current configuration.
    """
    try:
        # Read existing pyproject.toml
        with open("pyproject.toml", encoding="utf-8") as f:
            content = f.read()

        new_section = _build_dev_metrics_section(config)

        # Check if [tool.dev-metrics] section exists
        if "[tool.dev-metrics]" in content:
            # Section exists, replace it
            # Match from [tool.dev-metrics] to the next section or end of file
            pattern = r"\[tool\.dev-metrics\].*?(?=\n\[|\Z)"
            content = re.sub(pattern, new_section.rstrip(), content, flags=re.DOTALL)
        else:
            # Section doesn't exist, append it
            content = content.rstrip() + "\n\n" + new_section

        # Write back to pyproject.toml
        with open("pyproject.toml", "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        # Don't fail the entire script if we can't save config
        print(f"Warning: Could not save configuration to pyproject.toml: {e}", file=sys.stderr)


def _build_dev_metrics_section(config: MetricsConfig) -> str:
    """Build the [tool.dev-metrics] section content."""
    lines = ["[tool.dev-metrics]"]
    lines.append("# Paths for metrics calculation")
    lines.append(f"src-paths = {_format_toml_value([str(p) for p in config.src_paths])}")
    lines.append(f"tests-paths = {_format_toml_value([str(p) for p in config.tests_paths])}")
    lines.append("# Tool paths (can be overridden for custom installations)")
    lines.append(f"radon-path = {_format_toml_value(config.radon_list)}")
    lines.append(f"pylint-path = {_format_toml_value(config.pylint_list)}")
    lines.append(f"pytest-path = {_format_toml_value(config.pytest_list)}")
    lines.append("# Test file configuration")
    lines.append(f'test-pattern = "{config.test_pattern}"')
    lines.append("# Filter to specific test type subdirectory")
    lines.append(f"test-type = {_format_toml_value(config.test_types)}")
    lines.append(f'package = "{config.package}"  # Optional: auto-detected from src/ directory or project name')
    lines.append("# Optional: files to exclude from untested report")
    lines.append(f"excluded-files = {_format_toml_value(config.excluded_files)}")
    lines.append("")
    return "\n".join(lines)


def _format_toml_value(value: list[str]) -> str:
    """Format a list of strings as TOML array or string."""
    if len(value) == 1:
        # Single item - check if it has spaces
        item = value[0]
        if " " in item:
            # Has spaces, keep as list for clarity
            return f'["{item}"]'
        else:
            # No spaces, can be a simple string
            return f'"{item}"'
    else:
        # Multiple items, format as array
        formatted_items = [f'"{item}"' for item in value]
        if len(formatted_items) <= 3:
            # Short list, single line
            return f"[{', '.join(formatted_items)}]"
        else:
            # Long list, multi-line
            items_str = ",\n    ".join(formatted_items)
            return f"[\n    {items_str}\n]"


def as_list(value: str | list[str]) -> list[str]:
    if isinstance(value, str):
        return value.split(" ")
    return value


def as_str(value: str | list[str]) -> str:
    if isinstance(value, list):
        return " ".join(value)
    return value


def as_paths(value: str | list[str]) -> list[Path]:
    if isinstance(value, str):
        return [Path(p) for p in value.split(",")]
    return [Path(p) for p in value]


def parse_arguments() -> tuple[MetricsConfig, bool]:
    """Parse command line arguments and load configuration.

    Returns:
        Tuple of (config, show_config_only)
    """
    mapping_str = "\n".join(
        [
            "{:<17s} => {}".format(*args)
            for args in (
                ("--src", "tool.dev-metrics.src-paths"),
                ("--tests", "tool.dev-metrics.tests-paths"),
                ("--radon", "tool.dev-metrics.radon-path"),
                ("--pylint", "tool.dev-metrics.pylint-path"),
                ("--pytest", "tool.dev-metrics.pytest-path"),
                ("--test-pattern", "tool.dev-metrics.test-pattern"),
                ("--test-type", "tool.dev-metrics.test-type"),
                ("--package", "tool.dev-metrics.package"),
                ("--excluded-files", "tool.dev-metrics.excluded-files"),
            )
        ]
    )
    parser = ArgumentParser(
        description="Generate project metrics summary.\n\n"
        "Provides a concise overview of project statistics including:\n"
        "- Source code metrics (files, SLOC, complexity)\n"
        "- Test code metrics (coverage, test counts)\n"
        "- Code quality metrics (duplication, risk analysis)",
        epilog=dedent(""" \
            pyproject.toml mapping:

            """)
        + mapping_str
        + dedent("""

            Examples:
            
            # Run with defaults from pyproject.toml:
            dev-metrics.py

            # Show resolved configuration without running:
            dev-metrics.py --show
            
            # Override source paths:
            dev-metrics.py --src src lib --tests tests
            
            # Specify custom test pattern:
            dev-metrics.py --test-pattern 'test_*.py' --test-type unit integration
         """),
        add_help=False,
        allow_abbrev=False,
    )
    paths_group = parser.add_argument_group("Paths options", "Configure source and test directory locations")
    tool_group = parser.add_argument_group("Tool options", "Specify paths to external analysis tools")
    test_group = parser.add_argument_group("Test selection options", "Configure test discovery and filtering")
    package_group = parser.add_argument_group("Package options", "Configure package detection and file exclusions")

    parser.add_argument(
        "--show",
        action="store_true",
        help="Display resolved configuration from CLI args and pyproject.toml, then exit",
    )
    parser.add_argument(
        "--persist",
        action="store_true",
        help="Save the resolved configuration to pyproject.toml [tool.dev-metrics] section",
    )
    parser.add_argument("-h", "--help", action="help", help="Display this help message")
    paths_group.add_argument(
        "--src",
        dest="src_paths",
        action="extend",
        nargs="+",
        metavar="DIR1[ DIR2 ...]",
        help="Path(s) to source code directories (default: src)",
    )
    paths_group.add_argument(
        "--tests",
        dest="tests_paths",
        nargs="+",
        metavar="DIR1[ DIR2 ...]",
        help="Path(s) to test directories (default: tests)",
    )
    tool_group.add_argument(
        "--radon",
        dest="radon_list",
        nargs="+",
        help="Path to radon executable (for complexity analysis) - can specify multiple (default: radon)",
    )
    tool_group.add_argument(
        "--pylint",
        dest="pylint_list",
        nargs="+",
        metavar="PATH1[ PATH2 ...]",
        help="Path to pylint executable (for code quality checks) - can specify multiple (default: pylint)",
    )
    tool_group.add_argument(
        "--pytest",
        dest="pytest_list",
        nargs="+",
        metavar="PATH1[ PATH2 ...]",
        help="Path to pytest executable (for test execution) (default: pytest)",
    )
    test_group.add_argument(
        "--test-pattern",
        dest="test_pattern",
        type=str,
        metavar="PATTERN",
        help="Glob pattern for discovering test files (default: test_*.py)",
    )
    test_group.add_argument(
        "--test-type",
        dest="test_types",
        nargs="+",
        metavar="TYPE1[ TYPE2 ...]",
        help="Test type subdirectory names to include (default: unit functional integration e2e)",
    )
    package_group.add_argument(
        "--package",
        dest="package",
        metavar="NAME",
        help="Top-level package name (auto-detected from pyproject.toml if not specified)",
    )
    package_group.add_argument(
        "--excluded-files",
        dest="excluded_files",
        action="extend",
        nargs="+",
        metavar="FILE1[ FILE2 ...]",
        help="Files to exclude from untested files report (default: __init__.py __main__.py _version.py)",
    )

    args = parser.parse_args()

    # Load config from pyproject.toml
    pyproject_config = load_config_from_pyproject()

    # Apply configuration priority: CLI args > pyproject.toml > defaults

    # Source paths
    src_paths = (
        [Path(p) for p in args.src_paths]
        if args.src_paths
        else as_paths(pyproject_config.get("src-paths"))
        if "src-paths" in pyproject_config
        else [Path("src")]
    )

    # Test paths
    tests_paths = (
        [Path(p) for p in args.tests_paths]
        if args.tests_paths
        else as_paths(pyproject_config.get("tests-paths"))
        if "tests-paths" in pyproject_config
        else [Path("tests")]
    )

    # Tool paths
    radon_list = (
        args.radon_list
        if args.radon_list
        else as_list(pyproject_config.get("radon-path"))
        if "radon-path" in pyproject_config
        else ["radon"]
    )

    pylint_list = (
        args.pylint_list
        if args.pylint_list
        else as_list(pyproject_config.get("pylint-path"))
        if "pylint-path" in pyproject_config
        else ["pylint"]
    )

    pytest_list = (
        args.pytest_list
        if args.pytest_list
        else as_list(pyproject_config.get("pytest-path"))
        if "pytest-path" in pyproject_config
        else ["pytest"]
    )

    # Test configuration
    test_pattern = (
        args.test_pattern
        if args.test_pattern
        else as_str(pyproject_config.get("test-pattern"))
        if "test-pattern" in pyproject_config
        else "test_*.py"
    )

    test_types = (
        args.test_types
        if args.test_types
        else as_list(pyproject_config.get("test-type"))
        if "test-type" in pyproject_config
        else ["unit", "functional", "integration", "e2e"]
    )

    # Package configuration
    package_name = (
        args.package
        if args.package
        else as_str(pyproject_config.get("package"))
        if "package" in pyproject_config
        else detect_package_name(src_paths)
    )

    excluded_files = (
        args.excluded_files
        if args.excluded_files
        else as_list(pyproject_config.get("excluded-files"))
        if "excluded-files" in pyproject_config
        else ["__init__.py", "__main__.py", "_version.py"]
    )

    config = MetricsConfig(
        src_paths=src_paths,
        tests_paths=tests_paths,
        radon_list=radon_list,
        pylint_list=pylint_list,
        pytest_list=pytest_list,
        test_pattern=test_pattern,
        test_types=test_types,
        package=package_name,
        excluded_files=excluded_files,
    )

    return config, args.show, args.persist


def show_config(config: MetricsConfig) -> None:
    """Display the resolved configuration."""
    output_section_header("=== Resolved Configuration ===")

    output(f"{Colors.BOLD}Source Paths:{Colors.NC}")
    for path in config.src_paths:
        output(f"  - {path}")

    output(f"\n{Colors.BOLD}Test Paths:{Colors.NC}")
    for path in config.tests_paths:
        output(f"  - {path}")

    output(f"\n{Colors.BOLD}Tool Commands:{Colors.NC}")
    output(f"  Radon:  {' '.join(config.radon_list)}")
    output(f"  Pylint: {' '.join(config.pylint_list)}")
    output(f"  Pytest: {' '.join(config.pytest_list)}")

    output(f"\n{Colors.BOLD}Test Configuration:{Colors.NC}")
    output(f"  Pattern:    {config.test_pattern}")
    output(f"  Test Types: {', '.join(config.test_types) if config.test_types else 'All'}")

    output(f"\n{Colors.BOLD}Package Configuration:{Colors.NC}")
    output(f"  Package Name:    {config.package}")
    output(f"  Excluded Files:  {', '.join(config.excluded_files)}")

    output("")


def main() -> None:
    """Main entry point for metrics script."""
    # Load configuration
    config, show_only, persist = parse_arguments()

    # If --persist flag is set, save resolved configuration to pyproject.toml
    if persist:
        save_config_to_pyproject(config)
        output(f"{Colors.GREEN}Configuration saved to pyproject.toml [tool.dev-metrics]{Colors.NC}")

    # If --show flag is set, display config and exit
    if show_only:
        show_config(config)
        return

    # Phase 1: Gather all data
    metrics = gather_all_metrics(config)

    # Phase 2: Generate report
    generate_report(metrics)


if __name__ == "__main__":
    main()
