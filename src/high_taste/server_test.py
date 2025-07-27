"""Tests for MCP server implementation."""

import pytest
import asyncio
from pathlib import Path

from high_taste.server import FileContent, TasteCheckInput, check_files_standalone


@pytest.fixture
def taste_server():
    """Create a taste server for testing."""
    return TasteServer()


def test_server_initialization(taste_server):
    """Test that server initializes correctly."""
    assert taste_server.rules is not None
    assert len(taste_server.rules) > 0
    assert taste_server.server is not None


@pytest.mark.asyncio
async def test_taste_check_basic(taste_server):
    """Test basic taste_check functionality."""
    sample_files = [
        {
            "path": "test.py",
            "content": '''
def bad_function():
    try:
        return process_data()
    except Exception:
        return 0
'''
        }
    ]
    
    result = await taste_server.server.tool_handlers["taste_check"](sample_files)
    
    assert "violations" in result
    assert "total_files_checked" in result
    assert "total_violations" in result
    assert result["total_files_checked"] == 1
    assert result["total_violations"] > 0
    
    violations = result["violations"]
    assert len(violations) > 0
    
    # Check violation structure
    violation = violations[0]
    assert "rule_id" in violation
    assert "file_path" in violation
    assert "line_number" in violation
    assert "message" in violation
    assert violation["file_path"] == "test.py"


@pytest.mark.asyncio
async def test_taste_check_clean_code(taste_server):
    """Test taste_check with clean code."""
    sample_files = [
        {
            "path": "clean.py",
            "content": '''
def clean_function(data: dict) -> str:
    assert data, "Data cannot be empty"
    assert "key" in data, "Key must be present"
    
    return data["key"]
'''
        }
    ]
    
    result = await taste_server.server.tool_handlers["taste_check"](sample_files)
    
    assert result["total_files_checked"] == 1
    assert result["total_violations"] == 0
    assert len(result["violations"]) == 0


@pytest.mark.asyncio
async def test_taste_check_multiple_files(taste_server):
    """Test taste_check with multiple files."""
    sample_files = [
        {
            "path": "file1.py",
            "content": '''
def function1():
    try:
        return data["key"]
    except:
        return None
'''
        },
        {
            "path": "file2.py", 
            "content": '''
def function2():
    if a:
        if b:
            if c:
                if d:  # Deep nesting
                    return "nested"
'''
        }
    ]
    
    result = await taste_server.server.tool_handlers["taste_check"](sample_files)
    
    assert result["total_files_checked"] == 2
    assert result["total_violations"] > 0
    
    # Should have violations from both files
    file_paths = {v["file_path"] for v in result["violations"]}
    assert "file1.py" in file_paths
    assert "file2.py" in file_paths


@pytest.mark.asyncio
async def test_taste_check_non_python_files(taste_server):
    """Test that non-Python files are ignored."""
    sample_files = [
        {
            "path": "readme.md",
            "content": "# This is markdown"
        },
        {
            "path": "config.json",
            "content": '{"key": "value"}'
        }
    ]
    
    result = await taste_server.server.tool_handlers["taste_check"](sample_files)
    
    assert result["total_files_checked"] == 0
    assert result["total_violations"] == 0


@pytest.mark.asyncio
async def test_taste_check_syntax_error(taste_server):
    """Test handling of syntax errors."""
    sample_files = [
        {
            "path": "broken.py",
            "content": '''
def broken_function(
    # Missing closing parenthesis
'''
        }
    ]
    
    result = await taste_server.server.tool_handlers["taste_check"](sample_files)
    
    assert result["total_files_checked"] == 1
    assert result["total_violations"] > 0
    
    # Should have a syntax error violation
    syntax_violations = [v for v in result["violations"] if "syntax" in v["message"].lower()]
    assert len(syntax_violations) > 0


@pytest.mark.asyncio
async def test_taste_acquire_placeholder(taste_server):
    """Test that taste_acquire returns placeholder response."""
    diffs = ["diff --git a/file.py b/file.py\n+new code"]
    
    result = await taste_server.server.tool_handlers["taste_acquire"](diffs)
    
    assert "message" in result
    assert "not yet implemented" in result["message"]
    assert result["new_rules_created"] == 0


def test_check_files_directly():
    """Test the _check_files method directly."""
    taste_server = TasteServer()
    
    input_data = TasteCheckInput(files=[
        FileContent(path="test.py", content='''
def bad():
    FILES = ["a.json", "b.json", "c.json"]  # Hardcoded list
    return FILES[0], FILES[1]  # Tuple return
''')
    ])
    
    result = taste_server._check_files(input_data)
    
    assert result.total_files_checked == 1
    assert result.total_violations > 0
    assert len(result.summary_by_rule) > 0
    
    # Check that we got expected violations
    rule_ids = {v.rule_id for v in result.violations}
    assert "004" in rule_ids  # Hardcoded lists
    assert "005" in rule_ids  # Tuple returns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])