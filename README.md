# Taste

An MCP (Model Context Protocol) server that enforces coding style decisions based on taste and convention rather than semantic correctness. Following the "Effective C++" tradition, Taste provides rules with examples and rationale to maintain consistent, readable code.

## Overview

Taste helps development teams maintain code quality by:
- **Checking new code** against established taste rules (like a linter for style preferences)
- **Learning from expert refactoring** by analyzing before/after diffs to create new rules
- **Integrating seamlessly** with Claude Code and VS Code via MCP

Unlike traditional linters that focus on syntax and semantics, Taste enforces subjective but important style decisions that make code more maintainable, readable, and consistent with team preferences.

## Core Functions

### `taste_check`
Analyzes Python files against existing taste rules and reports violations with specific line numbers and rule references.

**Input**: List of file contents (Python code)
**Output**: Linting-style errors with rule numbers and descriptions

### `taste_acquire` 
Learns new taste rules by analyzing diffs where experienced programmers have refactored code originally written by junior developers or AI.

**Input**: Set of git diffs showing before/after code changes
**Output**: New rules created or confirmation that existing rules already cover the patterns

## Implementation Plan

### Phase 1: Core Architecture
1. **Rule System Design**
   - Create `rules/` directory with markdown files (one rule per file)
   - Implement rule parser to extract patterns, examples, and metadata
   - Design rule matching engine using AST analysis for semantic patterns
   - Create rule numbering/ID system for references

2. **MCP Server Foundation**
   - Set up MCP server infrastructure with proper protocol handling
   - Implement `taste_check` function with file content analysis
   - Implement `taste_acquire` function with diff analysis
   - Create standardized JSON output formats for both functions

### Phase 2: Pattern Recognition
3. **taste_check Implementation**
   - Build AST-based pattern matcher for Python code structures
   - Implement rule violation detection with line number reporting
   - Create rule severity system (error, warning, suggestion)
   - Add support for incremental checking (only changed lines)

4. **taste_acquire Implementation**
   - Develop diff parser to extract before/after code patterns
   - Create pattern generalization algorithm (specific → general rules)
   - Implement rule conflict detection and resolution
   - Build automatic rule description generation

### Phase 3: Integration
5. **IDE Integration**
   - Configure MCP server for Claude Code integration
   - Set up VS Code MCP client configuration
   - Create configuration files for both environments
   - Test end-to-end workflow in both IDEs

6. **Rule Management**
   - Implement rule CRUD operations (create, read, update, disable)
   - Add rule versioning and change tracking
   - Create rule validation and testing framework
   - Build rule export/import functionality

### Phase 4: Advanced Features
7. **Intelligence Enhancements**
   - Add machine learning for better pattern recognition
   - Implement context-aware rule application
   - Create rule recommendation system
   - Add support for custom rule templates

8. **Monitoring and Metrics**
   - Track rule violation frequency and trends
   - Measure rule effectiveness and adoption
   - Create dashboard for team rule compliance
   - Add automated rule quality assessment

## Project Structure

```
./
├── src/
│   ├── taste/              # Main MCP server code
│   │   ├── server.py       # MCP server implementation
│   │   ├── rules/          # Rule management and matching
│   │   ├── parsers/        # AST and diff parsing
│   │   └── utils/          # Helper functions
├── rules/                  # Taste rules (markdown files)
│   ├── 001-dynamic-discovery.md
│   ├── 002-explicit-imports.md
│   └── ...
├── tests/                  # Test files
├── examples/               # Example configurations and rules
├── docs/                   # Documentation
└── configs/                # MCP client configurations
    ├── claude-code.json
    └── vscode.json
```