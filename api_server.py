"""
Локальный сервер: отдаёт статику из папки проекта и POST /api/calculate для Python-расчётов.
Запуск: python api_server.py
"""

import json
import os
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

from main import process_request


ROOT = os.path.dirname(os.path.abspath(__file__))


class AppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/calculate":
            self.send_error(404, "Not Found")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json(400, {"ok": False, "error": "Некорректный JSON"})
            return
        try:
            result = process_request(body)
            self._send_json(200, {"ok": True, "result": result})
        except ValueError as e:
            self._send_json(400, {"ok": False, "error": str(e)})
        except Exception as e:
            self._send_json(500, {"ok": False, "error": str(e)})

    def _send_json(self, code: int, payload: dict):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        # тише консоль
        return


def run(host: str = "127.0.0.1", port: int = 8000):
    server = ThreadingHTTPServer((host, port), AppHandler)
    print(f"Сервер: http://{host}:{port}/  (API: POST /api/calculate)")
    server.serve_forever()


if __name__ == "__main__":
    run()
