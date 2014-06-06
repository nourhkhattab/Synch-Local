import sqlite3
import urllib2
class bDB:
    
    def __init__(self, path):
        self.conn = sqlite3.connect(path)
        self.c = self.conn.cursor()

    def pExist(self, name):
        t = (name,)
        print(name)
        self.c.execute('SELECT PlaylistID FROM CorePlaylists WHERE Name = ? AND PrimarySourceID = 1 LIMIT 1', t)
        r = self.c.fetchall()
        if len(r) != 0:
            return True
        else:
            return False

    def getAllPID(self):
        self.c.execute('SELECT TrackID, Uri FROM CoreTracks WHERE PrimarySourceID = 1')
        ret = []
        for i in self.c.fetchall():
            ret.append((i[0], urllib2.unquote(i[1])[7:]))
        return ret

    def getAllID(self):
        self.c.execute('SELECT TrackID FROM CoreTracks WHERE PrimarySourceID = 1')
        return self.c.fetchall()

    def getID(self, path):
        t = ("file://" + urllib2.quote(path.encode("utf-8")).replace("%26", "&").replace("%21", "!").replace("%28", "(").replace("%29", ")").replace("%2C", ",").replace("%27", "'").replace("%2B", "+").replace("%40", "@").replace("%7E", "~").replace("%24", "$"),)
        self.c.execute('SELECT TrackID FROM CoreTracks WHERE Uri = ?', t)
        try:
            return self.c.fetchall()[0][0]
        except IndexError: 
            return None

    def getPC(self, lid):
        t = (lid,)
        self.c.execute('SELECT PlayCount FROM CoreTracks WHERE TrackID = ?', t)
        return self.c.fetchall()[0][0]

    def getPlists(self):
        self.c.execute('SELECT P.Name, E.TrackID FROM CorePlaylists P, CorePlaylistEntries E WHERE P.PlaylistID = E.PlaylistID AND P.PrimarySourceID = 1')
        return self.c.fetchall()

    def upPlay(self, lid, new):
        t = (new, lid)
        self.c.execute('UPDATE CoreTracks SET PlayCount = ? WHERE TrackID = ?', t)
        self.conn.commit()

    def addPlist(self, name):
        self.c.execute('SELECT MAX(PlaylistID) FROM CorePlaylists')
        cnt = self.c.fetchall()[0][0] + 1
        t = (cnt, name)
        self.c.execute('INSERT INTO CorePlaylists VALUES (1, ?, ?, -1, 0, 0, 0, 0)', t)
        self.conn.commit()

    def addToPlist(self, name, track):
        self.c.execute('SELECT MAX(EntryID) FROM CorePlaylistEntries')
        cnt = self.c.fetchall()[0][0] + 1
        
        t = (name,)
        self.c.execute('SELECT PlaylistID FROM CorePlaylists WHERE Name = ?', t)
        pID = self.c.fetchall()[0][0]

        t = (cnt, pID, track) 
        self.c.execute('INSERT INTO CorePlaylistEntries VALUES (?, ?, ?, 0, 0)', t)
        self.conn.commit()

    def rmPlist(self, name, track):
        t = (name,)
        self.c.execute('SELECT PlaylistID FROM CorePlaylists WHERE Name = ? AND PrimarySourceID = 1', t)
        pid = self.c.fetchall()[0][0]

        t = (pid, track)
        self.c.execute('DELETE FROM CorePlaylistEntries WHERE PlaylistID = ? AND TrackID = ?', t)
        self.conn.commit()

    def close(self):
        self.conn.commit()
        self.conn.close()
        return None
