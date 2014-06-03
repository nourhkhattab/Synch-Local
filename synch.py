from getpass import getpass
from db import synchDB
from itunes import iTunesDB
from match import match
from sqlite3 import IntegrityError
from fuzzywuzzy import fuzz
from banshee import bDB
import os
from os.path import expanduser

home = expanduser("~")

# gmusic api imports
from gmapi.gmusicapi import Musicmanager
from gmapi.gmusicapi import Mobileclient
from gmapi.example import ask_for_credentials


def scan():
    ap = db.allPath()
    for root, dirs, files in os.walk(home + "/Music"):
        for file in files:
            if file.endswith((".mp3",".flac",".ogg",".m4p",".m4a")) and not file.startswith("."):
                pth = os.path.join(root, file)
                if pth.decode('utf-8') not in ap and "iTunes Media" not in pth.decode('utf-8'):
                    db.addSong(pth.decode('utf-8'))

def scanB():
    unmatched = db.getBUnmatched()
    for i in unmatched:
        db.addBID(i, bdb.getID(db.getPath(i)))

def scanI():
    unmatched = db.getIUnmatched()
    ipl = idb.getPaths()
    for i in unmatched:
        ip = db.getPath(i)
        pl = [b[1] for b in ipl]
        if ip in pl:
            db.addIID(i, ipl[pl.index(ip)][0])


def loginMM():
    mm = Musicmanager()
    if not mm.login():
        mm.perform_oauth()
        mm.login()
    return mm

def matchL(glib):
    unmatched = db.getUnmatched()
    for u in unmatched:
        p = db.getPath(u)
        m = match(p, glib)
        if m == "delete":
          db.remove(u)  
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
                while stupid:
                    im = raw_input("Enter:\n0 : If both are incorrect matches\n1 : If the first (attempting to match) path is the correct match\n2 : If the second (previously matched) path is the correct match\n")
                    if im in ('0', '1', '2'):
                        stupid = False
                if im == '0':
                    shame = [u, oldid]
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
                db.addGID(s, 'd'*s)
            elif term == 's':
                print("Track skipped")
            else:
                again = True
                while again:
                    op = 0
                    options = []
                    for i in glib:
                        if len([True for e in [i['title'],i['artist'],i['album']] if fuzz.token_set_ratio(e, term) > 85]) > 0:
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


def updateCount(glib):
    for c in glib:
        try:
            gPC = c['playCount']
        except KeyError:
            gPC = 0
        dc = db.getGLID(c['id'])
        if not dc:
            continue
        lPC = db.getPlay(dc)
        bid = db.getBID(dc)
        iid = db.getIID(dc)
        bPC = bdb.getPC(bid)
        if iid:
            iPC = idb.getPC(iid)
            if isUp:
                iOPC = lPC
            else:
                iOPC = db.getIPC(dc)
        else:
            iPC = 0
            iOPC = 0
        PC = gPC + bPC + iPC - iOPC - lPC 
        if PC-lPC > 0:
            db.upPlay(dc, PC)
        else:
            continue
        if PC - bPC > 0:
            bdb.upPlay(bid, PC)
        if PC-gPC > 0:
            mc.increment_song_playcount(c['id'], plays=(PC-gPC))
        if PC-iPC > 0:
            if isUp:
                db.upIPC(dc, PC)
            else:
                db.upIPC(dc, iPC)

def updatePlaylists(gpl):
    oPlist = db.getAllPlist()
    iPlist = [(i, l) for i in idb.playlists for l in idb.playlists[i]]
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
        iDiff = set()
    bDiff = (set(bPlist) - set(oPlist), set(oPlist) - set(bPlist))
    gDiff = (set(gPlist) - set(oPlist), set(oPlist) - set(gPlist))
    tDiff = (bDiff[0] | gDiff[0] | iDiff[0], bDiff[1] | gDiff[1]| iDiff[1])

    gDo = (iDiff[0] | bDiff[0] - gDiff[0], iDiff[1] | bDiff[1] - gDiff[1])
    bDo = (iDiff[0] | gDiff[0] - bDiff[0], iDiff[1] | gDiff[1] - bDiff[1])

    for i in set([t[0] for t in gDo[0]]):
        if i not in gPNames:
            gPNames[i] = mc.create_playlist(i)
    for i in set([t[0] for t in bDo[0]]):
        if not bdb.pExist(i):
            bdb.addPlist(i)

    for i in gDo[0]:
        mc.add_songs_to_playlist(gPNames[i[0]], db.getGID(i[1]))

    for i in gDo[1]:
        mc.remove_entries_from_playlist(grPlist[(i[0], db.getGID(i[1]))])

    for i in bDo[0]:
        bdb.addToPlist(i[0], db.getBID(i[1]))

    for i in bDo[1]:
        bdb.rmPlist(i[0], db.getBID(i[1]))

    for i in tDiff[0]:
        db.addPlist(i[0], i[1])
    
    for i in tDiff[1]:
        db.removePlist(i[0], i[1])

        
db = synchDB(home + "/Music/synch.db")
bdb = bDB()
idb = iTunesDB(home + "/Music/iTunes/iTunes Library.xml")
scan()
scanB()
scanI()
mc = ask_for_credentials()
print("Success!!")
glib = mc.get_all_songs()
print("Fetched songs")
matchL(glib)
print("MatchL done")
isUp = db.isUp()
print(isUp)
updateCount(glib)
db.notUp()
print("Update Count done")
gpl = mc.get_all_user_playlist_contents()
print("Fetched playlists")
updatePlaylists(gpl)
bdb.close()
db.close()
