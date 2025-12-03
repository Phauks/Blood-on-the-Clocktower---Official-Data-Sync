# Contributing to Blood on the Clocktower - Official Data Sync

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to this project.

## Table of Contents

- [Development Setup](#development-setup)
- [Code Style](#code-style)
- [Running Tests](#running-tests)
- [Making Changes](#making-changes)
- [Pull Request Process](#pull-request-process)
- [Security Guidelines](#security-guidelines)
- [Release Process](#release-process)

---

## Development Setup

### Prerequisites

- Python 3.11+ (3.12+ recommended)
- Git
- Virtual environment tool (venv, conda, etc.)

### Initial Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Phauks/Blood-on-the-Clocktower---Official-Data-Sync.git
   cd Blood-on-the-Clocktower---Official-Data-Sync
   ```

2. **Create a virtual environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   # Production dependencies
   pip install -r requirements.txt

   # Development dependencies (includes testing, linting, etc.)
   pip install -r requirements-dev.txt

   # Install Playwright browsers
   playwright install chromium
   ```

4. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

   This will automatically run code quality checks before each commit.

### Verify Installation

```bash
# Run the scraper (dry run)
python src/scrapers/character_scraper.py --help

# Run tests (once tests are implemented)
pytest

# Check code formatting
ruff check src/
ruff format --check src/

# Run type checking
mypy src/
```

---

## Code Style

This project follows modern Python best practices:

### Style Guidelines

- **PEP 8** compliance (enforced by ruff)
- **Type hints** on all function signatures
- **Docstrings** for all public functions (Google style)
- **Maximum line length**: 100 characters
- **Import ordering**: stdlib, third-party, local (automatic via ruff)

### Formatting

We use `ruff` for both linting and formatting:

```bash
# Auto-fix linting issues
ruff check src/ --fix

# Auto-format code
ruff format src/
```

### Type Checking

Use type hints and validate with mypy:

```bash
mypy src/ --install-types --non-interactive
```

Example of good type hints:

```python
def fetch_wiki_page(char_name: str) -> str | None:
    """Fetch a character's wiki page HTML.

    Args:
        char_name: Character name (e.g., "Fortune Teller")

    Returns:
        HTML content or None if request failed

    Raises:
        ValueError: If character name is invalid
    """
    ...
```

---

## Running Tests

### Test Structure

```
tests/
├── unit/              # Fast, isolated tests
│   ├── test_parsers.py
│   ├── test_validators.py
│   └── test_http_client.py
├── integration/       # Tests with mocked web requests
│   ├── test_scraper.py
│   └── test_reminder_fetcher.py
└── conftest.py        # Shared test fixtures
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_parsers.py

# Run with coverage
pytest --cov=src --cov-report=html

# Run only unit tests (fast)
pytest -m unit

# Run with verbose output
pytest -v

# Run in parallel (faster)
pytest -n auto
```

### Writing Tests

- Use descriptive test names: `test_parse_edition_from_icon_returns_correct_edition()`
- Test edge cases: empty strings, None, invalid input
- Mock external dependencies (HTTP requests, file I/O)
- Aim for 80%+ code coverage

Example test:

```python
import pytest
from src.scrapers.parsers import parse_edition_from_icon

def test_parse_edition_from_icon_extracts_correct_edition():
    """Should extract edition from icon path."""
    result = parse_edition_from_icon("src/assets/icons/tb/washerwoman_g.webp")
    assert result == "tb"

def test_parse_edition_from_icon_returns_unknown_for_invalid_path():
    """Should return 'unknown' for malformed paths."""
    result = parse_edition_from_icon("invalid/path")
    assert result == "unknown"

def test_parse_edition_from_icon_prevents_path_traversal():
    """Should reject path traversal attempts."""
    with pytest.raises(ValueError):
        parse_edition_from_icon("../../etc/passwd")
```

---

## Making Changes

### Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/bug-description
   ```

2. **Make your changes**
   - Write code following the style guidelines
   - Add tests for new functionality
   - Update documentation if needed

3. **Run quality checks**
   ```bash
   # Formatting
   ruff format src/

   # Linting
   ruff check src/ --fix

   # Type checking
   mypy src/

   # Tests
   pytest
   ```

4. **Commit your changes**

   Use [Conventional Commits](https://www.conventionalcommits.org/) format:

   ```bash
   git add .
   git commit -m "feat(scraper): add async batch fetching for wiki pages"
   ```

   **Commit message types**:
   - `feat`: New feature
   - `fix`: Bug fix
   - `docs`: Documentation changes
   - `style`: Code style changes (formatting, etc.)
   - `refactor`: Code refactoring
   - `test`: Adding or updating tests
   - `chore`: Maintenance tasks
   - `perf`: Performance improvements
   - `security`: Security fixes

   **Examples**:
   ```
   feat(parsers): add input validation to prevent path traversal
   fix(http_client): correct retry backoff calculation
   docs(readme): update installation instructions
   test(validators): add schema validation tests
   security(reminder_fetcher): add URL validation to prevent SSRF
   ```

5. **Push your branch**
   ```bash
   git push origin feature/your-feature-name
   ```

---

## Pull Request Process

### Before Submitting

- [ ] All tests pass (`pytest`)
- [ ] Code is formatted (`ruff format`)
- [ ] No linting errors (`ruff check`)
- [ ] Type checking passes (`mypy src/`)
- [ ] Documentation is updated
- [ ] Commits follow Conventional Commits format

### PR Template

When creating a PR, include:

```markdown
## Summary
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Security fix

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No security vulnerabilities introduced
- [ ] Backwards compatible (or breaking changes documented)

## Related Issues
Closes #123
```

### Review Process

1. Automated checks must pass (CI workflow)
2. At least one maintainer approval required
3. All review comments must be resolved
4. No merge conflicts with main branch

### After Merge

- Delete your feature branch
- Pull latest changes from main

---

## Security Guidelines

### Critical Rules

1. **Never commit secrets**
   - API keys, passwords, tokens
   - Use environment variables instead
   - Pre-commit hooks will detect some secrets

2. **Validate all external input**
   - Character names, edition IDs, URLs
   - Prevent path traversal attacks
   - Prevent SSRF attacks

3. **Sanitize HTML/text from untrusted sources**
   - Wiki content could be malicious
   - Use the `sanitize_text()` helper

4. **Use allowed lists, not blocked lists**
   - Example: Only allow specific file extensions
   - Example: Only allow bloodontheclocktower.com domain

### Security Checklist

When adding code that:
- **Reads from files**: Validate path doesn't contain `..` or absolute paths
- **Makes HTTP requests**: Validate URL matches expected domain
- **Processes user input**: Sanitize and validate
- **Writes to files**: Ensure destination is within expected directory

### Reporting Security Issues

**DO NOT** open a public GitHub issue for security vulnerabilities.

Instead, email: [maintainer email] with:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

---

## Release Process

Releases are automated via GitHub Actions:

### Automated Releases

1. **Daily Schedule**: Runs at midnight UTC
2. **Manual Trigger**: Via GitHub Actions UI
3. **On Data Changes**: When data/ folder is modified

### Release Criteria

- All tests pass
- Data passes schema validation
- ContentHash differs from previous release

### Version Format

- `YYYY.MM.DD-rN` (date-based with run number)
- Example: `2025.12.02-r1`

### Rollback Procedure

If a bad release is published:

1. **Immediate**: Delete the GitHub release
2. **Revert changes**:
   ```bash
   git revert <commit-hash>
   git push origin main
   ```
3. **Trigger new release**: Via manual workflow dispatch
4. **Notify users**: Update release notes

---

## Common Tasks

### Adding a New Character Field

1. Update `src/scrapers/extractors.py` to extract the field
2. Update `src/validators/schema_validator.py` to validate it
3. Add tests in `tests/unit/test_extractors.py`
4. Update `data/manifest.json` schema version if breaking change
5. Document in CHANGELOG.md

### Fixing a Scraping Bug

1. Identify the bug (usually in `src/scrapers/extractors.py`)
2. Write a failing test first (TDD)
3. Fix the bug
4. Verify test passes
5. Check if other similar code needs fixing

### Optimizing Performance

1. Profile the code: `python -m cProfile -o output.prof src/scrapers/character_scraper.py`
2. Identify bottlenecks
3. Optimize (async, caching, batching)
4. Measure improvement
5. Document in commit message

---

## Getting Help

- **Questions**: Open a [GitHub Discussion](../../discussions)
- **Bugs**: Open a [GitHub Issue](../../issues)
- **Discord**: [BOTC Community Server](https://discord.gg/bloodontheclocktower)

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

## Attribution

Blood on the Clocktower © The Pandemonium Institute. This is an unofficial fan project.
