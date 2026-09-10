import unittest

from search_engine.index import SearchIndex
from search_engine.ranking import rank_documents, score_document
from search_engine.tokenizer import tokenize


class RankingTests(unittest.TestCase):
    def setUp(self):
        self.index = SearchIndex()
        # "python" is common and unremarkable in doc_common, but the
        # dominant, repeated subject in doc_focused - it should score
        # noticeably higher for a "python" query.
        self.index.add_document(
            "doc_focused.txt",
            "python python python is a great programming language for "
            "python beginners who want to learn python quickly",
        )
        self.index.add_document(
            "doc_common.txt",
            "we discussed several languages including java ruby python "
            "and go during the meeting",
        )
        self.index.add_document(
            "doc_unrelated.txt",
            "the weather today is sunny with a light breeze from the west",
        )

    def test_document_with_more_occurrences_scores_higher(self):
        query = tokenize("python")
        focused_score = score_document(self.index, query, "doc_focused.txt")
        common_score = score_document(self.index, query, "doc_common.txt")
        self.assertGreater(focused_score, common_score)

    def test_unrelated_document_scores_zero(self):
        query = tokenize("python")
        score = score_document(self.index, query, "doc_unrelated.txt")
        self.assertEqual(score, 0.0)

    def test_rank_documents_orders_best_first(self):
        query = tokenize("python")
        ranked = rank_documents(self.index, query)
        ranked_doc_ids = [doc_id for doc_id, _score in ranked]
        self.assertEqual(ranked_doc_ids[0], "doc_focused.txt")
        self.assertNotIn("doc_unrelated.txt", ranked_doc_ids)

    def test_rare_term_worth_more_than_common_term(self):
        # "python" appears in 2/3 docs, "java" appears in only 1/3 docs.
        # both appear once in doc_common, so idf alone should make "java"
        # score higher than "python" there.
        java_score = score_document(self.index, ["java"], "doc_common.txt")
        python_score = score_document(
            self.index, ["python"], "doc_common.txt")
        self.assertGreater(java_score, python_score)


if __name__ == "__main__":
    unittest.main()
