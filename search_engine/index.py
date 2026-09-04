"""
Builds and persists the inverted index: term -> {doc_id: term_frequency},
plus the extra bits of bookkeeping ranking and snippets need later (doc
lengths, total doc count, per term document frequency, and the raw
extracted text of each doc so search doesn't have to re-crawl the files).
"""

import json

from search_engine.crawler import crawl_directory
from search_engine.tokenizer import tokenize


class SearchIndex:
    def __init__(self):
        # term -> {doc_id: term_frequency}
        self.postings = {}
        # doc_id -> total number of tokens in that doc (after stopword
        # removal), used for normalizing term frequency
        self.doc_lengths = {}
        # doc_id -> extracted plain text, kept around so search doesn't
        # need to touch the filesystem again to build snippets
        self.doc_texts = {}
        # insertion-ordered list of doc ids, mostly so output is stable
        self.doc_ids = []

    @property
    def doc_count(self):
        return len(self.doc_ids)

    def document_frequency(self, term):
        """How many documents contain this term at least once."""
        return len(self.postings.get(term, {}))

    def add_document(self, doc_id, text):
        tokens = tokenize(text)
        self.doc_ids.append(doc_id)
        self.doc_texts[doc_id] = text
        self.doc_lengths[doc_id] = len(tokens)

        term_counts = {}
        for token in tokens:
            term_counts[token] = term_counts.get(token, 0) + 1

        for term, count in term_counts.items():
            self.postings.setdefault(term, {})[doc_id] = count

    @classmethod
    def build_from_directory(cls, directory):
        """Crawl every .html/.txt file in `directory` and build a fresh
        index from scratch."""
        index = cls()
        documents = crawl_directory(directory)
        for doc_id in sorted(documents):
            index.add_document(doc_id, documents[doc_id])
        return index

    def to_dict(self):
        return {
            "doc_ids": self.doc_ids,
            "doc_lengths": self.doc_lengths,
            "doc_texts": self.doc_texts,
            "postings": self.postings,
        }

    @classmethod
    def from_dict(cls, data):
        index = cls()
        index.doc_ids = data["doc_ids"]
        index.doc_lengths = data["doc_lengths"]
        index.doc_texts = data["doc_texts"]
        index.postings = data["postings"]
        return index

    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, sort_keys=True)

    @classmethod
    def load(cls, path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
