import os
import sys
import json
import whoosh
import logging
from whoosh.index import create_in, open_dir
from whoosh.fields import *
from whoosh.qparser import QueryParser
from whoosh.qparser import MultifieldParser
from whoosh.analysis import StemmingAnalyzer
from lxml import html
from lxml.html.clean import clean_html

logging.basicConfig(stream=sys.stderr, level=logging.INFO)


def iter_goddess():
    """This is from my scraper.
    Seems handy, don't it!
    """
    for filename in os.listdir("data"):
        # this line is a little hacky: we don't want the category jsons
        if not filename.endswith(".json") or filename.endswith("s.json"):
            continue
        with open(os.path.join("data", filename), 'r') as fp:
            yield json.load(fp)


def load_goddess(goddess_id):
    with open(os.path.join("data", goddess_id + ".json"), 'r') as fp:
        return json.load(fp)


def search(indexer, query_string):
    with indexer.searcher() as searcher:
        exact_query = QueryParser(
            "title", schema=indexer.schema).parse(query_string)
        all_query = MultifieldParser(
            ["title", "extract"], schema=indexer.schema).parse(query_string)
        results = searcher.search(exact_query)
        if len(results) > 0:
            print("Query found title result:")
        else:
            results = searcher.search(all_query)
            print("Length of results: " + str(len(results)))
        for line in results:  # just the first 10
            print(line['title'] + ": " + line['pageid'])
            extract_extract = get_text_from_html(
                load_goddess(line['pageid'])['extract'])
            print("Extract of article: {}".format(extract_extract)[:1000])
            print("..." if len(extract_extract) > 1000 else "")


def get_text_from_html(html_string):
    """https://stackoverflow.com/posts/42461722/revisions"""
    if html_string == "":
        return None
    try:
        tree = html.fromstring(html_string)
        clean_tree = clean_html(tree)
        return clean_tree.text_content().strip()
    except XMLSyntaxError:
        logging.exception(
            "Error encountered trying to parse \"{}\"".format(html_string))
        return html_string


def build_index():
    stemmer = StemmingAnalyzer()
    schema = Schema(
        images=TEXT(stored=True),
        pageid=ID(stored=True),
        title=ID(stored=True),
        extract=TEXT(analyzer=stemmer, stored=False))
    indexer = create_in("index_dir", schema)
    with indexer.writer() as wr:
        #not a goddess, a goddess category. They're in data/categories.
        for goddess in iter_goddess():
            logging.debug("Indexing {} (ID {})".format(goddess['title'],
                                                       str(goddess['pageid'])))
            wr.add_document(
                title=goddess['title'],
                extract=get_text_from_html(goddess['extract']),
                pageid=str(goddess['pageid']),
                images=str(goddess['images']) if 'images' in goddess else "")
    return indexer


def load_index():
    return open_dir("index_dir")


def main():
    print("Directory of Goddesses (search \"exit\" to quit)")
    # indexer = build_index()
    indexer = load_index()
    searchTerm = input("Search a Goddess:  ")
    while searchTerm != "exit":
        results = search(indexer, searchTerm)
        searchTerm = input("Search a Goddess:  ")


if __name__ == '__main__':
    main()
