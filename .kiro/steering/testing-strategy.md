---
title: Testing Strategy
description: Guidelines for Kiro to write and maintain tests when checking functionality
inclusion: always
---

# Testing Strategy

## Core Principles

- **Write Tests First**: When checking functionality or making changes, write tests before implementing the solution
- **Preserve Tests**: Never delete tests after successful runs - they are valuable for regression testing
- **Test Coverage**: Aim for comprehensive test coverage of all code changes and new features
- **Test Types**: Include unit tests, integration tests, and API tests as appropriate

## Test Implementation Guidelines

### When to Write Tests

- When implementing new features or functionality
- When fixing bugs or addressing issues
- When refactoring existing code
- When checking if something works as expected

### Test Structure

- Follow the existing test naming conventions (`test_*.py`)
- Group related tests in test classes when appropriate
- Use descriptive test names that explain what is being tested
- Include setup, execution, and assertion phases in each test

### Test Quality

- Tests should be independent and not rely on other tests
- Mock external dependencies when appropriate
- Include both positive and negative test cases
- Test edge cases and boundary conditions

## Testing Tools

- Use pytest as the primary testing framework
- Run tests using the task runner: `task test`, `task flow:test`, or `task flow-manager:test`
- Execute tests in Docker containers using the appropriate task commands
- **IMPORTANT**: All project commands should be run using Taskfile

### Test Execution Commands

**Run all tests:**

```bash
task test                    # Run all tests for both services
task flow:test              # Run only flow service tests
task flow-manager:test      # Run only flow-manager service tests
```

**Run specific tests:**

```bash
# Run specific test file
task flow:test -- tests/test_actors.py
task flow-manager:test -- tests/test_api.py

# Run specific test function or class
task flow:test -- tests/test_actors.py::TestActorSystem::test_actor_creation
task flow-manager:test -- tests/test_api.py::test_websocket_connection

# Run tests matching a pattern
task flow:test -- -k "email"
task flow-manager:test -- -k "container"

# Run with verbose output
task flow:test -- tests/ -v
task flow-manager:test -- tests/ -v --tb=short
```

All test commands support standard pytest arguments and options.

## Example Test Pattern

```python
def test_feature_expected_behavior():
    # Setup
    test_input = "sample input"
    expected_output = "expected result"

    # Execute
    actual_output = feature_function(test_input)

    # Assert
    assert actual_output == expected_output
```

## Error Handling Tests

- Test both expected success paths and error conditions
- Verify that appropriate exceptions are raised
- Check error messages and status codes
- Test recovery mechanisms when applicable

Remember that tests are a critical part of the codebase and should be maintained with the same care as production code. They serve as documentation and protect against regressions.
