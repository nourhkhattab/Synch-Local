import sqlite3

class synchDB:

    def __init__(self, path):
        self.conn = sqlite3.connect(path)
        self.c = self.conn.cursor()
        self.c.execute('CREATE TABLE IF NOT EXISTS local (ID INTEGER PRIMARY KEY AUTOINCREMENT, GID TEXT UNIQUE, BID INTEGER UNIQUE, IID INTEGER UNIQUE, Path TEXT NOT NULL UNIQUE, PCount INTEGER DEFAULT 0, IPC INTEGER DEFAULT 0, metUP INTEGER DEFAULT 0)')
        self.c.execute('CREATE TABLE IF NOT EXISTS playlist (Plist TEXT, ID INTEGER, PRIMARY KEY (Plist, ID))')
        self.c.execute('CREATE TABLE IF NOT EXISTS meta (ID INTEGER PRIMARY KEY, Title TEXT NOT NULL, Artist TEXT NOT NULL, AlbumArtist TEXT NOT NULL, Album TEXT NOT NULL, Artwork TEXT, Track INTEGER DEFAULT 0, TTrack INTEGER DEFAULT 0, Disk INTEGER DEFAULT 0, TDisk INTEGER DEFAULT 0)')
        self.c.execute('CREATE TABLE IF NOT EXISTS iUP (UP INTEGER DEFAULT 1)')
        try:
            self.isUp()
        except IndexError: 
            self.c.execute('INSERT INTO iUP VALUES (1)')
        self.conn.commit()

    def isUp(self):
        self.c.execute('SELECT * FROM iUP')
        if self.c.fetchall()[0][0] == 1:
            return True
        return False

    def notUp(self):
        self.c.execute('UPDATE iUP SET UP = 0')
        self.conn.commit()
    
    def addSong(self, path):
        t = (path,)
        self.c.execute('INSERT INTO local (Path) VALUES (?)', t)
        self.conn.commit()
        return self.c.lastrowid

    def addGID(self, lid, gid):
        t = (gid, lid)
        self.c.execute('UPDATE local SET GID = ? WHERE ID = ?', t)
        self.conn.commit()

    def addBID(self, lid, bid):
        t = (bid, lid)
        self.c.execute('UPDATE local SET BID = ? WHERE ID = ?', t)
        self.conn.commit()

    def addIID(self, lid, iid):
        t = (iid, lid)
        self.c.execute('UPDATE local SET IID = ? WHERE ID = ?', t)
        self.conn.commit()
    
    def upPlay(self, lid, new):
        t = (new, lid)
        self.c.execute('UPDATE local SET PCount = ? WHERE ID = ?', t)
        self.conn.commit()

    def upIPC(self, lid, new):
        t = (new, lid)
        self.c.execute('UPDATE local SET IPC = ? WHERE ID = ?', t)
        self.conn.commit()

    def getGID(self, lid):
        t = (lid,)
        self.c.execute('SELECT GID FROM local WHERE ID = ?', t)
        r = self.c.fetchall()
        if 'd' * lid == r[0][0]:
            return False
        return r[0][0]

    def getGLID(self, gid):
        t = (gid,)
        self.c.execute('SELECT ID FROM local WHERE GID = ?', t)
        r = self.c.fetchall()
        if len(r) != 0:
            return r[0][0]
        else:
            return False

    def getBLID(self, bid):
        t = (bid,)
        self.c.execute('SELECT ID FROM local WHERE BID = ?', t)
        r = self.c.fetchall()
        if len(r) != 0:
            return r[0][0]
        else:
            return False
    
    def getILID(self, iid):
        t = (iid,)
        self.c.execute('SELECT ID FROM local WHERE IID = ?', t)
        r = self.c.fetchall()
        if len(r) != 0:
            return r[0][0]
        else:
            return False

    def getBID(self, lid):
        t = (lid,)
        self.c.execute('SELECT BID FROM local WHERE ID = ?', t)
        return self.c.fetchall()[0][0]

    def getAllBID(self):
        self.c.execute('SELECT ID, BID FROM local')
        return self.c.fetchall()
    
    def getIID(self, lid):
        t = (lid,)
        self.c.execute('SELECT IID FROM local WHERE ID = ?', t)
        try:
            return self.c.fetchall()[0][0]
        except IndexError:
            return False

    def getPath(self, lid):
        t = (lid,)
        self.c.execute('SELECT Path FROM local WHERE ID = ?', t)
        return self.c.fetchall()[0][0]

    def getUnmatched(self):
        self.c.execute('SELECT ID FROM local WHERE GID IS NULL')
        return [e for t in self.c.fetchall() for e in t]
    
    def getBUnmatched(self):
        self.c.execute('SELECT ID FROM local WHERE BID IS NULL')
        return [e for t in self.c.fetchall() for e in t]

    def getIUnmatched(self):
        self.c.execute('SELECT ID FROM local WHERE IID IS NULL')
        return [e for t in self.c.fetchall() for e in t]

    def getPlay(self, lid):
        t = (lid,)
        self.c.execute('SELECT PCount FROM local WHERE ID = ?', t)
        return self.c.fetchall()[0][0]

    def getIPC(self, lid):
        t = (lid,)
        self.c.execute('SELECT IPC FROM local WHERE ID = ?', t)
        return self.c.fetchall()[0][0]

    def allPath(self):
        self.c.execute('SELECT Path FROM local')
        return [e for t in self.c.fetchall() for e in t]
    
    def allID(self):
        self.c.execute('SELECT ID FROM local')
        return [e for t in self.c.fetchall() for e in t]

    def remove(self, lid):
        t = (lid,)
        self.c.execute('DELETE FROM local WHERE ID = ?', t)
        self.conn.commit()
    
    def clearBID(self, lid):
        t = (lid,)
        self.c.execute('UPDATE local SET BID = NULL WHERE ID = ?', t)
        self.conn.commit()

    def addPlist(self, plist, lid):
        t = (plist, lid)
        self.c.execute('INSERT INTO playlist (plist, ID) VALUES (?, ?)', t)
        self.conn.commit()

    def removePlist(self, lid, plist):
        t = (plist, lid)
        self.c.execute('DELETE FROM playlist WHERE plist LIKE ? AND ID = ?', t)
        self.conn.commit()

    def getAllPlist(self):
        self.c.execute('SELECT Plist, ID FROM playlist')
        return self.c.fetchall()

    def addMeta(self, lid, name, artist, aArtist, album, artwork=None, track=0, ttrack=0, disk=0, tdisk=0):
        t = (lid, name, artist, aArtist, album, artwork, track, ttrack, disk, tdisk)
        self.c.execute('INSERT INTO meta Values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', t)
        t = (lid,)
        self.c.execute('UPDATE local SET metUP = 1 WHERE ID = ?', t)
        self.conn.commit()

    def updateMeta(self, lid, field, change):
        t = (change, lid)
        self.c.execute('UPDATE meta SET '+ field + ' = ? WHERE ID = ?', t)
        t = (lid,)
        self.c.execute('UPDATE local SET metUP = 1 WHERE ID = ?', t)
        self.conn.commit()
        
    def getMeta(self, lid):
        t = (lid,)
        self.c.execute('SELECT Title, Artist, albumArtist, album, track, ttrack, disk, tdisk FROM meta WHERE ID = ?',t)
        return self.c.fetchall()[0] 

    def hasArt(self, lid):
        t = (lid,)
        self.c.execute('SELECT artwork FROM meta WHERE ID = ?',t)
        return not not self.c.fetchall()
         
    def close(self):
        self.conn.commit()
        self.conn.close()
        return None

        


