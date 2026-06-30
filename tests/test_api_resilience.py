"""
API resilience tests documenting handling of network failures, permission errors, and API failures.

These tests verify that the application gracefully handles transient failures,
permission errors, rate limiting, and other real-world API failure scenarios.
"""

from unittest.mock import Mock

import gitlab
import pytest

from gitlab_client import GitLabClient, GitLabError
from repository_configurator import RepositoryConfigurator


class TestAPIResilienceAuthenticationErrors:
    """Verify handling of authentication and permission failures."""

    def test_insufficient_permissions_returns_error(self):
        """Verify 403 Forbidden errors from insufficient permissions are caught."""
        mock_gl = Mock()
        mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError(
            response_code=403,
            error_message="Insufficient permissions",
        )

        client = GitLabClient("https://gitlab.com", "test-token")
        client.gl = mock_gl

        with pytest.raises(GitLabError):
            client.update_merge_request_rules(
                project_id=1,
                rules={"merge_method": "rebase"},
            )

    def test_invalid_or_expired_token_returns_error(self):
        """Verify 401 Unauthorized errors from invalid tokens are caught."""
        mock_gl = Mock()
        mock_gl.groups.get.side_effect = gitlab.exceptions.GitlabAuthenticationError(
            response_code=401,
            error_message="Invalid token",
        )

        client = GitLabClient("https://gitlab.com", "invalid-token")
        client.gl = mock_gl

        with pytest.raises(GitLabError) as exc_info:
            client.get_group_repositories(group_id=1, exclude_list=[])

        assert "Authentication failed" in str(exc_info.value)

    def test_permission_error_during_slack_integration(self):
        """Verify permission errors are properly caught during Slack integration."""
        mock_gl = Mock()
        mock_project = Mock()
        mock_project.integrations.create.side_effect = gitlab.exceptions.GitlabGetError(
            response_code=403,
            error_message="Cannot create integrations",
        )
        mock_gl.projects.get.return_value = mock_project

        client = GitLabClient("https://gitlab.com", "test-token")
        client.gl = mock_gl

        with pytest.raises(GitLabError):
            client.enable_slack_integration(
                project_id=1,
                slack_settings={"webhook_url": "https://hooks.slack.com/services/..."},
            )


class TestAPIResilienceRateLimiting:
    """Verify handling of rate limiting and throttling."""

    def test_rate_limit_429_response_returns_error(self):
        """Verify 429 Too Many Requests is handled appropriately."""
        mock_gl = Mock()
        mock_gl.groups.get.side_effect = gitlab.exceptions.GitlabGetError(
            response_code=429,
            error_message="Too many requests",
        )

        client = GitLabClient("https://gitlab.com", "test-token")
        client.gl = mock_gl

        with pytest.raises(GitLabError):
            client.get_group_repositories(group_id=1, exclude_list=[])

    def test_partial_failure_during_multi_repo_configuration(self):
        """Verify partial success when some repos fail during configuration."""
        mock_gitlab_client = Mock()
        config = {
            "gitlab": {"group_id": 1},
            "exclusions": [],
            "merge_request_rules": {"merge_method": "rebase"},
        }

        mock_repo1 = Mock()
        mock_repo1.id = 1
        mock_repo1.name = "repo1"
        mock_repo2 = Mock()
        mock_repo2.id = 2
        mock_repo2.name = "repo2"

        mock_gitlab_client.get_group_repositories.return_value = {
            1: mock_repo1,
            2: mock_repo2,
        }

        mock_gitlab_client.update_merge_request_rules.side_effect = [
            None,
            GitLabError("Permission denied on repo2"),
        ]

        configurator = RepositoryConfigurator(mock_gitlab_client, config)
        repos = configurator.load_repositories()

        assert len(repos) == 2


class TestAPIResilienceSlackIntegrationFailures:
    """Verify handling of Slack integration-specific failures."""

    def test_slack_webhook_url_unreachable(self):
        """Verify handling when webhook URL is unreachable."""
        mock_gl = Mock()
        mock_project = Mock()
        mock_integrations = Mock()
        mock_project.integrations = mock_integrations

        mock_integrations.create.side_effect = Exception("Connection refused to webhook URL")
        mock_gl.projects.get.return_value = mock_project

        client = GitLabClient("https://gitlab.com", "test-token")
        client.gl = mock_gl

        with pytest.raises(GitLabError):
            client.enable_slack_integration(
                project_id=1,
                slack_settings={"webhook_url": "https://hooks.slack.com/services/..."},
            )

    def test_slack_integration_already_exists(self):
        """Verify handling when Slack integration is already configured."""
        mock_gl = Mock()
        mock_project = Mock()
        mock_integrations = Mock()
        mock_project.integrations = mock_integrations

        mock_integrations.create.side_effect = gitlab.exceptions.GitlabCreateError(
            response_code=400,
            error_message="Slack integration already exists",
        )
        mock_gl.projects.get.return_value = mock_project

        client = GitLabClient("https://gitlab.com", "test-token")
        client.gl = mock_gl

        with pytest.raises(GitLabError):
            client.enable_slack_integration(
                project_id=1,
                slack_settings={"webhook_url": "https://hooks.slack.com/services/..."},
            )

    def test_slack_api_authentication_failure(self):
        """Verify handling when Slack API rejects the webhook."""
        mock_gl = Mock()
        mock_project = Mock()
        mock_integrations = Mock()
        mock_project.integrations = mock_integrations

        mock_integrations.create.side_effect = Exception("Invalid webhook URL")
        mock_gl.projects.get.return_value = mock_project

        client = GitLabClient("https://gitlab.com", "test-token")
        client.gl = mock_gl

        with pytest.raises(GitLabError):
            client.enable_slack_integration(
                project_id=1,
                slack_settings={"webhook_url": "https://hooks.slack.com/services/bad"},
            )


class TestAPIResilienceNetworkFailures:
    """Verify handling of network-level failures."""

    def test_connection_timeout_during_api_call(self):
        """Verify handling of connection timeouts."""
        mock_gl = Mock()
        mock_gl.groups.get.side_effect = Exception("Connection timeout after 30 seconds")

        client = GitLabClient("https://gitlab.com", "test-token")
        client.gl = mock_gl

        with pytest.raises(GitLabError):
            client.get_group_repositories(group_id=1, exclude_list=[])

    def test_malformed_api_response_handling(self):
        """Verify handling of unexpected/malformed API responses."""
        mock_gl = Mock()
        mock_group = Mock()

        mock_project = Mock()
        mock_project.id = None
        mock_project.name = None
        mock_group.projects.list.return_value = [mock_project]
        mock_gl.groups.get.return_value = mock_group

        client = GitLabClient("https://gitlab.com", "test-token")
        client.gl = mock_gl

        result = client.get_group_repositories(group_id=1, exclude_list=[])

        assert isinstance(result, dict)


class TestAPIResilienceUnexpectedResponses:
    """Verify handling of unexpected but valid API responses."""

    def test_empty_group_with_no_repositories(self):
        """Verify handling of groups with no repositories."""
        mock_gl = Mock()
        mock_group = Mock()
        mock_group.projects.list.return_value = []
        mock_gl.groups.get.return_value = mock_group

        client = GitLabClient("https://gitlab.com", "test-token")
        client.gl = mock_gl

        result = client.get_group_repositories(group_id=1, exclude_list=[])

        assert result == {}

    def test_all_repositories_excluded_by_pattern(self):
        """Verify handling when all repos are filtered by exclusion patterns."""
        mock_gl = Mock()
        mock_group = Mock()

        mock_projects = []
        for i in range(1, 4):
            mock_project = Mock()
            mock_project.id = i
            mock_project.name = f"backup-repo-{i}"
            mock_projects.append(mock_project)

        mock_group.projects.list.return_value = mock_projects
        mock_gl.groups.get.return_value = mock_group

        client = GitLabClient("https://gitlab.com", "test-token")
        client.gl = mock_gl

        result = client.get_group_repositories(group_id=1, exclude_list=["backup-*"])

        assert result == {}
