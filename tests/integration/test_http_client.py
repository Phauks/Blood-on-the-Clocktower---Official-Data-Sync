"""Integration tests for HTTP client with retry logic."""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, Mock
import requests

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "utils"))

from http_client import fetch_with_retry, rate_limit


class TestFetchWithRetry:
    """Tests for fetch_with_retry function."""

    @patch('http_client.requests.get')
    def test_successful_fetch(self, mock_get):
        """Should return response on successful fetch."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "test content"
        mock_response.headers = {"Content-Length": "12"}
        mock_response.iter_content = Mock(return_value=[b"test", b" ", b"content"])
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = fetch_with_retry("https://example.com")

        assert result is not None
        mock_get.assert_called_once()

    @patch('http_client.requests.get')
    def test_retry_on_failure(self, mock_get):
        """Should retry on request failure."""
        # First two calls fail, third succeeds
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.iter_content = Mock(return_value=[b"success"])
        mock_response.raise_for_status = Mock()
        mock_get.side_effect = [
            requests.RequestException("Connection error"),
            requests.RequestException("Timeout"),
            mock_response
        ]

        result = fetch_with_retry("https://example.com", max_retries=3)

        assert result is not None
        assert mock_get.call_count == 3

    @patch('http_client.requests.get')
    def test_returns_none_after_max_retries(self, mock_get):
        """Should return None after exhausting retries."""
        mock_get.side_effect = requests.RequestException("Always fails")

        result = fetch_with_retry("https://example.com", max_retries=2)

        assert result is None
        assert mock_get.call_count == 3  # Initial + 2 retries

    @patch('http_client.requests.get')
    def test_calls_on_retry_callback(self, mock_get):
        """Should call on_retry callback on each retry."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.iter_content = Mock(return_value=[b"data"])
        mock_response.raise_for_status = Mock()

        mock_get.side_effect = [
            requests.RequestException("Error 1"),
            requests.RequestException("Error 2"),
            mock_response
        ]

        retry_calls = []
        def on_retry(attempt, error):
            retry_calls.append((attempt, str(error)))

        result = fetch_with_retry("https://example.com", max_retries=3, on_retry=on_retry)

        assert result is not None
        assert len(retry_calls) == 2
        assert retry_calls[0][0] == 1
        assert retry_calls[1][0] == 2


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
