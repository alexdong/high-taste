"""Prompts for converting markdown rules to YAML format."""

SYSTEM_PROMPT = """You are an expert Python developer and technical writer specializing in code quality and best practices. You have deep experience with open source Python projects and understand real-world development challenges. Your writing is clear, practical, and actionable."""

RULE_DETAILS_PROMPT = """
<YAMLRuleFileDefinition>
You are tasked with generating a YAML file that describes a Python coding best practice.

The YAML file should include:
1. Rule title and ID
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

Key requirements:
- Create exactly 25 diverse examples that cover common scenarios in open source Python projects
- Use ONLY Python code in all examples
- Make examples realistic and practical, not toy examples
- Cover different domains: web development, data science, CLI tools, APIs, testing, etc.
- Ensure examples demonstrate the rule clearly with meaningful before/after code
- Write clear, actionable problem descriptions and solutions
- Focus on real-world scenarios developers encounter daily

For the `problems` and `solutions` sections:
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

Here is an example of the YAML file structure you should follow:
```yaml
title: Use comments to explain *why*, not *what*
id: COM001

description: |-
  Comments should explain the reasoning and intent behind code decisions
  rather than describing what the code literally does. "What" comments are
  redundant since the code itself shows what is happening. "Why" comments
  provide valuable context about business logic, edge cases, and design
  decisions.

problems:
  - They duplicate information already visible in the code
  - They become outdated when code changes but comments don't
  - They add noise without providing insight
  - They can make code harder to read by stating the obvious

solutions:
  - Explain business rules and requirements
  - Document assumptions and constraints
  - Describe complex algorithms and their purpose
  - Note workarounds and their reasons
  - Clarify non-obvious performance optimizations

examples:
  - scenario: Incrementing index
    before: >-
      ```python
      # add 1 to i
      i += 1
      ```
    after: >-
      ```python
      # Compensate for zero-based index
      i += 1
      ```

  - scenario: Mutable default argument
    before: >-
      ```python
      def add_item(item, bucket=[]):
          # append to bucket
          bucket.append(item)
          return bucket
      ```
    after: >-
      ```python
      def add_item(item, bucket=None):
          # Use a new list unless one is explicitly supplied.
          if bucket is None:
              bucket = []
          bucket.append(item)
          return bucket
      ```

  - scenario: Repeated expensive computation
    before: >-
      ```python
      # fetch the config every time
      for item in items:
          cfg = load_config()  # expensive I/O
          process(item, cfg)
      ```
    after: >-
      ```python
      # Load config once; reuse for all items
      cfg = load_config()  # expensive I/O
      for item in items:
          process(item, cfg)
      ```
```

A common mistake is to not provide enough diverse examples.

Use a <Counter> as a scratchpad to record how many examples you have provided after each scenario.

IMPORTANT that exactly 25 scenarios are provided.
<YAMLRuleFileDefinition>
"""
