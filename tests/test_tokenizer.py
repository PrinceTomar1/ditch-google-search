import unittest

from search_engine.tokenizer import tokenize


class TokenizerTests(unittest.TestCase):
    def test_lowercases_everything(self):
        self.assertEqual(tokenize("HELLO World"), ["hello", "world"])

    def test_strips_punctuation(self):
        tokens = tokenize("Wait... really?! Yes, absolutely.")
        for token in tokens:
            self.assertTrue(token.isalnum())
        self.assertNotIn("", tokens)

    def test_removes_stopwords(self):
        tokens = tokenize("The cat sat on the mat and looked at the dog")
        self.assertNotIn("the", tokens)
        self.assertNotIn("on", tokens)
        self.assertNotIn("and", tokens)
        self.assertNotIn("at", tokens)
        self.assertIn("cat", tokens)
        self.assertIn("sat", tokens)
        self.assertIn("mat", tokens)
        self.assertIn("looked", tokens)
        self.assertIn("dog", tokens)

    def test_keeps_stopwords_when_disabled(self):
        tokens = tokenize("the cat", remove_stopwords=False)
        self.assertEqual(tokens, ["the", "cat"])

    def test_empty_string(self):
        self.assertEqual(tokenize(""), [])

    def test_numbers_are_kept_as_tokens(self):
        self.assertEqual(tokenize("top 10 tips"), ["top", "10", "tips"])


if __name__ == "__main__":
    unittest.main()
