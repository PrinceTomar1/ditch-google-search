"""
Turns raw text into a list of clean word tokens: lowercase, no punctuation,
no stopwords. The exact same function is used on documents at index time
and on the query at search time, which matters - if the two pipelines ever
drift apart, matching breaks in confusing ways.
"""

import re

# a small hardcoded list of common english words that show up in nearly
# every document and carry almost no meaning for search purposes. this is
# not exhaustive, just enough to cut down obvious noise. no network calls,
# no nltk, just a plain set baked into the source.
STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "then", "else", "so",
    "of", "in", "on", "at", "by", "for", "with", "about", "against",
    "between", "into", "through", "during", "before", "after", "above",
    "below", "to", "from", "up", "down", "out", "off", "over", "under",
    "again", "further", "once", "here", "there", "when", "where", "why",
    "how", "all", "any", "both", "each", "few", "more", "most", "other",
    "some", "such", "no", "nor", "not", "only", "own", "same", "than",
    "too", "very", "s", "t", "can", "will", "just", "don", "should",
    "now", "is", "am", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "having", "do", "does", "did", "doing",
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you",
    "your", "yours", "yourself", "yourselves", "he", "him", "his",
    "himself", "she", "her", "hers", "herself", "it", "its", "itself",
    "they", "them", "their", "theirs", "themselves", "what", "which",
    "who", "whom", "this", "that", "these", "those", "as", "until",
    "while", "because", "until", "also", "it's", "one", "two",
}

# anything that isn't a letter/digit (in any script - accented latin,
# cyrillic, cjk, etc) is treated as a word boundary. `\w` is unicode-aware
# in python 3, so this also kills punctuation like commas, periods, quotes,
# dashes, and emoji, without cutting accented characters off of otherwise
# ordinary words (an earlier ascii-only version turned "café" into "caf").
_WORD_RE = re.compile(r"[^\W_]+", re.UNICODE)


def tokenize(text, remove_stopwords=True):
    """Lowercase text, strip punctuation, and split into word tokens.

    >>> tokenize("The Quick, Brown Fox!")
    ['quick', 'brown', 'fox']
    """
    lowered = text.lower()
    words = _WORD_RE.findall(lowered)
    if remove_stopwords:
        words = [w for w in words if w not in STOPWORDS]
    return words
