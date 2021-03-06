import xml.etree.ElementTree as ET
import urllib2
from os.path import expanduser
import unicodedata as UCD
home = expanduser("~")

class iTunesDB:

    def __init__(self, path):
        self.tree = ET.parse(path)
        self.root = self.tree.getroot()
        self.playlists = {}
        self.songs = []
        self.tToP = {}
        self.pCount = {}
        self.dictifyP()

    def dictifyS(self):
        for i in self.root.findall('./dict/dict/dict'):
            n = 0
            holder = {}
            meta = [i.text for i in i.findall("./")]
            while n < len(meta):
                holder[meta[n]] = meta[n+1]
                n += 2
            if 'Play Count' not in holder:
                holder['Play Count'] = '0'
            self.songs += [holder]
            self.pCount[holder['Persistent ID']] = int(holder['Play Count'])
            self.tToP[holder['Track ID']] = holder['Persistent ID']
    
    def dictifyP(self):
        self.dictifyS()
        for i in self.root.find('./dict/array'):
            name = i.find('./string').text
            if name in ('Library', 'Music') or i.find('./data') is not None or i.find('./array') is None:
                continue
            slist = []
            for s in i.find('./array'):
                slist += [self.tToP[s.find('./integer').text]]
            self.playlists[name] = slist

    def getPaths(self):
        return [(i.findall('string')[-3].text, home.decode('utf8') + u'/Music' + UCD.normalize('NFC', urllib2.unquote(i.findall('string')[-1].text[29:]).decode('utf8'))) for i in self.root.findall("./dict/dict/dict")]

    def getPC(self, iid):
        return self.pCount[iid]
