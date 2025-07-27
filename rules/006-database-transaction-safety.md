# Rule 006: Database Transaction Safety - Validate Before Commit

**Category:** Data Integrity  
**Severity:** Error  
**Rationale:** Committing transactions before validation can corrupt data and make errors unrecoverable

## Problem

Committing database transactions before validating that operations succeeded:
- Can corrupt data with invalid commits
- Makes errors unrecoverable (can't rollback after commit)
- Violates fail-fast principle
- Causes silent failures that create downstream issues
- Breaks ACID compliance and database consistency

## Solution

Always execute operations, validate success with assertions, then commit - enabling rollback on failure.

## Why This Matters

- **Data Integrity**: Prevents invalid commits from corrupting data
- **Error Recovery**: Enables transaction rollback when operations fail
- **Fail Fast**: Clear error messages at exact point of failure
- **ACID Compliance**: Maintains database consistency and transaction atomicity
- **Debugging**: SQL logging and specific error messages aid troubleshooting

## The Pattern: Execute → Validate → Commit

### Bad: Commit Before Validation

```python
conn.commit()
assert cursor.rowcount == 1, (
    f"Failed to create conversation {conversation.id}"
)  # Too late - data already committed!
```

### Good: Validate Before Commit

```python
logger.info("SQL: %s | Params: %s", sql.strip(), params)
cursor.execute(sql, params)
assert cursor.rowcount == 1, (
    f"Failed to insert conversation {conversation.id}"
)  # Check success first
conn.commit()  # Only commit if validation passes
```

## Complete Pattern with Proper Error Handling

```python
def insert_conversation(conn, cursor, conversation):
    """Insert conversation with proper transaction safety."""
    sql = "INSERT INTO conversations (id, title, created_at) VALUES (?, ?, ?)"
    params = (conversation.id, conversation.title, conversation.created_at)
    
    logger.info("SQL: %s | Params: %s", sql.strip(), params)
    cursor.execute(sql, params)
    
    # Validate success before committing - fail fast with clear message
    assert cursor.rowcount == 1, (
        f"Failed to insert conversation {conversation.id}: "
        f"expected 1 row affected, got {cursor.rowcount}"
    )
    
    conn.commit()
    logger.info("Successfully inserted conversation %s", conversation.id)
```

## Key Benefits

**Transaction Safety**
- Failed validation triggers rollback before data corruption
- Maintains ACID compliance and database consistency  
- Prevents partial operations from being permanently saved

**Fail Fast Principle**
- Assertions fail immediately with specific error messages
- Stops execution at exact point of failure
- No silent failures or defensive masking of problems

**Debugging Support**
- SQL logging helps trace execution flow
- Clear error messages identify exactly what failed
- Transaction boundaries are explicit and testable

## When to Use This Pattern

**Always use for:**
- INSERT/UPDATE/DELETE operations where row count matters
- Multi-step transactions that must complete atomically
- Operations where data integrity is critical

**Validation Techniques:**
- `cursor.rowcount` for affected row count validation
- `cursor.lastrowid` for auto-generated ID verification  
- Custom queries to verify expected state changes

## Multi-Operation Transactions

```python
def transfer_funds(conn, cursor, from_account, to_account, amount):
    """Transfer funds between accounts atomically."""
    try:
        # Operation 1: Debit from source
        cursor.execute(
            "UPDATE accounts SET balance = balance - ? WHERE id = ?",
            (amount, from_account)
        )
        assert cursor.rowcount == 1, f"Failed to debit account {from_account}"
        
        # Operation 2: Credit to destination  
        cursor.execute(
            "UPDATE accounts SET balance = balance + ? WHERE id = ?",
            (amount, to_account)
        )
        assert cursor.rowcount == 1, f"Failed to credit account {to_account}"
        
        # Validate final state
        cursor.execute("SELECT balance FROM accounts WHERE id = ?", (from_account,))
        from_balance = cursor.fetchone()[0]
        assert from_balance >= 0, f"Account {from_account} overdraft: {from_balance}"
        
        conn.commit()  # Only commit if all operations succeeded
        
    except Exception:
        conn.rollback()  # Rollback on any failure
        raise
```

## AST Patterns to Detect

- `conn.commit()` calls before validation statements
- Database operations without `cursor.rowcount` checks
- Missing assertion statements after critical database operations
- Transactions without proper rollback handling

## Assertion Guidelines

- **Use assertions for**: Database operation validation (programmer errors)
- **Let exceptions bubble**: Real database errors (network, permissions, constraints)
- **Provide specific messages**: Include operation details and expected vs actual results

## Related Rules

- Rule 001: Use assertions for validation rather than defensive exception handling
- Rule 002: Load database connections once at module level for efficiency