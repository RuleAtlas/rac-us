#!/usr/bin/env python3
"""Validate that all imports in .rac files resolve to existing variables."""

import re
import sys
from pathlib import Path
from collections import defaultdict

# Pattern to match imports declarations
# Handles both single imports and list imports
IMPORTS_BLOCK_PATTERN = re.compile(r"^\s*imports:\s*(.*)$")
IMPORTS_LIST_PATTERN = re.compile(r"^\s*-\s*(.+)$")

# Pattern to parse individual import: path#variable [as alias]
IMPORT_PATTERN = re.compile(r"([^#\s\[\]]+)#(\w+)(?:\s+as\s+\w+)?")

# Pattern to find variable/input definitions
VARIABLE_DEF_PATTERN = re.compile(r"^(variable|input)\s+(\w+):")
PARAMETER_DEF_PATTERN = re.compile(r"^parameter\s+(\w+):")


def extract_exports(filepath: Path) -> set[str]:
    """Extract all variable/input/parameter names defined in a file."""
    exports = set()
    try:
        content = filepath.read_text()
        for line in content.split("\n"):
            # Check for variable/input definitions
            match = VARIABLE_DEF_PATTERN.match(line)
            if match:
                exports.add(match.group(2))
                continue
            # Check for parameter definitions
            match = PARAMETER_DEF_PATTERN.match(line)
            if match:
                exports.add(match.group(1))
    except Exception as e:
        print(f"Warning: Could not read {filepath}: {e}", file=sys.stderr)
    return exports


def resolve_import_path(import_path: str, statute_dir: Path) -> Path | None:
    """
    Resolve an import path to a .rac file.

    Import path like "26/1/j/2" could resolve to:
    - statute/26/1/j/2.rac (file)
    - statute/26/1/j/2/index.rac (directory with index)
    """
    # Try direct file first
    direct_file = statute_dir / f"{import_path}.rac"
    if direct_file.exists():
        return direct_file

    # Try directory (check for any .rac file that might export the variable)
    dir_path = statute_dir / import_path
    if dir_path.is_dir():
        # Look for main file in directory
        for candidate in [dir_path / "index.rac", dir_path.parent / f"{dir_path.name}.rac"]:
            if candidate.exists():
                return candidate
        # Return directory path - caller will search all files in it
        return dir_path

    return None


def find_variable_in_path(import_path: str, variable: str, statute_dir: Path) -> tuple[bool, str]:
    """
    Find if a variable is exported from an import path.
    Returns (found: bool, error_message: str)
    """
    resolved = resolve_import_path(import_path, statute_dir)

    if resolved is None:
        return False, f"path '{import_path}' does not exist"

    if resolved.is_file():
        exports = extract_exports(resolved)
        if variable in exports:
            return True, ""
        return False, f"variable '{variable}' not found in {resolved.name} (exports: {sorted(exports) if exports else 'none'})"

    if resolved.is_dir():
        # Search all .rac files in directory
        all_exports = set()
        for rac_file in resolved.rglob("*.rac"):
            exports = extract_exports(rac_file)
            if variable in exports:
                return True, ""
            all_exports.update(exports)

        return False, f"variable '{variable}' not found in {import_path}/ directory (exports: {sorted(all_exports)[:10]}{'...' if len(all_exports) > 10 else ''})"

    return False, f"path '{import_path}' is neither file nor directory"


def extract_imports(filepath: Path) -> list[tuple[int, str, str]]:
    """
    Extract all imports from a file.
    Returns list of (line_number, import_path, variable_name)
    """
    imports = []
    content = filepath.read_text()
    lines = content.split("\n")

    in_imports_block = False

    for lineno, line in enumerate(lines, 1):
        # Check for imports: declaration
        block_match = IMPORTS_BLOCK_PATTERN.match(line)
        if block_match:
            rest = block_match.group(1).strip()

            # Inline list format: imports: [path#var, path#var]
            if rest.startswith("["):
                in_imports_block = False
                # Extract all imports from the line
                for match in IMPORT_PATTERN.finditer(rest):
                    imports.append((lineno, match.group(1), match.group(2)))
            # Block format starting
            elif not rest or rest == "|":
                in_imports_block = True
            continue

        # Inside imports block - look for list items
        if in_imports_block:
            list_match = IMPORTS_LIST_PATTERN.match(line)
            if list_match:
                import_str = list_match.group(1).strip()
                import_match = IMPORT_PATTERN.match(import_str)
                if import_match:
                    imports.append((lineno, import_match.group(1), import_match.group(2)))
            elif line.strip() and not line.strip().startswith("#"):
                # Non-empty, non-comment line that's not a list item = end of block
                if not line.startswith(" ") and not line.startswith("\t"):
                    in_imports_block = False

    return imports


def validate_file(filepath: Path, statute_dir: Path) -> list[str]:
    """Validate all imports in a single file."""
    errors = []

    try:
        imports = extract_imports(filepath)
    except Exception as e:
        return [f"{filepath}: failed to parse imports: {e}"]

    for lineno, import_path, variable in imports:
        found, error_msg = find_variable_in_path(import_path, variable, statute_dir)
        if not found:
            errors.append(f"{filepath}:{lineno}: broken import '{import_path}#{variable}' - {error_msg}")

    return errors


def build_dependency_graph(statute_dir: Path) -> dict[str, list[str]]:
    """Build a dependency graph for cycle detection."""
    graph = defaultdict(list)

    for rac_file in statute_dir.rglob("*.rac"):
        # Get relative path as node ID
        rel_path = rac_file.relative_to(statute_dir)
        node = str(rel_path.with_suffix("")).replace("/", "/")

        imports = extract_imports(rac_file)
        for _, import_path, _ in imports:
            graph[node].append(import_path)

    return graph


def find_cycles(graph: dict[str, list[str]]) -> list[list[str]]:
    """Find all cycles in the dependency graph using DFS."""
    cycles = []
    visited = set()
    rec_stack = set()
    path = []

    def dfs(node: str):
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                dfs(neighbor)
            elif neighbor in rec_stack:
                # Found cycle
                cycle_start = path.index(neighbor)
                cycles.append(path[cycle_start:] + [neighbor])

        path.pop()
        rec_stack.remove(node)

    for node in graph:
        if node not in visited:
            dfs(node)

    return cycles


def main():
    statute_dir = Path(__file__).parent.parent / "statute"

    if not statute_dir.exists():
        print(f"Error: {statute_dir} not found")
        sys.exit(1)

    all_errors = []
    files_checked = 0
    imports_checked = 0

    # Validate all imports resolve
    for rac_file in statute_dir.rglob("*.rac"):
        files_checked += 1
        imports = extract_imports(rac_file)
        imports_checked += len(imports)
        errors = validate_file(rac_file, statute_dir)
        all_errors.extend(errors)

    # Check for circular dependencies
    print(f"Building dependency graph...")
    graph = build_dependency_graph(statute_dir)
    cycles = find_cycles(graph)

    for cycle in cycles:
        cycle_str = " -> ".join(cycle)
        all_errors.append(f"Circular dependency detected: {cycle_str}")

    print(f"Checked {files_checked} files, {imports_checked} imports")

    if all_errors:
        print(f"\n❌ Found {len(all_errors)} import errors:\n")
        for error in sorted(all_errors):
            print(f"  {error}")
        sys.exit(1)
    else:
        print("\n✅ All imports resolve correctly, no circular dependencies")
        sys.exit(0)


if __name__ == "__main__":
    main()
