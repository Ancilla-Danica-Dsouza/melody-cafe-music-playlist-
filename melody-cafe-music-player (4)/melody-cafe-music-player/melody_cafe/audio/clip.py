# Melody Cafe Music Player - Ancilla Danica Dsouza | PRN: 25070721021
"""Cut a short clip out of a song, and save a copy (full song or 10 second clip) to a folder.

  .wav          cut exactly with Python's wave module
  .mp3          cut with ffmpeg if installed, otherwise cut by bytes (works well for normal mp3 files)
  .m4a / other  needs ffmpeg
"""

import os
import shutil
import subprocess
import wave

CLIP_SECONDS = 10

_BITRATES_MPEG1 = (0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320)
_BITRATES_MPEG2 = (0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160)


class ClipError(Exception):
    """Raised with a friendly message when a clip or copy cannot be made."""


def _is_sync(data, i):
    return i + 1 < len(data) and data[i] == 0xFF and (data[i + 1] & 0xE0) == 0xE0


def _mp3_start(data):
    """Index of the first audio frame (skips an ID3v2 tag)."""
    i = 0
    if data[:3] == b"ID3" and len(data) > 10:
        size = (data[6] & 0x7F) << 21 | (data[7] & 0x7F) << 14 | (data[8] & 0x7F) << 7 | (data[9] & 0x7F)
        i = 10 + size
    while i < len(data) - 1 and not _is_sync(data, i):
        i += 1
    return i


def _mp3_bytes_per_second(data, start):
    """Bytes of audio per second from the first frame header (assumes constant bitrate)."""
    try:
        b1, b2 = data[start + 1], data[start + 2]
        version = (b1 >> 3) & 3
        layer = (b1 >> 1) & 3
        idx = (b2 >> 4) & 15
        if layer == 1 and 0 < idx < 15:
            table = _BITRATES_MPEG1 if version == 3 else _BITRATES_MPEG2
            return table[idx] * 125
    except IndexError:
        pass
    return 16000                                    # assume 128 kbps


def _clip_wav(src, dst, seconds):
    w = wave.open(src, "rb")
    try:
        rate = w.getframerate()
        frames = w.readframes(min(int(rate * seconds), w.getnframes()))
        params = w.getparams()
    finally:
        w.close()
    out = wave.open(dst, "wb")
    try:
        out.setparams(params)
        out.writeframes(frames)
    finally:
        out.close()


def _clip_mp3_bytes(src, dst, seconds):
    with open(src, "rb") as f:
        data = f.read()
    start = _mp3_start(data)
    end = start + int(_mp3_bytes_per_second(data, start) * seconds)
    if end >= len(data):
        shutil.copyfile(src, dst)                   # already shorter than the clip
        return
    while end < len(data) and not _is_sync(data, end):   # finish on a frame boundary
        end += 1
    with open(dst, "wb") as f:
        f.write(data[start:end])


def _clip_ffmpeg(src, dst, seconds):
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-t", str(seconds), "-c", "copy", dst]
    r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if r.returncode != 0 or not os.path.exists(dst) or os.path.getsize(dst) == 0:
        raise ClipError("ffmpeg could not cut this file: " + r.stderr.decode("utf-8", "ignore")[:200])


def clip_audio(src, dst, seconds=CLIP_SECONDS):
    """Write the first `seconds` of src to dst (same format)."""
    ext = os.path.splitext(src)[1].lower()
    try:
        if ext == ".wav":
            _clip_wav(src, dst, seconds)
        elif shutil.which("ffmpeg"):
            _clip_ffmpeg(src, dst, seconds)
        elif ext == ".mp3":
            _clip_mp3_bytes(src, dst, seconds)
        else:
            raise ClipError("Cutting a " + (ext or "this") + " file into a 10 second clip needs ffmpeg "
                            "(install it from ffmpeg.org). mp3 and wav files work without it.")
    except (OSError, wave.Error) as e:
        raise ClipError("Could not make the clip: " + str(e))
    return dst


def safe_name(text):
    out = ""
    for ch in text:
        out += ch if (ch.isalnum() or ch in " -_().") else "_"
    return out.strip() or "song"


def unique_path(folder, base, ext):
    path = os.path.join(folder, base + ext)
    n = 1
    while os.path.exists(path):
        path = os.path.join(folder, base + " (" + str(n) + ")" + ext)
        n += 1
    return path


def export_song(src, name, mode, folder):
    """Save a copy of src into folder. mode is "full" (whole song) or "10s" (first 10 seconds).
    Returns the new file path."""
    if not os.path.exists(src):
        raise ClipError("The song file was not found: " + src)
    os.makedirs(folder, exist_ok=True)
    ext = os.path.splitext(src)[1] or ".mp3"
    if mode == "10s":
        dst = unique_path(folder, safe_name(name) + " (10 sec)", ext)
        return clip_audio(src, dst, CLIP_SECONDS)
    dst = unique_path(folder, safe_name(name), ext)
    try:
        shutil.copy2(src, dst)
    except OSError as e:
        raise ClipError("Could not save the file: " + str(e))
    return dst
