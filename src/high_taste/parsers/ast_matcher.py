"""AST-based pattern matcher for Python code analysis."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import TYPE_CHECKING, NamedTuple

from loguru import logger

if TYPE_CHECKING:
    from collections.abc import Callable


class CodeViolation(NamedTuple):
    """A code violation found by pattern matching."""

    rule_id: str
    line_number: int
    column: int
    message: str
    severity: str


@dataclass(frozen=True)
class ASTPattern:
    """Pattern for matching AST nodes."""

    rule_id: str
    description: str
    node_type: type[ast.AST]
    check_function: Callable[[ast.AST, list[str]], CodeViolation | None]


class TasteAnalyzer(ast.NodeVisitor):
    """AST visitor that checks code against taste rules."""

    def __init__(self, patterns: list[ASTPattern]) -> None:
        self.patterns = patterns
        self.violations: list[CodeViolation] = []
        self.source_lines: list[str] = []

    def analyze_code(self, source_code: str) -> list[CodeViolation]:
        """Analyze Python source code and return violations."""
        self.violations = []
        self.source_lines = source_code.splitlines()

        try:
            tree = ast.parse(source_code)
            self.visit(tree)
        except SyntaxError as e:
            self.violations.append(
                CodeViolation(
                    rule_id="SYNTAX",
                    line_number=e.lineno or 1,
                    column=e.offset or 0,
                    message=f"Syntax error: {e.msg}",
                    severity="Error",
                )
            )

        return self.violations

    def visit(self, node: ast.AST) -> None:
        """Visit AST node and check patterns."""
        for pattern in self.patterns:
            if isinstance(node, pattern.node_type):
                try:
                    violation = pattern.check_function(node, self.source_lines)
                    if violation:
                        self.violations.append(violation)
                except Exception as e:
                    logger.warning(f"Pattern check failed for {pattern.rule_id}: {e}")

        self.generic_visit(node)


def check_try_except_defensive(
    node: ast.Try, _source_lines: list[str]
) -> CodeViolation | None:
    """Check for defensive try/except patterns (Rule 001)."""
    if not node.handlers:
        return None

    # Look for broad exception handling
    for handler in node.handlers:
        if handler.type is None:  # bare except:
            return CodeViolation(
                rule_id="001",
                line_number=node.lineno,
                column=node.col_offset,
                message="Use assertions instead of bare except for validation",
                severity="Warning",
            )

        # Check for Exception or BaseException catches
        if isinstance(handler.type, ast.Name) and handler.type.id in [
            "Exception",
            "BaseException",
        ]:
            # Check if the handler returns a default value (common defensive pattern)
            for stmt in handler.body:
                if (
                    isinstance(stmt, ast.Return)
                    and stmt.value
                    and isinstance(stmt.value, ast.Constant)
                ):
                    value = stmt.value.value
                    if value in [0, 0.0, "", None, False]:
                        return CodeViolation(
                            rule_id="001",
                            line_number=node.lineno,
                            column=node.col_offset,
                            message="Defensive exception handling with default return - use assertions instead",
                            severity="Warning",
                        )

    return None


def check_repeated_file_loads(
    node: ast.Call, _source_lines: list[str]
) -> CodeViolation | None:
    """Check for file loading inside functions (Rule 002)."""
    # Look for open() calls or json.load() calls inside function definitions
    if isinstance(node.func, ast.Name) and node.func.id == "open":
        # Check if we're inside a function
        return CodeViolation(
            rule_id="002",
            line_number=node.lineno,
            column=node.col_offset,
            message="Consider loading files at module level instead of inside functions",
            severity="Warning",
        )

    # Look for json.load patterns
    if (
        isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "json"
        and node.func.attr == "load"
    ):
        return CodeViolation(
            rule_id="002",
            line_number=node.lineno,
            column=node.col_offset,
            message="Consider loading JSON at module level instead of inside functions",
            severity="Warning",
        )

    return None


def check_deep_nesting(node: ast.If, _source_lines: list[str]) -> CodeViolation | None:
    """Check for deeply nested if statements (Rule 003)."""

    def count_nesting_depth(node: ast.If, depth: int = 0) -> int:
        depth += 1
        max_depth = depth

        for child in ast.walk(node):
            if isinstance(child, ast.If) and child != node:
                child_depth = count_nesting_depth(child, depth)
                max_depth = max(max_depth, child_depth)

        return max_depth

    depth = count_nesting_depth(node)
    max_nesting_depth = 3
    if depth > max_nesting_depth:
        return CodeViolation(
            rule_id="003",
            line_number=node.lineno,
            column=node.col_offset,
            message=f"Deep nesting detected ({depth} levels) - consider using assertions for early validation",
            severity="Warning",
        )

    return None


def check_hardcoded_lists(
    node: ast.List, _source_lines: list[str]
) -> CodeViolation | None:
    """Check for hardcoded lists that could be dynamic (Rule 004)."""
    # Look for lists with string literals that might be file names
    min_list_size = 3
    min_string_count = 3
    if len(node.elts) >= min_list_size:  # Only flag lists with multiple items
        string_count = 0
        has_file_extension = False

        for elt in node.elts:
            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                string_count += 1
                if any(ext in elt.value for ext in [".json", ".txt", ".py", ".md"]):
                    has_file_extension = True

        if string_count >= min_string_count and has_file_extension:
            return CodeViolation(
                rule_id="004",
                line_number=node.lineno,
                column=node.col_offset,
                message="Consider dynamic discovery instead of hardcoded file list",
                severity="Warning",
            )

    return None


def check_tuple_returns(
    node: ast.Return, _source_lines: list[str]
) -> CodeViolation | None:
    """Check for tuple returns that should use NamedTuple (Rule 005)."""
    min_tuple_size = 2
    min_type_variety = 2
    if (
        node.value is not None
        and isinstance(node.value, ast.Tuple | ast.List)
        and len(node.value.elts) >= min_tuple_size
    ):
        # Check if the tuple contains mixed types (suggests structured data)
        types_seen = set()
        for elt in node.value.elts:
            if isinstance(elt, ast.Constant):
                types_seen.add(type(elt.value).__name__)
            elif isinstance(elt, ast.Name):
                types_seen.add("variable")

        if len(types_seen) >= min_type_variety:  # Mixed types suggest structured return
            return CodeViolation(
                rule_id="005",
                line_number=node.lineno,
                column=node.col_offset,
                message="Consider using NamedTuple or dataclass for structured return values",
                severity="Warning",
            )

    return None


def check_database_commit_order(
    node: ast.Call, source_lines: list[str]
) -> CodeViolation | None:
    """Check for commit before validation (Rule 006)."""
    if isinstance(node.func, ast.Attribute) and node.func.attr == "commit":
        # Look for the next few lines to see if there's an assertion
        line_num = node.lineno
        if line_num < len(source_lines):
            # Check next 3 lines for assertions
            for i in range(1, min(4, len(source_lines) - line_num + 1)):
                next_line = source_lines[line_num + i - 1].strip()
                if next_line.startswith("assert"):
                    return CodeViolation(
                        rule_id="006",
                        line_number=node.lineno,
                        column=node.col_offset,
                        message="Validate database operation before commit - move assertions before commit()",
                        severity="Error",
                    )

    return None


# Define all patterns
DEFAULT_PATTERNS = [
    ASTPattern("001", "Defensive try/except", ast.Try, check_try_except_defensive),
    ASTPattern("002", "Repeated file loads", ast.Call, check_repeated_file_loads),
    ASTPattern("003", "Deep nesting", ast.If, check_deep_nesting),
    ASTPattern("004", "Hardcoded lists", ast.List, check_hardcoded_lists),
    ASTPattern("005", "Tuple returns", ast.Return, check_tuple_returns),
    ASTPattern("006", "Database commit order", ast.Call, check_database_commit_order),
]


def analyze_python_code(
    source_code: str, patterns: list[ASTPattern] | None = None
) -> list[CodeViolation]:
    """Analyze Python source code and return taste violations."""
    if patterns is None:
        patterns = DEFAULT_PATTERNS

    analyzer = TasteAnalyzer(patterns)
    return analyzer.analyze_code(source_code)


if __name__ == "__main__":
    # Demo: Test with sample code
    sample_code = """
def bad_function(model):
    try:
        if model:
            if model in data:
                pricing_data = json.load(open("pricing.json"))  # Bad: repeated loading
                return pricing_data[model]["cost"]
        return 0.0  # Bad: defensive return
    except Exception:
        return 0.0  # Bad: broad exception
"""

    violations = analyze_python_code(sample_code)
    print(f"Found {len(violations)} violations:")
    for v in violations:
        print(f"  Rule {v.rule_id} (line {v.line_number}): {v.message}")
