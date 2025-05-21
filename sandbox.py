"""
For testing out short snips of code.
"""
import time
import os
import secret_variables
import mediawiki_api_calls
import pandas as pd
import regex_cleaners

SCRAPED_FILES_PATH = "pages/"
DATASETS_PATH = "datasets/"
NOTES_PATH = "pages/notes/"

start_time = time.perf_counter()
# pagesize = mediawiki_api_calls.get_pagesize(310)
# print(mediawiki_api_calls.get_revision_history(310))
# print(pagesize)
# print(mediawiki_api_calls.get_revision_deets(3278), 427) # expected result: 427
#wikitext = mediawiki_api_calls.get_wikitext(3274)
#print(wikitext)
#plaintext = regex_cleaners.deformat_cycle(wikitext)
#print(mediawiki_api_calls.get_revision_wordcount(3303))
mediawiki_api_calls.purge_folders(NOTES_PATH)
mediawiki_api_calls.scrape_one_page_new(secret_variables.DISCUSSION_ID,
                        SCRAPED_FILES_PATH+secret_variables.CAT_TALK_FILENAME,
                        handle_discussions=True)
# print(regex_cleaners.deformat_links(
#     "[http://www.infinityplus.co.uk/stories/colderwar.htm \"A Colder War\"] by Charles Stross\
#         and Ideas Generated from a Re-Read-NOTES-11141R/W.txt"))
# for filename in os.listdir(SCRAPED_FILES_PATH):
#     if " - " in filename:
#         print(filename)
end_time = time.perf_counter()
# hist = mediawiki_api_calls.get_revision_history(583)
print(f"The revision comparison function took {end_time - start_time} seconds to run")
#print(regex_cleaners.deformat_infobox_entity(wikitext))
