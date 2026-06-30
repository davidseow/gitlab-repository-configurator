import pytest
from unittest.mock import Mock, MagicMock, patch
from gitlab_client import GitLabClient


class TestGitLabClient:
    @pytest.fixture
    def mock_gitlab(self):
        return Mock()

    def test_init_with_url_and_token(self, mock_gitlab):
        client = GitLabClient("https://gitlab.com", "test-token")
        assert client.gitlab_url == "https://gitlab.com"
        assert client.token == "test-token"

    def test_get_group_repositories_filters_excluded(self, mock_gitlab):
        mock_group = Mock()
        mock_project1 = Mock()
        mock_project1.id = 1
        mock_project1.name = "repo1"
        mock_project2 = Mock()
        mock_project2.id = 2
        mock_project2.name = "repo2"
        mock_project3 = Mock()
        mock_project3.id = 3
        mock_project3.name = "repo3"
        mock_group.projects.list.return_value = [mock_project1, mock_project2, mock_project3]

        client = GitLabClient("https://gitlab.com", "test-token")
        client.gl = mock_gitlab
        mock_gitlab.groups.get.return_value = mock_group

        excluded = ["repo2"]
        result = client.get_group_repositories(group_id=1, exclude_list=excluded)

        assert len(result) == 2
        assert result[1].name == "repo1"
        assert result[3].name == "repo3"

    def test_update_merge_request_rules_applies_settings(self):
        mock_gl = Mock()
        mock_project = Mock()
        mock_gl.projects.get.return_value = mock_project

        client = GitLabClient("https://gitlab.com", "test-token")
        client.gl = mock_gl

        rules = {
            "merge_method": "rebase",
            "only_allow_merge_if_all_discussions_are_resolved": True,
            "only_allow_merge_if_pipeline_succeeds": True,
        }

        client.update_merge_request_rules(project_id=1, rules=rules)

        mock_project.save.assert_called_once()

    def test_enable_slack_integration_creates_integration(self):
        mock_gl = Mock()
        mock_project = Mock()
        mock_integrations = Mock()
        mock_project.integrations = mock_integrations
        mock_gl.projects.get.return_value = mock_project

        client = GitLabClient("https://gitlab.com", "test-token")
        client.gl = mock_gl

        slack_settings = {
            "webhook_url": "https://hooks.slack.com/...",
            "notify_on_push": True,
            "notify_on_merge_requests": True,
        }

        client.enable_slack_integration(project_id=1, slack_settings=slack_settings)

        mock_integrations.create.assert_called_once()

    def test_get_group_repositories_handles_pagination(self):
        mock_gl = Mock()
        mock_group = Mock()
        mock_projects = []
        for i in range(1, 6):
            mock_project = Mock()
            mock_project.id = i
            mock_project.name = f"repo{i}"
            mock_projects.append(mock_project)
        mock_group.projects.list.return_value = mock_projects

        client = GitLabClient("https://gitlab.com", "test-token")
        client.gl = mock_gl
        mock_gl.groups.get.return_value = mock_group

        result = client.get_group_repositories(group_id=1, exclude_list=[])
        assert len(result) == 5

    def test_get_group_repositories_with_recursive_option(self):
        mock_gl = Mock()
        mock_group = Mock()
        mock_projects = [Mock(id=1, name="repo1")]
        mock_group.projects.list.return_value = mock_projects

        client = GitLabClient("https://gitlab.com", "test-token")
        client.gl = mock_gl
        mock_gl.groups.get.return_value = mock_group

        result = client.get_group_repositories(group_id=1, exclude_list=[], recursive=True)

        mock_group.projects.list.assert_called()

    def test_exclusions_with_glob_patterns(self):
        mock_gl = Mock()
        mock_group = Mock()

        mock_projects = []
        for name in ["repo.backup", "data.backup", "archive-2023", "archive-old",
                     "staging-dev", "staging-qa", "test_repo", "test_project", "normal-repo"]:
            mock_project = Mock()
            mock_project.id = len(mock_projects) + 1
            mock_project.name = name
            mock_projects.append(mock_project)

        mock_group.projects.list.return_value = mock_projects

        client = GitLabClient("https://gitlab.com", "test-token")
        client.gl = mock_gl
        mock_gl.groups.get.return_value = mock_group

        patterns = ["*.backup", "archive-*", "staging-*", "test_*"]
        result = client.get_group_repositories(group_id=1, exclude_list=patterns)

        assert len(result) == 1
        assert result[9].name == "normal-repo"

    def test_mixed_exact_and_glob_patterns(self):
        mock_gl = Mock()
        mock_group = Mock()

        mock_projects = []
        for name in ["exact_repo", "project.backup", "staging-qa", "keep-this"]:
            mock_project = Mock()
            mock_project.id = len(mock_projects) + 1
            mock_project.name = name
            mock_projects.append(mock_project)

        mock_group.projects.list.return_value = mock_projects

        client = GitLabClient("https://gitlab.com", "test-token")
        client.gl = mock_gl
        mock_gl.groups.get.return_value = mock_group

        patterns = ["exact_repo", "*.backup", "staging-*"]
        result = client.get_group_repositories(group_id=1, exclude_list=patterns)

        assert len(result) == 1
        assert result[4].name == "keep-this"

    def test_edge_case_glob_patterns(self):
        mock_gl = Mock()
        mock_group = Mock()

        mock_projects = []
        for name in ["a", "ab", "abc", "a_b_c", "test_repo", "test_dev"]:
            mock_project = Mock()
            mock_project.id = len(mock_projects) + 1
            mock_project.name = name
            mock_projects.append(mock_project)

        mock_group.projects.list.return_value = mock_projects

        client = GitLabClient("https://gitlab.com", "test-token")
        client.gl = mock_gl
        mock_gl.groups.get.return_value = mock_group

        patterns = ["a?c", "test_*"]
        result = client.get_group_repositories(group_id=1, exclude_list=patterns)

        assert len(result) == 3
        assert 1 in result  # "a"
        assert 2 in result  # "ab"
        assert 4 in result  # "a_b_c"

    def test_no_match_excludes_nothing(self):
        mock_gl = Mock()
        mock_group = Mock()

        mock_projects = []
        for name in ["project-a", "project-b", "project-c"]:
            mock_project = Mock()
            mock_project.id = len(mock_projects) + 1
            mock_project.name = name
            mock_projects.append(mock_project)

        mock_group.projects.list.return_value = mock_projects

        client = GitLabClient("https://gitlab.com", "test-token")
        client.gl = mock_gl
        mock_gl.groups.get.return_value = mock_group

        patterns = ["*.backup", "archive-*"]
        result = client.get_group_repositories(group_id=1, exclude_list=patterns)

        assert len(result) == 3

    def test_is_excluded_helper_method(self):
        client = GitLabClient("https://gitlab.com", "test-token")

        assert client._is_excluded("repo.backup", ["*.backup"]) is True
        assert client._is_excluded("archive-2023", ["archive-*"]) is True
        assert client._is_excluded("staging-dev", ["staging-*"]) is True
        assert client._is_excluded("test_repo", ["test_*"]) is True
        assert client._is_excluded("exact_name", ["exact_name"]) is True
        assert client._is_excluded("other-project", ["*.backup", "archive-*"]) is False
        assert client._is_excluded("data.backup", ["repo.backup"]) is False
