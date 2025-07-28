#!/usr/bin/env python3
"""
Convert markdown rule files to YAML format using Pydantic AI with Sonnet-4.
"""

import argparse
import asyncio
import re
from pathlib import Path

from high_taste.utils import serialise_yaml

from .llm import agent_run
from .prompt import RULE_DETAILS_PROMPT


def get_conversion_prompt(md_content: str) -> str:
    """Generate the user prompt for converting a markdown rule to YAML format."""
    return f"""
${RULE_DETAILS_PROMPT}

Your task is to convert this markdown rule file into comprehensive YAML format with extensive examples.
Convert this markdown rule to the specified YAML format:

{md_content}
"""



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
        prompt = get_conversion_prompt(md_content)
        rule = await agent_run(prompt)

        # Convert to YAML format
        # Clean up title for key names
        clean_title = re.sub(r"[^a-zA-Z0-9_]", "_", rule.title.lower()).strip("_")
        while "__" in clean_title:
            clean_title = clean_title.replace("__", "_")

        yaml_data = {
            "title": rule.title,
            "id": rule.id,
            "description": rule.description,
            "problems_": rule.problems,
            "solutions": rule.solutions,
            "examples": [
                {
                    "scenario": example.scenario,
                    "before": example.before,
                    "after": example.after,
                }
                for example in rule.examples
            ],
        }
        # Create output path
        yaml_file_path = md_file_path.parent / f"{rule_id}.yaml"
        serialise_yaml(yaml_data, yaml_file_path)
        print(f"✓ Converted {rule_id} to {yaml_file_path}")
        return True

    except Exception as e:
        print(f"Error converting {md_file_path}: {e}")
        return False


async def main() -> None:
    """Main function to convert all markdown rule files."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Convert markdown rule files to YAML format"
    )
    parser.add_argument(
        "--first-only",
        action="store_true",
        help="Stop after converting the first markdown file (useful for testing)",
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
