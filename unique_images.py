import json
import os

goddesses = {} # id to images.
for f in os.listdir("data"):
  if(f.endswith(".json")):
    with open('data/' + f, 'r') as goddess_file:
      goddess = json.load(goddess_file)
      if('images' in goddess.keys()):
        goddesses[f] = goddess["images"]
        #goddesses[f[:-5]] = goddess["images"]

count_hash = {}
for key in goddesses:
  for images in goddesses[key]:
    if images["title"] not in count_hash:
      count_hash[images["title"]] = 1
    else:
      count_hash[images["title"]] = count_hash[images["title"]] + 1

for key in goddesses:
  for images in goddesses[key]:
    if(count_hash[images["title"]] < count_hash[goddesses[key][0]["title"]]):
      if(count_hash[images["title"]] > 1):
        print(count_hash[images["title"]])
      dum = images["title"]
      images["title"] = goddesses[key][0]["title"]
      goddesses[key][0]["title"] = dum

for key in goddesses:
  with open('data/' + key, 'r') as goddess_file:
    goddess = json.load(goddess_file)
    if('images' in goddess.keys()):
      goddess["images"] = goddesses[key]
  with open('data/' + key, 'w') as goddess_file:
    json.dump(goddess, goddess_file)
