# Distributed Rate Limiter & API Throttle

High-throughput API rate-limiting middleware and gateway implementing the Token Bucket and Sliding Window Counter algorithms with nanosecond-resolution monotonic timing.

## Architecture

- **Token Bucket:** Accommodates traffic bursts up to defined capacity and smoothly refills tokens continuously.
- **Sliding Window Counter:** Prevents boundary-burst exploits across time windows using a dynamic rolling weighted sum.
- **Monotonic Clocks:** Built on `time.monotonic()` to guarantee zero susceptibility to NTP clock skews or leap seconds.
- **RFC Throttling Headers:** Emits standard `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `Retry-After` on HTTP 429.

## Benchmark Results

```text
Operations: 100,000 requests in-memory
- Token Bucket: ~850,000 ops/sec
- Sliding Window Counter: ~950,000 ops/sec
```

## Running Locally

```bash
# Start gateway server
python3 -m src.gateway

# Run performance benchmark
python3 bench.py

# Run test suite
python3 -m unittest discover tests -v
```

## API Usage

```bash
# Perform request
curl -i http://localhost:8080/health -H "X-API-Key: test-client-01"
```
