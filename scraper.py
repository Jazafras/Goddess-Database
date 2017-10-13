"""
Maya K. Hess
CS483-Web Data
HW 1
I rewrote the template and shared that before implementing anything.
Some people will have credited me, probably, some won't, but I ended
up changing mine substantially with the extra necessary params anyway.
Continued query stuff is based on:
https://www.mediawiki.org/wiki/API:Query#Continuing_queries
"""
from time import sleep
import logging
import html
import os
import sys
from xml.etree import ElementTree as et
import requests
import json
import re
wiki = "https://en.wikipedia.org/w/api.php"

logging.basicConfig(stream=sys.stderr, level=logging.INFO)


def get_query_params(prop_array=None, pageid_array=None, export=False):
    params = {'action': 'query', 'format': 'json'}
    if prop_array is not None:
        params['prop'] = "|".join(prop_array)
    else:
        params['prop'] = ""  # this is what the API sandbox does.
    if pageid_array is not None:
        params['pageids'] = "|".join(pageid_array)
    # I didn't end up using export because the only hierarchy within the text that I really wanted was the sections, and it was unwieldy.
    if export:
        params['export'] = ""
    return params


def exec_request(params):
    """Wraps get for argument/progress visibility and not hammering server."""
    logging.debug("Waiting on req with params: {}".format(params))
    # Commented so as not to kill your life in case you're actually running this.
    # The API etiquette says as long as requests are serial, it's fine...
    # sleep(1)
    return requests.get(wiki, params=params)


def iter_request(params):
    """Pages through results over multiple requests.
    This is only a generator because nested data structures won't automatically update."""
    continue_token = {}
    while True:
        req = params.copy()
        req.update(continue_token)
        unwrapped_object = exec_request(req).json()
        if 'error' in unwrapped_object:
            logging.error(unwrapped_object['error'])
        elif 'warnings' in unwrapped_object:
            logging.warn(unwrapped_object['warnings'])
        if 'query' in unwrapped_object:
            yield unwrapped_object['query']
        if 'continue' not in unwrapped_object:
            break
        logging.debug("Continuing query")
        continue_token = unwrapped_object['continue']


def trim_prefix(string):
    """All those 'File:whatever' -> 'whatever'"""
    if ":" not in string:
        return string
    return string.split(":", maxsplit=1)[1]


def get_category_params(return_type, cmtitle=None, cmpageid=None):
    if cmtitle is None and cmpageid is None:
        raise ValueError("specify something or other")
    params = get_query_params()
    if cmtitle is not None:
        params['cmtitle'] = cmtitle
    else:
        params['cmpageid'] = cmpageid
    params['list'] = 'categorymembers'
    params['cmtype'] = return_type
    return params


def get_page(pageid):
    """Why only one page at a time? Becase continuing prop results
    across multiple results pages is the bane of my existence."""
    params = get_query_params(
        pageid_array=[str(pageid)], prop_array=["extracts", "images"])
    return exec_request(params).json()['query']['pages'][str(pageid)]


def get_category_contents(cmtitle=None, cmpageid=None, return_type="page"):
    params = get_category_params(
        return_type, cmtitle=cmtitle, cmpageid=cmpageid)
    return [(obj['pageid'], trim_prefix(obj['title']))
            for results_page in iter_request(params)
            for obj in results_page['categorymembers']]


def save_category_contents():
    """This would be nicer done separately for association and culture,
    but procedural garbage will suffice."""
    association_cat = "Category:Goddesses by association"
    culture_cat = "Category:Goddesses by culture"

    associations = get_category_contents(
        return_type="subcat", cmtitle=association_cat)
    cultures = get_category_contents(return_type="subcat", cmtitle=culture_cat)

    association_contents = {}
    culture_contents = {}
    for cat_id, cat_title in associations:
        logging.info("Getting pages in {}".format(cat_title))
        association_contents[cat_id] = get_category_contents(cmpageid=cat_id)
        with open('data/categories/{}.json'.format(cat_id), 'w') as fp:
            json.dump(association_contents[cat_id], fp)
    for cat_id, cat_title in cultures:
        logging.info("Getting pages in {}".format(cat_title))
        culture_contents[cat_id] = get_category_contents(cmpageid=cat_id)
        with open('data/categories/{}.json'.format(cat_id), 'w') as fp:
            json.dump(culture_contents[cat_id], fp)

    # these larger files are just for convenience loading for batch ops
    with open('data/associations.json', 'w') as fp:
        json.dump(association_contents, fp)
    with open('data/cultures.json', 'w') as fp:
        json.dump(culture_contents, fp)


def save_page_jsons():
    """All goddesses affiliated with an association or culture."""
    with open('data/associations.json', 'r') as fp:
        association_contents = json.load(fp)
    with open('data/cultures.json', 'r') as fp:
        culture_contents = json.load(fp)
    all_goddesses = set(
        tuple(v) for cat in association_contents.values() for v in cat) | set(
            tuple(v) for cat in culture_contents.values() for v in cat)
    for pageid, title in all_goddesses:
        logging.info("Retrieving {}".format(title))
        with open('data/{}.json'.format(pageid), 'w') as fp:
            json.dump(get_page(pageid), fp)


def iter_goddess():
    for filename in os.listdir("data"):
        # this line is a little hacky: we don't want the category jsons
        if not filename.endswith(".json") or filename.endswith("s.json"):
            continue
        with open(os.path.join("data", filename), 'r') as fp:
            yield json.load(fp)


def get_image_titles():
    """Layered generators are good for the soul, even when we're about to
    unique them into a set."""
    for goddess in iter_goddess():
        if 'images' not in goddess:
            continue
        for image_obj in goddess['images']:
            yield image_obj['title']


def save_images():
    """"""
    for title in set(get_image_titles()):
        if already_have_image(title):
            logging.debug("Already have {}".format(title))
            continue
        if any(title.endswith(ext) for ext in ['ogg', 'wav']):
            logging.info("Wiki didn't classify {} correctly".format(title))
            continue
        try:
            url = get_url_from_title(title)
            logging.debug("Downloading {} from {}".format(title, url)) 
            download_image(url, title)
        except et.ParseError:
            logging.exception("Error getting {}".format(title))
        except TypeError:
            logging.exception(
                "Couldn't find the root node with the url for {}".format(
                    title))


def get_url_from_title(title):
    """Title is something like "File:Pretty picture.jpg", and
    what we want is the mediawiki URL we can download."""
    content = requests.get(
        "https://en.wikipedia.org/wiki/{}".format(title)).content
    root = et.fromstring(content)
    for node in root.find(".//*[@class='fullImageLink']/*[@href]"):
        return (node.attrib['src'])


def download_image(image_url, title):
    """Don't reinvent the wheel! wget will automatically retry and handle the FS.
    For svgs, we're just grabbing the png/jpg preview."""
    path = "data/images/{}{}".format(
        trim_prefix(title), image_url[-4:] if title.endswith('.svg') else "")
    os.system('wget {} -O "{}"'.format(image_url[2:], path))


def already_have_image(title):
    """This is a convenience function for the debug process so you don't
    redo everything every time you rerun."""
    return any(
        filename.startswith(trim_prefix(title))
        for filename in os.listdir('data/images'))


def setup():
    logging.info("Making directories!")
    os.makedirs('data/images', exist_ok=True)
    os.makedirs('data/categories', exist_ok=True)


def main():
    setup()
    save_category_contents()
    save_page_jsons()
    # 160mb of images: you probably don't want to do this just for grading.
    # save_images()


if __name__ == '__main__':
    main()
