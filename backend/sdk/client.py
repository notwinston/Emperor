"""Anthropic SDK Client wrapper for Emperor AI Assistant.

This module provides a wrapper around the Anthropic SDK client,
enabling Domain Leads and Workers to use the API with:
- Shared authentication (uses same auth as CLI for max billing)
- Default configuration
- Rate limiting and retry handling
- Sync and async interfaces
"""

import asyncio
from typing import Any, Optional

from anthropic import Anthropic, AsyncAnthropic, APIError, RateLimitError, APITimeoutError

from config import settings, get_logger

logger = get_logger(__name__)


# Default configuration
DEFAULT_MODEL = "claude-sonnet-4-20250514"
DEFAULT_MAX_TOKENS = 4096
DEFAULT_TEMPERATURE = 0.7
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # seconds


class SDKClientError(Exception):
    """Base exception for SDK client errors."""
    pass


class SDKRateLimitError(SDKClientError):
    """Raised when rate limited by the API."""
    pass


class SDKTimeoutError(SDKClientError):
    """Raised when request times out."""
    pass


class SDKClient:
    """
    Wrapper for Anthropic SDK client.

    Provides both sync and async interfaces with:
    - Automatic retry on transient failures
    - Rate limit handling
    - Consistent configuration

    Note: Uses the same authentication as Claude Code CLI,
    so requests are billed to the same account (max billing mode).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
    ):
        """
        Initialize the SDK client.

        Args:
            api_key: Anthropic API key. If not provided, uses ANTHROPIC_API_KEY env var
            model: Default model to use
            max_tokens: Default max tokens for responses
            temperature: Default temperature for responses
        """
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

        # Initialize clients (they read ANTHROPIC_API_KEY from env if not provided)
        try:
            self._sync_client = Anthropic(api_key=api_key) if api_key else Anthropic()
            self._async_client = AsyncAnthropic(api_key=api_key) if api_key else AsyncAnthropic()
            logger.info(f"SDK client initialized with model: {model}")
        except Exception as e:
            logger.error(f"Failed to initialize SDK client: {e}")
            raise SDKClientError(f"Failed to initialize SDK client: {e}")

    @property
    def sync_client(self) -> Anthropic:
        """Get the synchronous Anthropic client."""
        return self._sync_client

    @property
    def async_client(self) -> AsyncAnthropic:
        """Get the asynchronous Anthropic client."""
        return self._async_client

    def create_message(
        self,
        messages: list[dict[str, Any]],
        system: Optional[str] = None,
        tools: Optional[list[dict[str, Any]]] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> Any:
        """
        Create a message using the sync client.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system: Optional system prompt
            tools: Optional list of tool definitions
            model: Model override
            max_tokens: Max tokens override
            temperature: Temperature override

        Returns:
            Anthropic Message response

        Raises:
            SDKClientError: If request fails after retries
        """
        return self._retry_request(
            lambda: self._sync_client.messages.create(
                model=model or self.model,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature if temperature is not None else self.temperature,
                system=system or "",
                messages=messages,
                tools=tools or [],
            )
        )

    async def create_message_async(
        self,
        messages: list[dict[str, Any]],
        system: Optional[str] = None,
        tools: Optional[list[dict[str, Any]]] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> Any:
        """
        Create a message using the async client.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system: Optional system prompt
            tools: Optional list of tool definitions
            model: Model override
            max_tokens: Max tokens override
            temperature: Temperature override

        Returns:
            Anthropic Message response

        Raises:
            SDKClientError: If request fails after retries
        """
        return await self._retry_request_async(
            lambda: self._async_client.messages.create(
                model=model or self.model,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature if temperature is not None else self.temperature,
                system=system or "",
                messages=messages,
                tools=tools or [],
            )
        )

    def _retry_request(self, request_fn, max_retries: int = MAX_RETRIES) -> Any:
        """
        Execute a request with retry logic.

        Args:
            request_fn: Function that makes the API request
            max_retries: Maximum number of retries

        Returns:
            The API response

        Raises:
            SDKClientError: If all retries fail
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                return request_fn()

            except RateLimitError as e:
                last_error = e
                wait_time = RETRY_DELAY * (2 ** attempt)
                logger.warning(
                    f"Rate limited (attempt {attempt + 1}/{max_retries}). "
                    f"Waiting {wait_time}s..."
                )
                import time
                time.sleep(wait_time)

            except APITimeoutError as e:
                last_error = e
                logger.warning(
                    f"Timeout (attempt {attempt + 1}/{max_retries}). Retrying..."
                )

            except APIError as e:
                # Non-retryable API errors
                logger.error(f"API error: {e}")
                raise SDKClientError(f"API error: {e}")

            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error: {e}")
                if attempt == max_retries - 1:
                    raise SDKClientError(f"Request failed: {e}")

        raise SDKClientError(f"Request failed after {max_retries} attempts: {last_error}")

    async def _retry_request_async(self, request_fn, max_retries: int = MAX_RETRIES) -> Any:
        """
        Execute an async request with retry logic.

        Args:
            request_fn: Async function that makes the API request
            max_retries: Maximum number of retries

        Returns:
            The API response

        Raises:
            SDKClientError: If all retries fail
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                return await request_fn()

            except RateLimitError as e:
                last_error = e
                wait_time = RETRY_DELAY * (2 ** attempt)
                logger.warning(
                    f"Rate limited (attempt {attempt + 1}/{max_retries}). "
                    f"Waiting {wait_time}s..."
                )
                await asyncio.sleep(wait_time)

            except APITimeoutError as e:
                last_error = e
                logger.warning(
                    f"Timeout (attempt {attempt + 1}/{max_retries}). Retrying..."
                )

            except APIError as e:
                # Non-retryable API errors
                logger.error(f"API error: {e}")
                raise SDKClientError(f"API error: {e}")

            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error: {e}")
                if attempt == max_retries - 1:
                    raise SDKClientError(f"Request failed: {e}")

        raise SDKClientError(f"Request failed after {max_retries} attempts: {last_error}")


# Singleton instance
_sdk_client: Optional[SDKClient] = None


def get_sdk_client() -> SDKClient:
    """
    Get the singleton SDK client instance.

    Returns:
        The shared SDKClient instance
    """
    global _sdk_client
    if _sdk_client is None:
        _sdk_client = SDKClient()
    return _sdk_client
