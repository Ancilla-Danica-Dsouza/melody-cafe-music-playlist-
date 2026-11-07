# Melody Cafe Music Player - Ancilla Danica Dsouza | PRN: 25070721021

"""Command line entry: open the player, or run the console tests."""

import sys
import time

from .core import Playlist
from .audio import (Audio, make_melody_file, NATIVE, PYGAME_OK, PYGAME_ERROR,
                    MCI_OK, AUDIO_OK)


def sound_test():
    print("Platform        :", sys.platform)
    print("Windows media   :", "available" if MCI_OK else "no")
    print("System player   :", NATIVE if NATIVE else "none found")
    print("pygame          :", "ready" if PYGAME_OK else "not working (" + PYGAME_ERROR + ")")
    if not AUDIO_OK:
        print("\nNo way to play sound was found. Run: python -m pip install pygame")
        return
    audio = Audio()
    try:
        how = audio.play(make_melody_file("SoundTest", 6))
        print("\nPlaying a 6 second melody using", how, "... you should hear it now.")
        time.sleep(6)
        audio.stop()
        print("Finished. If you heard nothing, check your volume and output device.")
    except Exception as e:
        print("\nPlaying failed:", e)


def run_test():
    p = Playlist()
    p.addSong("Sunrise", 210)
    p.addSong("Desert Rain", 185)
    p.addSong("Marina Lights", 240)
    p.insertAfter("Sunrise", "Skyline", 200)
    p.insertAfter("Marina Lights", "Night Drive", 195)
    print("After adding and inserting:")
    p.displayForward()
    p.displayBackward()
    print("\nRemoving songs:")
    p.removeSong("Sunrise")
    p.removeSong("Desert Rain")
    p.removeSong("Night Drive")
    p.removeSong("Unknown")
    print("\nAfter removals:")
    p.displayForward()
    p.displayBackward()
    print("\nplayNext from Marina Lights:")
    print("Next song:", p.playNext(p.find("Marina Lights")).title)


def online_test(argv):
    """python main.py --online-test "daft punk"  -> step by step check of the internet music search."""
    import socket
    import platform
    from .online import download_preview, OnlineError
    from .online import deezer, itunes
    i = argv.index("--online-test")
    query = argv[i + 1] if i + 1 < len(argv) else "daft punk"
    print("Python", platform.python_version(), "on", platform.system())
    print("Searching for:", query, "\n")
    first = None
    for name, host, fn in (("Deezer", "api.deezer.com", deezer.search),
                           ("iTunes", "itunes.apple.com", itunes.search)):
        print("[" + name + "]")
        try:
            socket.getaddrinfo(host, 443)
            print("  1. DNS lookup of", host, "... OK")
        except OSError as e:
            print("  1. DNS lookup of", host, "... FAILED:", e)
            print("     -> no internet, DNS blocked, or this site is blocked on your network. Try another network / VPN.")
            continue
        try:
            tracks = fn(query, limit=5)
            print("  2. Search ... OK,", len(tracks), "playable results")
            for t in tracks[:3]:
                print("       -", t["title"], "|", t["artist"])
            if tracks and first is None:
                first = tracks[0]
        except OnlineError as e:
            print("  2. Search ... FAILED:", e)
    if first is not None:
        print("\n[Download]")
        try:
            print("  Preview saved to:", download_preview(first))
            print("\nONLINE MUSIC WORKS. Open the app and use the Online music button.")
        except OnlineError as e:
            print("  FAILED:", e)
    else:
        print("\nNo provider worked. Copy everything above and send it to get help.")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--test" in argv:
        run_test()
        return
    if "--sound-test" in argv:
        sound_test()
        return
    if "--online-test" in argv:
        online_test(argv)
        return
    try:
        import tkinter as tk
        from .ui.app import PlayerApp
    except ImportError:
        print("tkinter is not installed. Running the console test instead.\n")
        run_test()
        return
    root = tk.Tk()
    PlayerApp(root)
    root.mainloop()
