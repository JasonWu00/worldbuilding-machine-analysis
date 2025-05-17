"""
This file uses the mediawiki_api_calls.py functions to
produce a set of pandas DataFrames that can then be used for analysis elsewhere.
"""
import os
import re
import json
import requests
import pandas as pd
# static variables that lead to where the source material is located at.
from bs4 import BeautifulSoup
import secret_variables
import mediawiki_api_calls

API_ENDPOINT = secret_variables.WIKI_URL + "/w/api.php"
SCRAPED_FILES_PATH = "pages/"
DATASETS_PATH = "datasets/"
NOTES_PATH = "pages/notes/"
NOTES_DATE_FINDER_REGEX = r"[0-9]{4} EST, [0-9]{2} [a-zA-Z]* [0-9]{4}"

#mediawiki_api_calls.scrapecycle()

pageids = mediawiki_api_calls.getallpageids()
pageids.sort()
altcats = []
for pageid in pageids:
    altcat = mediawiki_api_calls.get_categories(pageid)
    altcats.append("Undifferentiated" if altcat == [] else altcat[0])

print("pageids:")
print(pageids)
print("secondary categories for said pages:")
print(altcats)

wordcounts_main = []
filelist = os.listdir("pages/")
filelist.sort(key=lambda filename: filename[-8:-4])
filelist = filelist[:-1] # drop the Notes folder
for file in filelist:
    with open(SCRAPED_FILES_PATH + file, 'r', encoding='utf-8') as f:
        wordcounts_main.append(len(f.read().strip().split(" ")))

pages_df = pd.DataFrame({"Page ID": pageids,
                         "Other Category": altcats,
                         "Word Count": wordcounts_main,})
pages_df.to_csv(DATASETS_PATH+"main_pages_df.csv")

notesids = []
notes_filelist = os.listdir(NOTES_PATH)
notes_filelist.sort(key=lambda filename: filename[-8:-4])
for filename in notes_filelist:
    notesids.append(int(filename[-8:-4]))
#print(notesids)
print(*notes_filelist, sep="\n")

#print(mediawiki_api_calls.get_pageinfo(450))
#print(mediawiki_api_calls.get_revision_deets(2311), 6240) # expected result: 6240

notetypes = ["Discussion Notes"] * len(notesids)

# regex pulling datetimes for the notes
notesdts = []
noteswordcounts = []
pattern1 = r"[0-9]{1,2} [a-zA-Z]* [0-9]{4}"
pattern2 = r"[0-9]{4} EST"
print("Parsing the notes for datetimes")
for notesid in notesids:
    listid = notesid - mediawiki_api_calls.NOTES_IDS_START - 1
    with open(NOTES_PATH+notes_filelist[listid], 'r', encoding='utf-8') as f:
        filebody = f.read()
        mydt = filebody.split("\n\n")[1]
        ddmmyy = re.search(pattern1, mydt)[0] # some notes have two datetimes; choose more recent
        hourminute = re.search(pattern2, mydt)[0][:5]
        pd_dt = pd.to_datetime(ddmmyy) + pd.Timedelta(hours=int(hourminute[:2]),
                                                      minutes=int(hourminute[2:]))
        notesdts.append(pd_dt)
        noteswordcounts.append(len(filebody.strip().split(" ")))
    #print(listid, notes_filelist[listid], pd_dt, noteswordcounts)
#print(*notesdts, sep="\n")

notes_df = pd.DataFrame({"Page ID": notesids,
                         "Other Categories": notetypes,
                         "Word Count": noteswordcounts,
                         "Timestamp": notesdts})
notes_df.to_csv(DATASETS_PATH+"discussion_notes_df.csv")

print(mediawiki_api_calls.get_revision_history(583))

# for pageid in pageids:
#     revhistory = mediawiki_api_calls.get_revision_history(pageid)
