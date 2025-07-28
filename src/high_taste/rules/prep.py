#!/usr/bin/env python3
"""
Convert markdown rule files to YAML format using Pydantic AI with Sonnet-4.
"""

import argparse
import asyncio
import os
import re
import sys
from pathlib import Path

try:
    from pydantic_ai import Agent
    from pydantic_ai.models.anthropic import AnthropicModel
except ImportError:
    print("Error: pydantic-ai not found. Please install it first: pip install pydantic-ai")
    sys.exit(1)

from pydantic import BaseModel
from pydantic_ai.result import RunResult


class RuleExample(BaseModel):
    scenario: str
    before: str
    after: str


class ConvertedRule(BaseModel):
    title: str
    id: str
    description: str
    problems_with_bad_practice: list[str]
    solutions_for_good_practice: list[str]
    examples: list[RuleExample]


SYSTEM_PROMPT = """You are an expert Python developer and technical writer specializing in code quality and best practices. You have deep experience with open source Python projects and understand real-world development challenges. Your writing is clear, practical, and actionable."""


def get_conversion_prompt(md_content: str) -> str:
    """Generate the user prompt for converting a markdown rule to YAML format."""
    return f"""
Convert this markdown rule to the specified YAML format:

{md_content}

Your task is to convert this markdown rule file into comprehensive YAML format with extensive examples.

Requirements:
1. Extract the rule title and ID
2. Write a comprehensive description explaining what this rule is about
3. List specific problems with the bad practice (what goes wrong when this rule is violated)
4. List specific solutions and best practices
5. Create exactly 25 diverse Python examples covering different scenarios:
   - Web development (FastAPI, Flask, Django routes, middleware, etc.)
   - Data science (pandas operations, numpy arrays, data processing)
   - Testing (pytest fixtures, test organization, mocking)
   - CLI applications (argument parsing, user interaction)
   - Database operations (queries, transactions, ORM usage)
   - File and I/O operations
   - API clients and HTTP requests
   - Configuration and settings management
   - Logging and error handling
   - Async/await patterns
   - Class design and inheritance
   - Function composition and decorators
   - Package and module organization
   - Performance optimization
   - Security considerations

Key requirements:
- Create exactly 25 diverse examples that cover common scenarios in open source Python projects
- Use ONLY Python code in all examples
- Make examples realistic and practical, not toy examples
- Cover different domains: web development, data science, CLI tools, APIs, testing, etc.
- Ensure examples demonstrate the rule clearly with meaningful before/after code
- Write clear, actionable problem descriptions and solutions
- Focus on real-world scenarios developers encounter daily

For the problems_with_bad_practice and solutions_for_good_practice sections:
- Be specific and actionable
- Explain the "why" behind the rule
- Include consequences of not following the rule
- Provide concrete steps to implement the solution

Each example should:
- Have a clear scenario description
- Show realistic before/after code (not toy examples)
- Demonstrate the rule violation and its fix
- Be relevant to real open source Python projects
- Cover different complexity levels (simple to advanced)

Make the problems and solutions sections specific and actionable, explaining the real-world impact.
"""

async def convert_rule_with_ai(agent: Agent, prompt: str) -> RunResult[Rule]:
    """Convert a rule using the AI agent."""
    return await agent.run(
        prompt,
        settings=ModelSettings(temperature=0.2, max_tokens=50000)
    )


def get_ai_agent(system_prompt: str) -> Agent:
    """Initialize and return the AI agent."""
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        msg = "ANTHROPIC_API_KEY environment variable is required"
        raise ValueError(msg)

    model = AnthropicModel("claude-3-5-sonnet-20241022")
    return Agent(
        model,
        output_type=ConvertedRule,
        system_prompt=system_prompt,
    )


async def convert_rule_with_ai(agent: Agent, prompt: str) -> "RunResult[ConvertedRule]":
    """Convert a rule using the AI agent."""
    return await agent.run(prompt)




def extract_rule_info(md_content: str) -> dict[str, str]:  # noqa: PLR0912
    """Extract basic rule information from markdown content."""
    lines = md_content.strip().split("\n")

    # Extract title (first line or first # header)
    title = ""
    if lines and lines[0].startswith("#"):
        title = lines[0].lstrip("#").strip()
    elif lines:
        title = lines[0].strip()

    # Extract ID from **ID**: pattern
    rule_id = ""
    for line in lines:
        if line.startswith("**ID**:"):
            rule_id = line.split(":", 1)[1].strip()
            break

    # Extract category
    category = ""
    for line in lines:
        if line.startswith("**Category**:"):
            category = line.split(":", 1)[1].strip()
            break

    # Extract before/after examples
    before_code = ""
    after_code = ""
    in_before = False
    in_after = False

    for i, line in enumerate(lines):
        if line.strip() == "## Before":
            in_before = True
            continue
        if line.strip() == "## After":
            in_before = False
            in_after = True
            continue
        if line.startswith("##"):
            in_before = False
            in_after = False
            continue

        if in_before and line.strip().startswith("```python"):
            # Collect code until closing ```
            j = i + 1
            code_lines = []
            while j < len(lines) and not lines[j].strip().startswith("```"):
                code_lines.append(lines[j])
                j += 1
            before_code = "\n".join(code_lines)

        if in_after and line.strip().startswith("```python"):
            # Collect code until closing ```
            j = i + 1
            code_lines = []
            while j < len(lines) and not lines[j].strip().startswith("```"):
                code_lines.append(lines[j])
                j += 1
            after_code = "\n".join(code_lines)

    return {
        "title": title,
        "id": rule_id,
        "category": category,
        "before_code": before_code,
        "after_code": after_code,
        "full_content": md_content,
    }


async def convert_rule(md_file_path: Path) -> bool:
    """Convert a single markdown rule file to YAML format."""
    try:
        # Read the markdown file
        md_content = md_file_path.read_text(encoding="utf-8")

        # Extract basic rule info
        rule_info = extract_rule_info(md_content)
        rule_id = rule_info.get("id", "")

        if not rule_id:
            print(f"Warning: Could not extract rule ID from {md_file_path}")
            return False

        print(f"Converting rule {rule_id} from {md_file_path}")

        # Get AI response
        agent = get_ai_agent(SYSTEM_PROMPT)
        prompt = get_conversion_prompt(md_content)
        result = await convert_rule_with_ai(agent, prompt)

        # Convert to YAML format
        # Clean up title for key names
        clean_title = re.sub(r"[^a-zA-Z0-9_]", "_", result.output.title.lower()).strip(
            "_"
        )
        while "__" in clean_title:
            clean_title = clean_title.replace("__", "_")

        yaml_data = {
            "title": result.output.title,
            "id": result.output.id,
            "description": result.output.description,
            "problems_": result.output.problems,
            "solutions": result.output.solutions,
            "examples": [
                {
                    "scenario": example.scenario,
                    "before": example.before,
                    "after": example.after,
                }
                for example in result.output.examples
            ],
        }
        serialise_yaml(yaml_data, yaml_file_path)
        print(f"✓ Converted {rule_id} to {yaml_file_path}")
        return True

    except Exception as e:
        print(f"Error converting {md_file_path}: {e}")
        return False


async def main() -> None:
    """Main function to convert all markdown rule files."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Convert markdown rule files to YAML format")
    parser.add_argument(
        "--first-only",
        action="store_true",
        help="Stop after converting the first markdown file (useful for testing)"
    )
    args = parser.parse_args()

    rules_dir = Path("./rules")

    if not rules_dir.exists():
        print(f"Error: Rules directory {rules_dir} not found")
        return

    # Find all markdown files
    md_files = list(rules_dir.rglob("*.md"))
    print(f"Found {len(md_files)} markdown rule files")
    
    if args.first_only:
        print("Running in test mode - will stop after first successful conversion")

    # Convert files
    successful = 0
    skipped = 0
    failed = 0

    for md_file in md_files:
        try:
            result = await convert_rule(md_file)
            if result:
                successful += 1
                if args.first_only:
                    print("\n✓ Test mode: Successfully converted first file. Stopping.")
                    break
            else:
                skipped += 1
        except Exception as e:
            print(f"Failed to convert {md_file}: {e}")
            failed += 1

    print("\nConversion complete:")
    print(f"  ✓ Successfully converted: {successful}")
    print(f"  - Skipped: {skipped}")
    print(f"  ✗ Failed: {failed}")
    if not args.first_only:
        print("  📁 Output files written alongside markdown files")


if __name__ == "__main__":
    asyncio.run(main())
