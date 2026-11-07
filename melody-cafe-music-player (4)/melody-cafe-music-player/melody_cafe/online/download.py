# Melody Cafe Music Player - Ancilla Danica Dsouza | PRN: 25070721021
"""Download an online track as the FULL song or a 10 second clip."""

import os
import urllib.request

from ..audio.clip import clip_audio, CLIP_SECONDS
from .deezer import download_preview, PREVIEW_SECONDS
from . import youtube


def available_seconds(track):
    """How long the downloadable file is: whole song for Jamendo/YouTube, 30 s preview for Deezer / iTunes."""
    if track.get("full") and track.get("duration"):
        return track["duration"]
    return PREVIEW_SECONDS


def download_track(track, mode="full", timeout=90, opener=urllib.request.urlopen, cache_dir=None):
    """Returns (local_path, seconds). mode is "full" or "10s"."""
    if track.get("source") == "youtube":
        path = youtube.download(track, timeout=timeout, cache_dir=cache_dir)
    else:
        path = download_preview(track, timeout=timeout, opener=opener, cache_dir=cache_dir)
    total = available_seconds(track)
    if mode == "10s" and total > CLIP_SECONDS:
        stem, ext = os.path.splitext(path)
        clip = stem + "_10s" + ext
        if not (os.path.exists(clip) and os.path.getsize(clip) > 0):
            clip_audio(path, clip, CLIP_SECONDS)
        return clip, CLIP_SECONDS
    return path, total
