import sqlite3

class synchDB:

    def __init__(self):
        self.conn = sqlite3.connect('database.db')
        self.c = self.conn.cursor()
        self.c.execute('CREATE TABLE IF NOT EXISTS local (ID INTEGER PRIMARY KEY AUTOINCREMENT, GID TEXT UNIQUE, BID INTEGER UNIQUE, IID INTEGER UNIQUE, Path TEXT NOT NULL UNIQUE, PCount INTEGER DEFAULT 0, IPC INTEGER DEFAULT 0)')
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
        return self.c.fetchall()

    def getLID(self, gid):
        t = (gid,)
        self.c.execute('SELECT ID FROM local WHERE GID = ?', t)
        r = self.c.fetchall()
        if len(r) != 0:
            return r[0][0]
        else:
            return False

    def getBID(self, lid):
        t = (lid,)
        self.c.execute('SELECT BID FROM local WHERE ID = ?', t)
        return self.c.fetchall()[0][0]
    
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

    def close(self):
        self.conn.commit()
        self.conn.close()
        return None

        


