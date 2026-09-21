#!/usr/bin/env python3
"""
A tiny local web ui for the search engine. No frameworks, just the
standard library http.server module serving one plain html page with a
search box.

    python3 webui.py

then open http://localhost:8000 in a browser. It loads index.json on
startup the same way `main.py search` does, so build the index first:

    python3 main.py index ./data
    python3 webui.py
"""

import html
import os
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

from search_engine.index import IndexLoadError, SearchIndex
from search_engine.ranking import rank_documents
from search_engine.snippet import make_snippet
from search_engine.tokenizer import tokenize

DEFAULT_INDEX_PATH = "index.json"
DEFAULT_PORT = 8000

PAGE_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>ditch google - local search</title>
<style>
  body { font-family: sans-serif; max-width: 700px; margin: 40px auto; }
  h1 { font-size: 1.4em; }
  form { margin-bottom: 24px; }
  input[type=text] { width: 70%%; padding: 8px; font-size: 1em; }
  input[type=submit] { padding: 8px 16px; font-size: 1em; }
  .result { margin-bottom: 18px; }
  .doc-id { font-weight: bold; }
  .score { color: #666; font-size: 0.9em; }
  .snippet { color: #333; }
  .meta { color: #888; font-size: 0.85em; margin-bottom: 16px; }
</style>
</head>
<body>
<h1>ditch google</h1>
<p class="meta">a tiny local search engine indexing %(doc_count)s documents. no google involved.</p>
<form method="get" action="/">
  <input type="text" name="q" value="%(query)s" placeholder="search local docs...">
  <input type="submit" value="search">
</form>
%(results)s
</body>
</html>
"""

RESULT_TEMPLATE = """<div class="result">
  <div class="doc-id">%(rank)s. %(doc_id)s</div>
  <div class="score">score: %(score).2f</div>
  <div class="snippet">%(snippet)s</div>
</div>
"""


def render_results(index, query):
    if not query:
        return ""

    query_terms = tokenize(query)
    if not query_terms:
        return "<p>no searchable terms in that query (all stopwords?)</p>"

    ranked = rank_documents(index, query_terms)
    if not ranked:
        return "<p>no results for %s</p>" % html.escape(query)

    parts = []
    for rank, (doc_id, score) in enumerate(ranked, start=1):
        snippet = make_snippet(index.doc_texts.get(doc_id, ""), query_terms)
        parts.append(RESULT_TEMPLATE % {
            "rank": rank,
            "doc_id": html.escape(doc_id),
            "score": score,
            "snippet": html.escape(snippet),
        })
    return "".join(parts)


def make_handler(index):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            query = params.get("q", [""])[0]

            body = PAGE_TEMPLATE % {
                "doc_count": index.doc_count,
                "query": html.escape(query),
                "results": render_results(index, query),
            }

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(body.encode("utf-8"))

        def log_message(self, fmt, *args):
            # keep the default terminal output quiet-ish
            sys.stderr.write("webui: " + (fmt % args) + "\n")

    return Handler


def main():
    index_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_INDEX_PATH
    port = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_PORT

    if not os.path.exists(index_path):
        print(
            "error: %s not found - run `python3 main.py index ./data` "
            "first" % index_path,
            file=sys.stderr,
        )
        return 1

    try:
        index = SearchIndex.load(index_path)
    except IndexLoadError as exc:
        print(
            "error: %s - rebuild it with `python3 main.py index <directory>`"
            % exc,
            file=sys.stderr,
        )
        return 1
    handler = make_handler(index)
    server = HTTPServer(("localhost", port), handler)
    print("serving %d indexed docs at http://localhost:%d" % (
        index.doc_count, port))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nshutting down")
    return 0


if __name__ == "__main__":
    sys.exit(main())
