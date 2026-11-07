# Melody Cafe Music Player - Ancilla Danica Dsouza | PRN: 25070721021
"""Online music through Deezer's free public API (no account, no API key), with iTunes as backup.

  Deezer search : https://api.deezer.com/search?q=<text>        (30 second .mp3 previews)
  iTunes search : https://itunes.apple.com/search?term=<text>   (30 second .m4a previews)

Only the Python standard library is used (urllib), so nothing extra to install.
"""

import os
import json
import urllib.parse
import urllib.request

from .common import OnlineError, fetch_bytes, CACHE_DIR
from . import itunes

API_URL = "https://api.deezer.com/search"
PREVIEW_SECONDS = 30


def parse_results(payload):
    """Turn Deezer's JSON into a clean list of track dictionaries.
    Tracks without a preview link are skipped (they cannot be played)."""
    if not isinstance(payload, dict):
        raise OnlineError("Unexpected answer from the music service.")
    if "error" in payload:
        err = payload["error"]
        msg = err.get("message", "unknown error") if isinstance(err, dict) else str(err)
        raise OnlineError("Music service said: " + msg)
    tracks = []
    for item in payload.get("data", []):
        preview = item.get("preview") or ""
        if not preview:
            continue
        artist = item.get("artist") or {}
        album = item.get("album") or {}
        tracks.append({
            "id": str(item.get("id", "")),
            "title": item.get("title", "Unknown"),
            "artist": artist.get("name", "Unknown"),
            "album": album.get("title", ""),
            "duration": int(item.get("duration", 0) or 0),    # full song length
            "preview_url": preview,
            "link": item.get("link", ""),
            "source": "deezer",
        })
    return tracks


def search(query, limit=25, timeout=10, opener=urllib.request.urlopen):
    """Search Deezer only. Returns a list of track dictionaries."""
    query = query.strip()
    if not query:
        return []
    url = API_URL + "?" + urllib.parse.urlencode({"q": query, "limit": int(limit)})
    data = fetch_bytes(url, timeout, opener)
    try:
        return parse_results(json.loads(data.decode("utf-8")))
    except ValueError as e:
        raise OnlineError("Unreadable answer from Deezer: " + str(e))


def search_any(query, limit=25, timeout=10):
    """Try Deezer first; if it fails or finds nothing, try iTunes."""
    problems = []
    try:
        tracks = search(query, limit, timeout)
        if tracks:
            return tracks
        problems.append("Deezer: no playable results")
    except OnlineError as e:
        problems.append("Deezer: " + str(e))
    try:
        tracks = itunes.search(query, limit, timeout)
        if tracks:
            return tracks
        problems.append("iTunes: no playable results")
    except OnlineError as e:
        problems.append("iTunes: " + str(e))
    if all("no playable" in p for p in problems):
        return []
    raise OnlineError("  |  ".join(problems))


def download_preview(track, timeout=20, opener=urllib.request.urlopen, cache_dir=None):
    """Download the 30 second preview once and keep it in a cache folder.
    Returns the local file path (.mp3 or .m4a)."""
    cache_dir = cache_dir or CACHE_DIR
    os.makedirs(cache_dir, exist_ok=True)
    ext = os.path.splitext(urllib.parse.urlparse(track["preview_url"]).path)[1].lower()
    if ext not in (".mp3", ".m4a", ".aac", ".mp4"):
        ext = ".mp3"
    name = track.get("source", "deezer") + "_" + (track["id"] or str(abs(hash(track["preview_url"])))) + ext
    path = os.path.join(cache_dir, name)
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return path
    data = fetch_bytes(track["preview_url"], timeout, opener)
    if not data:
        raise OnlineError("The preview file was empty.")
    tmp = path + ".part"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, path)
    return path
