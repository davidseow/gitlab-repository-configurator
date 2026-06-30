from typing import Any

import yaml


class ConfigError(Exception):
    pass


class ConfigLoader:
    REQUIRED_FIELDS = ["gitlab", "merge_request_rules"]

    def __init__(self, config_path: str):
        self.config_path = config_path

    def load(self) -> dict[str, Any]:
        try:
            with open(self.config_path) as f:
                config = yaml.safe_load(f)
        except FileNotFoundError as e:
            raise ConfigError(f"Config file not found: {self.config_path}") from e
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in config file: {e}") from e

        self._validate_config(config)
        return config

    def _validate_config(self, config: dict[str, Any]) -> None:
        if not config:
            raise ConfigError("Config file is empty")

        for field in self.REQUIRED_FIELDS:
            if field not in config:
                raise ConfigError(f"Missing required field: {field}")

        gitlab_config = config.get("gitlab", {})
        required_gitlab = ["url", "token", "group_id"]
        for field in required_gitlab:
            if field not in gitlab_config:
                raise ConfigError(f"Missing required gitlab field: {field}")

    def get_gitlab_config(self, config: dict[str, Any]) -> dict[str, Any]:
        return config["gitlab"]

    def get_exclusions(self, config: dict[str, Any]) -> list[str]:
        return config.get("exclusions", [])

    def get_merge_request_rules(self, config: dict[str, Any]) -> dict[str, Any]:
        return config.get("merge_request_rules", {})

    def get_slack_config(self, config: dict[str, Any]) -> dict[str, Any]:
        return config.get("slack", {})
