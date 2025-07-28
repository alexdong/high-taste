# DRY: remove duplicate code by factoring common logic.

**ID**: REFACTOR001  
**Category**: Refactoring → refactoring

## Rule Description
DRY: remove duplicate code by factoring common logic.

## Before
```python
if user == 'admin':
    save()
if user == 'editor':
    save()
```

## After  
```python
if user in {'admin', 'editor'}:
    save()
```

## Full Example
```python
# Single point of change
```
