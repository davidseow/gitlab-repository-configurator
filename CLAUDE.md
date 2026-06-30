# CLAUDE.md - Development Guide for AI Assistants

This document provides comprehensive guidance for AI assistants working with the gitlab-repository-configurator codebase.

## Project Overview

**gitlab-repository-configurator** is a Python CLI application that serves as a single source of truth for configuring GitLab repositories within a group. It enables batch configuration of merge request rules and Slack integrations across multiple repositories with an interactive, user-friendly workflow.

### Key Characteristics
- **Type**: Command-line interface (CLI) application
- **Language**: Python 3.9+ (supports 3.9, 3.10, 3.11, 3.12)
- **Architecture**: Modular design with clear separation of concerns
- **Quality Approach**: Test-Driven Development (TDD) with 28+ unit tests
- **Package Manager**: UV (modern, fast Python package manager)
- **Code Quality**: Ruff (unified linting and formatting)
- **License**: MIT

### Core Capabilities
- Batch configuration of all repositories in a GitLab group
- Automatic discovery of nested group repositories
- Merge request rules configuration (merge method, discussion resolution, pipeline requirements)
- Slack integration for notifications
- Dry-run mode for previewing changes
- Glob pattern exclusions for skipping specific repositories
- Comprehensive error handling and logging

## Codebase Structure

### Directory Layout
```
gitlab-repository-configurator/
├── main.py                      # CLI entry point (67 lines)
├── config_loader.py             # YAML config loading (53 lines)
├── gitlab_client.py             # GitLab API wrapper (95 lines)
├── repository_configurator.py   # Orchestration logic (103 lines)
├── tests/                       # Test suite (550+ lines)
│   ├── __init__.py
│   ├── test_cli.py             # CLI command tests (31 lines)
│   ├── test_config_loader.py   # Config validation tests (105 lines)
│   ├── test_gitlab_client.py   # API interaction tests (224 lines)
│   ├── test_repository_configurator.py  # Orchestration tests (118 lines)
│   └── test_error_handling.py  # Error scenario tests (72 lines)
├── .gitlab-ci.yml              # CI/CD pipeline
├── Makefile                    # Build automation
├── pyproject.toml              # Project config & dependencies
├── config.yaml.example         # Example configuration
└── README.md                   # User-facing documentation
```

### Core Modules

#### main.py (67 lines) - CLI Entry Point
**Purpose**: Click-based CLI command entry point, error handling, and configuration initialization.

**Key Components**:
- `configure()` - Main CLI command with `--config` and `--dry-run` options
- Initializes `ConfigLoader`, `GitLabClient`, and `RepositoryConfigurator`
- Handles three custom exception types: `ConfigError`, `GitLabError`, generic exceptions
- Logging setup with INFO level and formatted output

**Entry Point Flow**:
```
main.py::configure()
  ├─ ConfigLoader.load() → parse & validate YAML
  ├─ Extract GitLab config → get token from config or GITLAB_TOKEN env var
  ├─ GitLabClient() → connect to GitLab API
  ├─ RepositoryConfigurator() → orchestration
  └─ configure_all() → execute configuration
```

**Error Handling**: Catches `ConfigError`, `GitLabError`, and generic exceptions, exits with code 1.

#### config_loader.py (53 lines) - Configuration Management
**Purpose**: YAML parsing, validation, and configuration extraction.

**Key Components**:
- `ConfigError` - Custom exception for configuration issues
- `ConfigLoader` class - Handles config file loading and validation
- `REQUIRED_FIELDS` - List of mandatory top-level config keys: `["gitlab", "merge_request_rules"]`

**Key Methods**:
- `load()` - Parses YAML file and validates structure
- `_validate_config()` - Ensures required fields and nested gitlab config
- `get_gitlab_config()` - Extracts GitLab connection settings
- `get_exclusions()` - Returns glob patterns for repository exclusion
- `get_merge_request_rules()` - Extracts merge request configuration
- `get_slack_config()` - Extracts Slack integration settings (optional)

**Required Config Fields**:
```yaml
gitlab:
  url: <string>
  token: <string> (or use GITLAB_TOKEN env var)
  group_id: <int>
merge_request_rules:
  merge_method: <rebase|ff|ff+commit>
  only_allow_merge_if_all_discussions_are_resolved: <bool>
  only_allow_merge_if_pipeline_succeeds: <bool>
exclusions: [<glob-patterns>]  # Optional
slack: {enabled, webhook_url, notify_on_push, notify_on_merge_requests}  # Optional
```

#### gitlab_client.py (95 lines) - GitLab API Wrapper
**Purpose**: Abstraction layer for GitLab API interactions using the python-gitlab library.

**Key Components**:
- `GitLabError` - Custom exception for API-related errors
- `GitLabClient` class - Manages connection and API calls

**Key Methods**:
- `__init__()` - Initializes connection to GitLab instance
- `get_group_projects()` - Recursively discovers all repositories in a group (including nested)
- `apply_merge_rules()` - Configures merge request rules on a project
- `enable_slack_integration()` - Enables Slack notifications on a project

**Features**:
- Error handling for API failures with graceful fallbacks
- Nested group repository discovery
- Project-level merge rule configuration
- Slack webhook integration for notifications

#### repository_configurator.py (103 lines) - Orchestration Logic
**Purpose**: Main orchestration of configuration workflow, user interaction, and rule application.

**Key Components**:
- `RepositoryConfigurator` class - Manages configuration workflow

**Key Methods**:
- `configure_all()` - Main orchestration entry point
- `_get_all_projects()` - Retrieves all projects with exclusion filtering
- `_matches_exclusion_pattern()` - Fnmatch-based glob pattern matching for exclusions
- `_confirm_with_user()` - Interactive confirmation prompts

**Workflow**:
1. Fetch all repositories in group
2. Apply exclusion filters (fnmatch/glob patterns)
3. Confirm with user at group level
4. For each repository:
   - Display repository details
   - Request per-repository confirmation
   - Apply merge request rules
   - Apply Slack integration (if enabled)
5. Handle dry-run mode (preview without applying)

**Design Pattern**: Dependency injection of `GitLabClient` for testability.

## Technology Stack

### Runtime Dependencies
| Package | Version | Purpose |
|---------|---------|---------|
| python-gitlab | ≥4.2.0 | GitLab API client |
| slack-sdk | ≥3.23.0 | Slack integration |
| click | ≥8.1.0 | CLI framework |
| pyyaml | ≥6.0 | YAML parsing |

### Development Dependencies
| Package | Version | Purpose |
|---------|---------|---------|
| pytest | ≥7.4.0 | Testing framework |
| pytest-mock | ≥3.11.1 | Mocking utilities |
| ruff | ≥0.1.0 | Linting & formatting |

### Build System
- **Package Manager**: UV (modern Python dependency management)
- **Build Automation**: Makefile with UV integration
- **CI/CD**: GitLab CI with Python 3.11 base image

## Development Workflow

### Initial Setup

```bash
# 1. Clone repository
git clone <repository-url>
cd gitlab-repository-configurator

# 2. Install UV (one-time)
pip install uv

# 3. Install project dependencies
make install

# 4. Create configuration (from example)
cp config.yaml.example config.yaml
```

### Common Development Commands

```bash
make install        # Install dependencies (one-time setup)
make test          # Run pytest test suite with verbose output
make lint          # Check code style with ruff
make format        # Auto-format code with ruff
make check         # Run linting and format checks (no changes)
make fix           # Auto-fix all formatting and linting issues
make run           # Run CLI (requires CONFIG env var or --config flag)
make dry-run       # Preview changes without applying
make clean         # Remove build artifacts and cache
make help          # Display all available commands
```

### Pre-Commit Checklist

Before committing changes:
```bash
make check    # Verify all linting and formatting
make test     # Ensure all tests pass
make fix      # Auto-fix any remaining issues
```

### Testing Strategy

**Run all tests**:
```bash
make test                           # Via Makefile
pytest tests/ -v                    # Direct pytest
pytest tests/test_gitlab_client.py  # Run specific module
```

**Test Coverage** (28+ tests across 5 files):
- `test_cli.py` (31 lines) - CLI command parsing, error handling
- `test_config_loader.py` (105 lines) - YAML parsing, validation, config extraction
- `test_gitlab_client.py` (224 lines) - API interactions, repository discovery, error scenarios
- `test_repository_configurator.py` (118 lines) - Filtering, confirmation flows, rule application
- `test_error_handling.py` (72 lines) - Error scenarios, edge cases, API failures

**Testing Approach**:
- Test-Driven Development (TDD): write tests first
- Unit tests with mocking (pytest-mock for GitLab API calls)
- Test isolation using temporary filesystems (click.testing.CliRunner)
- Comprehensive error scenario coverage

### TDD Development Cycle

1. **Write failing test** - Define expected behavior
2. **Implement feature** - Make test pass with minimal code
3. **Run all tests** - Ensure no regressions
4. **Refactor** - Improve code quality while tests remain green
5. **Format and lint** - Run `make fix` to auto-correct style

## Code Conventions

### Formatting Standards (Ruff)

**Line Length**: 100 characters (set in pyproject.toml)
**Quote Style**: Double quotes
**Indent**: Spaces (auto-detected)
**Line Endings**: Auto

```python
# ✓ Good - double quotes, clear naming
message = "Configuration loaded successfully"

# ✗ Bad - single quotes
message = 'Configuration loaded successfully'
```

### Linting Rules (Selected)

Ruff configuration enforces these rules:
- `E, W` - pycodestyle errors and warnings
- `F` - PyFlakes (undefined names, unused imports)
- `I` - isort (import sorting and organization)
- `UP` - pyupgrade (modern Python syntax)
- `B` - flake8-bugbear (common bugs)
- `C4` - flake8-comprehensions (list/dict/set comprehensions)
- `PIE` - flake8-pie (miscellaneous best practices)

**Ignored Rules**:
- `E501` - Line too long (handled by formatter)
- `W292` - Blank line at EOF (handled by formatter)
- `F841` - Unused variables in tests (allowed in test code)

### Comment Philosophy

**Minimize comments**. Only add comments for:
- **Non-obvious logic**: Subtle invariants or constraints not apparent from code
- **Workarounds**: Explanations for specific bug fixes or version-specific behavior
- **Why, not What**: Focus on reasoning, not description (good naming already tells what code does)

```python
# ✓ Good - explains WHY
# Retry on rate limit to handle GitLab API throttling (15-minute window)
time.sleep(60)

# ✗ Bad - just repeats what code says
# Sleep for 60 seconds
time.sleep(60)
```

### Import Organization

Imports are sorted via isort (integrated with Ruff):
1. Standard library imports
2. Third-party imports
3. Local application imports (gitlab_client, repository_configurator, config_loader)

```python
import logging
import os

import click
import yaml

from config_loader import ConfigError, ConfigLoader
from gitlab_client import GitLabClient, GitLabError
```

### Error Handling

Use custom exceptions for domain-specific errors:

```python
# Define custom exceptions (once per module)
class ConfigError(Exception):
    pass

class GitLabError(Exception):
    pass

# Raise with descriptive messages
raise ConfigError(f"Missing required field: {field}")

# Catch and handle appropriately
try:
    config = loader.load()
except ConfigError as e:
    click.echo(f"Configuration Error: {e}", err=True)
    raise SystemExit(1) from e
```

### Module Design Patterns

**Single Responsibility**: Each module handles one concern
- `config_loader.py` - Configuration parsing only
- `gitlab_client.py` - API interactions only
- `repository_configurator.py` - Workflow orchestration only
- `main.py` - CLI interface only

**Dependency Injection**: Inject dependencies for testability
```python
# Good - dependency injected, testable
configurator = RepositoryConfigurator(gitlab_client, config_data)

# Avoid - tightly coupled
configurator = RepositoryConfigurator()
```

**Type Hints**: Use for clarity (Python 3.9+ syntax)
```python
def load(self) -> dict[str, Any]:
    ...

def get_exclusions(self, config: dict[str, Any]) -> list[str]:
    ...
```

## Testing Strategy

### Test Structure

Tests follow pytest conventions:
- **Test files**: `test_*.py` in `tests/` directory
- **Test classes**: `Test*` (e.g., `TestCLI`, `TestConfigLoader`)
- **Test methods**: `test_*` (e.g., `test_configure_with_missing_config`)

### Example Test Pattern

```python
class TestConfigLoader:
    def test_load_valid_config(self):
        # Arrange: Set up test data
        with runner.isolated_filesystem():
            with open("config.yaml", "w") as f:
                f.write("...")
            
            # Act: Execute the code
            loader = ConfigLoader("config.yaml")
            config = loader.load()
            
            # Assert: Verify results
            assert config["gitlab"]["url"] == "https://gitlab.com"
    
    def test_load_missing_config(self):
        # Should raise ConfigError for missing files
        loader = ConfigLoader("nonexistent.yaml")
        with pytest.raises(ConfigError):
            loader.load()
```

### Mocking Strategy

Use pytest-mock for API interactions:
```python
def test_configure_applies_rules(mocker):
    # Mock GitLab API calls
    mock_client = mocker.Mock(spec=GitLabClient)
    mock_client.get_group_projects.return_value = [...]
    
    # Test with mocked client
    configurator = RepositoryConfigurator(mock_client, config_data)
    configurator.configure_all()
    
    # Verify API was called correctly
    mock_client.apply_merge_rules.assert_called_once()
```

### Running Tests with Coverage

```bash
# Run with coverage report
pytest tests/ --cov=. --cov-report=html

# View coverage in browser
open htmlcov/index.html
```

## CI/CD and Quality Gates

### GitLab CI Pipeline (.gitlab-ci.yml)

**Container**: Python 3.11
**Cache**: `.uv/` directory (UV package cache)

**Pipeline Stages**:

1. **Lint Stage** (fail-fast)
   - Runs `make check` (linting + format checks)
   - Fails if any style issues found
   - `allow_failure: false`

2. **Test Stage**
   - Runs `make test` (pytest suite)
   - Captures coverage percentage
   - Pattern: `/TOTAL.*\s+(\d+%)$/`
   - Fails if any tests fail
   - `allow_failure: false`

**Pre-stage Setup**:
```yaml
before_script:
  - pip install uv              # Install package manager
  - uv sync --all-extras        # Install all dependencies
```

### Quality Standards

All changes must:
- ✓ Pass ruff linting (`make lint`)
- ✓ Pass ruff formatting (`make format-check`)
- ✓ Pass all tests (`make test`)
- ✓ Have no broken imports
- ✓ Follow code conventions

## Configuration and Environment

### YAML Configuration Structure

```yaml
gitlab:
  url: https://gitlab.com              # Required: GitLab instance URL
  token: your-token                    # Optional: use GITLAB_TOKEN env var
  group_id: 123                        # Required: GitLab group ID

merge_request_rules:                   # Required
  merge_method: rebase                 # rebase | ff | ff+commit
  only_allow_merge_if_all_discussions_are_resolved: true
  only_allow_merge_if_pipeline_succeeds: true
  require_approval_count: 1

exclusions:                            # Optional
  - archive-*                          # Glob patterns (fnmatch syntax)
  - temp-*
  - legacy_*

slack:                                 # Optional
  enabled: true
  webhook_url: https://hooks.slack.com/services/...
  notify_on_push: true
  notify_on_merge_requests: true
```

### Environment Variables

- **GITLAB_TOKEN** (recommended): GitLab personal access token
  ```bash
  export GITLAB_TOKEN=glpat_xxx...
  ```

### Exclusion Patterns

Exclusion patterns use fnmatch (glob) syntax:
```python
import fnmatch

# Patterns
"archive-*"      # Matches: archive-1, archive-old, archive-staging
"test_*"         # Matches: test_repo, test_project, test_v2
"*-legacy"       # Matches: db-legacy, api-legacy, client-legacy
"deprecated"     # Exact match: deprecated
```

## Git Workflow

### Branch Naming

Feature branches follow the pattern:
```
claude/feature-description-xxxxx
```

Example: `claude/gitlab-group-repo-config-kx5f3o`

### Commit Messages

Write clear, descriptive commit messages:
```
Add support for glob patterns in exclusion list

This allows users to exclude multiple repositories using wildcard
patterns like 'archive-*' instead of listing each one individually.
```

### Pre-Push Checklist

Before pushing to GitLab:
```bash
make check      # Verify linting and formatting
make test       # Run full test suite
make fix        # Auto-fix any remaining issues
```

## Key Patterns and Examples

### Adding a New CLI Option

**Pattern**: Use Click decorators in `main.py`

```python
@click.command()
@click.option("--config", required=True, type=click.Path(exists=True))
@click.option("--dry-run", is_flag=True, help="Preview only")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def configure(config: str, dry_run: bool, verbose: bool) -> None:
    """Configure GitLab repositories..."""
```

### Adding a New API Operation

**Pattern**: Add method to `GitLabClient`, test with mocks

```python
class GitLabClient:
    def protect_branches(self, project_id: int, branch_pattern: str) -> None:
        """Protect branches matching pattern."""
        try:
            project = self.gl.projects.get(project_id)
            project.protectedbranches.create({"name": branch_pattern})
        except Exception as e:
            raise GitLabError(f"Failed to protect branches: {e}") from e
```

**Test Pattern**:
```python
def test_protect_branches(mocker):
    mock_client = mocker.Mock(spec=GitLabClient)
    client = GitLabClient("https://gitlab.com", "token")
    
    # Mock the API response
    mocker.patch.object(client, "protect_branches")
    
    # Test
    client.protect_branches(123, "main")
    client.protect_branches.assert_called_once_with(123, "main")
```

### Adding Configuration Extraction

**Pattern**: Add method to `ConfigLoader`, validate in `_validate_config()`

```python
class ConfigLoader:
    def get_branch_protection(self, config: dict[str, Any]) -> dict[str, Any]:
        return config.get("branch_protection", {})
    
    def _validate_config(self, config: dict[str, Any]) -> None:
        # Existing validation...
        if "branch_protection" in config:
            if not isinstance(config["branch_protection"], dict):
                raise ConfigError("branch_protection must be a dict")
```

## Common Pitfalls to Avoid

1. **Don't skip tests** - Write tests before implementation (TDD)
2. **Don't log secrets** - Never log tokens or sensitive data
3. **Don't catch generic exceptions** - Use specific exception types
4. **Don't assume GitLab state** - Always check API responses
5. **Don't hardcode values** - Use configuration instead
6. **Don't ignore dry-run mode** - Respect the flag throughout workflow
7. **Don't forget error handling** - API calls can fail; handle gracefully

## Quick Reference

### Check Before Committing
```bash
make check    # Verify style and formatting
make test     # Run all tests
make fix      # Auto-fix issues
```

### File a Bug Report
Include:
- Python version (`python --version`)
- Error message and traceback
- Configuration file (sanitized)
- Steps to reproduce

### Key Files by Task
| Task | File |
|------|------|
| Add CLI option | `main.py` |
| Add configuration field | `config_loader.py` + `pyproject.toml` |
| Add GitLab API operation | `gitlab_client.py` |
| Add orchestration logic | `repository_configurator.py` |
| Add tests | `tests/test_*.py` (match module) |
| Update dependencies | `pyproject.toml` |
| Add automation command | `Makefile` |
| Update pipeline | `.gitlab-ci.yml` |

## Related Documentation

- **User Guide**: [README.md](./README.md) - Installation, usage, configuration
- **Example Config**: [config.yaml.example](./config.yaml.example)
- **Ruff Configuration**: [pyproject.toml](./pyproject.toml#L51-L88)
- **Pytest Configuration**: [pyproject.toml](./pyproject.toml#L89-L101)
- **CI/CD Pipeline**: [.gitlab-ci.yml](./.gitlab-ci.yml)
