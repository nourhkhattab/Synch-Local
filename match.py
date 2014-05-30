import mutagen
import os
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from fuzzywuzzy import fuzz
from db import synchDB

def match(song, gdic):
    ftype = song[song.rfind('.'):].lower()
    try:
        if ftype == ".mp3":
            smp = MP3(song)
        elif ftype == ".wma":
            print("wma")
            return "False"
        elif ftype == ".flac":
            smp = FLAC(song)
        elif ftype == ".ogg":
            print("ogg")
            return "False"
        elif ftype in (".mp4", ".m4a"):
            smp = MP4(song)
        else:
            return False
    except IOError:
        return "delete"
    if ftype == ".flac":
        name = smp['title'][0]
        artist = smp['artist'][0]
        album = smp['album'][0]
    elif ftype == ".m4a":
        name = smp['\xa9nam'][0]
        artist = smp['\xa9ART'][0]
        album = smp['\xa9alb'][0] 
    else:
        name = smp["TIT2"].pprint()[5:].replace('[','(').replace(']',')')
        artist = smp["TPE1"].pprint()[5:].replace("Feat", "Featuring").replace("Andre 3000", "OutKast").replace("Big Boi", "OutKast")
        album = smp["TALB"].pprint()[5:]
    pmatch = [i for i in gdic if fuzz.token_set_ratio(name, i['title']) > 90]
    if len(pmatch) == 1:
        return pmatch[0]
    pmatch = [i for i in pmatch if fuzz.token_set_ratio(artist, i['artist']) > 90]
    if len(pmatch) == 1:
        return pmatch[0]
    pmatch = [i for i in pmatch if fuzz.token_set_ratio(album, i['album']) > 90]
    if len(pmatch) == 1:
        return pmatch[0]
    #pmatch = [i for i in pmatch if ((('(' not in name) and ('(' not in i['title'])) or ((('(' in name) and ('(' in i['title'])) and (name[name.rindex("(") + 1:name.rindex(")")].lower() == i['title'][i['title'].rindex("(") + 1:i['title'].rindex(")")].lower())))]
    pmatch = [i for i in gdic if fuzz.token_sort_ratio(name, i['title']) > 90]
    if len(pmatch) == 1:
        return pmatch[0]
    #print ([(i['title'], i['artist'], i['album'], i['durationMillis']) for i in pmatch])
    pmatch = [i for i in pmatch if abs(smp.info.length * 1000 - int(i['durationMillis'].encode('utf-8'))) < 1000]
    if len(pmatch) == 1:
        return pmatch[0]
    else:
        #print(name, artist, album, smp.info.length * 1000)
        return False
        

