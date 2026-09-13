# ditch google

A tiny local search engine, written from scratch, that indexes a folder of
documents on your own machine and ranks search results with real TF-IDF
math. No Google API, no scraping, no network calls at all - everything
runs offline against files sitting in `data/`.

I wanted to actually understand how a search engine decides what result
goes first instead of just trusting a black box API, so I built the whole
pipeline myself: crawling files, tokenizing text, building an inverted
index, scoring documents with TF-IDF, and generating a little snippet for
each result. It's obviously nowhere near a real search engine, but every
piece of it is real - the ranking numbers are actual math, not placeholders.

## how it works

### crawling / text extraction (`search_engine/crawler.py`)

The "crawler" here just walks a directory and reads `.html` and `.txt`
files off disk. For HTML files it needs to strip out tags and get only the
text a person would actually see in a browser - so it subclasses Python's
built-in `html.parser.HTMLParser` and collects text nodes while skipping
the contents of `<script>`, `<style>`, `<head>` and `<title>` tags. No
BeautifulSoup, just the standard library. Plain `.txt` files are read as-is
with whitespace collapsed.

### tokenizing (`search_engine/tokenizer.py`)

Before anything gets indexed (or searched), text goes through the same
pipeline: lowercase everything, pull out runs of letters/digits with a
regex (which incidentally strips all punctuation), and drop common English
stopwords ("the", "and", "of", etc) from a small hardcoded set baked
directly into the code. No NLTK, no downloaded word lists. The query typed
into `search` goes through this exact same function, which matters - if
indexing and querying tokenized differently, matching would quietly break.

### the inverted index (`search_engine/index.py`)

The index is a plain dict shaped like:

```
term -> { doc_id: how many times that term shows up in that doc }
```

alongside a bit of extra bookkeeping the ranking step needs: each
document's total token count (for normalizing term frequency), the total
number of documents, and each document's extracted plain text (so
generating a snippet later doesn't require re-reading the file).

`python3 main.py index ./data` crawls the directory, tokenizes every
document, builds this structure, and writes it out as `index.json`.
`python3 main.py search ...` only ever loads that JSON file - it never
touches `data/` again, so searching stays fast no matter how many queries
you run.

### ranking - actual TF-IDF (`search_engine/ranking.py`)

This is the part I actually cared about getting right. For a document and
a query term:

- **term frequency (tf)** - how often the term appears in the doc, divided
  by the doc's total token count, so a short document and a long document
  are on a level playing field.
- **inverse document frequency (idf)** - `log(N / (1 + df)) + 1`, where
  `N` is the total number of documents and `df` is how many documents
  contain the term at all. A term that shows up in almost every document
  (weak signal) gets a low idf; a term that shows up in only one or two
  documents (strong signal) gets a high idf.
- **score** - for a multi-word query, sum `tf * idf` across every query
  term, for each document. Documents are then sorted by that score,
  highest first, and anything scoring exactly zero is dropped from the
  results entirely.

No sklearn, no numpy, no external math libraries - just `math.log` and a
couple of dicts.

### query processing (`main.py`)

The query string typed on the command line runs through the identical
`tokenize()` function used at index time, so "Machine Learning!" and
"machine learning" produce the same query terms and match the same way.

### snippets (`search_engine/snippet.py`)

For each ranked result, the snippet builder finds the first word in that
document's text matching any query term and grabs a window of a few words
on either side, with `...` marking where the snippet was truncated. It's
deliberately simple - first match wins, no attempt to find the "best"
occurrence.

## running it

No dependencies to install - everything is Python standard library. See
`requirements.txt`.

Build the index:

```
$ python3 main.py index ./data
indexed 8 documents from ./data -> index.json
```

Search it:

```
$ python3 main.py search "machine learning"
1. machine-learning.html
   score: 0.14
   snippet: Machine Learning Basics Machine learning is a branch of...

2. guitar-basics.html
   score: 0.01
   snippet: ...For New Players The first few weeks of learning guitar are mostly about your fingertips toughening up...

3. python-tips.html
   score: 0.01
   snippet: Small Python Tips That Add Up Learning to read a traceback properly will save you...

4. home-cooking.html
   score: 0.01
   snippet: ...faster by fixing their knife skills than by learning new recipes A sharp knife and a comfortable...
```

```
$ python3 main.py search "watering plants"
1. gardening-tips.html
   score: 0.04
   snippet: ...The single biggest mistake new gardeners make is watering on a schedule instead of checking the soil...
```

`index.json` isn't checked into this repo (it's a generated build
artifact, see `.gitignore`) - run the `index` command once after cloning
and `search` will work off of it from then on.

### optional web ui

There's also a tiny browser front end using nothing but the standard
library's `http.server`:

```
$ python3 main.py index ./data
$ python3 webui.py
serving 8 indexed docs at http://localhost:8000
```

Then open `http://localhost:8000` in a browser - it's a single page with a
search box and a results list, no JavaScript framework, no build step.

## tests

```
$ python3 -m unittest discover -s tests -v
```

Covers:
- tokenizer correctness (lowercasing, punctuation stripping, stopword
  removal)
- inverted index construction on a small fixture corpus
- TF-IDF scoring - a document where a term shows up repeatedly and
  distinctively scores higher than one where it barely appears, and a
  document with none of the query terms scores exactly zero
- an end-to-end test that builds the index over the real `data/` sample
  set and checks that known queries return the expected top document

All 20 tests pass on a clean checkout.

## project layout

```
main.py              cli entrypoint (index / search subcommands)
webui.py             optional local web ui
search_engine/
  crawler.py         reads .html/.txt files, strips html down to text
  tokenizer.py        lowercase, strip punctuation, split, stopwords
  index.py            builds + saves/loads the inverted index
  ranking.py          tf-idf scoring
  snippet.py          grabs a snippet around the matched term
data/                sample documents to index
tests/               unittest test suite
```

## limitations (on purpose - this is a learning project, not a product)

- no stemming or lemmatization, so "run" and "running" are treated as
  completely different terms
- no phrase queries or boolean operators (`AND` / `OR` / `"exact phrase"`)
  - every query is just "sum tf-idf across these independent terms"
- stopwords are a small hardcoded English list - nothing else is handled,
  and there's no language detection
- everything is loaded into memory as one JSON file, so this would not
  scale past a small personal document collection
- snippets grab the *first* matching word, not necessarily the most
  relevant sentence in a document
- no spelling correction, synonyms, or query expansion of any kind
