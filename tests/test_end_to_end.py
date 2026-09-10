import os
import unittest

from search_engine.index import SearchIndex
from search_engine.ranking import rank_documents
from search_engine.tokenizer import tokenize

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


class EndToEndTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = SearchIndex.build_from_directory(DATA_DIR)

    def test_index_picks_up_the_whole_sample_dataset(self):
        # every sample doc under data/ should have made it into the index
        self.assertGreaterEqual(self.index.doc_count, 8)

    def test_machine_learning_query_ranks_the_right_doc_first(self):
        query = tokenize("machine learning")
        results = rank_documents(self.index, query)
        self.assertTrue(results, "expected at least one ranked result")
        top_doc_id, _score = results[0]
        self.assertEqual(top_doc_id, "machine-learning.html")

    def test_gardening_query_ranks_the_right_doc_first(self):
        query = tokenize("watering plants soil")
        results = rank_documents(self.index, query)
        self.assertTrue(results)
        top_doc_id, _score = results[0]
        self.assertEqual(top_doc_id, "gardening-tips.html")

    def test_scores_are_sorted_descending(self):
        query = tokenize("guitar chords")
        results = rank_documents(self.index, query)
        scores = [score for _doc_id, score in results]
        self.assertEqual(scores, sorted(scores, reverse=True))


if __name__ == "__main__":
    unittest.main()
