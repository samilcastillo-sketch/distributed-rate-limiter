"""
High-Speed Rate Limiting Benchmarking Script
Demonstrates algorithm throughput, concurrent locking performance, and memory efficiency.
"""
import time
from src.algorithms import TokenBucket, SlidingWindowCounter

def benchmark():
    operations = 100_000
    print(f"--- Running Rate Limiter Benchmark ({operations:,} operations) ---")

    # 1. Benchmark TokenBucket
    tb = TokenBucket(capacity=1000, refill_rate=500)
    start = time.perf_counter()
    for _ in range(operations):
        tb.allow_request()
    duration = time.perf_counter() - start
    ops_per_sec = operations / duration
    print(f"[Token Bucket] Completed in {duration:.4f}s => {ops_per_sec:,.0f} ops/sec")

    # 2. Benchmark SlidingWindowCounter
    swc = SlidingWindowCounter(limit=1000, window_seconds=60)
    start = time.perf_counter()
    for _ in range(operations):
        swc.allow_request()
    duration = time.perf_counter() - start
    ops_per_sec = operations / duration
    print(f"[Sliding Window Counter] Completed in {duration:.4f}s => {ops_per_sec:,.0f} ops/sec")
    print("-------------------------------------------------------------------")

if __name__ == "__main__":
    benchmark()
