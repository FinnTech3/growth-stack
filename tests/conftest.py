"""Shared fixtures: the three scripts loaded as modules, and a local HTTP server whose routes each test controls."""

from __future__ import annotations

import gzip
import http.server
import importlib.util
import socketserver
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "agensi" / "growth-stack"
SCRIPTS = {
    "page_audit": PACK / "shared" / "scripts" / "page_audit.py",
    "site_probe": PACK / "shared" / "scripts" / "site_probe.py",
    "text_stats": PACK / "shared" / "scripts" / "text_stats.py",
}


def load_module(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS[name])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="session")
def pa():
    return load_module("page_audit")


@pytest.fixture(scope="session")
def sp():
    return load_module("site_probe")


@pytest.fixture(scope="session")
def ts():
    return load_module("text_stats")


class Site:
    """A throwaway HTTP server. Set routes[path] to a dict (status, headers, body, delay, gzip, dribble) or a callable."""

    def __init__(self):
        self.routes: dict[str, object] = {}
        self.log: list[tuple[str, dict]] = []
        site = self

        class Handler(http.server.BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *args):
                pass

            def do_GET(self):
                site.log.append((self.path, {k.lower(): v for k, v in self.headers.items()}))
                route = site.routes.get(self.path) or site.routes.get(self.path.split("?")[0])
                if route is None:
                    route = {"status": 404, "body": "not found", "headers": {"Content-Type": "text/plain"}}
                if callable(route):
                    return route(self)
                body = route.get("body", b"")
                body = body.encode() if isinstance(body, str) else body
                headers = {"Content-Type": "text/html; charset=utf-8", **route.get("headers", {})}
                if route.get("gzip"):
                    body = gzip.compress(body)
                    headers["Content-Encoding"] = "gzip"
                time.sleep(route.get("delay", 0))
                self.send_response(route.get("status", 200))
                for k, v in headers.items():
                    self.send_header(k, v)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                if route.get("dribble"):
                    for i in range(0, len(body), 8):
                        try:
                            self.wfile.write(body[i : i + 8])
                            self.wfile.flush()
                        except OSError:
                            return
                        time.sleep(route["dribble"])
                else:
                    self.wfile.write(body)

        class Server(http.server.ThreadingHTTPServer):
            def server_bind(self):  # skip the reverse DNS lookup of the host name, which takes about 35 s per test on macOS
                socketserver.TCPServer.server_bind(self)
                self.server_name, self.server_port = "localhost", self.server_address[1]

        self.httpd = Server(("0.0.0.0", 0), Handler)
        self.httpd.daemon_threads = True
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True)
        self.thread.start()

    def url(self, path: str = "/", host: str = "127.0.0.1") -> str:
        return f"http://{host}:{self.port}{path}"

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()


@pytest.fixture
def site():
    s = Site()
    yield s
    s.close()


def fake_response(
    html: str,
    url: str = "https://example.test/",
    status: int = 200,
    headers: dict | None = None,
    elapsed: float = 0.1,
    chain=None,
    cut: bool = False,
):
    """A response object shaped like the one get() returns, so analyze() can be tested without a network."""
    body = html.encode()
    return SimpleNamespace(
        url=url,
        status=status,
        headers={"content-type": "text/html", **(headers or {})},
        body=body,
        chain=chain or [(url, status)],
        cut=cut,
        elapsed=elapsed,
    )
