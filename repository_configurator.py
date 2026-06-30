from typing import Dict, List, Any
from gitlab_client import GitLabClient


class RepositoryConfigurator:
    def __init__(self, gitlab_client: GitLabClient, config: Dict[str, Any]):
        self.gitlab_client = gitlab_client
        self.config = config

    def load_repositories(self) -> Dict[int, Any]:
        group_id = self.config["gitlab"]["group_id"]
        exclusions = self.config.get("exclusions", [])

        repos = self.gitlab_client.get_group_repositories(
            group_id=group_id,
            exclude_list=exclusions,
        )

        return repos

    def display_repositories(self, repositories: List[Any]) -> None:
        print("\n" + "=" * 60)
        print("Repositories to configure:")
        print("=" * 60)

        for i, repo in enumerate(repositories, 1):
            print(f"{i}. {repo.name}")
            if hasattr(repo, "web_url"):
                print(f"   URL: {repo.web_url}")
        print("=" * 60 + "\n")

    def confirm_action(self, prompt: str) -> bool:
        response = input(f"{prompt} (yes/no): ").strip().lower()
        return response in ["yes", "y"]

    def apply_rules_to_repository(self, repository: Any) -> None:
        dry_run = self.config.get("dry_run", False)

        if dry_run:
            print(f"[DRY RUN] Would configure {repository.name}")
            return

        merge_rules = self.config.get("merge_request_rules", {})
        if merge_rules:
            self.gitlab_client.update_merge_request_rules(
                project_id=repository.id,
                rules=merge_rules,
            )
            print(f"✓ Updated merge request rules for {repository.name}")

        slack_config = self.config.get("slack", {})
        if slack_config.get("enabled"):
            self.gitlab_client.enable_slack_integration(
                project_id=repository.id,
                slack_settings=slack_config,
            )
            print(f"✓ Enabled Slack integration for {repository.name}")

    def configure_all(self) -> None:
        print("\nLoading repositories...")
        repositories = self.load_repositories()

        if not repositories:
            print("No repositories found to configure.")
            return

        repo_list = list(repositories.values())
        self.display_repositories(repo_list)

        if not self.confirm_action("Proceed with configuration?"):
            print("Configuration cancelled.")
            return

        for repo in repo_list:
            print(f"\nConfiguring {repo.name}...")
            self.apply_rules_to_repository(repo)

            if not self.confirm_action(f"Continue to next repository?"):
                print("Configuration stopped.")
                break

        print("\n✓ Configuration complete!")
