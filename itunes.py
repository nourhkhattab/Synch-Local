import xml.etree.ElementTree as ET
import urllib2
from os.path import expanduser
import unicodedata as UCD
home = expanduser("~")

class iTunesDB:

    def __init__(self, path):
        self.tree = ET.parse(path)
        self.root = self.tree.getroot()

    def getPaths(self):
        return [(i.findall('string')[-3].text, home.decode('utf8') + u'/Music' + UCD.normalize('NFC', urllib2.unquote(i.findall('string')[-1].text[29:]).decode('utf8'))) for i in self.root.findall("./dict/dict/dict")]

    def getPC(self, iid):
        for i in self.root.findall("./dict/dict/dict"):
            l = [e.text for e in i.findall("./")]
            if iid in l:
                try:
                    return int([e.text for e in i.findall("./")][[e.text for e in i.findall("./")].index('Play Count')+1])
                except ValueError:
                    return 0
        return False
