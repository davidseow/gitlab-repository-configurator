import gitlab
from typing import List, Dict, Any, Optional
from fnmatch import fnmatch
import logging

logger = logging.getLogger(__name__)


class GitLabError(Exception):
    pass


class GitLabClient:
    def __init__(self, gitlab_url: str, token: str):
        self.gitlab_url = gitlab_url
        self.token = token
        self.gl = gitlab.Gitlab(gitlab_url, private_token=token)

    def _is_excluded(self, project_name: str, exclude_patterns: List[str]) -> bool:
        for pattern in exclude_patterns:
            if fnmatch(project_name, pattern):
                logger.info(f"Repository '{project_name}' matches exclusion pattern '{pattern}'")
                return True
        return False

    def get_group_repositories(
        self,
        group_id: int,
        exclude_list: List[str],
        recursive: bool = True,
    ) -> Dict[int, Any]:
        try:
            group = self.gl.groups.get(group_id)
            projects = group.projects.list(
                get_all=True,
                include_subgroups=recursive,
            )

            filtered = {}
            for project in projects:
                if not self._is_excluded(project.name, exclude_list):
                    filtered[project.id] = project

            logger.info(f"Found {len(filtered)} repositories in group {group_id}")
            return filtered
        except gitlab.exceptions.GitlabGetError as e:
            raise GitLabError(f"Group {group_id} not found: {e}")
        except gitlab.exceptions.GitlabAuthenticationError as e:
            raise GitLabError(f"Authentication failed: {e}")
        except Exception as e:
            raise GitLabError(f"Failed to fetch repositories: {e}")

    def update_merge_request_rules(self, project_id: int, rules: Dict[str, Any]) -> None:
        try:
            project = self.gl.projects.get(project_id)

            for key, value in rules.items():
                setattr(project, key, value)

            project.save()
            logger.info(f"Updated merge request rules for project {project_id}")
        except gitlab.exceptions.GitlabGetError:
            raise GitLabError(f"Project {project_id} not found")
        except Exception as e:
            raise GitLabError(f"Failed to update merge request rules for project {project_id}: {e}")

    def enable_slack_integration(
        self,
        project_id: int,
        slack_settings: Dict[str, Any],
    ) -> None:
        try:
            if not slack_settings.get("webhook_url"):
                raise GitLabError("Slack webhook_url is required")

            project = self.gl.projects.get(project_id)

            integration_data = {
                "webhook_url": slack_settings.get("webhook_url"),
                "notify_on_push": slack_settings.get("notify_on_push", True),
                "notify_on_merge_requests": slack_settings.get(
                    "notify_on_merge_requests", True
                ),
            }

            project.integrations.create("slack", integration_data)
            logger.info(f"Enabled Slack integration for project {project_id}")
        except gitlab.exceptions.GitlabGetError:
            raise GitLabError(f"Project {project_id} not found")
        except Exception as e:
            raise GitLabError(f"Failed to enable Slack integration for project {project_id}: {e}")
