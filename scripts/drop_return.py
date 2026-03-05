"""Strip `return` from .rac formula blocks, converting to expression-based syntax.

Patterns handled:
1. `return expr` → `expr` (simple)
2. if-guard chains → if/elif/else expressions
3. Assignments kept, final `return` stripped
"""

import re
import sys
from pathlib import Path


def transform_formula_block(lines: list[str], base_indent: str) -> list[str]:
    """Transform a multi-line formula block to expression-based syntax.

    Args:
        lines: Lines of the formula block (after `from DATE:`)
        base_indent: The indentation level of the formula body
    """
    if not lines:
        return lines

    # Parse into statements: assignments, if-guards, bare returns, bare exprs
    statements = parse_statements(lines, base_indent)
    return render_expression_based(statements, base_indent)


def parse_statements(lines: list[str], base_indent: str):
    """Parse formula lines into structured statements."""
    stmts = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip blank lines and comments
        if not stripped or stripped.startswith("#"):
            stmts.append(("comment", line))
            i += 1
            continue

        # Assignment: `name = expr`
        m = re.match(r"^(\s*)([a-zA-Z_]\w*)\s*=\s*(.+)$", line)
        if m and not stripped.startswith("if ") and not stripped.startswith("return "):
            # Make sure it's not `==`
            rest = m.group(3)
            if not rest.startswith("="):  # not ==
                stmts.append(("assign", m.group(1), m.group(2), rest))
                i += 1
                continue

        # If-guard: `if cond:` followed by indented `return expr`
        if stripped.startswith("if "):
            # Collect the if block and its body
            if_match = re.match(r"^(\s*)if\s+(.+):\s*$", line)
            if if_match:
                cond = if_match.group(2)
                indent = if_match.group(1)
                # Collect indented body
                body_lines = []
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]
                    next_stripped = next_line.strip()
                    if not next_stripped or next_stripped.startswith("#"):
                        body_lines.append(next_line)
                        j += 1
                        continue
                    # Check if more indented than the if
                    if len(next_line) - len(next_line.lstrip()) > len(indent):
                        body_lines.append(next_line)
                        j += 1
                    else:
                        break
                stmts.append(("if_block", indent, cond, body_lines))
                i = j
                continue

        # `return expr`
        if stripped.startswith("return "):
            expr = stripped[7:]
            indent = line[:len(line) - len(line.lstrip())]
            stmts.append(("return", indent, expr))
            i += 1
            continue

        # Bare expression (already expression-based)
        stmts.append(("expr", line))
        i += 1

    return stmts


def render_expression_based(stmts, base_indent: str) -> list[str]:
    """Convert parsed statements to expression-based syntax."""
    result = []

    # Separate: leading assignments/comments, then if-guards/returns at end
    # Strategy: keep assignments as-is, convert if-guard chains to if/elif/else,
    # strip `return` from final expression

    # Find the first if-guard or return (the "expression part")
    expr_start = None
    for idx, stmt in enumerate(stmts):
        if stmt[0] in ("if_block", "return", "expr"):
            # Check if this is the start of the expression chain
            # (all remaining non-comment stmts are if-guards/returns)
            all_expr = all(
                s[0] in ("if_block", "return", "expr", "comment")
                for s in stmts[idx:]
            )
            if all_expr:
                expr_start = idx
                break

    if expr_start is None:
        # No clear expression chain — just strip returns
        for stmt in stmts:
            if stmt[0] == "return":
                result.append(f"{stmt[1]}{stmt[2]}")
            elif stmt[0] == "comment":
                result.append(stmt[1])
            elif stmt[0] == "assign":
                result.append(f"{stmt[1]}{stmt[2]} = {stmt[3]}")
            elif stmt[0] == "expr":
                result.append(stmt[1])
            elif stmt[0] == "if_block":
                result.append(f"{stmt[1]}if {stmt[2]}:")
                result.extend(render_body(stmt[3]))
        return result

    # Emit leading assignments/comments
    for stmt in stmts[:expr_start]:
        if stmt[0] == "assign":
            result.append(f"{stmt[1]}{stmt[2]} = {stmt[3]}")
        elif stmt[0] == "comment":
            result.append(stmt[1])

    # Convert the expression chain (if-guards + final return) to if/elif/else
    expr_stmts = [s for s in stmts[expr_start:] if s[0] != "comment"]
    comments_in_chain = [s for s in stmts[expr_start:] if s[0] == "comment"]

    if len(expr_stmts) == 1:
        # Single return or expression
        stmt = expr_stmts[0]
        if stmt[0] == "return":
            result.append(f"{stmt[1]}{stmt[2]}")
        elif stmt[0] == "expr":
            result.append(stmt[1])
        elif stmt[0] == "if_block":
            # Single if block with no else — keep as-is but strip returns in body
            result.append(f"{stmt[1]}if {stmt[2]}:")
            result.extend(render_body(stmt[3]))
        return result

    # Multiple expr statements: convert if-guard chain to if/elif/else
    branches = []  # (condition, value_expr) pairs
    final_expr = None

    for stmt in expr_stmts:
        if stmt[0] == "if_block":
            cond = stmt[2]
            body = stmt[3]
            # Extract the value from the body (strip return)
            value = extract_body_value(body)
            branches.append((cond, value))
        elif stmt[0] == "return":
            final_expr = stmt[2]
        elif stmt[0] == "expr":
            final_expr = stmt[1].strip()

    if branches:
        indent = base_indent
        # First branch: if
        result.append(f"{indent}if {branches[0][0]}: {branches[0][1]}")
        # Middle branches: elif
        for cond, value in branches[1:]:
            result.append(f"{indent}elif {cond}: {value}")
        # Final: else
        if final_expr is not None:
            result.append(f"{indent}else: {final_expr}")
    elif final_expr is not None:
        result.append(f"{base_indent}{final_expr}")

    return result


def extract_body_value(body_lines: list[str]) -> str:
    """Extract the expression value from an if-block body."""
    for line in body_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("return "):
            return stripped[7:]
        return stripped
    return "0"


def render_body(body_lines: list[str]) -> list[str]:
    """Render body lines, stripping return keywords."""
    result = []
    for line in body_lines:
        stripped = line.strip()
        if stripped.startswith("return "):
            indent = line[:len(line) - len(line.lstrip())]
            result.append(f"{indent}{stripped[7:]}")
        else:
            result.append(line)
    return result


def transform_file(filepath: Path) -> str:
    """Transform a .rac file to expression-based syntax."""
    content = filepath.read_text()
    lines = content.split("\n")
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Detect `from YYYY-MM-DD:` with a multi-line body
        from_match = re.match(r"^(\s+)from\s+(\d{4}-\d{2}-\d{2}):\s*$", line)
        if from_match:
            from_indent = from_match.group(1)
            body_indent = from_indent + "  "  # Expected body indentation
            result.append(line)
            i += 1

            # Collect the formula body
            body_lines = []
            while i < len(lines):
                next_line = lines[i]
                next_stripped = next_line.strip()

                # Empty line within body — include it
                if not next_stripped:
                    body_lines.append(next_line)
                    i += 1
                    continue

                # Comment line — check indentation
                if next_stripped.startswith("#"):
                    if len(next_line) - len(next_line.lstrip()) >= len(body_indent):
                        body_lines.append(next_line)
                        i += 1
                        continue
                    else:
                        break

                # Check if still part of the body (more indented than `from`)
                line_indent = len(next_line) - len(next_line.lstrip())
                if line_indent >= len(body_indent):
                    body_lines.append(next_line)
                    i += 1
                else:
                    break

            # Strip trailing blank lines from body
            while body_lines and not body_lines[-1].strip():
                body_lines.pop()

            # Check if body contains `return` — if so, transform
            has_return = any("return " in bl.strip() for bl in body_lines if bl.strip() and not bl.strip().startswith("#"))
            if has_return and body_lines:
                transformed = transform_formula_block(body_lines, body_indent)
                result.extend(transformed)
            else:
                result.extend(body_lines)
            continue

        # Detect inline `from YYYY-MM-DD: return expr`
        inline_return = re.match(r"^(\s+from\s+\d{4}-\d{2}-\d{2}:\s+)return\s+(.+)$", line)
        if inline_return:
            result.append(f"{inline_return.group(1)}{inline_return.group(2)}")
            i += 1
            continue

        result.append(line)
        i += 1

    return "\n".join(result)


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("statute")
    rac_files = sorted(root.rglob("*.rac"))

    changed = 0
    for f in rac_files:
        original = f.read_text()
        transformed = transform_file(f)
        if transformed != original:
            f.write_text(transformed)
            changed += 1
            print(f"  transformed: {f}")

    print(f"\n{changed}/{len(rac_files)} files transformed")


if __name__ == "__main__":
    main()
