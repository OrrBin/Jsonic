# Testing Guide for Jsonic

## Quick Start

### 1. Install Testing Dependencies
```bash
pip install -r requirements-dev.txt
```

### 2. Run All Tests
```bash
pytest
```

### 3. Run with Coverage Report
```bash
pytest --cov=jsonic --cov-report=html --cov-report=term-missing
```

### 4. View HTML Coverage Report
```bash
open htmlcov/index.html  # macOS
# or
xdg-open htmlcov/index.html  # Linux
# or
start htmlcov/index.html  # Windows
```

## Test Commands

### Run Specific Test Categories
```bash
# Unit tests only
pytest -m unit

# Edge case tests only
pytest -m edge_case

# Integration tests only
pytest -m integration
```

### Run Specific Test Files
```bash
# Serialization tests
pytest tests/unit/test_serialization.py

# Deserialization tests
pytest tests/unit/test_deserialization.py

# Edge cases
pytest tests/edge_cases/test_edge_cases.py

# Custom serializers
pytest tests/unit/test_custom_serializers.py

# Register type tests
pytest tests/unit/test_register_type.py
```

### Run Specific Test Classes or Functions
```bash
# Specific class
pytest tests/unit/test_serialization.py::TestPrimitiveTypes

# Specific test
pytest tests/unit/test_serialization.py::TestPrimitiveTypes::test_primitive_serialization

# Pattern matching
pytest -k "serialization"  # Run all tests with "serialization" in name
pytest -k "edge_case"      # Run all edge case tests
```

### Verbose Output
```bash
# Show test names as they run
pytest -v

# Show print statements
pytest -s

# Both
pytest -vs
```

### Stop on First Failure
```bash
pytest -x
```

### Run Last Failed Tests
```bash
pytest --lf
```

### Run Failed Tests First
```bash
pytest --ff
```

## Coverage Commands

### Basic Coverage
```bash
pytest --cov=jsonic
```

### Coverage with Missing Lines
```bash
pytest --cov=jsonic --cov-report=term-missing
```

### Coverage HTML Report
```bash
pytest --cov=jsonic --cov-report=html
```

### Coverage with Branch Analysis
```bash
pytest --cov=jsonic --cov-branch --cov-report=term-missing
```

### Fail if Coverage Below Threshold
```bash
pytest --cov=jsonic --cov-fail-under=90
```

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures
├── unit/                          # Unit tests
│   ├── test_serialization.py     # serialize() tests
│   ├── test_deserialization.py   # deserialize() tests
│   ├── test_register_type.py     # register_jsonic_type() tests
│   └── test_custom_serializers.py # Custom serializer/deserializer tests
└── edge_cases/                    # Edge case tests
    └── test_edge_cases.py         # Comprehensive edge cases
```

## What's Tested

### ✅ Core Functionality
- Primitive types (int, float, str, bool, None)
- Collections (list, dict, nested structures)
- Serializable classes
- Custom serializers/deserializers
- register_jsonic_type()

### ✅ Features
- Private attributes (serialize_private_attributes flag)
- Transient attributes
- Init parameter mapping
- Expected type validation
- String input/output formats
- Datetime serialization

### ✅ Edge Cases
- None values in all contexts
- Empty collections
- Unicode and special characters
- Deep nesting (100+ levels)
- Large collections (10k+ items)
- Special numbers (infinity, NaN)
- Mixed types
- Inheritance
- Properties

### ✅ Error Handling
- Unserializable types
- Invalid JSON
- Type mismatches
- Missing fields
- Wrong expected_type

## Expected Results

After running the full test suite with coverage:

```bash
pytest --cov=jsonic --cov-report=term-missing
```

You should see:
- **100+ tests** passing
- **>90% line coverage**
- **>85% branch coverage**
- **<5 seconds** runtime

## Troubleshooting

### Tests Fail Due to Missing Dependencies
```bash
pip install -r requirements-dev.txt
```

### Import Errors
Make sure you're in the project root:
```bash
cd /path/to/Jsonic
pytest
```

### Coverage Not Working
Install pytest-cov:
```bash
pip install pytest-cov
```

### Tests Pass Locally But Fail in CI
Check Python version compatibility:
```bash
python --version  # Should be 3.6+
```

## Adding New Tests

### 1. Choose the Right Location
- Unit tests → `tests/unit/`
- Edge cases → `tests/edge_cases/`
- Integration tests → `tests/integration/`

### 2. Use Fixtures from conftest.py
```python
def test_my_feature(simple_user_class):
    user = simple_user_class("Alice", 30)
    # ... test code
```

### 3. Use Parametrize for Multiple Inputs
```python
@pytest.mark.parametrize("value,expected", [
    (1, 1),
    ("test", "test"),
    (None, None),
])
def test_roundtrip(value, expected):
    assert deserialize(serialize(value)) == expected
```

### 4. Mark Your Tests
```python
@pytest.mark.unit
def test_something():
    pass

@pytest.mark.edge_case
def test_edge_case():
    pass
```

### 5. Test Errors with pytest.raises
```python
def test_error_case():
    with pytest.raises(TypeError, match="Could not find serializer"):
        serialize(UnserializableObject())
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.6, 3.7, 3.8, 3.9, 3.10, 3.11]
    
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    - name: Run tests with coverage
      run: |
        pytest --cov=jsonic --cov-report=xml --cov-fail-under=90
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## Next Steps

1. **Run the tests**: `pytest --cov=jsonic --cov-report=html`
2. **Check coverage**: Open `htmlcov/index.html`
3. **Fix any failures**: Address failing tests
4. **Add missing tests**: Cover any gaps found in coverage report
5. **Set up CI/CD**: Add GitHub Actions workflow
6. **Add badge**: Add coverage badge to README

## Questions?

- Check `TEST_COVERAGE_PLAN.md` for detailed test strategy
- Check `TEST_IMPLEMENTATION_SUMMARY.md` for what was implemented
- Run `pytest --help` for all pytest options
