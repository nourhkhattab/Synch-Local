from getpass import getpass
from db import synchDB
from itunes import iTunesDB
from match import match
from sqlite3 import IntegrityError
import sqlite3
from fuzzywuzzy import fuzz
from banshee import bDB
import os
from os.path import expanduser
import urllib
from mutagen.id3 import APIC, ID3, TIT2, TPE1, TPE2, TALB, TRCK, TPOS
from mutagen import File as GLB
import unicodedata as UCD
# gmusic api imports
from gmapi.gmusicapi import Musicmanager
from gmapi.gmusicapi import Mobileclient
from gmapi.example import ask_for_credentials

class Synch:
    """ summary of class
    
    Attributes:
        a (str): Desc
    
    """
    def __init__(self, sPath="/Music/Synch/synch.db", iXML="/Music/iTunes/iTunes Library.xml", bConfig="/.config/banshee-1/banshee.db", mFolder="/Music"):
        """ Builds and returns a Synch Object.

        Args:
            sPath (str): Path to Synch db location, defaults to /Music/Synch/synch.db
            iXML (str): Path to iTunes XML, defaults to /Music/iTunes/iTunes Library.xml
            bConfig (str): Path to banshee database, defaults to /.config/banshee-1/banshee.db
            mFolder (str): Path to music folder, defaults to "/Music"




        """
        self.home = expanduser("~") # Home path
        self.mFolder = mFolder
        self.db = synchDB(self.home + sPath) # Creates/Opens Synch database
        self.bdb = bDB(self.home + bConfig) # Opens banshee database
        self.idb = iTunesDB(self.home + iXML) # Opens iTunes XML
        self.createLocalDB() # Scans all files 
        self.scanBanshee()
        self.scaniTunes()
        self.mc = ask_for_credentials()
        print("Login Successfull")
        self.glib = self.mc.get_all_songs()
        print("Fetched songs")
        self.matchL()
        self.metadata()
        self.isUp = self.db.isUp()
        self.updateCount()
        self.gpl = self.mc.get_all_user_playlist_contents()
        print("Fetched playlists")
        self.updatePlaylists()
        self.db.notUp()
        self.bdb.close()
        self.db.close()

    def createLocalDB(self):
        """Adds all local music to the synch database and extracts metadata
        """
        print("Starting scan of local files")
        db = self.db
        home = self.home
        allPaths = db.allPath()
        for root, dirs, files in os.walk(home + self.mFolder): # Find all music files
            for file in files:
                if file.endswith((".mp3",".flac",".ogg",".m4p",".m4a")) and not file.startswith("."):
                    pth = os.path.join(root, file)
                    if pth.decode('utf-8') not in allPaths and "iTunes Media" not in pth.decode('utf-8'): # Exempt all music imported into iTunes to prevent Duplicates
                        lid = db.addSong(pth.decode('utf-8'))
                        
                        # Below adds metadata 

                        sng = GLB(pth, easy=True)
                        title=artist=albumArtist=album=" "
                        if 'title' in sng:
                            title = sng['title'][0]
                        if 'artist' in sng:
                            artist = sng['artist'][0]
                        if 'performer' in sng:
                            albumArtist = sng['performer'][0]
                        if 'albumArtist' in sng:
                            albumArtist = sng['albumArtist'][0]
                        if 'album' in sng:
                            album = sng['album'][0]
                        db.addMeta(lid, title, artist, albumArtist, album)

        print("Finished scan of local files")

    def scanBanshee(self):
        """Scan Banshee files and add their id to the Synch db
        """
        print("Starting to scan Banshee")
        db = self.db
        bdb = self.bdb
        unmatched = db.getBUnmatched() # Get songs without a Banshee id
        for i in unmatched:
            db.addBID(i, bdb.getID(db.getPath(i))) # Add Banshee id to song

        print("Finished scanning Banshee")

    def scaniTunes(self):
        """ Scan iTunes files and add them to local db
        """
        print("Starting iTunes scan")
        db = self.db
        idb = self.idb
        unmatched = db.getIUnmatched() # Get songs without an iTunes id
        ipl = idb.getPaths()
        for i in unmatched:
            ip = db.getPath(i)
            pl = [b[1] for b in ipl] # List comprehension to get all paths
            if ip in pl:
                db.addIID(i, ipl[pl.index(ip)][0])

        print("Finished iTunes scan")

    def matchL(self, gManagerPath="/.config/google-musicmanager/ServerDatabase.db"):
        """Match local music to google music

        Args:
            gManagerPath (str): Path of the google music manager database, defaults to /.config/google-musicmanager/ServerDatabase.db

        """
        print("Starting local to google match")
        glib = self.glib
        db = self.db
        unmatched = db.getUnmatched() # Get all songs without a Google Music ID
        dconn = sqlite3.connect(self.home + gManagerPath) # Connect to Google Music Manager database
        dcur = dconn.cursor()
        for u in unmatched:
            p = db.getPath(u)
            t = (p[len(self.home) + len(self.mFolder) + 1:],) # Because Google Music works with a relative path
            dcur.execute('SELECT ServerId FROM XFILES WHERE FileHandle = ?', t)
            r = dcur.fetchall()
            if r: # If file is in Google Music Managers database 
                try:
                    db.addGID(u,r[0][0])
                    continue
                except IntegrityError: # If there is a conflict pass due to later conflict handling
                    None
            m = match(p, glib)
            if m == "delete":
                db.remove(u)  # Match returned that its a nonn existing song
                continue
            elif m:
                try:
                    stupid = True
                    db.addGID(u, m['id'])
                    continue
                except IntegrityError: 
                    oldid = db.getGLID(m['id'])
                    print("Song match conflict :(")
                    print("This is the raw path of the attempted matching song: " + p)
                    print("This is the raw path of the already matched song: " + db.getPath(oldid))
                    print("This is the Google Music song being matched to:" + "\n" + m['title'].encode('utf-8')+ "\n" + m['artist'].encode('utf-8')+ "\n" + m['album'].encode('utf-8'))
                    while stupid: # While incorrect option is chosen
                        im = raw_input("Enter:\n0 : If both are incorrect matches\n1 : If the first (attempting to match) path is the correct match\n2 : If the second (previously matched) path is the correct match\n")
                        if im in ('0', '1', '2'):
                            stupid = False
                    if im == '0':
                        shame = [u, oldid] # list of songs to be added
                        db.addGID(oldid, None)
                    elif im == '1':
                        shame = [oldid]
                        db.addGID(oldid, None)
                        db.addGID(u, m['id'])
                    else:
                        shame = [u]
                    print("Correcting...")
            else:
                shame = [u]
                print("Could not find a match")
            for s in shame:
                print("Manually matching: " + db.getPath(s))
                print("Enter a search term, type s to skip or type d if song is not on your Google Music account:")
                term = raw_input("[s|d|<search>] : ")
                if term == 'd':
                    print("Added to do not match list")
                    db.addGID(s, 'd'*s) # Unique identifier
                elif term == 's':
                    print("Track skipped")
                else:
                    again = True
                    while again:
                        op = 0
                        options = []
                        for i in glib:
                            if len([True for e in [i['title'],i['artist'],i['album']] if fuzz.token_set_ratio(e, term) > 85]) > 0: # Basic search algo
                                print(str(op).encode('utf-8') + ")\t" + i['title'].encode('utf-8')+'\t\t\t'+ i['artist'].encode('utf-8') + '\t\t\t'+i['album'].encode('utf-8'))
                                op += 1
                                options += [i['id']]
                        print ("Path reminder : "+ db.getPath(s))
                        print ("Enter either match number, s to skip, d is song is not on your Google Music account or n for a new search")
                        sel = raw_input("[s|d|n|<#num#>] : ")
                        print ('\n')
                        if sel == 'd':
                            print("Added to do not match list\n")
                            db.addGID(s, 'd'*s)
                            again = False
                        elif sel == 's':
                            print("Track skipped\n")
                            again = False
                        else:
                            try:
                                db.addGID(s, options[int(sel)])
                                again = False
                                print("Matched\n")
                            except IntegrityError:
                                oldid = db.getGLID(options[int(sel)])
                                db.addGID(oldid, None)
                                db.addGID(u, options[int(sel)])
                                shame += [oldid]
                                print("Matched and removed other in conflict\n")
                                again = False
                            except (ValueError, IndexError):
                                term = raw_input("New search term: ")
        print("Finished")
        dconn.close()


    def updateCount(self):
        """Updates playcount
        """
        glib = self.glib
        db = self.db
        idb = self.idb
        bdb = self.bdb
        mc = self.mc
        isUp = self.isUp
        print("Starting to update playcount")
        for c in glib:
            try:
                gPC = c['playCount']
            except KeyError:
                gPC = 0 # Songs with play count of 0 doesnt have it as a key
            dc = db.getGLID(c['id'])
            if not dc: # If the google song is not in our local database
                continue
            lPC = db.getPlay(dc)
            if lPC > gPC:
                mc.increment_song_playcount(c['id'], plays=(lPC-gPC)) # If google is behind local make it catch up first
                gPC = lPC                                             # Though this causes errors if the our glib dictionary is behind the server in counts
                                                                      # But it solves more problems then it causes
            bid = db.getBID(dc)
            iid = db.getIID(dc)
            try:
                bPC = bdb.getPC(bid)
            except IndexError:
                bPC = lPC # If song does not exist on banshee then make playcount local play count for calculation
            if iid:
                iPC = idb.getPC(iid)
                if isUp: # if iTunes has been updated since last sync
                    iOPC = lPC
                else:
                    iOPC = db.getIPC(dc)
            else: # Song is not on iTunes
                iPC = 0
                iOPC = 0
            PC = gPC + bPC + iPC - iOPC - lPC
            if PC < 50: # This is due to some errors, so I set my baseline to 50
                PC = 50
            if PC-lPC > 0:
                db.upPlay(dc, PC)
            if PC - bPC > 0:
                bdb.upPlay(bid, PC)
            if iPC > iOPC:
                    db.upIPC(dc, iPC)
            if PC-gPC > 0:
                mc.increment_song_playcount(c['id'], plays=(PC-gPC))

    def updatePlaylists(self):
        """ Updates playlists
        """
        print("Starting to update playlists")
        gpl = self.gpl
        db = self.db
        idb = self.idb
        bdb = self.bdb
        mc = self.mc
        isUp = self.isUp

        oPlist = db.getAllPlist()
        ogPlist = [i for i in oPlist if db.getGID(i[1])]
        iPlist = [(i, db.getILID(l)) for i in idb.playlists for l in idb.playlists[i]]
        brPlist = bdb.getPlists()
        grPlist = {(i['name'], j['trackId']):j['id'] for i in gpl for j in i['tracks']}
        gPNames = {i['name']:i['id'] for i in gpl}
        bPlist = []
        gPlist = []
        for i in brPlist:
            blid = db.getBLID(i[1])
            if blid:
                bPlist += [(i[0], blid)]
        for i in grPlist:
            glid = db.getGLID(i[1])
            if glid:
                gPlist += [(i[0], glid)]
        if isUp:
            iDiff = (set(iPlist) - set(oPlist), set(oPlist) - set(iPlist))
        else:
            iDiff = (set(), set())
        bDiff = (set(bPlist) - set(oPlist), set(oPlist) - set(bPlist))
        gDiff = (set(gPlist) - set(ogPlist), set(ogPlist) - set(gPlist))
        tDiff = (bDiff[0] | gDiff[0] | iDiff[0], bDiff[1] | gDiff[1]| iDiff[1])
        gDo = (tDiff[0] - gDiff[0], tDiff[1] - gDiff[1])
        bDo = (iDiff[0] | gDiff[0] - bDiff[0], iDiff[1] | gDiff[1] - bDiff[1])
        for i in set([t[0] for t in gDo[0]]):
            if i not in gPNames:
                gPNames[i] = mc.create_playlist(i)
        for i in set([t[0] for t in bDo[0]]):
            if not bdb.pExist(i):
                bdb.addPlist(i)

        for i in gDo[0]:
            glid = db.getGID(i[1])
            if glid:
                mc.add_songs_to_playlist(gPNames[i[0]], glid)

        for i in gDo[1]:
            glid = db.getGID(i[1])
            if glid:
                mc.remove_entries_from_playlist(grPlist[(i[0], glid)])

        for i in bDo[0]:
            bdb.addToPlist(i[0], db.getBID(i[1]))

        for i in bDo[1]:
            bdb.rmPlist(i[0], db.getBID(i[1]))

        for i in tDiff[0]:
            db.addPlist(i[0], i[1])
        for i in tDiff[1]:
            db.removePlist(i[0], i[1])

        print("finished")

    def metadata(self):
        """ Updates metadata
        """
        print("Starting to update metadata :"), 
        glib = self.glib
        db = self.db
        for i in glib:
            lid = db.getGLID(i['id'])
            if not lid:
                continue 
            ipath = db.getPath(lid)
            if ".mp3" not in ipath.lower():
                continue
            
            if 'albumArtRef' in i and not db.hasArt(lid):
                itag = ID3(ipath)
                itag.add(APIC(encoding=3, mime='image/jpeg', type=3, data=urllib.urlopen(i['albumArtRef'][0]['url']).read()))
                itag.save()
                db.updateMeta(lid, 'Artwork', "yes")

            
            meta = db.getMeta(lid)
            dMeta = {'title':meta[0], 'artist':meta[1], 'albumArtist':meta[2], 'album':meta[3]}
            diff = [j for j in dMeta if i[j] != dMeta[j]]
            if not diff:
                continue
            itag = ID3(ipath)
            for m in diff:
                db.updateMeta(lid, m, i[m])
            itag.add(TIT2(encoding=1, text=[i['title']]))
            itag.add(TPE1(encoding=1, text=[i['artist']]))
            itag.add(TPE2(encoding=1, text=[i['albumArtist']]))
            itag.add(TALB(encoding=1, text=[i['album']]))
            if 'totalDiscCount' in i:
                itag.add(TPOS(encoding=1, text=[unicode(i['discNumber']) + u'/' + unicode(i['totalDiscCount'])]))
            if 'totalTrackCount' in i:
                itag.add(TRCK(encoding=1, text=[unicode(i['trackNumber']) + u'/' + unicode(i['totalTrackCount'])]))
            itag.save()
        print("Finished updating metadata")

synchO = Synch()        
#home = expanduser("~")
#db = synchDB(home + "/Music/synch.db")
#bdb = bDB()
#idb = iTunesDB(home + "/Music/iTunes/iTunes Library.xml")
#scan()
#scanB()
#scanI()
#mc = ask_for_credentials()
#print("Success!!")
#glib = mc.get_all_songs()
#print("Fetched songs")
#matchL(glib)
#print("MatchL done")
#metadata(glib)
#print("Metadata Updated")
#isUp = db.isUp()
#print(isUp)
#updateCount(glib)
#db.notUp()
#print("Update Count done")
#gpl = mc.get_all_user_playlist_contents()
#print("Fetched playlists")
#updatePlaylists(gpl)
#bdb.close()
#db.close()
