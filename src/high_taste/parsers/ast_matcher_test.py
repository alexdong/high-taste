"""Tests for AST pattern matcher."""

import pytest

from high_taste.parsers.ast_matcher import analyze_python_code, CodeViolation


def test_defensive_try_except():
    """Test detection of defensive try/except patterns."""
    code = '''
def bad_function():
    try:
        if data:
            return data["key"]
        return 0
    except Exception:
        return 0
'''
    violations = analyze_python_code(code)
    rule_001_violations = [v for v in violations if v.rule_id == "001"]
    assert len(rule_001_violations) > 0
    assert "defensive" in rule_001_violations[0].message.lower()


def test_repeated_file_loading():
    """Test detection of file loading in functions."""
    code = '''
def load_data():
    with open("data.json") as f:
        return json.load(f)
'''
    violations = analyze_python_code(code)
    rule_002_violations = [v for v in violations if v.rule_id == "002"]
    assert len(rule_002_violations) > 0
    assert "module level" in rule_002_violations[0].message.lower()


def test_deep_nesting():
    """Test detection of deeply nested if statements."""
    code = '''
def nested_function(a, b, c, d):
    if a:
        if b:
            if c:
                if d:  # 4 levels deep
                    return "too deep"
    return None
'''
    violations = analyze_python_code(code)
    rule_003_violations = [v for v in violations if v.rule_id == "003"]
    assert len(rule_003_violations) > 0
    assert "deep nesting" in rule_003_violations[0].message.lower()


def test_hardcoded_file_lists():
    """Test detection of hardcoded file lists."""
    code = '''
FILES = ["file1.json", "file2.json", "file3.json"]
'''
    violations = analyze_python_code(code)
    rule_004_violations = [v for v in violations if v.rule_id == "004"]
    assert len(rule_004_violations) > 0
    assert "dynamic discovery" in rule_004_violations[0].message.lower()


def test_tuple_returns():
    """Test detection of tuple returns that should be structured."""
    code = '''
def get_data():
    return "name", 42, True  # Mixed types suggest structured data
'''
    violations = analyze_python_code(code)
    rule_005_violations = [v for v in violations if v.rule_id == "005"]
    assert len(rule_005_violations) > 0
    assert "namedtuple" in rule_005_violations[0].message.lower()


def test_database_commit_order():
    """Test detection of commit before validation."""
    code = '''
def save_data(conn, cursor):
    cursor.execute("INSERT INTO table VALUES (?)", (data,))
    conn.commit()
    assert cursor.rowcount == 1
'''
    violations = analyze_python_code(code)
    rule_006_violations = [v for v in violations if v.rule_id == "006"]
    assert len(rule_006_violations) > 0
    assert "before commit" in rule_006_violations[0].message.lower()


def test_clean_code_no_violations():
    """Test that clean code produces no violations."""
    code = '''
def clean_function(data: dict) -> str:
    assert data, "Data cannot be empty"
    assert "key" in data, "Key must be present"
    
    return data["key"]
'''
    violations = analyze_python_code(code)
    assert len(violations) == 0


def test_syntax_error_handling():
    """Test handling of syntax errors."""
    code = '''
def broken_function(
    # Missing closing parenthesis
'''
    violations = analyze_python_code(code)
    syntax_violations = [v for v in violations if v.rule_id == "SYNTAX"]
    assert len(syntax_violations) > 0
    assert "syntax error" in syntax_violations[0].message.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])