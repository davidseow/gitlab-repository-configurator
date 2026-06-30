import gitlab
from typing import List, Dict, Any, Optional


class GitLabClient:
    def __init__(self, gitlab_url: str, token: str):
        self.gitlab_url = gitlab_url
        self.token = token
        self.gl = gitlab.Gitlab(gitlab_url, private_token=token)

    def get_group_repositories(
        self,
        group_id: int,
        exclude_list: List[str],
        recursive: bool = True,
    ) -> Dict[int, Any]:
        group = self.gl.groups.get(group_id)
        projects = group.projects.list(
            get_all=True,
            include_subgroups=recursive,
        )

        filtered = {}
        for project in projects:
            if project.name not in exclude_list:
                filtered[project.id] = project

        return filtered

    def update_merge_request_rules(self, project_id: int, rules: Dict[str, Any]) -> None:
        project = self.gl.projects.get(project_id)

        for key, value in rules.items():
            setattr(project, key, value)

        project.save()

    def enable_slack_integration(
        self,
        project_id: int,
        slack_settings: Dict[str, Any],
    ) -> None:
        project = self.gl.projects.get(project_id)

        integration_data = {
            "webhook_url": slack_settings.get("webhook_url"),
            "notify_on_push": slack_settings.get("notify_on_push", True),
            "notify_on_merge_requests": slack_settings.get(
                "notify_on_merge_requests", True
            ),
        }

        project.integrations.create("slack", integration_data)
