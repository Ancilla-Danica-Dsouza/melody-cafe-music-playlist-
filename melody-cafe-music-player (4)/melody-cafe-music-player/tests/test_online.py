"""Online search tests. They use fake data, so no internet is needed."""
import io
import json
import os
import shutil
import tempfile
import unittest
import urllib.error

from melody_cafe.online import deezer
from melody_cafe.online import parse_results, OnlineError

SAMPLE = {"data": [
    {"id": 1, "title": "Song A", "duration": 200, "preview": "https://x/a.mp3",
     "link": "https://deezer.com/track/1", "artist": {"name": "Artist A"}, "album": {"title": "Album A"}},
    {"id": 2, "title": "No Preview", "duration": 100, "preview": "",
     "artist": {"name": "B"}, "album": {"title": "C"}},
]}


class FakeResp:
    def __init__(self, data):
        self.buf = io.BytesIO(data)

    def read(self):
        return self.buf.read()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class OnlineTests(unittest.TestCase):
    def test_parse_skips_tracks_without_preview(self):
        tracks = parse_results(SAMPLE)
        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0]["title"], "Song A")
        self.assertEqual(tracks[0]["artist"], "Artist A")
        self.assertEqual(tracks[0]["duration"], 200)

    def test_parse_error_payload(self):
        with self.assertRaises(OnlineError):
            parse_results({"error": {"message": "quota"}})

    def test_search_uses_opener(self):
        opener = lambda req, timeout=0: FakeResp(json.dumps(SAMPLE).encode())
        self.assertEqual(len(deezer.search("anything", opener=opener)), 1)

    def test_search_empty_query(self):
        self.assertEqual(deezer.search("   "), [])

    def test_search_network_failure(self):
        def boom(req, timeout=0):
            raise urllib.error.URLError("no internet")
        with self.assertRaises(OnlineError):
            deezer.search("x", opener=boom)

    def test_download_and_cache(self):
        folder = tempfile.mkdtemp()
        try:
            calls = []

            def opener(req, timeout=0):
                calls.append(1)
                return FakeResp(b"ID3fakemp3")
            track = parse_results(SAMPLE)[0]
            p1 = deezer.download_preview(track, opener=opener, cache_dir=folder)
            p2 = deezer.download_preview(track, opener=opener, cache_dir=folder)
            self.assertEqual(p1, p2)
            self.assertTrue(os.path.exists(p1))
            self.assertEqual(len(calls), 1)          # second call used the cache
        finally:
            shutil.rmtree(folder)


class BackupProviderTests(unittest.TestCase):
    def test_itunes_parse(self):
        from melody_cafe.online import itunes
        tracks = itunes.parse_results({"results": [
            {"trackId": 9, "trackName": "T", "artistName": "A", "collectionName": "C",
             "trackTimeMillis": 215000, "previewUrl": "https://x/p.m4a"},
            {"trackId": 10, "trackName": "none"}]})
        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0]["duration"], 215)
        self.assertEqual(tracks[0]["source"], "itunes")

    def test_fallback_to_itunes_when_deezer_fails(self):
        from unittest import mock
        from melody_cafe.online import itunes
        fake = [{"id": "1", "title": "x", "artist": "y", "album": "", "duration": 1,
                 "preview_url": "https://x/p.m4a", "link": "", "source": "itunes"}]
        with mock.patch.object(deezer, "search", side_effect=OnlineError("blocked")), \
             mock.patch.object(itunes, "search", return_value=fake):
            self.assertEqual(deezer.search_any("q"), fake)

    def test_both_fail_raises(self):
        from unittest import mock
        from melody_cafe.online import itunes
        with mock.patch.object(deezer, "search", side_effect=OnlineError("a")), \
             mock.patch.object(itunes, "search", side_effect=OnlineError("b")):
            with self.assertRaises(OnlineError):
                deezer.search_any("q")

    def test_m4a_extension_kept(self):
        folder = tempfile.mkdtemp()
        try:
            t = {"id": "5", "preview_url": "https://x/a/p.m4a", "source": "itunes"}
            path = deezer.download_preview(t, opener=lambda req, timeout=0: FakeResp(b"data"), cache_dir=folder)
            self.assertTrue(path.endswith("itunes_5.m4a"))
        finally:
            shutil.rmtree(folder)


class YouTubeOnlineTests(unittest.TestCase):
    def test_clean_title_and_artist(self):
        from melody_cafe.online.youtube import clean_title_and_artist
        title, artist = clean_title_and_artist("Coldplay - Yellow (Official Video)", "ColdplayVEVO")
        self.assertEqual(title, "Yellow")
        self.assertEqual(artist, "Coldplay")

        title2, artist2 = clean_title_and_artist("Espresso [Official Audio]", "Sabrina Carpenter - Topic")
        self.assertEqual(title2, "Espresso")
        self.assertEqual(artist2, "Sabrina Carpenter")

    def test_search_empty_query(self):
        from melody_cafe.online.youtube import search
        self.assertEqual(search("   "), [])

    def test_download_cached(self):
        from melody_cafe.online.youtube import download
        folder = tempfile.mkdtemp()
        try:
            cached_file = os.path.join(folder, "youtube_abc.m4a")
            with open(cached_file, "wb") as f:
                f.write(b"0" * 15000)
            t = {"id": "abc", "source": "youtube"}
            res = download(t, cache_dir=folder)
            self.assertEqual(res, cached_file)
        finally:
            shutil.rmtree(folder)


if __name__ == "__main__":
    unittest.main()
