"""
Reads local documents (.html and .txt) off disk and turns them into plain
text we can tokenize and index. Nothing here talks to the network - it's
all local files, which is the whole point of this project.
"""

import os
from html.parser import HTMLParser

# tags whose contents should never show up as visible text, even though
# HTMLParser will happily hand us the text between the open/close tags
_SKIP_TAGS = {"script", "style", "head", "title"}


class _VisibleTextExtractor(HTMLParser):
    """Strips tags out of an html document and keeps only what a person
    would actually see rendered in a browser."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._chunks = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in _SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag in _SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data):
        if self._skip_depth == 0:
            self._chunks.append(data)

    def get_text(self):
        return " ".join(self._chunks)


def extract_text_from_html(html_content):
    """Given a string of raw html, return the visible text with tags,
    scripts and styles stripped out."""
    parser = _VisibleTextExtractor()
    parser.feed(html_content)
    parser.close()
    # collapse the whitespace that tends to pile up between tags
    return " ".join(parser.get_text().split())


def load_document(path):
    """Read a single .html or .txt file from disk and return its plain
    text content. Raises ValueError for anything else."""
    ext = os.path.splitext(path)[1].lower()
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        raw = f.read()

    if ext in (".html", ".htm"):
        return extract_text_from_html(raw)
    elif ext == ".txt":
        return " ".join(raw.split())
    else:
        raise ValueError("unsupported file type: %s" % path)


def crawl_directory(directory):
    """Walk a directory (non-recursive is fine for our sample dataset, but
    this actually recurses so it scales to subfolders too) and return a
    dict of {doc_id: text} for every .html/.htm/.txt file found.

    doc_id is just the filename, e.g. "machine-learning.html", which is
    also what gets shown in search results.
    """
    documents = {}
    for root, _dirs, files in os.walk(directory):
        for filename in sorted(files):
            ext = os.path.splitext(filename)[1].lower()
            if ext not in (".html", ".htm", ".txt"):
                continue
            full_path = os.path.join(root, filename)
            doc_id = os.path.relpath(full_path, directory)
            documents[doc_id] = load_document(full_path)
    return documents
