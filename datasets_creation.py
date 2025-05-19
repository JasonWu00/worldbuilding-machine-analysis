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

# Counts words manually. Not part of the API calls since they don't return that info and I don't
# feel like API calling the raw html every time I want to check.
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
pages_df["Page Size (Bytes)"] = pages_df["Page ID"].apply(mediawiki_api_calls.get_pagesize)
pages_df.to_csv(DATASETS_PATH+"main_pages_df.csv", index=False)

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
notesbytescounts = []
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
        notesbytescounts.append(len(filebody))
    #print(listid, notes_filelist[listid], pd_dt, noteswordcounts)
#print(*notesdts, sep="\n")

notes_df = pd.DataFrame({"Page ID": notesids,
                         "Other Categories": notetypes,
                         "Word Count": noteswordcounts,
                         "Page Size (Bytes)": notesbytescounts,
                         "Timestamp": notesdts})
notes_df.to_csv(DATASETS_PATH+"discussion_notes_df.csv", index=False)

print(mediawiki_api_calls.get_revision_history(583))

revid_list = []
minor_list = []
for pageid in pageids:
    hist = mediawiki_api_calls.get_revision_history(pageid)
    for rev in hist:
        revid_list.append(rev["revid"]) #"revision id"
        minor_list.append(rev["minor"])

notes = """
Revisions:
- Revision page ID
- Page ID
- Timestamp
- is marked as "minor" or not
- Size of revision
"""
pageid_list = []
diffsize_list = []
timestamp_list = []
revsize_list = []
for revid in revid_list:
    rev_deets = mediawiki_api_calls.get_revision_deets(revid)
    pageid_list.append(rev_deets["toid"])
    # timestamp raw looks like: 2025-04-13T05:14:42Z
    timestamp_list.append(pd.to_datetime(rev_deets["totimestamp"]).tz_localize(None))
    revsize_list.append(rev_deets["tosize"] - rev_deets["fromsize"] if "fromsize" in rev_deets else 0)

revs_df = pd.DataFrame({
    "Revision ID": revid_list,
    "Page ID": pageid_list,
    "Timestamp": timestamp_list,
    "Is Minor": minor_list,
    "Revision Size (Bytes)": revsize_list
})
revs_df.to_csv(DATASETS_PATH+"revisions_df.csv", index=False)