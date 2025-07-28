# Replace long if/elif chains with dictionary dispatch.

**ID**: REFACTOR003  
**Category**: Refactoring → refactoring

## Rule Description
Replace long if/elif chains with dictionary dispatch.

## Before
```python
if cmd == 'start':
    start()
elif cmd == 'stop':
    stop()
elif cmd == 'pause':
    pause()
```

## After  
```python
commands = {'start': start, 'stop': stop, 'pause': pause}
commands[cmd]()
```

## Full Example
```python
# Easier to extend
```
