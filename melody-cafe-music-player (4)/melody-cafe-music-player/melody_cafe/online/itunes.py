# Melody Cafe Music Player - Ancilla Danica Dsouza | PRN: 25070721021
"""Backup provider: Apple's free iTunes Search API (no key). 30 second previews (.m4a)."""

import json
import urllib.parse
import urllib.request

from .common import OnlineError, fetch_bytes

API_URL = "https://itunes.apple.com/search"


def parse_results(payload):
    if not isinstance(payload, dict):
        raise OnlineError("Unexpected answer from iTunes.")
    tracks = []
    for item in payload.get("results", []):
        preview = item.get("previewUrl") or ""
        if not preview:
            continue
        tracks.append({
            "id": str(item.get("trackId", "")),
            "title": item.get("trackName", "Unknown"),
            "artist": item.get("artistName", "Unknown"),
            "album": item.get("collectionName", ""),
            "duration": int((item.get("trackTimeMillis") or 0) // 1000),
            "preview_url": preview,
            "link": item.get("trackViewUrl", ""),
            "source": "itunes",
        })
    return tracks


def search(query, limit=25, timeout=10, opener=urllib.request.urlopen):
    query = query.strip()
    if not query:
        return []
    url = API_URL + "?" + urllib.parse.urlencode(
        {"term": query, "media": "music", "entity": "song", "limit": int(limit)})
    data = fetch_bytes(url, timeout, opener)
    try:
        return parse_results(json.loads(data.decode("utf-8")))
    except ValueError as e:
        raise OnlineError("Unreadable answer from iTunes: " + str(e))
