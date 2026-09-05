"""
Plain old TF-IDF, written out by hand so it's obvious what's happening:

  tf(term, doc)  = how often the term shows up in that doc, normalized by
                   the doc's length so long documents don't win purely by
                   being long.
  idf(term)      = log(total_docs / (1 + docs_containing_term)) - terms
                   that show up in almost every document are worth less,
                   rare terms are worth more.
  score(doc, q)  = sum over query terms of tf(term, doc) * idf(term)

No sklearn, no numpy, just dicts and a for loop.
"""

import math


def term_frequency(index, term, doc_id):
    """Raw count of `term` in `doc_id`, normalized by the doc's total
    token count so a 10-word doc and a 1000-word doc are comparable."""
    raw_count = index.postings.get(term, {}).get(doc_id, 0)
    doc_length = index.doc_lengths.get(doc_id, 0)
    if doc_length == 0:
        return 0.0
    return raw_count / doc_length


def inverse_document_frequency(index, term):
    """Classic smoothed idf: log(N / (1 + df)). The +1 keeps us from
    dividing by zero for a term that isn't in the corpus at all, and also
    softens the score a little for very rare terms."""
    doc_count = index.doc_count
    doc_freq = index.document_frequency(term)
    return math.log(doc_count / (1 + doc_freq)) + 1


def score_document(index, query_terms, doc_id):
    """Sum of tf*idf across every query term for a single document."""
    total = 0.0
    for term in query_terms:
        tf = term_frequency(index, term, doc_id)
        if tf == 0:
            continue
        idf = inverse_document_frequency(index, term)
        total += tf * idf
    return total


def rank_documents(index, query_terms):
    """Score every document in the index against the query terms and
    return a list of (doc_id, score) sorted best-first, with zero-score
    documents left out entirely."""
    scores = []
    for doc_id in index.doc_ids:
        score = score_document(index, query_terms, doc_id)
        if score > 0:
            scores.append((doc_id, score))

    scores.sort(key=lambda pair: pair[1], reverse=True)
    return scores
