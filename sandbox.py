"""
For testing out short snips of code.
"""
import time
import os
import secret_variables
import mediawiki_api_calls
import pandas as pd
import regex_cleaners
import pandas_df_funcs
from bs4 import BeautifulSoup
import numpy as np

SCRAPED_FILES_PATH = "pages/"
DATASETS_PATH = "datasets/"
NOTES_PATH = "pages/notes/"

start_time = time.perf_counter()
for dfname in ["discussion_notes_df.csv", "main_pages_df.csv", "revisions_df.csv"]:
    df = pd.read_csv(f"datasets/{dfname}")
    for colname in ["Timestamp", "Last Edited Time"]:
        if colname in df.columns:
            df[colname] = pd.to_datetime(df[colname])
            df[colname] = df[colname] - pd.Timedelta(hours=5) # adjusting for EST timezone
    for colname in ["Content to Formatting Percent","Average Word Length"]:
        if colname in df.columns:
            df[colname] = df[colname].round(3)
    df.to_csv(f"datasets/{dfname}", index=False)
#mediawiki_api_calls.scrapecycle()
# pagesize = mediawiki_api_calls.get_pagesize(310)
# print(mediawiki_api_calls.get_revision_history(123))
# print(pagesize)
# print(mediawiki_api_calls.get_revision_deets(3278), 427) # expected result: 427
#wikitext = mediawiki_api_calls.get_wikitext(3272)
#print(BeautifulSoup(regex_cleaners.deformat_cycle(wikitext),features="html.parser").get_text())

#plaintext = regex_cleaners.deformat_cycle(wikitext)
#print(mediawiki_api_calls.get_revision_wordcount(3303))
# mediawiki_api_calls.purge_folders(NOTES_PATH)
# mediawiki_api_calls.scrape_one_page_new(secret_variables.DISCUSSION_ID,
#                         SCRAPED_FILES_PATH+secret_variables.CAT_TALK_FILENAME,
#                         handle_discussions=True)
# print(regex_cleaners.deformat_links(
#     "[http://www.infinityplus.co.uk/stories/colderwar.htm \"A Colder War\"] by Charles Stross\
#         and Ideas Generated from a Re-Read-NOTES-11141R/W.txt"))
# for filename in os.listdir(SCRAPED_FILES_PATH):
#     if " - " in filename:
#         print(filename)
# filelist = os.listdir("pages/")
# filelist.sort(key=lambda filename: filename[-9:-5])
# print(filelist)
#print(regex_cleaners.deformat_infobox_entity(mediawiki_api_calls.get_wikitext(3248)))
#print(mediawiki_api_calls.get_revision_wordcount(2585))
end_time = time.perf_counter()
# hist = mediawiki_api_calls.get_revision_history(583)
print(f"The code above took {end_time - start_time} seconds to run")
#print(regex_cleaners.deformat_infobox_entity(wikitext))
