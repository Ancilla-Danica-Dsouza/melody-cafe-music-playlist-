"""Tests for helpers, themes and melody generation (no GUI or sound card needed)."""
import os
import unittest
import wave

from melody_cafe.utils import fmt
from melody_cafe.audio.melody import make_melody_file
from melody_cafe.ui.themes import THEMES
from melody_cafe.ui.colors import mix, derive

REQUIRED = ("bg", "panel", "text", "muted", "accent", "button", "btn_text",
            "sel", "sel_text", "log", "deco", "tagline", "stripe")


class MiscTests(unittest.TestCase):
    def test_fmt(self):
        self.assertEqual(fmt(0), "0:00")
        self.assertEqual(fmt(65), "1:05")
        self.assertEqual(fmt(210), "3:30")

    def test_every_theme_has_all_keys(self):
        for name, t in THEMES.items():
            for key in REQUIRED:
                self.assertIn(key, t, name + " is missing " + key)
            derive(t)

    def test_uae_themes_exist(self):
        uae = [n for n in THEMES if n.startswith("UAE - ")]
        self.assertGreaterEqual(len(uae), 6)

    def test_mix(self):
        self.assertEqual(mix("#000000", "#ffffff", 0), "#000000")
        self.assertEqual(mix("#000000", "#ffffff", 1), "#ffffff")

    def test_melody_file_is_valid_and_repeatable(self):
        a = make_melody_file("UnitTestSong", 4)
        b = make_melody_file("UnitTestSong", 4)
        self.assertEqual(a, b)
        self.assertTrue(os.path.exists(a))
        w = wave.open(a, "rb")
        self.assertGreaterEqual(w.getnframes() / w.getframerate(), 4)
        w.close()


if __name__ == "__main__":
    unittest.main()
