"""
This file uses the mediawiki_api_calls.py functions to
produce a set of pandas DataFrames that can then be used for analysis elsewhere.

Author notes
Errors encountered while running the revision data scraper functions:

Error set 1:
socket.gaierror: [Errno -3] Temporary failure in name resolution    
urllib3.exceptions.NameResolutionError: <urllib3.connection.HTTPSConnection object at
0x7f9fef397a30>: Failed to resolve '[WEBSITE LINK]'
([Errno -3] Temporary failure in name resolution)   
urllib3.exceptions.MaxRetryError: HTTPSConnectionPool(host='[WEBSITE LINK]', port=443):
Max retries exceeded with url:
/w/api.php?action=compare&format=json&fromrev=2884&torelative=prev&prop=ids
(caused by prev error)     
requests.exceptions.ConnectionError: HTTPSConnectionPool(host='[WEBSITE LINK]', port=443):
Max retries exceeded with url:
/w/api.php?action=compare&format=json&fromrev=2884&torelative=prev&prop=ids
(caused by urllib3 error)

This seems to be an issue with the DNS or another component of the WiFi, according
to a quick search. That is beyond the scope of this code.

Error set 2:
jsondecodeerror: expecting value: line 1 column 1 (char 0) (points to a data=response.json() line)

This seems to be caused by the API request returning absolutely nothing, which once again seems
to be a connection issue since it only rarely occurs (despite me using the same parameters every
time) and to different page or revision IDs.
"""
# import os
# import re
# import json
# import requests
import pandas as pd
# static variables that lead to where the source material is located at.
# from bs4 import BeautifulSoup
# from typing import Tuple, List
import secret_variables
import mediawiki_api_calls
import pandas_df_funcs

API_ENDPOINT = secret_variables.WIKI_URL + "/w/api.php"
SCRAPED_FILES_PATH = "pages/"
DATASETS_PATH = "datasets/"
NOTES_PATH = "pages/notes/"
NOTES_DATE_FINDER_REGEX = r"[0-9]{4} EST, [0-9]{2} [a-zA-Z]* [0-9]{4}"
ROUNDING_PRECISION = 3

pageids = mediawiki_api_calls.getallpageids()
pageids.sort()
def produce_mainpages_df():
    """
    Placeholder
    """
    altcats = []
    pagenames = []
    for pageid in pageids:
        altcat = mediawiki_api_calls.get_categories(pageid)
        altcats.append(pandas_df_funcs.altcat_cleanup(altcat))
        title = mediawiki_api_calls.get_pageinfo(pageid)["title"]
        pagenames.append(pandas_df_funcs.pagename_cleanup(title))

    # print("pageids:")
    # print(pageids)
    # print("secondary categories for said pages:")
    # print(altcats)

    wordc, bytec, cfp, wordlen = [], [], [], []
    for pageid in pageids:
        #print(pageid)
        w, b, c, l = pandas_df_funcs.wordbytescount(pageid)
        wordc.append(w)
        bytec.append(b)
        cfp.append(c * 100)
        wordlen.append(l)
    customnotetypes = ["Placeholder"] * len(pageids)
    pages_df = pd.DataFrame({"Page ID": pageids,
                            "Page Name": pagenames,
                            "Other Category": altcats,
                            "Word Count": wordc,
                            "Page Size (Bytes)": bytec,
                            "Content to Formatting Percent": cfp,
                            "Average Word Length": wordlen,
                            "Author-denoted Categories": customnotetypes,
                            #"Is Discussion Note": [False] * len(pageids)
                            })
    for colname in ["Content to Formatting Percent", "Average Word Length"]:
        pages_df[colname] = pages_df[colname].round(ROUNDING_PRECISION)
    pages_df["Last Edited Time"] = pages_df["Page ID"].apply(lambda pageid:
                                                    pd.to_datetime(mediawiki_api_calls
                                                                    .get_page_lastedit(pageid))
                                                                    .tz_convert(None)
                                                                    )

    pages_df["Last Edited Time"] = pd.to_datetime(pages_df["Last Edited Time"])
    pages_df["Last Edited Time"] = pages_df["Last Edited Time"] - pd.Timedelta(hours=5)
    pages_df["Is Discussion Notes"] = pages_df["Page Name"].apply(lambda pagename:
                                                                  "Userpage" in pagename
                                                                  or "Category talk" in pagename)
    # manually set some categories
    for special_ids in [secret_variables.DISCUSSION_ID, secret_variables.USERPAGE_ID]:
        pages_df.loc[pages_df["Page ID"] == special_ids, "Other Category"] = "Documentation"
    pages_df.drop("Page Name").to_csv(DATASETS_PATH+"main_pages_df.csv", index=False)

def produce_notes_df():
    """
    Placeholder
    """
    notesids = []
    notenames = []
    for filename in pandas_df_funcs.noteslist:
        notesid = int(filename[-9:-5])
        notename = filename[:-16]
        # avoid duplicate entries with a check, unless list is empty
        if not notesids or notesid != notesids[-1]:
            notesids.append(int(filename[-9:-5]))
        if not notenames or notename != notenames[-1]:
            notenames.append(notename)
    #print(notesids)
    notetypes = ["Discussion Notes"] * len(notesids)
    customnotetypes = ["Placeholder"] * len(notesids)

    # regex pulling datetimes for the notes
    notesdts = []
    noteswordcounts = []
    notesbytescounts = []
    notescfp = []
    noteswordlen = []
    for notesid in notesids:
        notesdts.append(pandas_df_funcs.get_note_dt(notesid))
        w, b, c, l = pandas_df_funcs.wordbytescount(notesid, isnotes=True)
        noteswordcounts.append(w)
        notesbytescounts.append(b)
        notescfp.append(c * 100)
        noteswordlen.append(l)

    notes_df = pd.DataFrame({"Page ID": notesids,
                            #"Page Name": notenames,
                            "Other Categories": notetypes,
                            "Word Count": noteswordcounts,
                            "Page Size (Bytes)": notesbytescounts,
                            "Average Word Length": noteswordlen,
                            "Content to Formatting Percent": notescfp,
                            "Last Edited Time": notesdts,
                            "Author-denoted Categories": customnotetypes,
                            "Is Discussion Notes": [True] * len(notesids)
                            })
    for colname in ["Content to Formatting Percent", "Average Word Length"]:
        notes_df[colname] = notes_df[colname].round(ROUNDING_PRECISION)
    notes_df["Last Edited Time"] = pd.to_datetime(notes_df["Last Edited Time"])
    notes_df["Last Edited Time"] = notes_df["Last Edited Time"] - pd.Timedelta(hours=5)
    notes_df.to_csv(DATASETS_PATH+"discussion_notes_df.csv", index=False)

#print(mediawiki_api_calls.get_revision_history(583))

def produce_revs_df():
    """
    This function takes a long time to run (in the range of tens of minutes).
    This is due to the function calling on the API endpoints once per page
    and once per revision per page. This is further affected by Internet speed
    which may influence how long it takes to get an API response. Finally this
    function also pulls the full revision version text at each revision, further
    slowing the process. However, I don't have any better ways to pull the revision
    word differences.

    Last ran at around 11:30pm 21 May; fixed a bug with get_revision_wordcount since then
    so this will have to be rerun as soon as is reasonable

    Revisions:
    - Revision page ID
    - Page ID
    - Timestamp
    - is marked as "minor" or not
    - Size of revision (bytes)
    - Size of revision (words)
    """
    revid_list = []
    minor_list = []
    for pageid in pageids + [secret_variables.DISCUSSION_ID, secret_variables.USERPAGE_ID]:
        hist = mediawiki_api_calls.get_revision_history(pageid)
        for rev in hist:
            revid_list.append(rev["revid"]) #"revision id"
            minor_list.append(rev["minor"])
    #print(revid_list)
    pageid_list = []
    timestamps = []
    revbytesizes = []
    revwordsizes = []
    for revid in revid_list:
        rev_deets = mediawiki_api_calls.get_revision_deets(revid)
        pageid_list.append(rev_deets["toid"])
        # timestamp raw looks like: 2025-04-13T05:14:42Z
        timestamps.append(pd.to_datetime(rev_deets["totimestamp"]).tz_convert(None))
        worddiff = mediawiki_api_calls.get_revision_wordcount(revid)
        revwordsizes.append(worddiff)
        revbytesizes.append(rev_deets["tosize"]-rev_deets["fromsize"]
                            if "fromsize" in rev_deets
                            else rev_deets["tosize"])

    revs_df = pd.DataFrame({
        "Revision ID": revid_list,
        "Page ID": pageid_list,
        "Timestamp": timestamps,
        "Is Minor": minor_list,
        "Revision Size (Bytes)": revbytesizes,
        "Revision Size (Words)": revwordsizes,
    })
    revs_df["Timestamp"] = pd.to_datetime(revs_df["Timestamp"])
    revs_df["Timestamp"] = revs_df["Timestamp"] - pd.Timedelta(hours=5)
    revs_df.to_csv(DATASETS_PATH+"revisions_df.csv", index=False)

def update_revs_df():
    """
    Only API query the updates not in the df.

    I will have this as a separate func for now. I will update create_rvs_df
    when I have the time.
    """
    df = pd.read_csv("datasets/revisions_df.csv", parse_dates=["Timestamp"])
    revid_list = []
    minor_list = []
    existing_revids = df["Revision ID"].unique()
    for revision in mediawiki_api_calls.get_recent_revisions():
        # work I did outside certain categories no longer count
        if revision["revid"] not in existing_revids and revision["pageid"] in pageids:
            revid_list.append(revision["revid"])
            minor_list.append("minor" in revision)
    pageid_list = []
    timestamps = []
    revbytesizes = []
    revwordsizes = []
    for revid in revid_list:
        rev_deets = mediawiki_api_calls.get_revision_deets(revid)
        pageid_list.append(rev_deets["toid"])
        # timestamp raw looks like: 2025-04-13T05:14:42Z
        timestamps.append(pd.to_datetime(rev_deets["totimestamp"]).tz_convert(None))
        worddiff = mediawiki_api_calls.get_revision_wordcount(revid)
        revwordsizes.append(worddiff)
        revbytesizes.append(rev_deets["tosize"]-rev_deets["fromsize"]
                            if "fromsize" in rev_deets
                            else rev_deets["tosize"])
    revs_df = pd.DataFrame({
        "Revision ID": revid_list,
        "Page ID": pageid_list,
        "Timestamp": timestamps,
        "Is Minor": minor_list,
        "Revision Size (Bytes)": revbytesizes,
        "Revision Size (Words)": revwordsizes,
    })
    revs_df["Timestamp"] = pd.to_datetime(revs_df["Timestamp"])
    revs_df["Timestamp"] = revs_df["Timestamp"] - pd.Timedelta(hours=5)
    #revs_df.to_csv("datasets/new_revs_df.csv", index=False)
    df = pd.concat([df, revs_df])
    df.to_csv(DATASETS_PATH+"revisions_df.csv", index=False)

def main():
    """
    Main function.
    """
    # mediawiki_api_calls.scrapecycle()
    produce_mainpages_df()
    produce_notes_df()
    # produce_revs_df()
    # update_revs_df()
    # pandas_df_funcs.compile_single_excel()

if __name__ == "__main__":
    main()
