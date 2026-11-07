# Melody Cafe Music Player - Ancilla Danica Dsouza | PRN: 25070721021

"""PART B: doubly circular linked list.
last song's next -> first song, first song's prev -> last song"""

import random

from .song import Song


class Playlist:
    def __init__(self, log=print):
        self.head = None                 # first song (last song is head.prev)
        self.log = log

    def find(self, title):
        if self.head is None:
            return None
        cur = self.head
        while True:
            if cur.title == title:
                return cur
            cur = cur.next
            if cur == self.head:
                return None

    def addSong(self, title, duration, audio_file=None):
        node = Song(title, duration, audio_file)
        if self.head is None:
            node.next = node
            node.prev = node
            self.head = node
        else:
            tail = self.head.prev
            node.prev = tail
            node.next = self.head
            tail.next = node
            self.head.prev = node
        return node

    def insertAfter(self, key, title, duration, audio_file=None):
        target = self.find(key)
        if target is None:
            self.log("Song '" + key + "' not found. Cannot insert '" + title + "'.")
            return None
        node = Song(title, duration, audio_file)
        node.prev = target
        node.next = target.next
        target.next.prev = node
        target.next = node
        return node

    def removeSong(self, title):
        node = self.find(title)
        if node is None:
            self.log("Song '" + title + "' not found. Nothing removed.")
            return False
        if node.next == node:
            self.head = None
        else:
            node.prev.next = node.next
            node.next.prev = node.prev
            if node == self.head:
                self.head = node.next
        node.next = None
        node.prev = None
        return True

    def displayForward(self):
        if self.head is None:
            text = "Playlist is empty."
        else:
            text = ""
            cur = self.head
            while True:
                text += cur.title
                cur = cur.next
                if cur == self.head:
                    break
                text += " -> "
        self.log("Forward : " + text)

    def displayBackward(self):
        if self.head is None:
            text = "Playlist is empty."
        else:
            text = ""
            tail = self.head.prev
            cur = tail
            while True:
                text += cur.title
                cur = cur.prev
                if cur == tail:
                    break
                text += " -> "
        self.log("Backward: " + text)

    def playNext(self, current):
        if current is None:
            return self.head
        return current.next              # after the last song comes the first

    # ----- extra features built on the same list -----
    def count(self):
        if self.head is None:
            return 0
        n = 0
        cur = self.head
        while True:
            n += 1
            cur = cur.next
            if cur == self.head:
                return n

    def totalDuration(self):
        if self.head is None:
            return 0
        total = 0
        cur = self.head
        while True:
            total += cur.duration
            cur = cur.next
            if cur == self.head:
                return total

    def search(self, text):
        """Position (0-based) of the first song whose title contains text, or -1."""
        if self.head is None:
            return -1
        text = text.lower()
        index = 0
        cur = self.head
        while True:
            if text in cur.title.lower():
                return index
            index += 1
            cur = cur.next
            if cur == self.head:
                return -1

    def nodeAt(self, index):
        if self.head is None:
            return None
        cur = self.head
        for _ in range(index):
            cur = cur.next
        return cur

    def randomOther(self, current):
        """Shuffle: walk a random number of steps around the circle."""
        n = self.count()
        if n <= 1 or current is None:
            return self.head
        cur = current
        for _ in range(random.randint(1, n - 1)):
            cur = cur.next
        return cur
