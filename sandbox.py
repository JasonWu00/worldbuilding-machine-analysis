"""
For testing out short snips of code.
"""
import secret_variables
import mediawiki_api_calls
import pandas as pd

pagesize = mediawiki_api_calls.get_pagesize(310)
print(mediawiki_api_calls.get_revision_history(310))
print(pagesize)
print(mediawiki_api_calls.get_revision_deets(3278), 427) # expected result: 427
# hist = mediawiki_api_calls.get_revision_history(583)

# revid_list = []
# for rev in hist:
#     revid = rev["revid"]
#     revid_list.append(revid)

# for revid in revid_list:
#     print(mediawiki_api_calls.get_revision_deets(revid))