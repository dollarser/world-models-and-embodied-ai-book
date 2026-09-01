#!/usr/bin/env python3
"""Serve the strictly built book from site/ on a loopback-only HTTP server."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOOPBACK_HOSTS = {"127.0.0.1", "localhost"}


class PreviewHandler(SimpleHTTPRequestHandler):
    """Static handler with deterministic no-cache headers for local review."""

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def log_message(self, format: str, *args: object) -> None:
        return


def resolve_site(directory: str) -> Path:
    site = Path(directory)
    if not site.is_absolute():
        site = ROOT / site
    site = site.resolve()
    if not site.is_dir() or not (site / "index.html").is_file():
        raise ValueError(f"compiled book not found at {site}; run 'make docs-build' first")
    return site


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1", help="bind address; loopback by default")
    parser.add_argument("--port", type=int, default=8000, help="TCP port; default: 8000")
    parser.add_argument("--directory", default="site", help="compiled site directory; default: site")
    parser.add_argument("--check", action="store_true", help="validate the compiled site and exit")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        site = resolve_site(args.directory)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1
    if not 0 <= args.port <= 65535:
        print("ERROR: port must lie in [0, 65535]")
        return 1
    if args.host not in LOOPBACK_HOSTS:
        print(f"ERROR: host must be loopback-only: {sorted(LOOPBACK_HOSTS)}")
        return 1
    if args.check:
        print(f"compiled book preview ready: {site / 'index.html'}")
        return 0

    handler = partial(PreviewHandler, directory=str(site))
    server = ThreadingHTTPServer((args.host, args.port), handler)
    host, port = server.server_address[:2]
    print(f"Serving compiled book at http://{host}:{port}/ (Ctrl-C to stop)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping preview server.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
