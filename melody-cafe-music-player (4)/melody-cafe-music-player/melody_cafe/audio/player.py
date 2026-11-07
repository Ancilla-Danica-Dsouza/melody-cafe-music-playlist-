# Melody Cafe Music Player - Ancilla Danica Dsouza | PRN: 25070721021
"""The Audio class: plays one sound file at a time with whichever backend works.

Backend priority on Windows:
  1. pygame        — for .mp3 / .wav / .ogg (fastest, lowest latency)
  2. PowerShell    — for .m4a / .webm / .opus / any WMF format (online downloads)
  3. Windows MCI   — legacy fallback for .mp3 / .wav
  4. native        — winsound for .wav / afplay/ffplay on macOS/Linux

The PowerShell backend uses System.Windows.Media.MediaPlayer which is built
into every Windows 10/11 installation and handles AAC, Opus, MP3, WAV, FLAC.
"""

import os
import subprocess

from .backends import NATIVE, PYGAME_OK, MCI_OK, mci, winsound, pygame
from .ps_player import get_ps_player, ps_player_available

# Formats pygame.mixer handles reliably on Windows
_PYGAME_SAFE = frozenset((".mp3", ".wav", ".ogg", ".flac"))
# Formats Windows MCI handles (when codec is installed)
_MCI_SAFE = frozenset((".mp3", ".m4a", ".wav", ".wma", ".aac", ".mp4"))
# Formats the PowerShell WMF backend handles
_PS_SAFE = frozenset((".m4a", ".mp3", ".wav", ".webm", ".opus", ".ogg",
                       ".flac", ".aac", ".wma", ".mp4"))


class Audio:
    """Plays one sound file at a time."""
    def __init__(self):
        self.proc = None
        self.using = None   # "pygame" | "ps" | "mci" | "native"
        self.path = None
        self.volume = 0.8
        self._ps = None     # PowerShellPlayer instance (lazy)

    # ── helpers ──────────────────────────────────────────────────────────────

    def _ext(self, path):
        return os.path.splitext(path)[1].lower()

    def _ps_player(self):
        """Return the PowerShell player, creating it if needed."""
        if self._ps is None or not self._ps.is_alive():
            self._ps = get_ps_player()
        return self._ps

    def _native_play(self, path):
        if NATIVE == "winsound":
            winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            return
        if NATIVE == "afplay":
            cmd = ["afplay", path]
        elif NATIVE == "paplay":
            cmd = ["paplay", path]
        elif NATIVE == "aplay":
            cmd = ["aplay", "-q", path]
        else:
            cmd = ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path]
        self.proc = subprocess.Popen(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

    # ── public API ───────────────────────────────────────────────────────────

    def set_volume(self, v):
        """v is 0.0–1.0. Returns True if the current backend supports it."""
        self.volume = max(0.0, min(1.0, v))
        if self.using == "pygame":
            pygame.mixer.music.set_volume(self.volume)
            return True
        if self.using == "ps" and self._ps:
            self._ps.set_volume(self.volume)
            return True
        if self.using == "mci":
            mci("setaudio song volume to " + str(int(self.volume * 1000)))
            return True
        return False

    def seek(self, seconds):
        """Seek to a timestamp. Returns True if supported."""
        if self.using == "pygame":
            try:
                pygame.mixer.music.set_pos(seconds)
                return True
            except Exception:
                pass
        elif self.using == "ps" and self._ps:
            try:
                self._ps.seek(seconds)
                return True
            except Exception:
                pass
        elif self.using == "mci":
            try:
                mci(f"seek song to {int(seconds * 1000)}")
                mci("play song")
                return True
            except Exception:
                pass
        return False

    def play(self, path):
        """Play an audio file. Returns a string describing the backend used."""
        self.stop()
        self.path = path
        ext = self._ext(path)
        is_wav = ext == ".wav"

        # ── 1. pygame — fastest, best for .mp3/.wav ───────────────────────
        if PYGAME_OK and ext in _PYGAME_SAFE:
            try:
                pygame.mixer.music.load(path)
                pygame.mixer.music.play()
                self.using = "pygame"
                self.set_volume(self.volume)
                return "pygame"
            except Exception:
                pass  # fall through

        # ── 2. PowerShell WMF — handles .m4a, .webm, .opus, etc. ─────────
        if ext in _PS_SAFE and ps_player_available():
            try:
                ps = self._ps_player()
                if ps.play(path):
                    self.using = "ps"
                    ps.set_volume(self.volume)
                    return "PowerShell MediaPlayer"
            except Exception:
                pass  # fall through

        # ── 3. Windows MCI legacy fallback ────────────────────────────────
        if MCI_OK:
            try:
                if is_wav:
                    err, _ = mci('open "' + path + '" alias song')
                elif ext in _MCI_SAFE:
                    err, _ = mci('open "' + path + '" type mpegvideo alias song')
                else:
                    err, _ = mci('open "' + path + '" alias song')
                if err == 0:
                    mci("play song")
                    self.using = "mci"
                    self.set_volume(self.volume)
                    return "Windows media player"
                mci("close song")
            except Exception:
                pass

        # ── 4. Native winsound (wav only on Windows) ─────────────────────
        if is_wav and NATIVE:
            self._native_play(path)
            self.using = "native"
            return "system player (" + NATIVE + ")"

        # ── 5. pygame last-ditch (any format, may error) ─────────────────
        if PYGAME_OK:
            try:
                pygame.mixer.music.load(path)
                pygame.mixer.music.play()
                self.using = "pygame"
                self.set_volume(self.volume)
                return "pygame"
            except Exception:
                pass

        # ── 6. ffplay/afplay on non-Windows ──────────────────────────────
        if NATIVE in ("afplay", "ffplay"):
            self._native_play(path)
            self.using = "native"
            return "system player (" + NATIVE + ")"

        raise RuntimeError(
            "Cannot play this audio format. "
            "Install ffmpeg (https://ffmpeg.org) for broadest format support."
        )

    def stop(self):
        if self.using == "pygame" and PYGAME_OK:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
        if self.using == "ps" and self._ps:
            try:
                self._ps.stop()
            except Exception:
                pass
        if MCI_OK:
            try:
                mci("stop song")
                mci("close song")
            except Exception:
                pass
        if NATIVE == "winsound":
            try:
                winsound.PlaySound(None, winsound.SND_PURGE)
            except Exception:
                pass
        if self.proc is not None:
            try:
                self.proc.terminate()
            except Exception:
                pass
            self.proc = None
        self.using = None

    def pause(self):
        if self.using == "pygame":
            pygame.mixer.music.pause()
        elif self.using == "ps" and self._ps:
            self._ps.pause()
        elif self.using == "mci":
            mci("pause song")
        else:
            self.stop()   # system players: restart on resume

    def resume(self):
        if self.using == "pygame":
            pygame.mixer.music.unpause()
        elif self.using == "ps" and self._ps:
            self._ps.resume()
        elif self.using == "mci":
            mci("resume song")
        elif self.path:
            self._native_play(self.path)
