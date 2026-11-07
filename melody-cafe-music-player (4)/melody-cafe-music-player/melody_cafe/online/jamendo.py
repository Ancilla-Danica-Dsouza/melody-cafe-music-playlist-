# Melody Cafe Music Player - Ancilla Danica Dsouza | PRN: 25070721021
"""Jamendo: free, legal FULL-LENGTH songs (Creative Commons music from independent artists).

Needs a free developer key (client_id):
  1. Make a free account at https://devportal.jamendo.com
  2. Create an application, copy its Client ID
  3. In the app: Online music -> "Set Jamendo key"   (or set env var JAMENDO_CLIENT_ID)
"""

import json
import os
import urllib.parse
import urllib.request

from .common import OnlineError, fetch_bytes

API_URL = "https://api.jamendo.com/v3.0/tracks/"
KEY_FILE = os.path.join(os.path.expanduser("~"), ".melody_cafe", "jamendo_key.txt")


def get_key():
    key = os.environ.get("JAMENDO_CLIENT_ID", "").strip()
    if key:
        return key
    try:
        with open(KEY_FILE, "r", encoding="utf-8") as f:
            return f.read().strip() or None
    except OSError:
        return None


def save_key(key, path=None):
    path = path or KEY_FILE
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(key.strip())


def parse_results(payload):
    if not isinstance(payload, dict):
        raise OnlineError("Unexpected answer from Jamendo.")
    headers = payload.get("headers") or {}
    if headers.get("status", "success") != "success":
        raise OnlineError("Jamendo said: " + str(headers.get("error_message") or "request failed"))
    tracks = []
    for item in payload.get("results", []):
        allowed = item.get("audiodownload_allowed", True)
        url = (item.get("audiodownload") if allowed else "") or item.get("audio") or ""
        if not url:
            continue
        try:
            duration = int(float(item.get("duration", 0) or 0))
        except ValueError:
            duration = 0
        tracks.append({
            "id": str(item.get("id", "")),
            "title": item.get("name", "Unknown"),
            "artist": item.get("artist_name", "Unknown"),
            "album": item.get("album_name", ""),
            "duration": duration,
            "preview_url": url,                 # for Jamendo this is the FULL song
            "link": item.get("shareurl", ""),
            "source": "jamendo",
            "full": True,
        })
    return tracks


def search(query, limit=25, timeout=15, opener=urllib.request.urlopen, key=None):
    key = key or get_key()
    if not key:
        raise OnlineError("No Jamendo key set.")
    query = query.strip()
    if not query:
        return []
    url = API_URL + "?" + urllib.parse.urlencode({
        "client_id": key, "format": "json", "limit": int(limit), "search": query})
    data = fetch_bytes(url, timeout, opener)
    try:
        return parse_results(json.loads(data.decode("utf-8")))
    except ValueError as e:
        raise OnlineError("Unreadable answer from Jamendo: " + str(e))
