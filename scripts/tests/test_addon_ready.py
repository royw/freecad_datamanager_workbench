# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileNotice: Part of the DataManager addon.

"""Tests for scripts/project-ready.py.

Note: the script is loaded via importlib from its file path.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


def _load_addon_ready_module() -> object:
    script_path = Path(__file__).resolve().parents[1] / "project-ready.py"
    spec = importlib.util.spec_from_file_location("addon_ready", script_path)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def addon_ready() -> object:
    return _load_addon_ready_module()


def _fixtures_dir() -> Path:
    return Path(__file__).resolve().parent / "fixtures"


def _write_json(path: Path, obj: object) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")


# --------------------------------------------------------------------------------------
# JSON / spec loading
# --------------------------------------------------------------------------------------


def test_load_components_valid_json(addon_ready: object) -> None:
    components_path = _fixtures_dir() / "components-valid.json"
    components = addon_ready._load_components(components_path)

    assert isinstance(components, dict)
    assert set(components.keys()) == {
        "file",
        "dir",
        "content-exists",
        "content-has",
        "toml-keys",
        "xml",
    }

    spec = components["file"]
    assert isinstance(spec.path, Path)
    assert isinstance(spec.required, bool)
    assert spec.checker in addon_ready.CHECKERS.values()


@pytest.mark.parametrize(
    "fixture_name,expected_substr",
    [
        ("components-invalid-root.json", "invalid components JSON root"),
        ("components-invalid-entry.json", "invalid component entry"),
        ("components-invalid-checker-type.json", "invalid checker"),
        ("components-invalid-path-type.json", "invalid path"),
        ("components-invalid-required-type.json", "invalid required"),
        ("components-invalid-content-type.json", "invalid content"),
        ("components-invalid-content-list.json", "invalid content list"),
        ("components-invalid-unknown-checker.json", "unknown checker"),
    ],
)
def test_load_components_invalid_json(addon_ready: object, fixture_name: str, expected_substr: str) -> None:
    components_path = _fixtures_dir() / fixture_name
    with pytest.raises(RuntimeError) as excinfo:
        addon_ready._load_components(components_path)

    assert expected_substr in str(excinfo.value)


# --------------------------------------------------------------------------------------
# FileExists
# --------------------------------------------------------------------------------------


def test_file_exists_simple_file_pass(addon_ready: object, tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("x", encoding="utf-8")
    ok, msg = addon_ready.FileExists().check(tmp_path / "a.txt")
    assert ok is True
    assert msg is None


def test_file_exists_simple_file_fail(addon_ready: object, tmp_path: Path) -> None:
    ok, msg = addon_ready.FileExists().check(tmp_path / "missing.txt")
    assert ok is False
    assert msg == f"missing file: {tmp_path / 'missing.txt'}"


def test_file_exists_path_with_intermediate_glob_pass(addon_ready: object, tmp_path: Path) -> None:
    # tmp_path/sub/a.txt should satisfy tmp_path/*/a.txt
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "a.txt").write_text("x", encoding="utf-8")

    ok, msg = addon_ready.FileExists().check(tmp_path / "*" / "a.txt")
    assert ok is True
    assert msg is None


def test_file_exists_content_glob_under_dir_pass(addon_ready: object, tmp_path: Path) -> None:
    d = tmp_path / "docs"
    d.mkdir()
    (d / "README.md").write_text("x", encoding="utf-8")

    ok, msg = addon_ready.FileExists().check(d, "*.md")
    assert ok is True
    assert msg is None


def test_file_exists_content_glob_under_dir_fail(addon_ready: object, tmp_path: Path) -> None:
    d = tmp_path / "docs"
    d.mkdir()

    ok, msg = addon_ready.FileExists().check(d, "*.md")
    assert ok is False
    assert msg == f"no matches for glob {'*.md'!r} under {d}"


def test_file_exists_required_filenames_pass(addon_ready: object, tmp_path: Path) -> None:
    d = tmp_path / "docs"
    d.mkdir()
    (d / "a.txt").write_text("x", encoding="utf-8")
    (d / "b.txt").write_text("x", encoding="utf-8")

    ok, msg = addon_ready.FileExists().check(d, ["a.txt", "b.txt"])
    assert ok is True
    assert msg is None


def test_file_exists_required_filenames_one_missing(addon_ready: object, tmp_path: Path) -> None:
    d = tmp_path / "docs"
    d.mkdir()
    (d / "a.txt").write_text("x", encoding="utf-8")

    ok, msg = addon_ready.FileExists().check(d, ["a.txt", "b.txt"])
    assert ok is False
    assert msg == f"missing file: {d}/b.txt"


def test_file_exists_required_filenames_many_missing(addon_ready: object, tmp_path: Path) -> None:
    d = tmp_path / "docs"
    d.mkdir()

    ok, msg = addon_ready.FileExists().check(d, ["a.txt", "b.txt"])
    assert ok is False
    assert msg == f"missing files under {d}: {['a.txt', 'b.txt']!r}"


def test_file_exists_with_content_but_dir_missing(addon_ready: object, tmp_path: Path) -> None:
    ok, msg = addon_ready.FileExists().check(tmp_path / "missing_dir", "*.txt")
    assert ok is False
    assert msg == f"missing directory for file check: {tmp_path / 'missing_dir'}"


# --------------------------------------------------------------------------------------
# DirExists
# --------------------------------------------------------------------------------------


def test_dir_exists_pass(addon_ready: object, tmp_path: Path) -> None:
    d = tmp_path / "x"
    d.mkdir()
    ok, msg = addon_ready.DirExists().check(d)
    assert ok is True
    assert msg is None


def test_dir_exists_fail_non_glob(addon_ready: object, tmp_path: Path) -> None:
    ok, msg = addon_ready.DirExists().check(tmp_path / "missing")
    assert ok is False
    assert msg == f"missing directory: {tmp_path / 'missing'}"


def test_dir_exists_fail_glob(addon_ready: object, tmp_path: Path) -> None:
    ok, msg = addon_ready.DirExists().check(tmp_path / "does-not-exist" / "*")
    assert ok is False
    assert msg == f"missing directory matching glob: {tmp_path / 'does-not-exist' / '*'}"


# --------------------------------------------------------------------------------------
# ContentExists
# --------------------------------------------------------------------------------------


def test_content_exists_nonempty_pass(addon_ready: object, tmp_path: Path) -> None:
    p = tmp_path / "a.txt"
    p.write_text("hello", encoding="utf-8")
    ok, msg = addon_ready.ContentExists().check(p)
    assert ok is True
    assert msg is None


def test_content_exists_empty_fail(addon_ready: object, tmp_path: Path) -> None:
    p = tmp_path / "a.txt"
    p.write_text("   \n", encoding="utf-8")
    ok, msg = addon_ready.ContentExists().check(p)
    assert ok is False
    assert msg == f"empty file: {p}"


def test_content_exists_missing_fail(addon_ready: object, tmp_path: Path) -> None:
    p = tmp_path / "missing.txt"
    ok, msg = addon_ready.ContentExists().check(p)
    assert ok is False
    assert msg == f"missing file: {p}"


def test_content_exists_glob_candidates_pass(addon_ready: object, tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("hello", encoding="utf-8")
    ok, msg = addon_ready.ContentExists().check(tmp_path / "*.md")
    assert ok is True
    assert msg is None


def test_content_exists_expected_substring_pass(addon_ready: object, tmp_path: Path) -> None:
    p = tmp_path / "a.txt"
    p.write_text("hello world", encoding="utf-8")
    ok, msg = addon_ready.ContentExists().check(p, "world")
    assert ok is True
    assert msg is None


def test_content_exists_expected_substring_fail(addon_ready: object, tmp_path: Path) -> None:
    p = tmp_path / "a.txt"
    p.write_text("hello", encoding="utf-8")
    ok, msg = addon_ready.ContentExists().check(p, "world")
    assert ok is False
    assert msg == f"expected content not found in {p}: {'world'!r}"


def test_content_exists_invalid_content_type_list(addon_ready: object, tmp_path: Path) -> None:
    p = tmp_path / "a.txt"
    p.write_text("hello", encoding="utf-8")
    ok, msg = addon_ready.ContentExists().check(p, ["x"])  # type: ignore[arg-type]
    assert ok is False
    assert "invalid content (expected str) for ContentExists" in (msg or "")


# --------------------------------------------------------------------------------------
# ContentHas
# --------------------------------------------------------------------------------------


def test_content_has_pass(addon_ready: object, tmp_path: Path) -> None:
    p = tmp_path / "a.txt"
    p.write_text("hello world\nsecond line\n", encoding="utf-8")
    ok, msg = addon_ready.ContentHas().check(p, "hello\nsecond")
    assert ok is True
    assert msg is None


def test_content_has_missing_file_fail(addon_ready: object, tmp_path: Path) -> None:
    p = tmp_path / "missing.txt"
    ok, msg = addon_ready.ContentHas().check(p, "hello")
    assert ok is False
    assert msg == f"missing file: {p}"


def test_content_has_no_content_fail(addon_ready: object, tmp_path: Path) -> None:
    p = tmp_path / "a.txt"
    p.write_text("hello", encoding="utf-8")
    ok, msg = addon_ready.ContentHas().check(p, "")
    assert ok is False
    assert msg == f"no content specified for ContentHas check: {p}"


def test_content_has_invalid_content_type_list(addon_ready: object, tmp_path: Path) -> None:
    p = tmp_path / "a.txt"
    p.write_text("hello", encoding="utf-8")
    ok, msg = addon_ready.ContentHas().check(p, ["hello"])  # type: ignore[arg-type]
    assert ok is False
    assert "invalid content (expected str) for ContentHas" in (msg or "")


def test_content_has_missing_tokens_one(addon_ready: object, tmp_path: Path) -> None:
    p = tmp_path / "a.txt"
    p.write_text("hello", encoding="utf-8")
    ok, msg = addon_ready.ContentHas().check(p, "hello\nworld")
    assert ok is False
    assert msg == f"missing required substring in {p}: {'world'!r}"


def test_content_has_missing_tokens_many(addon_ready: object, tmp_path: Path) -> None:
    p = tmp_path / "a.txt"
    p.write_text("hello", encoding="utf-8")
    ok, msg = addon_ready.ContentHas().check(p, "world\nsecond")
    assert ok is False
    assert msg == f"missing required substrings in {p}: {['world', 'second']!r}"


# --------------------------------------------------------------------------------------
# TomlKeyExists
# --------------------------------------------------------------------------------------


def test_toml_key_exists_pass_list_content(addon_ready: object, tmp_path: Path) -> None:
    p = tmp_path / "pyproject.toml"
    p.write_text(
        """
[project]
name = "x"

[tool]
[tool.ruff]
line-length = 88
""".lstrip(),
        encoding="utf-8",
    )

    ok, msg = addon_ready.TomlKeyExists().check(
        p,
        [
            "project.name",
            "tool.ruff.line-length = 999  # ignored",
        ],
    )
    assert ok is True
    assert msg is None


def test_toml_key_exists_pass_str_content(addon_ready: object, tmp_path: Path) -> None:
    p = tmp_path / "pyproject.toml"
    p.write_text(
        """
[project]
name = "x"

[tool]
[tool.ruff]
line-length = 88
""".lstrip(),
        encoding="utf-8",
    )

    ok, msg = addon_ready.TomlKeyExists().check(p, "project.name\ntool.ruff")
    assert ok is True
    assert msg is None


def test_toml_key_exists_missing_file_fail(addon_ready: object, tmp_path: Path) -> None:
    p = tmp_path / "pyproject.toml"
    ok, msg = addon_ready.TomlKeyExists().check(p, "project.name")
    assert ok is False
    assert msg == f"missing file: {p}"


def test_toml_key_exists_no_content_fail(addon_ready: object, tmp_path: Path) -> None:
    p = tmp_path / "pyproject.toml"
    p.write_text("[project]\nname='x'\n", encoding="utf-8")
    ok, msg = addon_ready.TomlKeyExists().check(p, "")
    assert ok is False
    assert msg == f"no content specified for TomlKeyExists check: {p}"


def test_toml_key_exists_invalid_toml_fail(addon_ready: object, tmp_path: Path) -> None:
    p = tmp_path / "pyproject.toml"
    p.write_text("not = [toml", encoding="utf-8")
    ok, msg = addon_ready.TomlKeyExists().check(p, "project.name")
    assert ok is False
    assert f"unable to parse TOML {p}:" in (msg or "")


def test_toml_key_exists_missing_keys(addon_ready: object, tmp_path: Path) -> None:
    p = tmp_path / "pyproject.toml"
    p.write_text("[project]\nname='x'\n", encoding="utf-8")

    ok, msg = addon_ready.TomlKeyExists().check(p, ["project.name", "project.version"])
    assert ok is False
    assert msg == f"missing TOML key in {p}: project.version"


def test_toml_key_exists_missing_keys_many(addon_ready: object, tmp_path: Path) -> None:
    p = tmp_path / "pyproject.toml"
    p.write_text("[project]\nname='x'\n", encoding="utf-8")

    ok, msg = addon_ready.TomlKeyExists().check(p, ["project.version", "tool.ruff"])
    assert ok is False
    assert msg == f"missing TOML keys in {p}: {['project.version', 'tool.ruff']!r}"


# --------------------------------------------------------------------------------------
# ValidXML
# --------------------------------------------------------------------------------------


def test_valid_xml_single_file_pass(addon_ready: object, tmp_path: Path) -> None:
    p = tmp_path / "a.xml"
    p.write_text("<root />", encoding="utf-8")

    ok, msg = addon_ready.ValidXML().check(p)
    assert ok is True
    assert msg is None


def test_valid_xml_single_file_invalid_fail(addon_ready: object, tmp_path: Path) -> None:
    p = tmp_path / "a.xml"
    p.write_text("<root>", encoding="utf-8")

    ok, msg = addon_ready.ValidXML().check(p)
    assert ok is False
    assert (msg or "").startswith(f"invalid XML: {p}:")


def test_valid_xml_missing_path_fail(addon_ready: object, tmp_path: Path) -> None:
    p = tmp_path / "missing.xml"
    ok, msg = addon_ready.ValidXML().check(p)
    assert ok is False
    assert msg == f"no XML files found for: {p}"


def test_valid_xml_directory_default_glob_pass(addon_ready: object, tmp_path: Path) -> None:
    d = tmp_path / "xml"
    d.mkdir()
    (d / "a.xml").write_text("<root />", encoding="utf-8")
    (d / "b.xml").write_text("<root></root>", encoding="utf-8")

    ok, msg = addon_ready.ValidXML().check(d)
    assert ok is True
    assert msg is None


def test_valid_xml_directory_specific_files_pass(addon_ready: object, tmp_path: Path) -> None:
    d = tmp_path / "xml"
    d.mkdir()
    (d / "a.xml").write_text("<root />", encoding="utf-8")
    (d / "b.xml").write_text("<root />", encoding="utf-8")

    ok, msg = addon_ready.ValidXML().check(d, ["a.xml"])
    assert ok is True
    assert msg is None


def test_valid_xml_directory_specific_files_none_found_fail(addon_ready: object, tmp_path: Path) -> None:
    d = tmp_path / "xml"
    d.mkdir()
    (d / "a.xml").write_text("<root />", encoding="utf-8")

    ok, msg = addon_ready.ValidXML().check(d, ["missing.xml"])
    assert ok is False
    assert msg == f"no XML files found for: {d}"


def test_valid_xml_directory_invalid_file_fail(addon_ready: object, tmp_path: Path) -> None:
    d = tmp_path / "xml"
    d.mkdir()
    (d / "a.xml").write_text("<root />", encoding="utf-8")
    (d / "b.xml").write_text("<root>", encoding="utf-8")

    ok, msg = addon_ready.ValidXML().check(d)
    assert ok is False
    assert msg is not None
    assert "invalid XML:" in msg


# --------------------------------------------------------------------------------------
# run() integration: required/recommended and strict mode
# --------------------------------------------------------------------------------------


def test_run_required_failure_exit_1(addon_ready: object, tmp_path: Path) -> None:
    components_json = {
        "required-missing": {
            "path": "missing.txt",
            "required": True,
            "checker": "FileExists",
            "content": None,
        }
    }
    config_path = tmp_path / "components.json"
    _write_json(config_path, components_json)

    components = addon_ready._load_components(config_path)
    rc = addon_ready.run(tmp_path, components, strict=False)
    assert rc == 1


def test_run_recommended_failure_exit_0_non_strict(addon_ready: object, tmp_path: Path) -> None:
    components_json = {
        "recommended-missing": {
            "path": "missing.txt",
            "required": False,
            "checker": "FileExists",
            "content": None,
        }
    }
    config_path = tmp_path / "components.json"
    _write_json(config_path, components_json)

    components = addon_ready._load_components(config_path)
    rc = addon_ready.run(tmp_path, components, strict=False)
    assert rc == 0


def test_run_recommended_failure_exit_2_strict(addon_ready: object, tmp_path: Path) -> None:
    components_json = {
        "recommended-missing": {
            "path": "missing.txt",
            "required": False,
            "checker": "FileExists",
            "content": None,
        }
    }
    config_path = tmp_path / "components.json"
    _write_json(config_path, components_json)

    components = addon_ready._load_components(config_path)
    rc = addon_ready.run(tmp_path, components, strict=True)
    assert rc == 2


# --------------------------------------------------------------------------------------
# describe_components()
# --------------------------------------------------------------------------------------


def test_describe_components_sorted_and_phrasing(addon_ready: object) -> None:
    components: dict[str, object] = {
        # Intentionally not in path order
        "license": addon_ready.ComponentSpec(
            path=Path("LICENSE*"),
            required=True,
            content=None,
            checker=addon_ready.ContentExists,
        ),
        "docs": addon_ready.ComponentSpec(
            path=Path("docs"),
            required=False,
            content=None,
            checker=addon_ready.DirExists,
        ),
        "pyproject": addon_ready.ComponentSpec(
            path=Path("pyproject.toml"),
            required=True,
            content=["project.name"],
            checker=addon_ready.TomlKeyExists,
        ),
    }

    lines = addon_ready.describe_components(components)  # type: ignore[arg-type]

    # Sorted by path string: LICENSE* < docs < pyproject.toml
    assert lines[0].startswith("Require that")
    assert "LICENSE*" in lines[0]
    assert "non-empty" in lines[0]

    assert lines[1].startswith("Suggest that")
    assert "`docs`" in lines[1]

    assert lines[2].startswith("Require that")
    assert "`pyproject.toml`" in lines[2]

    # Single-line output preferred
    assert all("\n" not in line for line in lines)


def test_describe_components_does_not_expose_checker_names(addon_ready: object) -> None:
    components: dict[str, object] = {
        "x": addon_ready.ComponentSpec(
            path=Path("LICENSE*"),
            required=True,
            content=None,
            checker=addon_ready.ContentExists,
        )
    }

    (line,) = addon_ready.describe_components(components)  # type: ignore[arg-type]
    assert "ContentExists" not in line
    assert "FileExists" not in line
    assert "DirExists" not in line
    assert "TomlKeyExists" not in line
    assert "ValidXML" not in line


# --------------------------------------------------------------------------------------
# checklist selection (--check-list / PROJECT_READY_CHECKLIST)
# --------------------------------------------------------------------------------------


def test_check_list_arg_wins_over_env(addon_ready: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Create two different checklists.
    arg_list = tmp_path / "arg.json"
    env_list = tmp_path / "env.json"

    _write_json(
        arg_list,
        {
            "ok": {
                "path": "a.txt",
                "required": True,
                "checker": "FileExists",
                "content": None,
            }
        },
    )
    _write_json(
        env_list,
        {
            "bad": {
                "path": "b.txt",
                "required": True,
                "checker": "FileExists",
                "content": None,
            }
        },
    )

    monkeypatch.setenv("PROJECT_READY_CHECKLIST", str(env_list))

    args = addon_ready._parse_args([".", "--check-list", str(arg_list)])
    resolved = addon_ready._resolve_checklist_path(args)
    assert resolved == arg_list.resolve()


def test_check_list_env_used_when_no_arg(addon_ready: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_list = tmp_path / "env.json"
    _write_json(
        env_list,
        {
            "ok": {
                "path": "a.txt",
                "required": True,
                "checker": "FileExists",
                "content": None,
            }
        },
    )

    monkeypatch.setenv("PROJECT_READY_CHECKLIST", str(env_list))
    args = addon_ready._parse_args(["."])
    resolved = addon_ready._resolve_checklist_path(args)
    assert resolved == env_list.resolve()


def test_main_without_checklist_prints_help_and_exits_2(addon_ready: object, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.delenv("PROJECT_READY_CHECKLIST", raising=False)

    rc = addon_ready.main(["."])
    assert rc == 2

    captured = capsys.readouterr()
    # Help text printed to stderr.
    assert "usage:" in captured.err.lower()
