from pathlib import Path
import unittest

from scripts.check_site import check_page_semantics


class PageSemanticsTest(unittest.TestCase):
    def test_accepts_complete_reader_page(self) -> None:
        text = """
        <html lang="zh"><head>
        <meta name="viewport" content="width=device-width,initial-scale=1">
        </head><body>
        <a class="md-skip" href="#content">跳至正文</a>
        <main id="content"><h1>标题</h1><img src="diagram.png" alt="关系图"></main>
        </body></html>
        """
        self.assertEqual([], check_page_semantics(Path("site/example.html"), text))

    def test_rejects_missing_language_landmarks_and_alternatives(self) -> None:
        text = """
        <html><body>
        <a class="md-skip" href="#missing">跳至正文</a>
        <h1>标题一</h1><h1>标题二</h1><img src="diagram.png">
        </body></html>
        """
        errors = check_page_semantics(Path("site/broken.html"), text)
        self.assertTrue(any("one zh language" in error for error in errors))
        self.assertTrue(any("device-width viewport" in error for error in errors))
        self.assertTrue(any("one main landmark" in error for error in errors))
        self.assertTrue(any("exactly one H1" in error for error in errors))
        self.assertTrue(any("no local target" in error for error in errors))
        self.assertTrue(any("without non-empty alt text" in error for error in errors))

    def test_allows_short_error_page_without_skip_link(self) -> None:
        text = """
        <html lang="zh"><head>
        <meta name="viewport" content="width=device-width,initial-scale=1">
        </head><body><main><h1>页面未找到</h1></main></body></html>
        """
        self.assertEqual(
            [],
            check_page_semantics(
                Path("site/404.html"),
                text,
                require_skip_link=False,
            ),
        )


if __name__ == "__main__":
    unittest.main()
