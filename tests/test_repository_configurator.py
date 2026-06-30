import pytest
from unittest.mock import Mock, patch, MagicMock
from repository_configurator import RepositoryConfigurator


class TestRepositoryConfigurator:
    @pytest.fixture
    def mock_gitlab_client(self):
        return Mock()

    @pytest.fixture
    def mock_config(self):
        return {
            "gitlab": {"group_id": 1},
            "exclusions": ["repo1"],
            "merge_request_rules": {
                "merge_method": "rebase",
                "only_allow_merge_if_pipeline_succeeds": True,
            },
            "slack": {"webhook_url": "https://hooks.slack.com/...", "enabled": True},
        }

    def test_init_with_client_and_config(self, mock_gitlab_client, mock_config):
        configurator = RepositoryConfigurator(mock_gitlab_client, mock_config)
        assert configurator.gitlab_client == mock_gitlab_client
        assert configurator.config == mock_config

    def test_load_repositories_filters_exclusions(self, mock_gitlab_client, mock_config):
        mock_repo1 = Mock()
        mock_repo1.id = 1
        mock_repo1.name = "repo1"
        mock_repo2 = Mock()
        mock_repo2.id = 2
        mock_repo2.name = "repo2"
        mock_repo3 = Mock()
        mock_repo3.id = 3
        mock_repo3.name = "repo3"

        mock_gitlab_client.get_group_repositories.return_value = {
            2: mock_repo2,
            3: mock_repo3,
        }

        configurator = RepositoryConfigurator(mock_gitlab_client, mock_config)
        repos = configurator.load_repositories()

        assert len(repos) == 2
        assert 1 not in repos
        assert 2 in repos
        assert 3 in repos

    def test_display_repositories(self, mock_gitlab_client, mock_config, capsys):
        mock_repo1 = Mock(id=1, name="repo1", web_url="https://gitlab.com/repo1")
        mock_repo2 = Mock(id=2, name="repo2", web_url="https://gitlab.com/repo2")

        configurator = RepositoryConfigurator(mock_gitlab_client, mock_config)

        configurator.display_repositories([mock_repo1, mock_repo2])
        captured = capsys.readouterr()

        assert "repo1" in captured.out
        assert "repo2" in captured.out

    @patch("builtins.input", return_value="yes")
    def test_confirm_action_returns_true_on_yes(self, mock_input, mock_gitlab_client, mock_config):
        configurator = RepositoryConfigurator(mock_gitlab_client, mock_config)
        result = configurator.confirm_action("Continue?")
        assert result is True

    @patch("builtins.input", return_value="no")
    def test_confirm_action_returns_false_on_no(self, mock_input, mock_gitlab_client, mock_config):
        configurator = RepositoryConfigurator(mock_gitlab_client, mock_config)
        result = configurator.confirm_action("Continue?")
        assert result is False

    def test_apply_rules_to_repository(self, mock_gitlab_client, mock_config):
        mock_repo = Mock(id=1, name="test-repo")

        configurator = RepositoryConfigurator(mock_gitlab_client, mock_config)
        configurator.apply_rules_to_repository(mock_repo)

        mock_gitlab_client.update_merge_request_rules.assert_called_once()
        mock_gitlab_client.enable_slack_integration.assert_called_once()

    def test_dry_run_mode_does_not_apply_changes(self, mock_gitlab_client, mock_config):
        mock_repo = Mock(id=1, name="test-repo")
        mock_config["dry_run"] = True

        configurator = RepositoryConfigurator(mock_gitlab_client, mock_config)
        configurator.apply_rules_to_repository(mock_repo)

        mock_gitlab_client.update_merge_request_rules.assert_not_called()
        mock_gitlab_client.enable_slack_integration.assert_not_called()

    def test_configure_all_repositories(self, mock_gitlab_client, mock_config):
        mock_repo1 = Mock()
        mock_repo1.id = 1
        mock_repo1.name = "repo1"
        mock_repo1.web_url = "https://gitlab.com/repo1"
        mock_repo2 = Mock()
        mock_repo2.id = 2
        mock_repo2.name = "repo2"
        mock_repo2.web_url = "https://gitlab.com/repo2"

        mock_gitlab_client.get_group_repositories.return_value = {
            1: mock_repo1,
            2: mock_repo2,
        }

        configurator = RepositoryConfigurator(mock_gitlab_client, mock_config)

        with patch.object(configurator, "confirm_action", return_value=True):
            with patch.object(configurator, "display_repositories"):
                configurator.configure_all()

        assert mock_gitlab_client.get_group_repositories.called
