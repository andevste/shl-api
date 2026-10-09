"""Unit tests for SHLClient using mocked HTTP responses."""

from unittest.mock import MagicMock

import pytest
import requests

from shl.client import SHLClient
from shl.exceptions import SHLConnectionError, SHLNotFoundError, SHLTimeoutError


def test_client_init_and_close():
    client = SHLClient()
    assert client.base_url == "https://www.shl.se/api"
    client.close()


def test_client_context_manager():
    with SHLClient() as client:
        assert client.base_url == "https://www.shl.se/api"


def test_404_raises_shl_not_found():
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.text = "Not Found"
    mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_resp)

    mock_session = MagicMock()
    mock_session.get.return_value = mock_resp

    with SHLClient(session=mock_session) as client:
        with pytest.raises(SHLNotFoundError) as exc_info:
            client._request("/invalid-endpoint")
        assert exc_info.value.status_code == 404


def test_timeout_raises_shl_timeout():
    mock_session = MagicMock()
    mock_session.get.side_effect = requests.exceptions.Timeout("Connection timed out")

    with SHLClient(session=mock_session) as client, pytest.raises(SHLTimeoutError):
        client._request("/timeout-endpoint")


def test_connection_error_raises_shl_connection_error():
    mock_session = MagicMock()
    mock_session.get.side_effect = requests.exceptions.ConnectionError("Failed to resolve")

    with SHLClient(session=mock_session) as client, pytest.raises(SHLConnectionError):
        client._request("/offline")


def test_empty_response_returns_dict():
    mock_resp = MagicMock()
    mock_resp.content = b""
    mock_resp.text = ""
    mock_resp.headers = {"content-type": "application/json"}
    mock_resp.raise_for_status.return_value = None

    mock_session = MagicMock()
    mock_session.get.return_value = mock_resp

    with SHLClient(session=mock_session) as client:
        res = client._request("/empty")
        assert res == {}
