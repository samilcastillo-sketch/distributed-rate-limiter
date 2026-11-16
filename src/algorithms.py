"""
Rate Limiting Core Algorithms
Implements Token Bucket and Sliding Window Counter algorithms
with thread-safe monotonic clock time calculations.
"""
import time
import threading
from typing import Tuple, Dict

class TokenBucket:
    """
    Token Bucket Algorithm
    - capacity: Maximum burst size allowed.
    - refill_rate: Tokens added per second.
    """
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = float(capacity)
        self.refill_rate = float(refill_rate)
        self.tokens = float(capacity)
        self.last_refill = time.monotonic()
        self.lock = threading.Lock()

    def allow_request(self, tokens_needed: int = 1) -> Tuple[bool, int, float]:
        """
        Returns:
            (allowed: bool, remaining_tokens: int, retry_after_seconds: float)
        """
        with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.last_refill = now

            # Refill tokens up to capacity
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)

            if self.tokens >= tokens_needed:
                self.tokens -= tokens_needed
                return True, int(self.tokens), 0.0
            else:
                missing = tokens_needed - self.tokens
                retry_after = missing / self.refill_rate
                return False, int(self.tokens), round(retry_after, 3)

class SlidingWindowCounter:
    """
    Sliding Window Counter Algorithm
    Smooths traffic spikes across minute/second boundaries by computing
    a weighted average between the previous window and current window.
    """
    def __init__(self, limit: int, window_seconds: float = 60.0):
        self.limit = limit
        self.window_seconds = window_seconds
        self.current_window = int(time.time() // window_seconds)
        self.current_count = 0
        self.previous_count = 0
        self.lock = threading.Lock()

    def allow_request(self) -> Tuple[bool, int, float]:
        with self.lock:
            now = time.time()
            window = int(now // self.window_seconds)

            if window != self.current_window:
                if window == self.current_window + 1:
                    self.previous_count = self.current_count
                else:
                    self.previous_count = 0
                self.current_window = window
                self.current_count = 0

            # Weight factor for previous window
            window_progress = (now % self.window_seconds) / self.window_seconds
            estimated_count = self.previous_count * (1.0 - window_progress) + self.current_count

            if estimated_count < self.limit:
                self.current_count += 1
                remaining = max(0, int(self.limit - estimated_count - 1))
                return True, remaining, 0.0
            else:
                retry_after = self.window_seconds * (1.0 - window_progress)
                return False, 0, round(retry_after, 2)

class RateLimiterRegistry:
    """
    Manages isolated buckets per Client IP or API Key.
    """
    def __init__(self, algorithm: str = "token_bucket", capacity: int = 10, rate_or_window: float = 2.0):
        self.algorithm = algorithm
        self.capacity = capacity
        self.rate_or_window = rate_or_window
        self.buckets: Dict[str, object] = {}
        self.lock = threading.Lock()

    def get_limiter(self, key: str):
        with self.lock:
            if key not in self.buckets:
                if self.algorithm == "token_bucket":
                    self.buckets[key] = TokenBucket(self.capacity, self.rate_or_window)
                else:
                    self.buckets[key] = SlidingWindowCounter(self.capacity, self.rate_or_window)
            return self.buckets[key]
