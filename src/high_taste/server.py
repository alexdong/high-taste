"""MCP server implementation for High-Taste."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from importlib.resources import as_file, files
except ImportError:
    from importlib_resources import as_file, files  # Python < 3.9 fallback

from loguru import logger
from mcp.server import FastMCP
from pydantic import BaseModel

from high_taste.parsers.ast_matcher import analyze_python_code
from high_taste.rules.parser import TasteRule, load_all_rules

# Disable logging by default for cleaner output
logger.disable("high_taste")


class FileContent(BaseModel):
    """Input model for file content."""
    path: str
    content: str


class TasteCheckInput(BaseModel):
    """Input for taste_check function."""
    files: list[FileContent]


class TasteViolation(BaseModel):
    """A taste violation with rule information."""
    rule_id: str
    rule_title: str
    file_path: str
    line_number: int
    column: int
    message: str
    severity: str
    category: str


class TasteCheckResult(BaseModel):
    """Result of taste_check operation."""
    violations: list[TasteViolation]
    total_files_checked: int
    total_violations: int
    summary_by_rule: dict[str, int]


# Create the FastMCP server instance
mcp = FastMCP("high-taste")

# Global rules storage
rules: dict[str, TasteRule] = {}

def _load_rules(rules_dir: Path | None = None) -> None:
    """Load all taste rules from the rules directory."""
    global rules
    if rules_dir is None:
        # Try package data first using importlib.resources
        try:
            package_data_path = files("high_taste") / "data" / "rules"
            with as_file(package_data_path) as rules_path:
                rules = load_all_rules(rules_path)
                logger.info(f"Loaded {len(rules)} taste rules from package data")
                return
        except Exception as e:
            logger.warning(f"Package data access failed: {e}")
            # Fallback to development location if package data access fails
            rules_dir = Path(__file__).parent.parent.parent / "rules"
    
    try:
        rules = load_all_rules(rules_dir)
        logger.info(f"Loaded {len(rules)} taste rules from {rules_dir}")
    except Exception as e:
        logger.error(f"Failed to load rules from {rules_dir}: {e}")
        rules = {}


@mcp.tool()
def taste_check(files: list[dict[str, str]]) -> dict[str, Any]:
    """Check Python files against taste rules.
    
    Args:
        files: List of file objects with 'path' and 'content' keys
        
    Returns:
        Dictionary with violations and summary information
    """
    try:
        # Validate and parse input
        input_data = TasteCheckInput(
            files=[FileContent(path=f["path"], content=f["content"]) for f in files]
        )
        
        result = _check_files(input_data)
        return result.model_dump()
        
    except Exception as e:
        logger.error(f"Error in taste_check: {e}")
        return {
            "error": str(e),
            "violations": [],
            "total_files_checked": 0,
            "total_violations": 0,
            "summary_by_rule": {}
        }


@mcp.tool()
def taste_acquire(diffs: list[str]) -> dict[str, Any]:
    """Learn new taste rules from code diffs.
    
    Args:
        diffs: List of git diff strings showing before/after changes
        
    Returns:
        Dictionary with information about rules created or existing coverage
    """
    # TODO: Implement diff analysis and rule learning
    return {
        "message": "taste_acquire is not yet implemented",
        "new_rules_created": 0,
        "existing_rules_matched": [],
        "analysis_summary": "Diff analysis coming in future release"
    }


def _check_files(input_data: TasteCheckInput) -> TasteCheckResult:
    """Check files against taste rules."""
    all_violations: list[TasteViolation] = []
    summary_by_rule: dict[str, int] = {}
    
    for file_content in input_data.files:
        if not file_content.path.endswith(".py"):
            continue  # Only check Python files for now
        
        violations = _check_single_file(file_content)
        all_violations.extend(violations)
        
        # Update summary
        for violation in violations:
            summary_by_rule[violation.rule_id] = summary_by_rule.get(violation.rule_id, 0) + 1
    
    return TasteCheckResult(
        violations=all_violations,
        total_files_checked=len([f for f in input_data.files if f.path.endswith(".py")]),
        total_violations=len(all_violations),
        summary_by_rule=summary_by_rule
    )


def _check_single_file(file_content: FileContent) -> list[TasteViolation]:
    """Check a single file against taste rules."""
    violations: list[TasteViolation] = []
    
    try:
        # Use AST analyzer to find violations
        ast_violations = analyze_python_code(file_content.content)
        
        for violation in ast_violations:
            rule = rules.get(violation.rule_id)
            if rule:
                violations.append(TasteViolation(
                    rule_id=violation.rule_id,
                    rule_title=rule.title,
                    file_path=file_content.path,
                    line_number=violation.line_number,
                    column=violation.column,
                    message=violation.message,
                    severity=violation.severity,
                    category=rule.category
                ))
            else:
                # Handle cases where rule isn't loaded
                violations.append(TasteViolation(
                    rule_id=violation.rule_id,
                    rule_title=f"Rule {violation.rule_id}",
                    file_path=file_content.path,
                    line_number=violation.line_number,
                    column=violation.column,
                    message=violation.message,
                    severity=violation.severity,
                    category="Unknown"
                ))
    
    except Exception as e:
        logger.error(f"Error analyzing file {file_content.path}: {e}")
        # Add a violation for the analysis error
        violations.append(TasteViolation(
            rule_id="ERROR",
            rule_title="Analysis Error",
            file_path=file_content.path,
            line_number=1,
            column=0,
            message=f"Failed to analyze file: {e}",
            severity="Error",
            category="System"
        ))
    
    return violations


# Initialize rules when module is loaded
_load_rules()


def check_files_standalone(files: list[dict[str, str]]) -> dict[str, Any]:
    """Standalone function for checking files without MCP."""
    try:
        return taste_check(files)
    except Exception as e:
        logger.error(f"Error in standalone check: {e}")
        return {
            "error": str(e),
            "violations": [],
            "total_files_checked": 0,
            "total_violations": 0,
            "summary_by_rule": {}
        }


def create_server() -> FastMCP:
    """Create and return a configured Taste MCP server."""
    return mcp


if __name__ == "__main__":
    # Demo: Test the server functionality
    
    # Test taste_check with sample code
    sample_files = [
        {
            "path": "test.py",
            "content": """
def bad_function():
    try:
        return process_data()
    except Exception:
        return 0  # Defensive return
"""
        }
    ]
    
    result = check_files_standalone(sample_files)
    print("Taste check result:")
    print(json.dumps(result, indent=2))
    
    # To run as MCP server: mcp.run(transport="stdio")
    print("\nTo run as MCP server, call: mcp.run(transport='stdio')")
