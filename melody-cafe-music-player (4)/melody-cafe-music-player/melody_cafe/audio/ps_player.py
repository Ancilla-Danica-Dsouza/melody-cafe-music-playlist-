# Melody Cafe Music Player - Ancilla Danica Dsouza | PRN: 25070721021
"""PowerShell MediaPlayer backend for Windows.
Uses System.Windows.Media.MediaPlayer via a persistent PowerShell process.
Supports: .m4a, .mp3, .wav, .webm, .ogg, .flac — anything Windows Media Foundation handles.
"""

import sys
import os
import subprocess
import threading
import queue
import time

# Only available on Windows
PS_PLAYER_OK = sys.platform.startswith("win") and bool(
    subprocess.run(
        ["powershell", "-Command", "echo ok"],
        capture_output=True, timeout=5
    ).returncode == 0
) if sys.platform.startswith("win") else False


# PowerShell script that runs as a persistent controller
_PS_CONTROLLER = r"""
Add-Type -AssemblyName presentationCore
$player = New-Object System.Windows.Media.MediaPlayer
$player.Volume = 0.8

function Send-Status($msg) {
    Write-Output $msg
    [Console]::Out.Flush()
}

Send-Status "READY"

while ($true) {
    $line = [Console]::ReadLine()
    if ($null -eq $line) { break }
    $line = $line.Trim()
    if ($line -eq "") { continue }

    $parts = $line -split " ", 2
    $cmd = $parts[0].ToUpper()

    switch ($cmd) {
        "PLAY" {
            $uri = [uri]($parts[1].Trim())
            $player.Open($uri)
            Start-Sleep -Milliseconds 600
            $player.Play()
            Send-Status "PLAYING"
        }
        "PAUSE" {
            $player.Pause()
            Send-Status "PAUSED"
        }
        "RESUME" {
            $player.Play()
            Send-Status "PLAYING"
        }
        "STOP" {
            $player.Stop()
            $player.Close()
            Send-Status "STOPPED"
        }
        "VOLUME" {
            $vol = [double]($parts[1].Trim())
            $player.Volume = $vol
            Send-Status "VOL_OK"
        }
        "SEEK" {
            $secs = [double]($parts[1].Trim())
            $player.Position = [TimeSpan]::FromSeconds($secs)
            Send-Status "SEEK_OK"
        }
        "POS" {
            $pos = $player.Position.TotalSeconds
            Send-Status "POS $pos"
        }
        "QUIT" {
            $player.Stop()
            $player.Close()
            Send-Status "BYE"
            break
        }
    }
}
"""


class PowerShellPlayer:
    """Wraps a persistent PowerShell MediaPlayer process for low-latency audio control."""

    def __init__(self):
        self._proc = None
        self._reader_thread = None
        self._resp_queue = queue.Queue()
        self._lock = threading.Lock()
        self._start_process()

    def _start_process(self):
        try:
            self._proc = subprocess.Popen(
                ["powershell", "-WindowStyle", "Hidden", "-NonInteractive",
                 "-NoProfile", "-Command", _PS_CONTROLLER],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                bufsize=1,
            )
            self._reader_thread = threading.Thread(
                target=self._reader, daemon=True
            )
            self._reader_thread.start()
            # Wait for READY signal
            self._wait_response("READY", timeout=8)
        except Exception:
            self._proc = None

    def _reader(self):
        try:
            for line in self._proc.stdout:
                line = line.strip()
                if line:
                    self._resp_queue.put(line)
        except Exception:
            pass

    def _send(self, command):
        if not self._proc or self._proc.poll() is not None:
            self._start_process()
        if self._proc:
            try:
                self._proc.stdin.write(command + "\n")
                self._proc.stdin.flush()
            except Exception:
                pass

    def _wait_response(self, prefix=None, timeout=3):
        try:
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                remaining = deadline - time.monotonic()
                try:
                    resp = self._resp_queue.get(timeout=min(remaining, 0.2))
                    if prefix is None or resp.startswith(prefix):
                        return resp
                except queue.Empty:
                    continue
        except Exception:
            pass
        return None

    def is_alive(self):
        return self._proc is not None and self._proc.poll() is None

    def play(self, path):
        """Play a file. path must be an absolute local path."""
        # Convert to file:// URI that PowerShell MediaPlayer expects
        uri = path.replace("\\", "/")
        if not uri.startswith("/"):
            uri = "/" + uri
        uri = "file://" + uri
        with self._lock:
            self._send(f"PLAY {uri}")
            return self._wait_response("PLAYING", timeout=5) is not None

    def pause(self):
        with self._lock:
            self._send("PAUSE")
            self._wait_response("PAUSED", timeout=2)

    def resume(self):
        with self._lock:
            self._send("RESUME")
            self._wait_response("PLAYING", timeout=2)

    def stop(self):
        with self._lock:
            self._send("STOP")
            self._wait_response("STOPPED", timeout=2)

    def set_volume(self, v):
        """v is 0.0 to 1.0."""
        with self._lock:
            self._send(f"VOLUME {v:.3f}")
            self._wait_response("VOL_OK", timeout=1)

    def seek(self, seconds):
        with self._lock:
            self._send(f"SEEK {seconds:.2f}")
            self._wait_response("SEEK_OK", timeout=2)

    def position(self):
        """Returns current position in seconds, or 0.0."""
        with self._lock:
            self._send("POS")
            resp = self._wait_response("POS ", timeout=1)
            if resp and resp.startswith("POS "):
                try:
                    return float(resp[4:])
                except ValueError:
                    pass
        return 0.0

    def close(self):
        try:
            with self._lock:
                self._send("QUIT")
                time.sleep(0.3)
            if self._proc:
                self._proc.terminate()
        except Exception:
            pass
        self._proc = None


# Singleton instance (created lazily)
_ps_player = None


def get_ps_player():
    global _ps_player
    if _ps_player is None or not _ps_player.is_alive():
        _ps_player = PowerShellPlayer()
    return _ps_player


def ps_player_available():
    """Returns True if the PowerShell MediaPlayer backend works on this system."""
    if not PS_PLAYER_OK:
        return False
    try:
        p = get_ps_player()
        return p.is_alive()
    except Exception:
        return False

