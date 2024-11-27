"""
This file will make API calls to the MediaWiki API to get all the pages I need.
"""
import os
import requests
# static variables that lead to where the source material is located at.
from secret_variables import *
from bs4 import BeautifulSoup

API_ENDPOINT = WIKI_URL + "/w/api.php"
SCRAPED_FILES_PATH = "pages/"

def get_pages_by_category(api_endpoint, category):
    """
    Fetch all pages based on a given category.
    """
    params = {
        "action": "query",
        "format": "json",
        "list": "categorymembers",
        "cmtitle": category,
        "cmlimit": 60 # 59 pages I have to parse thru
    }
    headers = {
        "User-Agent": USERAGENT
        # Wikipedia requires a user agent string for Python script requests
    }
    response = requests.get(url=api_endpoint, params=params, headers=headers)
    print(response)
    data = response.json()
    return data

def scrape_one_page(pagelink, pagename):
    r = requests.get(pagelink, headers={"User-Agent": USERAGENT})
    soup = BeautifulSoup(r.content, 'html.parser')
    #print(soup)
    #print("="*20)
    all_pars = soup.find_all(['p', 'ul', 'th', 'td', 'h1', 'h3', 'h4', 'h5'])
    
    f = open(pagename+".txt", 'w') # creates file if not exists, otherwise opens with overwite
    start_writing = False
    for para in all_pars:
        if para.find(['th', 'td', 'ul']) is None and para.find_parent(['ul', 'tr']) is None: # no subtables or sublists
            paratext = para.get_text().strip()
            if "Create account" in paratext or "Personal tools" in paratext: break
            if paratext is not None:
                #print(paratext)
                if start_writing: f.write('\n\n')
                f.write(paratext)
                start_writing = True
        #if para.find(['li']) is not None: # tere is a sublist; don't print it
            #print(para.decompose().get_text().strip())
    f.close()

main_cat_json = get_pages_by_category(API_ENDPOINT, MAIN_CATEGORY)
for page in main_cat_json["query"]["categorymembers"]:
    print(f"id: {page['pageid']}; title: {page['title']}")
    pagelink = WIKI_URL + "/wiki/" + page['title'].replace(' ', '_')
    pagename = SCRAPED_FILES_PATH+page["title"].replace('/', '-')
    scrape_one_page(pagelink, pagename)