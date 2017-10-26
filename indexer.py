import os
import sys
import json
import whoosh
import logging
from whoosh.index import create_in
from whoosh.fields import *
from whoosh.qparser import QueryParser
from whoosh.qparser import MultifieldParser
from lxml import html
from lxml.html.clean import clean_html

logging.getLogger().setLevel(logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


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


def search(indexer, query_string):
    with indexer.searcher() as searcher:
        query = MultifieldParser(["title", "extract"], schema=indexer.schema).parse(query_string)
        results = searcher.search(query)
        print("Length of results: " + str(len(results)))
        for line in results[:50]:
            print(line['title'] + ": " + line['pageid'])

def get_text_from_html(html_string):
    """https://stackoverflow.com/posts/42461722/revisions"""
    if html_string == "":
        return None
    try:
        tree = html.fromstring(html_string)
        clean_tree = clean_html(tree)
        return clean_tree.text_content().strip()
    except XMLSyntaxError:
        logging.exception("Error encountered trying to parse \"{}\"".format(html_string))
        return html_string

def index():
    schema = Schema(images=TEXT(stored=True), pageid=ID(stored=True),
                    title=ID(stored=True), extract=TEXT(stored=False))
    indexer = create_in("index_dir", schema)
    """
    It's pretty rare to want to use something other than a context
    manager when one's available.

    writer = indexer.writer()
    writer.add_document(title=u"First document", path=u"/a", content=u"This is the document we've added!")
    writer.add_document(title=u"Second document", path=u"/b", content=u"The second one is even more interesting!")
    writer.commit()
    """
    # we're going to want to index based on the rendered html, I'd think.
    # there should be something in the stdlibs for that.
    # I'm guessing the titles should be IDs so we can do the 2-step thing
    # where we check to see if they've grabbed one exactly.
    with indexer.writer() as wr:
        for goddess in iter_goddess():
            logging.debug("Indexing {} (ID {})".format(goddess['title'], goddess['pageid']))
            wr.add_document(title=goddess['title'],
                            extract=get_text_from_html(goddess['extract']),
                            pageid=str(goddess['pageid']),
                            images=str(goddess['images']) if 'images' in goddess else "")

    return indexer

def main():
    searchTerm = 'murder'
    indexer = index()
    results = search(indexer, searchTerm)



if __name__ == '__main__':
    main()
