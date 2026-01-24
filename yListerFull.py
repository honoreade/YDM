
# coding: utf-8

# In[2]:

# Name: youParse.py
# Version: 1.4
# Author: pantuts
# Description: Parse URLs in Youtube User's Playlist (Video Playlist not Favorites)
# Use python3 and later
# Agreement: You can use, modify, or redistribute this tool under
# the terms of GNU General Public License (GPLv3).
# This tool is for educational purposes only. Any damage you make will not affect the author.
# Usage: python3 youParse.py youtubeURLhere

# pip install yt-dlp

import re
import urllib.request
import urllib.error
import sys
import yt_dlp
from tkinter import *
from tkinter import ttk
import tkinter.constants as Tkconstants
import tkinter.filedialog as tkFileDialog
import os
import subprocess
from threading import Thread
import queue as Queue
import time

def crawl(url):
    """Extract video URLs from a YouTube playlist using yt-dlp."""
    final_url = []

    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            playlist_info = ydl.extract_info(url, download=False)

            if 'entries' in playlist_info:
                for entry in playlist_info['entries']:
                    if entry and 'url' in entry:
                        video_url = f"https://www.youtube.com/watch?v={entry['id']}"
                        final_url.append(video_url)
                        print(video_url)
            else:
                print('No videos found in playlist.')
                return [], 0

    except Exception as e:
        print(f'Error extracting playlist: {e}')
        return [], 0

    return final_url, len(final_url)
        
# if len(sys.argv) < 2 or len(sys.argv) > 2:
#     print('USAGE: python3 youParse.py YOUTUBEurl')    
#     exit(1)
    
# else:
#     url = sys.argv[1]
#     if 'http' not in url:
#         url = 'http://' + url
#     listParser(url)

dir_opt = options = {}
options['initialdir'] = 'C:/'
options['mustexist'] = False
options['title'] = 'This is a title'

def askdirectory():
    """Returns a selected directoryname."""
    newPath = tkFileDialog.askdirectory(**dir_opt)
    if(newPath != ""):
        savePath.set(newPath)
    else:
        print("Hick")
    

# Get the list of videos - stores YouTube URLs for later processing
def listParser(list_url, q, progressQ):
    final_url, l = crawl(list_url)
    uset = list(dict.fromkeys(final_url))  # Remove duplicates while preserving order
    i = 0
    l = len(uset)
    linkArr = []

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }

    for url in uset:
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'Unknown')

                # Store the YouTube URL - we'll get fresh direct URL at download time
                fname = re.sub(r'[<>:\"\/\\|\?\*]+', "_", title) + ".mp4"

                linkArr.append({
                    'youtube_url': url,  # Store original YouTube URL
                    'title': title,
                    'ext': 'mp4',
                    'filename': fname
                })
                print(f"Parsed: {title}")

        except Exception as e:
            print(f"Error parsing {url}: {e}")

        i = i + 1
        progressQ.put(int(i * 100 / l))

    q.put(linkArr)


def get_direct_url(youtube_url):
    """Get fresh direct download URL for a YouTube video (progressive format for IDM)."""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)

            # Look for progressive formats (format 22=720p, 18=360p) that work with IDM
            # These have direct URLs starting with googlevideo.com/videoplayback
            # HLS/DASH manifests (manifest.googlevideo.com) don't work with IDM

            best_format = None
            best_height = 0

            for fmt in info.get('formats', []):
                url = fmt.get('url', '')
                has_video = fmt.get('vcodec') and fmt.get('vcodec') != 'none'
                has_audio = fmt.get('acodec') and fmt.get('acodec') != 'none'
                height = fmt.get('height', 0) or 0

                # Skip HLS/DASH manifests - IDM can't handle them
                if 'manifest.googlevideo.com' in url or url.endswith('.m3u8'):
                    continue

                # Only select formats with both video AND audio (progressive)
                if has_video and has_audio and url:
                    if height > best_height:
                        best_height = height
                        best_format = fmt

            if best_format:
                return best_format['url'], best_format.get('ext', 'mp4')

            return None, None
    except Exception as e:
        print(f"Error getting direct URL: {e}")
        return None, None


# Fire IDM for downloading
def downloadVideos():
    global allDownComplete
    global downGenerator
    print("Start Download next 3 video")
    if allDownComplete:
        if q.empty():
            print("Download queue not ready yet.")
            return
        allDownComplete = False
        downGenerator = downloaderCoroutine()
        print(next(downGenerator))
    else:
        print(next(downGenerator))

def downloaderCoroutine():
    global downStatus
    downStatus = 0
    root.after(100, update_downStatus)
    linkArr = q.get()
    counter = 0
    limit = 4
    prcs = []

    size = len(linkArr)
    done = 0
    for l in linkArr:
        # Get fresh direct URL right before downloading (URLs expire quickly)
        print(f"Getting direct URL for: {l['title']}")
        direct_url, ext = get_direct_url(l['youtube_url'])

        if not direct_url:
            print(f"Failed to get URL for: {l['title']}")
            done = done + 1
            downStatus = int(done*100/size)
            continue

        # Update filename extension if different
        fname = l['filename']
        if ext and ext != l['ext']:
            fname = re.sub(r'\.[^.]+$', f'.{ext}', fname)

        # C:\Program Files (x86)\Internet Download Manager\IDMan.exe" /n /d <link> /p <path> /f <filename>
        comm = '\"C:\\Program Files (x86)\\Internet Download Manager\\IDMan.exe\" /n /d \"' + direct_url + '\" /p \"' + savePath.get() + '\" /f \"' + fname + '\"'
        # os.system(comm)
        prcs.append(subprocess.Popen(comm))
        time.sleep(2)
        done = done + 1
        downStatus = int(done*100/size)
        counter = counter + 1
        print("Counter: "+str(counter))
        print(fname)
        if(counter >= limit):
            print("Press download again to continue...")
            counter = 0
            if done == size:
                allDownComplete = True
                return
            yield downStatus

def update_downStatus():
    downloadPb["value"] = downStatus
    if(downStatus == 100):
        return
    root.after(100, update_downStatus)

def update_bar(parserThread):
    if not progressQ.empty():
        p = progressQ.get()
        pb["value"] = p
        if p == 100:            
            parserThread.join()
            print("Parsing Complete")
            return
    root.after(100, update_bar, parserThread)


# Code for downloading
progressQ = Queue.Queue()
q = Queue.Queue()
def process():
    print("URL:", listURL.get())
    print("SAVE TO:", savePath.get())
    url = listURL.get()
    if(url != ""):
        parserThread = Thread(target = listParser, args = [url, q, progressQ])
        parserThread.daemon = True
        parserThread.start()        
        update_bar(parserThread)
    else:
        print("Nothing to get!!!")
    # print("Ikes!!!")
    

root = Tk()
root.resizable(width=FALSE, height=FALSE)
# root.geometry('{}x{}'.format(600,400))
root.title("Youtube Playlist using IDM")

mainframe = ttk.Frame(root, padding="3 3 12 12")
mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
mainframe.columnconfigure(0, weight=1)
mainframe.rowconfigure(0, weight=1)

listURL = StringVar()
savePath = StringVar()


# Default Path:
listURL.set("")

# Default Save path
savePath.set(os.getcwd())
# savePath.set("C:/Users/Bishal/Shared/Youtube/")

# Labels
ttk.Label(mainframe, text = "Playlist URL: ").grid(column = 1, row=1, sticky = E)
ttk.Label(mainframe, text = "Save Path: ").grid(column = 1, row=2, sticky = E)
ttk.Label(mainframe, text = "Parse Progress: ").grid(column = 1, row=3, sticky = E)
ttk.Label(mainframe, text = "Download Progress: ").grid(column = 1, row=4, sticky = E)

inputWid = 100
# URL Input
url_entry = ttk.Entry(mainframe, textvariable = listURL, width = inputWid)
url_entry.grid(column = 2, row=1, columnspan = 4, sticky = (W, E))

# Path Input
path_entry = ttk.Entry(mainframe,textvariable = savePath)
path_entry.grid(column = 2, row=2, columnspan = 3,sticky = (W, E))

# Progressbar
pb = ttk.Progressbar(mainframe, orient=HORIZONTAL, mode='determinate')
pb.grid(column = 2, row=3, sticky = (W, E), columnspan=3)
pb["value"] = 0
pb["maximum"] = 100

# Progressbar
downloadPb = ttk.Progressbar(mainframe, orient=HORIZONTAL, mode='determinate')
downloadPb.grid(column = 2, row=4, sticky = (W,E), columnspan=3)
downloadPb["value"] = 0
downloadPb["maximum"] = 100

# Buttons
ttk.Button(mainframe, text = "Change Folder", command = askdirectory).grid(column = 5, row=2, sticky = (W,E))
ttk.Button(mainframe, text = "Parse", command = process).grid(column = 5, row=3, sticky = (W,E))
ttk.Button(mainframe, text = "Download", command = downloadVideos).grid(column = 5, row=4, sticky = (W,E))

# Global variables
downStatus = 0
allDownComplete = True
downGenerator = None

for child in mainframe.winfo_children(): child.grid_configure(padx=5, pady=5)
url_entry.focus()

root.mainloop()

