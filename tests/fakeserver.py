"""测试用的本地 HTTP 服务：模拟 OpenAI 兼容接口和更新服务器。"""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class FakeServer:
    """routes: {(method, path): handler(body_dict) -> (status, bytes|dict, content_type)}"""

    def __init__(self):
        self.routes: dict = {}
        self.requests: list = []
        outer = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _handle(self, method):
                n = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(n) if n else b""
                try:
                    body = json.loads(raw) if raw else {}
                except Exception:
                    body = {}
                outer.requests.append((method, self.path, dict(self.headers), body))
                fn = outer.routes.get((method, self.path))
                if fn is None:
                    status, data, ctype = 404, {"error": {"message": "not found"}}, "application/json"
                else:
                    status, data, ctype = fn(body)
                if isinstance(data, (dict, list)):
                    data = json.dumps(data).encode()
                self.send_response(status)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self):
                self._handle("GET")

            def do_POST(self):
                self._handle("POST")

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def json(self, method, path, payload, status=200):
        self.routes[(method, path)] = lambda body: (status, payload, "application/json")

    def close(self):
        self.httpd.shutdown()
