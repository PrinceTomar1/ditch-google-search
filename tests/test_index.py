import os
import tempfile
import unittest

from search_engine.index import SearchIndex


class InvertedIndexTests(unittest.TestCase):
    def build_tiny_index(self):
        index = SearchIndex()
        index.add_document("doc1.txt", "cats and dogs are great pets")
        index.add_document("doc2.txt", "dogs love to play fetch outside")
        index.add_document("doc3.txt", "the stock market moved higher today")
        return index

    def test_doc_count(self):
        index = self.build_tiny_index()
        self.assertEqual(index.doc_count, 3)

    def test_postings_structure(self):
        index = self.build_tiny_index()
        # "dogs" shows up in doc1 and doc2, once each
        self.assertIn("dogs", index.postings)
        self.assertEqual(index.postings["dogs"], {"doc1.txt": 1, "doc2.txt": 1})

    def test_term_frequency_counted_correctly(self):
        index = SearchIndex()
        index.add_document("repeaty.txt", "dog dog dog cat")
        self.assertEqual(index.postings["dog"]["repeaty.txt"], 3)
        self.assertEqual(index.postings["cat"]["repeaty.txt"], 1)

    def test_document_frequency(self):
        index = self.build_tiny_index()
        self.assertEqual(index.document_frequency("dogs"), 2)
        self.assertEqual(index.document_frequency("cats"), 1)
        self.assertEqual(index.document_frequency("nonexistent"), 0)

    def test_doc_lengths_recorded(self):
        index = self.build_tiny_index()
        # "cats and dogs are great pets" -> "and" and "are" are stopwords
        self.assertEqual(index.doc_lengths["doc1.txt"], 4)

    def test_save_and_load_round_trip(self):
        index = self.build_tiny_index()
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "index.json")
            index.save(path)
            loaded = SearchIndex.load(path)

        self.assertEqual(loaded.doc_count, index.doc_count)
        self.assertEqual(loaded.postings, index.postings)
        self.assertEqual(loaded.doc_lengths, index.doc_lengths)
        self.assertEqual(loaded.doc_texts, index.doc_texts)


if __name__ == "__main__":
    unittest.main()
