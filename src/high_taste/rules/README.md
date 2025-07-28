# Rule Conversion Script

This directory contains `prep.py`, a script that converts markdown rule files to YAML format using Pydantic AI with Claude Sonnet-4.

## Setup

1. Install dependencies:
   ```bash
   uv add pydantic-ai PyYAML
   ```

2. Set your Anthropic API key:
   ```bash
   export ANTHROPIC_API_KEY="your_api_key_here"
   ```

## Usage

Run the conversion script from the project root:

```bash
# Set your API key
export ANTHROPIC_API_KEY="your_api_key_here"

# Convert all rules (run from project root)
uv run python src/high_taste/rules/prep.py

# Check output
ls rules_yaml/
cat rules_yaml/bnd001.yaml
```

## What it does

The script:

1. **Scans** all `./rules/**/*.md` files
2. **Skips** deterministic rules that can be implemented with tree-sitter (formatting, spacing, etc.)
3. **Converts** remaining rules to YAML format with:
   - Rule title and ID
   - Comprehensive description
   - Problems with bad practices
   - Solutions and best practices
   - **25 diverse Python examples** covering:
     - Web development (FastAPI, Flask, Django)
     - Data science (pandas, numpy)
     - Testing (pytest)
     - CLI applications
     - Database operations
     - File I/O
     - API clients
     - Configuration management
     - Async/await patterns
     - And more...

4. **Outputs** YAML files to `./rules_yaml/` directory

## Skipped Rules

The following rule types are automatically skipped because they can be implemented deterministically with tree-sitter:

- **Formatting**: FMT003, FMT004, FMT005
- **Comments**: COM001-COM005
- **Style**: STYLE001, STYLE002
- **Simple naming**: MN005, MN010
- **Simple structural**: FUNC001, FUNC003, FUNC004
- **Simple control flow**: CTRL003, CTRL004
- **Constants**: CONST003

## Output Format

Each YAML file follows this structure:

```yaml
title: [Rule title]
id: [Rule ID]
description: |-
  [Multi-line description]
problems_with_[practice]:
  - [List of problems]
solutions_for_[practice]:
  - [List of solutions]
examples:
  - scenario: [Description]
    before: |
      ```python
      [Bad code]
      ```
    after: |
      ```python
      [Good code]
      ```
  # ... 24 more examples
```

## Expected Output

The script will:
1. Scan 164 markdown files in `./rules/`
2. Skip ~20 deterministic rules (formatting, spacing, etc.)
3. Convert ~144 semantic rules to YAML
4. Generate comprehensive examples for each rule
5. Output files to `./rules_yaml/` directory

Example conversion output:
```
Found 164 markdown rule files
Skipping deterministic rule FMT003 (./rules/style/008-fmt003.md)
Converting rule BND001 from ./rules/boundaries/001-bnd001.md
Successfully converted BND001 to ./rules_yaml/bnd001.yaml
...
Conversion complete:
  Successfully converted: 144
  Skipped (deterministic): 20
  Failed: 0
  Output directory: ./rules_yaml/
```