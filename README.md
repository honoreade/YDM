# YDM (Youtube Playlist Downloader Addon for IDM)

YDM is an open source addon for **Internet Download Manager** (IDM) for downloading videos from YouTube playlists.

## Table of Contents
* [Features](#features)
* [Requirements](#requirements)
* [Installation](#installation)
* [Usage Example](#usage)
* [Limitations](#limitations)
* [Contributors](#team-members)

## <a name="features"></a>Features
* Download any playlist from YouTube
* Parse playlist to extract all video links
* Save all videos to a custom folder
* Integrates with Internet Download Manager (IDM)
* Simple GUI interface

## <a name="requirements"></a>Requirements
This program is only for `Windows` and requires:

* `Python 3.8` or greater
* `Internet Download Manager (IDM)` installed at the default location
* `yt-dlp` Python module

## <a name="installation"></a>Installation

**Installing the program**

Download this program by clicking the <a href="https://github.com/studiobytestorm/YDM/archive/master.zip">![downloadbutton](http://i.stack.imgur.com/0SWhD.png)</a> button above. Unzip it into a folder, e.g., `C:\YDM`. Then open command prompt and run:

```bash
cd C:\YDM
python yListerFull.py
```

**Installing the requirements**

1. Install `Python 3.8+` from [python.org](https://www.python.org/)
2. Install `yt-dlp` using pip:

```bash
pip install yt-dlp
```

## <a name="usage"></a>Usage Example

Run the program:

```bash
python yListerFull.py
```

This will open a GUI window:

1. **Playlist URL**: Paste a YouTube playlist URL
2. **Save Path**: Select the folder where videos will be saved
3. **Parse**: Click to extract video links from the playlist
4. **Download**: Once parsing is complete, click to send videos to IDM (downloads 4 at a time)

**Screenshot:**

<img src="http://i.stack.imgur.com/R0NRb.png" alt="Screenshot" style="width: 100%;"/>

## <a name="limitations"></a>Limitations
* Maximum video quality is **360p** (or 720p when available) due to YouTube's streaming format restrictions
* Higher resolutions (1080p+) on YouTube use separate video/audio streams that require merging, which IDM cannot handle
* For higher quality downloads, consider using `yt-dlp` directly with FFmpeg

## <a name="team-members"></a>Contributors
* "Bishal Santra" <bsantraigi@gmail.com>

## <a name="refs"></a>References
* [yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube video extraction library

---
