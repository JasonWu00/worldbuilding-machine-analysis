"""
Placeholder
"""

import os
import re
#import json
#import requests
from typing import Tuple
import pandas as pd
# static variables that lead to where the source material is located at.
#from bs4 import BeautifulSoup
import secret_variables
import mediawiki_api_calls

API_ENDPOINT = secret_variables.WIKI_URL + "/w/api.php"
SCRAPED_FILES_PATH = "pages/"
DATASETS_PATH = "datasets/"
NOTES_PATH = "pages/notes/"
NOTES_DATE_FINDER_REGEX = r"[0-9]{4} EST, [0-9]{2} [a-zA-Z]* [0-9]{4}"

#mediawiki_api_calls.scrapecycle()

filelist = os.listdir(SCRAPED_FILES_PATH)
filelist.sort(key=lambda filename: filename[-9:-5])
filelist = filelist[1:] # drops the notes folder

noteslist = os.listdir(NOTES_PATH)
noteslist.sort(key=lambda filename: filename[-9:-5])

def altcat_cleanup(altcat: str) -> str:
    """
    Sanitizes alternate category values.
    """
    if altcat == []:
        return "None"
    altcat = altcat[0]
    if "Discordant" in altcat: # full alt cat name references some stuff other people wrote
        return "Collaboration"
    if "Blue Marble" in altcat: # a subcategory
        return "Subcategory"
    return altcat

def wordbytescount(pageid: int, isnotes: float = False) -> Tuple[int, int, float]:
    """
    For a given page ID: calculate its word count, its bytes count, its text/format ratio,
    and its average word length.

    ## Parameters
    id: a page ID.    
    isnotes: default False; determines if the function should look in pages/ or pages/notes/.
    ## Returns
    wordcount: number of words in the raw file.    
    bytescount: length of the page or topic, in bytes, including wiki formatting.    
    tfr: text/format ratio, calculated as raw text byte count / wikitext byte count.    
    wordlength: average length of words in the raw file, measured in # of letters.
    """
    path = ""
    wikifile, rawfile = "", ""
    #print(f"{pageid}W")
    if not isnotes:
        path = SCRAPED_FILES_PATH
        wikifile = [x for x in filelist if f"{pageid}W" in x][0]
        rawfile = [x for x in filelist if f"{pageid}R" in x][0]
    else:
        path = NOTES_PATH
        wikifile = [x for x in noteslist if f"{pageid}W" in x][0]
        rawfile = [x for x in noteslist if f"{pageid}R" in x][0]
    wordcount, bytescount, rawbytescount, wordlength = 0, 0, 0, 0
    with open(path+wikifile, "r", encoding="utf-8") as f:
        # UTF-8 means that some chars take up more than 1 byte
        # Thus manual counting is necessary
        bytescount = len(f.read())
    with open(path+rawfile, "r", encoding="utf-8") as f:
        # UTF-8 means that some chars take up more than 1 byte
        # Thus manual counting is necessary
        text = f.read()
        wordcount = mediawiki_api_calls.get_wordcount_text(text)
        rawbytescount = len(text)
        wordlength = len(text) / wordcount
    return wordcount, bytescount, rawbytescount / bytescount, wordlength

def get_note_dt(notesid: int) -> pd.Timestamp:
    """
    Given a main page or discussion note ID:
    return the datetime associated with its posting.
    """

    dt_pattern = r"[0-9]{1,2} [a-zA-Z]* [0-9]{4}"
    hours_pattern = r"[0-9]{4} EST"
    path = NOTES_PATH
    #wikifile = [x for x in noteslist if f"{pageid}W" in x][0]
    rawfile = [x for x in noteslist if f"{notesid}R" in x][0]
    with open(path+rawfile, "r", encoding="utf-8") as f:
        filebody = f.read()
        #mydt = filebody.split("\n\n")
        ddmmyy = re.search(dt_pattern, filebody)[0]
        # some notes have two datetimes; choose more recent
        hourminute = re.search(hours_pattern, filebody)[0][:5]
        pd_dt = pd.to_datetime(ddmmyy) + pd.Timedelta(hours=int(hourminute[:2]),
                                                    minutes=int(hourminute[2:]))
        return pd_dt
