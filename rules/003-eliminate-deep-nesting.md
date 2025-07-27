# Rule 003: Eliminate Deep Nesting with Early Returns and Direct Access

**Category:** Readability  
**Severity:** Warning  
**Rationale:** Deep nesting creates cognitive overhead and makes code hard to follow

## Problem

Deep nesting with multiple conditional checks:
- Increases cognitive load (tracking multiple nested conditions)
- Makes the "happy path" unclear
- Creates maintenance burden when conditions change
- Makes testing and debugging more difficult
- Often indicates validation that should be done upfront

## Solution

Use assertions for validation, then perform direct operations with clear structure.

## Why This Matters

- **Cognitive Load**: Reduces mental effort to understand code flow
- **Clarity**: Makes the main logic path obvious
- **Maintainability**: Easier to modify and extend
- **Testability**: Simpler to write focused tests
- **Debugging**: Clearer execution flow

## Examples

### Bad: Deep Nesting

```python
def get_cost_info(model: str) -> dict[str, float | None]:
    if model:
        if model.strip():
            if model in pricing:
                if "input_price_per_1m_tokens" in pricing[model]:
                    if pricing[model]["input_price_per_1m_tokens"] is not None:
                        input_price = pricing[model]["input_price_per_1m_tokens"]
                        if "output_price_per_1m_tokens" in pricing[model]:
                            if pricing[model]["output_price_per_1m_tokens"] is not None:
                                output_price = pricing[model]["output_price_per_1m_tokens"]
                                cached_price = pricing[model].get("cached_input_price_per_1m_tokens")
                                return {
                                    "input_cost_per_token": input_price / 1_000_000,
                                    "output_cost_per_token": output_price / 1_000_000,
                                    "cached_input_cost_per_token": cached_price / 1_000_000 if cached_price else None,
                                }
    return {}  # What went wrong? We don't know!
```

### Good: Assert Preconditions, Then Direct Operations

```python
def get_cost_info(model: str) -> dict[str, float | None]:
    """Get cost information for a model with clear validation."""
    assert model.strip(), "Model name cannot be empty"
    assert model in MODEL_PRICING, f"Model {model} not found in pricing data"
    
    model_info = MODEL_PRICING[model]
    
    # Direct access after validation - no nesting needed
    input_price = model_info["input_price_per_1m_tokens"]
    output_price = model_info["output_price_per_1m_tokens"]
    cached_price = model_info.get("cached_input_price_per_1m_tokens")
    
    return {
        "input_cost_per_token": input_price / 1_000_000,
        "output_cost_per_token": output_price / 1_000_000,
        "cached_input_cost_per_token": cached_price / 1_000_000 if cached_price else None,
    }
```

### Even Better: Use Structured Data

```python
from dataclasses import dataclass

@dataclass
class ModelCostInfo:
    input_cost_per_token: float
    output_cost_per_token: float
    cached_input_cost_per_token: float | None

def get_cost_info(model: str) -> ModelCostInfo:
    assert model.strip(), "Model name cannot be empty"
    assert model in MODEL_PRICING, f"Model {model} not found"
    
    info = MODEL_PRICING[model]
    cached_price = info.get("cached_input_price_per_1m_tokens")
    
    return ModelCostInfo(
        input_cost_per_token=info["input_price_per_1m_tokens"] / 1_000_000,
        output_cost_per_token=info["output_price_per_1m_tokens"] / 1_000_000,
        cached_input_cost_per_token=cached_price / 1_000_000 if cached_price else None,
    )
```

## AST Patterns to Detect

- Functions with more than 3 levels of nesting
- Multiple consecutive `if` statements checking related conditions
- Long chains of `.get()` calls with default values
- Functions that return different types based on validation failures

## Refactoring Strategy

1. **Identify validation logic**: Extract all precondition checks
2. **Convert to assertions**: Replace nested ifs with upfront assertions
3. **Flatten main logic**: Perform operations directly after validation
4. **Use structured returns**: Replace dictionaries with dataclasses/NamedTuple

## Related Rules

- Rule 001: Use assertions for validation
- Rule 005: Use structured return types