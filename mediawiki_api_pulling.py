"""
This file will make API calls to the MediaWiki API, using hidden variables for obfuscation,
to produce a set of pandas DataFrames that can then be used for analysis elsewhere.

Some variables from secret_variables are obfuscated because I am not yet ready
to be revealing to absolutely everyone what I have written yet.
"""
import os
import json
import requests
# static variables that lead to where the source material is located at.
from bs4 import BeautifulSoup
import secret_variables

API_ENDPOINT = secret_variables.WIKI_URL + "/w/api.php"
SCRAPED_FILES_PATH = "pages/"
NOTES_PATH = "pages/notes/"

replace_keys_dict = {
    '/': '-',
    ':': ' -',
    '?': '',
    '\"': '\''
}

def get_pages_by_category(api_endpoint: str, category: str):
    """
    Fetch all pages based on a given category.
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
    response = requests.get(url=api_endpoint, params=params, headers=headers, timeout=10)
    print(response)
    data = response.json()
    return data

def scrape_one_page(pagelink, pagename, highlight_sections=False):
    """
    Grab one MediaWiki page and scrape its text content into a .txt file.
    """
    r = requests.get(pagelink, headers={"User-Agent": secret_variables.USERAGENT}, timeout=10)
    soup = BeautifulSoup(r.content, 'html.parser')
    #print(soup)
    #print("="*20)
    all_pars = soup.find_all(['p', 'ul', 'th', 'td', 'h1', 'h3', 'h4', 'h5', 'pre'])

    with open(pagename+".txt", 'w', encoding='utf-8') as f:
        # creates file if not exists, otherwise opens with overwite
        start_writing = False

        for para in all_pars:
            if para.find(['th', 'td', 'ul']) is None and para.find_parent(['ul', 'td']) is None:
                # no subtables or sublists
                paratext = para.get_text().strip()
                if "Create account" in paratext or "Personal tools" in paratext:
                    break
                if paratext is not None and paratext != "":
                    #print(paratext)
                    if start_writing:
                        f.write('\n\n')
                    if highlight_sections and para.name == "h3":
                        f.write("=\n")
                    f.write(paratext.replace('\n\n', '\n'))
                    start_writing = True
            #if para.find(['li']) is not None: # tere is a sublist; don't print it
                #print(para.decompose().get_text().strip())
        print(f"finished scraping text from page: {pagename}")

def parse_discussions(cat_talk_route, notes_path):
    """
    Parse the category talk page into individual topics.

    The talk page contains a number of topic blocks separated by this formatting:
    ====
    <br>
    ====
    This function divides the raw discussion text using these delimiters.
    """
    with open(cat_talk_route, 'r', encoding='utf-8') as f:
        topics = f.read().split("=")
        for topic in topics: #write each topic into separate txtfile
            paragraphs = topic.split('\n\n')
            header = paragraphs[0]
            for replace_key, replacement in replace_keys_dict.items():
                header = header.replace(replace_key, replacement)
            with open(notes_path+header[1:]+".txt", 'w', encoding='utf-8') as f: # skips first char
                filestring = "" # write everything to here, then clean up before posting
                for paragraph in paragraphs:
                    filestring += paragraph
                    filestring += '\n\n'
                f.write(filestring.strip())

def purge_folders(path, recursive=False):
    """
    Deletes every text file I scraped beforehand so that I can discard discussion topics
    and pages no longer part of the work.

    Sometimes I remove topics and pages from the webpages I scrape. Without this function,
    old pages and discussion topics get left behind in the folders. They interfere in
    accurate analysis and previously had to be manually deleted. I don't feel like checking
    which ones need to be deleted every time so here's the blanket option.
    """
    for filename in os.listdir(path):
        filepath = os.path.join(path, filename)
        try:
            if ".txt" in filepath and os.path.isfile(filepath):
                os.remove(filepath)
            elif recursive and os.path.isdir(filepath):
                purge_folders(filepath)
        except BaseException as e:
            print(f"Failed to purge files in folder {path}: {e}")

def scrapecycle():
    """
    Basically a main() function.
    """
    purge_folders(SCRAPED_FILES_PATH, recursive=True)
    main_cat_json = get_pages_by_category(API_ENDPOINT, secret_variables.MAIN_CATEGORY)
    #print(main_cat_json)
    for page in main_cat_json["query"]["categorymembers"]:
        print(f"id: {page['pageid']}; title: {page['title']}")
        pagelink = secret_variables.WIKI_URL + "/wiki/" + page['title'].replace(' ', '_')
        pagename = page["title"]
        for replace_key, replacement in replace_keys_dict.items():
            #print(replace_key)
            #if replace_key in pagename:
            pagename = pagename.replace(replace_key, replacement)
        scrape_one_page(pagelink, SCRAPED_FILES_PATH+pagename)
    #print("scraping the talk page")
    scrape_one_page(secret_variables.DISCUSSION_PAGE,
                    SCRAPED_FILES_PATH+secret_variables.CAT_TALK_FILENAME,
                    highlight_sections=True)
    parse_discussions(SCRAPED_FILES_PATH+secret_variables.CAT_TALK_FILENAME+".txt", NOTES_PATH)

def getallpageids():
    """
    Gets all page IDs for the secret main category.

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
    response = requests.get(url=API_ENDPOINT, params=params, headers=headers, timeout=10)
    #print(response)
    data = response.json()
    pageids = [x["pageid"] for x in data["query"]["categorymembers"]]
    #print(len(pageids))
    #print(pageids)
    return pageids

pageids = getallpageids()
print(pageids)

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
    response = requests.get(url=API_ENDPOINT, params=params, headers=headers, timeout=10)
    #print(response)
    data = response.json()
    # print(pageids)
    #print(json.dumps(data, indent=2))
    cats = data["query"]["pages"][str(pageid)]["categories"][1:] # bypass junk, get to categories
    output = []
    for cat in cats:
        # All categories take the form "Category:catname"
        # Drop the useless prefix
        output.append(cat["title"][9:])
    return output

# for pageid in pageids:
#     get_categories(pageid)
print(get_categories(567))

# get detailed data on each page, including revisions.
def get_revision_history(pageid: int):
    """
    Given a page ID, return a list of detailed revision data.

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
    response = requests.get(url=API_ENDPOINT, params=params, headers=headers, timeout=10)
    data = response.json()
    #print(json.dumps(data, indent=2))
    revisions = data["query"]["pages"][str(pageid)]["revisions"]
    output = []
    for revision in revisions:
        output.append(dict((key, revision[key])
                           for key in ["revid", "timestamp", "comment"]))
        if "minor" in revision: # this key only sometimes appears thus I must handle it manually
            output[-1]["minor"] = True
        else:
            output[-1]["minor"] = False
    return output
    #print("END")

for rev in get_revision_history(567):
    print(rev)
for rev in get_revision_history(429):
    print(rev)

def get_revision_diffs(revid: int):
    """
    Given a revision page ID, returns the number of bytes added or subtracted compared to prev rev.

    ## Parameters:
    revid: an ID.
    ## Output:
    an integer of the size difference, calculated using the size of the prev and current revisions.
    The diffsize field is misleading so I did not use it.
    """
    params = {
        "action": "compare",
        "format": "json",
        "fromrev": f"{revid}",
        "torelative": "prev",
        "prop": "diffsize|size|ids",
        #"rvprop": "ids|timestamp|flags|comment|user",
        #"rvlimit": 100,
        #"cmtitle": secret_variables.MAIN_CATEGORY,
        #"cmlimit": 100 # doesn't work with revisions; only 1 page at a time
    }
    headers = {
        "User-Agent": secret_variables.USERAGENT
        # Wikipedia requires a user agent string for Python script requests
    }
    response = requests.get(url=API_ENDPOINT, params=params, headers=headers, timeout=10)
    data = response.json()
    print(json.dumps(data, indent=2))
    tosize = data["compare"]["tosize"]
    if "fromsize" in data["compare"]:
        fromsize = data["compare"]["fromsize"]
    else:
        fromsize = 0
    return tosize - fromsize

print(get_revision_diffs(3030), 0) # expected result: 0
print(get_revision_diffs(3029), 6904) # expected result: 6904
print(get_revision_diffs(2630), 4029) # expected result: 4029
print(get_revision_diffs(2311), 6040) # expected result: 6040
print(get_revision_diffs(3278), 427) # expected result: 427

plans = """
Data to collect at a future date:

Info on each page:
- PageID (use in place of title for obfuscation)
- Type (tale, fake wikipedia entry, or discussion note)
- (Maybe separate them into two tables?)
- Text count

Revisions:
- Revision page ID
- Timestamp
- is marked as "minor" or not
- Size of revision
"""
