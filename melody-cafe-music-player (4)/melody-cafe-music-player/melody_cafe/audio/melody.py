# Melody Cafe Music Player - Ancilla Danica Dsouza | PRN: 25070721021
"""Makes a small melody (.wav) from a song title, so songs without a real file still play."""

import os
import math
import random
import struct
import wave
import tempfile


def make_melody_file(title, seconds):
    """Songs without a real audio file get a melody made from the title.
    The same title always gives the same tune."""
    seconds = int(min(max(seconds, 3), 600))
    safe = ""
    for ch in title:
        safe += ch if ch.isalnum() else "_"
    path = os.path.join(tempfile.gettempdir(), "melody_cafe_" + safe + "_" + str(seconds) + ".wav")
    if os.path.exists(path):
        return path
    rate = 22050
    rnd = random.Random(title)
    scale = (261.63, 293.66, 329.63, 392.00, 440.00, 523.25, 587.33)
    note_len = int(rate * 0.35)
    phrase = bytearray()
    for _ in range(16):
        f = rnd.choice(scale)
        for k in range(note_len):
            t = k / rate
            env = min(1.0, k / 300.0) * (1.0 - k / note_len) ** 0.6
            v = math.sin(2 * math.pi * f * t) + 0.4 * math.sin(4 * math.pi * f * t)
            phrase += struct.pack("<h", int(14000 * env * v))
    repeats = int(seconds / (16 * 0.35)) + 1
    w = wave.open(path, "wb")
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(rate)
    w.writeframes(bytes(phrase) * repeats)
    w.close()
    return path
