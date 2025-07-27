"""Tests for rule parser."""

import pytest
from pathlib import Path

from taste.rules.parser import parse_rule_file, load_all_rules, TasteRule


def test_parse_rule_file():
    """Test parsing a single rule file."""
    rules_dir = Path(__file__).parent.parent.parent.parent / "rules"
    test_file = rules_dir / "001-assertions-over-exceptions.md"
    
    assert test_file.exists(), f"Test rule file not found: {test_file}"
    
    rule = parse_rule_file(test_file)
    
    assert rule.id == "001"
    assert "Replace Defensive try/except with Assertions" in rule.title
    assert rule.category == "Error Handling"
    assert rule.severity == "Warning"
    assert rule.problem != ""
    assert rule.solution != ""
    assert len(rule.examples) >= 2  # Should have Bad and Good examples
    assert len(rule.ast_patterns) > 0
    
    # Check examples structure
    bad_example = next((ex for ex in rule.examples if ex.label == "Bad"), None)
    good_example = next((ex for ex in rule.examples if ex.label == "Good"), None)
    
    assert bad_example is not None, "Should have Bad example"
    assert good_example is not None, "Should have Good example"
    assert "try" in bad_example.code.lower()
    assert "assert" in good_example.code.lower()


def test_load_all_rules():
    """Test loading all rules from directory."""
    rules_dir = Path(__file__).parent.parent.parent.parent / "rules"
    
    assert rules_dir.exists(), f"Rules directory not found: {rules_dir}"
    
    rules = load_all_rules(rules_dir)
    
    assert len(rules) >= 6, f"Expected at least 6 rules, got {len(rules)}"
    assert "001" in rules
    assert "002" in rules
    
    # Verify rule structure
    rule_001 = rules["001"]
    assert isinstance(rule_001, TasteRule)
    assert rule_001.id == "001"
    assert rule_001.title != ""
    assert rule_001.category != ""


def test_rule_file_naming():
    """Test that rule files follow naming convention."""
    rules_dir = Path(__file__).parent.parent.parent.parent / "rules"
    rule_files = list(rules_dir.glob("*.md"))
    
    for file_path in rule_files:
        # Should start with 3 digits
        filename = file_path.stem
        assert filename[:3].isdigit(), f"Rule file should start with 3 digits: {file_path}"
        assert filename[3] == "-", f"Rule file should have dash after number: {file_path}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])