from typing import Dict, List, Any
import logging
from gitlab_client import GitLabClient, GitLabError

logger = logging.getLogger(__name__)


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

    def apply_rules_to_repository(self, repository: Any) -> bool:
        dry_run = self.config.get("dry_run", False)

        if dry_run:
            print(f"[DRY RUN] Would configure {repository.name}")
            return True

        try:
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
            return True
        except GitLabError as e:
            print(f"✗ Error configuring {repository.name}: {e}")
            return False

    def configure_all(self) -> None:
        try:
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

            successful = 0
            failed = 0

            for repo in repo_list:
                print(f"\nConfiguring {repo.name}...")
                if self.apply_rules_to_repository(repo):
                    successful += 1
                else:
                    failed += 1

                if not self.confirm_action(f"Continue to next repository?"):
                    print("Configuration stopped.")
                    break

            print(f"\n{'='*60}")
            print(f"Summary: {successful} successful, {failed} failed")
            print(f"{'='*60}")
        except GitLabError as e:
            print(f"Error during configuration: {e}")
