import sys
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
        query = MultifieldParser(["title", "content"], schema=indexer.schema).parse(searchTerm)
        results = searcher.search(query)
        print("Length of results: " + str(len(results)))
        for line in results:
            print line['title'] + ": " + line['content']

def index():
    schema = Schema(title=TEXT(stored=True), path=ID(stored=True), content=TEXT(stored=True))
    indexer = create_in("indexDir", schema)
    """
    It's pretty rare to want to use something other than a context
    manager when one's available.

    writer = indexer.writer()
    writer.add_document(title=u"First document", path=u"/a", content=u"This is the document we've added!")
    writer.add_document(title=u"Second document", path=u"/b", content=u"The second one is even more interesting!")
    writer.commit()
    """
    with indexer.writer() as wr:
        wr.add_document(title="here is one", path="lol", content="whatever")
        wr.add_document(title="another", path="rofl", content="also whatever")

    return indexer

def main():
    searchTerm = 'First OR Second'
    indexer = index()
    results = search(indexer, searchTerm)



if __name__ == '__main__':
    main()
