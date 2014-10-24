from getpass import getpass
from db import synchDB
from itunes import iTunesDB
from match import match
from manager import managerDB
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
    def __init__(self, sPath="/Music/Synch/synch.db", iXML="/Music/iTunes/iTunes Library.xml", bConfig="/.config/banshee-1/banshee.db", mFolder="/Music", gManagerPath="/.config/google-musicmanager/ServerDatabase.db"):
        """ Builds and returns a Synch Object.

        Args:
            sPath (str): Path to Synch db location, defaults to /Music/Synch/synch.db
            iXML (str): Path to iTunes XML, defaults to /Music/iTunes/iTunes Library.xml
            bConfig (str): Path to banshee database, defaults to /.config/banshee-1/banshee.db
            mFolder (str): Path to music folder, defaults to "/Music"




        """
        self.home = expanduser("~") # Home path
        self.mFolder = mFolder
        #self.db = synchDB(self.home + sPath) # Creates/Opens Synch database
        self.man = managerDB(self.home + gManagerPath, self.home, self.mFolder) # Connect to Google Music Manager database
        #self.bdb = bDB(self.home + bConfig) # Opens banshee database
        #self.idb = iTunesDB(self.home + iXML) # Opens iTunes XML
        #self.createLocalDB() # Scans all files 
        #self.scanBanshee()
        #self.scaniTunes()
        #self.mc = ask_for_credentials()
        #print("Login Successfull")
        #self.glib = self.mc.get_all_songs()
        #print("Fetched songs")
        #self.scanGMusic()
        #self.matchL()
        #self.metadata()
        #self.isUp = self.db.isUp()
        #self.updateCount()
        #self.gpl = self.mc.get_all_user_playlist_contents()
        #print("Fetched playlists")
        #self.updatePlaylists()
        #self.db.notUp()
        #self.bdb.close()
        #self.db.close()
        self.man.close()




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

    def scanGMusic(self):
        db = self.db
        print('Scanning Google Library')
        glib = self.glib
        gids = [i['id'] for i in glib]
        remove = [db.getGLID(j) for j in db.getAllGID() if j not in gids]
        for i in remove:
            db.addGID(i, None)
        print('Finished Scan')

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

    def matchL(self):
        """Match local music to google music

        Args:
            gManagerPath (str): Path of the google music manager database, defaults to /.config/google-musicmanager/ServerDatabase.db

        """
        print("Starting local to google match")
        glib = self.glib
        db = self.db
        man = self.man
        unmatched = db.getUnmatched() # Get all songs without a Google Music ID
        for u in unmatched:
            p = db.getPath(u)
            r = man.getGID(p)
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
        print("Starting to update metadata") 
        glib = self.glib
        db = self.db
        man = self.man
        mMeta = {}
        for g in man.getAllMeta():
            mMeta[g[0]] = {'title':g[1], 'artist':g[3], 'albumArtist':g[4], 'album':g[2], 'genre':g[6], 'trackNumber':g[7], 'totalTrackCount':g[8], 'diskNumber':g[9], 'totalDiskCount':g[10]}
        for i in glib:
            lid = db.getGLID(i['id'])
            if not lid:
                continue 
            ipath = db.getPath(lid)
            try:
                m = mMeta[i['id']]
            except KeyError:
                db.addGID(lid, None)
                continue 
            tags = [t for t in m for j in i if t == j]
            nMatch = []
            for t in tags:
                if m[t] != i[t]:
                    nMatch += [t]
            if nMatch:
                if '.mp3' in ipath or '.m4a' in ipath:
                    try:
                        sng = GLB(ipath, easy=True) 
                    except IOError:
                        db.remove(lid)
                        continue
                else:
                    continue
                for n in nMatch:
                    if '.mp3' in ipath and n == 'albumArtist':
                        sng['performer'] = [i['albumArtist']]
                        man.setMeta(i['id'], 'MusicAlbumArtist', i['albumArtist'])
                    else:
                        if n in ('trackNumber', 'totalTrackCount', 'diskNumber', 'totalDiskCount'):
                            if n in ('trackNumber', 'totalTrackCount'):
                                sng['tracknumber'] = [str(i['trackNumber']) + '/' + str(i['totalTrackCount'])]
                                man.setMeta(i['id'], 'MusicTrackNumber', int(i['trackNumber']))
                                man.setMeta(i['id'], 'MusicTrackCount', int(i['totalTrackCount']))
                            else:
                                sng['disknumber'] = [str(i['diskNumber']) + '/' + str(i['totalDiskCount'])]
                                man.setMeta(i['id'], 'MusicDiscNumber', int(i['discNumber']))
                                man.setMeta(i['id'], 'MusicDiscCount', int(i['totalDiscCount']))
                        else:
                            sng[n.lower()] = [i[n]]
                            man.setMeta(i['id'], n.lower().replace('title', 'MusicName').replace('albumArtist', 'MusicAlbumArtist').replace('album', 'MusicAlbum').replace('artist', 'MusicArtist').replace('genre', 'MusicGenre'), i[n])
                    db.setUpMeta(lid)
                sng.save()


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
