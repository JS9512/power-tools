from pydeezer import Deezer
from pydeezer.constants import track_formats
import sys
from config import serverConfig

deezer = Deezer(arl=serverConfig.deezer_arl)
track_id = str(sys.argv[1].split("/")[-1])
track = deezer.get_track(track_id)
# track is now a dict with a key of info, download, tags, and get_tag
# info and tags are dict
track_info = track["info"]
tags_separated_by_comma = track["tags"]
# download and get_tag are partial functions
quality = {
    "MP3_128": track_formats.MP3_128,
    "MP3_256": track_formats.MP3_256,
    "MP3_320": track_formats.MP3_320,
    "FLAC": track_formats.FLAC,
}[sys.argv[2]]
track["download"](".", quality=quality) # this will download the file, default file name is Filename.[mp3 or flac]
song_name = track_info["DATA"]['SNG_TITLE'].replace("'","").replace("’","")
flac_song = song_name + ".flac"
mp3_song = song_name + ".mp3"
import os
with open("lyrics.txt", "w") as f:
    f.write(open(song_name+".lrc", "r").read())