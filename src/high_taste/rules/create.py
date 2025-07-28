"""Create new high-taste rules from GitHub commit analysis."""

import traceback
from pathlib import Path

import click

from high_taste.utils.git_commit import (
    GitHubCommit,
    fetch_commit_data,
    parse_github_url,
)

from .llm import Rule, agent_run
from .prompt import RULE_DETAILS_PROMPT
from .repo import (
    determine_rule_directory,
    generate_rule_id,
    get_next_rule_number,
    save_rule_to_file,
)


class GeneratedRule(Rule):
    category: str


def create_analysis_prompt(commit: GitHubCommit) -> str:
    """Create prompt for analyzing commit and generating rule."""
    return f"""
${RULE_DETAILS_PROMPT}

Given a git diff showing before/after changes, identify if there's a clear style improvement pattern that could be generalized into a coding rule.

Focus on:
- Code organization and structure improvements
- Naming convention upgrades
- Function/class design enhancements
- Error handling improvements
- Performance optimizations
- Readability enhancements

Generate a rule ONLY if there's a clear, generalizable pattern that represents good taste rather than just bug fixes.

For the category, choose from: boundaries, concurrency, control_flow, functions, naming, performance, refactoring, structure, style, testing

COMMIT MESSAGE:
{commit.message}

COMMIT URL:
{commit.url}

DIFF:
{commit.diff}

"""


async def create_rule_from_commit(github_url: str) -> Path | None:
    """Create a new rule by analyzing a GitHub commit.

    Args:
        github_url: GitHub commit URL

    Returns:
        Path to created rule file, or None if no rule was generated
    """
    # Parse GitHub URL
    owner, repo, commit_hash = parse_github_url(github_url)

    # Fetch commit data
    commit = await fetch_commit_data(owner, repo, commit_hash)

    # Analyze with AI
    prompt = create_analysis_prompt(commit)
    rule = await agent_run(prompt)

    # Check if a rule was actually generated
    if not rule.title.strip():
        return None

    # Update rule ID with correct number
    category_dir = determine_rule_directory(rule.category)
    number = get_next_rule_number(category_dir)
    rule.id = generate_rule_id(rule.category, number)

    # Save to file
    return save_rule_to_file(rule)


@click.command()
@click.argument("github_url")
@click.option("--debug", is_flag=True, help="Enable debug logging")
def learn(github_url: str, debug: bool) -> None:
    """Learn a new high-taste rule from a GitHub commit.

    Analyzes a GitHub commit diff to extract coding style patterns
    and creates a new rule if a clear high-taste improvement is detected.

    Example: python -m high_taste.rules.create https://github.com/user/repo/commit/abc123
    """

    async def _learn() -> None:
        try:
            click.echo(f"🔍 Analyzing commit: {github_url}")
            rule_path = await create_rule_from_commit(github_url)

            if rule_path:
                click.echo(f"✅ New rule created: {rule_path}")
                click.echo("💡 Rule has been saved and can be used for checking code")
            else:
                click.echo("❌ No clear high-taste pattern detected in this commit")
                click.echo("💡 Try a commit that shows clear style improvements")
        except Exception as e:
            if debug:
                traceback.print_exc()
            click.echo(f"❌ Error analyzing commit: {e}", err=True)

    asyncio.run(_learn())


if __name__ == "__main__":
    import asyncio

    import click

    learn()
