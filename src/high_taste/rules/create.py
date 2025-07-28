"""Create new high-taste rules from GitHub commit analysis."""

import os
import re
from pathlib import Path

import click
import httpx
import yaml
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel

from .llm import RuleExample, Rule
from .prompt import SYSTEM_PROMPT, RULE_DETAILS_PROMPT

from high_taste.utils import serialise_yaml

class GitHubCommit(BaseModel):
    """GitHub commit data."""
    message: str
    diff: str
    url: str

class GeneratedRule(Rule):
    category: str

def parse_github_url(url: str) -> tuple[str, str, str]:
    """Parse GitHub commit URL into owner, repo, commit_hash."""
    # Handle various GitHub URL formats
    patterns = [
        r"github\.com/([^/]+)/([^/]+)/commit/([a-f0-9]+)",
        r"github\.com/([^/]+)/([^/]+)/commits/([a-f0-9]+)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1), match.group(2), match.group(3)
    
    raise ValueError(f"Invalid GitHub commit URL: {url}")


async def fetch_commit_data(owner: str, repo: str, commit_hash: str) -> GitHubCommit:
    """Fetch commit data from GitHub API."""
    # Use GitHub API v3 for commit data
    base_url = "https://api.github.com"
    commit_url = f"{base_url}/repos/{owner}/{repo}/commits/{commit_hash}"
    
    headers = {}
    if github_token := os.getenv("GITHUB_TOKEN"):
        headers["Authorization"] = f"token {github_token}"
    
    async with httpx.AsyncClient() as client:
        # Fetch commit details
        response = await client.get(commit_url, headers=headers)
        response.raise_for_status()
        commit_data = response.json()
        
        # Fetch commit diff
        diff_response = await client.get(
            commit_url,
            headers={**headers, "Accept": "application/vnd.github.diff"}
        )
        diff_response.raise_for_status()
        
        return GitHubCommit(
            message=commit_data["commit"]["message"],
            diff=diff_response.text,
            url=f"https://github.com/{owner}/{repo}/commit/{commit_hash}"
        )


def get_commit_analysis_agent() -> Agent:
    """Create AI agent for analyzing commits and generating rules."""
    assert os.getenv("ANTHROPIC_API_KEY"), (
        "ANTHROPIC_API_KEY environment variable is required"
    )
    
    model = AnthropicModel("anthropic:claude-sonnet-4-latest")
    return Agent(
        model,
        result_type=GeneratedRule,
        system_prompt=SYSTEM_PROMPT,
    )


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


def determine_rule_directory(category: str) -> Path:
    """Determine the appropriate directory for a rule category."""
    rules_base = Path(__file__).parent.parent.parent.parent / "rules"
    return rules_base / category


def get_next_rule_number(category_dir: Path) -> int:
    """Get the next available rule number in a category."""
    if not category_dir.exists():
        return 1
    
    existing_files = list(category_dir.glob("*.yaml"))
    if not existing_files:
        return 1
    
    numbers = []
    for file in existing_files:
        match = re.match(r"(\d+)-", file.name)
        if match:
            numbers.append(int(match.group(1)))
    
    return max(numbers) + 1 if numbers else 1


def generate_rule_id(category: str, number: int) -> str:
    """Generate rule ID based on category and number."""
    category_prefixes = {
        "boundaries": "BND",
        "concurrency": "CON",
        "control_flow": "CTRL",
        "functions": "FUNC",
        "naming": "NAME",
        "performance": "PERF",
        "refactoring": "REF",
        "structure": "STRUCT",
        "style": "STYLE",
        "testing": "TEST",
    }
    
    prefix = category_prefixes.get(category, "MISC")
    return f"{prefix}{number:03d}"


def save_rule_to_file(rule: GeneratedRule, category_dir: Path, number: int) -> Path:
    """Save generated rule to YAML file."""
    category_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"{number:03d}-{rule.id.lower()}.yaml"
    file_path = category_dir / filename
    
    # Convert to YAML format
    rule_data = {
        "title": rule.title,
        "id": rule.id,
        "description": rule.description,
        "problems": rule.problems,
        "solutions": rule.solutions,
        "examples": [
            {
                "scenario": ex.scenario,
                "before": ex.before,
                "after": ex.after,
            }
            for ex in rule.examples
        ]
    }
    serialise_yaml(rule_data, file_path)
    return file_path


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
    agent = get_ai_agent(SYSTEM_PROMPT)
    prompt = create_analysis_prompt(commit)
    result = await agent.run(prompt)
    
    rule = result.data
    
    # Check if a rule was actually generated
    if not rule.title.strip():
        return None
    
    # Determine file location
    category_dir = determine_rule_directory(rule.category)
    number = get_next_rule_number(category_dir)
    
    # Update rule ID with correct number
    rule.id = generate_rule_id(rule.category, number)
    
    # Save to file
    return save_rule_to_file(rule, category_dir, number)


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
                import traceback
                traceback.print_exc()
            click.echo(f"❌ Error analyzing commit: {e}", err=True)
    
    asyncio.run(_learn())


if __name__ == "__main__":
    import asyncio

    import click
    
    learn()
