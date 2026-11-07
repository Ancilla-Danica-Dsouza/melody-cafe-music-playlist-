"""Tests for clipping, saving copies, Jamendo parsing and download modes (no internet needed)."""
import os
import shutil
import tempfile
import unittest
import wave
from unittest import mock

from melody_cafe.audio import clip
from melody_cafe.audio.clip import clip_audio, export_song, ClipError
from melody_cafe.audio.melody import make_melody_file
from melody_cafe.online import jamendo, download_track, search_sources, OnlineError
from melody_cafe.online import deezer


def fake_mp3(seconds=26, kbps=128):
    """Constant bitrate MPEG-1 Layer 3 frames (44.1 kHz): header FF FB 90 00, 417 bytes each."""
    frame = bytes([0xFF, 0xFB, 0x90, 0x00]) + bytes(413)
    count = int(seconds * kbps * 125 / 417) + 1
    return b"ID3\x03\x00\x00\x00\x00\x00\x00" + frame * count


class FakeResp:
    def __init__(self, data):
        self.data = data

    def read(self):
        return self.data

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class ClipTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir)

    def secs(self, path):
        w = wave.open(path, "rb")
        n = w.getnframes() / w.getframerate()
        w.close()
        return n

    def test_wav_clip_is_10_seconds(self):
        src = make_melody_file("ClipTestSong", 30)
        dst = os.path.join(self.dir, "c.wav")
        clip_audio(src, dst, 10)
        self.assertAlmostEqual(self.secs(dst), 10, delta=0.1)

    def test_mp3_clip_by_bytes(self):
        src = os.path.join(self.dir, "a.mp3")
        with open(src, "wb") as f:
            f.write(fake_mp3(26))
        dst = os.path.join(self.dir, "b.mp3")
        with mock.patch.object(clip.shutil, "which", return_value=None):
            clip_audio(src, dst, 10)
        size = os.path.getsize(dst)
        self.assertAlmostEqual(size, 160000, delta=900)       # about 10 s at 128 kbps
        with open(dst, "rb") as f:
            self.assertEqual(f.read(2), b"\xff\xfb")      # starts on a frame

    def test_short_file_is_copied_whole(self):
        src = os.path.join(self.dir, "s.mp3")
        with open(src, "wb") as f:
            f.write(fake_mp3(5))
        dst = os.path.join(self.dir, "t.mp3")
        with mock.patch.object(clip.shutil, "which", return_value=None):
            clip_audio(src, dst, 10)
        self.assertGreater(os.path.getsize(dst), 70000)

    def test_unknown_format_without_ffmpeg(self):
        src = os.path.join(self.dir, "x.m4a")
        with open(src, "wb") as f:
            f.write(b"data")
        with mock.patch.object(clip.shutil, "which", return_value=None):
            with self.assertRaises(ClipError):
                clip_audio(src, os.path.join(self.dir, "y.m4a"), 10)

    def test_export_full_and_10s(self):
        src = make_melody_file("ExportTest", 30)
        out = os.path.join(self.dir, "out")
        full = export_song(src, "My: Song?", "full", out)
        tiny = export_song(src, "My: Song?", "10s", out)
        again = export_song(src, "My: Song?", "full", out)
        self.assertAlmostEqual(self.secs(full), self.secs(src), delta=0.1)
        self.assertAlmostEqual(self.secs(tiny), 10, delta=0.1)
        self.assertNotEqual(full, again)                       # never overwrites
        self.assertIn("(10 sec)", tiny)

    def test_export_missing_file(self):
        with self.assertRaises(ClipError):
            export_song("/no/such/file.mp3", "x", "full", self.dir)


class JamendoAndDownloadTests(unittest.TestCase):
    PAYLOAD = {"headers": {"status": "success"}, "results": [
        {"id": "7", "name": "Free Song", "artist_name": "Indie", "album_name": "A", "duration": "192",
         "audio": "https://j/stream.mp3", "audiodownload": "https://j/dl/7/mp32/",
         "audiodownload_allowed": True, "shareurl": "https://jamendo.com/track/7"},
        {"id": "8", "name": "Stream only", "artist_name": "X", "duration": "100",
         "audio": "https://j/s8.mp3", "audiodownload": "", "audiodownload_allowed": False},
        {"id": "9", "name": "no url", "audio": "", "audiodownload": ""}]}

    def test_parse(self):
        t = jamendo.parse_results(self.PAYLOAD)
        self.assertEqual(len(t), 2)
        self.assertTrue(t[0]["full"])
        self.assertEqual(t[0]["duration"], 192)
        self.assertEqual(t[0]["preview_url"], "https://j/dl/7/mp32/")
        self.assertEqual(t[1]["preview_url"], "https://j/s8.mp3")       # download not allowed -> stream

    def test_parse_error(self):
        with self.assertRaises(OnlineError):
            jamendo.parse_results({"headers": {"status": "failed", "error_message": "bad id"}})

    def test_search_needs_key(self):
        with mock.patch.object(jamendo, "get_key", return_value=None):
            with self.assertRaises(OnlineError):
                jamendo.search("x")

    def test_key_roundtrip(self):
        d = tempfile.mkdtemp()
        try:
            p = os.path.join(d, "sub", "k.txt")
            jamendo.save_key("  abc123 ", p)
            with open(p) as f:
                self.assertEqual(f.read(), "abc123")
        finally:
            shutil.rmtree(d)

    def test_download_full_vs_10s(self):
        d = tempfile.mkdtemp()
        try:
            track = {"id": "7", "title": "t", "artist": "a", "duration": 192, "full": True,
                     "preview_url": "https://j/dl/7/mp32/", "source": "jamendo"}
            op = lambda req, timeout=0: FakeResp(fake_mp3(26))
            with mock.patch.object(clip.shutil, "which", return_value=None):
                p_full, s_full = download_track(track, "full", opener=op, cache_dir=d)
                p_10, s_10 = download_track(track, "10s", opener=op, cache_dir=d)
            self.assertEqual(s_full, 192)
            self.assertEqual(s_10, 10)
            self.assertTrue(p_10.endswith("_10s.mp3"))
            self.assertLess(os.path.getsize(p_10), os.path.getsize(p_full))
        finally:
            shutil.rmtree(d)

    def test_preview_track_full_means_30s(self):
        d = tempfile.mkdtemp()
        try:
            track = {"id": "1", "preview_url": "https://x/a.mp3", "source": "deezer", "duration": 240}
            _, secs = download_track(track, "full", opener=lambda r, timeout=0: FakeResp(fake_mp3(5)), cache_dir=d)
            self.assertEqual(secs, 30)
        finally:
            shutil.rmtree(d)

    def test_search_sources_without_key_gives_notice(self):
        prev = [{"id": "1", "title": "p", "artist": "a", "duration": 1, "preview_url": "u", "source": "deezer"}]
        with mock.patch.object(jamendo, "get_key", return_value=None), \
             mock.patch("melody_cafe.online.search", return_value=prev):
            tracks, notice = search_sources("q", prefer_full=True)
        self.assertEqual(tracks, prev)
        self.assertIn("Jamendo key", notice)

    def test_search_sources_uses_jamendo_when_key(self):
        full = [{"id": "7", "title": "f", "artist": "a", "duration": 200, "full": True,
                 "preview_url": "u", "source": "jamendo"}]
        with mock.patch.object(jamendo, "get_key", return_value="k"), \
             mock.patch.object(jamendo, "search", return_value=full):
            tracks, notice = search_sources("q", prefer_full=True)
        self.assertEqual(tracks, full)
        self.assertEqual(notice, "")


if __name__ == "__main__":
    unittest.main()
