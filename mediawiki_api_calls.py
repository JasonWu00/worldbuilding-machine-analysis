"""
This file contains functions for API calls to the MediaWiki API, using hidden variables for
obfuscation.

Some variables from secret_variables are obfuscated because I am not yet ready
to be revealing to absolutely everyone what I have written yet.
"""
import os
import re
#from typing import Tuple, List
#import json
import requests
# static variables that lead to where the source material is located at.
#from bs4 import BeautifulSoup
import secret_variables
import regex_cleaners

API_ENDPOINT = secret_variables.WIKI_URL + "/w/api.php"
SCRAPED_FILES_PATH = "pages/"
DATASETS_PATH = "datasets/"
NOTES_PATH = "pages/notes/"
NOTES_IDS_START = 999
TIMEOUT_LIMIT = None
# I can afford to wait a minute to get past a connection crater
# though I probably should not make the limit forever; maybe a big number like 120 seconds

replace_keys_dict = {
    '/': '-',
    ':': ' - ',
    '?': '',
    '\"': '\''
}

def get_pages_by_category(api_endpoint: str, category: str):
    """
    Fetch all pages based on a given category.

    ## Parameters
    api_endpoint: an API endpoint; see the name.    
    category: a MediaWiki category to search through.
    ## Returns
    a raw JSON of all pages in the given category (see the raw docstring for formatting):    
    {    
        batchcomplete: ""    
        query: {    
            categorymembers: [    
                {    
                    pageid: int,    
                    ns: 0,    
                    title: pagename,    
                }    
                (repeat for other pages)    
            ]     
        }    
    }
    """
    params = {
        "action": "query",
        "format": "json",
        "list": "categorymembers",
        "cmtitle": category,
        "cmlimit": 100 # number to be increased in the future if I get that many files
    }
    headers = {
        "User-Agent": secret_variables.USERAGENT
        # Wikipedia requires a user agent string for Python script requests
    }
    response = requests.get(url=api_endpoint, params=params, headers=headers, timeout=TIMEOUT_LIMIT)
    print(response)
    data = response.json()
    return data

def scrape_one_page_new(pageid: int, pagename: str, handle_discussions=False):
    """
    API queries a MediaWiki page. Both its formatted and raw forms will be saved.

    ## Parameters:
    pagelink: a URL to a given MediaWiki page.    
    pagename: path + name for the local .txt file.    
    highlight_sections: default False; marks topic sections in the category discussions\
    page by separating them with a special character that does not appear in main text bodies.
    ## Returns
    Not returned but rather generated: two .txt file at the indicated path with the indicated
    names, denoted as "wikitext" or "raw".
    """
    print(f"Getting wikitext for pageid {pageid}")
    wikitext = get_wikitext_current(pageid)

    with open(pagename+"-"+f"{pageid}W"+".txt", 'w', encoding='utf-8') as f:
        f.write(wikitext)
    rawtext = regex_cleaners.deformat_cycle(wikitext)
    with open(pagename+"-"+f"{pageid}R"+".txt", 'w', encoding='utf-8') as f:
        f.write(rawtext)
    print(f"Wrote page to {pagename}-{pageid}R/W.txt")

    if handle_discussions: # the discussion page calls for special procedures
        topics = re.split(r"----\n<br>\n----", wikitext) # all topics are separated by this
        topics_counter = NOTES_IDS_START
        for topic in topics: #write each topic into separate txtfile
            #print(topic)
            if topics_counter != NOTES_IDS_START: # skip the first topic; contains junk
                header = re.search(r"===[ ]{0,1}(.*?)[ ]{0,1}===", topic).group(1)
                header = regex_cleaners.deformat_links(header)
                for replace_key, replacement in replace_keys_dict.items():
                    header = header.replace(replace_key, replacement)
                header = header.replace("  ", " ")
                with open(NOTES_PATH+header+f"-NOTES-{topics_counter:04}W.txt",
                        'w', encoding='utf-8') as n:
                    n.write(topic) # this is for the raw wikitext
                with open(NOTES_PATH+header+f"-NOTES-{topics_counter:04}R.txt",
                        'w', encoding='utf-8') as n:
                    n.write(regex_cleaners.deformat_cycle(topic)) # rawtext
                print(f"Wrote notes to {NOTES_PATH+header}-NOTES-1{topics_counter:04}R/W.txt")
            topics_counter+=1

def purge_folders(path, recursive=False):
    """
    Deletes every text file previously generated. Meant to be used immediately before scraping
    additional pages to delete text files for pages or topics that no longer exist.

    Sometimes I remove topics and pages from the webpages I scrape. Without this function,
    old pages and discussion topics get left behind in the folders. They interfere in
    accurate analysis and previously had to be manually deleted. I don't feel like checking
    which ones need to be deleted every time so here's the blanket option.

    ## Parameters
    path: local file path to all generated .txt files.    
    recursive: default False; determines if the function will also purge subfolders.
    ## Returns
    none.
    """
    for filename in os.listdir(path):
        filepath = os.path.join(path, filename)
        if ".txt" in filepath and os.path.isfile(filepath):
            os.remove(filepath)
        elif recursive and os.path.isdir(filepath):
            purge_folders(filepath)

def scrapecycle():
    """
    Carries out a "web scrape cycle".
    - Delete existing .txt files
    - Get via API call all pages belonging the obfuscated main category
    - Run the scrape_one_page() function on each page to pull their formatted text data
    and store it in a text file at the given directory
    - Run a special set of instructions to scrape then parse a long discussions page that
    requires its own procedure.

    ## Parameters
    None.
    ## Returns
    A number of .txt files in the /notes folder, which is also kept hidden for now.
    Text files names take the format pagename-pageid.txt, with pageid taking up 4 chars.
    """
    purge_folders(SCRAPED_FILES_PATH, recursive=True)
    main_cat_json = get_pages_by_category(API_ENDPOINT, secret_variables.MAIN_CATEGORY)
    #print(main_cat_json)
    for page in main_cat_json["query"]["categorymembers"]:
        #print(f"id: {page['pageid']}; title: {page['title']}")
        #pagelink = secret_variables.WIKI_URL + "/wiki/" + page['title'].replace(' ', '_')
        pagename = page["title"]
        pageid = page["pageid"]
        for replace_key, replacement in replace_keys_dict.items():
            #print(replace_key)
            #if replace_key in pagename:
            pagename = pagename.replace(replace_key, replacement)
        scrape_one_page_new(pageid, SCRAPED_FILES_PATH+pagename)
    #print("scraping the talk page")
    scrape_one_page_new(secret_variables.USERPAGE_ID, SCRAPED_FILES_PATH+"Userpage")
    scrape_one_page_new(secret_variables.DISCUSSION_ID,
                        SCRAPED_FILES_PATH+secret_variables.CAT_TALK_FILENAME,
                        handle_discussions=True)
    # scrape_one_page(secret_variables.DISCUSSION_PAGE,
    #                 SCRAPED_FILES_PATH+secret_variables.CAT_TALK_FILENAME,
    #                 highlight_sections=True)
    #parse_discussions(SCRAPED_FILES_PATH+secret_variables.CAT_TALK_FILENAME+".txt", NOTES_PATH)
    #os.remove(SCRAPED_FILES_PATH+secret_variables.CAT_TALK_FILENAME+".txt")

def getallpageids() -> list[int]:
    """
    Gets all page IDs for the main category, as well as the discussion talk page and the 

    ## Parameters
    None.
    ## Returns
    a list of page IDs.
    """
    params = {
            "action": "query",
            "format": "json",
            "list": "categorymembers",
            "cmtitle": secret_variables.MAIN_CATEGORY,
            "cmlimit": 100 # number to be increased in the future if I get that many files
        }
    headers = {
        "User-Agent": secret_variables.USERAGENT
        # Wikipedia requires a user agent string for Python script requests
    }
    response = requests.get(url=API_ENDPOINT, params=params, headers=headers, timeout=TIMEOUT_LIMIT)
    #print(response)
    data = response.json()
    pageids = [x["pageid"] for x in data["query"]["categorymembers"]]
    #print(len(pageids))
    #print(pageids)
    return pageids + [secret_variables.DISCUSSION_ID, secret_variables.USERPAGE_ID]

#pageids = getallpageids()
#print(pageids)

def get_categories(pageid: int):
    """
    Returns the category of a given page.

    I previously attempted to use a generator to pull all pages of a given category to pass
    to the api to get all of their other categories, but it straight up returned nothing.
    I also tried feeding more than 5 pages at once but pages past the 5th or so return
    incorrect data; with pages that clearly have categories claiming to have none.
    I don't know how to fix this so I will leave this as a per-page call to be used
    in a pandas apply() function.

    ## Parameters
    pageid: an ID.
    ## Returns
    A list of categories other than the main hidden category, or [] if no others exist.
    """
    # I have no idea what the upper limit for pages accepted into pageids is
    # so doing it manually
    params = {
        "action": "query",
        "format": "json",
        "prop": "categories",
        "pageids": pageid, # the api does not accept Python lists; needs a bit of engineering
        "cllimit": 5,
        "clshow": "!hidden",
        #"rvlimit": 100, #
    }
    headers = {
        "User-Agent": secret_variables.USERAGENT
        # Wikipedia requires a user agent string for Python script requests
    }
    response = requests.get(url=API_ENDPOINT, params=params, headers=headers, timeout=TIMEOUT_LIMIT)
    #print(response)
    data = response.json()
    # print(pageids)
    #print(json.dumps(data, indent=2))
    pagedata = data["query"]["pages"][str(pageid)]
    print(f"API called category data for page {pageid}")
    if "categories" in pagedata: # some pages, like my user page, have no categories.
        cats = data["query"]["pages"][str(pageid)]["categories"][1:] # bypass junk, get to categories

        # All categories take the form "Category:catname"
        # Drop the useless prefix
        return [cat["title"][9:] for cat in cats]
    return []

# for pageid in pageids:
#     get_categories(pageid)
# print(get_categories(567))

# get detailed data on each page, including revisions.
def get_recent_revisions():
    """
    Get my most recent revisions as of the last 3 or 4 days. This lets me soft-update the datasets
    without rebuilding everything.
    """
    params = {
        "action": "query",
        "format": "json",
        "list": "usercontribs",
        "ucuser": secret_variables.USERNAME,
        #"prop": "revisions",
        #"rvprop": "ids|timestamp|flags|comment|user",
        "ucend": "2025-05-20T00:00:00Z",
        "uclimit": 100,
    }
    headers = {
        "User-Agent": secret_variables.USERAGENT
        # Wikipedia requires a user agent string for Python script requests
    }
    response = requests.get(url=API_ENDPOINT, params=params, headers=headers, timeout=TIMEOUT_LIMIT)
    data = response.json()
    return data["query"]["usercontribs"]

def get_revision_history(pageid: int):
    """
    Given a page ID, return a list of detailed revision data. This includes:
    - Revision ID
    - Timestamp
    - User-provided comment (might or might not be useful)
    - minor: whether this was marked as a minor edit or not

    ## Parameters:
    pageid: an ID.
    ## Output:
    a list of dictionaries each containing a revision ID, timestamp, and comment.
    Revision sizes will be calculated in another function.
    """
    params = {
        "action": "query",
        "format": "json",
        "pageids": f"{pageid}",
        "prop": "revisions",
        "rvprop": "ids|timestamp|flags|comment|user",
        "rvlimit": 100,
        #"cmtitle": secret_variables.MAIN_CATEGORY,
        #"cmlimit": 100 # doesn't work with revisions; only 1 page at a time
    }
    headers = {
        "User-Agent": secret_variables.USERAGENT
        # Wikipedia requires a user agent string for Python script requests
    }
    response = requests.get(url=API_ENDPOINT, params=params, headers=headers, timeout=TIMEOUT_LIMIT)
    data = response.json()
    #print(json.dumps(data, indent=2))
    revisions = data["query"]["pages"][str(pageid)]["revisions"]
    output = []
    for revision in revisions:
        output.append(dict((key, revision[key])
                           for key in ["revid", "timestamp", "comment"]))
        output[-1]["minor"] = "minor" in revision
    print(f"Acquired revision history for page with ID {pageid}")
    return output
    #print("END")

# for rev in get_revision_history(567):
#     print(rev)
# for rev in get_revision_history(429):
#     print(rev)

def get_revision_deets(revid: int):
    """
    Given a revision page ID, returns the "details" for the revision.

    ## Parameters:
    revid: an ID.
    ## Output:
    A json object containing a number of variables.
    """
    params = {
        "action": "compare",
        "format": "json",
        "fromrev": f"{revid}",
        "torelative": "prev",
        "prop": "diffsize|size|ids|title|comment|timestamp",
        #"rvprop": "ids|timestamp|flags|comment|user",
        #"rvlimit": 100,
        #"cmtitle": secret_variables.MAIN_CATEGORY,
        #"cmlimit": 100 # doesn't work with revisions; only 1 page at a time
    }
    headers = {
        "User-Agent": secret_variables.USERAGENT
        # Wikipedia requires a user agent string for Python script requests
    }
    response = requests.get(url=API_ENDPOINT, params=params, headers=headers, timeout=TIMEOUT_LIMIT)
    data = response.json()
    #print(json.dumps(data, indent=2))
    print(f"Returning full comparison details for revision with id {revid}")
    return data["compare"]
    # tosize = data["compare"]["tosize"]
    # if "fromsize" in data["compare"]:
    #     fromsize = data["compare"]["fromsize"]
    # else:
    #     fromsize = 0
    # return [tosize - fromsize, data["compare"]["toid"],]

# print(get_revision_deets(3030), 0) # expected result: 0
# print(get_revision_deets(3029), 6904) # expected result: 6904
# print(get_revision_deets(2630), 4029) # expected result: 4029
# print(get_revision_deets(2311), 6240) # expected result: 6240
# print(get_revision_deets(3278), 427) # expected result: 427

def get_pageinfo(pageid: int):
    """
    Given a page ID, pulls some info not present in other functions.

    ## Parameters:
    pageid: an ID.
    ## Output:
    a json object with some extended info on a given page.
    """
    params = {
        "action": "query",
        "format": "json",
        "pageids": f"{pageid}",
        "prop": "info",
        #"rvprop": "ids|timestamp|flags|comment|user",
        #"rvlimit": 100,
        #"cmtitle": secret_variables.MAIN_CATEGORY,
        #"cmlimit": 100 # doesn't work with revisions; only 1 page at a time
    }
    headers = {
        "User-Agent": secret_variables.USERAGENT
        # Wikipedia requires a user agent string for Python script requests
    }
    response = requests.get(url=API_ENDPOINT, params=params, headers=headers, timeout=TIMEOUT_LIMIT)
    data = response.json()
    #print(json.dumps(data, indent=2))
    print(f"Returning full info for page {pageid}")
    return data["query"]["pages"][str(pageid)]
    # revisions = data["query"]["pages"][str(pageid)]["revisions"]
    # output = []
    # for revision in revisions:
    #     output.append(dict((key, revision[key])
    #                        for key in ["revid", "timestamp", "comment"]))
    #     output[-1]["minor"] = "minor" in revision
    # return output
# https://arboretumfictoria.miraheze.org/w/api.php?action=query&prop=revisions&rvprop=size&titles=2S16%20Earthshaker

def get_pagesize(pageid: int):
    """
    Given a page ID, pulls the page's size in bytes. Can't be bothered to wordcount it.

    ## Parameters:
    pageid: an ID.
    ## Output:
    a json object with the page's size in bytes.
    """
    params = {
        "action": "query",
        "format": "json",
        "pageids": f"{pageid}",
        "prop": "revisions",
        "rvprop": "size",
        #"rvlimit": 100,
        #"cmtitle": secret_variables.MAIN_CATEGORY,
        #"cmlimit": 100 # doesn't work with revisions; only 1 page at a time
    }
    headers = {
        "User-Agent": secret_variables.USERAGENT
        # Wikipedia requires a user agent string for Python script requests
    }
    response = requests.get(url=API_ENDPOINT, params=params, headers=headers, timeout=TIMEOUT_LIMIT)
    data = response.json()
    #print(json.dumps(data, indent=2))
    print(f"Returning page size for page {pageid}")
    return data["query"]["pages"][str(pageid)]["revisions"][0]["size"]

def get_wikitext(revid: int) -> str:
    """
    Returns the formatted wikitext for a given page at a given revision ID.

    ## Parameters
    revid: a revision ID
    ## Returns
    a string containing formatted wikitext, or an empty string if revid = 0.
    """
    if revid == 0:
        return ""
    params = {
        "action": "parse",
        "format": "json",
        "oldid": f"{revid}",
        "prop": "wikitext",
        #"rvprop": "size",
        #"rvlimit": 100,
        #"cmtitle": secret_variables.MAIN_CATEGORY,
        #"cmlimit": 100 # doesn't work with revisions; only 1 page at a time
    }
    headers = {
        "User-Agent": secret_variables.USERAGENT
        # Wikipedia requires a user agent string for Python script requests
    }
    response = requests.get(url=API_ENDPOINT, params=params, headers=headers, timeout=TIMEOUT_LIMIT)
    data = response.json()
    return data["parse"]["wikitext"]["*"]

def get_wikitext_current(pageid: int) -> str:
    """
    get_wikitext except it gets the latest for a given page.
    """
    params = {
        "action": "parse",
        "format": "json",
        "pageid": f"{pageid}",
        "prop": "wikitext",
        #"rvprop": "size",
        #"rvlimit": 100,
        #"cmtitle": secret_variables.MAIN_CATEGORY,
        #"cmlimit": 100 # doesn't work with revisions; only 1 page at a time
    }
    headers = {
        "User-Agent": secret_variables.USERAGENT
        # Wikipedia requires a user agent string for Python script requests
    }
    response = requests.get(url=API_ENDPOINT, params=params, headers=headers, timeout=TIMEOUT_LIMIT)

    # I encountered a bug where the response.json() line failed for some reason
    # jsondecodeerror: expecting value line 1 column 1 (char 0)
    # so here I am trying to catch the response if or when it happens again
    data = response.json()
    return data["parse"]["wikitext"]["*"]

def get_wordcount_file(filename: str):
    """
    Opens a file then runs get_wordcount_text() on its contents.
    """
    with open(filename, 'r', encoding='utf-8') as f:
        return get_wordcount_text(f.read())
def get_wordcount_text(text: str):
    """
    Splits a text into words, then counts how many there are.
    """
    return len(text.strip().split(" "))

def get_revision_wordcount(revid: int):
    """
    Given a revision ID, compares the file at that revision to the previous version.
    Returns length difference (current - prev) measured by words.
    """
    params = {
        "action": "compare",
        "format": "json",
        "fromrev": f"{revid}",
        "torelative": "prev",
        "prop": "ids",
        #"rvprop": "ids|timestamp|flags|comment|user",
        #"rvlimit": 100,
        #"cmtitle": secret_variables.MAIN_CATEGORY,
        #"cmlimit": 100 # doesn't work with revisions; only 1 page at a time
    }
    headers = {
        "User-Agent": secret_variables.USERAGENT
        # Wikipedia requires a user agent string for Python script requests
    }
    response = requests.get(url=API_ENDPOINT, params=params, headers=headers, timeout=TIMEOUT_LIMIT)
    deets = response.json()
    old_rev_id = deets["compare"]["fromrevid"] if "fromrevid" in deets["compare"] else 0

    # Extract wikitext for provided revision ID, then clean text and count words.
    rev_wikitext = get_wikitext(revid)
    old_rev_wikitext = get_wikitext(old_rev_id)
    rev_raw = regex_cleaners.deformat_cycle(rev_wikitext)
    old_rev_raw = regex_cleaners.deformat_cycle(old_rev_wikitext)

    curr_words = get_wordcount_text(rev_raw)
    old_words = get_wordcount_text(old_rev_raw)
    #print(revid, old_rev_id)
    #print(curr_words, old_words)
    worddiff = curr_words - old_words
    #bytediff = len(rev_wikitext) - len(old_rev_wikitext)
    return worddiff
    # insert deformatting functions here

def get_page_lastedit(pageid: int) -> str:
    """
    See function title.
    """
    params = {
        "action": "query",
        "format": "json",
        "pageids": f"{pageid}",
        "prop": "revisions",
        "rvprop": "ids|timestamp|flags|comment|user",
        "rvlimit": 1,
        #"cmtitle": secret_variables.MAIN_CATEGORY,
        #"cmlimit": 100 # doesn't work with revisions; only 1 page at a time
    }
    headers = {
        "User-Agent": secret_variables.USERAGENT
        # Wikipedia requires a user agent string for Python script requests
    }
    response = requests.get(url=API_ENDPOINT, params=params, headers=headers, timeout=TIMEOUT_LIMIT)
    data = response.json()
    ts = data["query"]["pages"][f"{pageid}"]["revisions"][0]["timestamp"]
    return ts

PLANS = """
To Do:
New pipeline
- using the API, pull wikitext for a given page or revision
- deformat the text using regex
- save plaintext and wikitext versions as text files
- reuse this functionality to calculate word changes between revisions

Data to collect at a future date:

Info on each page: GOT
- Page ID (use in place of title for obfuscation)
- Type (tale, fake wikipedia entry, or discussion note)
- (Maybe separate them into two tables?)
- Text count
- Avg word length
- Formatting vs. Actual Text ratios
- Number of edits?

Revisions: GOT
- Revision page ID
- Page ID
- Timestamp
- is marked as "minor" or not
- Size of revision (bytes, words)

ML predicted values (use Hugging Face models? do it in a py notebook?)
- Generalized topic categories (history, science, politics, etc)
- Specialized topic categories (To be determined)
- Sentiments (positive/negative?)

Things to potentially investigate in visualizations
- Distribution of revisions over time
    - Hours of day? Days of week? From start to now?
- Word counts? Length? Categorization?
"""
