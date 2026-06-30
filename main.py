import os
import click
import logging
from config_loader import ConfigLoader, ConfigError
from gitlab_client import GitLabClient, GitLabError
from repository_configurator import RepositoryConfigurator

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


@click.command()
@click.option(
    "--config",
    "-c",
    required=True,
    type=click.Path(exists=True),
    help="Path to configuration YAML file",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview changes without applying them",
)
def configure(config: str, dry_run: bool) -> None:
    """
    Configure GitLab repositories in a group with merge request rules and Slack integration.
    """
    try:
        loader = ConfigLoader(config)
        config_data = loader.load()

        if dry_run:
            config_data["dry_run"] = True

        gitlab_config = loader.get_gitlab_config(config_data)

        gitlab_url = gitlab_config["url"]
        token = gitlab_config["token"]

        if not token:
            token = os.getenv("GITLAB_TOKEN")
            if not token:
                raise ConfigError(
                    "GitLab token not found. Set it in config file or GITLAB_TOKEN env var."
                )

        gitlab_client = GitLabClient(gitlab_url, token)
        configurator = RepositoryConfigurator(gitlab_client, config_data)

        configurator.configure_all()

    except ConfigError as e:
        click.echo(f"Configuration Error: {e}", err=True)
        raise SystemExit(1)
    except GitLabError as e:
        click.echo(f"GitLab Error: {e}", err=True)
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


if __name__ == "__main__":
    configure()
