import pytest

from config_loader import ConfigError, ConfigLoader


class TestConfigLoader:
    @pytest.fixture
    def sample_config(self):
        return {
            "gitlab": {
                "url": "https://gitlab.com",
                "token": "test-token",
                "group_id": 1,
            },
            "exclusions": ["repo1", "repo2"],
            "merge_request_rules": {
                "merge_method": "rebase",
                "only_allow_merge_if_all_discussions_are_resolved": True,
                "only_allow_merge_if_pipeline_succeeds": True,
            },
            "slack": {
                "webhook_url": "https://hooks.slack.com/services/...",
                "enabled": True,
            },
        }

    def test_load_config_from_file(self, sample_config, tmp_path):
        import yaml

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(sample_config, f)

        loader = ConfigLoader(str(config_file))
        config = loader.load()

        assert config["gitlab"]["url"] == "https://gitlab.com"
        assert config["gitlab"]["token"] == "test-token"
        assert config["gitlab"]["group_id"] == 1
        assert "repo1" in config["exclusions"]

    def test_load_config_missing_file_raises_error(self):
        loader = ConfigLoader("/nonexistent/config.yaml")
        with pytest.raises(ConfigError):
            loader.load()

    def test_validate_config_required_fields(self, sample_config, tmp_path):
        import yaml

        config_file = tmp_path / "config.yaml"

        invalid_config = {
            "gitlab": {
                "url": "https://gitlab.com",
            }
        }
        with open(config_file, "w") as f:
            yaml.dump(invalid_config, f)

        loader = ConfigLoader(str(config_file))
        with pytest.raises(ConfigError):
            loader.load()

    def test_get_gitlab_config(self, sample_config, tmp_path):
        import yaml

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(sample_config, f)

        loader = ConfigLoader(str(config_file))
        config = loader.load()
        gitlab_config = loader.get_gitlab_config(config)

        assert gitlab_config["url"] == "https://gitlab.com"
        assert gitlab_config["token"] == "test-token"
        assert gitlab_config["group_id"] == 1

    def test_get_exclusions(self, sample_config, tmp_path):
        import yaml

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(sample_config, f)

        loader = ConfigLoader(str(config_file))
        config = loader.load()
        exclusions = loader.get_exclusions(config)

        assert exclusions == ["repo1", "repo2"]

    def test_get_merge_request_rules(self, sample_config, tmp_path):
        import yaml

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(sample_config, f)

        loader = ConfigLoader(str(config_file))
        config = loader.load()
        rules = loader.get_merge_request_rules(config)

        assert rules["merge_method"] == "rebase"
        assert rules["only_allow_merge_if_all_discussions_are_resolved"] is True
        assert rules["only_allow_merge_if_pipeline_succeeds"] is True

    def test_empty_token_in_config(self, tmp_path):
        """Verify empty token string is allowed (falls back to env var)."""
        import yaml

        config_file = tmp_path / "config.yaml"
        config_data = {
            "gitlab": {
                "url": "https://gitlab.com",
                "token": "",
                "group_id": 1,
            },
            "exclusions": [],
            "merge_request_rules": {},
        }
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        loader = ConfigLoader(str(config_file))
        config = loader.load()
        gitlab_config = loader.get_gitlab_config(config)

        assert gitlab_config["token"] == ""

    def test_non_https_url_in_config(self, tmp_path):
        """Verify non-HTTPS URLs are allowed in config (validation happens at CLI)."""
        import yaml

        config_file = tmp_path / "config.yaml"
        config_data = {
            "gitlab": {
                "url": "http://gitlab.example.com",
                "token": "test-token",
                "group_id": 1,
            },
            "exclusions": [],
            "merge_request_rules": {},
        }
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        loader = ConfigLoader(str(config_file))
        config = loader.load()
        gitlab_config = loader.get_gitlab_config(config)

        assert gitlab_config["url"] == "http://gitlab.example.com"

    def test_non_integer_group_id_in_config(self, tmp_path):
        """Verify non-integer group_id is loaded as-is (type validation at runtime)."""
        import yaml

        config_file = tmp_path / "config.yaml"
        config_data = {
            "gitlab": {
                "url": "https://gitlab.com",
                "token": "test-token",
                "group_id": "invalid-string",
            },
            "exclusions": [],
            "merge_request_rules": {},
        }
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        loader = ConfigLoader(str(config_file))
        config = loader.load()
        gitlab_config = loader.get_gitlab_config(config)

        assert gitlab_config["group_id"] == "invalid-string"
