"""
Contains functions that de-formats wikitext using RegEx.
"""

RESEARCH_CITATIONS = """
https://community.splunk.com/t5/Splunk-Search/Regex-that-matches-all-characters-including-newline/m-p/659011
on the usage of (?s)

https://stackoverflow.com/questions/2503413/regular-expression-to-stop-at-first-match
on the usage of non-greedy (.*?)
"""
import re

def deformat_quotes(wikitext: str) -> str:
    """
    Given a block of wikitext containing a quote object: strip away the formatting
    and return the text with the quoted text and source as plain text.

    ## Parameters
    wikitext: a block of text with MediaWiki formatting, containing one or more quote objects
    ## Returns
    a block of text with raw quote text
    """
    # These regex patterns required a bunch of Stack Overflow dumpster diving to figure out.
    # See the string under the file docstring.
    # I only remembered to save some threads, so others are lost to my forgetfulness.
    noticebox_pattern = r"(?s){{Notice(.*?) \| header =[ ]{0,1}(.*?)\n \| text = (.*?)\n}}"
    quotes_pattern = r"(?s){{Quote(.*?)\| quote =[\n]{0,1}(.*?)\n \| speaker = (.*?)\n \| source =\n}}"
    newtext = wikitext
    patterns_replacements = {
        quotes_pattern: r"QUOTE\n\2\n- \3",
        noticebox_pattern: r"\2\n\3",
    }
    for pattern, replacement in patterns_replacements.items():
        if re.search(pattern, newtext):
            newtext = re.sub(pattern, replacement, newtext)

def deformat_links(wikitext: str) -> str:
    """
    Given a block of wikitext containing links of various forms: strip away their formatting
    and return the text with the link embed phrase(s) instead of the links themselves.

    ## Parameters
    wikitext: a block of text with MediaWiki formatting, containing one or more links
    ## Returns
    a block of text with the link embed text in place of the links.
    """
    external_link_pattern = r"\[https://[0-9a-zA-Z#:/._\'\-\u2020]* ([0-9a-zA-Z:/._ \'\-\u2020]{1,})\]"
    internal_link_pattern = r"\[\[([0-9a-zA-Z# ]*)\]\]"
    internal_link_displaytext_pattern = r"\[\[[0-9a-zA-Z# ]*\|([0-9a-zA-Z ]{1,})\]\]"
    categories_link_pattern = r"\[\[Category:[a-zA-Z0-9 /]*\]\]"
    file_link_pattern = r"\[\[File:[0-9a-zA-Z .|]*\]\]"

    newtext = wikitext

    for regex_pattern in [external_link_pattern, internal_link_pattern,
                          internal_link_displaytext_pattern]:
        # Find each type of link, then replace them with the raw text within
        if re.search(regex_pattern, newtext): # only if such a link exists in the text
            newtext = re.sub(regex_pattern, r"\1", newtext)

    # delete category and file links altogether
    for regex_pattern in [categories_link_pattern, file_link_pattern]:
        if re.search(regex_pattern, newtext):
            newtext = re.sub(regex_pattern, "", newtext)
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
    xib_param_pattern = r"(?s)(data|header|label|ddata1|ddata2) =[ ]{0,1}(.*?)( \||}})"
    #mypattern2 = r"{{xib_param[=a-zA-Z 0-9\n'<br>\|&;:,]*}}"
    infobox_pattern = r"(?s){{Infobox entity\n(.*?)}}\n}}"

    # each Infobox contains a number of smaller xib_param boxes
    # this pulls the raw data from each and every such box
    datablocks = re.findall(xib_param_pattern, wikitext)

    # their presence signifies that a given raw data entry does not display to the wiki
    # and thus should not be returned
    badlist = ["test", "placeholder", ""]

    rawdata = ""
    for pair in datablocks:
        #print(pair)
        if len(pair) == 3 and pair[1].strip("\n") not in badlist:
            rawdata += pair[1].strip("\n")
            rawdata += "\n\n"

    #rawdata = rawdata[:-2]

    #for thing in output:
        #print(thing)
    newtext = re.sub(infobox_pattern, rawdata, wikitext)

    return newtext
