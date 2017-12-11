## Goddesses Database Search

To run, first run:

`python3 scraper.py`

Then, you need to move the scraped images to the appropriate directory:

`mv data/images static/goddess_images/images`

Alternatively, you could comment out the line that scrapes images, and use the images from the google drive, sent by Monte. Place those images in the `static/goddess_images/images` directory. Now, index the data with `python3 indexer.py`. Now, run the code that assigns similarities with `python3 similarities.py`. Finally, run `python3 unique_images.py` to assign images in the best way possible to their respective goddess.

After everything is together, you can run the program with `python3 goddesses.py`.

This is the whole git repo.
