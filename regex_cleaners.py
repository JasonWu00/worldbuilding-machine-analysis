"""
Contains functions that de-formats wikitext using RegEx.
"""
import re
from bs4 import BeautifulSoup
#import pandas as pd

RESEARCH_CITATIONS = """
https://community.splunk.com/t5/Splunk-Search/Regex-that-matches-all-characters-including-newline/m-p/659011
on the usage of (?s)

https://stackoverflow.com/questions/2503413/regular-expression-to-stop-at-first-match
on the usage of non-greedy (.*?)
"""

def deformat_cycle(wikitext: str) -> str:
    """
    runs all the other deformats sequentially.
    """
    newtext = wikitext
    for deformat in [deformat_infobox_entity, deformat_wikitable, deformat_quotes,
                      deformat_links, deformat_misc]:
        newtext = deformat(newtext)
        #print(newtext)
        #print("\n"*3)
    return BeautifulSoup(newtext,features="html.parser").get_text()

def deformat_misc(wikitext: str) -> str:
    """
    Removes various minor wikitext formatting artifacts not covered by the other functions.

    ## Parameters
    wikitext: a block of text with MediaWiki formatting elements not cleaned up by the other funcs
    ## Returns
    a block of text that roughly approaches "plain text".
    """
    newtext = wikitext
    elements_list = ["\'\'\'", "\'\'", "----"]
    regex_replacement_dict = {
        r"[=]{3,5}(.*?)[=]{3,5}": r"\1", # turns === test === to test
        r"<br>": " ",
        r"----\n<br>\n----": "=",
        r"<hr>": "----",
        r"<div (.*?) data-expandtext=\"(.*?)\">": r"Collapsible Section: \2",
    }
    for element in elements_list:
        newtext = newtext.replace(element, "")
    for pattern, replacement in regex_replacement_dict.items():
        if re.search(pattern, newtext):
            newtext = re.sub(pattern, replacement, newtext)
    return newtext


def deformat_wikitable(wikitext: str) -> str:
    """
    Given a block of text containing one or more wikitable objects: strip formatting
    and return the text with the table contents laid out in raw format.

    ## Parameters
    wikitext: a block of text with MediaWiki formatting, containing one or more quote objects
    ## Returns
    a block of text with raw table contents
    """
    newtext = wikitext
    wikitable_pattern = r"(?s){\| class=\"wikitable( sortable){0,1}\"(.*?)\|}"
    wikitable_rowheader_pattern = r"[^ ]([!|] .*?)[\n]"
    wikitable_title_pattern = r"\|\+ (.*?)\n\|"
    while re.search(wikitable_pattern, newtext):
        start, end = re.search(wikitable_pattern, newtext).span()
        snip = newtext[start:end]

        rowsheads = re.findall(wikitable_rowheader_pattern, snip)
        title = re.findall(wikitable_title_pattern, snip)
        #print(rowsheads)

        rawdata = ""
        if title:
            rawdata += title[0].strip(" ")
            rawdata += "\n"
        for rowhead in rowsheads:
            #print(row)
            if "wikitable" not in rowhead:
                #print(x.strip(" ") for x in row.split(" || "))
                rawdata += rowhead.strip(" ")
                rawdata += "\n"

        newtext = re.sub(wikitable_pattern, rawdata, newtext, count=1)
    return newtext

def deformat_quotes(wikitext: str) -> str:
    """
    Given a block of wikitext containing a quote object: strip away the formatting
    and return the text with the quoted text and source as plain text. Also works
    on notice boxes.

    ## Parameters
    wikitext: a block of text with MediaWiki formatting, containing one or more quote objects
    ## Returns
    a block of text with raw quote text
    """
    # These regex patterns required a bunch of Stack Overflow dumpster diving to figure out.
    # See the string under the file docstring.
    # I only remembered to save some threads, so others are lost to my forgetfulness.
    noticebox_pattern = r"(?s){{Notice(.*?) \| header =[\n]{0,1}(.*?)\n \| text = (.*?)[\n]{0,1}}}"
    quotes_pattern = r"(?s){{Quote(.*?)\| quote =[ \n]{0,1}(.*?)\n \| speaker = (.*?)\n \| source =[ ]{0,1}\n}}"
    newtext = wikitext
    patterns_replacements = {
        quotes_pattern: r"\2\n\3\n\n",
        noticebox_pattern: r"\2\n\3\n\n",
    }
    for pattern, replacement in patterns_replacements.items():
        #print(pattern, replacement)
        while re.search(pattern, newtext):
            #print("Found a noticebox or quote")
            #print(re.search(pattern, newtext))
            newtext = re.sub(pattern, replacement, newtext, count=1)
    return newtext

def deformat_links(wikitext: str) -> str:
    """
    Given a block of wikitext containing links of various forms: strip away their formatting
    and return the text with the link embed phrase(s) instead of the links themselves.

    ## Parameters
    wikitext: a block of text with MediaWiki formatting, containing one or more links
    ## Returns
    a block of text with the link embed text in place of the links.
    """
    external_link_pattern = r"\[http[s]{0,1}:.*? (.{1,}?)\]"
    internal_link_pattern = r"\[\[([^:|]*?)\]\]"
    internal_link_displaytext_pattern = r"\[\[.*?\|(.*?)\]\]"
    categories_link_pattern = r"\[\[Category:.*?\]\]"
    file_link_pattern = r"\[\[File:(.*?)\]\]"

    newtext = wikitext
    # delete category and file links altogether
    for regex_pattern in [categories_link_pattern, file_link_pattern]:
        while re.search(regex_pattern, newtext):
            newtext = re.sub(regex_pattern, "", newtext, count=1)

    for regex_pattern in [external_link_pattern, internal_link_pattern,
                          internal_link_displaytext_pattern]:
        # Find each type of link, then replace them with the raw text within
        #print(regex_pattern)
        while re.search(regex_pattern, newtext): # only if such a link exists in the text
            newtext = re.sub(regex_pattern, r"\1", newtext, count=1)

    return newtext

def deformat_infobox_entity(wikitext: str) -> str:
    """
    Given a block of wikitext containing an Infobox entity: strip away the formatting
    and return the text with the Infobox replaced by its raw data.
    
    ## Parameters
    wikitext: a block of text with MediaWiki formatting, containing an Infobox.
    ## Returns
    a block of text with the Infobox replace with raw data.
    """
    newtext = wikitext
    badlist = ["test", "placeholder", ""]
    xib_param_pattern = r"(?s)(data|header|label|ddata1|ddata2) =[ ]{0,1}(.*?)( \||}})"
    #mypattern2 = r"{{xib_param[=a-zA-Z 0-9\n'<br>\|&;:,]*}}"
    infobox_pattern = r"(?s){{Infobox entity\n(.*?)}}\n}}"

    # each Infobox contains a number of smaller xib_param boxes
    # this pulls the raw data from each and every such box
    # one at a time so as to not cross contaminate
    while re.search(infobox_pattern, newtext):
        start, end = re.search(infobox_pattern, newtext).span()
        snip = newtext[start:end]

        xibs = re.findall(xib_param_pattern, snip)
        #print(rowsheads)

        rawdata = ""
        for xib in xibs:
            #print(row)
            if len(xib) >= 2 and xib[1] not in ["", "\n"] and xib[1].strip("\n") not in badlist:
                rawdata += xib[1].strip("\n")
                rawdata += "\n\n"

        newtext = re.sub(infobox_pattern, rawdata, newtext, count=1)
    return newtext
