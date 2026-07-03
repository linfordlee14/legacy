#!/usr/bin/env python3
"""Specification conventions checker.

Implements the automatable stages 1 to 6 of deployment/CI_CD.md section 4.2
(CI-06) against this repository:

  1. Markdown structural lint (heading level jumps, unbalanced code fences,
     inconsistent table rows)
  2. Relative link check (files, and heading anchors where given)
  3. Mandatory 12 sections, in order, for specification documents
  4. Title block presence (Status, Owner, Last updated, Depends on)
  5. No em dash characters anywhere in repository content
  6. TODO markers use the TODO(verify) / TODO(decision) forms

Stage 7 (tier discipline) is reviewer judgment by specification; it is carried
by the pull request checklist, not by this script.

Exit code 0 when clean, 1 when any check fails.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

SKIP_DIRS = {".git", "node_modules", ".venv", ".next", "__pycache__", ".pytest_cache", "out"}

EM_DASH = "—"
EM_DASH_EXTENSIONS = {".md", ".py", ".ts", ".tsx", ".css", ".yml", ".yaml", ".sh", ".mjs", ".json"}
EM_DASH_EXEMPT_FILES = {
    "knowledge/MASTER_CONTEXT.md",
    "apps/web/package-lock.json",
    "scripts/check_specs.py",  # defines the character it scans for
}
# Verbatim quote of the canonical mission statement (MASTER_CONTEXT section 3):
# quoted text keeps its original characters.
EM_DASH_EXEMPT_LINES = {("docs/MISSION.md", "as an act of faith-driven service")}

SPEC_DIRS = {
    "docs", "specs", "architecture", "database", "api", "ai", "agents",
    "knowledge", "memory", "security", "deployment", "testing", "ui", "roadmap",
}
ROOT_SPEC_FILES = {"CONTRIBUTING.md"}
# Exempt from structure checks per docs/SPEC_CONVENTIONS.md section 3.
STRUCTURE_EXEMPT = {
    "README.md", "CHANGELOG.md",
    "knowledge/MASTER_CONTEXT.md", "docs/SPEC_CONVENTIONS.md",
}

MANDATORY_SECTIONS = [
    "Purpose", "Goals", "Scope", "Requirements", "Acceptance Criteria",
    "Dependencies", "Risks", "Future Enhancements", "Examples",
    "Open Questions", "References", "Related Specifications",
]

TITLE_BLOCK_ROWS = ["Status", "Owner", "Last updated", "Depends on"]

# Marker lines: TODO leads the line content (after blockquote and list
# prefixes). Prose that merely mentions TODO items is not a marker.
TODO_MARKER_PREFIX = re.compile(r"^[\s>*-]*TODO")
TODO_WELL_FORMED = re.compile(r"^[\s>*-]*TODO\((verify|decision)\):")
# A parenthesized TODO with an unknown qualifier is wrong anywhere.
TODO_BAD_QUALIFIER = re.compile(r"TODO\((?!verify\)|decision\))")
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.*)$")
LINK_PATTERN = re.compile(r"\]\(([^)\s]+)\)")


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def iter_files(extensions: set[str]) -> list[Path]:
    files = []
    for path in sorted(REPO_ROOT.rglob("*")):
        if path.is_dir() or path.suffix not in extensions:
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        files.append(path)
    return files


def spec_documents() -> list[Path]:
    docs = []
    for path in iter_files({".md"}):
        r = rel(path)
        if r in STRUCTURE_EXEMPT:
            continue
        parts = Path(r).parts
        if (len(parts) == 2 and parts[0] in SPEC_DIRS) or r in ROOT_SPEC_FILES:
            docs.append(path)
    return docs


def strip_code_blocks(lines: list[str]) -> list[str]:
    """Blank out fenced code block contents so checks skip examples."""
    out, in_fence = [], False
    for line in lines:
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            out.append("")
            continue
        out.append("" if in_fence else line)
    return out


def heading_slug(text: str) -> str:
    text = re.sub(r"[`*_]", "", text.strip().lower())
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    return re.sub(r"\s+", "-", text.strip())


def check_markdown_structure(errors: list[str]) -> None:
    for path in iter_files({".md"}):
        r = rel(path)
        if r == "knowledge/MASTER_CONTEXT.md":
            continue
        raw = path.read_text(encoding="utf-8").splitlines()
        fence_count = sum(1 for line in raw if line.lstrip().startswith("```"))
        if fence_count % 2 != 0:
            errors.append(f"{r}: unbalanced code fences")
        lines = strip_code_blocks(raw)

        prev_level = 0
        for i, line in enumerate(lines, 1):
            m = HEADING_PATTERN.match(line)
            if not m:
                continue
            level = len(m.group(1))
            # House style (SPEC_CONVENTIONS section 3): an h3 tagline directly
            # under the h1 title is the standard title block opening.
            tagline = prev_level == 1 and level == 3
            if prev_level and level > prev_level + 1 and not tagline:
                errors.append(f"{r}:{i}: heading level jumps from h{prev_level} to h{level}")
            prev_level = level

        in_table, header_cells = False, 0
        for i, line in enumerate(lines, 1):
            is_row = line.lstrip().startswith("|")
            if is_row:
                cells = len([c for c in line.strip().strip("|").split("|")])
                if not in_table:
                    in_table, header_cells = True, cells
                elif cells != header_cells:
                    errors.append(
                        f"{r}:{i}: table row has {cells} cells, header has {header_cells}"
                    )
            else:
                in_table = False


def check_links(errors: list[str]) -> None:
    anchors_cache: dict[Path, set[str]] = {}

    def anchors_of(path: Path) -> set[str]:
        if path not in anchors_cache:
            found = set()
            for line in strip_code_blocks(path.read_text(encoding="utf-8").splitlines()):
                m = HEADING_PATTERN.match(line)
                if m:
                    found.add(heading_slug(m.group(2)))
            anchors_cache[path] = found
        return anchors_cache[path]

    for path in iter_files({".md"}):
        lines = strip_code_blocks(path.read_text(encoding="utf-8").splitlines())
        for i, line in enumerate(lines, 1):
            for match in LINK_PATTERN.finditer(line):
                link = match.group(1)
                if link.startswith(("http://", "https://", "mailto:")):
                    continue
                target_part, _, anchor = link.partition("#")
                target = (
                    path.parent / target_part if target_part else path
                ).resolve()
                if target_part and not target.exists():
                    errors.append(f"{rel(path)}:{i}: broken link {link}")
                    continue
                if anchor and target.suffix == ".md" and target.exists():
                    if anchor not in anchors_of(target):
                        errors.append(f"{rel(path)}:{i}: broken anchor {link}")


def check_sections_and_title_blocks(errors: list[str]) -> None:
    for path in spec_documents():
        r = rel(path)
        text = path.read_text(encoding="utf-8")
        lines = strip_code_blocks(text.splitlines())

        positions = []
        for section in MANDATORY_SECTIONS:
            pattern = re.compile(rf"^#{{2,3}}\s+(\d+\.\s+)?{re.escape(section)}\b", re.IGNORECASE)
            pos = next((i for i, line in enumerate(lines) if pattern.match(line)), None)
            if pos is None:
                errors.append(f"{r}: missing mandatory section '{section}'")
            positions.append(pos)
        present = [p for p in positions if p is not None]
        if present != sorted(present):
            errors.append(f"{r}: mandatory sections out of order")

        for row in TITLE_BLOCK_ROWS:
            if not re.search(rf"^\|\s*{re.escape(row)}\s*\|", text, re.MULTILINE):
                errors.append(f"{r}: title block missing '{row}' row")


def check_em_dashes(errors: list[str]) -> None:
    for path in iter_files(EM_DASH_EXTENSIONS):
        r = rel(path)
        if r in EM_DASH_EXEMPT_FILES:
            continue
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if EM_DASH not in line:
                continue
            if any(r == f and marker in line for f, marker in EM_DASH_EXEMPT_LINES):
                continue
            errors.append(f"{r}:{i}: em dash found")


def check_todo_format(errors: list[str]) -> None:
    for path in iter_files({".md", ".py", ".ts", ".tsx"}):
        r = rel(path)
        if r == "knowledge/MASTER_CONTEXT.md" or r == "scripts/check_specs.py":
            continue
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if "TODO" not in line:
                continue
            is_marker = TODO_MARKER_PREFIX.match(line)
            if (is_marker and not TODO_WELL_FORMED.match(line)) or TODO_BAD_QUALIFIER.search(
                line
            ):
                errors.append(f"{r}:{i}: TODO must use TODO(verify): or TODO(decision): form")


def main() -> int:
    errors: list[str] = []
    check_markdown_structure(errors)
    check_links(errors)
    check_sections_and_title_blocks(errors)
    check_em_dashes(errors)
    check_todo_format(errors)
    if errors:
        print(f"spec checks FAILED ({len(errors)} error(s)):")
        for error in errors:
            print(f"  {error}")
        return 1
    print("spec checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
