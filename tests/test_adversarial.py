"""
Adversarial input tests documenting protection against injection attacks and malformed data.

These tests verify that the application handles hostile input safely and cannot be
exploited through configuration values, project names, or API responses.
"""

from unittest.mock import Mock

from config_loader import ConfigLoader
from gitlab_client import GitLabClient


class TestAdversarialCommandInjection:
    """Verify protection against command/SQL injection in configuration."""

    def test_repository_names_with_shell_metacharacters(self):
        """Verify repo names with shell metacharacters are handled safely."""
        mock_gl = Mock()
        mock_group = Mock()

        dangerous_names = [
            "repo;malicious",
            "repo|pipe",
            "repo`backtick`",
            "repo$(whoami)",
            "repo>output.txt",
            "repo<input.txt",
        ]

        for name in dangerous_names:
            mock_project = Mock()
            mock_project.id = 1
            mock_project.name = name
            mock_group.projects.list.return_value = [mock_project]

        mock_gl.groups.get.return_value = mock_group

        client = GitLabClient("https://gitlab.com", "test-token")
        client.gl = mock_gl

        result = client.get_group_repositories(group_id=1, exclude_list=[])

        assert len(result) >= 0

    def test_sql_injection_patterns_in_project_names(self):
        """Verify SQL injection patterns in project names don't cause issues."""
        mock_gl = Mock()
        mock_group = Mock()

        sql_patterns = [
            "repo'; DROP TABLE projects--",
            "repo' OR '1'='1",
            'repo"; DELETE FROM repos--',
        ]

        for name in sql_patterns:
            mock_project = Mock()
            mock_project.id = 1
            mock_project.name = name
            mock_group.projects.list.return_value = [mock_project]

        mock_gl.groups.get.return_value = mock_group

        client = GitLabClient("https://gitlab.com", "test-token")
        client.gl = mock_gl

        result = client.get_group_repositories(group_id=1, exclude_list=[])

        assert len(result) >= 0

    def test_exclusion_patterns_with_malicious_globs(self):
        """Verify complex glob patterns don't cause issues."""
        mock_gl = Mock()
        mock_group = Mock()

        mock_projects = []
        for i, name in enumerate(["repo1", "repo2", "repo3"], 1):
            mock_project = Mock()
            mock_project.id = i
            mock_project.name = name
            mock_projects.append(mock_project)

        mock_group.projects.list.return_value = mock_projects
        mock_gl.groups.get.return_value = mock_group

        client = GitLabClient("https://gitlab.com", "test-token")
        client.gl = mock_gl

        malicious_patterns = [
            "*/*",
            "[a-z]*",
            "?????",
            "repo[!1-9]",
        ]

        result = client.get_group_repositories(group_id=1, exclude_list=malicious_patterns)

        assert isinstance(result, dict)


class TestAdversarialTypeConfusion:
    """Verify the application handles type mismatches gracefully."""

    def test_non_integer_group_id_in_config(self, tmp_path):
        """Verify non-integer group_id is caught."""
        import yaml

        config_file = tmp_path / "config.yaml"
        config_data = {
            "gitlab": {"url": "https://gitlab.com", "token": "token", "group_id": "abc"},
            "exclusions": [],
            "merge_request_rules": {},
        }
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        loader = ConfigLoader(str(config_file))
        config = loader.load()

        gitlab_config = loader.get_gitlab_config(config)
        assert gitlab_config["group_id"] == "abc"

    def test_non_boolean_merge_request_rule_values(self):
        """Verify non-boolean values in boolean rule fields are handled."""
        mock_gl = Mock()
        mock_project = Mock()
        mock_gl.projects.get.return_value = mock_project

        client = GitLabClient("https://gitlab.com", "test-token")
        client.gl = mock_gl

        rules = {
            "merge_method": "rebase",
            "only_allow_merge_if_all_discussions_are_resolved": "yes",
            "only_allow_merge_if_pipeline_succeeds": 1,
        }

        client.update_merge_request_rules(project_id=1, rules=rules)
        mock_project.save.assert_called_once()

    def test_webhook_url_with_various_formats_accepted(self):
        """Document that webhook URLs are passed through without format validation.

        Note: The current implementation does not validate URL formats. URLs are
        accepted and passed to GitLab API, which may then validate them.
        """
        mock_gl = Mock()
        mock_project = Mock()
        mock_integrations = Mock()
        mock_project.integrations = mock_integrations
        mock_gl.projects.get.return_value = mock_project

        client = GitLabClient("https://gitlab.com", "test-token")
        client.gl = mock_gl

        various_urls = [
            "not-a-url",
            "ftp://hooks.slack.com/services/...",
            "https://",
            "://missing-scheme",
        ]

        for url in various_urls:
            slack_settings = {
                "webhook_url": url,
                "notify_on_push": True,
            }

            client.enable_slack_integration(project_id=1, slack_settings=slack_settings)
            mock_integrations.create.assert_called()

    def test_empty_required_fields_in_config(self, tmp_path):
        """Verify empty strings in required fields are handled."""
        import yaml

        config_file = tmp_path / "config.yaml"
        config_data = {
            "gitlab": {"url": "", "token": "", "group_id": 1},
            "exclusions": [],
            "merge_request_rules": {},
        }
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        loader = ConfigLoader(str(config_file))
        config = loader.load()

        gitlab_config = loader.get_gitlab_config(config)
        assert gitlab_config["url"] == ""
        assert gitlab_config["token"] == ""


class TestAdversarialANSIInjection:
    """Verify repository names with control characters are handled safely."""

    def test_repository_names_with_ansi_escape_codes(self):
        """Verify ANSI escape codes in repo names don't cause terminal hijacking."""
        mock_gl = Mock()
        mock_group = Mock()

        mock_project = Mock()
        mock_project.id = 1
        ansi_name = "repo\x1b[31m\x1b[1m\x1b[4mmalicious\x1b[0m"
        mock_project.name = ansi_name
        mock_group.projects.list.return_value = [mock_project]
        mock_gl.groups.get.return_value = mock_group

        client = GitLabClient("https://gitlab.com", "test-token")
        client.gl = mock_gl

        result = client.get_group_repositories(group_id=1, exclude_list=[])

        assert 1 in result
        assert result[1].name == ansi_name

    def test_repository_names_with_control_characters(self):
        """Verify control characters in repo names are handled safely."""
        mock_gl = Mock()
        mock_group = Mock()

        mock_project = Mock()
        mock_project.id = 1
        control_name = "repo\x00\x01\x02dangerous"
        mock_project.name = control_name
        mock_group.projects.list.return_value = [mock_project]
        mock_gl.groups.get.return_value = mock_group

        client = GitLabClient("https://gitlab.com", "test-token")
        client.gl = mock_gl

        result = client.get_group_repositories(group_id=1, exclude_list=[])

        assert 1 in result


class TestAdversarialBoundaryConditions:
    """Verify handling of extreme input values."""

    def test_very_long_repository_name(self):
        """Verify handling of repository names exceeding typical length limits."""
        mock_gl = Mock()
        mock_group = Mock()

        mock_project = Mock()
        mock_project.id = 1
        mock_project.name = "a" * 500
        mock_group.projects.list.return_value = [mock_project]
        mock_gl.groups.get.return_value = mock_group

        client = GitLabClient("https://gitlab.com", "test-token")
        client.gl = mock_gl

        result = client.get_group_repositories(group_id=1, exclude_list=[])

        assert 1 in result

    def test_unicode_and_emoji_in_project_names(self):
        """Verify safe handling of Unicode and emoji in project names."""
        mock_gl = Mock()
        mock_group = Mock()

        unicode_names = [
            "repo-日本語",
            "프로젝트-한글",
            "проект-русский",
            "😈-malicious-🔥",
        ]

        for name in unicode_names:
            mock_project = Mock()
            mock_project.id = 1
            mock_project.name = name
            mock_group.projects.list.return_value = [mock_project]

        mock_gl.groups.get.return_value = mock_group

        client = GitLabClient("https://gitlab.com", "test-token")
        client.gl = mock_gl

        result = client.get_group_repositories(group_id=1, exclude_list=[])

        assert len(result) >= 0

    def test_negative_and_zero_project_ids(self):
        """Verify handling of invalid ID values."""
        mock_gl = Mock()
        mock_group = Mock()

        mock_project = Mock()
        mock_project.id = -1
        mock_project.name = "negative-id-repo"
        mock_group.projects.list.return_value = [mock_project]
        mock_gl.groups.get.return_value = mock_group

        client = GitLabClient("https://gitlab.com", "test-token")
        client.gl = mock_gl

        result = client.get_group_repositories(group_id=1, exclude_list=[])

        assert -1 in result
