from __future__ import print_function
import sys
from collections import defaultdict
import time
import re

try:
    from lxml import etree
except ImportError:
    import xml.etree.ElementTree as etree

import re

def _get_namespace(tag):
    #print(tag)
    namespace = re.match("^{(.*?)}", tag).group(1)
    if not namespace.startswith("http://www.mediawiki.org/xml/export-"):
        raise ValueError("%s not recognized as MediaWiki database dump"
                         % namespace)
    return namespace

def extract_pages(f):
    elems = (elem for _, elem in etree.iterparse(f, events=["end"])) #init iterparse tree

    elem = next(elems)
    namespace = _get_namespace(elem.tag)
    ns_mapping = {"ns": namespace}
    page_tag = "{%(ns)s}page" % ns_mapping
    text_path = "./{%(ns)s}revision/{%(ns)s}text" % ns_mapping
    id_path = "./{%(ns)s}id" % ns_mapping
    title_path = "./{%(ns)s}title" % ns_mapping
    ns_path = "./{%(ns)s}ns" % ns_mapping

    for elem in elems:
        if elem.tag == page_tag:
            if elem.find(ns_path).text != '0':
                continue
            text = elem.find(text_path).text
            if text is None:
                continue
            yield (int(elem.find(id_path).text),
                   elem.find(title_path).text,
                   text)

            elem.clear()
            if hasattr(elem, "getprevious"):
                while elem.getprevious() is not None:
                    del elem.getparent()[0]

def text_process(hashing, text):
    '''Text normalization'''

    text = str(text)
    text = re.sub(r"\{\{(.*?)\}\}"," ",text) #remove infobox
    text = re.sub(r"\[\[(.*?)\]\]"," ",text) #remove links
    text = re.sub(r"(https?:\/\/)?(www\.)?\w+\.\w+"," ",text)
    text = re.sub(r"[^a-zA-Z0-9 \\]"," ",text) #remove special characters except \ 
    text = text.lower() #Convert to lower case

    for word in text.split():
        hashing[word] += 1

if __name__ == "__main__":
    inputfile = sys.argv[1]
    outputfile = sys.argv[2]
    hashing = defaultdict(int)

    start_time = time.time()
    for pageid, title, text in extract_pages(inputfile):
        title = title.encode("utf-8")
        text = text.replace("\n", " ").encode("utf-8")

        full_text = title + text
        text_process(hashing, full_text)
        print("%d\n" % pageid)
    
    f = open(outputfile,'w')
    for key in hashing.keys():
        f.write("%s : %d\n" %(key,hashing[key]))
    finish_time = time.time() - start_time
    print('-- Time: %d(s)\n\n\n'%finish_time)
    f.close()