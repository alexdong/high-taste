# Rule 002: Load Heavy Resources Once at Module Level

**Category:** Performance  
**Severity:** Error  
**Rationale:** Repeatedly loading data in functions causes significant performance degradation

## Problem

Loading heavy resources (files, data structures, configurations) inside functions that are called repeatedly:
- Creates unnecessary I/O operations on every function call
- Significantly degrades performance (often 100-1000x slower)
- Makes dependencies less obvious
- Complicates error handling

## Solution

Load heavy resources once at module initialization and cache them at module level.

## Why This Matters

- **Performance**: Eliminates repeated I/O operations (1000x speedup typical)
- **Clarity**: Makes dependencies explicit at module level
- **Reliability**: Better error handling during startup vs runtime
- **Efficiency**: Direct memory access vs file system calls

## Examples

### Bad: Repeated Loading

```python
def get_model_pricing(model: str) -> dict[str, float]:
    pricing_data = _load_pricing_data()  # File I/O every call!
    return pricing_data[model]

def calculate_cost(model: str, tokens: int) -> float:
    pricing = get_model_pricing(model)  # Another file load!
    return tokens * pricing["price_per_token"]
```

### Good: Load Once at Module Level

```python
# Load once during module initialization
MODEL_PRICING: dict[str, dict[str, float]] = _load_pricing_data()

def get_model_pricing(model: str) -> dict[str, float]:
    assert model in MODEL_PRICING, f"Model {model} not found"
    return MODEL_PRICING[model]  # Direct memory access

def calculate_cost(model: str, tokens: int) -> float:
    pricing = MODEL_PRICING[model]  # Direct access, no I/O
    return tokens * pricing["price_per_token"]
```

### Even Better: Eliminate Unnecessary Getters

```python
def calculate_cost(model: str, tokens: int) -> float:
    assert model in MODEL_PRICING, f"Model {model} not found"
    return tokens * MODEL_PRICING[model]["price_per_token"]
```

## Performance Impact

Real-world measurements for loading a 50KB JSON file:

- **Repeated loading (1000 calls)**: ~500ms total
- **Load once**: ~0.5ms total (**1000x faster**)

## AST Patterns to Detect

- File I/O operations (`open()`, `json.load()`, etc.) inside functions
- Functions that load the same resource repeatedly
- Database connections created in functions rather than module level
- Configuration loading inside loops or frequently called functions

## Implementation Notes

- Use type annotations for module-level constants
- Consider lazy loading for very large resources
- Handle loading errors at module level with clear messages
- Use `functools.lru_cache` for computed resources that vary by parameters

## Related Rules

- Rule 001: Assertions for validation after loading  
- Rule 004: Dynamic Data Discovery (what to load)