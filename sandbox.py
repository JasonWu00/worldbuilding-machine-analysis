"""
For testing out short snips of code.
"""
import secret_variables
import mediawiki_api_calls
import pandas as pd
import regex_cleaners

# pagesize = mediawiki_api_calls.get_pagesize(310)
# print(mediawiki_api_calls.get_revision_history(310))
# print(pagesize)
# print(mediawiki_api_calls.get_revision_deets(3278), 427) # expected result: 427
wikitext = mediawiki_api_calls.get_wikitext(3397)
print(wikitext)
# hist = mediawiki_api_calls.get_revision_history(583)

print(regex_cleaners.deformat_infobox_entity(wikitext))
