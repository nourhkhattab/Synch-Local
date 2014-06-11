import sqlite3

class managerDB:

    def __init__(self, path, home, mFolder):
        self.conn = sqlite3.connect(path)
        self.home = home
        self.mFolder = mFolder
        self.c = self.conn.cursor()
        

    def getGID(self, path):
        t = (path[len(self.home) + len(self.mFolder) + 1:],) # Because Google Music works with a relative path
        self.c.execute('SELECT ServerId FROM XFILES WHERE FileHandle = ?', t)
        r = self.c.fetchall()
        return r

    def updateMeta(self, gid, field, change):
        t = (change, gid)
        self.c.execute('UPDATE XFILES SET '+ field + ' = ? WHERE ServerId = ?', t)
        self.conn.commit()
    
    def getMeta(self, gid):
        t = (gid,)
        self.c.execute('SELECT MusicName, MusicAlbum, MusicArtist, MusicAlbumArtist, MusicComposer, MusicGenre, MusicYear, MusicTrackCount, MusicTrackNumber, MusicDiscCount, MusicDiscNumber FROM XFILES WHERE ServerId = ?', t)
        return self.c.fetchall()

    def getAllMeta(self):
        self.c.execute('SELECT ServerId, MusicName, MusicAlbum, MusicArtist, MusicAlbumArtist, MusicComposer, MusicGenre, MusicTrackNumber, MusicTrackCount, MusicDiscNumber, MusicDiscCount FROM XFILES WHERE IsFolder = 0', )
        return self.c.fetchall()

    def setMeta(self, gid, field, change):
        t = (change, gid)
        self.c.execute('UPDATE XFILES SET ' + field + ' = ? WHERE ServerId = ?', t)
        self.conn.commit()

    def close(self):
        self.conn.commit()
        self.conn.close()
        return None

