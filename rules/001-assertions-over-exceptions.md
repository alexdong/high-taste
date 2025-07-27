# Rule 001: Replace Defensive try/except with Assertions

**Category:** Error Handling  
**Severity:** Warning  
**Rationale:** Defensive exception handling masks real issues and makes debugging harder

## Problem

Defensive exception handling with try/except blocks for validation creates several issues:
- Masks real problems with silent failures
- Makes debugging harder by catching and hiding errors
- Creates unclear function contracts
- Adds cognitive load through nested error handling

## Solution

Use assertions for precondition validation and let real errors bubble up naturally.

## Why This Matters

- **Fail Fast**: Assertions fail immediately with clear error messages
- **Explicit Contracts**: Makes function preconditions and expectations obvious
- **Better Debugging**: No silent failures or masked errors
- **Reduced Complexity**: Eliminates nested error handling logic

## Examples

### Bad: Defensive Exception Handling

```python
def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    try:
        if model and model in MODEL_PRICING:
            if input_tokens >= 0 and output_tokens >= 0:
                pricing = MODEL_PRICING[model]
                if "input_price_per_1m_tokens" in pricing:
                    return (input_tokens * pricing["input_price_per_1m_tokens"] + 
                            output_tokens * pricing["output_price_per_1m_tokens"]) / 1_000_000
        return 0.0  # Silent failure!
    except Exception as e:
        logger.error(f"Cost calculation error: {e}")
        return 0.0  # Masks the real problem
```

### Good: Clear Assertions

```python
def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate cost for LLM usage with clear precondition validation."""
    assert model.strip(), "Model name cannot be empty"
    assert model in MODEL_PRICING, f"Model {model} not found in pricing data"
    assert input_tokens >= 0, f"Input tokens must be non-negative, got {input_tokens}"
    assert output_tokens >= 0, f"Output tokens must be non-negative, got {output_tokens}"
    
    pricing = MODEL_PRICING[model]
    input_cost = input_tokens * pricing["input_price_per_1m_tokens"] / 1_000_000
    output_cost = output_tokens * pricing["output_price_per_1m_tokens"] / 1_000_000
    return input_cost + output_cost
```

## When to Use

- **Assertions**: For preconditions, invariants, and programmer errors
- **Exceptions**: For runtime conditions outside your control (network, file I/O, user input)

## AST Patterns to Detect

- `try/except` blocks that catch broad exceptions for validation
- Functions returning `None`, `0`, or default values in except blocks
- Exception handling for data validation rather than external failures

## Related Rules

- Rule 003: Eliminate Deep Nesting with Early Returns
- Rule 006: Database Transaction Safety