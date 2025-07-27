"""Rule parser for taste markdown files."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple

from loguru import logger


class RuleExample(NamedTuple):
    """Code example showing bad vs good patterns."""

    label: str  # "Bad" or "Good"
    description: str
    code: str


@dataclass(frozen=True)
class TasteRule:
    """A single taste rule with metadata and examples."""

    id: str
    title: str
    category: str
    severity: str
    rationale: str
    problem: str
    solution: str
    why_matters: str
    examples: list[RuleExample]
    ast_patterns: list[str]
    related_rules: list[str]

    def __str__(self) -> str:
        return f"Rule {self.id}: {self.title}"


def _extract_section_content(content: str, section_name: str) -> str:
    """Extract content from a markdown section."""
    pattern = rf"^## {re.escape(section_name)}\s*$(.*?)(?=^## |\Z)"
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ""


def _extract_code_examples(content: str) -> list[RuleExample]:
    """Extract code examples from the Examples section."""
    examples_section = _extract_section_content(content, "Examples")
    if not examples_section:
        return []

    examples = []

    # Pattern to match ### Bad: description or ### Good: description
    example_pattern = r"^### (Bad|Good): (.+?)$\s*```python\s*(.*?)^```"
    matches = re.finditer(example_pattern, examples_section, re.MULTILINE | re.DOTALL)

    for match in matches:
        label = match.group(1)
        description = match.group(2).strip()
        code = match.group(3).strip()
        examples.append(RuleExample(label, description, code))

    return examples


def _extract_ast_patterns(content: str) -> list[str]:
    """Extract AST patterns from the rule content."""
    ast_section = _extract_section_content(content, "AST Patterns to Detect")
    if not ast_section:
        return []

    # Extract bullet points (lines starting with -)
    patterns = []
    for raw_line in ast_section.split("\n"):
        line = raw_line.strip()
        if line.startswith("- "):
            patterns.append(line[2:].strip())

    return patterns


def _extract_related_rules(content: str) -> list[str]:
    """Extract related rule references."""
    related_section = _extract_section_content(content, "Related Rules")
    if not related_section:
        return []

    # Extract rule references like "Rule 001" or "Rule 003"
    rule_pattern = r"Rule (\d+)"
    matches = re.findall(rule_pattern, related_section)
    return [f"{int(match):03d}" for match in matches]


def _extract_metadata(content: str) -> dict[str, str]:
    """Extract metadata from the rule header."""
    metadata = {}

    # Extract from lines like **Category:** Error Handling
    metadata_search_limit = 10
    for raw_line in content.split("\n")[
        :metadata_search_limit
    ]:  # Only check first few lines
        line = raw_line.strip()
        if line.startswith("**") and ":**" in line:
            # Split on :** and clean up
            parts = line.split(":**", 1)
            expected_parts = 2
            if len(parts) == expected_parts:
                key = parts[0].replace("**", "").strip().lower().replace(" ", "_")
                value = parts[1].strip()
                metadata[key] = value

    return metadata


def parse_rule_file(file_path: Path) -> TasteRule:
    """Parse a single rule markdown file into a TasteRule object."""
    assert file_path.exists(), f"Rule file does not exist: {file_path}"
    assert file_path.suffix == ".md", f"Rule file must be markdown: {file_path}"

    content = file_path.read_text(encoding="utf-8")

    # Extract rule ID from filename (e.g., 001-assertions-over-exceptions.md -> 001)
    rule_id = file_path.stem.split("-")[0]
    assert rule_id.isdigit(), f"Rule file must start with number: {file_path}"

    # Extract title from first line (# Rule 001: Title)
    first_line = content.split("\n")[0]
    title_match = re.match(r"^# Rule \d+: (.+)$", first_line)
    title = title_match.group(1) if title_match else file_path.stem

    # Extract metadata
    metadata = _extract_metadata(content)

    # Extract main sections
    problem = _extract_section_content(content, "Problem")
    solution = _extract_section_content(content, "Solution")
    why_matters = _extract_section_content(content, "Why This Matters")

    # Extract structured data
    examples = _extract_code_examples(content)
    ast_patterns = _extract_ast_patterns(content)
    related_rules = _extract_related_rules(content)

    logger.debug(f"Parsed rule {rule_id}: {title}")

    return TasteRule(
        id=rule_id,
        title=title,
        category=metadata.get("category", "Unknown"),
        severity=metadata.get("severity", "Warning"),
        rationale=metadata.get("rationale", ""),
        problem=problem,
        solution=solution,
        why_matters=why_matters,
        examples=examples,
        ast_patterns=ast_patterns,
        related_rules=related_rules,
    )


def load_all_rules(rules_dir: Path) -> dict[str, TasteRule]:
    """Load all taste rules from the rules directory."""
    assert rules_dir.exists(), f"Rules directory does not exist: {rules_dir}"

    rules = {}
    rule_files = list(rules_dir.glob("*.md"))

    assert rule_files, f"No rule files found in {rules_dir}"

    for file_path in sorted(rule_files):
        try:
            rule = parse_rule_file(file_path)
            rules[rule.id] = rule
            logger.info(f"Loaded rule {rule.id}: {rule.title}")
        except Exception as e:
            logger.error(f"Failed to parse rule file {file_path}: {e}")
            raise

    logger.info(f"Loaded {len(rules)} taste rules")
    return rules


if __name__ == "__main__":
    # Demo: Parse a single rule file
    rules_dir = Path(__file__).parent.parent.parent.parent / "rules"
    test_file = rules_dir / "001-assertions-over-exceptions.md"

    if test_file.exists():
        rule = parse_rule_file(test_file)
        print(f"Rule: {rule}")
        print(f"Examples: {len(rule.examples)}")
        print(f"AST Patterns: {rule.ast_patterns}")
    else:
        print(f"Test file not found: {test_file}")
