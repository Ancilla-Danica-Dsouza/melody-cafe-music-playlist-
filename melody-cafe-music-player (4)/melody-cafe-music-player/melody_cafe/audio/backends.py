# Melody Cafe Music Player - Ancilla Danica Dsouza | PRN: 25070721021
"""Detects which audio engines exist on this computer and reads audio file lengths."""

import sys
import shutil
import wave

winsound = None               # filled in below when available
pygame = None
ctypes = None
_winmm = None

# ---------------------------------------------------------------------------
# Audio backends
# ---------------------------------------------------------------------------
NATIVE = None                 # winsound, afplay, paplay, aplay or ffplay
if sys.platform.startswith("win"):
    try:
        import winsound
        NATIVE = "winsound"
    except ImportError:
        pass
elif sys.platform == "darwin":
    if shutil.which("afplay"):
        NATIVE = "afplay"
else:
    for _tool in ("paplay", "aplay", "ffplay"):
        if shutil.which(_tool):
            NATIVE = _tool
            break

PYGAME_OK = False
PYGAME_ERROR = "pygame is not installed"
try:
    import pygame
    pygame.mixer.init()
    PYGAME_OK = True
    PYGAME_ERROR = ""
except Exception as _e:
    PYGAME_ERROR = str(_e)

MCI_OK = False                # Windows built-in media player
if sys.platform.startswith("win"):
    try:
        import ctypes
        _winmm = ctypes.windll.winmm
        MCI_OK = True
    except Exception:
        pass

AUDIO_OK = PYGAME_OK or NATIVE is not None or MCI_OK


def mci(command):
    buf = ctypes.create_unicode_buffer(255)
    err = _winmm.mciSendStringW(command, buf, 254, 0)
    return err, buf.value


def file_length_seconds(path):
    """Length of an audio file in whole seconds, or None if it cannot be read."""
    if path.lower().endswith(".wav"):
        try:
            w = wave.open(path, "rb")
            secs = int(w.getnframes() / w.getframerate())
            w.close()
            return max(secs, 1)
        except Exception:
            pass
    if PYGAME_OK:
        try:
            return max(int(pygame.mixer.Sound(path).get_length()), 1)
        except Exception:
            pass
    if MCI_OK:
        try:
            mci("close lenprobe")
            err, _ = mci('open "' + path + '" type mpegvideo alias lenprobe')
            if err == 0:
                mci("set lenprobe time format milliseconds")
                err, text = mci("status lenprobe length")
                mci("close lenprobe")
                if err == 0 and text.isdigit():
                    return max(int(text) // 1000, 1)
        except Exception:
            pass
    return None
