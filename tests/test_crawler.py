import os
import tempfile
import unittest

from search_engine.crawler import crawl_directory, load_document


class CrawlerTests(unittest.TestCase):
    def test_empty_file_is_read_as_empty_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "empty.txt")
            open(path, "w").close()
            self.assertEqual(load_document(path), "")

    def test_malformed_html_does_not_raise(self):
        # unclosed tags, a fragment with no </html> - HTMLParser is lenient
        # about this by design, but worth pinning down that we rely on that
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "broken.html")
            with open(path, "w", encoding="utf-8") as f:
                f.write("<html><body><p>Broken <div>nested<span>text")
            text = load_document(path)
        self.assertIn("Broken", text)
        self.assertIn("nested", text)
        self.assertIn("text", text)

    def test_binary_garbage_with_html_extension_does_not_raise(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "binary.html")
            with open(path, "wb") as f:
                f.write(bytes(range(256)) * 4)
            # errors="replace" on read means this should never raise, even
            # though the bytes aren't valid utf-8 or sensible html
            load_document(path)

    def test_crawl_directory_reflects_current_directory_contents(self):
        # crawl_directory is used to fully rebuild the index every time
        # `index` runs, so it should never carry over anything from a file
        # that no longer exists
        with tempfile.TemporaryDirectory() as tmp:
            keep_path = os.path.join(tmp, "keep.txt")
            gone_path = os.path.join(tmp, "gone.txt")
            with open(keep_path, "w", encoding="utf-8") as f:
                f.write("keep this")
            with open(gone_path, "w", encoding="utf-8") as f:
                f.write("remove this")

            docs = crawl_directory(tmp)
            self.assertIn("keep.txt", docs)
            self.assertIn("gone.txt", docs)

            os.remove(gone_path)
            docs_after = crawl_directory(tmp)
            self.assertIn("keep.txt", docs_after)
            self.assertNotIn("gone.txt", docs_after)


if __name__ == "__main__":
    unittest.main()
