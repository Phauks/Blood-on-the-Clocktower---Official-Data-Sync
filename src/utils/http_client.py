"""
HTTP client utilities with retry logic and rate limiting.

Provides robust HTTP request handling for wiki scraping with:
- Exponential backoff retry on transient failures
- Rate limiting to be respectful to servers
- Consistent User-Agent across all requests
- Request size limits to prevent memory exhaustion
"""

import time
from collections.abc import Callable

import requests
from requests.exceptions import RequestException

# Import config - handle both module and direct execution
try:
    import sys
    from pathlib import Path

    # Add scrapers to path for config access
    sys.path.insert(0, str(Path(__file__).parent.parent / "scrapers"))
    from config import (
        HTTP_MAX_RETRIES,
        HTTP_RETRY_BACKOFF,
        RATE_LIMIT_SECONDS,
        REQUEST_TIMEOUT,
        USER_AGENT,
    )
except ImportError:
    # Fallback defaults
    REQUEST_TIMEOUT = 30
    RATE_LIMIT_SECONDS = 1.0
    HTTP_MAX_RETRIES = 3
    HTTP_RETRY_BACKOFF = 2.0
    USER_AGENT = "BOTC-Data-Sync/1.0"


def fetch_with_retry(
    url: str,
    max_retries: int | None = None,
    timeout: int | None = None,
    backoff_factor: float | None = None,
    on_retry: Callable[[int, Exception], None] | None = None,
    max_size_mb: int = 10,
) -> requests.Response | None:
    """Fetch a URL with automatic retry on transient failures.

    Uses exponential backoff: wait = backoff_factor * (2 ** attempt)
    e.g., with backoff_factor=1.0: 1s, 2s, 4s, 8s...

    Args:
        url: URL to fetch
        max_retries: Maximum retry attempts (default: from config)
        timeout: Request timeout in seconds (default: from config)
        backoff_factor: Base backoff time in seconds (default: from config)
        on_retry: Optional callback(attempt, exception) called before each retry
        max_size_mb: Maximum response size in megabytes (default: 10MB)

    Returns:
        Response object if successful, None if all retries failed

    Raises:
        ValueError: If response exceeds max_size_mb

    Security:
        - Validates response size to prevent memory exhaustion attacks
        - Explicitly verifies HTTPS certificates
        - Disables automatic redirects to prevent redirect-based attacks
    """
    if max_retries is None:
        max_retries = HTTP_MAX_RETRIES
    if timeout is None:
        timeout = REQUEST_TIMEOUT
    if backoff_factor is None:
        backoff_factor = HTTP_RETRY_BACKOFF

    max_size_bytes = max_size_mb * 1024 * 1024

    for attempt in range(max_retries + 1):
        try:
            # Use streaming to check size before downloading entire response
            response = requests.get(
                url,
                timeout=timeout,
                headers={"User-Agent": USER_AGENT},
                stream=True,
                verify=True,  # Explicit HTTPS verification
                allow_redirects=False,  # Prevent redirect-based attacks
            )
            response.raise_for_status()

            # Check Content-Length header if available
            content_length = response.headers.get("Content-Length")
            if content_length:
                size = int(content_length)
                if size > max_size_bytes:
                    response.close()
                    raise ValueError(
                        f"Response size ({size / 1024 / 1024:.2f}MB) exceeds "
                        f"maximum allowed ({max_size_mb}MB)"
                    )

            # Download content with size limit
            content_chunks = []
            total_size = 0

            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    total_size += len(chunk)
                    if total_size > max_size_bytes:
                        response.close()
                        raise ValueError(f"Response size exceeded {max_size_mb}MB during download")
                    content_chunks.append(chunk)

            # Reconstruct response with validated content
            response._content = b"".join(content_chunks)
            return response

        except RequestException as e:

            # Don't retry on client errors (4xx) except 429 (rate limit)
            if hasattr(e, "response") and e.response is not None:
                status = e.response.status_code
                if 400 <= status < 500 and status != 429:
                    return None

            # Last attempt - don't retry
            if attempt >= max_retries:
                break

            # Calculate backoff time
            wait_time = backoff_factor * (2**attempt)

            # Call retry callback if provided
            if on_retry:
                on_retry(attempt + 1, e)

            time.sleep(wait_time)

        except ValueError:
            # Size limit exceeded - don't retry
            raise

    return None


def fetch_url(url: str, timeout: int | None = None) -> str | None:
    """Simple URL fetch without retry (for backwards compatibility).

    Args:
        url: URL to fetch
        timeout: Request timeout in seconds

    Returns:
        Response text if successful, None on failure
    """
    response = fetch_with_retry(url, max_retries=0, timeout=timeout)
    return response.text if response else None


def fetch_json(url: str, timeout: int | None = None) -> dict | None:
    """Fetch URL and parse as JSON.

    Args:
        url: URL to fetch
        timeout: Request timeout in seconds

    Returns:
        Parsed JSON dict if successful, None on failure
    """
    response = fetch_with_retry(url, timeout=timeout)
    if response:
        try:
            return response.json()
        except ValueError:
            return None
    return None


def rate_limit(seconds: float | None = None) -> None:
    """Sleep for rate limiting.

    Args:
        seconds: Time to sleep (default: from config)
    """
    if seconds is None:
        seconds = RATE_LIMIT_SECONDS
    time.sleep(seconds)
