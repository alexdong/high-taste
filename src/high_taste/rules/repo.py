import re
from pathlib import Path

import yaml

from .llm import Rule


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


def save_rule_to_file(rule: Rule) -> Path:
    """Save generated rule to YAML file."""
    # Determine file location from rule category
    category_dir = determine_rule_directory(rule.category)
    number = get_next_rule_number(category_dir)
    
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
        ],
    }
    with file_path.open("w", encoding="utf-8") as f:
        yaml.dump(rule_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    return file_path
