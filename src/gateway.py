"""
High Performance Rate Limiting API Gateway
Zero-dependency HTTP server that enforces throttling before routing requests.
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import logging
from .algorithms import RateLimiterRegistry

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("RateLimiterGateway")

class GatewayHandler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, data: dict, headers: dict = None):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        if headers:
            for k, v in headers.items():
                self.send_header(k, str(v))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        # Identify client by API Key header or Client IP
        client_key = self.headers.get("X-API-Key") or self.client_address[0]
        limiter = self.server.registry.get_limiter(client_key)

        allowed, remaining, retry_after = limiter.allow_request()

        rate_headers = {
            "X-RateLimit-Limit": self.server.registry.capacity,
            "X-RateLimit-Remaining": remaining,
            "X-RateLimit-Algorithm": self.server.registry.algorithm
        }

        if not allowed:
            rate_headers["Retry-After"] = retry_after
            return self._send_json(429, {
                "error": "Too Many Requests",
                "message": f"Rate limit exceeded. Try again in {retry_after} seconds.",
                "client_id": client_key
            }, rate_headers)

        if self.path == "/health":
            return self._send_json(200, {"status": "ok"}, rate_headers)

        # Normal successful response
        return self._send_json(200, {
            "message": "Request processed successfully through Rate Limiter Gateway",
            "client_id": client_key,
            "remaining_quota": remaining
        }, rate_headers)

def run_gateway(host="0.0.0.0", port=8080, algorithm="token_bucket", capacity=10, rate=5.0):
    registry = RateLimiterRegistry(algorithm=algorithm, capacity=capacity, rate_or_window=rate)
    server = HTTPServer((host, port), GatewayHandler)
    server.registry = registry
    logger.info(f"Rate Limiter Gateway running on http://{host}:{port} using [{algorithm}]")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Gateway shutting down...")
    finally:
        server.server_close()

if __name__ == "__main__":
    run_gateway()
