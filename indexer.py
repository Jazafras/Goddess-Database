import os
import sys
import json
import whoosh
from whoosh.index import create_in
from whoosh.fields import *
from whoosh.qparser import QueryParser
from whoosh.qparser import MultifieldParser


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


def search(indexer, searchTerm):
    with indexer.searcher() as searcher:
        query = MultifieldParser(["title", "extract"], schema=indexer.schema).parse(searchTerm)
        results = searcher.search(query)
        print("Length of results: " + str(len(results)))
        for line in results[:50]:
            print(line['title'] + ": " + line['pageid'])

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
            wr.add_document(title=goddess['title'],
                            extract=goddess['extract'],
                            pageid=str(goddess['pageid']),
                            images=str(goddess['images']) if 'images' in goddess else "")

    return indexer

def main():
    searchTerm = 'First OR Second'
    indexer = index()
    results = search(indexer, searchTerm)



if __name__ == '__main__':
    main()
