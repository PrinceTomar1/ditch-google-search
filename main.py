#!/usr/bin/env python3
"""
Command line entrypoint for the search engine.

    python3 main.py index ./data
    python3 main.py search "machine learning"

`index` crawls a directory of .html/.txt files and writes index.json.
`search` loads that index.json and runs a query against it - it never
re-reads the source documents, so search stays fast even as the number of
queries grows.
"""

import argparse
import os
import sys

from search_engine.index import IndexLoadError, SearchIndex
from search_engine.ranking import rank_documents
from search_engine.snippet import make_snippet
from search_engine.tokenizer import tokenize

DEFAULT_INDEX_PATH = "index.json"


def cmd_index(args):
    directory = args.directory
    if not os.path.isdir(directory):
        print("error: %s is not a directory" % directory, file=sys.stderr)
        return 1

    index = SearchIndex.build_from_directory(directory)
    if index.doc_count == 0:
        print("warning: no .html/.txt files found in %s" % directory,
              file=sys.stderr)

    index.save(args.output)
    print("indexed %d documents from %s -> %s" % (
        index.doc_count, directory, args.output))
    return 0


def cmd_search(args):
    if not os.path.exists(args.index_path):
        print(
            "error: %s not found - run `python3 main.py index ./data` "
            "first" % args.index_path,
            file=sys.stderr,
        )
        return 1

    try:
        index = SearchIndex.load(args.index_path)
    except IndexLoadError as exc:
        print(
            "error: %s - rebuild it with `python3 main.py index <directory>`"
            % exc,
            file=sys.stderr,
        )
        return 1

    query_terms = tokenize(args.query)

    if not query_terms:
        print("query had no searchable terms after removing stopwords")
        return 0

    results = rank_documents(index, query_terms)[: args.limit]

    if not results:
        print("no results for %r" % args.query)
        return 0

    for rank, (doc_id, score) in enumerate(results, start=1):
        snippet = make_snippet(index.doc_texts.get(doc_id, ""), query_terms)
        print("%d. %s" % (rank, doc_id))
        print("   score: %.2f" % score)
        print("   snippet: %s" % snippet)
        print()

    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="a tiny local search engine - no google required",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    index_parser = subparsers.add_parser(
        "index", help="crawl a directory and build the search index")
    index_parser.add_argument(
        "directory", help="directory of .html/.txt files to index")
    index_parser.add_argument(
        "-o", "--output", default=DEFAULT_INDEX_PATH,
        help="where to write the index json (default: %(default)s)")
    index_parser.set_defaults(func=cmd_index)

    search_parser = subparsers.add_parser(
        "search", help="query a previously built index")
    search_parser.add_argument("query", help="text to search for")
    search_parser.add_argument(
        "-i", "--index-path", default=DEFAULT_INDEX_PATH,
        help="path to the index json (default: %(default)s)")
    search_parser.add_argument(
        "-n", "--limit", type=int, default=10,
        help="max number of results to show (default: %(default)s)")
    search_parser.set_defaults(func=cmd_search)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
