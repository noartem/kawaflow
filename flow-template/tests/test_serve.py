import os
import socket
from unittest.mock import MagicMock, patch

import pytest

from serve import SOCKET_PATH, handle_command, main


@pytest.fixture
def mock_module():
    with patch("serve.Module") as MockModule:
        instance = MockModule.return_value
        instance.dump.return_value = {"test": "data"}
        yield instance


@pytest.fixture
def setup_socket():
    if os.path.exists(SOCKET_PATH):
        if os.path.islink(SOCKET_PATH) or os.path.isfile(SOCKET_PATH):
            os.unlink(SOCKET_PATH)
        elif os.path.isdir(SOCKET_PATH):
            os.rmdir(SOCKET_PATH)
    yield
    if os.path.exists(SOCKET_PATH):
        if os.path.islink(SOCKET_PATH) or os.path.isfile(SOCKET_PATH):
            os.unlink(SOCKET_PATH)
        elif os.path.isdir(SOCKET_PATH):
            os.rmdir(SOCKET_PATH)


def test_handle_command_dump(mock_module):
    result = handle_command("dump", mock_module)
    assert result == {"test": "data"}
    mock_module.dump.assert_called_once()


def test_handle_command_unknown(mock_module):
    result = handle_command("unknown", mock_module)
    assert result == {"error": "unknown command"}


def test_handle_command_other(mock_module):
    mock_module.other_command.return_value = {"other": "result"}
    result = handle_command("other_command", mock_module)
    assert result == {"error": "unknown command"}  # handle_command only supports "dump"


@patch("socket.socket")
@patch("serve.os.path.exists", return_value=False)
@patch("serve.os.remove")
def test_main_socket_communication(
    mock_remove, mock_exists, mock_socket_class, mock_module, setup_socket
):
    mock_socket_class.AF_UNIX = socket.AF_INET  # Set AF_UNIX on the mock socket class
    mock_conn = MagicMock()
    mock_socket_class.return_value.__enter__.return_value.accept.return_value = (
        mock_conn,
        "addr",
    )
    mock_conn.recv.side_effect = [b"dump", b""]

    with patch("serve.Module", return_value=mock_module):
        main()


@patch("serve.socket.socket")
@patch("serve.os.path.exists", return_value=True)
@patch("serve.os.remove")
def test_main_socket_remove_exists(
    mock_remove, mock_exists, mock_socket, mock_module, setup_socket
):
    with patch("serve.socket.AF_UNIX", socket.AF_INET):
        mock_conn = MagicMock()
        mock_socket.return_value.__enter__.return_value.accept.return_value = (
            mock_conn,
            "addr",
        )
        mock_conn.recv.side_effect = [b"dump", b""]

        with patch("serve.Module", return_value=mock_module):
            main()

        mock_remove.assert_called_once_with(SOCKET_PATH)


@patch("serve.os.path.exists", return_value=False)
@patch("serve.os.remove")
def test_main_socket_bind_error(
    mock_remove, mock_exists, mock_module, setup_socket
):
    with patch("socket.socket", autospec=True) as mock_socket_class:
        mock_socket_instance = mock_socket_class.return_value.__enter__.return_value
        mock_socket_instance.bind.side_effect = OSError("Bind error")
        with patch("serve.Module", return_value=mock_module):
            with pytest.raises(OSError, match="Bind error"):
                main()
