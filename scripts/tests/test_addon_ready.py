"""Tests for scripts/addon-ready.py.

Note: addon-ready.py is not importable as a normal module because of the hyphen in
its filename, so these tests load it via importlib.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


def _load_addon_ready_module() -> object:
    script_path = (
        Path(__file__).resolve().parents[1] / "addon-ready.py"
    )
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
