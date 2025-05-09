"""
This file will make API calls to the MediaWiki API to get all the pages I need.
"""
#import os
import requests
# static variables that lead to where the source material is located at.
from bs4 import BeautifulSoup
from secret_variables import *

API_ENDPOINT = WIKI_URL + "/w/api.php"
SCRAPED_FILES_PATH = "pages/"
NOTES_PATH = "pages/notes/"

replace_keys_dict = {
    '/': '-',
    ':': '-',
    '?': '',
    '\"': '\''
}

def get_pages_by_category(api_endpoint, category):
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
        "User-Agent": USERAGENT
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
    r = requests.get(pagelink, headers={"User-Agent": USERAGENT}, timeout=10)
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
    """
    with open(cat_talk_route, 'r', encoding='utf-8') as f:
        topics = f.read().split("=")
        for topic in topics: #write each topic into separate txtfile
            paragraphs = topic.split('\n\n')
            header = paragraphs[0]
            for replace_key, replacement in replace_keys_dict.items():
                header = header.replace(replace_key, replacement)
            with open(notes_path+header[1:]+".txt", 'w', encoding='utf-8') as f: # skips bad first char
                filestring = "" # write everything to here, then clean up before posting
                for paragraph in paragraphs:
                    filestring += paragraph
                    filestring += '\n\n'
                f.write(filestring.strip())

main_cat_json = get_pages_by_category(API_ENDPOINT, MAIN_CATEGORY)
for page in main_cat_json["query"]["categorymembers"]:
    print(f"id: {page['pageid']}; title: {page['title']}")
    pagelink = WIKI_URL + "/wiki/" + page['title'].replace(' ', '_')
    pagename = page["title"]
    for replace_key, replacement in replace_keys_dict.items():
        #print(replace_key)
        #if replace_key in pagename:
            pagename = pagename.replace(replace_key, replacement)
    scrape_one_page(pagelink, SCRAPED_FILES_PATH+pagename)
#print("scraping the talk page")
scrape_one_page(DISCUSSION_PAGE, SCRAPED_FILES_PATH+CAT_TALK_FILENAME, highlight_sections=True)
parse_discussions(SCRAPED_FILES_PATH+CAT_TALK_FILENAME+".txt", NOTES_PATH)
