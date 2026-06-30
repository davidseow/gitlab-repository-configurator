import pytest
from unittest.mock import Mock
from gitlab_client import GitLabClient, GitLabError
from repository_configurator import RepositoryConfigurator


class TestErrorHandling:
    def test_gitlab_client_handles_missing_group(self):
        client = GitLabClient("https://gitlab.com", "test-token")
        client.gl = Mock()
        client.gl.groups.get.side_effect = Exception("Not found")

        with pytest.raises(GitLabError) as exc_info:
            client.get_group_repositories(group_id=999, exclude_list=[])

        assert "Failed to fetch repositories" in str(exc_info.value)

    def test_gitlab_client_handles_missing_project(self):
        client = GitLabClient("https://gitlab.com", "test-token")
        client.gl = Mock()
        client.gl.projects.get.side_effect = Exception("Not found")

        with pytest.raises(GitLabError) as exc_info:
            client.update_merge_request_rules(project_id=999, rules={})

        assert "Failed to update" in str(exc_info.value)

    def test_slack_integration_requires_webhook_url(self):
        client = GitLabClient("https://gitlab.com", "test-token")
        client.gl = Mock()

        with pytest.raises(GitLabError) as exc_info:
            client.enable_slack_integration(
                project_id=1,
                slack_settings={"enabled": True},
            )

        assert "webhook_url" in str(exc_info.value).lower()

    def test_apply_rules_handles_gitlab_error(self):
        mock_client = Mock()
        mock_client.update_merge_request_rules.side_effect = GitLabError("API Error")

        config = {
            "gitlab": {"group_id": 1},
            "merge_request_rules": {"merge_method": "rebase"},
            "slack": {"enabled": False},
        }

        configurator = RepositoryConfigurator(mock_client, config)
        mock_repo = Mock(id=1, name="test-repo")

        result = configurator.apply_rules_to_repository(mock_repo)
        assert result is False

    def test_dry_run_returns_true(self):
        mock_client = Mock()
        config = {
            "gitlab": {"group_id": 1},
            "dry_run": True,
            "merge_request_rules": {"merge_method": "rebase"},
            "slack": {"enabled": True, "webhook_url": "https://hooks.slack.com"},
        }

        configurator = RepositoryConfigurator(mock_client, config)
        mock_repo = Mock(id=1, name="test-repo")

        result = configurator.apply_rules_to_repository(mock_repo)
        assert result is True
        mock_client.update_merge_request_rules.assert_not_called()
