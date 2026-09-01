from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer
import sys
from tempfile import TemporaryDirectory
from threading import Thread
import unittest
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from serve_book import PreviewHandler, resolve_site  # noqa: E402


class ServeBookTests(unittest.TestCase):
    def test_resolve_site_accepts_compiled_index(self):
        with TemporaryDirectory() as directory:
            site = Path(directory)
            (site / "index.html").write_text("<!doctype html>", encoding="utf-8")
            self.assertEqual(resolve_site(str(site)), site.resolve())

    def test_resolve_site_rejects_missing_index(self):
        with TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                resolve_site(directory)

    def test_loopback_server_returns_compiled_page_and_review_headers(self):
        with TemporaryDirectory() as directory:
            site = Path(directory)
            (site / "index.html").write_text("<!doctype html><title>Book</title>", encoding="utf-8")
            handler = partial(PreviewHandler, directory=str(site))
            server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with urlopen(f"http://127.0.0.1:{server.server_port}/", timeout=2) as response:
                    self.assertEqual(response.status, 200)
                    self.assertIn(b"<title>Book</title>", response.read())
                    self.assertEqual(response.headers["Cache-Control"], "no-store")
                    self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
