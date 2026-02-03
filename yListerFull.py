
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

# FFmpeg path for high quality downloads
FFMPEG_PATH = r"C:\ffmpeg-2026-01-12-git-21a3e44fbe-full_build\bin"

# Add FFmpeg to PATH so yt-dlp can find it
if FFMPEG_PATH not in os.environ.get('PATH', ''):
    os.environ['PATH'] = FFMPEG_PATH + os.pathsep + os.environ.get('PATH', '')

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
            # Handle single video URL
            elif 'id' in playlist_info:
                video_url = f"https://www.youtube.com/watch?v={playlist_info['id']}"
                final_url.append(video_url)
                print(f"Found single video: {video_url}")
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


def download_high_quality(youtube_url, output_path, filename, max_height=None, progress_callback=None):
    """Download video using yt-dlp with FFmpeg for best quality (1080p+)."""
    # Sanitize filename
    safe_filename = re.sub(r'[<>:\"\/\\|\?\*]+', "_", filename)
    safe_filename = re.sub(r'\.[^.]+$', '', safe_filename)

    output_template = os.path.join(output_path, safe_filename + '.mp4')

    # Construct format string based on max_height
    if max_height and max_height != "Best":
        # Limit height, prefer mp4 video and m4a audio for compatibility
        # Try to get the best video that fits the height limit
        format_str = f'bestvideo[height<={max_height}]+bestaudio/best[height<={max_height}]/best'
    else:
        # Best available (4K/8K), no limits
        format_str = 'bestvideo+bestaudio/best'

    ydl_opts = {
        'format': format_str,
        'merge_output_format': 'mp4',
        'outtmpl': output_template,
        'ffmpeg_location': FFMPEG_PATH,
        'verbose': True,
        'no_warnings': False,
        'keepvideo': False,
        'overwrites': True,
        
        # Ensure we prioritize resolution
        'format_sort': ['res', 'ext:mp4:m4a'],
        
        # Connection & Anti-throttling
        'retries': 10,
        'fragment_retries': 10,
        'file_access_retries': 5,
        'extractor_retries': 5,
        # Removed 'extractor_args' to allow default clients (web/android/ios) for maximum stream availability
        
        # Explicitly disable external configs and cookie extraction
        'ignoreerrors': True,
        'ignore_config': True,
        'cookiesfrombrowser': None,
        
        # Network
        'sleep_interval': 2,
        'max_sleep_interval': 5,
        'sleep_interval_requests': 1,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
        },
    }

    try:
        print(f"[DEBUG] FFmpeg path: {FFMPEG_PATH}")
        print(f"[DEBUG] Output: {output_template}")
        print(f"[DEBUG] YouTube URL: {youtube_url}")
        print(f"[DEBUG] Quality: {max_height if max_height else 'Best'}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
        print(f"[DEBUG] Download complete: {output_template}")
        return True, output_template
    except Exception as e:
        print(f"Error downloading {filename}: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e)


def download_high_quality_batch(linkArr, output_path, status_callback=None, max_height=None):
    """Download all videos in high quality mode using yt-dlp + FFmpeg."""
    total = len(linkArr)
    completed = 0

    for item in linkArr:
        youtube_url = item['youtube_url']
        title = item['title']
        filename = item['filename']

        print(f"\n[{completed + 1}/{total}] Downloading: {title}")

        success, result = download_high_quality(youtube_url, output_path, filename, max_height)

        if success:
            print(f"✓ Completed: {title}")
        else:
            print(f"✗ Failed: {title} - {result}")

        completed += 1
        if status_callback:
            status_callback(int(completed * 100 / total))

    print(f"\n=== Download Complete: {completed}/{total} videos ===")
    return completed


# Fire IDM for downloading (or use yt-dlp for high quality)
def downloadVideos():
    global allDownComplete
    global downGenerator
    global downStatus

    # Check which mode is selected
    mode = downloadMode.get()

    if mode == "hq":
        # High Quality Mode - use yt-dlp + FFmpeg
        if q.empty():
            print("Download queue not ready yet.")
            return

        print("=== HIGH QUALITY MODE (yt-dlp + FFmpeg) ===")
        print("Downloading best available quality (up to 4K)...")

        linkArr = q.get()

        def status_update(progress):
            global downStatus
            downStatus = progress

        # Run in a separate thread to not block UI
        def hq_download_thread():
            global downStatus
            global allDownComplete
            downStatus = 0
            
            # Map selection to height value
            res_str = resolutionVar.get()
            height_map = {
                "Best (4K/8K)": "Best",
                "1440p (2K)": "1440",
                "1080p (HD)": "1080",
                "720p (HD)": "720",
                "480p": "480"
            }
            max_height = height_map.get(res_str, "Best")
            
            root.after(100, update_downStatus)
            download_high_quality_batch(linkArr, savePath.get(), status_update, max_height)
            downStatus = 100
            allDownComplete = True

        allDownComplete = False
        hq_thread = Thread(target=hq_download_thread)
        hq_thread.daemon = True
        hq_thread.start()
    else:
        # IDM Mode - original behavior
        print("=== IDM MODE (max 720p) ===")
        print("Start Download next 4 videos")
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
downloadMode = StringVar()

# Default Path:
listURL.set("")

# Default Save path
savePath.set(os.getcwd())
# savePath.set("C:/Users/Bishal/Shared/Youtube/")

# Default download mode
downloadMode.set("hq")  # Default to high quality

# Labels
ttk.Label(mainframe, text = "Playlist URL: ").grid(column = 1, row=1, sticky = E)
ttk.Label(mainframe, text = "Save Path: ").grid(column = 1, row=2, sticky = E)
ttk.Label(mainframe, text = "Download Mode: ").grid(column = 1, row=3, sticky = E)
ttk.Label(mainframe, text = "Parse Progress: ").grid(column = 1, row=4, sticky = E)
ttk.Label(mainframe, text = "Download Progress: ").grid(column = 1, row=5, sticky = E)

inputWid = 100
# URL Input
url_entry = ttk.Entry(mainframe, textvariable = listURL, width = inputWid)
url_entry.grid(column = 2, row=1, columnspan = 4, sticky = (W, E))

# Path Input
path_entry = ttk.Entry(mainframe,textvariable = savePath)
path_entry.grid(column = 2, row=2, columnspan = 3,sticky = (W, E))

# Download Mode Selection (Radio Buttons)
modeFrame = ttk.LabelFrame(mainframe, text="Download Settings", padding="3 3 12 12")
modeFrame.grid(column = 2, row=3, columnspan=3, sticky = (W, E))

ttk.Radiobutton(modeFrame, text="High Quality Mode",
                variable=downloadMode, value="hq").grid(column=0, row=0, sticky=W)

# Resolution Selector (Only relevant for HQ mode)
resolutionVar = StringVar()
resolutionVar.set("1080p (HD)") # Default
resCombo = ttk.Combobox(modeFrame, textvariable=resolutionVar, state="readonly", width=15)
resCombo['values'] = ("Best (4K/8K)", "1440p (2K)", "1080p (HD)", "720p (HD)", "480p")
resCombo.grid(column=1, row=0, sticky=W, padx=5)

ttk.Radiobutton(modeFrame, text="IDM Mode (Legacy)",
                variable=downloadMode, value="idm").grid(column=0, row=1, sticky=W, pady=5)

# Progressbar - Parse
pb = ttk.Progressbar(mainframe, orient=HORIZONTAL, mode='determinate')
pb.grid(column = 2, row=4, sticky = (W, E), columnspan=3)
pb["value"] = 0
pb["maximum"] = 100

# Progressbar - Download
downloadPb = ttk.Progressbar(mainframe, orient=HORIZONTAL, mode='determinate')
downloadPb.grid(column = 2, row=5, sticky = (W,E), columnspan=3)
downloadPb["value"] = 0
downloadPb["maximum"] = 100

# Buttons
ttk.Button(mainframe, text = "Change Folder", command = askdirectory).grid(column = 5, row=2, sticky = (W,E))
ttk.Button(mainframe, text = "Parse", command = process).grid(column = 5, row=4, sticky = (W,E))
ttk.Button(mainframe, text = "Download", command = downloadVideos).grid(column = 5, row=5, sticky = (W,E))

# Global variables
downStatus = 0
allDownComplete = True
downGenerator = None

for child in mainframe.winfo_children(): child.grid_configure(padx=5, pady=5)
url_entry.focus()

root.mainloop()

