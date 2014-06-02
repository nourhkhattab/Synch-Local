import sqlite3

class playlistDB:

    def __init__(self):
        self.conn = sqlite3.connect('playlist.db')
        self.c = self.conn.cursor()
        self.c.execute('CREATE TABLE IF NOT EXISTS local (PID INTEGER PRIMARY KEY AUTOINCREMENT, GID TEXT UNIQUE, BID INTEGER UNIQUE, IID INTEGER UNIQUE, Path TEXT NOT NULL UNIQUE, PCount INTEGER DEFAULT 0, IPC INTEGER DEFAULT 0)')
        self.conn.commit()
