# Rule 005: Use Named Tuples for Structured Function Returns

**Category:** Type Safety  
**Severity:** Warning  
**Rationale:** Anonymous tuples and dictionaries create unclear, error-prone interfaces

## Problem

Functions that return anonymous tuples or generic dictionaries:
- Unclear what each value represents
- Error-prone due to positional arguments
- No type safety or IDE support
- Difficult to extend with additional fields
- Magic strings and index numbers in calling code

## Solution

Use NamedTuple or dataclasses for self-documenting, structured return values.

## Why This Matters

- **Self-Documentation**: Field names explain what each value represents
- **Type Safety**: IDE support with autocomplete and type checking
- **Error Prevention**: Prevents argument order mistakes
- **Extensibility**: Easy to add fields without breaking existing code
- **Immutability**: NamedTuples are immutable by default

## Examples

### Bad: Anonymous Tuple Return

```python
def _calculate_usage_metrics(result, config) -> tuple[int, float]:
    """Calculate token usage and cost from result."""
    tokens_used = (usage.request_tokens or 0) + (usage.response_tokens or 0)
    cost_usd = calculate_cost(model=config.model, input_tokens=..., output_tokens=...)
    return tokens_used, cost_usd

# Usage is unclear and error-prone
tokens, cost = _calculate_usage_metrics(result, config)  # Which is which?
cost, tokens = _calculate_usage_metrics(result, config)  # Oops! Wrong order
```

### Also Bad: Dictionary Return

```python
def _calculate_usage_metrics(result, config) -> dict[str, int | float]:
    return {
        "tokens": tokens_used,
        "cost": cost_usd,  # Typos in keys are runtime errors
    }

# Usage requires magic strings
metrics = _calculate_usage_metrics(result, config)
print(f"Cost: {metrics['cost']}")  # Typo-prone, no autocomplete
```

### Good: Named Tuple with Clear Fields

```python
from typing import NamedTuple

class UsageMetrics(NamedTuple):
    """Detailed usage metrics breakdown."""
    input_tokens: int
    output_tokens: int
    cached_tokens: int
    total_tokens: int
    total_cost_usd: float

def _calculate_usage_metrics(result, config) -> UsageMetrics:
    """Calculate detailed token usage and cost breakdown from result."""
    usage = result.usage()
    input_tokens = usage.request_tokens or 0
    output_tokens = usage.response_tokens or 0
    
    # Extract cached tokens from details if available
    cached_tokens = 0
    if usage.details:
        cached_keys = ['cache_read_input_tokens', 'cached_tokens', 'cache_tokens']
        for key in cached_keys:
            if key in usage.details:
                cached_tokens = usage.details[key]
                break
    
    total_tokens = usage.total_tokens or (input_tokens + output_tokens)
    cost_usd = calculate_cost(model=config.model, input_tokens=input_tokens, output_tokens=output_tokens)
    
    return UsageMetrics(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cached_tokens=cached_tokens,
        total_tokens=total_tokens,
        total_cost_usd=cost_usd
    )

# Usage is self-documenting and type-safe
metrics = _calculate_usage_metrics(result, config)
print(f"Used {metrics.input_tokens} input tokens, {metrics.output_tokens} output tokens")
print(f"Cached: {metrics.cached_tokens}, Total cost: ${metrics.total_cost_usd:.4f}")
```

### Alternative: Dataclass for Methods or Mutable Data

```python
from dataclasses import dataclass

@dataclass(frozen=True)  # frozen=True makes it immutable like NamedTuple
class UsageMetrics:
    """Detailed usage metrics breakdown."""
    input_tokens: int
    output_tokens: int
    cached_tokens: int
    total_tokens: int
    total_cost_usd: float
    
    @property
    def cost_per_token(self) -> float:
        """Calculate cost per token."""
        return self.total_cost_usd / self.total_tokens if self.total_tokens > 0 else 0.0
    
    def format_summary(self) -> str:
        """Format a human-readable summary."""
        return (f"Tokens: {self.input_tokens} -> {self.output_tokens} "
                f"(cached: {self.cached_tokens}), Cost: ${self.total_cost_usd:.4f}")
```

## When to Use Each Approach

- **NamedTuple**: Simple data containers, immutable, lightweight
- **Dataclass**: Need methods, default values, or mutable fields  
- **Regular dict**: Only for truly dynamic data where keys aren't known at design time

## AST Patterns to Detect

- Functions returning `tuple[...]` with multiple heterogeneous types
- Functions returning `dict[str, Any]` or `dict[str, Union[...]]`
- Magic number indexing (`result[0]`, `result[1]`) on function returns
- Magic string keys (`result["field"]`) on function returns

## Refactoring Strategy

1. **Identify multi-value returns**: Find functions returning tuples/dicts
2. **Analyze usage patterns**: See how return values are used
3. **Define structure**: Create NamedTuple/dataclass with meaningful field names
4. **Add type annotations**: Specify exact types for each field
5. **Update callers**: Replace indexing/key access with attribute access

## Related Rules

- Rule 003: Eliminate deep netting (clearer return structure)
- Rule 001: Use assertions to validate return value construction