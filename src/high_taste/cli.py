"""CLI entry point for High-Taste MCP server."""

from pathlib import Path

import click
from loguru import logger

try:
    from importlib.resources import as_file, files
except ImportError:
    from importlib_resources import as_file, files  # Python < 3.9 fallback

from high_taste.rules.parser import load_all_rules
from high_taste.server import check_files_standalone, mcp

# Disable loguru by default for cleaner CLI output
logger.disable("high_taste")


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug logging")
def main(*, debug: bool) -> None:
    """High-Taste - MCP server for enforcing coding style decisions."""
    if debug:
        logger.enable("high_taste")


@main.command()
def serve() -> None:
    """Start the MCP server."""
    click.echo("Starting High-Taste MCP server...")
    mcp.run(transport="stdio")


def _check_files_impl(files: tuple[str, ...]) -> None:
    """Implementation for file checking."""
    file_contents = []
    for file_path in files:
        path = Path(file_path)
        if path.suffix == ".py":
            try:
                content = path.read_text(encoding="utf-8")
                file_contents.append({"path": str(path), "content": content})
            except Exception as e:
                click.echo(f"Error reading {file_path}: {e}", err=True)
        else:
            click.echo(f"Skipping non-Python file: {file_path}")
    
    if not file_contents:
        click.echo("No Python files to check.")
        return
    
    result = check_files_standalone(file_contents)
    
    # Display results
    if result["total_violations"] == 0:
        click.echo(f"✅ No violations found in {result['total_files_checked']} files")
    else:
        click.echo(f"❌ Found {result['total_violations']} violations in {result['total_files_checked']} files")
        click.echo()
        
        for violation in result["violations"]:
            severity_icon = "🔴" if violation["severity"] == "Error" else "🟡"
            click.echo(f"{severity_icon} {violation['file_path']}:{violation['line_number']}:{violation['column']}")
            click.echo(f"   Rule {violation['rule_id']}: {violation['message']}")
            click.echo(f"   Category: {violation['category']}")
            click.echo()
        
        # Show summary
        click.echo("Summary by rule:")
        for rule_id, count in result["summary_by_rule"].items():
            click.echo(f"  Rule {rule_id}: {count} violations")


@main.command()
@click.argument("files", nargs=-1, type=click.Path(exists=True))
def check(files: tuple[str, ...]) -> None:
    """Check Python files against taste rules (standalone mode)."""
    if not files:
        click.echo("No files provided. Use 'high-taste check file1.py file2.py'")
        return
    
    _check_files_impl(files)


@main.command()
def rules() -> None:
    """List all available taste rules."""
    taste_rules = {}
    
    # Try package data first using importlib.resources
    try:
        package_data_path = files("high_taste") / "data" / "rules"
        with as_file(package_data_path) as rules_path:
            taste_rules = load_all_rules(rules_path)
            click.echo(f"Available taste rules ({len(taste_rules)} total):")
            click.echo()
            
            for _rule_id, rule in sorted(taste_rules.items()):
                severity_icon = "🔴" if rule.severity == "Error" else "🟡"
                click.echo(f"{severity_icon} Rule {rule.id}: {rule.title}")
                click.echo(f"   Category: {rule.category} | Severity: {rule.severity}")
                click.echo(f"   {rule.rationale}")
                click.echo()
            return
    except Exception as e:
        click.echo(f"Package data access failed: {e}", err=True)
        # Fall through to try development location
    
    # Fallback to development location
    try:
        rules_dir = Path(__file__).parent.parent.parent / "rules"
        taste_rules = load_all_rules(rules_dir)
        
        click.echo(f"Available taste rules ({len(taste_rules)} total):")
        click.echo()
        
        for _rule_id, rule in sorted(taste_rules.items()):
            severity_icon = "🔴" if rule.severity == "Error" else "🟡"
            click.echo(f"{severity_icon} Rule {rule.id}: {rule.title}")
            click.echo(f"   Category: {rule.category} | Severity: {rule.severity}")
            click.echo(f"   {rule.rationale}")
            click.echo()
    
    except Exception as e:
        click.echo(f"Error loading rules from {rules_dir}: {e}", err=True)


if __name__ == "__main__":
    main()
