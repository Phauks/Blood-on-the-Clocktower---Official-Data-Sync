"""
HTTP client utilities with retry logic and rate limiting.

Provides robust HTTP request handling for wiki scraping with:
- Exponential backoff retry on transient failures
- Rate limiting to be respectful to servers
- Consistent User-Agent across all requests
"""

import time
from typing import Callable

import requests
from requests.exceptions import RequestException

# Import config - handle both module and direct execution
try:
    import sys
    from pathlib import Path
    # Add scrapers to path for config access
    sys.path.insert(0, str(Path(__file__).parent.parent / "scrapers"))
    from config import (
        REQUEST_TIMEOUT,
        RATE_LIMIT_SECONDS,
        HTTP_MAX_RETRIES,
        HTTP_RETRY_BACKOFF,
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
    
    Returns:
        Response object if successful, None if all retries failed
    """
    if max_retries is None:
        max_retries = HTTP_MAX_RETRIES
    if timeout is None:
        timeout = REQUEST_TIMEOUT
    if backoff_factor is None:
        backoff_factor = HTTP_RETRY_BACKOFF
    
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            response = requests.get(
                url,
                timeout=timeout,
                headers={"User-Agent": USER_AGENT}
            )
            response.raise_for_status()
            return response
            
        except RequestException as e:
            last_exception = e
            
            # Don't retry on client errors (4xx) except 429 (rate limit)
            if hasattr(e, 'response') and e.response is not None:
                status = e.response.status_code
                if 400 <= status < 500 and status != 429:
                    return None
            
            # Last attempt - don't retry
            if attempt >= max_retries:
                break
            
            # Calculate backoff time
            wait_time = backoff_factor * (2 ** attempt)
            
            # Call retry callback if provided
            if on_retry:
                on_retry(attempt + 1, e)
            
            time.sleep(wait_time)
    
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
