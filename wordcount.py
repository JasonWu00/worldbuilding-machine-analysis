"""
MediaWiki does not include a word counter. I am quickly making one of my own.
"""
import os

SCRAPED_FILES_PATH = "pages/"

mastercount = 0

def parsefolder(path):
    count = 0
    for filename in os.listdir(path):
        if ".txt" not in filename:
            count += parsefolder(path+filename+"/")
        else:
            with open(path + filename, 'r', encoding='utf-8') as f:
                texts = f.read().strip().split(" ")
                for text in texts:
                    if text.isalnum():
                        count += 1
    return count

mastercount = parsefolder(SCRAPED_FILES_PATH)
print(mastercount)
