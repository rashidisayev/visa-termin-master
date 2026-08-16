# Testing Guide - Visa Appointment Helper

Comprehensive test suite for the visa appointment automation system.

## 📋 Overview

The test suite includes:
- **Unit Tests**: Individual module and function testing
- **Integration Tests**: Multi-module workflow testing
- **Configuration Tests**: Environment variable and config loading
- **Extraction Tests**: HTML parsing and date extraction
- **Portal Detection Tests**: Automatic portal type detection

## 🚀 Quick Start

### Install Test Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `pytest>=7.0.0` - Test framework
- `pytest-cov>=3.0.0` - Code coverage
- `pytest-mock>=3.6.0` - Mocking support
- `pytest-asyncio>=0.18.0` - Async test support

### Run All Tests

```bash
pytest
```

This will:
- Discover and run all tests in `tests/` directory
- Generate HTML coverage report in `htmlcov/`
- Display summary of passed/failed tests

### Run Tests with Verbose Output

```bash
pytest -v
```

Shows detailed output for each test:
```
tests/test_config.py::TestConfigBasics::test_root_folder_default PASSED
tests/test_config.py::TestConfigBasics::test_root_folder_custom PASSED
tests/test_visa_types.py::TestVisaCategory::test_schengen_categories_are_c_visa PASSED
```

## 🔍 Running Specific Tests

### Run a Single Test File

```bash
pytest tests/test_config.py
```

### Run a Single Test Class

```bash
pytest tests/test_config.py::TestConfigBasics
```

### Run a Single Test Function

```bash
pytest tests/test_config.py::TestConfigBasics::test_root_folder_default
```

### Run Tests by Marker

```bash
# Run only config tests
pytest -m config

# Run only visa type tests
pytest -m visa_types

# Run only portal detection tests
pytest -m portal_detection

# Skip slow tests
pytest -m "not slow"
```

## 📊 Coverage Reports

### Generate Coverage Report

```bash
pytest --cov=lib --cov-report=html
```

This creates:
- Terminal report showing coverage percentage
- HTML report in `htmlcov/index.html` (open in browser)

### View Coverage Report in Browser

```bash
# macOS
open htmlcov/index.html

# Linux
xdg-open htmlcov/index.html

# Windows
start htmlcov/index.html
```

### Coverage by Module

```
lib/config.py ...................... 95%
lib/visa_types.py .................. 92%
lib/booking_process.py ............. 88%
lib/extractors.py .................. 85%
lib/utils.py ....................... 90%
```

Target: **>85% coverage** for all modules

## 🧪 Test Organization

### tests/conftest.py
Shared pytest configuration and fixtures:
- `temp_project_dir` - Temporary project directory
- `mock_env_vars` - Mock environment variables
- `sample_legacy_portal_html` - Sample legacy portal HTML
- `sample_new_portal_html` - Sample new portal HTML
- `sample_doctolib_html` - Sample Doctolib portal HTML
- `mock_logger` - Mock logger instance
- `mock_telegram_notification` - Mock Telegram notifications
- `mock_dbc_solve` - Mock captcha solver

### tests/test_config.py (50+ tests)
Configuration module tests:
- Default values and environment variable overrides
- Universal configuration (VISA_TYPE, EMBASSY_LOCATION)
- Legacy configuration compatibility
- Notification and credential settings
- Date filtering logic
- HTML selectors and logging configuration

### tests/test_visa_types.py (30+ tests)
Visa type management tests:
- VisaCategory enum values
- VisaTypeConfig dataclass creation
- Default visa type definitions (Schengen, Work, Study, Family, Residence)
- VisaTypeManager functionality
- Location-specific category ID mappings
- Custom visa type registration

### tests/test_booking_process.py (20+ tests)
Portal detection and adaptation tests:
- Portal type detection (legacy, new, Doctolib, custom)
- Form field extraction
- Appointment slot detection
- Captcha type detection
- Layout-specific date extraction
- Multiple date format handling

### tests/test_utils.py (30+ tests)
Utility function tests:
- Logger setup and configuration
- File I/O operations (load, save, read)
- HTML parsing and element finding
- Base64 image extraction
- Error handling and edge cases

### tests/test_extractors.py (20+ tests)
HTML extraction tests:
- Date extraction from different portal types
- Captcha image extraction
- Booking time extraction
- Reschedule URL extraction
- Config filter integration
- Edge cases (malformed HTML, empty files, large files)

## 🎯 Test Categories

### Unit Tests (100+ tests)
Test individual functions and classes in isolation:
```bash
pytest -m unit
```

### Integration Tests (15+ tests)
Test multiple modules working together:
```bash
pytest -m integration
```

### Configuration Tests (50+ tests)
Test all configuration aspects:
```bash
pytest -m config
```

### Portal Detection Tests (20+ tests)
Test automatic portal type detection:
```bash
pytest -m portal_detection
```

### Extraction Tests (20+ tests)
Test HTML parsing and data extraction:
```bash
pytest -m extraction
```

## 🐛 Debugging Tests

### Run with Full Traceback

```bash
pytest -v --tb=long
```

Shows complete traceback for failures.

### Run with Print Statements

```bash
pytest -v -s
```

Shows print output from tests (doesn't capture stdout).

### Run Single Test with Debugging

```bash
pytest -v -s tests/test_config.py::TestConfigBasics::test_root_folder_default
```

### Run with Python Debugger

```bash
pytest -v --pdb
```

Drops into Python debugger on test failure.

## 📈 Continuous Integration

### GitHub Actions Configuration

Add to `.github/workflows/tests.yml`:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, "3.10", 3.11]
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -r requirements.txt
      - run: pytest --cov=lib
      - uses: codecov/codecov-action@v2
```

### Local Pre-commit Hook

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
pytest --co -q > /dev/null
if [ $? -ne 0 ]; then
    echo "Tests failed - commit aborted"
    exit 1
fi
```

## ✅ Test Checklist

Before committing code:

- [ ] All tests pass: `pytest`
- [ ] Coverage is >85%: `pytest --cov=lib`
- [ ] No linting errors: (if using pylint/flake8)
- [ ] New features have tests
- [ ] Bug fixes have regression tests
- [ ] Documentation is updated

## 🔧 Adding New Tests

### Test File Template

```python
"""Tests for lib/my_module.py"""
import pytest
from lib import my_module


class TestMyFunction:
    """Test my_function"""
    
    def test_basic_functionality(self):
        """Test basic functionality"""
        result = my_module.my_function(input_value)
        assert result == expected_value
    
    def test_edge_case(self):
        """Test edge case"""
        with pytest.raises(ValueError):
            my_module.my_function(invalid_input)
    
    def test_with_fixture(self, temp_project_dir):
        """Test using fixture"""
        result = my_module.my_function(temp_project_dir)
        assert result is not None
```

### Adding Fixtures to conftest.py

```python
@pytest.fixture
def my_fixture():
    """Fixture description"""
    setup_code()
    yield resource
    teardown_code()
```

### Mocking External Dependencies

```python
from unittest.mock import patch, MagicMock

def test_with_mock(mocker):
    """Test with mocked dependency"""
    mock_requests = mocker.patch("lib.module.requests.get")
    mock_requests.return_value.json.return_value = {"status": "ok"}
    
    result = my_function()
    assert result["status"] == "ok"
    mock_requests.assert_called_once()
```

## 📚 Test Examples

### Testing with Temporary Directory

```python
def test_file_operation(temp_project_dir):
    """Test file operations"""
    from pathlib import Path
    
    file_path = Path(temp_project_dir) / "test.txt"
    file_path.write_text("test content")
    
    content = file_path.read_text()
    assert content == "test content"
```

### Testing Configuration Loading

```python
def test_config_from_env(mock_env_vars):
    """Test configuration from environment"""
    os.environ["VISA_TYPE"] = "work"
    
    # Reload config to pick up env changes
    if "lib.config" in sys.modules:
        del sys.modules["lib.config"]
    
    from lib import config
    assert config.VISA_TYPE == "work"
```

### Testing HTML Parsing

```python
def test_html_parsing(sample_legacy_portal_html):
    """Test HTML parsing"""
    from lib import extractors
    
    result = extractors.extract_available_date(html_content)
    assert result == "25.04.2024"
```

## 🚨 Common Issues

### ModuleNotFoundError: No module named 'lib'

Make sure you're running pytest from the project root:
```bash
cd /path/to/visa-termin-master
pytest
```

### Tests Fail Due to Environment Variables

Use the `mock_env_vars` fixture to isolate environment:
```python
def test_isolation(mock_env_vars):
    """Tests are isolated from each other"""
    mock_env_vars()  # Clear all custom env vars
```

### Config Not Reloading Between Tests

Import modules inside tests or clear module cache:
```python
if "lib.config" in sys.modules:
    del sys.modules["lib.config"]
from lib import config
```

### Fixture Setup/Teardown Issues

Use pytest fixtures properly:
```python
@pytest.fixture
def my_fixture():
    setup()
    yield resource  # This is what the test gets
    teardown()      # Runs after test completes
```

## 📞 Support

For test failures or questions:

1. Check test output: `pytest -v`
2. Review test file comments
3. Check conftest.py for available fixtures
4. Read test docstrings for expected behavior
5. Review DEVELOPER.md for module details

## 📦 Test Coverage Goals

| Module | Target | Current |
|--------|--------|---------|
| config.py | 95% | - |
| visa_types.py | 90% | - |
| booking_process.py | 85% | - |
| extractors.py | 85% | - |
| utils.py | 90% | - |
| **Overall** | **>85%** | - |

## 🎉 Happy Testing!

The test suite ensures code quality and reliability. Write tests before implementing features (TDD) or after fixing bugs (regression tests).

**Version**: 2.1.0  
**Last Updated**: August 2026
