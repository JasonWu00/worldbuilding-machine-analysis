"""
This file will make API calls to the MediaWiki API to 
"""

import requests
from secret_variables import *

API_ENDPOINT = WIKI_URL + "/w/api.php"

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

main_cat_json = get_pages_by_category(API_ENDPOINT, MAIN_CATEGORY)
for page in main_cat_json["query"]["categorymembers"]:
    print(f"id: {page['pageid']}; title: {page['title']}")