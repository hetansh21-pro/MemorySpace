"""
MemorySpace Lightweight Web Dashboard Server
Zero-dependency HTTP server with REST API & Real-time Web UI.
"""

import json
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from ..core.monitor import get_memory_stats, get_top_processes
from ..core.protector import (
    protect_all_configured_apps,
    add_app_to_protection,
    remove_app_from_protection,
)
from ..core.optimizer import optimize_memory_soft
from ..config import load_config
from ..daemon import is_daemon_running

STATIC_DIR = Path(__file__).resolve().parent / "static"


class MemorySpaceHTTPHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress noisy HTTP request logging in stdout
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            self._serve_file(STATIC_DIR / "index.html", "text/html; charset=utf-8")
        elif path == "/style.css":
            self._serve_file(STATIC_DIR / "style.css", "text/css; charset=utf-8")
        elif path == "/app.js":
            self._serve_file(STATIC_DIR / "app.js", "application/javascript; charset=utf-8")
        elif path == "/api/status":
            self._send_json({
                "memory": get_memory_stats(),
                "daemon_running": is_daemon_running(),
                "config": load_config(),
            })
        elif path == "/api/processes":
            limit = 20
            qs = parse_qs(parsed.query)
            if "limit" in qs:
                try:
                    limit = int(qs["limit"][0])
                except Exception:
                    pass
            self._send_json({
                "processes": get_top_processes(limit=limit),
                "protection": protect_all_configured_apps(),
            })
        else:
            self.send_error(404, "File Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            payload = {}

        if path == "/api/optimize":
            res = optimize_memory_soft()
            stats = get_memory_stats()
            self._send_json({"success": True, "result": res, "stats": stats})
        elif path == "/api/protect":
            app_name = payload.get("app")
            if app_name:
                add_app_to_protection(app_name)
                self._send_json({"success": True, "message": f"Added '{app_name}' to protected list"})
            else:
                self._send_json({"success": False, "error": "Missing 'app' param"}, 400)
        elif path == "/api/unprotect":
            app_name = payload.get("app")
            if app_name:
                remove_app_from_protection(app_name)
                self._send_json({"success": True, "message": f"Removed '{app_name}' from protected list"})
            else:
                self._send_json({"success": False, "error": "Missing 'app' param"}, 400)
        else:
            self.send_error(404, "Endpoint Not Found")

    def _serve_file(self, filepath: Path, content_type: str):
        if not filepath.exists():
            self.send_error(404, "File Not Found")
            return
        try:
            with open(filepath, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, str(e))

    def _send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)


def start_web_server(host: str = "127.0.0.1", port: int = 7890, block: bool = True):
    server = HTTPServer((host, port), MemorySpaceHTTPHandler)
    print(f"MemorySpace Web Dashboard running at: http://{host}:{port}")
    if block:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down MemorySpace Web Dashboard...")
            server.server_close()
    else:
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        return server
