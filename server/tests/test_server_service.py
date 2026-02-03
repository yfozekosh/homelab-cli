"""Unit tests for ServerService"""

import pytest
from unittest.mock import patch, MagicMock
import subprocess
import socket

from server.server_service import ServerService


@pytest.fixture
def server_service():
    """Create ServerService instance with mocked environment"""
    with patch.dict('os.environ', {'SSH_USER': 'testuser'}):
        yield ServerService()


class TestResolveHostname:
    """Tests for resolve_hostname method"""

    def test_resolve_valid_hostname(self, server_service):
        """Successfully resolve a valid hostname"""
        with patch('socket.gethostbyname', return_value='192.168.1.100'):
            result = server_service.resolve_hostname('test.local')
            assert result == '192.168.1.100'

    def test_resolve_ip_address(self, server_service):
        """Return IP address as-is"""
        with patch('socket.gethostbyname', return_value='192.168.1.100'):
            result = server_service.resolve_hostname('192.168.1.100')
            assert result == '192.168.1.100'

    def test_resolve_unknown_hostname(self, server_service):
        """Return 'Unable to resolve' for unknown hostname"""
        with patch('socket.gethostbyname', side_effect=socket.gaierror):
            result = server_service.resolve_hostname('unknown.local')
            assert result == "Unable to resolve"


class TestPing:
    """Tests for ping method"""

    def test_ping_success(self, server_service):
        """Successful ping returns True"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch('subprocess.run', return_value=mock_result):
            result = server_service.ping('192.168.1.100')
            assert result is True

    def test_ping_failure(self, server_service):
        """Failed ping returns False"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        with patch('subprocess.run', return_value=mock_result):
            result = server_service.ping('192.168.1.100')
            assert result is False

    def test_ping_timeout(self, server_service):
        """Ping timeout returns False"""
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired('ping', 5)):
            result = server_service.ping('192.168.1.100')
            assert result is False

    def test_ping_exception(self, server_service):
        """Ping exception returns False"""
        with patch('subprocess.run', side_effect=Exception('Network error')):
            result = server_service.ping('192.168.1.100')
            assert result is False


class TestSendWol:
    """Tests for send_wol method (returns None, uses wakeonlan library)"""

    def test_send_wol_calls_library(self, server_service):
        """send_wol calls wakeonlan library"""
        with patch('server.server_service.send_magic_packet') as mock_wol:
            server_service.send_wol('AA:BB:CC:DD:EE:FF')
            mock_wol.assert_called_once_with('AA:BB:CC:DD:EE:FF')


class TestShutdown:
    """Tests for shutdown method (returns None on success, raises on failure)"""

    def test_shutdown_success(self, server_service):
        """Successfully shutdown server (no exception)"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        with patch('subprocess.run', return_value=mock_result):
            # Should not raise
            server_service.shutdown('192.168.1.100')

    def test_shutdown_failure_raises(self, server_service):
        """Failed shutdown raises Exception"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Connection refused"
        with patch('subprocess.run', return_value=mock_result):
            with pytest.raises(Exception, match="SSH command failed"):
                server_service.shutdown('192.168.1.100')

    def test_shutdown_timeout_is_expected(self, server_service):
        """Shutdown timeout is expected behavior (no exception)"""
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired('ssh', 15)):
            # Should not raise - timeout is expected during shutdown
            server_service.shutdown('192.168.1.100')

    def test_shutdown_exit_255_is_ok(self, server_service):
        """Exit code 255 is OK (connection closed during shutdown)"""
        mock_result = MagicMock()
        mock_result.returncode = 255
        mock_result.stdout = ""
        mock_result.stderr = ""
        with patch('subprocess.run', return_value=mock_result):
            # Should not raise
            server_service.shutdown('192.168.1.100')


class TestSSHConnection:
    """Tests for SSH-related methods"""

    def test_test_ssh_connection_success(self, server_service):
        """Successfully test SSH connection"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch('subprocess.run', return_value=mock_result):
            result = server_service.test_ssh_connection('192.168.1.100')
            assert result is True

    def test_test_ssh_connection_failure(self, server_service):
        """Failed SSH connection returns False"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        with patch('subprocess.run', return_value=mock_result):
            result = server_service.test_ssh_connection('192.168.1.100')
            assert result is False

    def test_test_sudo_poweroff_success(self, server_service):
        """Successfully test sudo poweroff"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        with patch('subprocess.run', return_value=mock_result):
            result = server_service.test_sudo_poweroff('192.168.1.100')
            assert result is True

    def test_test_sudo_poweroff_failure(self, server_service):
        """Failed sudo poweroff test returns False"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = ""
        with patch('subprocess.run', return_value=mock_result):
            result = server_service.test_sudo_poweroff('192.168.1.100')
            assert result is False

    def test_test_sudo_poweroff_password_required(self, server_service):
        """Sudo requiring password returns False"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = "a password is required"
        with patch('subprocess.run', return_value=mock_result):
            result = server_service.test_sudo_poweroff('192.168.1.100')
            assert result is False


class TestBuildSSHTarget:
    """Tests for _build_ssh_target method"""

    def test_builds_correct_target(self, server_service):
        """Builds user@hostname format"""
        result = server_service._build_ssh_target('192.168.1.100')
        assert result == 'testuser@192.168.1.100'

    def test_uses_ssh_user_from_env(self):
        """Uses SSH_USER from environment"""
        with patch.dict('os.environ', {'SSH_USER': 'customuser'}):
            service = ServerService()
            result = service._build_ssh_target('host.local')
            assert result == 'customuser@host.local'
