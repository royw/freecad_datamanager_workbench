#!/usr/bin/env python3

"""Project readiness checker for a FreeCAD Addon repository.

This script validates that a target project contains required components and warns
when recommended components are missing.

The checklist is stored in an external JSON file (default: `scripts/addon-ready.json`).

## addon-ready.json format

The JSON must be an object (dictionary) mapping a human-friendly component name to a
spec object:

```json
{
  "some component name": {
    "path": "relative/path/or/glob",
    "required": true,
    "checker": "CheckerName",
    "content": null
  }
}
```

Fields:

- **path**: string, path relative to the project root.
  - Supports globbing in any segment, e.g. `freecad/*/resources/icons/*.svg`.
- **required**: boolean.
  - `true` -> failing this check is an ERROR and causes a non-zero exit.
  - `false` -> failing this check is a WARN.
- **checker**: string, one of the keys in `CHECKERS`.
- **content**: null | string | list[string], checker-specific.

Checker-specific `content` semantics:

- **FileExists**
  - `content: null` -> `path` must match at least one file.
  - `content: "glob"` -> `path` must resolve to a directory (or globbed directories)
    containing at least one match for the glob (e.g. `"**/*.md"`).
  - `content: ["a", "b"]` -> `path` must resolve to a directory (or globbed
    directories) containing those filenames.
- **DirExists**
  - `content` is ignored; `path` must match at least one directory.
- **ContentExists**
  - `content: null` -> file(s) matched by `path` must be readable and non-empty.
- **ContentHas**
  - `content: "..."` -> file must contain each non-empty line as a substring.
- **TomlKeyExists**
  - `content: ["a.b.c", ...]` -> `pyproject.toml` must contain those dotted keys.
  - Lines containing `=` are allowed; everything after `=` is ignored.
- **ValidXML**
  - If `path` resolves to a file -> validate that it is well-formed XML.
  - If `path` resolves to a directory -> validate `*.xml` in that directory.
  - If `content: ["x.xml", ...]` and `path` is a directory -> validate only those files.

Exit codes:

- `0` success
- `1` at least one required component failed
- `2` invalid CLI arguments/components file, or `--strict` and a recommended check failed
"""

import argparse
from dataclasses import dataclass
import json
import sys
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Protocol, TypedDict


class CheckProtocol(Protocol):
    def check(
        self, path: Path, content: str | list[str] | None = None
    ) -> tuple[bool, str | None]:
        ...


def _has_glob(path: Path) -> bool:
    # True if any path segment contains glob metacharacters.
    return any(any(ch in part for ch in ("*", "?", "[", "]")) for part in path.parts)


def _expand_glob_path(path: Path) -> list[Path]:
    # Expand a path that may contain glob metacharacters in any segment.
    # Example: freecad/*/resources -> [freecad/datamanager_wb/resources, ...]
    if not _has_glob(path):
        return [path]

    parts = path.parts
    first_glob_index = next(
        i for i, part in enumerate(parts) if any(ch in part for ch in ("*", "?", "[", "]"))
    )

    base = Path(*parts[:first_glob_index])
    pattern = str(Path(*parts[first_glob_index:]))
    try:
        return list(base.glob(pattern))
    except OSError:
        return []


class FileExists:
    def check(self, path: Path, content: str | list[str] | None = None) -> tuple[bool, str | None]:
        # Supports:
        # - path globs (including intermediate segments)
        # - directory-scoped glob checks via `content: "pattern"`
        # - directory required filename list via `content: ["a", "b"]`
        expanded = _expand_glob_path(path)

        if content is None:
            if any(p.is_file() for p in expanded):
                return True, None
            return False, f"missing file: {path}"

        dirs = [p for p in expanded if p.is_dir()]
        if not dirs:
            return False, f"missing directory for file check: {path}"

        if isinstance(content, str):
            for d in dirs:
                for match in d.glob(content):
                    if match.exists():
                        return True, None
            return False, f"no matches for glob {content!r} under {path}"

        missing: list[str] = []
        for name in content:
            if not any((d / name).exists() for d in dirs):
                missing.append(name)

        if not missing:
            return True, None
        if len(missing) == 1:
            return False, f"missing file: {path}/{missing[0]}"
        return False, f"missing files under {path}: {missing!r}"


class ValidXML:
    def check(self, path: Path, content: str | list[str] | None = None) -> tuple[bool, str | None]:
        # Validate well-formed XML files.
        # If path is a directory, validate *.xml unless `content` names specific files.
        files: list[Path] = []

        expanded = _expand_glob_path(path)
        if not expanded:
            return False, f"missing XML file/directory: {path}"

        for p in expanded:
            if p.is_file():
                files.append(p)
            elif p.is_dir():
                files.extend(self._files_in_dir(p, content))

        if not files:
            return False, f"no XML files found for: {path}"

        for file_path in files:
            ok, msg = self._validate_one(file_path)
            if not ok:
                return False, msg

        return True, None

    def _files_in_dir(self, directory: Path, content: str | list[str] | None) -> list[Path]:
        if content is None:
            return [p for p in directory.glob("*.xml") if p.is_file()]

        if isinstance(content, str):
            filenames = [content]
        else:
            filenames = content

        out: list[Path] = []
        for name in filenames:
            p = directory / name
            if p.is_file():
                out.append(p)
        return out

    def _validate_one(self, file_path: Path) -> tuple[bool, str | None]:
        try:
            ET.parse(file_path)
        except (OSError, ET.ParseError) as exc:
            return False, f"invalid XML: {file_path}: {exc}"
        return True, None


class DirExists:
    def check(self, path: Path, _content: str | list[str] | None = None) -> tuple[bool, str | None]:
        # Directory existence check. `path` may include globs.
        expanded = _expand_glob_path(path)
        if any(p.is_dir() for p in expanded):
            return True, None
        if _has_glob(path):
            return False, f"missing directory matching glob: {path}"
        return False, f"missing directory: {path}"


class ContentExists:
    def check(self, path: Path, content: str | list[str] | None = None) -> tuple[bool, str | None]:
        candidates: list[Path]

        if path.is_file():
            candidates = [path]
        else:
            candidates = []
            name = path.name
            if any(ch in name for ch in ("*", "?", "[", "]")):
                for match in path.parent.glob(name):
                    if match.is_file():
                        candidates.append(match)

        if not candidates:
            return False, f"missing file: {path}"

        if content is None:
            for candidate in candidates:
                try:
                    text = candidate.read_text(encoding="utf-8")
                except OSError:
                    continue
                if text.strip():
                    return True, None
            return False, f"empty file: {path}"

        candidate = candidates[0]
        try:
            text = candidate.read_text(encoding="utf-8")
        except OSError as exc:
            return False, f"unable to read {candidate}: {exc}"

        if isinstance(content, list):
            return False, f"invalid content (expected str) for ContentExists: {content!r}"

        if content in text:
            return True, None
        return False, f"expected content not found in {path}: {content!r}"


class ContentHas:
    def check(self, path: Path, content: str | list[str] | None = None) -> tuple[bool, str | None]:
        if not path.is_file():
            return False, f"missing file: {path}"

        if not content:
            return False, f"no content specified for ContentHas check: {path}"

        if isinstance(content, list):
            return False, f"invalid content (expected str) for ContentHas: {content!r}"

        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            return False, f"unable to read {path}: {exc}"

        missing: list[str] = []
        for token in (line.strip() for line in content.splitlines()):
            if not token:
                continue
            if token not in text:
                missing.append(token)

        if not missing:
            return True, None

        if len(missing) == 1:
            return False, f"missing required substring in {path}: {missing[0]!r}"
        return False, f"missing required substrings in {path}: {missing!r}"


class TomlKeyExists:
    def check(self, path: Path, content: str | list[str] | None = None) -> tuple[bool, str | None]:
        # Validates existence of dotted keys in a TOML file.
        # Any `= value` in the configured key line is ignored.
        if not path.is_file():
            return False, f"missing file: {path}"

        if not content:
            return False, f"no content specified for TomlKeyExists check: {path}"

        try:
            data = tomllib.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            return False, f"unable to parse TOML {path}: {exc}"

        if isinstance(content, list):
            raw_lines = content
        else:
            raw_lines = content.splitlines()

        missing: list[str] = []
        for raw_line in (line.strip() for line in raw_lines):
            if not raw_line or raw_line.startswith("#"):
                continue

            key = raw_line.partition("=")[0].strip()
            ok, msg = self._check_one(data, key)
            if not ok:
                missing.append(msg or key)

        if not missing:
            return True, None

        if len(missing) == 1:
            return False, f"missing TOML key in {path}: {missing[0]}"
        return False, f"missing TOML keys in {path}: {missing!r}"

    def _check_one(self, data: dict[str, Any], dotted_key: str) -> tuple[bool, str | None]:
        current: Any = data
        for part in dotted_key.split("."):
            if not isinstance(current, dict) or part not in current:
                return False, dotted_key
            current = current[part]

        return True, None


@dataclass(frozen=True, slots=True)
class ComponentSpec:
    path: Path
    required: bool
    content: str | list[str] | None
    checker: type[CheckProtocol]


class ComponentSpecJson(TypedDict):
    path: str
    required: bool
    content: str | list[str] | None
    checker: str


CHECKERS: dict[str, type[CheckProtocol]] = {
    "ContentExists": ContentExists,
    "ContentHas": ContentHas,
    "DirExists": DirExists,
    "FileExists": FileExists,
    "TomlKeyExists": TomlKeyExists,
    "ValidXML": ValidXML,
}


def _default_components_path() -> Path:
    return Path(__file__).resolve().with_suffix("").with_name("addon-ready.json")


def _load_components(path: Path) -> dict[str, ComponentSpec]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise RuntimeError(f"unable to read components file {path}: {exc}") from exc
    except ValueError as exc:
        raise RuntimeError(f"invalid JSON in components file {path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise RuntimeError(f"invalid components JSON root (expected object): {path}")

    out: dict[str, ComponentSpec] = {}
    for name, spec_any in raw.items():
        if not isinstance(name, str) or not isinstance(spec_any, dict):
            raise RuntimeError(f"invalid component entry: {name!r}")

        spec = spec_any  # runtime-validated dict

        checker_name = spec.get("checker")
        if not isinstance(checker_name, str):
            raise RuntimeError(f"invalid checker for component {name!r}")

        path_str = spec.get("path")
        if not isinstance(path_str, str):
            raise RuntimeError(f"invalid path for component {name!r}")

        required = spec.get("required")
        if not isinstance(required, bool):
            raise RuntimeError(f"invalid required flag for component {name!r}")

        content = spec.get("content")
        if content is not None and not isinstance(content, (str, list)):
            raise RuntimeError(f"invalid content for component {name!r}")
        if isinstance(content, list) and not all(isinstance(x, str) for x in content):
            raise RuntimeError(f"invalid content list for component {name!r}")

        # At this point the dict is validated to match ComponentSpecJson.
        spec_json: ComponentSpecJson = {
            "path": path_str,
            "required": required,
            "content": content,
            "checker": checker_name,
        }

        checker = CHECKERS.get(spec_json["checker"])
        if checker is None:
            raise RuntimeError(
                f"unknown checker {spec_json['checker']!r} for component {name!r}"
            )

        out[name] = ComponentSpec(
            path=Path(spec_json["path"]),
            required=spec_json["required"],
            content=spec_json["content"],
            checker=checker,
        )

    return out


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="addon-ready",
        description="Check a FreeCAD Addon project for required/recommended components.",
    )
    parser.add_argument(
        "project_root",
        nargs="?",
        default=".",
        help="Path to the project root (default: current directory)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail if recommended components are missing (default: warn only)",
    )
    parser.add_argument(
        "--components",
        default=None,
        help="Path to addon-ready.json (default: scripts/addon-ready.json next to this script)",
    )
    return parser.parse_args(argv)


def run(project_root: Path, components: dict[str, ComponentSpec], *, strict: bool = False) -> int:
    # Required failures -> ERROR and exit non-zero.
    # Recommended failures -> WARN; in --strict mode, warnings also cause non-zero exit.
    required_failures: list[str] = []
    recommended_failures: list[str] = []

    for name, spec in components.items():
        full_path = project_root / spec.path
        checker_cls: type[CheckProtocol] = spec.checker
        checker = checker_cls()
        ok, msg = checker.check(full_path, spec.content)

        if ok:
            continue

        rendered = msg or f"check failed: {name}"
        if spec.required:
            required_failures.append(rendered)
        else:
            recommended_failures.append(rendered)

    for failure in required_failures:
        print(f"ERROR {failure}")

    for failure in recommended_failures:
        if failure.startswith("missing file: "):
            print(f"WARN recommend adding file: {failure.removeprefix('missing file: ')}")
        elif failure.startswith("missing file matching glob: "):
            print(
                f"WARN recommend adding file: {failure.removeprefix('missing file matching glob: ')}"
            )
        else:
            print(f"WARN  {failure}")

    if required_failures:
        return 1

    if strict and recommended_failures:
        return 2

    return 0


def main(argv: list[str]) -> int:
    args = _parse_args(argv)
    root = Path(args.project_root).expanduser().resolve()

    components_path = _default_components_path() if args.components is None else Path(args.components).expanduser().resolve()
    try:
        components = _load_components(components_path)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if not root.exists() or not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2

    return run(root, components, strict=args.strict)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
