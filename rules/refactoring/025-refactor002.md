# Use comprehensions for simple data transformations.

**ID**: REFACTOR002  
**Category**: Refactoring → refactoring

## Rule Description
Use comprehensions for simple data transformations.

## Before
```python
squares = []
for n in numbers:
    squares.append(n*n)
```

## After  
```python
squares = [n*n for n in numbers]
```

## Full Example
```python
# More declarative
```
