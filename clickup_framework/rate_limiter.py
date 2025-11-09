"""
Rate Limiter

Implements token bucket algorithm for API rate limiting.
Default: 100 requests per minute (ClickUp standard plan limit)
"""

import time
import threading
from typing import Optional


class RateLimiter:
    """Token bucket rate limiter for API requests."""

    def __init__(self, requests_per_minute: int = 100):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests allowed per minute
        """
        self.requests_per_minute = requests_per_minute
        self.tokens = requests_per_minute
        self.max_tokens = requests_per_minute
        self.last_update = time.time()
        self.lock = threading.Lock()

        # Calculate token refill rate (tokens per second)
        self.refill_rate = requests_per_minute / 60.0

    def acquire(self, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """
        Acquire tokens for making requests.

        Blocks until tokens are available or timeout expires.

        Args:
            tokens: Number of tokens to acquire (default: 1)
            timeout: Maximum time to wait in seconds (None = wait forever)

        Returns:
            True if tokens acquired, False if timeout

        Raises:
            ValueError: If tokens requested exceeds max_tokens
        """
        if tokens > self.max_tokens:
            raise ValueError(
                f"Cannot acquire {tokens} tokens (max: {self.max_tokens})"
            )

        start_time = time.time()

        while True:
            with self.lock:
                # Refill tokens based on time elapsed
                now = time.time()
                elapsed = now - self.last_update
                self.tokens = min(
                    self.max_tokens, self.tokens + elapsed * self.refill_rate
                )
                self.last_update = now

                # Check if we have enough tokens
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return True

            # Check timeout
            if timeout is not None:
                if time.time() - start_time >= timeout:
                    return False

            # Wait a bit before trying again
            sleep_time = min(0.1, (tokens - self.tokens) / self.refill_rate)
            time.sleep(sleep_time)

    def get_available_tokens(self) -> float:
        """Get current number of available tokens."""
        with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            tokens = min(self.max_tokens, self.tokens + elapsed * self.refill_rate)
            return tokens

    def reset(self):
        """Reset rate limiter to full capacity."""
        with self.lock:
            self.tokens = self.max_tokens
            self.last_update = time.time()

    def __repr__(self) -> str:
        return (
            f"RateLimiter(requests_per_minute={self.requests_per_minute}, "
            f"available_tokens={self.get_available_tokens():.2f})"
        )
