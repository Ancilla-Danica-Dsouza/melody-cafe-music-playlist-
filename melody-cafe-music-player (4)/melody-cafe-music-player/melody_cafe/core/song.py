# Melody Cafe Music Player - Ancilla Danica Dsouza | PRN: 25070721021

"""PART A(c): the node structure."""


class Song:
    def __init__(self, title, duration, audio_file=None):
        self.title = title[:30]          # title up to 30 characters
        self.duration = duration         # duration in seconds
        self.audio_file = audio_file     # optional real mp3/wav file
        self.next = None
        self.prev = None
