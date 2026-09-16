"""Domain-generalization guard for corpus, tool, and orchestration code.

The built-in manifest is the sole carve-out: benchmark identifiers and titles
are registration data there. Runtime code must not recognize those subjects.
"""

from __future__ import annotations

import ast
from pathlib import Path

BACKEND_SRC = Path(__file__).resolve().parents[3] / "src" / "chronicle"

FORBIDDEN_STRINGS = [
    "troppau",
    "laibach",
    "naples",
    "verona",
    "sarajevo",
    "szogyeny",
    "metternich",
    "castlereagh",
    "berchtold",
    "franz joseph",
    "blank-cheque-golden",
    "concert-of-europe-1814-1822",
    "blank cheque",
    "concert of europe",
    "july crisis",
]

# ``acquisition`` builds corpora from arbitrary topics; ``ai/orchestration`` (already
# scanned) will hold the LangGraph control-flow graph. Both must stay topic-agnostic.
SCANNED_PACKAGES = ["corpus", "ai/tools", "ai/orchestration", "acquisition", "ai/evaluation"]
EXCLUDED_FILES = {"corpus/manifest.py"}
ID_NAMES = {"corpusid", "corpus_id", "packageid", "package_id", "investigation_id"}


def _source_files() -> list[Path]:
    files: list[Path] = []
    for package in SCANNED_PACKAGES:
        root = BACKEND_SRC / package
        assert root.is_dir(), f"expected generalization surface is missing: {package}"
        for path in root.rglob("*.py"):
            if path.relative_to(BACKEND_SRC).as_posix() not in EXCLUDED_FILES:
                files.append(path)
    return sorted(files)


def _identifier_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id.casefold().lstrip("_")
    if isinstance(node, ast.Attribute):
        return node.attr.casefold().lstrip("_")
    if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant):
        if isinstance(node.slice.value, str):
            return node.slice.value.casefold().lstrip("_")
    return None


def _is_string_literal(node: ast.AST) -> bool:
    if isinstance(node, ast.Constant):
        return isinstance(node.value, str)
    if isinstance(node, (ast.Set, ast.List, ast.Tuple)):
        return any(_is_string_literal(element) for element in node.elts)
    return False


def test_scanned_packages_are_present_and_nonempty():
    files = _source_files()
    represented = {
        next(package for package in SCANNED_PACKAGES if path.is_relative_to(BACKEND_SRC / package))
        for path in files
    }
    assert represented == set(SCANNED_PACKAGES)
    assert len(files) >= 15


def test_no_known_benchmark_names_or_ids_outside_explicit_manifest_data():
    violations = []
    for path in _source_files():
        text = path.read_text(encoding="utf-8").casefold()
        for forbidden in FORBIDDEN_STRINGS:
            if forbidden in text:
                violations.append(f"{path.relative_to(BACKEND_SRC)}: contains {forbidden!r}")
    assert not violations, "\n".join(violations)


def test_no_runtime_branch_compares_corpus_or_package_id_to_a_literal():
    violations = []
    for path in _source_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Compare):
                continue
            operands = [node.left, *node.comparators]
            has_id = any(_identifier_name(operand) in ID_NAMES for operand in operands)
            if has_id and any(_is_string_literal(operand) for operand in operands):
                violations.append(f"{path.relative_to(BACKEND_SRC)}:{node.lineno}")
    assert not violations, "literal corpus/package ID comparisons:\n" + "\n".join(violations)


def test_manifest_is_the_only_carve_out_and_contains_expected_benchmark_data():
    manifest_path = BACKEND_SRC / "corpus" / "manifest.py"
    text = manifest_path.read_text(encoding="utf-8").casefold()
    assert "blank-cheque-golden" in text
    assert "concert-of-europe-1814-1822" in text
