"""Unit tests for the doubly circular linked list (Part B)."""
import unittest

from melody_cafe.core import Playlist


def titles_forward(p):
    out = []
    if p.head is None:
        return out
    cur = p.head
    while True:
        out.append(cur.title)
        cur = cur.next
        if cur == p.head:
            return out


def titles_backward(p):
    out = []
    if p.head is None:
        return out
    tail = p.head.prev
    cur = tail
    while True:
        out.append(cur.title)
        cur = cur.prev
        if cur == tail:
            return out


class PlaylistTests(unittest.TestCase):
    def setUp(self):
        self.msgs = []
        self.p = Playlist(log=self.msgs.append)
        self.p.addSong("Sunrise", 210)
        self.p.addSong("Desert Rain", 185)
        self.p.addSong("Marina Lights", 240)

    def test_add_keeps_order(self):
        self.assertEqual(titles_forward(self.p), ["Sunrise", "Desert Rain", "Marina Lights"])

    def test_circular_links(self):
        self.assertIs(self.p.head.prev.next, self.p.head)
        self.assertIs(self.p.head.prev, self.p.find("Marina Lights"))

    def test_backward_is_reverse_of_forward(self):
        self.assertEqual(titles_backward(self.p), list(reversed(titles_forward(self.p))))

    def test_insert_after(self):
        self.p.insertAfter("Sunrise", "Skyline", 200)
        self.assertEqual(titles_forward(self.p),
                         ["Sunrise", "Skyline", "Desert Rain", "Marina Lights"])

    def test_insert_after_last_song(self):
        self.p.insertAfter("Marina Lights", "Night Drive", 195)
        self.assertEqual(titles_forward(self.p)[-1], "Night Drive")
        self.assertIs(self.p.head.prev.title == "Night Drive", True)

    def test_insert_after_missing_logs(self):
        self.assertIsNone(self.p.insertAfter("Nope", "X", 1))
        self.assertTrue(self.msgs)

    def test_remove_middle_and_head(self):
        self.assertTrue(self.p.removeSong("Desert Rain"))
        self.assertTrue(self.p.removeSong("Sunrise"))
        self.assertEqual(titles_forward(self.p), ["Marina Lights"])
        self.assertEqual(self.p.head.title, "Marina Lights")

    def test_remove_last_song_empties_list(self):
        for t in ("Sunrise", "Desert Rain", "Marina Lights"):
            self.p.removeSong(t)
        self.assertIsNone(self.p.head)
        self.assertEqual(self.p.count(), 0)

    def test_remove_unknown(self):
        self.assertFalse(self.p.removeSong("Unknown"))

    def test_play_next_wraps(self):
        self.assertEqual(self.p.playNext(self.p.find("Marina Lights")).title, "Sunrise")
        self.assertEqual(self.p.playNext(None).title, "Sunrise")

    def test_count_and_total(self):
        self.assertEqual(self.p.count(), 3)
        self.assertEqual(self.p.totalDuration(), 210 + 185 + 240)

    def test_search_and_node_at(self):
        self.assertEqual(self.p.search("rain"), 1)
        self.assertEqual(self.p.search("zzz"), -1)
        self.assertEqual(self.p.nodeAt(2).title, "Marina Lights")

    def test_random_other_is_different(self):
        cur = self.p.find("Sunrise")
        for _ in range(30):
            self.assertIsNot(self.p.randomOther(cur), cur)

    def test_title_limited_to_30_chars(self):
        n = self.p.addSong("x" * 50, 10)
        self.assertEqual(len(n.title), 30)

    def test_display_messages(self):
        self.p.displayForward()
        self.p.displayBackward()
        self.assertIn("Sunrise -> Desert Rain -> Marina Lights", self.msgs[0])
        self.assertIn("Marina Lights -> Desert Rain -> Sunrise", self.msgs[1])

    def test_empty_playlist_display(self):
        q = Playlist(log=self.msgs.append)
        q.displayForward()
        self.assertIn("empty", self.msgs[-1])


if __name__ == "__main__":
    unittest.main()
