"""
Automated Test Suite for Distributed Rate Limiter
Verifies burst limits, steady-state refills, and multithreaded consistency.
"""
import unittest
import time
import threading
from src.algorithms import TokenBucket, SlidingWindowCounter, RateLimiterRegistry

class TestRateLimiter(unittest.TestCase):
    def test_token_bucket_burst_and_throttle(self):
        # 5 tokens capacity, 1 token per second refill
        bucket = TokenBucket(capacity=5, refill_rate=1.0)

        # First 5 requests should pass
        for i in range(5):
            allowed, remaining, _ = bucket.allow_request()
            self.assertTrue(allowed, f"Request {i+1} should be allowed")
            self.assertEqual(remaining, 4 - i)

        # 6th request must be rejected (burst exhausted)
        allowed, remaining, retry_after = bucket.allow_request()
        self.assertFalse(allowed)
        self.assertEqual(remaining, 0)
        self.assertGreater(retry_after, 0.0)

    def test_token_bucket_refills_over_time(self):
        bucket = TokenBucket(capacity=2, refill_rate=10.0) # 10 tokens/sec
        bucket.allow_request()
        bucket.allow_request()

        # Bucket is now empty
        allowed, _, _ = bucket.allow_request()
        self.assertFalse(allowed)

        # Wait 0.15s (should refill ~1.5 tokens)
        time.sleep(0.15)
        allowed, remaining, _ = bucket.allow_request()
        self.assertTrue(allowed, "Bucket should have refilled after wait")

    def test_sliding_window_counter_boundary(self):
        counter = SlidingWindowCounter(limit=3, window_seconds=10.0)
        self.assertTrue(counter.allow_request()[0])
        self.assertTrue(counter.allow_request()[0])
        self.assertTrue(counter.allow_request()[0])
        # 4th exceeds limit
        self.assertFalse(counter.allow_request()[0])

    def test_multithreaded_concurrency_consistency(self):
        # Proves no race conditions occur when 10 threads hit the same bucket
        bucket = TokenBucket(capacity=100, refill_rate=1.0)
        allowed_count = 0
        lock = threading.Lock()

        def worker():
            nonlocal allowed_count
            for _ in range(20):
                allowed, _, _ = bucket.allow_request()
                if allowed:
                    with lock:
                        allowed_count += 1

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Since capacity was 100, exactly 100 requests must have passed
        self.assertEqual(allowed_count, 100)

if __name__ == "__main__":
    unittest.main()
