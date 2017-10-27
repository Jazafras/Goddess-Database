==REQUIREMENTS==
I set up a virtualenv on an AWS instance. 
The corresponding output of `pip freeze`:
    certifi==2017.7.27.1
    chardet==3.0.4
    idna==2.6
    requests==2.18.4
    urllib3==1.22
    Whoosh==2.7.4
    yapf==0.17.0
Except obviously you don't need to yapf it... 
==SETUP==
It will attempt to make the directories `data`, `data/images`,
and `data/categories`; I put `scraper.py` in a `src` directory
and ran it from the project root a la:
    python3 src/scraper.py
But I'm pretty sure you will be able to execute it however you
like.
Line 22 has the logging setting. Set the level to ERROR if you
don't want to see much output, or DEBUG if you feel cool seeing
text scroll up the terminal. There will be some expected 
exceptions.
==INDEXER==
indexer.py contains a function that builds an index and a function that
can search through the index. The user will be prompted for a searchterm
and have the total number of results that match the term returned.
Of those matched, the top 10 goddesses, their ID, and <90 characters of their
article extract will be printed.
Running from the project root a la:
    python3 <path to indexer.py>
is necessary in order for the index_dir to be created. After the first run, you
may want to comment/uncomment to not build the index multiple times.
