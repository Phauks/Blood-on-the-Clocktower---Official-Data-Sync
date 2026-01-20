"""Integration tests for HTTP client with retry logic."""

import pytest
from unittest.mock import patch, Mock, MagicMock
import requests

from src.utils.http_client import fetch_with_retry, rate_limit, get_session, close_session


class TestFetchWithRetry:
    """Tests for fetch_with_retry function."""

    def setup_method(self):
        """Reset session before each test."""
        close_session()

    def teardown_method(self):
        """Clean up session after each test."""
        close_session()

    @patch('src.utils.http_client.get_session')
    def test_successful_fetch(self, mock_get_session):
        """Should return response on successful fetch."""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "test content"
        mock_response.headers = {"Content-Length": "12"}
        mock_response.iter_content = Mock(return_value=[b"test", b" ", b"content"])
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response

        result = fetch_with_retry("https://example.com")

        assert result is not None
        mock_session.get.assert_called_once()

    @patch('src.utils.http_client.get_session')
    def test_retry_on_failure(self, mock_get_session):
        """Should retry on request failure."""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        # First two calls fail, third succeeds
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.iter_content = Mock(return_value=[b"success"])
        mock_response.raise_for_status = Mock()
        mock_session.get.side_effect = [
            requests.RequestException("Connection error"),
            requests.RequestException("Timeout"),
            mock_response
        ]

        result = fetch_with_retry("https://example.com", max_retries=3, backoff_factor=0.01)

        assert result is not None
        assert mock_session.get.call_count == 3

    @patch('src.utils.http_client.get_session')
    def test_returns_none_after_max_retries(self, mock_get_session):
        """Should return None after exhausting retries."""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        mock_session.get.side_effect = requests.RequestException("Always fails")

        result = fetch_with_retry("https://example.com", max_retries=2, backoff_factor=0.01)

        assert result is None
        assert mock_session.get.call_count == 3  # Initial + 2 retries

    @patch('src.utils.http_client.get_session')
    def test_calls_on_retry_callback(self, mock_get_session):
        """Should call on_retry callback on each retry."""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.iter_content = Mock(return_value=[b"data"])
        mock_response.raise_for_status = Mock()

        mock_session.get.side_effect = [
            requests.RequestException("Error 1"),
            requests.RequestException("Error 2"),
            mock_response
        ]

        retry_calls = []
        def on_retry(attempt, error):
            retry_calls.append((attempt, str(error)))

        result = fetch_with_retry(
            "https://example.com",
            max_retries=3,
            on_retry=on_retry,
            backoff_factor=0.01
        )

        assert result is not None
        assert len(retry_calls) == 2
        assert retry_calls[0][0] == 1
        assert retry_calls[1][0] == 2


class TestGetSession:
    """Tests for session management."""

    def setup_method(self):
        """Reset session before each test."""
        close_session()

    def teardown_method(self):
        """Clean up session after each test."""
        close_session()

    def test_creates_session(self):
        """Should create a session on first call."""
        session = get_session()
        assert session is not None
        assert isinstance(session, requests.Session)

    def test_reuses_session(self):
        """Should reuse the same session on subsequent calls."""
        session1 = get_session()
        session2 = get_session()
        assert session1 is session2

    def test_session_has_user_agent(self):
        """Session should have User-Agent header configured."""
        session = get_session()
        assert "User-Agent" in session.headers


class TestRateLimit:
    """Tests for rate_limit function."""

    def test_rate_limit_delays(self):
        """Should delay for specified seconds."""
        import time

        start = time.time()
        rate_limit(0.1)  # 100ms delay
        elapsed = time.time() - start

        assert elapsed >= 0.1
        assert elapsed < 0.2  # Should not take too long
