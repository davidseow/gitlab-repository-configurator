from click.testing import CliRunner

from main import configure


class TestCLI:
    def test_configure_with_missing_config(self):
        runner = CliRunner()
        result = runner.invoke(configure, ["--config", "nonexistent.yaml"])
        assert result.exit_code != 0

    def test_configure_with_invalid_yaml(self):
        runner = CliRunner()

        with runner.isolated_filesystem():
            with open("config.yaml", "w") as f:
                f.write("invalid: [yaml: content:")

            result = runner.invoke(configure, ["--config", "config.yaml"])
            assert result.exit_code == 1
            assert "Error" in result.output

    def test_configure_displays_error_on_config_error(self):
        runner = CliRunner()

        with runner.isolated_filesystem():
            with open("config.yaml", "w") as f:
                f.write("gitlab:\n  url: https://gitlab.com")

            result = runner.invoke(configure, ["--config", "config.yaml"])
            assert result.exit_code == 1
