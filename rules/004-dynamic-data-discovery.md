# Rule 004: Dynamic Data Discovery vs Hardcoded Lists

**Category:** Maintainability  
**Severity:** Warning  
**Rationale:** Hardcoded lists require manual maintenance and become stale quickly

## Problem

Hardcoded lists of data that should be discovered dynamically:
- Require manual updates when new items are added
- Become stale and out of sync with actual data
- Create bugs when developers forget to update lists
- Make code fragile to changes in data structure

## Solution

Extract available data dynamically from existing data structures, file systems, or APIs.

## Why This Matters

- **Maintenance**: Eliminates manual list updates when data changes
- **Reliability**: Prevents bugs from forgotten updates
- **Resilience**: Automatically adapts to new data without code changes
- **DRY Principle**: Single source of truth for data

## Examples

### Bad: Hardcoded File Lists

```python
# Requires maintenance when adding providers
PRICING_FILES = ["anthropic.json", "openai.json", "google.json"]  # Forgot "cohere.json"!

def load_all_pricing() -> dict[str, dict]:
    all_pricing = {}
    for filename in PRICING_FILES:  # Missing files won't be loaded
        file_path = PRICING_DIR / filename
        with open(file_path) as f:
            provider = filename.replace(".json", "")
            all_pricing[provider] = json.load(f)
    return all_pricing
```

### Good: Dynamic File Discovery

```python
def load_all_pricing() -> dict[str, dict]:
    all_pricing = {}
    pricing_files = list(PRICING_DIR.glob("*.json"))  # Finds ALL JSON files
    
    for file_path in pricing_files:
        provider = file_path.stem  # filename without extension
        with open(file_path) as f:
            all_pricing[provider] = json.load(f)
    
    return all_pricing
```

### Bad: Hardcoded Test Data

```python
def test_cost_calculation():
    # Becomes stale when models change
    test_models = [
        "claude-3-5-sonnet-20241022", 
        "gpt-4o-mini", 
        "gemini-2.0-flash"  # What about new models?
    ]
    for model in test_models:
        cost = calculate_cost(model, 1000, 500)
        assert cost > 0, f"Cost should be positive for {model}"
```

### Good: Use Available Data

```python
def test_cost_calculation():
    test_models = list(MODEL_PRICING.keys())  # Tests ALL available models
    
    for model in test_models:
        cost = calculate_cost(model, 1000, 500)
        assert cost > 0, f"Cost should be positive for {model}"
```

### Even Better: Smart Sampling for Large Datasets

```python
import random

def test_cost_calculation():
    all_models = list(MODEL_PRICING.keys())
    # Test a representative sample if there are many models
    test_models = random.sample(all_models, min(10, len(all_models)))
    
    for model in test_models:
        cost = calculate_cost(model, 1000, 500)
        assert cost > 0, f"Cost should be positive for {model}"
```

## Real-World Impact

When Quinn added support for new LLM providers, the dynamic discovery approach automatically included them in tests and processing without any code changes.

## AST Patterns to Detect

- Lists/tuples with string literals that correspond to file names
- Hardcoded model names, API endpoints, or configuration keys
- Test data that duplicates information available elsewhere
- Manual enumeration of items that exist in data structures

## Discovery Patterns

### File System
```python
# JSON files
config_files = list(CONFIG_DIR.glob("*.json"))

# Python modules
modules = [f.stem for f in SRC_DIR.glob("*.py") if f.stem != "__init__"]
```

### Data Structures
```python
# Dictionary keys
available_models = list(MODEL_PRICING.keys())

# Object attributes
api_methods = [attr for attr in dir(api_client) if not attr.startswith('_')]
```

### Database/API
```python
# Database tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
```

## Related Rules

- Rule 002: Load data once at module level
- Rule 005: Use structured data for complex returns