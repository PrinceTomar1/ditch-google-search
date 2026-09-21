import argparse
import contextlib
import io
import os
import tempfile
import unittest

import main
from search_engine.index import SearchIndex


class CmdSearchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.index_path = os.path.join(self.tmp.name, "index.json")

        index = SearchIndex()
        index.add_document("doc1.txt", "python programming tips and tricks")
        index.save(self.index_path)

    def _run_search(self, query, index_path=None, limit=10):
        args = argparse.Namespace(
            query=query,
            index_path=index_path or self.index_path,
            limit=limit,
        )
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main.cmd_search(args)
        return code, out.getvalue()

    def test_empty_query_is_handled_without_crashing(self):
        code, out = self._run_search("")
        self.assertEqual(code, 0)
        self.assertIn("no searchable terms", out)

    def test_whitespace_only_query_is_handled(self):
        code, out = self._run_search("   ")
        self.assertEqual(code, 0)
        self.assertIn("no searchable terms", out)

    def test_zero_result_query_is_clean(self):
        code, out = self._run_search("zzzznonexistentqueryterm")
        self.assertEqual(code, 0)
        self.assertIn("no results", out)

    def test_missing_index_file_gives_clean_error(self):
        args = argparse.Namespace(
            query="python",
            index_path=os.path.join(self.tmp.name, "nope.json"),
            limit=10,
        )
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = main.cmd_search(args)
        self.assertEqual(code, 1)
        self.assertIn("not found", err.getvalue())

    def test_corrupted_index_gives_clean_error_not_a_traceback(self):
        bad_path = os.path.join(self.tmp.name, "corrupt.json")
        with open(bad_path, "w", encoding="utf-8") as f:
            f.write("{not valid json")

        args = argparse.Namespace(query="python", index_path=bad_path, limit=10)
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = main.cmd_search(args)

        self.assertEqual(code, 1)
        self.assertIn("not valid json", err.getvalue())


class CmdIndexTests(unittest.TestCase):
    def test_missing_directory_gives_clean_error(self):
        args = argparse.Namespace(
            directory="/no/such/directory/anywhere",
            output=os.path.join(tempfile.gettempdir(), "unused-index.json"),
        )
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = main.cmd_index(args)
        self.assertEqual(code, 1)
        self.assertIn("not a directory", err.getvalue())


if __name__ == "__main__":
    unittest.main()
