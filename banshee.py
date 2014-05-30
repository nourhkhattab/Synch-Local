import sqlite3
import urllib2
from os.path import expanduser
class bDB:
    
    def __init__(self):
        home = expanduser("~")
        self.conn = sqlite3.connect(home + '/.config/banshee-1/banshee.db')
        self.c = self.conn.cursor()

    def getAllPID(self):
        self.c.execute('SELECT TrackID, Uri FROM CoreTracks WHERE PrimarySourceID = 1')
        ret = []
        for i in self.c.fetchall():
            ret.append((i[0], urllib2.unquote(i[1])[7:]))
        return ret

    def getID(self, path):
        t = ("file://" + urllib2.quote(path.encode("utf-8")).replace("%26", "&").replace("%21", "!").replace("%28", "(").replace("%29", ")").replace("%2C", ",").replace("%27", "'").replace("%2B", "+").replace("%40", "@").replace("%7E", "~").replace("%24", "$"),)
        self.c.execute('SELECT TrackID FROM CoreTracks WHERE Uri = ?', t)
        try:
            return self.c.fetchall()[0][0]
        except IndexError: 
            return self.c.fetchall()[0][0]

    def getPC(self, lid):
        t = (lid,)
        self.c.execute('SELECT PlayCount FROM CoreTracks WHERE TrackID = ?', t)
        return self.c.fetchall()[0][0]

    def upPlay(self, lid, new):
        t = (new, lid)
        self.c.execute('UPDATE CoreTracks SET PlayCount = ? WHERE TrackID = ?', t)
        self.conn.commit()

    def close(self):
        self.conn.commit()
        self.conn.close()
        return None
