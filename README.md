# GitLab Repository Configurator

A single source of truth for configuring repositories within a GitLab group. Streamline the process of applying consistent merge request rules and Slack integration settings across all repositories in a group.

## Features

- **Batch Configuration**: Apply settings to all repositories in a GitLab group
- **Nested Group Support**: Automatically discovers repositories in sub-groups
- **Exclusion List**: Exclude specific repositories from configuration
- **Merge Request Rules**: Configure merge methods, require all discussions resolved, require pipeline success
- **Slack Integration**: Enable Slack notifications for merge requests and push events
- **Confirmation Prompts**: Explicit confirmation at group and per-repository level
- **Dry-Run Mode**: Preview changes before applying
- **Robust Error Handling**: Graceful handling of API failures with detailed error messages
- **Logging**: Track all API calls and operations

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd gitlab-repository-configurator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

### 1. Create Configuration File

Copy the example configuration:
```bash
cp config.yaml.example config.yaml
```

### 2. Edit Configuration

Edit `config.yaml` with your settings:
```yaml
gitlab:
  url: https://gitlab.com
  token: your-personal-access-token  # Or use GITLAB_TOKEN env var
  group_id: 123

exclusions:
  - archive-repo
  - deprecated-project

merge_request_rules:
  merge_method: rebase              # Options: rebase, ff, ff+commit
  only_allow_merge_if_all_discussions_are_resolved: true
  only_allow_merge_if_pipeline_succeeds: true
  require_approval_count: 1

slack:
  enabled: true
  webhook_url: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
  notify_on_push: true
  notify_on_merge_requests: true
```

### 3. Set GitLab Token

You can set the token in two ways:

**Option A**: In config.yaml (not recommended for sensitive environments)
```yaml
gitlab:
  token: your-personal-access-token
```

**Option B**: Using environment variable (recommended)
```bash
export GITLAB_TOKEN=your-personal-access-token
```

## Exclusion Patterns (Glob Matching)

The exclusion list supports glob patterns using fnmatch syntax. This allows you to exclude repositories based on naming patterns rather than listing each one individually.

### Common Patterns

- `*.backup` - Matches any repository ending with `.backup` (e.g., `project.backup`, `data.backup`)
- `archive-*` - Matches repositories starting with `archive-` (e.g., `archive-2023`, `archive-old`)
- `staging-*` - Matches repositories starting with `staging-` (e.g., `staging-dev`, `staging-qa`)
- `test_*` - Matches repositories starting with `test_` (e.g., `test_repo`, `test_project`)
- `*-temp` - Matches repositories ending with `-temp` (e.g., `build-temp`, `merge-temp`)
- `[abc]*` - Matches repositories starting with a, b, or c
- `exact_name` - Exact match (without wildcards)

### Advanced fnmatch Syntax

- `*` - Matches any characters (including none)
- `?` - Matches any single character
- `[abc]` - Matches any of a, b, or c
- `[!abc]` - Matches any character except a, b, c
- `[a-z]` - Matches any character in range a to z

### Configuration Example

```yaml
exclusions:
  # Glob patterns
  - "*.backup"
  - "*.temp"
  - "archive-*"
  - "staging-*"
  - "test_*"
  - "[temporary]*"
  # Exact matches (no wildcards)
  - "deprecated-project"
  - "internal-only"
  - "do-not-configure"
```

### How It Works

1. The tool reads exclusion patterns from your configuration
2. For each repository discovered, it checks if the repository name matches any exclusion pattern
3. Matching repositories are excluded from configuration
4. Pattern matching is case-sensitive

## Usage

### Basic Usage
```bash
python main.py --config config.yaml
```

### Dry-Run Mode
Preview changes without applying:
```bash
python main.py --config config.yaml --dry-run
```

### Get Help
```bash
python main.py --help
```

## Workflow

1. Load configuration from YAML file
2. Discover all repositories in the specified group (including sub-groups)
3. Filter out excluded repositories
4. Display repositories and request confirmation to proceed
5. For each repository:
   - Display repository name and URL
   - Apply merge request rules
   - Configure Slack integration
   - Request confirmation before proceeding to next repository
6. Display summary report with success/failure counts

## Example Session

```
Loading repositories...

============================================================
Repositories to configure:
============================================================
1. project-a
   URL: https://gitlab.com/group/project-a
2. project-b
   URL: https://gitlab.com/group/project-b
3. project-c
   URL: https://gitlab.com/group/project-c
============================================================

Proceed with configuration? (yes/no): yes

Configuring project-a...
✓ Updated merge request rules for project-a
✓ Enabled Slack integration for project-a
Continue to next repository? (yes/no): yes

Configuring project-b...
✓ Updated merge request rules for project-b
✓ Enabled Slack integration for project-b
Continue to next repository? (yes/no): yes

Configuring project-c...
✓ Updated merge request rules for project-c
✓ Enabled Slack integration for project-c
Continue to next repository? (yes/no): no
Configuration stopped.

============================================================
Summary: 3 successful, 0 failed
============================================================
```

## Security Best Practices

1. **Never commit tokens**: Use environment variables or .gitignore for config.yaml
2. **Restrict permissions**: Give the GitLab token only the necessary permissions
3. **Validate inputs**: The tool validates group IDs and repository names
4. **Secure storage**: Store Slack webhook URLs securely
5. **No logging of secrets**: Error messages don't expose tokens or sensitive data

## Testing

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test Suite
```bash
pytest tests/test_gitlab_client.py -v
pytest tests/test_config_loader.py -v
pytest tests/test_repository_configurator.py -v
pytest tests/test_error_handling.py -v
```

### Run with Coverage Report
```bash
pytest tests/ --cov=. --cov-report=html
open htmlcov/index.html
```

## Architecture

### Modules

- **main.py**: Click-based CLI entry point
- **gitlab_client.py**: GitLab API wrapper with error handling
- **repository_configurator.py**: Main orchestration and user interaction logic
- **config_loader.py**: YAML configuration loading and validation

### Design Principles

- **Single Responsibility**: Each module has one clear purpose
- **Dependency Injection**: Dependencies injected for testability
- **Separation of Concerns**: Clean separation between I/O, API, and business logic
- **Componentized Architecture**: Easy to extend and maintain
- **TDD Approach**: 28 comprehensive unit tests covering all components

### Test Coverage

- **Config Loading**: YAML parsing, validation, error handling
- **GitLab Client**: Repository discovery, API interactions, error scenarios
- **Repository Configurator**: Filtering, confirmation flows, rule application
- **CLI**: Command-line parsing, error reporting
- **Error Handling**: API failures, missing data, validation errors

## Troubleshooting

### Authentication Failed
- Verify your GitLab token is valid and has access to the group
- Check that the token hasn't expired
- Ensure GITLAB_TOKEN environment variable is set (if not using config file)

### Group Not Found
- Verify the group ID is correct
- Ensure your token has access to the group
- Check the GitLab URL is correct

### Permission Denied
- Ensure your token has "api" and "write_repository" scopes
- Verify you have write access to the repositories

### Slack Integration Failed
- Verify the webhook URL is correct
- Check that the Slack workspace accepts the webhook
- Ensure notify_on_merge_requests or notify_on_push is enabled

## Contributing

- Follow TDD approach: write tests first
- Keep code concise and clear
- Add minimal comments (only for non-obvious logic)
- Run tests before committing: `pytest tests/`
- Ensure all 28 tests pass

## License

See LICENSE file for details
