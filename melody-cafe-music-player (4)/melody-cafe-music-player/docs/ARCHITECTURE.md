# Architecture

```
melody_cafe/
├── core/            PART A + B: the data structure (no GUI, no audio)
│   ├── song.py        Song node  (title, duration, audio_file, next, prev)
│   └── playlist.py    Playlist   (doubly circular linked list)
├── audio/           everything that makes sound
│   ├── backends.py    finds winsound / afplay / paplay / aplay / ffplay / pygame / Windows MCI
│   ├── player.py      Audio class: play, pause, resume, stop, volume
│   └── melody.py      makes a .wav melody from a song title
├── online/          internet music
│   └── deezer.py      search() + download_preview() using urllib
├── ui/              tkinter interface
│   ├── themes.py      all colour themes (incl. UAE themes)
│   ├── colors.py      fonts + colour helpers
│   ├── widgets.py     Pill, RoundIcon, Slider, Swatches, PlaylistView
│   ├── online_window.py  search window (runs network calls in threads)
│   └── app.py         PlayerApp main window
├── utils.py         fmt() mm:ss formatter
└── cli.py           command line flags: --test, --sound-test, or open the GUI
```

## The linked list
- `head` points to the first song; the last song is `head.prev`.
- `last.next -> first` and `first.prev -> last`, so playback wraps around forever.
- Nothing stores songs in a Python list or array. The playlist view walks the nodes to draw rows.

| Method | What it does |
|---|---|
| `addSong(title, duration)` | add at the end |
| `insertAfter(key, title, duration)` | insert after the song called `key` |
| `removeSong(title)` | unlink a song (handles head / only-song cases) |
| `displayForward()` / `displayBackward()` | print using `next` / `prev` |
| `playNext(current)` | next song, wrapping last -> first |
