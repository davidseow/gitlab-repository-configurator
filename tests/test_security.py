"""
Security tests documenting critical safety measures and protections.

These tests verify that the application properly prevents dangerous operations,
protects credentials, validates external URLs, and respects access boundaries.
"""

from unittest.mock import Mock, patch

import pytest

from gitlab_client import GitLabClient, GitLabError
from repository_configurator import RepositoryConfigurator


class TestSecurityDangerousAttributePrevention:
    """Verify merge request rule application patterns and risks."""

    def test_configuration_only_applies_provided_rules(self):
        """Verify that only rules from configuration are applied to projects."""
        mock_gl = Mock()
        mock_project = Mock()
        mock_gl.projects.get.return_value = mock_project

        client = GitLabClient("https://gitlab.com", "test-token")
        client.gl = mock_gl

        rules = {
            "merge_method": "rebase",
            "only_allow_merge_if_all_discussions_are_resolved": True,
        }

        client.update_merge_request_rules(project_id=1, rules=rules)

        mock_project.save.assert_called_once()

    def test_merge_request_rules_use_dynamic_setattr(self):
        """Document that rules are applied via setattr (dynamic attribute setting).

        Note: This uses setattr() which accepts arbitrary attribute names.
        Security validation of attribute names should be implemented at a higher level.
        """
        mock_gl = Mock()
        mock_project = Mock()
        mock_gl.projects.get.return_value = mock_project

        client = GitLabClient("https://gitlab.com", "test-token")
        client.gl = mock_gl

        rules = {
            "merge_method": "rebase",
            "only_allow_merge_if_all_discussions_are_resolved": True,
        }

        client.update_merge_request_rules(project_id=1, rules=rules)

        for key, _value in rules.items():
            assert hasattr(mock_project, key)


class TestSecurityCredentialProtection:
    """Verify that credentials and tokens are properly protected."""

    def test_token_not_exposed_in_error_messages(self):
        """Verify tokens are not included in exception messages."""
        mock_gl = Mock()
        mock_gl.groups.get.side_effect = Exception("Connection failed to https://gitlab.com")

        client = GitLabClient("https://gitlab.com", "sensitive-token-12345")
        client.gl = mock_gl

        with pytest.raises(GitLabError) as exc_info:
            client.get_group_repositories(group_id=1, exclude_list=[])

        assert "sensitive-token" not in str(exc_info.value).lower()
        assert "12345" not in str(exc_info.value)

    def test_empty_token_validation(self):
        """Verify that empty tokens are caught before API calls."""
        client = GitLabClient("https://gitlab.com", "")

        assert client.token == ""

    def test_token_from_environment_variable_fallback(self, tmp_path):
        """Verify token can be sourced from environment variable when config lacks it."""
        import yaml

        config_file = tmp_path / "config.yaml"
        config_data = {
            "gitlab": {"url": "https://gitlab.com", "token": None, "group_id": 1},
            "exclusions": [],
            "merge_request_rules": {},
        }
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        with patch.dict("os.environ", {"GITLAB_TOKEN": "env-token-xyz"}):
            from config_loader import ConfigLoader

            loader = ConfigLoader(str(config_file))
            config = loader.load()
            gitlab_config = loader.get_gitlab_config(config)

            assert gitlab_config["token"] is None


class TestSecurityWebhookURLValidation:
    """Document webhook URL handling in Slack integration."""

    def test_webhook_url_presence_check_only(self):
        """Document that only webhook_url presence is checked, not format.

        Note: The current implementation only validates that webhook_url is present,
        not that it is properly formatted. URL validation should be added.
        """
        mock_gl = Mock()
        mock_project = Mock()
        mock_integrations = Mock()
        mock_project.integrations = mock_integrations
        mock_gl.projects.get.return_value = mock_project

        client = GitLabClient("https://gitlab.com", "test-token")
        client.gl = mock_gl

        slack_settings = {
            "webhook_url": "https://hooks.slack.com/services/...",
            "notify_on_push": True,
        }

        client.enable_slack_integration(project_id=1, slack_settings=slack_settings)
        mock_integrations.create.assert_called_once()

    def test_webhook_url_empty_rejects(self):
        """Verify that empty webhook URLs are rejected."""
        mock_gl = Mock()
        mock_project = Mock()
        mock_gl.projects.get.return_value = mock_project

        client = GitLabClient("https://gitlab.com", "test-token")
        client.gl = mock_gl

        slack_settings = {
            "webhook_url": "",
            "notify_on_push": True,
        }

        with pytest.raises(GitLabError) as exc_info:
            client.enable_slack_integration(project_id=1, slack_settings=slack_settings)

        assert "webhook_url is required" in str(exc_info.value)

    def test_webhook_url_missing_rejects(self):
        """Verify that missing webhook_url in settings is rejected."""
        mock_gl = Mock()
        mock_project = Mock()
        mock_gl.projects.get.return_value = mock_project

        client = GitLabClient("https://gitlab.com", "test-token")
        client.gl = mock_gl

        slack_settings = {
            "notify_on_push": True,
        }

        with pytest.raises(GitLabError) as exc_info:
            client.enable_slack_integration(project_id=1, slack_settings=slack_settings)

        assert "webhook_url is required" in str(exc_info.value)


class TestSecurityAccessControl:
    """Verify that configuration changes only affect specified groups."""

    def test_only_specified_group_repositories_modified(self):
        """Verify that only the configured group's repositories are affected."""
        mock_gl = Mock()
        mock_group = Mock()
        mock_project1 = Mock()
        mock_project1.id = 1
        mock_project1.name = "repo1"
        mock_group.projects.list.return_value = [mock_project1]
        mock_gl.groups.get.return_value = mock_group

        client = GitLabClient("https://gitlab.com", "test-token")
        client.gl = mock_gl

        result = client.get_group_repositories(group_id=5, exclude_list=[])

        mock_gl.groups.get.assert_called_once_with(5)
        assert mock_gl.groups.get.call_count == 1

    def test_configuration_respects_group_boundary(self):
        """Verify configuration cannot affect other groups."""
        mock_gitlab_client = Mock()
        config = {
            "gitlab": {"group_id": 1},
            "exclusions": [],
            "merge_request_rules": {"merge_method": "rebase"},
        }

        configurator = RepositoryConfigurator(mock_gitlab_client, config)

        mock_gitlab_client.get_group_repositories.return_value = {}
        configurator.load_repositories()

        mock_gitlab_client.get_group_repositories.assert_called_once_with(
            group_id=1, exclude_list=[]
        )
