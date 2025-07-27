"""CLI entry point for Taste MCP server."""

import click
from loguru import logger

from taste.server import mcp


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug logging")
def main(debug: bool) -> None:
    """Taste - MCP server for enforcing coding style decisions."""
    if debug:
        logger.enable("taste")
    else:
        logger.disable("taste")


@main.command()
def serve() -> None:
    """Start the MCP server."""
    click.echo("Starting Taste MCP server...")
    mcp.run(transport="stdio")


@main.command()
@click.argument("files", nargs=-1, type=click.Path(exists=True))
def check(files: tuple[str, ...]) -> None:
    """Check Python files against taste rules (standalone mode)."""
    if not files:
        click.echo("No files provided. Use 'taste check file1.py file2.py'")
        return
    
    from pathlib import Path

    from taste.server import check_files_standalone
    
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
def rules() -> None:
    """List all available taste rules."""
    from pathlib import Path

    from taste.rules.parser import load_all_rules
    
    rules_dir = Path(__file__).parent.parent.parent / "rules"
    try:
        rules = load_all_rules(rules_dir)
        
        click.echo(f"Available taste rules ({len(rules)} total):")
        click.echo()
        
        for _rule_id, rule in sorted(rules.items()):
            severity_icon = "🔴" if rule.severity == "Error" else "🟡"
            click.echo(f"{severity_icon} Rule {rule.id}: {rule.title}")
            click.echo(f"   Category: {rule.category} | Severity: {rule.severity}")
            click.echo(f"   {rule.rationale}")
            click.echo()
    
    except Exception as e:
        click.echo(f"Error loading rules: {e}", err=True)


if __name__ == "__main__":
    main()
