# Melody Cafe Music Player - Ancilla Danica Dsouza | PRN: 25070721021

"""Small helpers."""


def fmt(seconds):
    seconds = int(seconds)
    return str(seconds // 60) + ":" + str(seconds % 60).zfill(2)
