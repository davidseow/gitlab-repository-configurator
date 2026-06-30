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

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

1. Copy the example configuration:
```bash
cp config.yaml.example config.yaml
```

2. Edit `config.yaml` with your settings:
```yaml
gitlab:
  url: https://gitlab.com
  token: your-personal-access-token
  group_id: 123

exclusions:
  - repo-to-exclude
  - another-repo

merge_request_rules:
  merge_method: rebase
  only_allow_merge_if_all_discussions_are_resolved: true
  only_allow_merge_if_pipeline_succeeds: true

slack:
  enabled: true
  webhook_url: https://hooks.slack.com/services/...
  notify_on_merge_requests: true
```

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

## Security

- Store GitLab tokens in environment variables: `GITLAB_TOKEN`
- Never commit `config.yaml` with actual tokens
- Use `.gitignore` to exclude configuration files with secrets

## Testing

Run tests with pytest:
```bash
pytest tests/
```

Run tests with coverage:
```bash
pytest tests/ --cov=. --cov-report=html
```

## Architecture

### Modules

- **main.py**: CLI entry point using Click framework
- **gitlab_client.py**: GitLab API wrapper for repository operations
- **repository_configurator.py**: Main orchestration logic
- **config_loader.py**: YAML configuration loading and validation

### Design Principles

- **Single Responsibility**: Each module handles one concern
- **Dependency Injection**: Tests can mock dependencies
- **Separation of Concerns**: I/O, API calls, and business logic are separate
- **Componentized**: Easy to extend and test individually

## Workflow

1. Load configuration from YAML file
2. Discover all repositories in the specified group (including sub-groups)
3. Filter out excluded repositories
4. Display repositories and request confirmation
5. For each repository:
   - Display current settings
   - Request per-repository confirmation
   - Apply merge request rules
   - Enable Slack integration
6. Display summary report

## Error Handling

- Invalid configuration raises `ConfigError`
- GitLab API errors are caught and reported
- Missing credentials will prompt for `GITLAB_TOKEN` environment variable

## Contributing

- Write tests first (TDD approach)
- Keep code concise and clear
- Add minimal comments (only for non-obvious logic)
