# Contributing to Jsonic

Thank you for your interest in contributing to Jsonic! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Running Tests](#running-tests)
- [Code Style](#code-style)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)

---

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Assume good intentions

---

## Getting Started

### Prerequisites

- Python 3.8–3.13
- Git
- pip

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:

```bash
git clone https://github.com/YOUR_USERNAME/jsonic.git
cd jsonic
```

3. Add upstream remote:

```bash
git remote add upstream https://github.com/OrrBin/Jsonic.git
```

---

## Development Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
# Install package in editable mode
pip install -e .

# Install development dependencies
pip install pytest pytest-cov
```

### 3. Verify Installation

```bash
python -c "from jsonic import serialize, deserialize; print('Success!')"
```

---

## Running Tests

### Run All Tests

```bash
pytest tests/
```

### Run with Coverage

```bash
pytest tests/ --cov=jsonic --cov-report=html
```

View coverage report:
```bash
open htmlcov/index.html  # On macOS
# Or navigate to htmlcov/index.html in your browser
```

### Run Specific Tests

```bash
# Run a specific test file
pytest tests/unit/test_dataclass_support.py

# Run a specific test class
pytest tests/unit/test_dataclass_support.py::TestBasicDataclass

# Run a specific test
pytest tests/unit/test_dataclass_support.py::TestBasicDataclass::test_simple_dataclass

# Run tests matching a pattern
pytest tests/ -k "dataclass"
```

### Run Tests in Verbose Mode

```bash
pytest tests/ -v
```

### Run Tests with Output

```bash
pytest tests/ -s  # Shows print statements
```

---

## Code Style

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with some modifications:

- Line length: 120 characters (not 79)
- Use type hints for all function parameters and return values
- Use docstrings for public functions and classes

### Example

```python
from typing import Optional

def serialize_object(obj: object, include_private: bool = False) -> dict:
    """
    Serialize a Python object to a dictionary.
    
    Args:
        obj: The object to serialize
        include_private: Whether to include private attributes
        
    Returns:
        Dictionary representation of the object
        
    Raises:
        SerializationError: If object cannot be serialized
    """
    # Implementation here
    pass
```

### Formatting

We recommend using `black` for code formatting:

```bash
pip install black
black jsonic/ tests/
```

### Type Checking

We use type hints throughout the codebase:

```bash
pip install mypy
mypy jsonic/
```

### Linting

```bash
pip install flake8
flake8 jsonic/ tests/
```

---

## Pull Request Process

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- root Markdown files and `examples/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions or changes

### 2. Make Your Changes

- Write clear, concise code
- Add tests for new functionality
- Update documentation as needed
- Follow the code style guidelines

### 3. Test Your Changes

```bash
# Run all tests
pytest tests/

# Check coverage
pytest tests/ --cov=jsonic

# Inspect measured line and branch coverage
```

### 4. Commit Your Changes

Write clear commit messages:

```bash
git add .
git commit -m "Add feature: support for custom datetime formats

- Implement custom datetime serializer
- Add tests for datetime edge cases
- Update documentation with examples"
```

Commit message format:
- First line: Brief summary (50 chars or less)
- Blank line
- Detailed description with bullet points

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:
- Clear title describing the change
- Description of what changed and why
- Link to related issues (if any)
- Screenshots (if UI changes)

### 6. PR Review Process

- Maintainers will review your PR
- Address any feedback or requested changes
- Once approved, your PR will be merged

---

## Reporting Bugs

### Before Reporting

1. Check if the bug has already been reported
2. Try to reproduce with the latest version
3. Gather relevant information

### Bug Report Template

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Create object '...'
2. Serialize with '...'
3. See error

**Expected behavior**
What you expected to happen.

**Actual behavior**
What actually happened.

**Code Example**
```python
from jsonic import serialize

# Minimal reproducible example
```

**Environment**
- Python version: 3.10
- Jsonic version: 1.0.0
- OS: macOS 12.0

**Additional context**
Any other relevant information.
```

---

## Suggesting Features

### Feature Request Template

```markdown
**Feature Description**
Clear description of the feature.

**Use Case**
Why is this feature needed? What problem does it solve?

**Proposed API**
```python
# Example of how the feature would be used
```

**Alternatives Considered**
Other ways to achieve the same goal.

**Additional Context**
Any other relevant information.
```

---

## Development Guidelines

### Adding New Features

1. **Discuss First**: Open an issue to discuss the feature before implementing
2. **Write Tests**: Add comprehensive tests for the new feature
3. **Update Docs**: Update README.md, EXAMPLES.md, and docstrings
4. **Maintain Coverage**: Add meaningful regression cases and inspect measured branch coverage
5. **No Breaking Changes**: Avoid breaking existing APIs

### Writing Tests

```python
import pytest
from jsonic import serialize, deserialize
from dataclasses import dataclass

class TestNewFeature:
    """Test suite for new feature."""
    
    def test_basic_functionality(self):
        """Test basic use case."""
        # Arrange
        @dataclass
        class Example:
            value: str
        
        obj = Example("test")
        
        # Act
        data = serialize(obj)
        result = deserialize(data, expected_type=Example)
        
        # Assert
        assert result.value == "test"
    
    def test_edge_case(self):
        """Test edge case."""
        # Test implementation
        pass
    
    def test_error_handling(self):
        """Test error conditions."""
        with pytest.raises(ValueError):
            # Code that should raise ValueError
            pass
```

### Test Organization

```
tests/
├── unit/              # Unit tests
│   ├── test_serialization.py
│   ├── test_deserialization.py
│   └── ...
├── integration/       # Integration tests
└── edge_cases/        # Edge case tests
```

---

## Documentation Guidelines

### Docstring Format

```python
def function_name(param1: str, param2: int = 0) -> bool:
    """
    Brief one-line description.
    
    More detailed description if needed. Can span multiple lines
    and include examples.
    
    Args:
        param1: Description of param1
        param2: Description of param2 (default: 0)
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When param1 is empty
        TypeError: When param2 is negative
        
    Example:
        >>> function_name("test", 5)
        True
    """
    pass
```

### README Updates

When adding features, update:
- Features list
- Quick Start section (if relevant)
- Advanced Features section
- Examples

### EXAMPLES.md Updates

Add practical examples showing:
- Basic usage
- Common use cases
- Edge cases
- Integration with other libraries

---

## Release Process

(For maintainers)

1. Update version in `setup.py`
2. Update CHANGELOG.md
3. Create git tag: `git tag v1.0.0`
4. Push tag: `git push origin v1.0.0`
5. Build package: `python setup.py sdist bdist_wheel`
6. Upload to PyPI: `twine upload dist/*`

---

## Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Open a GitHub Issue
- **Chat**: Join our Discord/Slack (if available)
- **Email**: maintainer@example.com

---

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in documentation

---

Thank you for contributing to Jsonic! 🎉

## Current verification workflow

Use `python -m pip install -r requirements-dev.txt`; metadata and developer
dependencies live in pyproject.toml. Follow RELEASE.md to reproduce CI, package
inspection, fresh installation, historical fixtures and executed documentation.
No local test result alone establishes a release.
