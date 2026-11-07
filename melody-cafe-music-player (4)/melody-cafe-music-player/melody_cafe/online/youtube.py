# Melody Cafe Music Player - Ancilla Danica Dsouza | PRN: 25070721021
"""YouTube online music search and download via yt-dlp.
Enables full-length songs with no 30-second preview limitations.
"""

import os
import re
import shutil
import urllib.parse
from .common import OnlineError, CACHE_DIR

try:
    import yt_dlp
    YT_DLP_OK = True
except ImportError:
    yt_dlp = None
    YT_DLP_OK = False


def is_available():
    """Returns True if yt-dlp is installed and available."""
    return YT_DLP_OK


def clean_title_and_artist(raw_title, uploader=""):
    """Parse 'Artist - Title' patterns common on YouTube."""
    raw = raw_title.strip()
    # Strip common suffixes like (Official Video), [Official Audio], etc.
    raw = re.sub(r"[\(\[](?:Official\s+(?:Music\s+)?Video|Official\s+Audio|Audio|Lyric\s+Video|Lyrics|Visualizer)[\)\]]", "", raw, flags=re.IGNORECASE).strip()
    
    if " - " in raw:
        parts = raw.split(" - ", 1)
        artist = parts[0].strip()
        title = parts[1].strip()
    elif " — " in raw:
        parts = raw.split(" — ", 1)
        artist = parts[0].strip()
        title = parts[1].strip()
    else:
        title = raw
        artist = uploader.replace(" - Topic", "").replace("VEVO", "").strip() or "YouTube Artist"
    return title or "Unknown", artist or "Unknown"


def search(query, limit=15):
    """Search YouTube for full-length songs using yt-dlp.
    Returns a list of track dictionaries compatible with the app.
    """
    if not is_available():
        raise OnlineError("yt-dlp is not installed. Run: python -m pip install yt-dlp")
    
    query = query.strip()
    if not query:
        return []
    
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
        "socket_timeout": 12,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            res = ydl.extract_info(f"ytsearch{int(limit)}:{query}", download=False)
    except Exception as e:
        raise OnlineError(f"YouTube search failed: {e}")
    
    tracks = []
    for entry in res.get("entries", []):
        if not entry:
            continue
        vid_id = entry.get("id") or ""
        raw_title = entry.get("title") or "Unknown"
        uploader = entry.get("uploader") or entry.get("channel") or ""
        duration = int(float(entry.get("duration") or 0))
        
        # Skip extremely long videos (> 20 mins) like multi-hour compilations by default
        if duration > 1200:
            continue
        
        title, artist = clean_title_and_artist(raw_title, uploader)
        webpage_url = entry.get("webpage_url") or entry.get("url") or f"https://www.youtube.com/watch?v={vid_id}"
        
        tracks.append({
            "id": vid_id,
            "title": title,
            "artist": artist,
            "album": "YouTube",
            "duration": duration,
            "preview_url": webpage_url,
            "link": webpage_url,
            "source": "youtube",
            "full": True,
        })
    return tracks


def download(track, timeout=60, cache_dir=None):
    """Download full-length audio for a YouTube track using yt-dlp.
    Returns the path to the downloaded audio file (.mp3, .m4a, etc.).

    Format priority (no ffmpeg required):
      1. mp3  – directly playable by pygame on Windows
      2. m4a  – playable via Windows MCI
      3. best – anything yt-dlp can grab as fallback
    """
    if not is_available():
        raise OnlineError("yt-dlp is not installed. Run: python -m pip install yt-dlp")

    cache_dir = cache_dir or CACHE_DIR
    os.makedirs(cache_dir, exist_ok=True)

    vid_id = track.get("id") or str(abs(hash(track.get("preview_url", ""))))

    # Return cached copy if we already have a usable file
    for ext in (".mp3", ".m4a", ".opus", ".webm", ".wav"):
        existing = os.path.join(cache_dir, f"youtube_{vid_id}{ext}")
        if os.path.exists(existing) and os.path.getsize(existing) > 10000:
            return existing

    url = (track.get("preview_url") or track.get("link")
           or f"https://www.youtube.com/watch?v={vid_id}")
    outtmpl = os.path.join(cache_dir, f"youtube_{vid_id}.%(ext)s")

    has_ffmpeg = shutil.which("ffmpeg") is not None

    if has_ffmpeg:
        # With ffmpeg: always convert to MP3 — universally playable
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": outtmpl,
            "quiet": True,
            "no_warnings": True,
            "socket_timeout": timeout,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }
    else:
        # Without ffmpeg: request an already-encoded mp3 stream first,
        # then fall back to m4a (Windows MCI can play it), then anything.
        ydl_opts = {
            "format": (
                "bestaudio[ext=mp3]"
                "/bestaudio[acodec=mp3]"
                "/bestaudio[ext=m4a]"
                "/bestaudio/best"
            ),
            "outtmpl": outtmpl,
            "quiet": True,
            "no_warnings": True,
            "socket_timeout": timeout,
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            # When ffmpeg post-processes, the extension changes to .mp3
            if has_ffmpeg:
                mp3_path = os.path.splitext(filename)[0] + ".mp3"
                if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 0:
                    return mp3_path
            if os.path.exists(filename) and os.path.getsize(filename) > 0:
                return filename
            # Fallback scan for any downloaded file with this vid_id
            for ext in (".mp3", ".m4a", ".opus", ".webm", ".wav"):
                cand = os.path.join(cache_dir, f"youtube_{vid_id}{ext}")
                if os.path.exists(cand) and os.path.getsize(cand) > 0:
                    return cand
            raise OnlineError("Downloaded file could not be found.")
    except Exception as e:
        raise OnlineError(f"Could not download YouTube audio: {e}")

