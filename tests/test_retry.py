import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from mapricot import Mapricot, MapricotError


def serve(statuses):
    seen = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            seen.append(self.path)
            status, code = statuses.pop(0) if statuses else (200, None)
            body = {"ok": True} if status == 200 else {"error": {"code": code, "message": code}, "requestId": "r1"}
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("X-Request-Id", "r1")
            self.end_headers()
            self.wfile.write(json.dumps(body).encode())

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, seen, f"http://127.0.0.1:{server.server_port}"


class RetryTest(unittest.TestCase):
    def test_retries_503_and_concurrency_exceeded(self):
        server, seen, base_url = serve([(503, "origin_overloaded"), (429, "concurrency_exceeded")])
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        client = Mapricot("k", base_url=base_url)
        self.assertEqual(client.search("x", focus={"lat": 1, "lon": 2}, country=["US", "CA"]), {"ok": True})
        self.assertEqual(len(seen), 3)
        self.assertEqual(seen[0], "/v1/search?q=x&focus=1%2C2&country=US%2CCA")

    def test_does_not_retry_credit_exhausted(self):
        server, seen, base_url = serve([(429, "credit_exhausted")])
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        with self.assertRaises(MapricotError) as caught:
            Mapricot("k", base_url=base_url).account()
        self.assertEqual((caught.exception.status, caught.exception.code, caught.exception.request_id), (429, "credit_exhausted", "r1"))
        self.assertEqual(len(seen), 1)
