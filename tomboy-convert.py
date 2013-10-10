from lxml import etree
import json
from dateutil import parser
import time
import random
import os


home = os.path.abspath(os.path.expanduser('~'))
MAC_TOMBOY_FILES = "Library/Application Support/Tomboy/"

TOMBOY_PATH = os.path.join(home, MAC_TOMBOY_FILES)

# for a test:
TOMBOY_FILE = "f272146a-52d1-4f90-a565-2212e405ad27.note"


def generate_random_key():
    """Generate random 30 digit (15 byte) hex string.
    stackoverflow question 2782229
    """
    return '%030x' % (random.randrange(256**15),)


def nvpy_fn():
    # use nvpy's way of creating filenames
    #   from random keys,
    #   ensuring they are unique
    get_fn = lambda: generate_random_key() + ".json"

    ls = os.listdir(os.path.join(home, '.nvpy'))
    nvfn = get_fn()
    while nvfn in ls:
        nvfn = get_fn()
    return nvfn


def dictize(nodes):
    # stuff the tomboy note elements into a dict
    basetag = lambda i: i.split('}')[1]
    d = {}
    
    for n in nodes:
        tag = basetag(n.tag)
        # then it encloses at least a note-content node,
        #  and likely other nodes (such as link, etc).
        if tag == 'text':
            n = n.getchildren()[0]
            b = [(n.text or '')]
            for i in n.iter():
                b.append((i.text or '') + (i.tail or ''))           
            #  --> this does not appear everywhere:
            #      throw away the UUID identifying part of tomboy's content
            # body = n.text.split('\n', 1)[1]
            body = ''.join(b)
        else:
            body = (n.text or '') + (n.tail or '')
        d[tag] = body
    return d

def to_nvpy_note(tb):
    # transfer a tomboy_note to an nvpy_note
    nv = { 'tags': ['tomboy-import'], }
    
    # convert the Tomboy string timestamps to nvpy time.time() form
    timestring_mktime = lambda s: time.mktime(parser.parse(s).timetuple())
    
    # title + content => content
    #  (but throw away the UUID identifying part of tomboy's content)
    nv['content'] = tb['title'] + '\n' + tb['text']
    nv['modifydate'] = timestring_mktime(tb['last-change-date'])
    nv['createdate'] = timestring_mktime(tb['create-date'])
    nv['savedate'] = time.time()  # now
    nv['syncdate'] = 0
    return nv


def convert_file(fn):
        
    with open( TOMBOY_PATH + fn,'r') as f:
        tree = etree.parse(f)
    
    # development time context:
    # print etree.tostring(tree)
    
    # setup:
    node = tree.getroot()
    # the containing node is "note"; we only care about it's children
    # confirm it's a tomboy note
    assert node.tag == '{http://beatniksoftware.com/tomboy}note'
    
    nodes = node.getchildren()
    tomboy_note = dictize(nodes)
    note = to_nvpy_note(tomboy_note)
    with open(nvpy_fn(), "wb") as f:
        json.dump(note, f, indent=2)


def main():
    # test:
    # convert_file(TOMBOY_FILE)
    # --< / test >--
    for fn in os.listdir(TOMBOY_PATH):
        if not fn.endswith('.note'): continue
        convert_file(fn)        

main()