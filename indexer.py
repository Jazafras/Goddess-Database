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
    """Iterate through data dir and load JSON objects."""
    for filename in os.listdir("data"):
        # this line is a little hacky: we don't want the category jsons
        if not filename.endswith(".json") or filename.endswith("s.json"):
            continue
        with open(os.path.join("data", filename), 'r') as fp:
            yield json.load(fp)


def load_goddess(goddess_id):
    """Use specific goddess ID to load the particular file."""
    logging.debug("Loading {}.json".format(goddess_id))
    with open(os.path.join("data", goddess_id + ".json"), 'r') as fp:
        return json.load(fp)


def search(indexer, query_string):
    """Search for query string in title and extract.
    If an exact title match is found, prefers this single result."""
    with indexer.searcher() as searcher:
        # ideally these parsers would not be created with each search
        # but we can change that later
        exact_query = QueryParser(
            "title", schema=indexer.schema).parse(query_string)
        all_query = MultifieldParser(
            ["title", "extract", "categories"], schema=indexer.schema).parse(query_string)
        results = searcher.search(exact_query)
        if len(results) > 0:
            print("Query found exact title result:")
        else:
            results = searcher.search(all_query)
            print("Length of results: " + str(len(results)))
        for line in results:  # just the first 10
            print(line['title'] + ": " + line['pageid'])
            extract_extract = get_text_from_html(
                load_goddess(line['pageid'])['extract'])
            #print("Extract of article: {}".format(extract_extract)[:1000])
            #print("..." if len(extract_extract) > 1000 else "")
            #Issues have been had with the previous 2 lines on my [Monte's] Windows8 Box...
            #I'm also not sure how to print the categories... sad.


def get_text_from_html(html_string):
    """From https://stackoverflow.com/posts/42461722/revisions
    Take the HTML markup out of the stored extracts to only index text,
    display cleanly."""
    if html_string == "":
        return None
    try:
        tree = html.fromstring(html_string)
        clean_tree = clean_html(tree)
        return clean_tree.text_content().strip()
    except XMLSyntaxError:
        logging.exception(
            "Error encountered trying to parse \"{}\"".format(html_string))
        return html_string  # this is a design choice we may come back to


def get_goddess_categories(goddess_id):
    categories = []
    titles = []
    data = json.load(open('data/cultures.json'))
    for category_key, sub_list in data.items():
        for entry in sub_list:
            if int(entry[0]) == int(goddess_id):
                categories.append(category_key)
    data = json.load(open('data/associations.json'))
    for category_key, sub_list in data.items():
        for entry in sub_list:
            if int(entry[0]) == int(goddess_id):
                categories.append(category_key)

    for category in categories:
        data = json.load(open('data/category_titles/{}.json'.format(category)))
        titles.append(data[0])
    return ", ".join(map(str, titles))

def build_index():
    """Build an index stemming extracts.
    Stores image info because these may be needed later for results display."""
    stemmer = StemmingAnalyzer()
    schema = Schema(
        images=TEXT(stored=True),
        pageid=ID(stored=True),
        categories=TEXT(stored=False),
        title=ID(stored=True),
        extract=TEXT(analyzer=stemmer, stored=False))
    if not os.path.exists("index_dir"):
        os.mkdir("index_dir")
    indexer = create_in("index_dir", schema)
    with indexer.writer() as wr:
        for goddess in iter_goddess():
            logging.debug("Indexing {} (ID {})".format(goddess['title'],
                                                       str(goddess['pageid'])))
            wr.add_document(
                title=goddess['title'],
                extract=get_text_from_html(goddess['extract']),
                pageid=str(goddess['pageid']),
                categories=get_goddess_categories(goddess['pageid']),
                images=str(goddess['images']) if 'images' in goddess else ""
                ),
    return indexer


def load_index():
    """Load previously created index."""
    return open_dir("index_dir")


def main():
    print("Directory of Goddesses (search \"exit\" to quit)")
    # ATTN PROF. MCCAMISH: COMMENT / UNCOMMENT FOR BUILDING / LOADING
    indexer = build_index()
    # indexer = load_index()
    searchTerm = input("Search a Goddess:  ")
    while searchTerm != "exit":
        results = search(indexer, searchTerm)
        searchTerm = input("Search a Goddess:  ")


if __name__ == '__main__':
    main()
