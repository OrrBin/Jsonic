# Quick Test Reference Card

## Setup (One Time)
```bash
pip install -r requirements-dev.txt
```

## Most Common Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=jsonic --cov-report=html

# View coverage report
open htmlcov/index.html

# Run specific test file
pytest tests/unit/test_serialization.py

# Run tests matching pattern
pytest -k "serialization"

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

## Test Statistics

- **Files**: 5 test files
- **Tests**: 100+ test functions
- **Coverage**: >90% line, >85% branch
- **Runtime**: <5 seconds
- **Lines**: 1500+ lines of test code

## What's Tested

✅ All core functionality (serialize, deserialize)
✅ All features (private attrs, transient, mapping)
✅ 50+ edge cases (None, empty, unicode, deep nesting)
✅ 20+ error scenarios
✅ Custom serializers/deserializers
✅ External class registration

## Test Files

```
tests/
├── conftest.py                    # Fixtures
├── unit/
│   ├── test_serialization.py     # 40+ tests
│   ├── test_deserialization.py   # 35+ tests
│   ├── test_register_type.py     # 15+ tests
│   └── test_custom_serializers.py # 10+ tests
└── edge_cases/
    └── test_edge_cases.py         # 50+ tests
```

## Quick Checks

```bash
# Did I break anything?
pytest

# What's my coverage?
pytest --cov=jsonic --cov-report=term-missing

# Which tests are failing?
pytest -v --tb=short

# Run just the fast tests
pytest -m unit

# Run just edge cases
pytest -m edge_case
```

## Before Committing

```bash
# Run full test suite with coverage
pytest --cov=jsonic --cov-report=term-missing --cov-fail-under=90

# If this passes, you're good to commit! ✅
```

## Need Help?

- **Full guide**: See `TESTING_GUIDE.md`
- **Strategy**: See `TEST_COVERAGE_PLAN.md`
- **Summary**: See `TEST_SUMMARY.md`
- **Pytest help**: Run `pytest --help`
