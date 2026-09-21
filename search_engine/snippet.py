"""
Builds a short "...surrounding words..." snippet for a search result, the
same way most search engines show a preview of where your terms actually
showed up in the page.
"""

import re

# unicode-aware so accented/non-latin words stay intact instead of getting
# chopped into fragments - see the matching note in tokenizer.py
_WORD_RE = re.compile(r"[^\W_]+", re.UNICODE)

# how many words to show on each side of the matched term
_WINDOW = 8


def make_snippet(text, query_terms, window=_WINDOW):
    """Find the first place in `text` where any of the query terms shows
    up (case-insensitively) and return a short window of words around it.

    Falls back to the first few words of the doc if none of the query
    terms actually appear in the text (shouldn't normally happen since
    this is only called on documents that scored above zero, but it's
    cheap to be safe).
    """
    words = _WORD_RE.findall(text)
    if not words:
        return ""

    query_set = {t.lower() for t in query_terms}

    match_index = None
    for i, word in enumerate(words):
        if word.lower() in query_set:
            match_index = i
            break

    if match_index is None:
        start, end = 0, window * 2
    else:
        start = max(0, match_index - window)
        end = match_index + window + 1

    end = min(end, len(words))
    snippet_words = words[start:end]
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(words) else ""

    snippet = " ".join(snippet_words)
    return "%s%s%s" % (prefix, snippet, suffix)
