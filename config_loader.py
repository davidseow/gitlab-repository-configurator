import yaml
from typing import Dict, List, Any
from pathlib import Path


class ConfigError(Exception):
    pass


class ConfigLoader:
    REQUIRED_FIELDS = ["gitlab", "merge_request_rules"]

    def __init__(self, config_path: str):
        self.config_path = config_path

    def load(self) -> Dict[str, Any]:
        try:
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)
        except FileNotFoundError:
            raise ConfigError(f"Config file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in config file: {e}")

        self._validate_config(config)
        return config

    def _validate_config(self, config: Dict[str, Any]) -> None:
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

    def get_gitlab_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return config["gitlab"]

    def get_exclusions(self, config: Dict[str, Any]) -> List[str]:
        return config.get("exclusions", [])

    def get_merge_request_rules(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return config.get("merge_request_rules", {})

    def get_slack_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return config.get("slack", {})
